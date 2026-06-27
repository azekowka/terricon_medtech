"""Service-guide chatbot.

A domain-restricted assistant that ONLY helps with the platform's offered
services: finding service prices, finding doctors, comparing clinics, cheapest
cities and how to use the site. It answers from our real data (services, prices,
doctors) and returns actionable links. Off-topic questions are politely declined.

No external LLM required — intent + entity detection over the live DB.
"""
from __future__ import annotations

import functools

from fastapi import APIRouter, Depends
from rapidfuzz import fuzz
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..doctors_loader import load_specialties_meta
from ..models import Clinic, Doctor, Price, Service
from ..normalization.text import normalize_text
from ..schemas import ChatRequest
from .doctors import REGION_NAMES

router = APIRouter(prefix="/api/assistant", tags=["assistant"])

GREET = ("привет", "здравств", "салем", "сәлем", "hello", "hi", "добр", "help",
         "помощ", "что ты", "что умеешь", "как польз", "what can", "how to", "көмек")
CHEAP = ("дешевл", "дешево", "выгод", "cheap", "арзан", "where cheap")
DOCTOR_KW = ("врач", "доктор", "специалист", "приём", "прием", "записаться", "doctor",
             "дәрігер", "қабылдау", "appointment")
PRICE_KW = ("цена", "стоит", "сколько", "прайс", "price", "бағас", "анализ", "узи",
            "мрт", "кт", "рентген", "тест", "analys")
ABOUT_KW = ("что это", "о сервис", "about", "кто ты", "бұл не")


def fmt(n) -> str:
    try:
        return f"{int(round(float(n))):,}".replace(",", " ") + " ₸"
    except (TypeError, ValueError):
        return "—"


def L(locale: str) -> str:
    return locale if locale in ("ru", "kk", "en") else "ru"


def _has(low: str, tokens: set[str], kws) -> bool:
    """Keyword match: multi-word -> substring; short -> exact token; else substring-in-token."""
    for k in kws:
        if " " in k:
            if k in low:
                return True
        elif len(k) <= 3:
            if k in tokens:
                return True
        else:
            if any(k in tok for tok in tokens):
                return True
    return False


# ---- localized snippets ---------------------------------------------------
T = {
    "ru": {
        "capabilities": "Я помощник MedServicePrice 🩺 Помогу с услугами платформы:\n"
                        "• найти цену анализа или процедуры\n• подобрать врача по специальности и городу\n"
                        "• сравнить клиники и найти выгодное предложение\n• показать цены по городам на карте\n\n"
                        "Спросите, например: «сколько стоит ОАК», «кардиолог в Алматы», «где дешевле приём врача».",
        "offtopic": "Я отвечаю только по услугам MedServicePrice — цены на анализы, врачи, сравнение клиник. "
                    "Попробуйте: «цена УЗИ», «найти невролога», «где дешевле».",
        "svc": "💊 {name}: от {min} до {max} за приём в {count} клиниках. Средняя цена — {avg}.",
        "svc_city": " В городе {city}: от {cmin} ({ccount} клиник).",
        "svc_action": "Сравнить цены",
        "svc_none": "Пока нет данных по ценам на «{q}». Посмотрите похожие услуги в сравнении.",
        "doc": "👨‍⚕️ {spec}{city}: {count} врачей. Приём от {min}, лучший рейтинг {rating}★.",
        "doc_action": "Смотреть врачей",
        "doc_none": "Не нашёл врачей по запросу. Откройте каталог врачей и выберите специализацию.",
        "cheap": "💡 Дешевле всего приём врача в {city} — от {price}.",
        "cheap_action": "Открыть карту цен",
        "browse_services": "Все услуги",
        "browse_doctors": "Каталог врачей",
    },
    "kk": {
        "capabilities": "Мен MedServicePrice көмекшісімін 🩺 Платформа қызметтері бойынша көмектесемін:\n"
                        "• талдау немесе процедура бағасын табу\n• мамандық пен қала бойынша дәрігер таңдау\n"
                        "• клиникаларды салыстыру\n• қалалар бойынша бағаларды картадан көрсету\n\n"
                        "Мысалы: «ОАК қанша тұрады», «Алматыдағы кардиолог», «қай жерде арзан».",
        "offtopic": "Мен тек MedServicePrice қызметтері бойынша жауап беремін — бағалар, дәрігерлер, салыстыру. "
                    "Мысалы: «УДЗ бағасы», «невролог табу».",
        "svc": "💊 {name}: {count} клиникада {min}–{max}. Орташа — {avg}.",
        "svc_city": " {city} қаласында: {cmin}-ден ({ccount} клиника).",
        "svc_action": "Бағаларды салыстыру",
        "svc_none": "«{q}» бойынша баға деректері әзірге жоқ.",
        "doc": "👨‍⚕️ {spec}{city}: {count} дәрігер. Қабылдау {min}-ден, үздік рейтинг {rating}★.",
        "doc_action": "Дәрігерлерді көру",
        "doc_none": "Дәрігер табылмады. Дәрігерлер каталогын ашыңыз.",
        "cheap": "💡 Дәрігер қабылдауы {city} қаласында ең арзан — {price}-ден.",
        "cheap_action": "Баға картасын ашу",
        "browse_services": "Барлық қызметтер",
        "browse_doctors": "Дәрігерлер каталогы",
    },
    "en": {
        "capabilities": "I'm the MedServicePrice assistant 🩺 I help with the platform's services:\n"
                        "• find the price of a lab test or procedure\n• find a doctor by specialty and city\n"
                        "• compare clinics and find the best deal\n• show prices by city on the map\n\n"
                        "Try: \"price of CBC\", \"cardiologist in Almaty\", \"where is it cheaper\".",
        "offtopic": "I only help with MedServicePrice services — prices, doctors, clinic comparison. "
                    "Try: \"ultrasound price\", \"find a neurologist\".",
        "svc": "💊 {name}: from {min} to {max} across {count} clinics. Average — {avg}.",
        "svc_city": " In {city}: from {cmin} ({ccount} clinics).",
        "svc_action": "Compare prices",
        "svc_none": "No price data for \"{q}\" yet.",
        "doc": "👨‍⚕️ {spec}{city}: {count} doctors. Appointments from {min}, top rating {rating}★.",
        "doc_action": "Browse doctors",
        "doc_none": "No doctors found for your query.",
        "cheap": "💡 Cheapest doctor appointment is in {city} — from {price}.",
        "cheap_action": "Open price map",
        "browse_services": "All services",
        "browse_doctors": "Doctors catalog",
    },
}


