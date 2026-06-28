"""DoctorsClinicsParser — derives REAL clinics + "приём врача" prices from the
scraped idoctor dataset (data/doctors/doctors.json).

Every doctor carries their medcenters (name, address, geo, online-booking) and
an appointment price. Aggregating those by (clinic, city, specialty) -> min price
yields thousands of real clinics and "doctor visit" prices across all 18 KZ
regions — the platform's biggest real-coverage source, all from open data that we
already collected (idoctor.kz).

This is a local source (no network at parse time): it reads the JSON the idoctor
scraper produced and flows through the exact same pipeline as every other source.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..config import settings
from .base import BaseParser, RawRecord

# Region slug -> Russian city name fallback when a doctor has no explicit city.
REGION_NAMES = {
    "almaty": "Алматы", "astana": "Астана", "shymkent": "Шымкент",
    "karaganda": "Караганда", "aktobe": "Актобе", "taraz": "Тараз",
    "pavlodar": "Павлодар", "ust-kamenogorsk": "Усть-Каменогорск",
    "semey": "Семей", "kostanay": "Костанай", "kyzylorda": "Кызылорда",
    "uralsk": "Уральск", "petropavlovsk": "Петропавловск", "aktau": "Актау",
    "kokshetau": "Кокшетау", "taldykorgan": "Талдыкорган",
    "turkestan": "Туркестан", "ekibastuz": "Экибастуз",
}


class DoctorsClinicsParser(BaseParser):
    source = "idoctor"

    def __init__(self, data_dir: Path | None = None):
        # local source — no HTTP client
        self._owns_client = False
        self.client = None  # type: ignore[assignment]
        self.path = (data_dir or settings.data_path) / "doctors" / "doctors.json"

    @staticmethod
    def _specialty(d: dict) -> str | None:
        specs = d.get("specialties") or []
        if specs and specs[0].get("name"):
            return specs[0]["name"].strip()
        return None

    @staticmethod
    def _num(v) -> float | None:
        """Coerce a geo/price value to float; idoctor sometimes carries the literal
        placeholders 'latitude'/'longitude' instead of numbers."""
        try:
            f = float(v)
            return f if f == f else None  # drop NaN
        except (TypeError, ValueError):
            return None

    def collect(self) -> list[RawRecord]:
        if not self.path.exists():
            return []
        with open(self.path, encoding="utf-8") as f:
            doctors = json.load(f)

        # Aggregate by (clinic_name, city, specialty) -> cheapest appointment.
        # agg[key] = {price, clinic metadata}; clinic rating = mean of its doctors' ratings.
        agg: dict[tuple[str, str, str], dict] = {}
        clinic_rating: dict[tuple[str, str], list] = {}  # (name, city) -> [sum, count]
        for d in doctors:
            spec = self._specialty(d)
            if not spec:
                continue
            city = (d.get("city") or REGION_NAMES.get(d.get("region", ""), "") or "").strip()
            if not city:
                continue
            d_rating = self._num(d.get("rating"))
            for c in d.get("clinics") or []:
                name = (c.get("name") or "").strip()
                if not name:
                    continue
                if d_rating is not None and 0 < d_rating <= 5:
                    acc = clinic_rating.setdefault((name, city), [0.0, 0])
                    acc[0] += d_rating
                    acc[1] += 1
                price = self._num(c.get("price_discount") or c.get("price"))
                # sane bounds for a doctor appointment — drops junk outliers
                if not price or not (100 <= price <= 200_000):
                    continue
                key = (name, city, spec)
                cur = agg.get(key)
                if cur is None or price < cur["price"]:
                    agg[key] = {
                        "price": price,
                        "address": c.get("address") or "",
                        "lat": self._num(c.get("lat")),
                        "lng": self._num(c.get("lng")),
                        "online_booking": bool(c.get("online_booking")),
                    }

        records: list[RawRecord] = []
        for (clinic_name, city, spec), v in agg.items():
            racc = clinic_rating.get((clinic_name, city))
            rating = round(racc[0] / racc[1], 1) if racc and racc[1] else None
            records.append(
                RawRecord(
                    source=self.source,
                    # Specialty is the distinguishing token; "приём врача" is treated
                    # as noise by the normalizer, so visits cluster by specialty.
                    service_name_raw=f"Приём врача ({spec})",
                    price_raw=str(int(round(v["price"]))),
                    currency="KZT",
                    clinic_name=clinic_name,
                    city=city,
                    address=v["address"],
                    lat=v["lat"],
                    lng=v["lng"],
                    rating=rating,
                    has_online_booking=v["online_booking"],
                    # No public clinic website -> keep users on our own clinic page.
                    website="",
                    source_url="",
                    payload={"category_hint": "doctor", "specialty": spec, "real": True},
                )
            )
        return records

    def close(self) -> None:
        return
