"""Core unit + integration tests for the parsing/normalization/search pipeline."""
from app.models import Clinic, Price, PriceHistory, Service, UnmatchedQueue
from app.normalization import Normalizer, normalize_text
from app.parsers.base import parse_price
from app.parsers.pipeline import run_sources
from app.search import SearchParams, autocomplete, search_offers


# ---- text + price parsing ----
def test_normalize_text_strips_noise_and_case():
    assert normalize_text("  ОАК  ") == "оак"
    assert normalize_text("Витамин Ё") == normalize_text("витамин е")


def test_parse_price_variants():
    assert parse_price("2 200 ₸") == 2200
    assert parse_price("от 3500 тг.") == 3500
    assert parse_price("1\xa0950") == 1950
    assert parse_price("нет цены") is None
    # thousands / decimal separators (regression: previously truncated)
    assert parse_price("1.200 ₸") == 1200
    assert parse_price("28.000 тг") == 28000
    assert parse_price("1,200.00") == 1200.0
    assert parse_price("1 200,50") == 1200.5
    assert parse_price("99.99") == 99.99


# ---- normalizer ----
def test_normalizer_exact_synonym_and_fuzzy():
    services = [
        {"id": "1", "code": "oak", "name": "Общий анализ крови (ОАК)",
         "category": "laboratory", "synonyms": ["ОАК", "CBC", "клинический анализ крови"]},
    ]
    n = Normalizer(services)
    assert n.match("ОАК").service_id == "1"          # exact synonym
    assert n.match("CBC").service_id == "1"          # exact synonym (latin)
    assert n.match("клинический анализ крови ").matched  # exact-ish
    # close misspelling -> fuzzy
    m = n.match("Клинический анализ крови, развернутый")
    assert m.matched and m.matched_by in {"exact", "fuzzy"}
    # nonsense -> unmatched
    assert not n.match("Консультация астролога").matched


# ---- integration: seeded DB ----
def test_seed_counts(seeded_db):
    db = seeded_db
    assert db.query(Service).count() >= 50          # TZ: >=50 dictionary entries
    assert db.query(Clinic).count() >= 3
    assert db.query(Price).filter(Price.is_active.is_(True)).count() >= 100  # TZ: >=100
    # substantial normalization (mixed curated + messy real data lowers the overall rate)
    matched = db.query(Price).filter(Price.service_id.isnot(None)).count()
    total = db.query(Price).count()
    assert matched >= 1000 and matched / total > 0.5


def test_multiple_real_sources(seeded_db):
    # TZ 6: >=3 distinct real sources in the normalized data
    sources = {s for (s,) in seeded_db.query(Price.source).distinct().all()}
    assert len(sources) >= 3
    assert "seed" not in sources  # records carry real clinic-brand sources


def test_multiformat_fixtures_ingested(seeded_db):
    # TZ 3.1: PDF / XLSX / DOCX price lists flow through the pipeline
    sources = {s for (s,) in seeded_db.query(Price.source).distinct().all()}
    for src in ("gorpolik_astana", "odc_shymkent", "crb_aktobe"):
        assert src in sources, f"missing document source {src}"


def test_file_extractors():
    from pathlib import Path

    from app.config import settings
    from app.parsers.file_extract import extract_file

    fix = settings.data_path / "fixtures"
    for fname in ("gorpoliklinika_astana.pdf", "obldiagcentr_shymkent.xlsx", "crb_aktobe.docx"):
        pairs = extract_file(str(fix / fname))
        assert len(pairs) >= 10, f"{fname} extracted too few rows"
        # each pair has a Cyrillic-looking name and a parseable price
        name, price_raw = pairs[0]
        assert parse_price(price_raw) and parse_price(price_raw) > 0


def test_synonym_dedup_collapses_one_clinic(seeded_db):
    """Two synonym spellings of one service at one clinic -> a single Price row."""
    from app.models import Clinic
    from app.normalization import build_normalizer_from_db
    from app.parsers.pipeline import _dedup_key

    db = seeded_db
    clinic = db.query(Clinic).first()
    n = build_normalizer_from_db(db)
    # "Прием терапевта" and its synonym "Консультация терапевта" resolve to one service
    m1 = n.match("Прием терапевта")
    m2 = n.match("Консультация терапевта")
    assert m1.service_id and m1.service_id == m2.service_id

    k1 = _dedup_key(clinic.id, m1.service_id, "kdl")
    k2 = _dedup_key(clinic.id, m2.service_id, "kdl")
    assert k1 == k2  # same dedup key despite different raw spellings


def test_unmatched_queue_populated(seeded_db):
    assert seeded_db.query(UnmatchedQueue).filter_by(status="pending").count() >= 1


def test_history_backfilled(seeded_db):
    assert seeded_db.query(PriceHistory).count() > seeded_db.query(Price).count()


def test_dedup_on_rerun(seeded_db):
    db = seeded_db
    before = db.query(Price).count()
    logs = run_sources(db, ["seed"])
    after = db.query(Price).count()
    assert after == before                  # no duplicates created
    assert logs[0].records_new == 0
    assert logs[0].records_updated > 0


def test_autocomplete_and_search(seeded_db):
    db = seeded_db
    hits = autocomplete(db, "терапевт")
    assert any("терапевт" in h["name"].lower() for h in hits)

    sid = next(h["id"] for h in autocomplete(db, "Прием терапевта") if "терапевт" in h["name"].lower())
    res = search_offers(db, SearchParams(service_id=sid, sort="price_asc"))
    offers = res["offers"]
    assert len(offers) >= 3
    # sorted ascending
    prices = [o["price_kzt"] for o in offers]
    assert prices == sorted(prices)
    # stats present
    assert res["stats"]["min_price"] == prices[0]


def test_search_city_filter(seeded_db):
    db = seeded_db
    res = search_offers(db, SearchParams(q="Прием терапевта", city="Алматы"))
    assert res["offers"]  # has results
    assert all(o["city"] == "Алматы" for o in res["offers"])
