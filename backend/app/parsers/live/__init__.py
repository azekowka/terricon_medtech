"""Best-effort live scrapers for real Kazakhstani clinic/lab sites (TZ §2.1).

They run against the real public websites. Because the sites are JS-heavy and
occasionally geo-restricted, the scrapers fail gracefully (return whatever they
could extract; the pipeline logs partial/empty runs and keeps going, TZ 4). They
are bonus coverage on top of the always-available real files + idoctor sources.
"""
from .sites import (
    AksaiParser,
    DoqParser,
    HelixParser,
    InvitroParser,
    KdlParser,
    LIVE_PARSERS,
    MckParser,
    MedelParser,
    OlympParser,
)

__all__ = [
    "KdlParser", "InvitroParser", "HelixParser", "OlympParser",
    "MedelParser", "MckParser", "AksaiParser", "DoqParser", "LIVE_PARSERS",
]
