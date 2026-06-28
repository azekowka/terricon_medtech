"""In-process async parse-job manager for the admin panel.

A single job runs at a time in a daemon thread with its own DB session, exposing
live progress (phase + message tail) that the admin UI polls. SQLite WAL mode
(see db.py) keeps the rest of the API responsive while the job writes.
"""
from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone

from .db import SessionLocal
from .parsers.pipeline import (
    mark_stale_inactive,
    normalize_prices,
    rebuild_dictionary,
    run_full,
)

_lock = threading.Lock()
_job: dict | None = None


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new(kind: str, sources: list[str]) -> dict:
    return {
        "id": uuid.uuid4().hex[:12],
        "kind": kind,
        "sources": sources,
        "status": "running",  # running | done | error
        "phase": "",
        "messages": [],
        "result": None,
        "error": None,
        "started_at": _iso(),
        "finished_at": None,
    }


def get_job() -> dict | None:
    return _job


def is_running() -> bool:
    return _job is not None and _job["status"] == "running"


def _progress(state: dict):
    def cb(msg: str) -> None:
        if not msg:
            return
        if msg.startswith("Фаза"):
            state["phase"] = msg
        state["messages"].append(msg)
        # keep only the tail to bound memory
        if len(state["messages"]) > 200:
            del state["messages"][:-200]
    return cb


def _runner(state: dict, work) -> None:
    db = SessionLocal()
    try:
        state["result"] = work(db, _progress(state))
        state["status"] = "done"
        _progress(state)("Готово ✓")
    except Exception as exc:  # noqa: BLE001
        state["status"] = "error"
        state["error"] = f"{type(exc).__name__}: {exc}"
        state["messages"].append(f"Ошибка: {exc}")
    finally:
        db.close()
        state["finished_at"] = _iso()


def _start(kind: str, work, sources: list[str] | None = None) -> dict:
    global _job
    with _lock:
        if is_running():
            return _job  # type: ignore[return-value]
        state = _new(kind, sources or [])
        _job = state
    threading.Thread(target=_runner, args=(state, work), daemon=True).start()
    return state


def start_parse(sources: list[str]) -> dict:
    return _start("parse", lambda db, p: run_full(db, sources, p), sources)


def start_rebuild() -> dict:
    def work(db, p):
        d = rebuild_dictionary(db, p)
        n = normalize_prices(db, p)
        mark_stale_inactive(db)
        return {"dictionary": d, "normalization": n}

    return _start("rebuild", work)
