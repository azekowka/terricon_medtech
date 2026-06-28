"""Build the services dictionary FROM the collected raw data (TZ 3.2).

The dictionary is NOT loaded from any prepared file. It is derived by clustering
the raw service names the parsers collected into `raw_prices`:

    distinct raw names  ->  normalize text  ->  fuzzy-cluster within a category
                        ->  canonical service (name, synonyms, category, code)

Each cluster becomes one `Service`. The most frequent raw variant is the canonical
name; every variant in the cluster is kept as a synonym, so normalization later is
an exact lookup for known names and a fuzzy match for new ones.

This makes "ОАК / CBC / Общий анализ крови" collapse into one service, exactly as
the spec illustrates, but with the dictionary *grown from the data we scraped*.
"""
from __future__ import annotations

import hashlib
import re

from rapidfuzz import fuzz, process
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Price, RawPrice, Service, UnmatchedQueue
from ..normalization.text import normalize_text

# ---- category inference (keyword based, doctor-first) ----------------------
CATEGORY_LABELS = {
    "laboratory": "Лаборатория",
    "doctor": "Приём врача",
    "diagnostic": "Диагностика",
    "procedure": "Процедура",
}
_DOC_KW = ("прием ", "приём ", "приема", "приёма", "консультац", "осмотр врача",
           "осмотр специалист", "вызов врача", "врач на дом")
_DIAG_KW = ("узи", "мрт", " кт ", "кт ", "рентген", "доплер", "допплер", "томограф",
            "сцинтиграф", "маммограф", "флюорограф", "флюорогр", "эхокг", "эхо-кг",
            "эхокардиограф", "ктг", "холтер", "эндоскоп", "гастроскоп", "колоноскоп",
            "ректоскоп", "фгдс", "эфгдс", "биопси", "денситометр", "ээг", "экг",
            "эхоэг", "рэг", "эмг", "спирограф", "спирометр", "кольпоскоп",
            "дерматоскоп", "аудиометр", "офтальмоскоп", "гистолог", "цитолог",
            "сцинтиграфия", "пэт", "ангиограф", "урофлоуметр")
_LAB_KW = (
    # general
    "анализ", " кровь", " крови", " моча", " мочи", " кале", " кала", "мазок",
    "посев", "соскоб", "соэ", "оак", "оам", "биохим", "коагул", "коагулограм",
    "гемостаз", "пцр", "ифа", "хроматограф", "иммуноблот",
    # immunology / serology
    "антитела", "антител", "антиген", "иммуноглобулин", "интерлейкин",
    "ig g", "igg", "igm", "iga", "ige", "anti", "авидност", "аллерген",
    # markers / hormones
    "маркер", "гормон", "са 125", "са-125", "са 19", "рэа", "афп", "пса", "psa",
    "пролактин", "тестостерон", "эстрадиол", "прогестерон", "кортизол",
    "альдостерон", "адреналин", "инсулин", "с-пептид", "паратгормон", "ттг",
    "т3", "т4", "ат-тпо", "соматотроп", "лг", "фсг",
    # biochemistry analytes
    "глюкоз", "холестерин", "триглицерид", "лпнп", "лпвп", "креатинин",
    "мочевина", "мочевая кислота", "билирубин", "общий белок", "альбумин",
    "ферритин", "трансферрин", "железо", "кальций", "калий", "натрий", "магний",
    "фосфор", "хлор", "амилаз", "липаз", "алт", "аст", "ггт", "лдг", "кфк",
    "щелочная фосфатаз", "д-димер", "ачтв", "мно", "пти", "фибриноген",
    "гомоцистеин", "фолат", "фолиевая", "витамин", "гепатит", "вич", "сифилис",
    "covid", "sars", "группа крови", "резус", "онкоцитолог", "цитолог крови",
)
# regex signals that strongly imply a lab test regardless of keyword list
_LAB_RE = re.compile(
    r"\big[gmae]\b|\bca[\s\-]?\d|анти-?тел|в (крови|моче|сыворотке|плазме|кале)\b|"
    r"методом и?фа|количественн|качественн",
)


def categorize(name: str) -> str:
    n = " " + name.lower().replace("ё", "е") + " "
    if any(k in n for k in _DOC_KW):
        return "doctor"
    if any(k in n for k in _DIAG_KW):
        return "diagnostic"
    if any(k in n for k in _LAB_KW) or _LAB_RE.search(n):
        return "laboratory"
    return "procedure"


# ---- canonical-name prettifier --------------------------------------------
_LEADING_CODE = re.compile(r"^\s*[A-Za-zА-Яа-я]?\d[\d.\-/]*\.?\s+")
_WS = re.compile(r"\s+")


_DOCTOR_VISIT_RE = re.compile(r"^при[её]м врача\s*\((.+)\)\s*$", re.IGNORECASE)


def _pretty(name: str) -> str:
    s = _WS.sub(" ", _LEADING_CODE.sub("", str(name).replace("\xa0", " "))).strip(" .—–-\t")
    # "Приём врача (Акушер-гинеколог)" -> "Акушер-гинеколог" (the category chip already
    # says "Приём врача", so the name keeps only the specialty).
    m = _DOCTOR_VISIT_RE.match(s)
    if m:
        return m.group(1).strip()
    # de-shout ALL-CAPS names (keep short acronyms like ОАК, УЗИ, ПЦР, СОЭ intact)
    letters = [c for c in s if c.isalpha()]
    if len(s) > 5 and letters and all((not c.isalpha()) or c.isupper() for c in s):
        s = s.capitalize()
    return s or str(name).strip()


