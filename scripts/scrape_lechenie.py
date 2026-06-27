"""
Build a disease catalog ("Лечение заболеваний") from idoctor's illness API.

Endpoint: GET https://ext.idoctor.kz/ext-api/v2/illnesses/{alias}
  -> {id, alias, name, skills:[{id,alias,name}], similar:[{id,alias,name}], ...}

We BFS the `similar` graph from seed illnesses, collecting each illness's name and
the specialties (skills) that treat it. Diseases are grouped by specialty -> the
category structure for the catalog page. Only factual data is stored (names,
treating specialties, relations) — not the prose descriptions.

Usage: python scripts/scrape_lechenie.py [--max 500] [--delay 0.4]
Output: data/diseases/{diseases.json, categories.json}
"""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import deque

import httpx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "diseases")
API = "https://ext.idoctor.kz/ext-api/v2/illnesses"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Origin": "https://idoctor.kz",
    "Referer": "https://idoctor.kz/",
    "x-user-city": "almaty",
}
SEEDS = ["1445-diffuznaya-mastopatiya"]
DOC_API = "https://ext.idoctor.kz/ext-api/v2/doctors"


def _get(client, url, delay):
    for attempt in range(4):
        try:
            r = client.get(url)
            time.sleep(delay)
            if r.status_code == 200:
                return r
            if r.status_code in (403, 429, 503):
                try:
                    client.get("https://idoctor.kz/")
                except Exception:
                    pass
                time.sleep(delay * (2 ** attempt) + 0.5)
        except Exception:
            time.sleep(delay)
    return None


def _bootstrap_seeds(client, delay: float, max_docs: int = 130) -> list[str]:
    """Diverse illness seeds: per specialty pick the most-reviewed doctor (most
    likely to have illnesses tagged), read their `illnesses` aliases so BFS spans
    all medical fields, not one cluster."""
    path = os.path.join(ROOT, "data", "doctors", "doctors.json")
    if not os.path.exists(path):
        return list(SEEDS)
    docs = json.load(open(path, encoding="utf-8"))
    best: dict[str, dict] = {}
    for d in docs:
        sp = d.get("primary_specialty") or "?"
        if sp not in best or (d.get("reviews") or 0) > (best[sp].get("reviews") or 0):
            best[sp] = d
    picked = sorted(best.values(), key=lambda d: -(d.get("reviews") or 0))[:max_docs]
    seeds = set(SEEDS)
    for i, d in enumerate(picked):
        r = _get(client, f"{DOC_API}/{d['alias']}", delay)
        if r is None:
            continue
        for ill in ((r.json() or {}).get("data") or {}).get("illnesses") or []:
            if ill.get("alias"):
                seeds.add(ill["alias"])
        if (i + 1) % 25 == 0:
            print(f"  seeds: {len(seeds)} from {i+1}/{len(picked)} doctors")
    print(f"bootstrapped {len(seeds)} seed diseases from {len(picked)} doctors")
    return list(seeds)


def scrape(max_count: int, delay: float):
    os.makedirs(OUT, exist_ok=True)
    client = httpx.Client(headers=HEADERS, timeout=25.0)
    diseases: dict[str, dict] = {}
    skills: dict[str, str] = {}  # alias -> name
    seed_list = _bootstrap_seeds(client, delay)
    queue = deque(seed_list)
    queued = set(seed_list)

    while queue and len(diseases) < max_count:
        alias = queue.popleft()
        try:
            r = client.get(f"{API}/{alias}")
            time.sleep(delay)
        except Exception:
            time.sleep(delay)
            continue
        if r.status_code != 200:
            continue
        d = (r.json() or {}).get("data") or {}
        if not d.get("id"):
            continue
        dskills = [{"alias": s["alias"], "name": s["name"]} for s in (d.get("skills") or []) if s.get("alias")]
        for s in dskills:
            skills.setdefault(s["alias"], s["name"])
        similar = [{"alias": s["alias"], "name": s["name"]} for s in (d.get("similar") or []) if s.get("alias")]
        diseases[alias] = {
            "id": d["id"],
            "alias": alias,
            "name": d.get("name"),
            "skills": dskills,
            "similar": [s["alias"] for s in similar][:12],
        }
        # enqueue related (and capture their names too)
        for s in (d.get("similar") or []):
            a = s.get("alias")
            if a and a not in queued:
                queued.add(a)
                queue.append(a)
        if len(diseases) % 25 == 0:
            print(f"  {len(diseases)} diseases, {len(skills)} specialties (queue {len(queue)})")

    client.close()

    # group by specialty -> categories
    cats: dict[str, dict] = {}
    for dis in diseases.values():
        for s in dis["skills"]:
            c = cats.setdefault(s["alias"], {"alias": s["alias"], "name": skills.get(s["alias"], s["alias"]),
                                             "diseases": []})
            c["diseases"].append({"alias": dis["alias"], "name": dis["name"]})
    categories = sorted(cats.values(), key=lambda c: -len(c["diseases"]))

    json.dump(list(diseases.values()), open(os.path.join(OUT, "diseases.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    json.dump(categories, open(os.path.join(OUT, "categories.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nTOTAL {len(diseases)} diseases in {len(categories)} categories -> {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=500)
    ap.add_argument("--delay", type=float, default=0.4)
    args = ap.parse_args()
    scrape(args.max, args.delay)
