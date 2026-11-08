"""Data shapes shared across the Card Scout pipeline.

A note on identity (for Cooper): two cards are "the same card" if they match on
player + year + brand + card_type + grade. That tuple is what we use to pull
comps and to value a listing. If we get it wrong, the FMV will be wrong.
"""
from datetime import datetime
from typing import List, Optional

import pydantic


class CardModel(pydantic.BaseModel):
    """The thing that's actually being sold, normalized."""
    player_name: str
    year: int
    brand: str               # e.g. "Panini Prizm", "Topps Chrome", "Fleer"
    card_type: str           # e.g. "Base", "Silver Prizm", "Rookie", "Refractor Rookie"
    graded: bool
    grader: Optional[str] = None      # "PSA" | "BGS" | "SGC"
    grade: Optional[float] = None     # 10.0, 9.5, ...

    def identifier(self) -> str:
        grade = f" {self.grader} {self.grade}" if self.graded else " Raw"
        return f"{self.year} {self.brand} {self.player_name} {self.card_type}{grade}"

    def comp_key(self) -> str:
        """Stable cache key for comp lookups."""
        return self.identifier().lower()


class HistoricalComp(pydantic.BaseModel):
    """A single past sale used to anchor fair-market value."""
    sale_price: float
    sale_date: datetime
    title: str
    url: Optional[str] = None
    source: str = "eBay Sold"


class CompSummary(pydantic.BaseModel):
    """Aggregated comp stats for a card."""
    n: int
    median: float
    mean: float
    stdev: float
    cv: float                          # coefficient of variation = stdev/median
    confidence: str                    # "high" | "low" | "none"
    samples: List[HistoricalComp] = []


class ActiveListing(pydantic.BaseModel):
    listing_id: str
    title: str
    card: CardModel
    current_price: float
    shipping_cost: float = 0.0
    buy_it_now: bool = False
    end_time: Optional[datetime] = None   # may be None for BIN
    url: str
    image_url: Optional[str] = None


class DetectedDeal(pydantic.BaseModel):
    deal_id: str
    listing: ActiveListing
    fair_market_value: float
    comps: CompSummary
    discount: float                    # (fmv - (price+shipping)) / fmv
    max_bid: float                     # ceiling honoring target margin
    status: str = "detected"           # detected | approved | rejected | snipe_queued | won | lost | expired
    explainer: Optional[str] = None
    created_at: datetime = pydantic.Field(default_factory=datetime.utcnow)


class BidOutcome(pydantic.BaseModel):
    """What actually happened. Feeds the self-improvement loop."""
    deal_id: str
    placed_bid: Optional[float] = None
    won: Optional[bool] = None
    final_price: Optional[float] = None
    notes: Optional[str] = None
    recorded_at: datetime = pydantic.Field(default_factory=datetime.utcnow)
