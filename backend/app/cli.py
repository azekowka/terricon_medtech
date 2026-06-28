"""Command-line interface for DB init, real seeding and manual parsing.

Examples:
    python -m app.cli init                       # create tables
    python -m app.cli seed                        # full bootstrap from REAL data
    python -m app.cli parse --source real idoctor # collect+build+normalize given sources
    python -m app.cli parse --live                # add the live web scrapers
    python -m app.cli rebuild-dict                # rebuild dictionary + re-normalize only
    python -m app.cli stats
"""
from __future__ import annotations

import json

from .db import SessionLocal, init_db
from .parsers.pipeline import normalize_prices, rebuild_dictionary, run_full
from .parsers.registry import DEFAULT_SOURCES, LIVE_SOURCES, LOCAL_SOURCES, PARSERS


def _p(msg):
    print(msg, flush=True)


def cmd_init(_args):
    init_db()
    _p("Database initialized (tables created).")


def cmd_seed(args):
    """Full bootstrap from real data (doctors/illnesses + real pipeline)."""
    init_db()
    db = SessionLocal()
    try:
        from .seeding import bootstrap_if_empty

        # force a full run even if partially populated
        from .doctors_loader import load_doctors
        from .illness_loader import load_illnesses
        from .models import Doctor, Illness

        if db.query(Doctor).count() == 0:
            load_doctors(db)
        if db.query(Illness).count() == 0:
            load_illnesses(db)
        sources = LOCAL_SOURCES + (LIVE_SOURCES if args.live else [])
        result = run_full(db, sources, progress=_p)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        db.close()


def cmd_parse(args):
    init_db()
    db = SessionLocal()
    try:
        sources = args.source or DEFAULT_SOURCES
        if args.live:
            sources = list(dict.fromkeys(sources + LIVE_SOURCES))
        result = run_full(db, sources, progress=_p)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        db.close()


def cmd_rebuild_dict(_args):
    init_db()
    db = SessionLocal()
    try:
        d = rebuild_dictionary(db, progress=_p)
        n = normalize_prices(db, progress=_p)
        print(json.dumps({"dictionary": d, "normalization": n}, ensure_ascii=False, indent=2))
    finally:
        db.close()


def cmd_stats(_args):
    from sqlalchemy import func

    from .models import Clinic, Price, Service, UnmatchedQueue

    init_db()
    db = SessionLocal()
    try:
        print("clinics:", db.query(func.count(Clinic.id)).scalar())
        print("cities:", db.query(func.count(func.distinct(Clinic.city))).scalar())
        print("services (dictionary):", db.query(func.count(Service.id)).scalar())
        print("active prices:", db.query(func.count(Price.id)).filter(Price.is_active.is_(True)).scalar())
        print("matched prices:", db.query(func.count(Price.id)).filter(Price.service_id.isnot(None)).scalar())
        print("sources:", db.query(func.count(func.distinct(Price.source))).scalar())
        print("unmatched pending:", db.query(func.count(UnmatchedQueue.id)).filter(UnmatchedQueue.status == "pending").scalar())
    finally:
        db.close()


def main():
    import argparse
    import sys

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # Cyrillic-safe on Windows consoles
        except Exception:
            pass

    parser = argparse.ArgumentParser(prog="medservice")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init").set_defaults(func=cmd_init)

    p_seed = sub.add_parser("seed")
    p_seed.add_argument("--live", action="store_true", help="also run live web scrapers")
    p_seed.set_defaults(func=cmd_seed)

    p_parse = sub.add_parser("parse")
    p_parse.add_argument("--source", nargs="*", choices=list(PARSERS), help="source keys")
    p_parse.add_argument("--live", action="store_true", help="add live scrapers")
    p_parse.set_defaults(func=cmd_parse)

    sub.add_parser("rebuild-dict").set_defaults(func=cmd_rebuild_dict)
    sub.add_parser("stats").set_defaults(func=cmd_stats)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
