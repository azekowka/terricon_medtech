"""Registry mapping source keys to parser implementations.

Adding a new source = add one entry here (TZ 4: extensibility without touching
the core pipeline)."""
from __future__ import annotations

from .base import BaseParser
from .fixtures import FixtureParser
from .live import HelixParser, InvitroParser, KdlParser
from .real_prices import RealPricesParser
from .seed_source import SeedParser

PARSERS: dict[str, type[BaseParser]] = {
    "seed": SeedParser,
    "fixtures": FixtureParser,  # PDF/XLSX/DOCX sample price lists (TZ 3.1 formats)
    "real": RealPricesParser,   # REAL clinic price lists (PDF/DOCX/XLSX/XLS)
    "kdl": KdlParser,
    "invitro": InvitroParser,
    "helix": HelixParser,
}

# Sources that hit the network (vs. the local curated "seed" source).
LIVE_SOURCES = ["kdl", "invitro", "helix"]


def get_parser(source: str) -> BaseParser:
    if source not in PARSERS:
        raise KeyError(f"Unknown source '{source}'. Known: {', '.join(PARSERS)}")
    return PARSERS[source]()
