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

from ..config import settings
from ..db import get_db
from ..doctors_loader import load_specialties_meta
from ..llm import chat_completion
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
CLINIC_KW = ("клиник", "медцентр", "медицинск", "больниц", "поликлиник", "clinic",
             "емхана", "ауруха")


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
        "browse_map": "Цены на карте",
        "city": "🏥 В городе {city}: {doctors} врачей{clin} в нашей базе, приём от {min}. "
                "Выберите специализацию или посмотрите всех врачей и клиники.",
        "city_clin": " и {n} клиник",
        "city_pick": "Подскажите город (Алматы, Астана, Шымкент, Актобе…) или откройте карту цен по городам.",
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
        "browse_map": "Картадан бағалар",
        "city": "🏥 {city} қаласында: {doctors} дәрігер{clin} бар, қабылдау {min}-ден. "
                "Мамандықты таңдаңыз немесе барлық дәрігерлер мен клиникаларды қараңыз.",
        "city_clin": " және {n} клиника",
        "city_pick": "Қаланы айтыңыз (Алматы, Астана, Шымкент, Ақтөбе…) немесе баға картасын ашыңыз.",
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
        "browse_map": "Prices on map",
        "city": "🏥 In {city}: {doctors} doctors{clin} in our base, appointments from {min}. "
                "Pick a specialty or browse all doctors and clinics.",
        "city_clin": " and {n} clinics",
        "city_pick": "Tell me a city (Almaty, Astana, Shymkent, Aktobe…) or open the price map.",
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
    """Detect the city mentioned LAST in the text; stem-match to handle Russian
    case endings (Караганда → "в Караганде")."""
    best, best_pos = (None, None), -1
    for slug, name in REGION_NAMES.items():
        nm = name.lower()
        stem = nm[:-1] if len(nm) > 4 else nm
        pos = max(low.rfind(stem), low.rfind(slug))
        if pos > best_pos:
            best_pos, best = pos, (slug, name)
    return best


def _detect_specialty(low: str):
    for token, alias in _specialties_index():
        if token in low:
            return alias, token
    return None, None


def _reply(text: str, actions: list[dict] | None = None) -> dict:
    return {"reply": text, "actions": actions or []}


_LANG = {"ru": "Russian", "kk": "Kazakh", "en": "English"}


@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """OpenAI-backed reply grounded in our data; falls back to the deterministic
    engine if no API key or the LLM call fails. Action links always come from our
    data (the LLM never invents URLs)."""
    det = _resolve_with_history(req, db)
    if not settings.openai_api_key or not (req.message or "").strip():
        return det
    loc = L(req.locale)
    facts = det["reply"]
    actions_hint = (
        " Доступные кнопки-действия: " + "; ".join(a["label"] for a in det["actions"])
        if det.get("actions") else ""
    )
    system = (
        "You are the assistant for MedServicePrice.kz — a Kazakhstan medical price & doctor "
        "aggregator. You ONLY help with this platform's services: finding service/lab prices, "
        "finding doctors, comparing clinics, the cheapest city, and how to use the site. "
        "If the request is unrelated, politely decline and steer back to these features. "
        f"Always answer in {_LANG.get(loc, 'Russian')}, concise (1-3 sentences), friendly. "
        "Use ONLY the FACTS below for any prices, counts, ratings or names — never invent data. "
        "If the FACTS contain no specific numbers (e.g. they only describe what you can do), "
        "do NOT state any prices or counts — instead ask the user to specify the service, "
        "doctor specialty or city. "
        "Action buttons are shown to the user automatically; do NOT paste URLs.\n\n"
        f"FACTS: {facts}{actions_hint}"
    )
    messages = [{"role": "system", "content": system}]
    for turn in (req.history or [])[-6:]:
        messages.append({"role": "assistant" if turn.role == "bot" else "user", "content": turn.text})
    messages.append({"role": "user", "content": req.message})

    llm = chat_completion(messages)
    if not llm:
        return det
    return {"reply": llm, "actions": det["actions"]}


