"""Live scraper for the KDL / Olymp laboratory network (kdl.kz / kdlolymp.kz)."""
from __future__ import annotations

from ..base import BaseParser, RawRecord
from ..html_extract import extract_price_pairs


class KdlParser(BaseParser):
    source = "kdl"
    base_url = "https://www.kdlolymp.kz"
    # candidate analysis-catalog pages (best effort; structure may change)
    catalog_paths = [
        "/analizy-i-tseny",
        "/analizy",
        "/price",
        "/",
    ]

    clinic_name = "KDL Olymp (онлайн-прайс)"
    city = "Алматы"

    def collect(self) -> list[RawRecord]:
        records: list[RawRecord] = []
        for path in self.catalog_paths:
            resp = self.get(path)
            if resp is None or resp.status_code != 200:
                continue
            pairs = extract_price_pairs(resp.text)
            for name, price_raw, currency in pairs:
                records.append(
                    RawRecord(
                        source=self.source,
                        service_name_raw=name,
                        price_raw=price_raw,
                        currency=currency,
                        clinic_name=self.clinic_name,
                        city=self.city,
                        website=self.base_url,
                        source_url=str(resp.url),
                    )
                )
            if records:
                break  # got a useful catalog page
        return records
