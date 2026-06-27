"""Map data: cheapest price per city (Aviasales-style price bubbles)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Doctor
from .doctors import REGION_NAMES

router = APIRouter(prefix="/api/map", tags=["map"])

# approximate city centroids (lat, lng)
REGION_COORDS: dict[str, tuple[float, float]] = {
    "almaty": (43.2389, 76.8897),
    "astana": (51.1694, 71.4491),
    "shymkent": (42.3174, 69.5874),
    "karaganda": (49.8047, 73.1094),
    "aktobe": (50.2839, 57.1670),
    "taraz": (42.9000, 71.3667),
    "pavlodar": (52.2873, 76.9674),
    "ust-kamenogorsk": (49.9480, 82.6280),
    "semey": (50.4111, 80.2275),
    "kostanay": (53.2144, 63.6322),
    "kyzylorda": (44.8479, 65.5093),
    "uralsk": (51.2270, 51.3865),
    "petropavlovsk": (54.8753, 69.1628),
    "aktau": (43.6410, 51.1980),
    "kokshetau": (53.2833, 69.3833),
    "taldykorgan": (45.0156, 78.3736),
    "turkestan": (43.3017, 68.2517),
    "ekibastuz": (51.7244, 75.3230),
}


@router.get("/cities")
def map_cities(db: Session = Depends(get_db)):
    """Per-city cheapest doctor appointment price + counts, for map bubbles."""
    rows = (
        db.query(
            Doctor.region,
            func.min(Doctor.min_price),
            func.count(Doctor.id),
            func.max(Doctor.rating),
        )
        # floor out unrealistic scraped values so bubbles show a sensible "from X"
        .filter(Doctor.min_price.isnot(None), Doctor.min_price >= 1000)
        .group_by(Doctor.region)
        .all()
    )
    out = []
    for region, min_price, cnt, best_rating in rows:
        coords = REGION_COORDS.get(region)
        if not coords or not min_price:
            continue
        lat, lng = coords
        out.append({
            "slug": region,
            "name": REGION_NAMES.get(region, region),
            "lat": lat,
            "lng": lng,
            "min_price": float(min_price),
            "doctors": cnt,
            "best_rating": float(best_rating) if best_rating is not None else None,
        })
    out.sort(key=lambda c: -c["doctors"])
    return {"cities": out}
