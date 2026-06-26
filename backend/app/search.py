"""Search & comparison logic (TZ 3.3).

  * autocomplete over the services dictionary (name + synonyms)
  * offer search: resolve a query/service to clinics, apply filters, sort, and
    annotate freshness (TZ 4: data older than `stale_days` is not "current")
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from .config import settings
from .models import Clinic, Price, Service
from .normalization import build_normalizer_from_db
from .normalization.text import normalize_text


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _haversine(lat1, lng1, lat2, lng2) -> float | None:
    if None in (lat1, lng1, lat2, lng2):
        return None
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(a)), 2)


def autocomplete(db: Session, q: str, limit: int = 10) -> list[dict]:
    nq = normalize_text(q)
    if not nq:
        return []
    services = db.query(Service).all()
    # offer counts per service (active only)
    counts = dict(
        db.query(Price.service_id, func.count(Price.id))
        .filter(Price.is_active.is_(True), Price.service_id.isnot(None))
        .group_by(Price.service_id)
        .all()
    )
    scored = []
    for s in services:
        keys = [normalize_text(s.name), *[normalize_text(x) for x in (s.synonyms or [])]]
        best = 0
        for k in keys:
            if not k:
                continue
            if k == nq:
                best = max(best, 100)
            elif k.startswith(nq) or nq.startswith(k):
                best = max(best, 80)
            elif nq in k or k in nq:
                best = max(best, 60)
        if best:
            scored.append((best, counts.get(s.id, 0), s))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [
        {
            "id": s.id,
            "code": s.code,
            "name": s.name,
            "category": s.category,
            "offers_count": counts.get(s.id, 0),
        }
        for _, _, s in scored[:limit]
    ]


def resolve_service(db: Session, q: str) -> Service | None:
    normalizer = build_normalizer_from_db(db)
    m = normalizer.match(q)
    if m.matched:
        return db.query(Service).filter_by(id=m.service_id).first()
    # try direct dictionary autocomplete top hit
    hits = autocomplete(db, q, limit=1)
    if hits:
        return db.query(Service).filter_by(id=hits[0]["id"]).first()
    return None


@dataclass
class SearchParams:
    service_id: str | None = None
    q: str | None = None
    city: str | None = None
    category: str | None = None
    price_min: float | None = None
    price_max: float | None = None
    rating_min: float | None = None
    online_booking: bool | None = None
    sort: str = "price_asc"  # price_asc|price_desc|updated|distance|rating
    include_stale: bool = False
    lat: float | None = None
    lng: float | None = None
    limit: int = 100
    offset: int = 0


def search_offers(db: Session, p: SearchParams) -> dict:
    service: Service | None = None
    if p.service_id:
        service = db.query(Service).filter_by(id=p.service_id).first()
    elif p.q:
        service = resolve_service(db, p.q)

    query = db.query(Price, Clinic).join(Clinic, Price.clinic_id == Clinic.id)
    query = query.filter(Price.is_active.is_(True))

    if service is not None:
        query = query.filter(Price.service_id == service.id)
    elif p.q:
        like = f"%{p.q.strip()}%"
        query = query.filter(
            (Price.service_name_norm.ilike(like)) | (Price.service_name_raw.ilike(like))
        )

    if p.city:
        query = query.filter(Clinic.city == p.city)
    if p.category:
        query = query.filter(Price.category == p.category)
    if p.price_min is not None:
        query = query.filter(Price.price_kzt >= p.price_min)
    if p.price_max is not None:
        query = query.filter(Price.price_kzt <= p.price_max)
    if p.rating_min is not None:
        query = query.filter(Clinic.rating >= p.rating_min)
    if p.online_booking is not None:
        query = query.filter(Clinic.has_online_booking.is_(p.online_booking))

    rows = query.all()

    stale_cutoff = _now().timestamp() - settings.stale_days * 86400
    offers = []
    for price, clinic in rows:
        parsed = _aware(price.parsed_at)
        is_stale = parsed.timestamp() < stale_cutoff
        if is_stale and not p.include_stale:
            continue
        distance = _haversine(p.lat, p.lng, clinic.lat, clinic.lng)
        offers.append(
            {
                "price_id": price.id,
                "clinic_id": clinic.id,
                "clinic_name": clinic.name,
                "city": clinic.city,
                "address": clinic.address,
                "phone": clinic.phone,
                "working_hours": clinic.working_hours,
                "website": clinic.website,
                "rating": clinic.rating,
                "has_online_booking": clinic.has_online_booking,
                "lat": clinic.lat,
                "lng": clinic.lng,
                "service_name_raw": price.service_name_raw,
                "service_name_norm": price.service_name_norm,
                "category": price.category,
                "price_kzt": float(price.price_kzt),
                "currency": price.currency,
                "duration_days": price.duration_days,
                "source": price.source,
                "source_url": price.source_url,
                "parsed_at": parsed.isoformat(),
                "is_stale": is_stale,
                "distance_km": distance,
            }
        )

    # sorting
    sort = p.sort
    if sort == "price_desc":
        offers.sort(key=lambda o: o["price_kzt"], reverse=True)
    elif sort == "updated":
        offers.sort(key=lambda o: o["parsed_at"], reverse=True)
    elif sort == "rating":
        offers.sort(key=lambda o: (o["rating"] or 0), reverse=True)
    elif sort == "distance" and p.lat is not None:
        offers.sort(key=lambda o: (o["distance_km"] is None, o["distance_km"] or 1e9))
    else:  # price_asc default
        offers.sort(key=lambda o: o["price_kzt"])

    total = len(offers)
    prices_only = [o["price_kzt"] for o in offers]
    stats = {
        "count": total,
        "min_price": min(prices_only) if prices_only else None,
        "max_price": max(prices_only) if prices_only else None,
        "avg_price": round(sum(prices_only) / len(prices_only), 2) if prices_only else None,
    }
    page = offers[p.offset : p.offset + p.limit]
    return {
        "service": (
            {
                "id": service.id,
                "code": service.code,
                "name": service.name,
                "category": service.category,
                "duration_days": service.duration_days,
            }
            if service
            else None
        ),
        "query": p.q,
        "stats": stats,
        "offers": page,
    }