@functools.lru_cache(maxsize=1)
def _specialties_index() -> list[tuple[str, str]]:
    """[(keyword_lower, alias)] sorted by length desc for greedy matching."""
    out = []
    for s in load_specialties_meta():
        name = (s.get("name") or "").lower()
        if not name:
            continue
        token = name.split("(")[0].strip()  # "невролог (невропатолог)" -> "невролог"
        if len(token) >= 4:
            out.append((token, s["alias"]))
    out.sort(key=lambda x: -len(x[0]))
    return out


def _detect_city(low: str):
    for slug, name in REGION_NAMES.items():
        if name.lower() in low or slug in low:
            return slug, name
    return None, None


def _detect_specialty(low: str):
    for token, alias in _specialties_index():
        if token in low:
            return alias, token
    return None, None


def _reply(text: str, actions: list[dict] | None = None) -> dict:
    return {"reply": text, "actions": actions or []}


@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    msg = (req.message or "").strip()
    loc = L(req.locale)
    tr = T[loc]
    if not msg:
        return _reply(tr["capabilities"])
    low = msg.lower()
    tokens = set(normalize_text(msg).split())

    # 1. greeting / help / about
    if (_has(low, tokens, GREET) and len(msg) <= 45) or _has(low, tokens, ABOUT_KW):
        return _reply(tr["capabilities"], [
            {"label": tr["browse_services"], "href": "/compare"},
            {"label": tr["browse_doctors"], "href": "/doctors"},
        ])

    city_slug, city_name = _detect_city(low)

    # 2. specific specialty -> doctor reply
    spec_alias, spec_name = _detect_specialty(low)
    if spec_alias:
        return _doctor_reply(db, tr, spec_alias, spec_name, city_slug, city_name, loc)

    # 3. "where cheaper" (no specific specialty)
    if _has(low, tokens, CHEAP):
        return _cheapest_reply(db, tr)

    # 4. generic doctor intent
    if _has(low, tokens, DOCTOR_KW):
        return _doctor_reply(db, tr, None, None, city_slug, city_name, loc)

    # 5. service price intent
    svc = _resolve_service(db, msg)
    if svc:
        return _service_reply(db, tr, svc, city_slug, city_name)
    if _has(low, tokens, PRICE_KW):
        return _reply(tr["svc_none"].format(q=msg[:40]), [
            {"label": tr["browse_services"], "href": "/compare"},
        ])

    # 5. off-topic
    return _reply(tr["offtopic"], [
        {"label": tr["browse_services"], "href": "/compare"},
        {"label": tr["browse_doctors"], "href": "/doctors"},
    ])


