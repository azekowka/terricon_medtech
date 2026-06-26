"""Doctors API — powers the /doctors directory clone (region + specialty filters)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..doctors_loader import load_regions_meta, load_specialties_meta
from ..models import Doctor

router = APIRouter(prefix="/api/doctors", tags=["doctors"])

REGION_NAMES = {
    "almaty": "Алматы", "astana": "Астана", "shymkent": "Шымкент",
    "karaganda": "Караганда", "aktobe": "Актобе", "taraz": "Тараз",
    "pavlodar": "Павлодар", "ust-kamenogorsk": "Усть-Каменогорск",
    "semey": "Семей", "kostanay": "Костанай", "kyzylorda": "Кызылорда",
    "uralsk": "Уральск", "petropavlovsk": "Петропавловск", "aktau": "Актау",
    "kokshetau": "Кокшетау", "taldykorgan": "Талдыкорган",
    "turkestan": "Туркестан", "ekibastuz": "Экибастуз",
}


def _card(d: Doctor) -> dict:
    clinic = (d.clinics or [None])[0]
    return {
        "id": d.id,
        "name": d.name,
        "avatar": d.avatar,
        "specialties": d.specialties or [],
        "primary_specialty": d.primary_specialty,
        "experience_years": d.experience_years,
        "category": d.category,
        "accepts_children": d.accepts_children,
        "age_min": d.age_min,
        "age_max": d.age_max,
        "rating": d.rating,
        "reviews": d.reviews,
        "verified": d.verified,
        "top": d.top,
        "min_price": d.min_price,
        "online_booking": d.online_booking,
        "city": d.city,
        "region": d.region,
        "clinics_count": len(d.clinics or []),
        "clinic": (
            {
                "name": clinic.get("name"),
                "address": clinic.get("address"),
                "price": clinic.get("price"),
                "price_discount": clinic.get("price_discount"),
                "discount": clinic.get("discount"),
                "online_booking": clinic.get("online_booking"),
            }
            if clinic
            else None
        ),
    }


@router.get("/meta")
def meta(db: Session = Depends(get_db)):
    region_counts = dict(
        db.query(Doctor.region, func.count(Doctor.id)).group_by(Doctor.region).all()
    )
    regions = [
        {"slug": s, "name": REGION_NAMES.get(s, s), "count": region_counts.get(s, 0)}
        for s in REGION_NAMES
        if region_counts.get(s, 0) > 0
    ]
    regions.sort(key=lambda r: -r["count"])
    specialties = [s for s in load_specialties_meta() if s.get("count", 0) > 0]
    total = db.query(func.count(Doctor.id)).scalar() or 0
    return {"regions": regions, "specialties": specialties, "total": total}


@router.get("")
def list_doctors(
    region: str | None = None,
    specialty: str | None = None,
    q: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    rating_min: float | None = None,
    experience_min: int | None = None,
    accepts_children: bool | None = None,
    online_booking: bool | None = None,
    verified: bool | None = None,
    sort: str = "rating",  # rating | price_asc | price_desc | experience | reviews
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=60),
    db: Session = Depends(get_db),
):
    query = db.query(Doctor)
    if region:
        query = query.filter(Doctor.region == region)
    if specialty:
        query = query.filter(Doctor.spec_aliases.like(f"%,{specialty},%"))
    if q:
        query = query.filter(Doctor.name.ilike(f"%{q.strip()}%"))
    if price_min is not None:
        query = query.filter(Doctor.min_price >= price_min)
    if price_max is not None:
        query = query.filter(Doctor.min_price <= price_max)
    if rating_min is not None:
        query = query.filter(Doctor.rating >= rating_min)
    if experience_min is not None:
        query = query.filter(Doctor.experience_years >= experience_min)
    if accepts_children is not None:
        query = query.filter(Doctor.accepts_children.is_(accepts_children))
    if online_booking is not None:
        query = query.filter(Doctor.online_booking.is_(online_booking))
    if verified is not None:
        query = query.filter(Doctor.verified.is_(verified))

    if sort == "price_asc":
        query = query.order_by(Doctor.min_price.is_(None).asc(), Doctor.min_price.asc())
    elif sort == "price_desc":
        query = query.order_by(Doctor.min_price.desc())
    elif sort == "experience":
        query = query.order_by(Doctor.experience_years.desc())
    elif sort == "reviews":
        query = query.order_by(Doctor.reviews.desc())
    else:  # rating: top/verified/rating first (idoctor-like ranking)
        query = query.order_by(Doctor.top.desc(), Doctor.verified.desc(), Doctor.rating.desc())

    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "region": region,
        "region_name": REGION_NAMES.get(region, region) if region else None,
        "doctors": [_card(d) for d in rows],
    }


@router.get("/{doctor_id}")
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    d = db.get(Doctor, doctor_id)
    if not d:
        raise HTTPException(404, "Doctor not found")
    return {
        **_card(d),
        "alias": d.alias,
        "partner": d.partner,
        "clinics": d.clinics or [],
        "diseases": d.diseases or [],
        "profile_url": d.profile_url,
    }
