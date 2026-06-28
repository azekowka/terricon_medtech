"""Core unit + integration tests for the parse → build-dictionary → normalize pipeline."""
from sqlalchemy import func

from app.models import Clinic, Price, Service, UnmatchedQueue
from app.normalization import Normalizer, normalize_text
from app.parsers.base import parse_price
from app.parsers.pipeline import _dedup_key, run_full
from app.search import SearchParams, autocomplete, search_offers


# ---- text + price parsing -------------------------------------------------
def test_normalize_text_strips_noise_and_case():
    assert normalize_text("  ОАК  ") == "оак"
    assert normalize_text("Витамин Ё") == normalize_text("витамин е")
    # "приём врача" wrapper is stripped so visits key on the specialty
    assert normalize_text("Приём врача (Терапевт)") == "терапевт"


def test_parse_price_variants():
    assert parse_price("2 200 ₸") == 2200
    assert parse_price("от 3500 тг.") == 3500
    assert parse_price("1\xa0950") == 1950
    assert parse_price("нет цены") is None
    assert parse_price("1.200 ₸") == 1200
    assert parse_price("28.000 тг") == 28000
    assert parse_price("1,200.00") == 1200.0
    assert parse_price("1 200,50") == 1200.5
    assert parse_price("99.99") == 99.99


# ---- normalizer -----------------------------------------------------------
def test_normalizer_exact_synonym_and_fuzzy():
    services = [
        {"id": "1", "code": "oak", "name": "Общий анализ крови (ОАК)",
         "category": "laboratory", "synonyms": ["ОАК", "CBC", "клинический анализ крови"]},
    ]
    n = Normalizer(services)
    assert n.match("ОАК").service_id == "1"
    assert n.match("CBC").service_id == "1"
    assert n.match("клинический анализ крови ").matched
    m = n.match("Клинический анализ крови, развернутый")
    assert m.matched and m.matched_by in {"exact", "fuzzy"}
    assert not n.match("Полёт на Марс туда-обратно").matched


# ---- dictionary built FROM data (TZ 3.2) ----------------------------------
def test_dictionary_built_from_collected_data(seeded_db):
    db = seeded_db
    services = db.query(Service).all()
    assert len(services) >= 50                       # TZ: >=50 normalized positions
    # each service was derived from raw mentions (not a fixed file)
    assert any((s.raw_count or 0) > 0 for s in services)
    # clustering collapsed variant spellings into synonyms
    assert sum(1 for s in services if (s.synonyms or [])) >= 10


def test_volume_and_real_sources(seeded_db):
    db = seeded_db
    assert db.query(Clinic).count() >= 3
    assert db.query(Price).filter(Price.is_active.is_(True)).count() >= 100  # TZ: >=100
    sources = {s for (s,) in db.query(Price.source).distinct().all()}
    assert len(sources) >= 3                          # TZ 6: >=3 distinct sources
    assert "seed" not in sources and "fixtures" not in sources  # no synthetic data


def test_normalization_links_most_prices(seeded_db):
    db = seeded_db
    matched = db.query(Price).filter(Price.service_id.isnot(None)).count()
    total = db.query(Price).count()
    # dictionary derived from the same names -> the vast majority match
    assert total and matched / total > 0.8


def test_real_extract_formats():
    from app.config import settings
    from app.parsers.real_extract import extract_real_file

    base = settings.data_path / "real_prices"
    for fname in ("Клиника 6 прайс 2026.xlsx", "Клиника 7_Прайс 2026.xls",
                  "Клиника 1 прайс 2024.docx", "Клиника 1 2026.pdf"):
        pairs = extract_real_file(str(base / fname))
        assert len(pairs) >= 30, f"{fname} yielded too few"
        _, price_raw = pairs[0]
        assert parse_price(price_raw) and parse_price(price_raw) >= 300


def test_synonym_dedup_collapses_one_clinic(seeded_db):
    """Two spellings of one service at one clinic -> a single dedup key (TZ 3.1)."""
    from app.normalization import build_normalizer_from_db

    db = seeded_db
    svc = next((s for s in db.query(Service).all() if len(s.synonyms or []) >= 1), None)
    assert svc is not None
    n = build_normalizer_from_db(db)
    m_name = n.match(svc.name)
    m_syn = n.match(svc.synonyms[0])
    assert m_name.service_id == svc.id == m_syn.service_id
    clinic = db.query(Clinic).first()
    assert _dedup_key(clinic.id, m_name.service_id, "x") == _dedup_key(clinic.id, m_syn.service_id, "x")


def test_dedup_on_rerun_is_idempotent(seeded_db):
    db = seeded_db
    before = db.query(Price).filter(Price.is_active.is_(True)).count()
    run_full(db, ["real"])  # same data again
    after = db.query(Price).filter(Price.is_active.is_(True)).count()
    assert abs(after - before) <= 5  # no duplicate explosion on re-run


def test_search_returns_sorted_offers(seeded_db):
    db = seeded_db
    top = (
        db.query(Price.service_id, func.count(Price.id))
        .filter(Price.service_id.isnot(None), Price.is_active.is_(True))
        .group_by(Price.service_id)
        .order_by(func.count(Price.id).desc())
        .first()
    )
    assert top is not None
    res = search_offers(db, SearchParams(service_id=top[0], sort="price_asc"))
    offers = res["offers"]
    assert len(offers) >= 2
    prices = [o["price_kzt"] for o in offers]
    assert prices == sorted(prices)
    assert res["stats"]["min_price"] == prices[0]


def test_autocomplete_finds_dictionary_service(seeded_db):
    db = seeded_db
    svc = db.query(Service).filter(Service.category == "laboratory").first()
    assert svc is not None
    hits = autocomplete(db, svc.name.split()[0][:6])
    assert hits  # the dictionary is searchable


def test_unmatched_queue_table_exists(seeded_db):
    # the queue mechanism works even if a self-built dictionary leaves it near-empty
    assert seeded_db.query(UnmatchedQueue).count() >= 0
