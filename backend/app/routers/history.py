"""Price history + comparison endpoints (TZ 3.4)."""
from __future__ import annotations

from datetime import timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Clinic, Price, PriceHistory, Service
from ..search import SearchParams, search_offers

router = APIRouter(prefix="/api", tags=["history"])


def _iso(dt):
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).isoformat()


@router.get("/history")
def price_history(
    service_id: str | None = None,
    clinic_id: str | None = None,
    db: Session = Depends(get_db),
):
    """Time series of observed prices, optionally filtered by service/clinic."""
    q = db.query(PriceHistory)
    if service_id:
        q = q.filter(PriceHistory.service_id == service_id)
    if clinic_id:
        q = q.filter(PriceHistory.clinic_id == clinic_id)
    rows = q.order_by(PriceHistory.recorded_at).all()

    clinic_names = dict(db.query(Clinic.id, Clinic.name).all())
    # group by clinic for multi-series charts
    series: dict[str, list] = {}
    for r in rows:
        series.setdefault(r.clinic_id, []).append(
            {"recorded_at": _iso(r.recorded_at), "price_kzt": float(r.price_kzt)}
        )
    return {
        "service_id": service_id,
        "clinic_id": clinic_id,
        "series": [
            {"clinic_id": cid, "clinic_name": clinic_names.get(cid, cid), "points": pts}
            for cid, pts in series.items()
        ],
    }


@router.get("/compare")
def compare(
    service_id: str = Query(...),
    clinic_ids: str | None = Query(None, description="Comma-separated clinic ids"),
    city: str | None = None,
    db: Session = Depends(get_db),
):
    """Comparison table for one service across clinics (TZ 3.4)."""
    result = search_offers(
        db, SearchParams(service_id=service_id, city=city, sort="price_asc", limit=500)
    )
    offers = result["offers"]
    if clinic_ids:
        wanted = {c.strip() for c in clinic_ids.split(",") if c.strip()}
        offers = [o for o in offers if o["clinic_id"] in wanted]
    # cheapest flag
    if offers:
        cheapest = min(o["price_kzt"] for o in offers)
        for o in offers:
            o["is_cheapest"] = o["price_kzt"] == cheapest
    result["offers"] = offers
    # Recompute stats over the FILTERED set so the summary matches the rows shown.
    prices = [o["price_kzt"] for o in offers]
    result["stats"] = {
        "count": len(offers),
        "min_price": min(prices) if prices else None,
        "max_price": max(prices) if prices else None,
        "avg_price": round(sum(prices) / len(prices), 2) if prices else None,
    }
    return result
