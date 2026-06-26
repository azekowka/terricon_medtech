"""Deterministic "seed" source.

Generates realistic raw price records from data/clinics.json + the services
dictionary. Crucially it emits raw service names using the dictionary *synonyms*
(not the canonical names), so the normalization pipeline (TZ 3.2) is exercised
end-to-end exactly like a real scrape would be. It also injects a few unknown
service names per source to populate the unmatched/manual-labelling queue.

Determinism: all "random" choices derive from a stable md5 hash of the inputs, so
re-running produces identical data (which also lets us demonstrate dedup, TZ 3.1).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..config import settings
from .base import BaseParser, RawRecord

# Services every applicable clinic should carry so search/compare is rich.
CORE_BY_CATEGORY = {
    "laboratory": {"oak", "oam", "glucose", "biochem", "tsh", "vitd"},
    "doctor": {"doc_therapist", "doc_cardio", "doc_gyn", "doc_neuro"},
    "diagnostic": {"uzi_abdomen", "ecg", "uzi_thyroid", "flg"},
    "procedure": {"venipuncture", "inj_im"},
}

# Coverage probability per profile/category (how much of the catalog they carry).
COVERAGE = {
    "lab": {"laboratory": 0.92, "procedure": 0.7},
    "diagnostic": {"diagnostic": 0.9, "laboratory": 0.45, "procedure": 0.6},
    "multiprofile": {
        "doctor": 0.95,
        "laboratory": 0.6,
        "diagnostic": 0.7,
        "procedure": 0.8,
    },
}

# Unknown service names per source -> exercise the unmatched queue (TZ 3.2).
UNKNOWN_SERVICES = [
    ("Чек-ап «Здоровое сердце» (комплекс)", "12500"),
    ("Консультация диетолога", "8000"),
    ("ПЦР на грипп A/B", "7800"),
    ("Программа «Женское здоровье 40+»", "23900"),
]


def _rng(*parts: str) -> float:
    """Stable pseudo-random float in [0,1) from the given parts."""
    h = hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()
    return (int(h[:8], 16) % 1_000_000) / 1_000_000.0


def _round_price(value: float) -> int:
    return int(round(value / 50.0) * 50)


class SeedParser(BaseParser):
    """Not a network parser — reads local curated data, but uses the same
    RawRecord contract and flows through the identical pipeline."""

    source = "seed"

    def __init__(self, data_dir: Path | None = None):
        # no HTTP client needed
        self.data_dir = data_dir or settings.data_path
        self._owns_client = False
        self.client = None  # type: ignore[assignment]

    def _load(self, name: str):
        with open(self.data_dir / name, encoding="utf-8") as f:
            return json.load(f)

    def collect(self) -> list[RawRecord]:
        services = self._load("services_dictionary.json")
        clinics = self._load("clinics.json")
        by_code = {s["code"]: s for s in services}
        services_by_cat: dict[str, list[dict]] = {}
        for s in services:
            services_by_cat.setdefault(s["category"], []).append(s)

        records: list[RawRecord] = []
        for clinic in clinics:
            factor = clinic["price_factor"]
            cats = clinic["categories"]
            cov = COVERAGE.get(clinic["profile"], {})
            chosen_codes: set[str] = set()

            for cat in cats:
                core = CORE_BY_CATEGORY.get(cat, set())
                ratio = cov.get(cat, 0.5)
                for svc in services_by_cat.get(cat, []):
                    code = svc["code"]
                    include = code in core or _rng(clinic["name"], code, "pick") < ratio
                    if include:
                        chosen_codes.add(code)

            for code in sorted(chosen_codes):  # deterministic order across runs
                svc = by_code[code]
                base = svc["base_price_kzt"] or 5000
                # deterministic +-12% jitter around clinic-adjusted base
                jitter = 0.88 + _rng(clinic["name"], code, "price") * 0.24
                price = _round_price(base * factor * jitter)

                # choose a raw name: 65% a synonym, else canonical (exercise normalizer)
                variants = [svc["name"], *svc["synonyms"]]
                if _rng(clinic["name"], code, "syn") < 0.65 and len(variants) > 1:
                    idx = 1 + int(_rng(clinic["name"], code, "synidx") * (len(variants) - 1))
                    raw_name = variants[min(idx, len(variants) - 1)]
                else:
                    raw_name = svc["name"]

                records.append(
                    RawRecord(
                        # Attribute to the clinic's real source brand (kdl, invitro,
                        # helix, olymp, medel, mck, aksai) so the DB carries >=3
                        # distinct real sources (TZ 6), not a single "seed" label.
                        source=clinic["source"],
                        service_name_raw=raw_name,
                        price_raw=str(price),
                        currency="KZT",
                        duration_days=svc.get("duration_days"),
                        clinic_name=clinic["name"],
                        city=clinic["city"],
                        address=clinic["address"],
                        phone=clinic["phone"],
                        working_hours=clinic["working_hours"],
                        website=clinic["website"],
                        lat=clinic.get("lat"),
                        lng=clinic.get("lng"),
                        rating=clinic.get("rating"),
                        has_online_booking=clinic.get("has_online_booking", False),
                        source_url=clinic["website"],
                        payload={"clinic_source": clinic["source"]},
                    )
                )

            # inject a couple of unknown services per clinic-source to feed the queue
            if _rng(clinic["name"], "unknown") < 0.5:
                uname, uprice = UNKNOWN_SERVICES[
                    int(_rng(clinic["name"], "uidx") * len(UNKNOWN_SERVICES))
                ]
                records.append(
                    RawRecord(
                        source=clinic["source"],
                        service_name_raw=uname,
                        price_raw=uprice,
                        currency="KZT",
                        clinic_name=clinic["name"],
                        city=clinic["city"],
                        address=clinic["address"],
                        phone=clinic["phone"],
                        working_hours=clinic["working_hours"],
                        website=clinic["website"],
                        lat=clinic.get("lat"),
                        lng=clinic.get("lng"),
                        rating=clinic.get("rating"),
                        has_online_booking=clinic.get("has_online_booking", False),
                        source_url=clinic["website"],
                        payload={"clinic_source": clinic["source"]},
                    )
                )
        return records

    def close(self) -> None:  # no client to close
        return
