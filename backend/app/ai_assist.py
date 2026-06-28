"""Optional AI-assisted resolution of the unmatched queue (TZ 3.2 — AI allowed).

Algorithmic clustering is the always-on backbone; this is the "hybrid" AI step:
for each queued raw name we offer the LLM a few fuzzy candidate services and ask
it to pick the right one (or none). Confident picks are resolved like a manual
review (synonym learned + prices relinked). Degrades gracefully with no API key.
"""
from __future__ import annotations

import json
import re

from rapidfuzz import fuzz, process
from sqlalchemy.orm import Session

from .models import Price, Service, UnmatchedQueue
from .normalization.text import normalize_text


def _candidates(services: list[Service], raw: str, k: int = 5) -> list[Service]:
    keys = [normalize_text(s.name) for s in services]
    hits = process.extract(normalize_text(raw), keys, scorer=fuzz.token_set_ratio, limit=k)
    return [services[i] for _, _, i in hits]


def _resolve(db: Session, item: UnmatchedQueue, service: Service) -> int:
    syns = list(service.synonyms or [])
    if item.service_name_raw not in syns:
        syns.append(item.service_name_raw)
        service.synonyms = syns
    relinked = 0
    for p in db.query(Price).filter(
        Price.service_name_raw == item.service_name_raw, Price.service_id.is_(None)
    ).all():
        p.service_id = service.id
        p.service_name_norm = service.name
        p.category = service.category
        relinked += 1
    item.status = "resolved"
    item.suggested_service_id = service.id
    return relinked


def assist_unmatched(db: Session, limit: int = 40) -> dict:
    from .llm import available, chat_completion

    pending = (
        db.query(UnmatchedQueue)
        .filter_by(status="pending")
        .order_by(UnmatchedQueue.occurrences.desc())
        .limit(limit)
        .all()
    )
    if not pending:
        return {"ok": True, "resolved": 0, "message": "Очередь пуста — нечего размечать."}
    if not available():
        return {
            "ok": False,
            "reason": "no_api_key",
            "resolved": 0,
            "message": "AI-разметка недоступна: не задан OPENAI_API_KEY. "
                       "Алгоритмическая нормализация уже применена.",
        }

    services = db.query(Service).all()
    by_id = {s.id: s for s in services}

    tasks = []
    for it in pending:
        cands = _candidates(services, it.service_name_raw)
        tasks.append({
            "raw": it.service_name_raw,
            "candidates": [{"id": c.id, "name": c.name, "category": c.category} for c in cands],
        })

    prompt = (
        "Ты нормализуешь названия медицинских услуг к справочнику. Для каждого "
        "элемента выбери id наиболее подходящей услуги из candidates или null, если "
        "ни одна не подходит. Ответ — строго JSON-массив вида "
        '[{"raw": "...", "id": "<id|null>"}]. Без пояснений.\n\n'
        + json.dumps(tasks, ensure_ascii=False)
    )
    reply = chat_completion(
        [{"role": "user", "content": prompt}], temperature=0.0, max_tokens=1500
    )
    if not reply:
        return {"ok": False, "reason": "llm_error", "resolved": 0,
                "message": "AI не ответил — попробуйте ещё раз."}

    m = re.search(r"\[.*\]", reply, re.DOTALL)
    try:
        decisions = json.loads(m.group(0) if m else reply)
    except Exception:
        return {"ok": False, "reason": "bad_response", "resolved": 0,
                "message": "AI вернул неразборчивый ответ."}

    by_raw = {it.service_name_raw: it for it in pending}
    resolved = 0
    for d in decisions if isinstance(decisions, list) else []:
        sid = d.get("id")
        it = by_raw.get(d.get("raw"))
        if it and sid and sid in by_id:
            _resolve(db, it, by_id[sid])
            resolved += 1
    db.commit()
    return {"ok": True, "resolved": resolved, "considered": len(pending),
            "message": f"AI разметил {resolved} из {len(pending)} позиций."}
