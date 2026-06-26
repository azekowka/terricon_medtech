"""On-demand fetch + cache of a doctor's full profile from idoctor's public API.

Endpoints (base https://ext.idoctor.kz/ext-api/v2, header `x-user-city: <region>`):
  GET /doctors/{alias}                 -> bio (description), illnesses, clinics, …
  GET /doctors/{alias}/services        -> services with prices
  GET /comments?type=doctor&id={id}&mood=positive&page=N&perPage=M -> reviews

Cached into the Doctor row so a profile is fetched at most once.
"""
from __future__ import annotations

import logging

import httpx
from sqlalchemy.orm import Session

from .models import Doctor

logger = logging.getLogger("medservice.doctors")
API = "https://ext.idoctor.kz/ext-api/v2"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Origin": "https://idoctor.kz",
    "Referer": "https://idoctor.kz/",
}


def _appt(appointments):
    p = (appointments or {}).get("primary") or {}
    return p.get("price"), p.get("priceWithDiscount"), p.get("discountPercentage")


def _clinics(medcenters):
    out = []
    for mc in medcenters or []:
        price, price_disc, disc = _appt(mc.get("appointments"))
        geo = mc.get("geo") or {}
        out.append({
            "id": mc.get("id"),
            "name": mc.get("name"),
            "short": mc.get("shortName"),
            "price": price, "price_discount": price_disc, "discount": disc,
            "online_booking": mc.get("hasOnlineBooking"),
            "address": geo.get("address"),
            "lat": geo.get("latitude"), "lng": geo.get("longitude"),
            "schedule": [
                {"day": s.get("name"), "start": s.get("startTime"), "end": s.get("endTime"),
                 "work": s.get("isWork"), "h24": s.get("is24HoursWork")}
                for s in (mc.get("schedule") or [])
            ],
        })
    return out


def _diseases(illnesses):
    out = []
    for it in illnesses or []:
        if isinstance(it, dict):
            n = it.get("name")
        else:
            n = str(it)
        if n:
            out.append(n)
    return out[:40]


def _reviews(items):
    out = []
    for c in items or []:
        out.append({
            "author": c.get("authorName") or "Аноним",
            "rating": c.get("rating"),
            "text": (c.get("text") or "").strip(),
            "tags": [t.get("name") for t in (c.get("tags") or []) if isinstance(t, dict) and t.get("name")],
            "reply": (c.get("reply") or {}).get("text") if isinstance(c.get("reply"), dict) else c.get("reply"),
            "created_at": c.get("createdAt"),
            "visit_date": c.get("visitDate"),
        })
    return out


def fetch_profile(doctor: Doctor) -> dict | None:
    """Fetch bio/services/reviews for one doctor. Returns the enrichment dict."""
    alias = doctor.alias or f"{doctor.id}"
    region = doctor.region or "almaty"
    headers = {**HEADERS, "x-user-city": region}
    enrich: dict = {}
    try:
        with httpx.Client(headers=HEADERS, timeout=20.0, follow_redirects=True) as cl:
            try:
                cl.get("https://idoctor.kz/")  # seed Cloudflare cookie
            except Exception:
                pass
            # 1. detail
            r = cl.get(f"{API}/doctors/{alias}", headers=headers)
            if r.status_code == 200:
                d = (r.json() or {}).get("data") or {}
                enrich["description"] = d.get("description")
                enrich["diseases"] = _diseases(d.get("illnesses"))
                if d.get("medcenters"):
                    enrich["clinics"] = _clinics(d.get("medcenters"))
                if d.get("skills"):
                    enrich["specialties"] = [
                        {"name": s.get("name"), "alias": s.get("alias")} for s in d["skills"]
                    ]
                enrich["has_comments"] = bool(d.get("hasComments"))
                enrich["online_bookings"] = d.get("onlineBookingsCount") or 0
                if d.get("rating") is not None:
                    try:
                        enrich["rating"] = float(d["rating"])
                    except (TypeError, ValueError):
                        pass
                has_services = bool(d.get("hasServices"))
            else:
                has_services = False
            # 2. services
            if has_services:
                rs = cl.get(f"{API}/doctors/{alias}/services", headers=headers)
                if rs.status_code == 200:
                    sv = (rs.json() or {}).get("data") or []
                    enrich["services"] = sv if isinstance(sv, list) else []
            # 3. reviews
            if enrich.get("has_comments"):
                revs = []
                for mood in ("positive", "negative"):
                    try:
                        rr = cl.get(f"{API}/comments", headers=headers, params={
                            "type": "doctor", "id": doctor.id, "mood": mood,
                            "page": 1, "perPage": 15})
                        if rr.status_code == 200:
                            revs += _reviews((rr.json() or {}).get("data") or [])
                    except Exception:
                        pass
                enrich["reviews"] = revs
    except Exception as exc:
        logger.warning("profile fetch failed for %s: %s", alias, exc)
        return None
    return enrich


def ensure_profile(db: Session, doctor: Doctor) -> Doctor:
    """Fetch + cache the full profile if not already cached."""
    if doctor.profile_fetched:
        return doctor
    enrich = fetch_profile(doctor)
    if enrich is not None:
        if "description" in enrich:
            doctor.description = enrich["description"]
        if enrich.get("diseases"):
            doctor.diseases = enrich["diseases"]
        if enrich.get("clinics"):
            doctor.clinics = enrich["clinics"]
        if enrich.get("specialties"):
            doctor.specialties = enrich["specialties"]
            aliases = [s["alias"] for s in enrich["specialties"] if s.get("alias")]
            doctor.spec_aliases = "," + ",".join(aliases) + "," if aliases else ","
            doctor.primary_specialty = enrich["specialties"][0]["name"]
        doctor.services = enrich.get("services", doctor.services)
        doctor.review_items = enrich.get("reviews", [])
        doctor.has_comments = enrich.get("has_comments", False)
        doctor.online_bookings = enrich.get("online_bookings", 0)
        if "rating" in enrich:
            doctor.rating = enrich["rating"]
    doctor.profile_fetched = True
    db.commit()
    return doctor
