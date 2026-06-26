"""RealPricesParser — ingests REAL clinic price lists (data/real_prices/).

These are actual price lists supplied for the hackathon (PDF / DOCX / XLSX / XLS)
from real Kazakhstani clinics. A `_clinics.json` sidecar maps each file to clinic
metadata. Files are parsed by the column/line-aware `real_extract` and yielded as
RawRecords, flowing through the same normalization pipeline as every other source.

Per-clinic record count is capped so a single 5000-row tariff list doesn't dominate
the DB (the cap is logged via the ParseLog record counts).
"""
from __future__ import annotations

import json
from pathlib import Path

from ..config import settings
from .base import BaseParser, RawRecord
from .real_extract import extract_real_file

PER_CLINIC_CAP = 400


class RealPricesParser(BaseParser):
    source = "real"

    def __init__(self, data_dir: Path | None = None, cap: int = PER_CLINIC_CAP):
        self._owns_client = False
        self.client = None  # type: ignore[assignment]
        self.dir = data_dir or (settings.data_path / "real_prices")
        self.cap = cap

    def collect(self) -> list[RawRecord]:
        meta_path = self.dir / "_clinics.json"
        if not meta_path.exists():
            return []
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

        records: list[RawRecord] = []
        for fname, clinic in meta.items():
            path = self.dir / fname
            if not path.exists():
                continue
            try:
                pairs = extract_real_file(str(path))
            except Exception:
                continue
            ext = path.suffix.lower().lstrip(".")
            for name, price_raw in pairs[: self.cap]:
                records.append(
                    RawRecord(
                        source=clinic["source"],
                        service_name_raw=name,
                        price_raw=price_raw,
                        currency="KZT",
                        clinic_name=clinic["clinic_name"],
                        city=clinic["city"],
                        address=clinic.get("address", ""),
                        phone=clinic.get("phone", ""),
                        working_hours=clinic.get("working_hours", ""),
                        website=clinic.get("website", ""),
                        lat=clinic.get("lat"),
                        lng=clinic.get("lng"),
                        rating=clinic.get("rating"),
                        has_online_booking=clinic.get("has_online_booking", False),
                        source_url=clinic.get("website", "") or f"file://{fname}",
                        payload={"format": ext, "file": fname, "real": True},
                    )
                )
        return records

    def close(self) -> None:
        return
