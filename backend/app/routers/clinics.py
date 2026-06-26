"""Clinic endpoints: list (for map/filters) + clinic card (TZ 3.3)."""
from __future__ import annotations

from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Clinic, Price
from .meta import CATEGORY_LABELS

router = APIRouter(prefix="/api/clinics", tags=["clinics"])


def _iso(dt):
    if dt is None:
        return None
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).isoformat()


@router.get("")
def list_clinics(
    city: str | None = None,
    source: str | None = None,
    online_booking: bool | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Clinic)
    if city:
        query = query.filter(Clinic.city == city)
    if source:
        query = query.filter(Clinic.source == source)
    if online_booking is not None:
        query = query.filter(Clinic.has_online_booking.is_(online_booking))
    clinics = query.order_by(Clinic.city, Clinic.name).all()
    # offer counts per clinic
    from sqlalchemy import func

    counts = dict(
        db.query(Price.clinic_id, func.count(Price.id))
        .filter(Price.is_active.is_(True))
        .group_by(Price.clinic_id)
        .all()
    )
    return [
        {
            "id": c.id,
            "name": c.name,
            "city": c.city,
            "address": c.address,
            "phone": c.phone,
            "working_hours": c.working_hours,
            "website": c.website,
            "source": c.source,
            "lat": c.lat,
            "lng": c.lng,
            "rating": c.rating,
            "has_online_booking": c.has_online_booking,
            "services_count": counts.get(c.id, 0),
        }
        for c in clinics
    ]


@router.get("/{clinic_id}")
def get_clinic(clinic_id: str, db: Session = Depends(get_db)):
    c = db.query(Clinic).filter_by(id=clinic_id).first()
    if not c:
        raise HTTPException(404, "Clinic not found")
    prices = (
        db.query(Price)
        .filter(Price.clinic_id == c.id, Price.is_active.is_(True))
        .order_by(Price.category, Price.service_name_norm)
        .all()
    )
    services = [
        {
            "price_id": p.id,
            "service_id": p.service_id,
            "service_name": p.service_name_norm or p.service_name_raw,
            "service_name_raw": p.service_name_raw,
            "category": p.category,
            "category_label": CATEGORY_LABELS.get(p.category, p.category or "Прочее"),
            "price_kzt": float(p.price_kzt),
            "currency": p.currency,
            "duration_days": p.duration_days,
            "source_url": p.source_url,
            "parsed_at": _iso(p.parsed_at),
            "matched": p.service_id is not None,
        }
        for p in prices
    ]
    return {
        "id": c.id,
        "name": c.name,
        "city": c.city,
        "address": c.address,
        "phone": c.phone,
        "working_hours": c.working_hours,
        "website": c.website,
        "source": c.source,
        "lat": c.lat,
        "lng": c.lng,
        "rating": c.rating,
        "has_online_booking": c.has_online_booking,
        "services_count": len(services),
        "services": services,
    }
