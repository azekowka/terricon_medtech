"""Services dictionary endpoints (TZ 3.2)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Price, Service
from .meta import CATEGORY_LABELS

router = APIRouter(prefix="/api/services", tags=["services"])


def _offer_counts(db: Session) -> dict:
    return dict(
        db.query(Price.service_id, func.count(Price.id))
        .filter(Price.is_active.is_(True), Price.service_id.isnot(None))
        .group_by(Price.service_id)
        .all()
    )


@router.get("")
def list_services(
    category: str | None = None,
    q: str | None = None,
    sort: str = "name",  # name | popular
    limit: int = Query(2000, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    query = db.query(Service)
    if category:
        query = query.filter(Service.category == category)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(Service.name.ilike(like))
    counts = _offer_counts(db)
    if sort == "popular":
        # order by number of active offers (dictionary is small enough to sort in app)
        services = sorted(query.all(), key=lambda s: counts.get(s.id, 0), reverse=True)[:limit]
    else:
        services = query.order_by(Service.category, Service.name).limit(limit).all()
    return [
        {
            "id": s.id,
            "code": s.code,
            "name": s.name,
            "category": s.category,
            "category_label": CATEGORY_LABELS.get(s.category, s.category),
            "specialty": s.specialty,
            "tarif_code": s.tarif_code,
            "synonyms": s.synonyms or [],
            "duration_days": s.duration_days,
            "offers_count": counts.get(s.id, 0),
        }
        for s in services
    ]


@router.get("/{service_id}")
def get_service(service_id: str, db: Session = Depends(get_db)):
    s = db.query(Service).filter_by(id=service_id).first()
    if not s:
        raise HTTPException(404, "Service not found")
    agg = (
        db.query(
            func.count(Price.id),
            func.min(Price.price_kzt),
            func.max(Price.price_kzt),
            func.avg(Price.price_kzt),
        )
        .filter(Price.service_id == s.id, Price.is_active.is_(True))
        .first()
    )
    return {
        "id": s.id,
        "code": s.code,
        "name": s.name,
        "category": s.category,
        "category_label": CATEGORY_LABELS.get(s.category, s.category),
        "specialty": s.specialty,
        "tarif_code": s.tarif_code,
        "synonyms": s.synonyms or [],
        "duration_days": s.duration_days,
        "base_price_kzt": s.base_price_kzt,
        "stats": {
            "count": agg[0] or 0,
            "min_price": float(agg[1]) if agg[1] is not None else None,
            "max_price": float(agg[2]) if agg[2] is not None else None,
            "avg_price": round(float(agg[3]), 2) if agg[3] is not None else None,
        },
    }
