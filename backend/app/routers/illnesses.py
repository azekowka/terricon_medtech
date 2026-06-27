"""Diseases catalog ("Лечение заболеваний"): categories -> diseases -> disease
page with the doctors who treat it (mapped via specialty to our doctors)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Doctor, Illness
from .doctors import REGION_NAMES, _card

router = APIRouter(prefix="/api/illnesses", tags=["illnesses"])


@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    """Diseases grouped by treating specialty (a disease appears under each of its
    specialties) — powers the catalog grid + per-category disease lists."""
    rows = db.query(Illness).all()
    cats: dict[str, dict] = {}
    for ill in rows:
        for s in ill.skills or []:
            a = s.get("alias")
            if not a:
                continue
            c = cats.setdefault(a, {"alias": a, "name": s.get("name", a), "diseases": []})
            c["diseases"].append({"alias": ill.alias, "name": ill.name})
    out = sorted(cats.values(), key=lambda c: -len(c["diseases"]))
    for c in out:
        c["count"] = len(c["diseases"])
        c["diseases"].sort(key=lambda d: d["name"])
    return {"total_diseases": len(rows), "categories": out}


@router.get("")
def list_illnesses(
    q: str | None = None,
    category: str | None = None,
    limit: int = Query(300, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(Illness)
    if category:
        query = query.filter(Illness.spec_aliases.like(f"%,{category},%"))
    if q:
        query = query.filter(Illness.name.ilike(f"%{q.strip()}%"))
    rows = query.order_by(Illness.name).limit(limit).all()
    return [{"alias": i.alias, "name": i.name, "primary_skill": i.primary_skill} for i in rows]


@router.get("/{alias}")
def illness_detail(
    alias: str,
    region: str | None = None,
    db: Session = Depends(get_db),
):
    ill = db.query(Illness).filter_by(alias=alias).first()
    if not ill:
        raise HTTPException(404, "Illness not found")

    # doctors who treat it = our doctors whose specialty is among the illness's skills
    aliases = [s["alias"] for s in (ill.skills or []) if s.get("alias")]
    doctors, total = [], 0
    if aliases:
        dq = db.query(Doctor).filter(
            or_(*[Doctor.spec_aliases.like(f"%,{a},%") for a in aliases]),
            Doctor.min_price.isnot(None),
        )
        if region:
            dq = dq.filter(Doctor.region == region)
        total = dq.count()
        rows = dq.order_by(Doctor.top.desc(), Doctor.verified.desc(), Doctor.rating.desc()).limit(12).all()
        doctors = [_card(d) for d in rows]

    # resolve related diseases (only those we have in the catalog)
    sim_aliases = ill.similar or []
    sim_rows = db.query(Illness).filter(Illness.alias.in_(sim_aliases)).all() if sim_aliases else []
    similar = [{"alias": s.alias, "name": s.name} for s in sim_rows][:10]

    return {
        "id": ill.id,
        "alias": ill.alias,
        "name": ill.name,
        "skills": ill.skills or [],
        "similar": similar,
        "doctors": doctors,
        "doctors_total": total,
        "region": region,
        "region_name": REGION_NAMES.get(region) if region else None,
    }
