import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import List

# Import Google Antigravity SDK components
from google.antigravity import Agent, LocalAgentConfig, ToolContext
from google.antigravity.triggers import every, TriggerContext

# Import our card scout data models and evaluation pipeline
from models import CardModel, ActiveListing, DetectedDeal
from mock_data import get_real_listings, generate_comps
from deal_evaluator import DealEvaluator

# Setup clean logging output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Initialize our central valuation engine (default 20% margin)
evaluator = DealEvaluator(target_margin=0.20)

# =============================================================================
# COOPER'S CORNER: WHAT IS AN AGENT TOOL?
# In the Google Antigravity SDK, a "Tool" is a Python function that the AI agent 
# can choose to execute when it needs real-world data or actions. 
# The agent reads the function's docstring to understand WHEN and HOW to use it!
# =============================================================================

def force_market_scout(ctx: ToolContext) -> str:
    """Forces the Card Scout agent to scan active marketplaces (eBay) immediately for deals.
    
    This queries the scraper pipeline, updates prices, evaluates profit margins, 
    and returns a summary of newly approved deals.
    """
    logging.info("🤖 AGENT TOOL: Executing force_market_scout...")
    
    # Retrieve current active deals or initialize empty list in agent state
    active_deals = ctx.get_state("detected_deals", [])
    
    # Load raw live listings from our mock scraper pipeline
    raw_listings = get_real_listings()
    new_approved_count = 0
    
    updated_deals = []
    for listing, true_fmv in raw_listings:
        # Run Margin of Safety evaluation math
        deal = evaluator.evaluate_listing(listing, true_fmv)
        updated_deals.append(deal)
        
        if deal.status == "Approved":
            new_approved_count += 1
            
    # Save the updated deals list back to the state so the agent remembers them!
    ctx.set_state("detected_deals", updated_deals)
    
    return (
        f"Scan complete. Scouted {len(raw_listings)} listings. "
        f"Located {new_approved_count} approved undervalued deals exceeding target 20% margin!"
    )

def list_scouted_opportunities(ctx: ToolContext) -> str:
    """Returns a readable list of all currently scouted card opportunities and status."""
    deals: List[DetectedDeal] = ctx.get_state("detected_deals", [])
    if not deals:
        return "No deals have been scouted yet. Run 'force_market_scout' first."
        
    summary = ["--- Current Scout Opportunities ---"]
    for d in deals:
        c = d.listing.card
        grade_str = f" {c.grader} {c.grade}" if c.graded else " Raw"
        summary.append(
            f"ID: {d.deal_id} | {c.year} {c.brand} {c.player_name}{grade_str}\n"
            f"  Current Price: ${d.listing.current_price:.2f} | Comps FMV: ${d.fair_market_value:.2f}\n"
            f"  Max Bid Ceiling: ${d.max_bid:.2f} | Discount: {d.estimated_margin*100:.1f}%\n"
            f"  Scout Rating: {d.status}"
        )
    return "\n".join(summary)

def approve_deal_for_snipe(deal_id: str, ctx: ToolContext) -> str:
    """Explicitly approves a detected undervalued card deal for the T-3s sniper queue.
    
    Args:
        deal_id: The unique ID of the deal (e.g. 'deal-ebay-103')
    """
    deals: List[DetectedDeal] = ctx.get_state("detected_deals", [])
    for d in deals:
        if d.deal_id == deal_id:
            d.status = "Approved"
            ctx.set_state("detected_deals", deals)
            logging.info(f"🎯 SNIPER QUEUE: Deal {deal_id} approved for T-3s sniper bid.")
            return f"Success! Deal {deal_id} has been moved to the active Sniper Queue."
    return f"Error: Deal ID {deal_id} not found."

# =============================================================================
# COOPER'S CORNER: WHAT IS A BACKGROUND TRIGGER?
# A "Trigger" is an asynchronous function that runs in the background. 
# Here, we use the `every` trigger helper to execute a scouting cycle automatically
# every 60 seconds, simulating a constant eye on the market while we sleep!
# =============================================================================

async def background_scout_cycle(ctx: TriggerContext):
    """Periodic background trigger that runs every 60 seconds to scan listings."""
    logging.info("⏰ BACKGROUND TRIGGER: Commencing automatic 60s market scan...")
    
    # In a real environment, this background trigger would scrape live eBay endpoints
    # and update our Firestore database so the frontend dashboard displays fresh cards.
    raw_listings = get_real_listings()
    approved_deals = []
    
    for listing, true_fmv in raw_listings:
        deal = evaluator.evaluate_listing(listing, true_fmv)
        if deal.status == "Approved":
            approved_deals.append(deal)
            
    logging.info(
        f"⏰ SCAN RESULTS: Scouted {len(raw_listings)} listings. "
        f"Detected {len(approved_deals)} hot opportunities."
    )
    
    # We can push a high-priority notification to the main agent conversation
    if approved_deals:
        best_deal = max(approved_deals, key=lambda x: x.estimated_margin)
        c = best_deal.listing.card
        await ctx.send(
            f"ALERT: Hot undervalued opportunity detected! "
            f"{c.year} {c.brand} {c.player_name} is selling for ${best_deal.listing.current_price:.2f} "
            f"which is {best_deal.estimated_margin*100:.1f}% below its comps FMV of ${best_deal.fair_market_value:.2f}!"
        )

# Configure the trigger to execute every 60 seconds
scout_timer_trigger = every(60, background_scout_cycle)

# =============================================================================
# AGENT INITIALIZATION & SETUP
# =============================================================================

config = LocalAgentConfig(
    system_instructions=(
        "You are 'Card Scout', a premium autonomous sports card trading and bidding assistant. "
        "Your goal is to locate undervalued card opportunities for a roster of NBA superstars "
        "and legends, and queue them for sniping. "
        "Strictly adhere to the following rules:\n"
        "1. For any active player or legend, you may recommend or approve cards for sniping.\n"
        "2. Focus on cards with a target profit margin of safety of 20% or more.\n"
        "3. Keep your responses professional and explain the comps analysis when requested."
    ),
    tools=[force_market_scout, list_scouted_opportunities, approve_deal_for_snipe],
    triggers=[scout_timer_trigger]
)

async def main():
    print("--- Starting Card Scout Agent Session ---")
    print("Agent is boot-loading custom tools and triggers...")
    
    async with Agent(config) as agent:
        # Step 1: Force an initial market scan using our tools
        print("\n[Turn 1] Scout: Force an initial scan and review opportunities...")
        response1 = await agent.chat("Scout the market now and list what you find.")
        print(await response1.text())
        
        # Step 2: Inquire about the Michael Jordan comps
        print("\n[Turn 2] User: Cooper asks why the Michael Jordan card is valued at $6,200...")
        response2 = await agent.chat("Why is the Michael Jordan rookie card valued at $6,200? Show me the comps.")
        print(await response2.text())

        # Step 3: Test bidding on Anthony Edwards
        print("\n[Turn 3] User: Can we queue a sniper bid for Anthony Edwards?")
        response3 = await agent.chat("Can we queue a sniper bid for Anthony Edwards?")
        print(await response3.text())

        print("\n[Turn 4] Background: Keeping session open to demonstrate background trigger log ticks...")
        print("Awaiting background trigger logs (Ctrl+C to exit)...")
        try:
            # Let the trigger fire once to demonstrate background polling
            await asyncio.sleep(65)
        except KeyboardInterrupt:
            print("\nExiting session.")

if __name__ == "__main__":
    # Run the async agent loop
    asyncio.run(main())
