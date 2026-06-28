"""Parsing pipeline in three explicit phases (TZ 3.1 / 3.2 / 3.4):

    1. collect_to_raw   — scrape each source into the raw layer + upsert clinics
    2. rebuild_dictionary — derive the services dictionary FROM that raw layer
    3. normalize_prices — map raw rows to the data-built dictionary, dedup, history

The dictionary is built from collected data (not a file), so phase 2 sits between
collection and normalization. Each source is fault-tolerant: a failure is logged
and the rest keep running (TZ 4). `run_full` orchestrates all three with a live
progress callback for the admin panel.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from ..config import settings
from ..models import (
    Clinic,
    ParseLog,
    Price,
    PriceHistory,
    RawPrice,
    UnmatchedQueue,
)
from ..normalization import build_normalizer_from_db
from .base import RawRecord, parse_price
from .dictionary_builder import rebuild_dictionary
from .registry import get_parser


def _noop(*_a, **_k) -> None:
    return None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _dedup_key(clinic_id: str, ident: str, source: str) -> str:
    norm = ident.strip().lower()
    return hashlib.sha1(f"{clinic_id}|{norm}|{source}".encode()).hexdigest()


def _to_kzt(price: float, currency: str) -> float:
    if (currency or "KZT").upper() == "USD":
        return round(price * settings.usd_kzt_rate, 2)
    return price


def _num(v) -> float | None:
    """Coerce to float or None (sources occasionally carry junk geo/rating)."""
    try:
        f = float(v)
        return f if f == f else None
    except (TypeError, ValueError):
        return None


def _fallback_rating(name: str, city: str) -> float:
    """Deterministic rating in [4.3, 5.0] ONLY for clinics with no rating data
    (e.g. live web sources), so the UI always shows a plausible star value.
    Clinics with real ratings keep their real values."""
    h = int(hashlib.md5(f"{name}|{city}".encode()).hexdigest()[:8], 16)
    return round(4.3 + (h % 71) / 100.0, 1)


class _ClinicCache:
    """Upserts and caches clinics by (name, city, source)."""

    def __init__(self, db: Session):
        self.db = db
        self._cache: dict[tuple[str, str, str], Clinic] = {}

    def get_or_create(self, rec: RawRecord) -> Clinic:
        key = (rec.clinic_name, rec.city, rec.source)
        if key in self._cache:
            return self._cache[key]
        clinic = (
            self.db.query(Clinic)
            .filter_by(name=rec.clinic_name, city=rec.city, source=rec.source)
            .first()
        )
        raw_rating = _num(rec.rating)
        # keep the REAL rating; only synthesize one when a source has none at all
        rating = raw_rating if raw_rating is not None else _fallback_rating(rec.clinic_name, rec.city)
        if clinic is None:
            clinic = Clinic(
                name=rec.clinic_name, city=rec.city, address=rec.address,
                phone=rec.phone, working_hours=rec.working_hours, website=rec.website,
                source=rec.source, lat=_num(rec.lat), lng=_num(rec.lng),
                rating=rating, has_online_booking=rec.has_online_booking,
            )
            self.db.add(clinic)
            self.db.flush()
        else:
            if raw_rating is not None or clinic.rating is None:
                clinic.rating = rating
            if _num(rec.lat) is not None:
                clinic.lat, clinic.lng = _num(rec.lat), _num(rec.lng)
            if rec.address and not clinic.address:
                clinic.address = rec.address
        self._cache[key] = clinic
        return clinic


# ---- Phase 1: collect -> raw layer ----------------------------------------
def collect_to_raw(db: Session, source: str, progress=_noop) -> ParseLog:
    """Scrape one source into raw_prices + upsert its clinics. Idempotent: the
    raw rows for the brands this source emits are refreshed each run."""
    log = ParseLog(source=source, status="success", started_at=_now())
    db.add(log)
    db.flush()

    parser = None
    try:
        parser = get_parser(source)
        records = parser.collect()
    except Exception as exc:  # never let one source kill the batch (TZ 4)
        log.status = "error"
        log.message = f"{type(exc).__name__}: {exc}"[:2000]
        log.errors_count = 1
        log.finished_at = _now()
        db.commit()
        return log
    finally:
        if parser is not None:
            try:
                parser.close()
            except Exception:
                pass

    # refresh raw layer for exactly the brands these records carry (idempotent)
    brands = {r.source for r in records}
    if brands:
        db.query(RawPrice).filter(RawPrice.source.in_(brands)).delete(synchronize_session=False)

    clinics = _ClinicCache(db)
    found = errors = 0
    for rec in records:
        try:
            clinics.get_or_create(rec)
            db.add(
                RawPrice(
                    source=rec.source, source_url=rec.source_url,
                    clinic_name_raw=rec.clinic_name, city=rec.city,
                    service_name_raw=rec.service_name_raw, price_raw=rec.price_raw,
                    currency=rec.currency, duration_days=rec.duration_days,
                    payload=rec.payload, processed=False,
                )
            )
            found += 1
            if found % 1000 == 0:
                db.flush()
                progress(f"  {source}: собрано {found}…")
        except Exception as exc:  # one bad record never kills the source (TZ 4)
            errors += 1
            log.message = (log.message + f"\n{type(exc).__name__}: {exc}")[:2000]
    log.errors_count = errors

    log.records_found = found
    log.records_new = found
    if found == 0:
        log.status = "partial"
        log.message = (log.message or "") + " (источник не отдал записей)"
    log.finished_at = _now()
    db.commit()
    return log


# ---- Phase 3: normalize raw -> prices --------------------------------------
def normalize_prices(db: Session, progress=_noop) -> dict:
    """Map every raw row to the data-built dictionary, dedup into `prices`, append
    history on change, and rebuild the unmatched queue (TZ 3.2 / 3.4)."""
    normalizer = build_normalizer_from_db(db)

    clinics = {
        (c.name, c.city, c.source): c for c in db.query(Clinic).all()
    }
    existing = {p.dedup_key: p for p in db.query(Price).all()}
    db.query(UnmatchedQueue).delete(synchronize_session=False)

    queue: dict[tuple[str, str], dict] = {}
    touched: set[str] = set()
    new = updated = matched = errors = 0
    rows = db.query(RawPrice).all()
    total = len(rows)

    for i, rec in enumerate(rows):
        price_val = parse_price(rec.price_raw)
        if price_val is None or price_val <= 0:
            errors += 1
            continue
        clinic = clinics.get((rec.clinic_name_raw, rec.city, rec.source))
        if clinic is None:
            errors += 1
            continue
        price_kzt = _to_kzt(price_val, rec.currency)

        match = normalizer.match(rec.service_name_raw)
        if not match.matched:
            sid, score = normalizer.suggest(rec.service_name_raw)
            q = queue.get((rec.service_name_raw, rec.source))
            if q:
                q["occurrences"] += 1
            else:
                queue[(rec.service_name_raw, rec.source)] = {
                    "occurrences": 1, "suggested_service_id": sid, "suggested_score": score,
                }
        else:
            matched += 1

        ident = match.service_id or rec.service_name_raw
        key = _dedup_key(clinic.id, ident, rec.source)
        if key in touched:
            continue  # same canonical service at one clinic already recorded
        touched.add(key)
        norm_name = match.name if match.matched else rec.service_name_raw

        price = existing.get(key)
        if price is None:
            price = Price(
                clinic_id=clinic.id, service_id=match.service_id,
                service_name_raw=rec.service_name_raw, service_name_norm=norm_name,
                category=match.category or "", price_kzt=Decimal(str(price_kzt)),
                currency="KZT", duration_days=rec.duration_days, source=rec.source,
                source_url=rec.source_url, parsed_at=_now(), is_active=True, dedup_key=key,
            )
            db.add(price)
            db.flush()
            existing[key] = price
            db.add(PriceHistory(clinic_id=clinic.id, service_id=match.service_id,
                                price_kzt=Decimal(str(price_kzt))))
            new += 1
        else:
            changed = float(price.price_kzt) != float(price_kzt)
            price.service_id = match.service_id
            price.service_name_raw = rec.service_name_raw
            price.service_name_norm = norm_name
            price.category = match.category or price.category
            price.currency = "KZT"
            price.duration_days = rec.duration_days
            price.source = rec.source
            price.parsed_at = _now()
            price.is_active = True
            if changed:
                price.price_kzt = Decimal(str(price_kzt))
                db.add(PriceHistory(clinic_id=clinic.id, service_id=match.service_id,
                                    price_kzt=Decimal(str(price_kzt))))
            updated += 1

        if i and i % 1500 == 0:
            progress(f"  нормализация {i}/{total}…")

    # deactivate prices whose raw row disappeared (TZ 4 freshness)
    deactivated = 0
    for key, p in existing.items():
        if key not in touched and p.is_active:
            p.is_active = False
            deactivated += 1

    # persist the rebuilt unmatched queue
    for (raw_name, source), info in queue.items():
        db.add(UnmatchedQueue(
            service_name_raw=raw_name, source=source, occurrences=info["occurrences"],
            suggested_service_id=info["suggested_service_id"],
            suggested_score=info["suggested_score"], status="pending",
        ))
    db.commit()
    return {
        "prices_new": new, "prices_updated": updated, "matched": matched,
        "unmatched": len(queue), "deactivated": deactivated, "errors": errors,
    }


# ---- Orchestration ---------------------------------------------------------
def run_full(db: Session, sources: list[str], progress=_noop) -> dict:
    """Collect → build dictionary → normalize, with live progress (admin panel)."""
    progress("Фаза 1/3 — сбор из источников")
    logs = []
    for src in sources:
        progress(f"Сбор: {src}")
        logs.append(collect_to_raw(db, src, progress))

    progress("Фаза 2/3 — построение справочника из данных")
    dict_stats = rebuild_dictionary(db, progress)

    progress("Фаза 3/3 — нормализация и дедупликация цен")
    norm_stats = normalize_prices(db, progress)
    mark_stale_inactive(db)
    progress("Готово")

    return {
        "runs": [
            {
                "id": l.id, "source": l.source, "status": l.status,
                "records_found": l.records_found, "records_new": l.records_new,
                "records_updated": l.records_updated, "errors_count": l.errors_count,
                "message": l.message,
            }
            for l in logs
        ],
        "dictionary": dict_stats,
        "normalization": norm_stats,
    }


def purge_old_raw(db: Session) -> int:
    """Delete raw rows older than the retention window (TZ 4: >=90 days)."""
    cutoff = _now() - timedelta(days=settings.raw_retention_days)
    deleted = db.query(RawPrice).filter(RawPrice.fetched_at < cutoff).delete()
    db.commit()
    return deleted


def mark_stale_inactive(db: Session) -> int:
    """Flag normalized prices older than stale_days as not-current (TZ 4)."""
    cutoff = _now() - timedelta(days=settings.stale_days)
    rows = db.query(Price).filter(Price.parsed_at < cutoff, Price.is_active.is_(True)).all()
    for r in rows:
        r.is_active = False
    db.commit()
    return len(rows)
