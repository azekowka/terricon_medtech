"""Registry mapping source keys to parser implementations.

Adding a new source = add one entry here (TZ 4: extensibility without touching
the core pipeline). NO synthetic/seed sources — every source is real:

  * real     — real clinic price files (PDF/DOCX/XLSX/XLS) we parse
  * idoctor  — real clinics + "приём врача" prices derived from the idoctor dataset
  * live web — real public clinic/lab sites
"""
from __future__ import annotations

from .base import BaseParser
from .doctors_source import DoctorsClinicsParser
from .live import LIVE_PARSERS
from .real_prices import RealPricesParser

PARSERS: dict[str, type[BaseParser]] = {
    "real": RealPricesParser,        # real clinic price lists (files)
    "idoctor": DoctorsClinicsParser,  # real clinics + visit prices, 18 regions
    **{p.source: p for p in LIVE_PARSERS},  # kdl, invitro, helix, olymp, medel, mck, aksai, doq
}

# Always-available local sources (no network) — the reliable demo backbone.
LOCAL_SOURCES = ["real", "idoctor"]

# Sources that hit the network (best-effort, fault tolerant).
LIVE_SOURCES = [p.source for p in LIVE_PARSERS]

# Default when the admin/CLI does not specify: everything we can reach.
DEFAULT_SOURCES = LOCAL_SOURCES + LIVE_SOURCES


def get_parser(source: str) -> BaseParser:
    if source not in PARSERS:
        raise KeyError(f"Unknown source '{source}'. Known: {', '.join(PARSERS)}")
    return PARSERS[source]()