def _analyze(text: str, loc: str, db: Session) -> dict:
    """Detect intent + entities in `text` and build a grounded reply (with intent tag)."""
    tr = T[loc]
    msg = (text or "").strip()
    if not msg:
        return {**_reply(tr["capabilities"]), "intent": "capabilities"}
    low = msg.lower()
    tokens = set(normalize_text(msg).split())

    # 1. greeting / help / about
    if (_has(low, tokens, GREET) and len(msg) <= 45) or _has(low, tokens, ABOUT_KW):
        return {**_reply(tr["capabilities"], [
            {"label": tr["browse_services"], "href": "/compare"},
            {"label": tr["browse_doctors"], "href": "/doctors"},
        ]), "intent": "capabilities"}

    city_slug, city_name = _detect_city(low)

    # 2. specific specialty -> doctor reply
    spec_alias, spec_name = _detect_specialty(low)
    if spec_alias:
        return {**_doctor_reply(db, tr, spec_alias, spec_name, city_slug, city_name, loc), "intent": "doctor"}

    # 3. clinics intent (e.g. "клиники в Актобе") -> guide through the city
    if _has(low, tokens, CLINIC_KW):
        return {**_city_reply(db, tr, city_slug, city_name), "intent": "city"}

    # 4. "where cheaper" (no specific specialty)
    if _has(low, tokens, CHEAP):
        return {**_cheapest_reply(db, tr), "intent": "cheap"}

    # 5. generic doctor intent
    if _has(low, tokens, DOCTOR_KW):
        return {**_doctor_reply(db, tr, None, None, city_slug, city_name, loc), "intent": "doctor"}

    # 6. service price intent
    svc = _resolve_service(db, msg)
    if svc:
        return {**_service_reply(db, tr, svc, city_slug, city_name), "intent": "service"}
    if _has(low, tokens, PRICE_KW):
        return {**_reply(tr["svc_none"].format(q=msg[:40]), [
            {"label": tr["browse_services"], "href": "/compare"},
        ]), "intent": "svc_none"}

    # 7. a city was mentioned but nothing else -> guide through that city
    if city_slug:
        return {**_city_reply(db, tr, city_slug, city_name), "intent": "city"}

    # 8. off-topic
    return {**_reply(tr["offtopic"], [
        {"label": tr["browse_services"], "href": "/compare"},
        {"label": tr["browse_doctors"], "href": "/doctors"},
    ]), "intent": "offtopic"}


def _resolve_with_history(req: ChatRequest, db: Session) -> dict:
    """Analyze the current message; for short follow-ups (e.g. "а в Караганде?"),
    re-analyze combined with the last user turn so context (specialty/service) carries over."""
    loc = L(req.locale)
    det = _analyze(req.message, loc, db)
    if det["intent"] in ("offtopic", "capabilities", "svc_none") and req.history:
        last_user = next((h.text for h in reversed(req.history) if h.role == "user"), None)
        if last_user:
            det2 = _analyze(f"{last_user} {req.message}", loc, db)
            if det2["intent"] in ("doctor", "service", "cheap", "city"):
                det = det2
    return det


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


def _city_reply(db, tr, city_slug, city_name):
    """Guide the user through a city's offerings (doctors + clinics)."""
    if not city_slug:
        return _reply(tr["city_pick"], [
            {"label": tr["browse_map"], "href": "/map"},
            {"label": tr["browse_doctors"], "href": "/doctors"},
        ])
    nclin = db.query(func.count(Clinic.id)).filter(Clinic.city == city_name).scalar() or 0
    ndoc, mn = (
        db.query(func.count(Doctor.id), func.min(Doctor.min_price))
        .filter(Doctor.region == city_slug, Doctor.min_price >= 500)
        .first()
    )
    clin = tr["city_clin"].format(n=nclin) if nclin else ""
    text = tr["city"].format(city=city_name, doctors=ndoc or 0, clin=clin, min=fmt(mn))
    return _reply(text, [
        {"label": tr["doc_action"], "href": f"/doctors?region={city_slug}"},
        {"label": tr["browse_map"], "href": "/map"},
    ])


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
