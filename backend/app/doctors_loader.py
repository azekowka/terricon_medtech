"""Load scraped idoctor doctors (data/doctors/*.json) into the Doctor table."""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from .config import settings
from .models import Doctor


def _doctors_path():
    return settings.data_path / "doctors"


def _row(it: dict) -> dict | None:
    did = it.get("id")
    if not did:
        return None
    specs = it.get("specialties") or []
    clinics = it.get("clinics") or []
    aliases = [s["alias"] for s in specs if s.get("alias")]
    return dict(
        id=did,
        alias=it.get("alias") or "",
        name=it.get("name") or "",
        avatar=it.get("avatar"),
        reviews=it.get("reviews") or 0,
        experience_years=it.get("experience_years"),
        rating=it.get("rating"),
        verified=bool(it.get("verified")),
        partner=bool(it.get("partner")),
        top=bool(it.get("top")),
        category=it.get("category"),
        accepts_children=bool(it.get("accepts_children")),
        age_min=str(it["age_min"]) if it.get("age_min") is not None else None,
        age_max=str(it["age_max"]) if it.get("age_max") is not None else None,
        region=it.get("region") or "",
        city=it.get("city"),
        min_price=it.get("min_price"),
        online_booking=any(c.get("online_booking") for c in clinics),
        primary_specialty=specs[0]["name"] if specs else None,
        spec_aliases="," + ",".join(aliases) + "," if aliases else ",",
        specialties=specs,
        clinics=clinics,
        diseases=it.get("diseases") or [],
        profile_url=it.get("profile_url"),
    )


def load_doctors(db: Session) -> int:
    """Bulk-load the scraped doctors (fast for the full ~40k dataset)."""
    path = _doctors_path() / "doctors.json"
    if not path.exists():
        return 0
    with open(path, encoding="utf-8") as f:
        items = json.load(f)
    # fresh load -> bulk insert; otherwise replace
    db.query(Doctor).delete()
    db.commit()
    batch, count = [], 0
    for it in items:
        row = _row(it)
        if not row:
            continue
        batch.append(row)
        count += 1
        if len(batch) >= 4000:
            db.bulk_insert_mappings(Doctor, batch)
            db.commit()
            batch = []
    if batch:
        db.bulk_insert_mappings(Doctor, batch)
        db.commit()
    return count


def load_specialties_meta():
    path = _doctors_path() / "specialties.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []


def load_regions_meta():
    path = _doctors_path() / "regions.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []
