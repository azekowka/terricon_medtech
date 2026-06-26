"""Price-subscription endpoints (TZ 3.4: подписка на изменение цены)."""
from __future__ import annotations

from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Clinic, Service, Subscription
from ..schemas import SubscriptionCreate

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


def _iso(dt):
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).isoformat()


@router.post("")
def create_subscription(body: SubscriptionCreate, db: Session = Depends(get_db)):
    if not db.query(Service).filter_by(id=body.service_id).first():
        raise HTTPException(404, "Service not found")
    if body.clinic_id and not db.query(Clinic).filter_by(id=body.clinic_id).first():
        raise HTTPException(404, "Clinic not found")
    sub = Subscription(
        email=body.email,
        service_id=body.service_id,
        clinic_id=body.clinic_id,
        target_price_kzt=body.target_price_kzt,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return {"id": sub.id, "status": "subscribed", "created_at": _iso(sub.created_at)}


@router.get("")
def list_subscriptions(email: str, db: Session = Depends(get_db)):
    subs = db.query(Subscription).filter_by(email=email, active=True).all()
    svc = dict(db.query(Service.id, Service.name).all())
    clin = dict(db.query(Clinic.id, Clinic.name).all())
    return [
        {
            "id": s.id,
            "service_id": s.service_id,
            "service_name": svc.get(s.service_id),
            "clinic_id": s.clinic_id,
            "clinic_name": clin.get(s.clinic_id) if s.clinic_id else None,
            "target_price_kzt": float(s.target_price_kzt) if s.target_price_kzt is not None else None,
            "created_at": _iso(s.created_at),
        }
        for s in subs
    ]


@router.delete("/{sub_id}")
def delete_subscription(sub_id: str, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter_by(id=sub_id).first()
    if not sub:
        raise HTTPException(404, "Subscription not found")
    sub.active = False
    db.commit()
    return {"status": "unsubscribed"}
