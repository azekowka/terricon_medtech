"""Parsing pipeline: collect -> raw layer -> normalize -> dedup/upsert.

Implements TZ 3.1 (dedup, raw layer, error journaling), TZ 3.2 (normalization,
unmatched queue) and TZ 3.4 (price history). Each source runs independently and a
failure in one is logged but does not stop the others (TZ 4: fault tolerance).
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
from .registry import get_parser


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _dedup_key(clinic_id: str, raw_name: str, source: str) -> str:
    norm = raw_name.strip().lower()
    return hashlib.sha1(f"{clinic_id}|{norm}|{source}".encode()).hexdigest()


def _to_kzt(price: float, currency: str) -> float:
    if currency.upper() == "USD":
        return round(price * settings.usd_kzt_rate, 2)
    return price


class _ClinicCache:
    """Upserts and caches clinics by (name, city, source) within a run."""

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
        if clinic is None:
            clinic = Clinic(
                name=rec.clinic_name,
                city=rec.city,
                address=rec.address,
                phone=rec.phone,
                working_hours=rec.working_hours,
                website=rec.website,
                source=rec.source,
                lat=rec.lat,
                lng=rec.lng,
                rating=rec.rating,
                has_online_booking=rec.has_online_booking,
            )
            self.db.add(clinic)
            self.db.flush()  # assign id
        else:
            # refresh light metadata if newly provided
            if rec.rating is not None:
                clinic.rating = rec.rating
            if rec.lat is not None:
                clinic.lat, clinic.lng = rec.lat, rec.lng
        self._cache[key] = clinic
        return clinic


def _queue_unmatched(db: Session, raw_name: str, source: str, suggestion) -> None:
    existing = (
        db.query(UnmatchedQueue)
        .filter_by(service_name_raw=raw_name, source=source)
        .first()
    )
    if existing:
        existing.occurrences += 1
        existing.updated_at = _now()
        return
    sid, score = suggestion
    db.add(
        UnmatchedQueue(
            service_name_raw=raw_name,
            source=source,
            occurrences=1,
            suggested_service_id=sid,
            suggested_score=score,
            status="pending",
        )
    )


def run_source(db: Session, source: str) -> ParseLog:
    """Run a single source end-to-end, returning its ParseLog."""
    log = ParseLog(source=source, status="success", started_at=_now())
    db.add(log)
    db.flush()

    parser = None
    try:
        parser = get_parser(source)
        records = parser.collect()
    except Exception as exc:  # never let one source kill the batch (TZ 4)
        log.status = "error"
        log.message = f"{type(exc).__name__}: {exc}"
        log.errors_count = 1
        log.finished_at = _now()
        db.commit()
        if parser is not None:
            parser.close()
        return log
    finally:
        if parser is not None:
            try:
                parser.close()
            except Exception:
                pass

    normalizer = build_normalizer_from_db(db)
    clinics = _ClinicCache(db)
    found = new = updated = errors = 0

    for rec in records:
        found += 1
        try:
            # 1. persist raw layer
            db.add(
                RawPrice(
                    source=rec.source,
                    source_url=rec.source_url,
                    clinic_name_raw=rec.clinic_name,
                    city=rec.city,
                    service_name_raw=rec.service_name_raw,
                    price_raw=rec.price_raw,
                    currency=rec.currency,
                    duration_days=rec.duration_days,
                    payload=rec.payload,
                    processed=True,
                )
            )

            price_val = parse_price(rec.price_raw)
            if price_val is None or price_val <= 0:
                errors += 1
                continue
            price_kzt = _to_kzt(price_val, rec.currency)

            clinic = clinics.get_or_create(rec)

            # 2. normalize
            match = normalizer.match(rec.service_name_raw)
            if not match.matched:
                _queue_unmatched(
                    db,
                    rec.service_name_raw,
                    rec.source,
                    normalizer.suggest(rec.service_name_raw),
                )

            # 3. dedup / upsert normalized price.
            # Dedup on the RESOLVED identity when matched, so the same canonical
            # service scraped under two synonyms at one clinic collapses into one
            # row (TZ 3.1). Fall back to the raw name only for unmatched records.
            ident = match.service_id or rec.service_name_raw
            key = _dedup_key(clinic.id, ident, rec.source)
            # Only adopt the dictionary name when we actually MATCHED; otherwise keep
            # the raw name (match.name may hold a below-threshold suggestion).
            norm_name = match.name if match.matched else rec.service_name_raw
            price = db.query(Price).filter_by(dedup_key=key).first()
            if price is None:
                price = Price(
                    clinic_id=clinic.id,
                    service_id=match.service_id,
                    service_name_raw=rec.service_name_raw,
                    service_name_norm=norm_name,
                    category=match.category or "",
                    price_kzt=Decimal(str(price_kzt)),
                    # price_kzt is always stored in tenge; USD is converted above,
                    # so the canonical currency label is KZT (TZ 2.2).
                    currency="KZT",
                    duration_days=rec.duration_days,
                    source=rec.source,
                    source_url=rec.source_url,
                    parsed_at=_now(),
                    is_active=True,
                    dedup_key=key,
                )
                db.add(price)
                db.flush()
                db.add(
                    PriceHistory(
                        clinic_id=clinic.id,
                        service_id=match.service_id,
                        price_kzt=Decimal(str(price_kzt)),
                    )
                )
                new += 1
            else:
                changed = float(price.price_kzt) != float(price_kzt)
                price.service_id = match.service_id
                price.service_name_raw = rec.service_name_raw
                price.service_name_norm = norm_name
                price.category = match.category or price.category
                price.currency = "KZT"
                price.duration_days = rec.duration_days
                price.parsed_at = _now()
                price.is_active = True
                if changed:
                    price.price_kzt = Decimal(str(price_kzt))
                    db.add(
                        PriceHistory(
                            clinic_id=clinic.id,
                            service_id=match.service_id,
                            price_kzt=Decimal(str(price_kzt)),
                        )
                    )
                updated += 1
        except Exception as exc:
            errors += 1
            log.message = (log.message + f"\n{type(exc).__name__}: {exc}")[:2000]

    log.records_found = found
    log.records_new = new
    log.records_updated = updated
    log.errors_count = errors
    if found == 0:
        log.status = "partial"
        log.message = (log.message or "") + " (no records extracted)"
    elif errors:
        log.status = "partial"
    log.finished_at = _now()
    db.commit()
    return log


def run_sources(db: Session, sources: list[str]) -> list[ParseLog]:
    logs = []
    for source in sources:
        logs.append(run_source(db, source))
    return logs


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
