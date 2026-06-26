"""Service-name normalizer.

Maps a heterogeneous raw service name (e.g. "ОАК", "CBC", "Клинический анализ
крови") to a single canonical dictionary service (TZ 3.2).

Strategy (cheap -> expensive):
  1. Exact match against the normalized synonym/name index   -> score 100
  2. Fuzzy match (rapidfuzz WRatio) against all index keys    -> best score
  3. Below the configured threshold -> no match (unmatched queue)

The matcher is built from the live `services` table, so edits made through the
admin UI immediately affect normalization.
"""
from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz, process

from ..config import settings
from .text import normalize_text


@dataclass
class MatchResult:
    service_id: str | None
    code: str | None
    name: str | None
    category: str | None
    score: float
    matched_by: str  # "exact" | "fuzzy" | "none"

    @property
    def matched(self) -> bool:
        return self.service_id is not None


@dataclass
class _Entry:
    service_id: str
    code: str
    name: str
    category: str


class Normalizer:
    def __init__(self, services: list[dict], threshold: int | None = None):
        """services: list of dicts with id, code, name, category, synonyms."""
        self.threshold = threshold if threshold is not None else settings.match_threshold
        # index: normalized_key -> _Entry
        self._index: dict[str, _Entry] = {}
        for s in services:
            entry = _Entry(
                service_id=s["id"], code=s["code"], name=s["name"], category=s["category"]
            )
            keys = [s["name"], *(s.get("synonyms") or [])]
            for key in keys:
                nk = normalize_text(key)
                if nk and nk not in self._index:
                    self._index[nk] = entry
        self._keys = list(self._index.keys())

    def match(self, raw_name: str) -> MatchResult:
        nk = normalize_text(raw_name)
        if not nk:
            return MatchResult(None, None, None, None, 0.0, "none")

        # 1. exact
        if nk in self._index:
            e = self._index[nk]
            return MatchResult(e.service_id, e.code, e.name, e.category, 100.0, "exact")

        # 2. fuzzy
        if not self._keys:
            return MatchResult(None, None, None, None, 0.0, "none")
        best = process.extractOne(nk, self._keys, scorer=fuzz.WRatio)
        if best is not None:
            key, score, _ = best
            if score >= self.threshold:
                e = self._index[key]
                return MatchResult(e.service_id, e.code, e.name, e.category, float(score), "fuzzy")
            # return the best suggestion even if below threshold (for the queue)
            e = self._index[key]
            return MatchResult(None, e.code, e.name, e.category, float(score), "none")

        return MatchResult(None, None, None, None, 0.0, "none")

    def suggest(self, raw_name: str) -> tuple[str | None, float]:
        """Best (service_id, score) even below threshold — used to seed the queue."""
        nk = normalize_text(raw_name)
        if not nk or not self._keys:
            return None, 0.0
        best = process.extractOne(nk, self._keys, scorer=fuzz.WRatio)
        if best is None:
            return None, 0.0
        key, score, _ = best
        return self._index[key].service_id, float(score)


def build_normalizer_from_db(db) -> Normalizer:
    """Construct a Normalizer from the live services dictionary table."""
    from ..models import Service

    rows = db.query(Service).all()
    services = [
        {
            "id": r.id,
            "code": r.code,
            "name": r.name,
            "category": r.category,
            "synonyms": r.synonyms or [],
        }
        for r in rows
    ]
    return Normalizer(services)
