"""Generic live clinic/lab scraper.

A site is described declaratively (base URL, candidate catalogue paths, clinic
identity, whether it needs JS rendering). `collect()` tries each path politely
(httpx, then a headless browser if `render` is set), runs the shared heuristic
HTML→(name, price) extractor, and stops at the first page that yields data.

Adding a source = a ~8-line subclass (TZ 4: extensibility without touching core).
Everything is best-effort and fault tolerant: an unreachable/JS-only/blocked site
just returns [] and the pipeline logs a partial run and moves on.
"""
from __future__ import annotations

from urllib.parse import urljoin

from ..base import BaseParser, RawRecord
from ..html_extract import extract_price_pairs


class GenericLiveParser(BaseParser):
    source = ""
    base_url = ""
    catalog_paths: list[str] = ["/"]
    clinic_name = ""
    city = "Алматы"
    address = ""
    website = ""
    render = False
    request_delay = 1.5
    min_records = 3  # stop once a page yields at least this many pairs

    def collect(self) -> list[RawRecord]:
        records: list[RawRecord] = []
        for path in self.catalog_paths:
            html = self.get_html(path, render=self.render)
            if not html:
                continue
            pairs = extract_price_pairs(html)
            for name, price_raw, currency in pairs:
                records.append(
                    RawRecord(
                        source=self.source,
                        service_name_raw=name,
                        price_raw=price_raw,
                        currency=currency,
                        clinic_name=self.clinic_name,
                        city=self.city,
                        address=self.address,
                        website=self.website or self.base_url,
                        source_url=urljoin(self.base_url, path),
                        payload={"live": True},
                    )
                )
            if len(records) >= self.min_records:
                break
        return records
