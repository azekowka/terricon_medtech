"""Best-effort live scrapers for real Kazakhstani clinic/lab sites.

These run against the real public websites. Because the sites are JS-heavy and
occasionally geo-restricted, the scrapers fail gracefully (return whatever they
could extract; the pipeline logs partial/empty runs and keeps going). The bulk
of demo data is provided by the deterministic `seed` source, which exercises the
exact same normalization pipeline.
"""
from .helix import HelixParser
from .invitro import InvitroParser
from .kdl import KdlParser

__all__ = ["KdlParser", "InvitroParser", "HelixParser"]
