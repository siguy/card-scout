import pydantic
from typing import Optional, List
from datetime import datetime

class CardModel(pydantic.BaseModel):
    """Represents the unique characteristics of a sports card."""
    player_name: str
    year: int
    brand: str  # e.g., "Panini Prizm", "Fleer", "Topps Chrome", "Upper Deck"
    card_type: str  # e.g., "Base", "Silver Prizm", "Rookie Card", "Autograph", "Jersey Patch"
    graded: bool
    grader: Optional[str] = None  # e.g., "PSA", "BGS", "SGC"
    grade: Optional[float] = None  # e.g., 10.0, 9.5, 9.0, 8.5

    def get_identifier(self) -> str:
        """Generates a clean string key representing the card specifications."""
        grade_str = f" {self.grader} {self.grade}" if self.graded else " Raw"
        return f"{self.year} {self.brand} {self.player_name} {self.card_type}{grade_str}"

class HistoricalComp(pydantic.BaseModel):
    """Represents a completed past sale used for valuation valuation/comparables (comps)."""
    card: CardModel
    sale_price: float
    sale_date: datetime
    source: str  # e.g., "eBay Sold", "Card Ladder"
    url: Optional[str] = None

class ActiveListing(pydantic.BaseModel):
    """Represents a live card listed for sale (auction or buy-it-now)."""
    listing_id: str
    title: str
    card: CardModel
    current_price: float
    buy_it_now: bool
    end_time: datetime  # Critical for sniper to know when the final 15s starts
    shipping_cost: float
    url: str
    image_url: Optional[str] = None

class DetectedDeal(pydantic.BaseModel):
    """Represents an active listing identified as an arbitrage opportunity."""
    deal_id: str
    listing: ActiveListing
    fair_market_value: float
    estimated_margin: float  # e.g. 0.25 for 25% discount
    max_bid: float  # Absolute ceiling price honoring target profit margin
    target_bid: float  # The optimal starting bid/sniping price
    status: str = "Detected"  # "Detected", "Approved", "Sniped", "Missed", "Ignored"
    explainer: Optional[str] = None
    created_at: datetime = pydantic.Field(default_factory=datetime.now)
