"""Unit tests for the comp engine's pure logic (no network)."""
from datetime import datetime

from backend.comp_engine import _build_query, _drop_outliers, _parse_price, summarize
from backend.models import CardModel, HistoricalComp


def test_build_query_includes_grade_only_when_graded():
    raw = CardModel(player_name="Luka Doncic", year=2018, brand="Panini Prizm",
                    card_type="Silver Prizm Rookie", graded=False)
    assert "PSA" not in _build_query(raw)
    graded = raw.model_copy(update={"graded": True, "grader": "PSA", "grade": 10.0})
    assert "PSA 10" in _build_query(graded)


def test_parse_price_handles_commas_and_ranges():
    assert _parse_price("$1,234.56") == 1234.56
    assert _parse_price("$50.00 to $75.00") == 50.00
    assert _parse_price("free") is None


def test_drop_outliers_removes_obvious_garbage():
    prices = [100, 102, 98, 101, 99, 100, 99, 10_000]  # one $10k outlier
    cleaned = _drop_outliers(prices)
    assert 10_000 not in cleaned
    assert len(cleaned) == 7


def test_summarize_marks_low_confidence_when_too_few_comps():
    comps = [HistoricalComp(sale_price=100, sale_date=datetime.utcnow(), title="t") for _ in range(3)]
    s = summarize(comps, min_comps=5, max_cv=0.35)
    assert s.confidence == "low"
    assert s.median == 100


def test_summarize_marks_low_confidence_when_too_noisy():
    prices = [100, 200, 50, 400, 80, 300, 90, 150]
    comps = [HistoricalComp(sale_price=p, sale_date=datetime.utcnow(), title="t") for p in prices]
    s = summarize(comps, min_comps=5, max_cv=0.10)  # very strict
    assert s.confidence == "low"


def test_summarize_high_confidence_when_tight_cluster():
    comps = [
        HistoricalComp(sale_price=p, sale_date=datetime.utcnow(), title="t")
        for p in [100, 101, 99, 100, 102, 98, 100, 101]
    ]
    s = summarize(comps, min_comps=5, max_cv=0.35)
    assert s.confidence == "high"
    assert 99 <= s.median <= 101


def test_summarize_handles_empty():
    s = summarize([], min_comps=5, max_cv=0.35)
    assert s.confidence == "none"
    assert s.n == 0
