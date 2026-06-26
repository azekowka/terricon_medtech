"""Heuristic HTML -> (service_name, price) extraction shared by live parsers.

Clinic price pages vary wildly (tables, cards, definition lists), so we use a
couple of robust heuristics rather than brittle per-site CSS selectors:

  1. Table rows: a row where one cell looks like a price and another like a name.
  2. Price-labelled elements: an element whose text contains a tenge price, paired
     with the nearest preceding text that looks like a service name.

Returns list of (name, price_raw, currency).
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

# 1 200 ₸ / 1200 тг / 1 200 тенге / 1200 KZT / от 3 500 тг
PRICE_RE = re.compile(
    r"(\d[\d\s.,]{0,15}\d|\d)\s*(₸|тг\.?|тенге|kzt)",
    re.IGNORECASE,
)
# fallback: a bare 3-6 digit number (used only inside price-labelled contexts)
BARE_NUM_RE = re.compile(r"\b(\d[\d\s ]{2,6}\d)\b")

_NAME_OK = re.compile(r"[А-Яа-яЁё]{3,}")


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\xa0", " ")).strip()


def _is_price_text(text: str) -> bool:
    return bool(PRICE_RE.search(text or ""))


def _looks_like_name(text: str) -> bool:
    text = _clean(text)
    return len(text) >= 4 and bool(_NAME_OK.search(text)) and not _is_price_text(text)


def extract_from_tables(soup: BeautifulSoup) -> list[tuple[str, str, str]]:
    pairs: list[tuple[str, str, str]] = []
    for row in soup.find_all("tr"):
        cells = [_clean(c.get_text(" ")) for c in row.find_all(["td", "th"])]
        if len(cells) < 2:
            continue
        price_cell = next((c for c in cells if _is_price_text(c)), None)
        if not price_cell:
            continue
        name_cell = next((c for c in cells if _looks_like_name(c)), None)
        if not name_cell:
            continue
        m = PRICE_RE.search(price_cell)
        if m:
            pairs.append((name_cell, m.group(1), "KZT"))
    return pairs


def extract_from_price_labels(soup: BeautifulSoup) -> list[tuple[str, str, str]]:
    pairs: list[tuple[str, str, str]] = []
    # elements whose class/text suggests a price
    candidates = soup.find_all(
        lambda t: isinstance(t, Tag)
        and t.name in {"span", "div", "p", "b", "strong"}
        and _is_price_text(t.get_text(" "))
    )
    for el in candidates:
        m = PRICE_RE.search(_clean(el.get_text(" ")))
        if not m:
            continue
        name = _nearest_name(el)
        if name:
            pairs.append((name, m.group(1), "KZT"))
    return pairs


def _nearest_name(el: Tag) -> str | None:
    """Walk up/back to find the nearest service-name-like text."""
    # try previous siblings
    for sib in el.find_all_previous(string=True, limit=8):
        text = _clean(str(sib))
        if _looks_like_name(text):
            return text
    # try parent container's heading
    parent = el.parent
    for _ in range(3):
        if parent is None:
            break
        heading = parent.find(["h1", "h2", "h3", "h4", "a", "span"])
        if heading is not None:
            text = _clean(heading.get_text(" "))
            if _looks_like_name(text):
                return text
        parent = parent.parent
    return None


def extract_price_pairs(html: str) -> list[tuple[str, str, str]]:
    """Return de-duplicated (name, price_raw, currency) pairs from a page."""
    soup = BeautifulSoup(html, "lxml")
    pairs = extract_from_tables(soup)
    if len(pairs) < 3:
        pairs += extract_from_price_labels(soup)
    # de-dup by normalized name keeping first price
    seen: set[str] = set()
    out: list[tuple[str, str, str]] = []
    for name, price, cur in pairs:
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append((name, price, cur))
    return out