def _code(category: str, key: str) -> str:
    h = hashlib.md5(f"{category}|{key}".encode("utf-8")).hexdigest()[:10]
    return f"svc_{h}"


# ---- clustering ------------------------------------------------------------
MERGE_THRESHOLD = 88  # token_set_ratio above which two raw names are one service
_MIN_LEN = 3
_MAX_SYNONYMS = 50


class _Cluster:
    __slots__ = ("key", "canonical", "category", "count", "sources", "variants")

    def __init__(self, key, name, category, count, sources):
        self.key = key
        self.canonical = name
        self.category = category
        self.count = count
        self.sources = set(sources)
        self.variants: dict[str, int] = {name: count}  # original name -> count


def _gather(db: Session) -> list[tuple[str, str, int]]:
    """(name, source, count) for every distinct raw service name + source."""
    return db.query(
        RawPrice.service_name_raw, RawPrice.source, func.count()
    ).group_by(RawPrice.service_name_raw, RawPrice.source).all()


def build_clusters(db: Session) -> list[_Cluster]:
    # aggregate per distinct raw name: total count + which sources
    agg: dict[str, dict] = {}
    for name, source, cnt in _gather(db):
        name = (name or "").strip()
        if not name:
            continue
        a = agg.setdefault(name, {"count": 0, "sources": set()})
        a["count"] += cnt
        a["sources"].add(source)

    # most frequent names seed clusters and become canonical
    items = sorted(agg.items(), key=lambda kv: -kv[1]["count"])

    # bucket by category so unrelated categories never merge (and to bound work)
    buckets: dict[str, list[_Cluster]] = {}
    bucket_keys: dict[str, list[str]] = {}
    exact: dict[str, dict[str, _Cluster]] = {}  # cat -> nk -> cluster

    for name, a in items:
        nk = normalize_text(name)
        if not nk or len(nk) < _MIN_LEN:
            continue
        cat = categorize(name)
        clusters = buckets.setdefault(cat, [])
        keys = bucket_keys.setdefault(cat, [])
        ex = exact.setdefault(cat, {})

        hit = ex.get(nk)  # identical normalized name -> always the same service
        # Fuzzy-merge only for non-doctor categories. Doctor specialties are
        # discrete ("Терапевт" must NOT absorb "Стоматолог-терапевт"), so they
        # cluster by exact key only (token_set_ratio=100 on a subset would merge them).
        if hit is None and cat != "doctor" and keys:
            best = process.extractOne(nk, keys, scorer=fuzz.token_set_ratio)
            if best and best[1] >= MERGE_THRESHOLD:
                hit = clusters[best[2]]

        if hit is not None:
            hit.count += a["count"]
            hit.sources |= a["sources"]
            hit.variants[name] = hit.variants.get(name, 0) + a["count"]
        else:
            c = _Cluster(nk, name, cat, a["count"], a["sources"])
            clusters.append(c)
            keys.append(nk)
            ex[nk] = c

    return [c for cl in buckets.values() for c in cl]


def _synonyms(cluster: _Cluster) -> list[str]:
    # every distinct raw variant (minus the canonical) — capped, frequent first
    variants = sorted(cluster.variants.items(), key=lambda kv: -kv[1])
    out: list[str] = []
    seen = {normalize_text(cluster.canonical)}
    for name, _ in variants:
        nk = normalize_text(name)
        if nk in seen:
            continue
        seen.add(nk)
        out.append(name)
        if len(out) >= _MAX_SYNONYMS:
            break
    return out


def rebuild_dictionary(db: Session, progress=None) -> dict:
    """Cluster the raw layer into the `services` dictionary. Idempotent: stable
    codes mean re-running on the same data keeps service ids stable."""
    if progress:
        progress("Анализ собранных названий…")
    clusters = build_clusters(db)
    clusters.sort(key=lambda c: -c.count)

    seen_codes: set[str] = set()
    built = 0
    for c in clusters:
        code = _code(c.category, c.key)
        if code in seen_codes:
            continue
        seen_codes.add(code)
        svc = db.query(Service).filter_by(code=code).first()
        if svc is None:
            svc = Service(code=code)
            db.add(svc)
        svc.name = _pretty(c.canonical)
        svc.category = c.category
        svc.synonyms = _synonyms(c)
        svc.raw_count = int(c.count)
        svc.source_count = len(c.sources)
        svc.specialty = ""
        built += 1
        if progress and built % 200 == 0:
            progress(f"Справочник: {built} услуг…")

    # drop services that are no longer present in the data (clean, data-derived).
    # Prices are re-linked in the normalize phase right after, so orphaning is safe.
    db.flush()
    stale = db.query(Service).filter(Service.code.notin_(seen_codes)).all() if seen_codes else []
    for s in stale:
        db.query(UnmatchedQueue).filter(UnmatchedQueue.suggested_service_id == s.id).update(
            {UnmatchedQueue.suggested_service_id: None}, synchronize_session=False
        )
        db.query(Price).filter(Price.service_id == s.id).update(
            {Price.service_id: None}, synchronize_session=False
        )
        db.delete(s)
    db.commit()

    by_cat: dict[str, int] = {}
    for c in clusters:
        by_cat[c.category] = by_cat.get(c.category, 0) + 1
    return {"services": built, "by_category": by_cat, "removed_stale": len(stale)}
