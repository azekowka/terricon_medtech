"""FixtureParser — ingests local PDF/XLSX/DOCX price lists (TZ 3.1 formats).

Represents public clinics that publish price lists as documents. Files live in
data/fixtures/ with a `_clinics.json` sidecar carrying clinic metadata. Each file
is parsed by the format-appropriate extractor and yielded as RawRecords, flowing
through the identical normalization pipeline as the web scrapers.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..config import settings
from .base import BaseParser, RawRecord
from .file_extract import extract_file


class FixtureParser(BaseParser):
    source = "fixtures"

    def __init__(self, fixtures_dir: Path | None = None):
        self._owns_client = False
        self.client = None  # type: ignore[assignment]
        self.fixtures_dir = fixtures_dir or (settings.data_path / "fixtures")

    def collect(self) -> list[RawRecord]:
        meta_path = self.fixtures_dir / "_clinics.json"
        if not meta_path.exists():
            return []
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

        records: list[RawRecord] = []
        for fname, clinic in meta.items():
            path = self.fixtures_dir / fname
            if not path.exists():
                continue
            for name, price_raw in extract_file(str(path)):
                records.append(
                    RawRecord(
                        source=clinic["source"],
                        service_name_raw=name,
                        price_raw=price_raw,
                        currency="KZT",
                        clinic_name=clinic["clinic_name"],
                        city=clinic["city"],
                        address=clinic["address"],
                        phone=clinic["phone"],
                        working_hours=clinic["working_hours"],
                        website=clinic["website"],
                        lat=clinic.get("lat"),
                        lng=clinic.get("lng"),
                        rating=clinic.get("rating"),
                        has_online_booking=clinic.get("has_online_booking", False),
                        source_url=f"{clinic['website']}/{fname}",
                        payload={"format": clinic.get("format"), "file": fname},
                    )
                )
        return records

    def close(self) -> None:
        return
