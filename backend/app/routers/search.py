"""Search & autocomplete endpoints (TZ 3.3)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..search import SearchParams, autocomplete, search_offers

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/autocomplete")
def autocomplete_endpoint(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=25),
    db: Session = Depends(get_db),
):
    return {"query": q, "suggestions": autocomplete(db, q, limit)}


@router.get("")
def search_endpoint(
    service_id: str | None = None,
    q: str | None = None,
    city: str | None = None,
    category: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    rating_min: float | None = None,
    online_booking: bool | None = None,
    sort: str = "price_asc",
    include_stale: bool = False,
    lat: float | None = None,
    lng: float | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    params = SearchParams(
        service_id=service_id,
        q=q,
        city=city,
        category=category,
        price_min=price_min,
        price_max=price_max,
        rating_min=rating_min,
        online_booking=online_booking,
        sort=sort,
        include_stale=include_stale,
        lat=lat,
        lng=lng,
        limit=limit,
        offset=offset,
    )
    return search_offers(db, params)
