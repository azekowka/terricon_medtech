"""Parser base class and the raw-record contract.

Every source parser yields `RawRecord`s; the pipeline is responsible for
normalization, dedup and persistence. Parsers must:
  * be polite (delay between requests, TZ 8)
  * respect robots.txt (TZ 8)
  * never raise out of `collect()` — failures are logged and the source is
    skipped so the rest keep running (TZ 4: fault tolerance)
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

DEFAULT_HEADERS = {
    "User-Agent": (
        "MedServicePriceBot/1.0 (+https://medserviceprice.kz; hackathon MVP; "
        "respects robots.txt)"
    ),
    "Accept-Language": "ru,kk;q=0.9,en;q=0.8",
}


@dataclass
class RawRecord:
    """One raw price observation as scraped, before normalization."""

    source: str
    service_name_raw: str
    price_raw: str
    # clinic identity / metadata
    clinic_name: str = ""
    city: str = ""
    address: str = ""
    phone: str = ""
    working_hours: str = ""
    website: str = ""
    lat: float | None = None
    lng: float | None = None
    rating: float | None = None
    has_online_booking: bool = False
    # service metadata
    currency: str = "KZT"
    duration_days: int | None = None
    source_url: str = ""
    payload: dict = field(default_factory=dict)


class BaseParser:
    """Base HTTP parser with politeness + robots.txt handling."""

    source: str = ""
    base_url: str = ""
    request_delay: float = 1.2  # seconds between requests (TZ 8)

    def __init__(self, client: httpx.Client | None = None, delay: float | None = None):
        self.client = client or httpx.Client(
            headers=DEFAULT_HEADERS, timeout=20.0, follow_redirects=True
        )
        self._owns_client = client is None
        if delay is not None:
            self.request_delay = delay
        self._robots: RobotFileParser | None = None
        self._last_request = 0.0

    # ---- robots.txt -------------------------------------------------------
    def _load_robots(self) -> None:
        if self._robots is not None or not self.base_url:
            return
        rp = RobotFileParser()
        robots_url = urljoin(self.base_url, "/robots.txt")
        try:
            resp = self.client.get(robots_url, timeout=10.0)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
            else:
                rp.parse([])  # no robots -> allow
        except Exception:
            rp.parse([])  # unreachable robots -> be permissive but still polite
        self._robots = rp
        # The robots.txt fetch is a real request to the host — count it so the
        # first catalog GET still waits request_delay (TZ 8 politeness).
        self._last_request = time.monotonic()

    def robots_allows(self, url: str) -> bool:
        self._load_robots()
        if self._robots is None:
            return True
        ua = DEFAULT_HEADERS["User-Agent"]
        try:
            return self._robots.can_fetch(ua, url)
        except Exception:
            return True

    # ---- polite GET -------------------------------------------------------
    def _effective_delay(self) -> float:
        """Honor the site's published Crawl-delay if it exceeds our floor (TZ 8)."""
        delay = self.request_delay
        if self._robots is not None:
            try:
                cd = self._robots.crawl_delay(DEFAULT_HEADERS["User-Agent"])
                if cd:
                    delay = max(delay, float(cd))
            except Exception:
                pass
        return delay

    def get(self, url: str) -> httpx.Response | None:
        """Polite GET honoring robots.txt and the configured delay."""
        full = url if urlparse(url).netloc else urljoin(self.base_url, url)
        if not self.robots_allows(full):
            return None
        delay = self._effective_delay()
        elapsed = time.monotonic() - self._last_request
        if elapsed < delay:
            time.sleep(delay - elapsed)
        try:
            resp = self.client.get(full)
            self._last_request = time.monotonic()
            return resp
        except Exception:
            self._last_request = time.monotonic()
            return None

    # ---- to be implemented by subclasses ----------------------------------
    def collect(self) -> list[RawRecord]:
        raise NotImplementedError

    def close(self) -> None:
        if self._owns_client:
            self.client.close()


# ---- shared parsing helpers ----------------------------------------------
_NUM_RE = re.compile(r"\d[\d\s.,]*\d|\d")


def parse_price(raw: str) -> float | None:
    """Extract a numeric price from messy strings.

    Correctly handles space / NBSP / dot / comma thousands separators and
    decimal commas (common on KZT price pages):
        "2 200 KZT" -> 2200      "ot 3 500 tg" -> 3500
        "1.200" -> 1200          "1 200,50"    -> 1200.5
        "1,200.00" -> 1200.0     "99.99"       -> 99.99
    """
    if raw is None:
        return None
    m = _NUM_RE.search(str(raw))
    if not m:
        return None
    # drop every whitespace char (space, NBSP, thin space) used as a grouping sep
    num = "".join(m.group(0).split())

    has_dot, has_comma = "." in num, "," in num
    if has_dot and has_comma:
        # the right-most separator is the decimal point
        if num.rfind(".") > num.rfind(","):
            num = num.replace(",", "")                    # comma = thousands
        else:
            num = num.replace(".", "").replace(",", ".")  # dot = thousands
    elif has_comma:
        head, _, tail = num.rpartition(",")
        num = f"{head}.{tail}" if len(tail) in (1, 2) else num.replace(",", "")
    elif has_dot:
        head, _, tail = num.rpartition(".")
        if len(tail) not in (1, 2):
            num = num.replace(".", "")                     # dot = thousands

    try:
        return float(num)
    except ValueError:
        return None
