"""Metadata endpoints powering the UI filters and the landing dashboard."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Clinic, Price, Service
from ..normalization.normalizer import Normalizer  # noqa: F401 (keep import graph warm)

router = APIRouter(prefix="/api/meta", tags=["meta"])

CATEGORY_LABELS = {
    "laboratory": "Лаборатория",
    "doctor": "Приём врача",
    "diagnostic": "Диагностика",
    "procedure": "Процедура",
}


@router.get("")
def meta(db: Session = Depends(get_db)):
    cities = [c for (c,) in db.query(Clinic.city).distinct().order_by(Clinic.city).all()]
    sources = [s for (s,) in db.query(Clinic.source).distinct().order_by(Clinic.source).all()]
    categories = [
        {"key": k, "label": CATEGORY_LABELS.get(k, k)}
        for (k,) in db.query(Service.category).distinct().order_by(Service.category).all()
    ]
    n_clinics = db.query(func.count(Clinic.id)).scalar() or 0
    n_services = db.query(func.count(Service.id)).scalar() or 0
    n_prices = db.query(func.count(Price.id)).filter(Price.is_active.is_(True)).scalar() or 0
    last = db.query(func.max(Price.parsed_at)).scalar()
    price_range = db.query(func.min(Price.price_kzt), func.max(Price.price_kzt)).filter(
        Price.is_active.is_(True)
    ).first()
    return {
        "cities": cities,
        "sources": sources,
        "categories": categories,
        "category_labels": CATEGORY_LABELS,
        "counts": {
            "clinics": n_clinics,
            "services": n_services,
            "active_prices": n_prices,
            "cities": len(cities),
            "sources": len(sources),
        },
        "price_range": {
            "min": float(price_range[0]) if price_range and price_range[0] is not None else None,
            "max": float(price_range[1]) if price_range and price_range[1] is not None else None,
        },
        "last_updated": (last.replace(tzinfo=timezone.utc).isoformat() if last and not last.tzinfo else (last.isoformat() if last else None)),
        "server_time": datetime.now(timezone.utc).isoformat(),
    }
