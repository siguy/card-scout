"""Decides whether a listing is a deal.

The math (for Cooper):
    total_cost    = current_price + shipping
    discount      = (fmv - total_cost) / fmv     # how undervalued, as a fraction
    max_bid       = fmv * (1 - target_margin) - shipping
                    # i.e. the most we'd ever pay to still keep our margin

A listing is "approved" only when:
    - we have HIGH confidence comps (enough data, not too noisy), AND
    - the discount meets or exceeds target_margin.

If either fails, we still record it as "detected" so it shows up in the
dashboard with an honest "low confidence" tag — never auto-flagged for bidding.
"""
from .comp_engine import fair_value
from .config import Config, load_config
from .models import ActiveListing, CompSummary, DetectedDeal


class DealEvaluator:
    def __init__(self, config: Config | None = None):
        self.config = config or load_config()
        self.target_margin = self.config.target_margin

    def evaluate(self, listing: ActiveListing, comps: CompSummary | None = None) -> DetectedDeal:
        comps = comps or fair_value(listing.card, self.config)
        fmv = comps.median
        shipping = listing.shipping_cost or 0.0
        total_cost = listing.current_price + shipping
        discount = (fmv - total_cost) / fmv if fmv > 0 else 0.0
        max_bid = round(max(fmv * (1 - self.target_margin) - shipping, 0), 2)

        if comps.confidence != "high":
            status = "detected"
        elif discount >= self.target_margin:
            status = "approved"
        else:
            status = "detected"

        explainer = self._explain(listing, comps, fmv, discount, max_bid, status)
        return DetectedDeal(
            deal_id=f"deal-{listing.listing_id}",
            listing=listing,
            fair_market_value=round(fmv, 2),
            comps=comps,
            discount=round(discount, 3),
            max_bid=max_bid,
            status=status,
            explainer=explainer,
        )

    def _explain(
        self,
        listing: ActiveListing,
        comps: CompSummary,
        fmv: float,
        discount: float,
        max_bid: float,
        status: str,
    ) -> str:
        if comps.confidence == "none":
            return (
                f"No recent sold comps found for {listing.card.identifier()}. "
                "Can't value this honestly — skip."
            )
        if comps.confidence == "low":
            return (
                f"Only {comps.n} comps with CV={comps.cv:.2f} (target ≥{self.config.comps.min_comps} "
                f"and CV ≤{self.config.comps.max_cv}). Fair value rough estimate ${fmv:,.2f} "
                f"but we won't auto-approve until comps firm up."
            )
        ebay_fee = round(fmv * 0.13, 2)
        net = round(fmv - (listing.current_price + listing.shipping_cost) - ebay_fee, 2)
        verdict = "APPROVED for review" if status == "approved" else "watching, not deep enough yet"
        return (
            f"FMV ${fmv:,.2f} from {comps.n} sold comps (median; CV={comps.cv:.2f}). "
            f"Listed at ${listing.current_price:,.2f} + ${listing.shipping_cost:,.2f} ship "
            f"= {discount*100:.1f}% under FMV. "
            f"Max bid honoring {int(self.target_margin*100)}% margin: ${max_bid:,.2f}. "
            f"At FMV resale, after ~13% eBay fees (${ebay_fee:,.2f}), net ≈ ${net:,.2f}. "
            f"Verdict: {verdict}."
        )
