"""Load scraped idoctor doctors (data/doctors/*.json) into the Doctor table."""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from .config import settings
from .models import Doctor


def _doctors_path():
    return settings.data_path / "doctors"


def load_doctors(db: Session) -> int:
    path = _doctors_path() / "doctors.json"
    if not path.exists():
        return 0
    with open(path, encoding="utf-8") as f:
        items = json.load(f)
    count = 0
    for it in items:
        did = it.get("id")
        if not did:
            continue
        doc = db.get(Doctor, did)
        if doc is None:
            doc = Doctor(id=did)
            db.add(doc)
        specs = it.get("specialties") or []
        clinics = it.get("clinics") or []
        aliases = [s["alias"] for s in specs if s.get("alias")]
        doc.alias = it.get("alias") or ""
        doc.name = it.get("name") or ""
        doc.avatar = it.get("avatar")
        doc.reviews = it.get("reviews") or 0
        doc.experience_years = it.get("experience_years")
        doc.rating = it.get("rating")
        doc.verified = bool(it.get("verified"))
        doc.partner = bool(it.get("partner"))
        doc.top = bool(it.get("top"))
        doc.category = it.get("category")
        doc.accepts_children = bool(it.get("accepts_children"))
        doc.age_min = str(it.get("age_min")) if it.get("age_min") is not None else None
        doc.age_max = str(it.get("age_max")) if it.get("age_max") is not None else None
        doc.region = it.get("region") or ""
        doc.city = it.get("city")
        doc.min_price = it.get("min_price")
        doc.online_booking = any(c.get("online_booking") for c in clinics)
        doc.primary_specialty = specs[0]["name"] if specs else None
        doc.spec_aliases = "," + ",".join(aliases) + "," if aliases else ","
        doc.specialties = specs
        doc.clinics = clinics
        doc.diseases = it.get("diseases") or []
        doc.profile_url = it.get("profile_url")
        count += 1
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
