"""Admin endpoints: manual parse trigger, logs, unmatched queue, stats (TZ 3.1/3.2)."""
from __future__ import annotations

from datetime import timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import SessionLocal, get_db
from ..models import (
    Clinic,
    ParseLog,
    Price,
    RawPrice,
    Service,
    UnmatchedQueue,
)
from ..parsers.registry import LIVE_SOURCES, PARSERS
from ..parsers.pipeline import mark_stale_inactive, run_sources
from ..schemas import ParseRequest, ResolveUnmatched

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _iso(dt):
    if dt is None:
        return None
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).isoformat()


def _run_parse_bg(sources: list[str]) -> None:
    db = SessionLocal()
    try:
        run_sources(db, sources)
    finally:
        db.close()


@router.post("/parse")
def trigger_parse(
    req: ParseRequest,
    background: bool = Query(False, description="Run asynchronously"),
    bg: BackgroundTasks = None,  # type: ignore[assignment]
    db: Session = Depends(get_db),
):
    """Manually trigger parsing (TZ 3.1: ручной запуск)."""
    sources = req.sources or ["seed"]
    if req.include_live:
        sources = list(dict.fromkeys(sources + LIVE_SOURCES))
    unknown = [s for s in sources if s not in PARSERS]
    if unknown:
        raise HTTPException(400, f"Unknown sources: {', '.join(unknown)}")

    if background and bg is not None:
        bg.add_task(_run_parse_bg, sources)
        return {"status": "scheduled", "sources": sources}

    logs = run_sources(db, sources)
    mark_stale_inactive(db)  # maintain the 30-day freshness flag (TZ 4)
    return {
        "status": "completed",
        "runs": [
            {
                "id": l.id,
                "source": l.source,
                "status": l.status,
                "records_found": l.records_found,
                "records_new": l.records_new,
                "records_updated": l.records_updated,
                "errors_count": l.errors_count,
                "message": l.message,
                "started_at": _iso(l.started_at),
                "finished_at": _iso(l.finished_at),
            }
            for l in logs
        ],
    }


@router.get("/parse-logs")
def parse_logs(limit: int = Query(30, ge=1, le=200), db: Session = Depends(get_db)):
    logs = db.query(ParseLog).order_by(ParseLog.started_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "source": l.source,
            "status": l.status,
            "records_found": l.records_found,
            "records_new": l.records_new,
            "records_updated": l.records_updated,
            "errors_count": l.errors_count,
            "message": l.message,
            "started_at": _iso(l.started_at),
            "finished_at": _iso(l.finished_at),
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
            "id": it.id,
            "service_name_raw": it.service_name_raw,
            "source": it.source,
            "occurrences": it.occurrences,
            "suggested_service_id": it.suggested_service_id,
            "suggested_service_name": svc_names.get(it.suggested_service_id),
            "suggested_score": it.suggested_score,
            "status": it.status,
            "created_at": _iso(it.created_at),
        }
        for it in items
    ]


@router.post("/unmatched/{item_id}/resolve")
def resolve_unmatched(
    item_id: str, body: ResolveUnmatched, db: Session = Depends(get_db)
):
    """Map a queued raw name to a dictionary service, learn the synonym, and
    re-link existing prices (closes the manual-labelling loop, TZ 3.2)."""
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

    # re-link existing prices that carried this raw name
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
    by_city = dict(
        db.query(Clinic.city, func.count(Clinic.id)).group_by(Clinic.city).all()
    )
    by_source = dict(
        db.query(Price.source, func.count(Price.id))
        .filter(Price.is_active.is_(True))
        .group_by(Price.source)
        .all()
    )
    by_category = dict(
        db.query(Price.category, func.count(Price.id))
        .filter(Price.is_active.is_(True))
        .group_by(Price.category)
        .all()
    )
    return {
        "clinics": db.query(func.count(Clinic.id)).scalar() or 0,
        "services": db.query(func.count(Service.id)).scalar() or 0,
        "active_prices": db.query(func.count(Price.id)).filter(Price.is_active.is_(True)).scalar() or 0,
        "raw_rows": db.query(func.count(RawPrice.id)).scalar() or 0,
        "matched_prices": db.query(func.count(Price.id)).filter(Price.service_id.isnot(None)).scalar() or 0,
        "unmatched_pending": db.query(func.count(UnmatchedQueue.id)).filter(UnmatchedQueue.status == "pending").scalar() or 0,
        "clinics_by_city": by_city,
        "prices_by_source": by_source,
        "prices_by_category": by_category,
    }
