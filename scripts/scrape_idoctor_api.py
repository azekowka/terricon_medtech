"""
Full doctor scrape via idoctor.kz's public JSON API.

Endpoint:  GET https://ext.idoctor.kz/ext-api/v2/doctors?page=N&perPage=100
Header:    x-user-city: <region alias>   (scopes the list to a city/region)
Response:  {data:[...doctors...], pagination:{currentPage, hasNextPage, total}}

Each doctor matches the same schema as the SSR `initialDoctorsList`, so we reuse
`normalize()` from scrape_idoctor. perPage is capped at 100 server-side.

Usage:  python scripts/scrape_idoctor_api.py [--per-page 100] [--delay 0.4] [--region almaty]
Output: data/doctors/{doctors.json, specialties.json, regions.json}
"""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter

import httpx

from scrape_idoctor import OUT_DIR, REGIONS, normalize, _dump as _dump_meta

API = "https://ext.idoctor.kz/ext-api/v2/doctors"


def _safe_dump(doctors, skill_names, all_regions):
    """Atomic write (tmp + replace) so a read never sees a partial file and a
    crash never truncates the dataset."""
    docs = list(doctors.values())
    path = os.path.join(OUT_DIR, "doctors.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False)
    os.replace(tmp, path)
    # meta files (small)
    counts = Counter()
    for d in docs:
        for s in d.get("specialties") or []:
            if s.get("alias"):
                counts[s["alias"]] += 1
    with open(os.path.join(OUT_DIR, "specialties.json"), "w", encoding="utf-8") as f:
        json.dump([{"alias": a, "name": skill_names.get(a, a), "count": counts[a]}
                   for a in sorted(skill_names, key=lambda x: -counts.get(x, 0))],
                  f, ensure_ascii=False, indent=1)
    region_counts = Counter(d["region"] for d in docs)
    with open(os.path.join(OUT_DIR, "regions.json"), "w", encoding="utf-8") as f:
        json.dump([{"slug": s, "name": REGIONS.get(s, s), "count": region_counts.get(s, 0)}
                   for s in all_regions], f, ensure_ascii=False, indent=2)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Origin": "https://idoctor.kz",
    "Referer": "https://idoctor.kz/",
}


def scrape_api(regions, per_page, delay, max_pages=None, resume=True):
    os.makedirs(OUT_DIR, exist_ok=True)
    client = httpx.Client(headers=HEADERS, timeout=30.0)
    doctors: dict[int, dict] = {}
    skill_names: dict[str, str] = {}
    # resume: merge into any existing dataset so batched runs accumulate
    existing = os.path.join(OUT_DIR, "doctors.json")
    all_regions = list(REGIONS)
    if resume and os.path.exists(existing) and os.path.getsize(existing) > 100:
        # fail-loud: never silently start empty and overwrite a real dataset
        prev = json.load(open(existing, encoding="utf-8"))
        for d in prev:
            doctors[d["id"]] = d
            for s in d.get("specialties") or []:
                if s.get("alias"):
                    skill_names.setdefault(s["alias"], s["name"])
        print(f"resumed from {len(doctors)} existing doctors")

    client.get("https://idoctor.kz/")  # seed Cloudflare __cf_bm cookie

    for slug in regions:
        h = {"x-user-city": slug}
        page = 1
        total = None
        added = 0
        while True:
            # robust fetch: retry on rate-limit / errors with backoff + cookie refresh
            r = None
            for attempt in range(6):
                try:
                    r = client.get(API, params={"page": page, "perPage": per_page}, headers=h)
                except Exception:
                    r = None
                if r is not None and r.status_code == 200:
                    break
                wait = delay * (2 ** attempt) + 0.5
                if r is None or r.status_code in (403, 429, 503):
                    try:
                        client.get("https://idoctor.kz/")  # refresh Cloudflare cookie
                    except Exception:
                        pass
                time.sleep(wait)
            time.sleep(delay)
            if r is None or r.status_code != 200:
                print(f"  {slug} p{page}: giving up ({r.status_code if r else 'no resp'})")
                break
            payload = r.json()
            data = payload.get("data") or []
            pag = payload.get("pagination") or {}
            total = pag.get("total", total)
            for rd in data:
                d = normalize(rd, slug)
                if d["id"] and d["id"] not in doctors:
                    doctors[d["id"]] = d
                    added += 1
                for s in d["specialties"]:
                    if s.get("alias"):
                        skill_names.setdefault(s["alias"], s["name"])
            if not pag.get("hasNextPage") or not data:
                break
            page += 1
            if max_pages and page > max_pages:
                break
        print(f"{slug} ({REGIONS.get(slug, slug)}): +{added} (total in city: {total}) | running {len(doctors)}")
        _safe_dump(doctors, skill_names, all_regions)  # incremental save

    client.close()
    _safe_dump(doctors, skill_names, all_regions)
    print(f"\nTOTAL {len(doctors)} doctors, {len(skill_names)} specialties -> {OUT_DIR}")
    return len(doctors)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--region")
    ap.add_argument("--per-page", type=int, default=100)
    ap.add_argument("--delay", type=float, default=0.4)
    ap.add_argument("--max-pages", type=int, default=None)
    args = ap.parse_args()
    regs = [r.strip() for r in args.region.split(",")] if args.region else list(REGIONS)
    scrape_api(regs, args.per_page, args.delay, args.max_pages)
