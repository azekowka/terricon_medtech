"""Admin endpoints: live async parse, dictionary rebuild, AI assist, queue, stats.

The dictionary is built FROM the collected data (TZ 3.2), so the admin exposes
three actions: run the full pipeline (collect → build dictionary → normalize),
rebuild the dictionary only, and AI-assist the unmatched queue. Parsing runs in a
background thread with live progress the UI polls.
"""
from __future__ import annotations

from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import parse_jobs
from ..db import get_db
from ..models import Clinic, ParseLog, Price, RawPrice, Service, UnmatchedQueue
from ..parsers.registry import LIVE_SOURCES, LOCAL_SOURCES, PARSERS
from ..schemas import ParseRequest, ResolveUnmatched

router = APIRouter(prefix="/api/admin", tags=["admin"])

SOURCE_LABELS = {
    "real": "Реальные прайс-файлы клиник (PDF/DOCX/XLSX)",
    "idoctor": "Клиники и приёмы врачей (idoctor, 18 регионов)",
    "kdl": "KDL / Olymp (kdlolymp.kz)",
    "invitro": "INVITRO (invitro.kz)",
    "helix": "Helix (helix.kz)",
    "olymp": "Олимп (olymp.kz)",
    "medel": "МЕДЭЛ (medel.kz)",
    "mck": "МЦК (mck.kz)",
    "aksai": "Аксай (aksai-clinic.kz)",
    "doq": "doq.kz (агрегатор)",
}


def _iso(dt):
    if dt is None:
        return None
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).isoformat()


@router.get("/sources")
def sources():
    """Available parse sources for the admin source picker."""
    return [
        {
            "key": k,
            "label": SOURCE_LABELS.get(k, k),
            "kind": "local" if k in LOCAL_SOURCES else "live",
        }
        for k in PARSERS
    ]


@router.post("/parse")
def trigger_parse(req: ParseRequest):
    """Start the full real pipeline (collect → build dictionary → normalize)
    asynchronously. Returns the job id; poll /api/admin/job for live progress."""
    if parse_jobs.is_running():
        return {"status": "already_running", "job": _job_view(parse_jobs.get_job())}
    sources = req.sources or list(LOCAL_SOURCES)
    if req.include_live:
        sources = list(dict.fromkeys(sources + LIVE_SOURCES))
    unknown = [s for s in sources if s not in PARSERS]
    if unknown:
        raise HTTPException(400, f"Unknown sources: {', '.join(unknown)}")
    job = parse_jobs.start_parse(sources)
    return {"status": "started", "job": _job_view(job)}


@router.post("/rebuild-dict")
def rebuild_dict():
    """Rebuild the dictionary from existing raw data + re-normalize (no re-collect)."""
    if parse_jobs.is_running():
        return {"status": "already_running", "job": _job_view(parse_jobs.get_job())}
    job = parse_jobs.start_rebuild()
    return {"status": "started", "job": _job_view(job)}


def _job_view(job: dict | None) -> dict | None:
    if not job:
        return None
    return {
        "id": job["id"],
        "kind": job["kind"],
        "sources": job["sources"],
        "status": job["status"],
        "phase": job["phase"],
        "messages": job["messages"][-40:],
        "result": job["result"],
        "error": job["error"],
        "started_at": job["started_at"],
        "finished_at": job["finished_at"],
    }


@router.get("/job")
def job_status():
    """Current/last parse job state for live progress polling."""
    return {"running": parse_jobs.is_running(), "job": _job_view(parse_jobs.get_job())}


@router.post("/ai-assist")
def ai_assist(limit: int = Query(40, ge=1, le=200), db: Session = Depends(get_db)):
    """AI-assisted resolution of the unmatched queue (TZ 3.2 — AI optional)."""
    from ..ai_assist import assist_unmatched

    return assist_unmatched(db, limit=limit)


@router.get("/parse-logs")
def parse_logs(limit: int = Query(30, ge=1, le=200), db: Session = Depends(get_db)):
    logs = db.query(ParseLog).order_by(ParseLog.started_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id, "source": l.source, "status": l.status,
            "records_found": l.records_found, "records_new": l.records_new,
            "records_updated": l.records_updated, "errors_count": l.errors_count,
            "message": l.message, "started_at": _iso(l.started_at), "finished_at": _iso(l.finished_at),
        }
        for l in logs
    ]


@router.get("/unmatched")
def unmatched(
    status: str = Query("pending"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(UnmatchedQueue)
    if status != "all":
        q = q.filter(UnmatchedQueue.status == status)
    items = q.order_by(UnmatchedQueue.occurrences.desc()).limit(limit).all()
    svc_names = dict(db.query(Service.id, Service.name).all())
    return [
        {
            "id": it.id, "service_name_raw": it.service_name_raw, "source": it.source,
            "occurrences": it.occurrences, "suggested_service_id": it.suggested_service_id,
            "suggested_service_name": svc_names.get(it.suggested_service_id),
            "suggested_score": it.suggested_score, "status": it.status,
            "created_at": _iso(it.created_at),
        }
        for it in items
    ]


@router.post("/unmatched/{item_id}/resolve")
def resolve_unmatched(item_id: str, body: ResolveUnmatched, db: Session = Depends(get_db)):
    """Map a queued raw name to a dictionary service, learn the synonym, re-link
    existing prices (closes the manual-labelling loop, TZ 3.2)."""
    item = db.query(UnmatchedQueue).filter_by(id=item_id).first()
    if not item:
        raise HTTPException(404, "Queue item not found")
    service = db.query(Service).filter_by(id=body.service_id).first()
    if not service:
        raise HTTPException(404, "Service not found")

    if body.add_synonym:
        syns = list(service.synonyms or [])
        if item.service_name_raw not in syns:
            syns.append(item.service_name_raw)
            service.synonyms = syns

    relinked = 0
    rows = (
        db.query(Price)
        .filter(Price.service_name_raw == item.service_name_raw, Price.service_id.is_(None))
        .all()
    )
    for p in rows:
        p.service_id = service.id
        p.service_name_norm = service.name
        p.category = service.category
        relinked += 1

    item.status = "resolved"
    item.suggested_service_id = service.id
    db.commit()
    return {"status": "resolved", "service_id": service.id, "prices_relinked": relinked}


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    by_city = dict(db.query(Clinic.city, func.count(Clinic.id)).group_by(Clinic.city).all())
    by_source = dict(
        db.query(Price.source, func.count(Price.id))
        .filter(Price.is_active.is_(True)).group_by(Price.source).all()
    )
    by_category = dict(
        db.query(Price.category, func.count(Price.id))
        .filter(Price.is_active.is_(True)).group_by(Price.category).all()
    )
    return {
        "clinics": db.query(func.count(Clinic.id)).scalar() or 0,
        "cities": db.query(func.count(func.distinct(Clinic.city))).scalar() or 0,
        "services": db.query(func.count(Service.id)).scalar() or 0,
        "active_prices": db.query(func.count(Price.id)).filter(Price.is_active.is_(True)).scalar() or 0,
        "raw_rows": db.query(func.count(RawPrice.id)).scalar() or 0,
        "sources": db.query(func.count(func.distinct(Price.source))).filter(Price.is_active.is_(True)).scalar() or 0,
        "matched_prices": db.query(func.count(Price.id)).filter(Price.service_id.isnot(None)).scalar() or 0,
        "unmatched_pending": db.query(func.count(UnmatchedQueue.id)).filter(UnmatchedQueue.status == "pending").scalar() or 0,
        "clinics_by_city": by_city,
        "prices_by_source": by_source,
        "prices_by_category": by_category,
    }
