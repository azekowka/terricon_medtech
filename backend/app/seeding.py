"""Dictionary loading + database bootstrap/seed orchestration."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from .config import settings
from .models import Price, PriceHistory, Service
from .parsers.pipeline import mark_stale_inactive, run_sources


def _stable(*parts: str) -> float:
    h = hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()
    return (int(h[:8], 16) % 1_000_000) / 1_000_000.0


def backfill_history(db: Session, weeks: int = 6) -> int:
    """Synthesize realistic past price points so the history chart is meaningful.

    Generates weekly observations trending toward the current price. Idempotent:
    skips if older history already exists.
    """
    now = datetime.now(timezone.utc)
    already = (
        db.query(PriceHistory)
        .filter(PriceHistory.recorded_at < now - timedelta(days=3))
        .count()
    )
    if already > 0:
        return 0
    prices = (
        db.query(Price)
        .filter(Price.is_active.is_(True), Price.service_id.isnot(None))
        .all()
    )
    added = 0
    for p in prices:
        current = float(p.price_kzt)
        # total drift over the window: -8%..+8%
        drift = (_stable(p.id, "drift") - 0.5) * 0.16
        start = current * (1 - drift)
        for i in range(weeks):
            frac = i / max(weeks - 1, 1)
            val = start + (current - start) * frac
            # small weekly noise
            val *= 0.985 + _stable(p.id, str(i)) * 0.03
            val = round(val / 50.0) * 50
            recorded = now - timedelta(days=(weeks - i) * 7)
            db.add(
                PriceHistory(
                    clinic_id=p.clinic_id,
                    service_id=p.service_id,
                    price_kzt=Decimal(str(val)),
                    recorded_at=recorded,
                )
            )
            added += 1
    db.commit()
    return added


def load_dictionary(db: Session) -> int:
    """Idempotently upsert the services dictionary from JSON (TZ 3.2)."""
    path = settings.data_path / "services_dictionary.json"
    with open(path, encoding="utf-8") as f:
        items = json.load(f)
    count = 0
    for it in items:
        svc = db.query(Service).filter_by(code=it["code"]).first()
        if svc is None:
            svc = Service(code=it["code"])
            db.add(svc)
        svc.name = it["name"]
        svc.category = it["category"]
        svc.specialty = it.get("specialty", "")
        svc.tarif_code = it.get("tarif_code", "")
        svc.synonyms = it["synonyms"]
        svc.base_price_kzt = it.get("base_price_kzt")
        svc.duration_days = it.get("duration_days")
        count += 1
    db.commit()
    return count


def seed_database(db: Session, include_live: bool = False) -> dict:
    """Full seed: load dictionary, then run the seed source (and optionally live)."""
    n_services = load_dictionary(db)
    # seed = curated realistic data; fixtures = sample PDF/XLSX/DOCX (TZ 3.1);
    # real = actual clinic price lists supplied for the hackathon
    sources = ["seed", "fixtures", "real"]
    if include_live:
        from .parsers.registry import LIVE_SOURCES

        sources += LIVE_SOURCES
    logs = run_sources(db, sources)
    backfill_history(db)
    mark_stale_inactive(db)  # keep is_active consistent with the 30-day rule (TZ 4)
    return {
        "services_loaded": n_services,
        "runs": [
            {
                "source": l.source,
                "status": l.status,
                "found": l.records_found,
                "new": l.records_new,
                "updated": l.records_updated,
                "errors": l.errors_count,
            }
            for l in logs
        ],
    }


def bootstrap_if_empty(db: Session) -> dict | None:
    """On first boot, ensure the dictionary is loaded and seed data exists."""
    n_services = db.query(Service).count()
    if n_services == 0:
        load_dictionary(db)
    n_prices = db.query(Price).count()
    if n_prices == 0:
        return seed_database(db, include_live=False)
    return None
