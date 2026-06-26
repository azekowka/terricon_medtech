"""Command-line interface for DB init, seeding and manual parsing.

Examples:
    python -m app.cli init
    python -m app.cli seed                 # dictionary + seed source
    python -m app.cli seed --live          # also run live web scrapers
    python -m app.cli parse --source kdl invitro
    python -m app.cli stats
"""
from __future__ import annotations

import argparse
import json

from .db import SessionLocal, init_db
from .parsers.pipeline import run_sources
from .parsers.registry import LIVE_SOURCES, PARSERS
from .seeding import load_dictionary, seed_database


def cmd_init(_args):
    init_db()
    print("Database initialized (tables created).")


def cmd_seed(args):
    init_db()
    db = SessionLocal()
    try:
        result = seed_database(db, include_live=args.live)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        db.close()


def cmd_parse(args):
    init_db()
    db = SessionLocal()
    try:
        load_dictionary(db)  # ensure dictionary present for normalization
        sources = args.source or ["seed"]
        if args.live:
            sources = list(dict.fromkeys(sources + LIVE_SOURCES))
        logs = run_sources(db, sources)
        for l in logs:
            print(
                f"[{l.source}] {l.status} found={l.records_found} "
                f"new={l.records_new} updated={l.records_updated} errors={l.errors_count}"
            )
    finally:
        db.close()


def cmd_stats(_args):
    from sqlalchemy import func

    from .models import Clinic, Price, Service, UnmatchedQueue

    init_db()
    db = SessionLocal()
    try:
        print("clinics:", db.query(func.count(Clinic.id)).scalar())
        print("services:", db.query(func.count(Service.id)).scalar())
        print("active prices:", db.query(func.count(Price.id)).filter(Price.is_active.is_(True)).scalar())
        print("matched prices:", db.query(func.count(Price.id)).filter(Price.service_id.isnot(None)).scalar())
        print("unmatched pending:", db.query(func.count(UnmatchedQueue.id)).filter(UnmatchedQueue.status == "pending").scalar())
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(prog="medservice")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init").set_defaults(func=cmd_init)

    p_seed = sub.add_parser("seed")
    p_seed.add_argument("--live", action="store_true", help="also run live scrapers")
    p_seed.set_defaults(func=cmd_seed)

    p_parse = sub.add_parser("parse")
    p_parse.add_argument("--source", nargs="*", choices=list(PARSERS), help="source keys")
    p_parse.add_argument("--live", action="store_true", help="add live scrapers")
    p_parse.set_defaults(func=cmd_parse)

    sub.add_parser("stats").set_defaults(func=cmd_stats)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