def _service_candidates(db: Session):
    """Services that actually have prices, with their normalized name/synonym keys."""
    counts = dict(
        db.query(Price.service_id, func.count(Price.id))
        .filter(Price.is_active.is_(True), Price.service_id.isnot(None))
        .group_by(Price.service_id)
        .all()
    )
    out = []
    for s in db.query(Service).all():
        if counts.get(s.id, 0) == 0:
            continue
        keys = [normalize_text(s.name)] + [normalize_text(x) for x in (s.synonyms or [])]
        out.append((s, [k for k in keys if k]))
    return out


def _resolve_service(db: Session, msg: str):
    """Precise resolver: exact whole-word abbreviation, phrase containment, then fuzzy."""
    nmsg = normalize_text(msg)
    if not nmsg:
        return None
    tokens = set(nmsg.split())
    best, best_score = None, 0.0
    for s, keys in _service_candidates(db):
        for k in keys:
            kt = k.split()
            # exact abbreviation/word as a standalone token (ОАК, ПСА, ТТГ…)
            if len(kt) == 1 and len(kt[0]) >= 2 and kt[0] in tokens:
                if 96 > best_score:
                    best, best_score = s, 96
            # full phrase contained in the message
            elif len(k) >= 5 and k in nmsg:
                sc = 90 + min(len(kt), 8)
                if sc > best_score:
                    best, best_score = s, sc
        # fuzzy against the canonical name
        fs = fuzz.token_set_ratio(nmsg, keys[0])
        if fs > best_score and fs >= 82:
            best, best_score = s, fs
    return best if best_score >= 82 else None


def _service_reply(db, tr, svc: Service, city_slug, city_name):
    agg = (
        db.query(func.count(Price.id), func.min(Price.price_kzt),
                 func.max(Price.price_kzt), func.avg(Price.price_kzt))
        .filter(Price.service_id == svc.id, Price.is_active.is_(True))
        .first()
    )
    count, mn, mx, avg = agg
    text = tr["svc"].format(name=svc.name, min=fmt(mn), max=fmt(mx), count=count or 0, avg=fmt(avg))
    if city_name:
        cagg = (
            db.query(func.min(Price.price_kzt), func.count(Price.id))
            .join(Clinic, Price.clinic_id == Clinic.id)
            .filter(Price.service_id == svc.id, Price.is_active.is_(True))
            .filter(func.lower(Clinic.city) == city_name.lower())
            .first()
        )
        if cagg and cagg[1]:
            text += tr["svc_city"].format(city=city_name, cmin=fmt(cagg[0]), ccount=cagg[1])
    return _reply(text, [{"label": tr["svc_action"], "href": f"/compare?service_id={svc.id}"}])


def _doctor_reply(db, tr, spec_alias, spec_name, city_slug, city_name, loc):
    q = db.query(func.count(Doctor.id), func.min(Doctor.min_price), func.max(Doctor.rating)).filter(
        Doctor.min_price.isnot(None), Doctor.min_price >= 500
    )
    if spec_alias:
        q = q.filter(Doctor.spec_aliases.like(f"%,{spec_alias},%"))
    if city_slug:
        q = q.filter(Doctor.region == city_slug)
    count, mn, rating = q.first()
    if not count:
        return _reply(tr["doc_none"], [{"label": tr["browse_doctors"], "href": "/doctors"}])
    spec_label = (spec_name.capitalize() if spec_name else ("Врачи" if loc == "ru" else "Doctors"))
    city_part = f" ({city_name})" if city_name else ""
    text = tr["doc"].format(spec=spec_label, city=city_part, count=count,
                            min=fmt(mn), rating=f"{rating:.1f}" if rating else "—")
    href = "/doctors"
    params = []
    if city_slug:
        params.append(f"region={city_slug}")
    if spec_alias:
        params.append(f"specialty={spec_alias}")
    if params:
        href += "?" + "&".join(params)
    return _reply(text, [{"label": tr["doc_action"], "href": href}])


def _cheapest_reply(db, tr):
    row = (
        db.query(Doctor.region, func.min(Doctor.min_price))
        .filter(Doctor.min_price >= 1000)
        .group_by(Doctor.region)
        .order_by(func.min(Doctor.min_price))
        .first()
    )
    if not row:
        return _reply(tr["offtopic"])
    slug, price = row
    text = tr["cheap"].format(city=REGION_NAMES.get(slug, slug), price=fmt(price))
    return _reply(text, [
        {"label": tr["cheap_action"], "href": "/map"},
        {"label": tr["browse_doctors"], "href": f"/doctors?region={slug}"},
    ])
