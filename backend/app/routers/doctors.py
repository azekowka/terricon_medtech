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


@router.get("/recommendations")
def recommendations(
    region: str | None = None,
    specialty: str | None = None,
    exclude: int | None = None,
    db: Session = Depends(get_db),
):
    """Aggregator-style "best deals": a few genuinely advantageous picks
    (best value, cheapest with good rating, top rated) with computed reasons —
    like Aviasales/Trip.com smart suggestions."""
    q = db.query(Doctor).filter(Doctor.min_price.isnot(None), Doctor.rating.isnot(None))
    if region:
        q = q.filter(Doctor.region == region)
    if specialty:
        q = q.filter(Doctor.spec_aliases.like(f"%,{specialty},%"))
    if exclude:
        q = q.filter(Doctor.id != exclude)
    # pool: well-rated, priced doctors (cap for performance)
    pool = q.order_by(Doctor.rating.desc()).limit(400).all()
    pool = [d for d in pool if d.min_price and d.min_price > 0]
    if len(pool) < 3:
        return {"items": [], "avg_price": None}

    prices = [float(d.min_price) for d in pool]
    avg = sum(prices) / len(prices)

    picks: list[tuple[str, Doctor]] = []
    used: set[int] = set()

    def take(label, doc):
        if doc and doc.id not in used:
            used.add(doc.id)
            picks.append((label, doc))

    # 1. Best value: high rating AND below-average price (maximize rating, then cheapest)
    value = [d for d in pool if (d.rating or 0) >= 4.3 and float(d.min_price) <= avg]
    value.sort(key=lambda d: (-(d.rating or 0), float(d.min_price)))
    take("bestValue", value[0] if value else None)

    # 2. Cheapest with a solid rating
    cheap = sorted([d for d in pool if (d.rating or 0) >= 4.0 and d.id not in used],
                   key=lambda d: float(d.min_price))
    take("cheapest", cheap[0] if cheap else None)

    # 3. Top rated (with enough reviews) — quality pick
    top = sorted([d for d in pool if d.id not in used and (d.reviews or 0) >= 10],
                 key=lambda d: (-(d.rating or 0), -(d.reviews or 0)))
    take("topRated", top[0] if top else None)

    # 4. fallback popular if we still have < 3
    if len(picks) < 3:
        pop = sorted([d for d in pool if d.id not in used],
                     key=lambda d: -(d.reviews or 0))
        take("popular", pop[0] if pop else None)

    items = []
    for label, d in picks[:3]:
        price = float(d.min_price)
        below_pct = round((avg - price) / avg * 100) if avg else 0
        items.append({
            "type": label,
            "doctor": _card(d),
            "below_avg_pct": max(0, below_pct),
            "cheaper_than_avg": max(0, round(avg - price)),
            "rating": d.rating,
            "reviews": d.reviews,
            "experience": d.experience_years,
        })
    return {"items": items, "avg_price": round(avg)}


def _full(d: Doctor) -> dict:
    return {
        **_card(d),
        "alias": d.alias,
        "partner": d.partner,
        "clinics": d.clinics or [],
        "diseases": d.diseases or [],
        "description": d.description,
        "services": d.services or [],
        "reviews_list": d.review_items or [],
        "has_comments": d.has_comments,
        "online_bookings": d.online_bookings,
        "profile_fetched": d.profile_fetched,
        "profile_url": d.profile_url,
    }


@router.get("/{doctor_id}")
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    d = db.get(Doctor, doctor_id)
    if not d:
        raise HTTPException(404, "Doctor not found")
    return _full(d)


@router.get("/{doctor_id}/profile")
def get_doctor_profile(doctor_id: int, db: Session = Depends(get_db)):
    """Full profile — fetched from idoctor's API and cached on first view."""
    d = db.get(Doctor, doctor_id)
    if not d:
        raise HTTPException(404, "Doctor not found")
    if not d.profile_fetched:
        from ..doctors_profile import ensure_profile

        ensure_profile(db, d)
    return _full(d)
