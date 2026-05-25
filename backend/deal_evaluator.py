from datetime import datetime
from models import ActiveListing, DetectedDeal, CardModel
from mock_data import get_fmv, generate_comps

class DealEvaluator:
    def __init__(self, target_margin: float = 0.20):
        """Initializes the evaluator with a target margin percentage (default 20%)."""
        self.target_margin = target_margin

    def evaluate_listing(self, listing: ActiveListing, true_fmv: float = None) -> DetectedDeal:
        """Evaluates an active card listing against calculated comps to check if it's a deal.
        
        Math details for Cooper:
        1. FMV = Comps average.
        2. Max Bid = FMV * (1 - Target Margin) - Shipping Cost
        3. If current_price is below Max Bid, we have a deal!
        """
        # If true_fmv is not explicitly provided, we query our valuation catalog
        if true_fmv is None:
            c = listing.card
            true_fmv = get_fmv(c.player_name, c.year, c.brand, c.card_type, c.graded, c.grader, c.grade)

        # 1. Calculate Maximum Bid honoring the target margin of safety
        # e.g., if FMV is $1,000, and target margin is 28%, we want to buy it at maximum $720 minus shipping
        max_bid = round(true_fmv * (1 - self.target_margin) - listing.shipping_cost, 2)

        # 2. Calculate the estimated margin of discount relative to Fair Market Value
        estimated_margin = round((true_fmv - listing.current_price) / true_fmv, 3)

        # 3. Determine target bid (optimal starting bid or exact sniper bid)
        target_bid = round(min(listing.current_price * 1.05, max_bid), 2)

        # 4. Status determination
        status = "Detected"
        if listing.current_price <= max_bid:
            status = "Approved"  # Good deal, recommended for sniper queue!
        else:
            status = "Detected"  # Listed, but not undervalued enough yet

        # 5. Business Strategy Explainer Generator (Cooper's ROI Math!)
        c = listing.card
        ebay_fee = round(true_fmv * 0.13, 2)
        projected_gross = round(true_fmv - listing.current_price, 2)
        net_profit = round(true_fmv - listing.current_price - listing.shipping_cost - ebay_fee, 2)
        net_margin = round((net_profit / true_fmv) * 100, 1)

        grade_desc = f"{c.grader} {c.grade}" if c.graded else "Raw Card"
        if c.graded and c.grade == 10.0:
            strategy_desc = "Graded Blue-Chip Flip. This is a pristine gem-mint card with stable liquidity."
        elif c.graded:
            strategy_desc = f"Graded Holding Arbitrage. Excellent mid-tier {c.grader} {c.grade} hold."
        else:
            strategy_desc = "Raw-to-Graded Arbitrage. Buying clean raw cards to submit for grading to capture PSA 10 premiums."

        explainer = (
            f"🎯 Exit Strategy: {strategy_desc} "
            f"Average comps FMV is verified at ${true_fmv:,.2f}. At a current listing of ${listing.current_price:,.2f}, "
            f"this item offers a raw discount of {estimated_margin*100:.1f}%. Reselling at comps FMV, "
            f"after accounting for 13% eBay seller transaction fees (${ebay_fee:,.2f}) and shipping, "
            f"yields a clean projected net-of-fee profit of ${net_profit:,.2f} ({net_margin}% Net ROI)!"
        )

        deal_id = f"deal-{listing.listing_id}"
        return DetectedDeal(
            deal_id=deal_id,
            listing=listing,
            fair_market_value=true_fmv,
            estimated_margin=estimated_margin,
            max_bid=max_bid,
            target_bid=target_bid,
            status=status,
            explainer=explainer
        )

# Simple self-test
if __name__ == "__main__":
    from mock_data import get_real_listings
    evaluator = DealEvaluator(target_margin=0.20)
    print("--- Card Scout Comps & Deal Evaluation Test ---")
    for listing, true_fmv in get_real_listings():
        deal = evaluator.evaluate_listing(listing, true_fmv)
        c = deal.listing.card
        print(f"\nCard: {c.get_identifier()}")
        print(f"  Current Price: ${deal.listing.current_price:.2f} | Shipping: ${deal.listing.shipping_cost:.2f}")
        print(f"  Comps / FMV:   ${deal.fair_market_value:.2f}")
        print(f"  Max Bid Limit: ${deal.max_bid:.2f} (Target Margin: 20%)")
        print(f"  Scout Rating:  {deal.status} | Margin: {deal.estimated_margin*100:.1f}% Discount")
