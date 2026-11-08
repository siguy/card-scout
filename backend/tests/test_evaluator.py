"""Tests Cooper can read top-to-bottom and understand.

Each test sets up a fake listing + fake comps, runs the evaluator, and
asserts the math. No network, no eBay, no scraping.
"""
from datetime import datetime, timedelta, timezone

from backend.config import Config, CompsConfig, RiskConfig
from backend.deal_evaluator import DealEvaluator
from backend.models import ActiveListing, CardModel, CompSummary, HistoricalComp


def _comps(median: float, n: int = 8, cv: float = 0.05, confidence: str = "high") -> CompSummary:
    return CompSummary(
        n=n,
        median=median,
        mean=median,
        stdev=median * cv,
        cv=cv,
        confidence=confidence,
        samples=[
            HistoricalComp(
                sale_price=median,
                sale_date=datetime.utcnow() - timedelta(days=i),
                title="test",
            )
            for i in range(min(n, 5))
        ],
    )


def _listing(price: float, shipping: float = 5.0) -> ActiveListing:
    return ActiveListing(
        listing_id="test-1",
        title="2018 Panini Prizm Luka Doncic Silver Rookie PSA 10",
        card=CardModel(
            player_name="Luka Doncic",
            year=2018,
            brand="Panini Prizm",
            card_type="Silver Prizm Rookie",
            graded=True,
            grader="PSA",
            grade=10.0,
        ),
        current_price=price,
        shipping_cost=shipping,
        end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        url="https://www.ebay.com/itm/test",
    )


def _cfg(margin: float = 0.30) -> Config:
    return Config(target_margin=margin, comps=CompsConfig(), risk=RiskConfig())


def test_approves_when_deeply_discounted_and_high_confidence():
    # FMV $1000, listing $650+$5 ship, 30% margin → discount = (1000 - 655)/1000 = 34.5%
    deal = DealEvaluator(_cfg()).evaluate(_listing(price=650, shipping=5), _comps(median=1000))
    assert deal.status == "approved"
    assert deal.discount > 0.30
    # max_bid = 1000*0.70 - 5 = 695
    assert deal.max_bid == 695.0


def test_rejects_when_low_confidence_even_if_cheap():
    # Bargain price but only 2 comps → never auto-approve.
    deal = DealEvaluator(_cfg()).evaluate(
        _listing(price=100), _comps(median=1000, n=2, confidence="low")
    )
    assert deal.status == "detected"


def test_detected_when_discount_below_target():
    # Only 10% under FMV; 30% required.
    deal = DealEvaluator(_cfg()).evaluate(_listing(price=895), _comps(median=1000))
    assert deal.status == "detected"


def test_no_comps_means_none_status_and_zero_max_bid():
    deal = DealEvaluator(_cfg()).evaluate(_listing(price=100), _comps(median=0, n=0, confidence="none"))
    assert deal.status == "detected"
    assert deal.fair_market_value == 0
    assert deal.max_bid == 0


def test_max_bid_honors_custom_margin():
    deal = DealEvaluator(_cfg(margin=0.40)).evaluate(_listing(price=300, shipping=10), _comps(median=1000))
    # max_bid = 1000*0.60 - 10 = 590
    assert deal.max_bid == 590.0
