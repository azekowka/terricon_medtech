"""
Scraper for idoctor.kz doctors across ALL Kazakhstan regions.

The pages embed a rich JSON `initialDoctorsList` (Next.js RSC) with everything we
need: name, specialties (skills), clinics (medcenters) with full weekly schedule,
geo/address, appointment prices, qualification/category, patient age, rating,
reviews, experience, avatar. The default `/REGION/doctors` shows the top 15; the
specialty-filtered `/REGION/doctors/SPECIALTY` shows that specialty's top 15 — so
iterating regions x specialties yields broad coverage without any hidden API.

`--enrich N` additionally fetches N profile pages for "Лечение заболеваний"
(diseases treated). Polite: configurable delay + retries.

Usage:
    python scripts/scrape_idoctor.py --specialties 40 --enrich 120
    python scripts/scrape_idoctor.py --region almaty --specialties 60
Output: data/doctors/{doctors.json, specialties.json, regions.json}
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import Counter

import httpx
from bs4 import BeautifulSoup

from idoctor_extract import extract_doctors_list

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "doctors")
BASE = "https://idoctor.kz"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MedServicePriceBot/1.0 (research)",
    "Accept-Language": "ru,kk;q=0.9",
}

REGIONS = {
    "almaty": "Алматы", "astana": "Астана", "shymkent": "Шымкент",
    "karaganda": "Караганда", "aktobe": "Актобе", "taraz": "Тараз",
    "pavlodar": "Павлодар", "ust-kamenogorsk": "Усть-Каменогорск",
    "semey": "Семей", "kostanay": "Костанай", "kyzylorda": "Кызылорда",
    "uralsk": "Уральск", "petropavlovsk": "Петропавловск", "aktau": "Актау",
    "kokshetau": "Кокшетау", "taldykorgan": "Талдыкорган",
    "turkestan": "Туркестан", "ekibastuz": "Экибастуз",
}


def _appt(appointments):
    p = (appointments or {}).get("primary") or {}
    return p.get("price"), p.get("priceWithDiscount"), p.get("discountPercentage")


def normalize(raw: dict, region: str) -> dict:
    clinics = []
    for mc in raw.get("medcenters") or []:
        price, price_disc, disc = _appt(mc.get("appointments"))
        geo = mc.get("geo") or {}
        schedule = [
            {"day": s.get("name"), "start": s.get("startTime"), "end": s.get("endTime"),
             "work": s.get("isWork"), "h24": s.get("is24HoursWork")}
            for s in (mc.get("schedule") or [])
        ]
        clinics.append({
            "id": mc.get("id"), "name": mc.get("name"), "short": mc.get("shortName"),
            "price": price, "price_discount": price_disc, "discount": disc,
            "online_booking": mc.get("hasOnlineBooking"),
            "address": geo.get("address"),
            "lat": geo.get("latitude"), "lng": geo.get("longitude"),
            "schedule": schedule,
        })
    quals = raw.get("qualifications") or []
    child = raw.get("child") or {}
    age = child.get("age") or {}
    prices = [c["price_discount"] or c["price"] for c in clinics if (c["price_discount"] or c["price"])]
    rating = raw.get("rating")
    try:
        rating = float(rating) if rating is not None else None
    except (TypeError, ValueError):
        rating = None
    return {
        "id": raw.get("id"),
        "alias": raw.get("alias"),
        "name": raw.get("fullName"),
        "avatar": raw.get("avatar"),
        "reviews": raw.get("commentsCount"),
        "experience_years": raw.get("workExperience"),
        "rating": rating,
        "verified": bool(raw.get("isVerifiedByUs")),
        "partner": bool(raw.get("isPartner")),
        "top": bool(raw.get("isTop")),
        "category": quals[0]["name"] if quals else None,
        "accepts_children": bool(child.get("accept")),
        "age_min": age.get("min"),
        "age_max": age.get("max"),
        "specialties": [{"name": s.get("name"), "alias": s.get("alias")} for s in (raw.get("skills") or [])],
        "clinics": clinics,
        "region": region,
        "city": (raw.get("city") or {}).get("name"),
        "min_price": min(prices) if prices else None,
        "profile_url": f"{BASE}/{region}/doctor/{raw.get('alias')}",
    }


def fetch(client, url, delay):
    for attempt in range(3):
        try:
            r = client.get(url)
            time.sleep(delay)
            if r.status_code == 200:
                return r.text
            if r.status_code == 404:
                return None
        except Exception:
            time.sleep(delay)
    return None


def enrich_diseases(client, doc, delay):
    html = fetch(client, doc["profile_url"], delay)
    if not html:
        return
    soup = BeautifulSoup(html, "lxml")
    h = next((e for e in soup.find_all(["h2", "h3"])
              if "Лечение заболеваний" in e.get_text()), None)
    if not h:
        return
    out, seen = [], set()
    for el in h.find_all_next():
        if el.name in ("h2", "h3"):
            break
        if el.name in ("a", "li"):
            t = re.sub(r"\s+", " ", el.get_text(" ", strip=True))
            if t and 2 < len(t) < 60 and t.lower() not in seen and not re.search(
                r"отзыв|услуг|показать|ещё|все ", t, re.I
            ):
                seen.add(t.lower())
                out.append(t)
        if len(out) >= 20:
            break
    doc["diseases"] = out


def scrape(regions, max_specialties, enrich, delay):
    os.makedirs(OUT_DIR, exist_ok=True)
    client = httpx.Client(headers=HEADERS, timeout=25.0, follow_redirects=True)
    doctors: dict[int, dict] = {}
    skill_names: dict[str, str] = {}
    skill_freq: Counter = Counter()

    # Pass 1: region defaults -> seed doctors + harvest specialties
    print("Pass 1: region default pages")
    for slug in regions:
        html = fetch(client, f"{BASE}/{slug}/doctors", delay)
        if not html:
            print(f"  {slug}: no data")
            continue
        raw = extract_doctors_list(html) or []
        for rd in raw:
            d = normalize(rd, slug)
            if d["id"] and d["id"] not in doctors:
                doctors[d["id"]] = d
            for s in d["specialties"]:
                if s.get("alias"):
                    skill_names[s["alias"]] = s["name"]
                    skill_freq[s["alias"]] += 1
        print(f"  {slug}: {len(raw)} docs (total {len(doctors)})")

    top_specialties = [a for a, _ in skill_freq.most_common(max_specialties)]
    print(f"\nPass 2: {len(top_specialties)} specialties x {len(regions)} regions")
    for slug in regions:
        before = len(doctors)
        for alias in top_specialties:
            html = fetch(client, f"{BASE}/{slug}/doctors/{alias}", delay)
            if not html:
                continue
            for rd in extract_doctors_list(html) or []:
                d = normalize(rd, slug)
                if d["id"] and d["id"] not in doctors:
                    doctors[d["id"]] = d
                for s in d["specialties"]:
                    if s.get("alias"):
                        skill_names.setdefault(s["alias"], s["name"])
        print(f"  {slug} ({REGIONS.get(slug, slug)}): +{len(doctors)-before} (total {len(doctors)})")
        _dump(doctors, skill_names, regions)  # incremental save

    # Pass 3: enrich a capped subset with diseases (prioritize verified/top)
    if enrich:
        print(f"\nPass 3: enriching {enrich} profiles with diseases")
        ranked = sorted(doctors.values(), key=lambda d: (d["verified"], d["top"], d["reviews"] or 0), reverse=True)
        for i, doc in enumerate(ranked[:enrich]):
            enrich_diseases(client, doc, delay)
            if (i + 1) % 25 == 0:
                print(f"  enriched {i+1}")
                _dump(doctors, skill_names, regions)

    client.close()
    _dump(doctors, skill_names, regions)
    print(f"\nTOTAL {len(doctors)} doctors, {len(skill_names)} specialties -> {OUT_DIR}")


def _dump(doctors, skill_names, regions):
    docs = list(doctors.values())
    with open(os.path.join(OUT_DIR, "doctors.json"), "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False)
    with open(os.path.join(OUT_DIR, "specialties.json"), "w", encoding="utf-8") as f:
        counts = Counter()
        for d in docs:
            for s in d["specialties"]:
                if s.get("alias"):
                    counts[s["alias"]] += 1
        json.dump(
            [{"alias": a, "name": skill_names.get(a, a), "count": counts.get(a, 0)}
             for a in sorted(skill_names, key=lambda x: -counts.get(x, 0))],
            f, ensure_ascii=False, indent=1,
        )
    region_counts = Counter(d["region"] for d in docs)
    with open(os.path.join(OUT_DIR, "regions.json"), "w", encoding="utf-8") as f:
        json.dump(
            [{"slug": s, "name": REGIONS.get(s, s), "count": region_counts.get(s, 0)} for s in regions],
            f, ensure_ascii=False, indent=2,
        )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--region")
    ap.add_argument("--specialties", type=int, default=40)
    ap.add_argument("--enrich", type=int, default=100)
    ap.add_argument("--delay", type=float, default=0.55)
    args = ap.parse_args()
    regs = [args.region] if args.region else list(REGIONS)
    scrape(regs, args.specialties, args.enrich, args.delay)
