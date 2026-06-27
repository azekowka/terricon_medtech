"""Load the scraped disease catalog (data/diseases/diseases.json) into Illness."""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from .config import settings
from .models import Illness


def _path():
    return settings.data_path / "diseases" / "diseases.json"


def load_illnesses(db: Session) -> int:
    path = _path()
    if not path.exists():
        return 0
    items = json.load(open(path, encoding="utf-8"))
    db.query(Illness).delete()
    db.commit()
    batch, n = [], 0
    for it in items:
        if not it.get("id") or not it.get("alias"):
            continue
        skills = it.get("skills") or []
        aliases = [s["alias"] for s in skills if s.get("alias")]
        batch.append(dict(
            id=it["id"],
            alias=it["alias"],
            name=it.get("name") or it["alias"],
            skills=skills,
            similar=it.get("similar") or [],
            spec_aliases="," + ",".join(aliases) + "," if aliases else ",",
            primary_skill=skills[0]["name"] if skills else None,
            primary_skill_alias=skills[0]["alias"] if skills else None,
        ))
        n += 1
        if len(batch) >= 2000:
            db.bulk_insert_mappings(Illness, batch)
            db.commit()
            batch = []
    if batch:
        db.bulk_insert_mappings(Illness, batch)
        db.commit()
    return n
