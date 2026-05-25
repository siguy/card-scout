import asyncio
import os
import sys
import logging
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel

# Import our card scout data models and evaluations
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models import DetectedDeal, ActiveListing, CardModel
from mock_data import get_real_listings
from deal_evaluator import DealEvaluator
from scout_agent import scout_timer_trigger

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(
    title="Card Scout Cloud Service",
    description="24/7 autonomous sports card scout and auction sniper agent.",
    version="1.0.0"
)

# Enable CORS so our Firebase hosting dashboard can securely query this API!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your Firebase Hosting domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

evaluator = DealEvaluator(target_margin=0.20)
active_deals: List[DetectedDeal] = []

# Scraper polling logic running as a background service task
async def continuous_market_scout_loop():
    """Background task running the Antigravity scout polling cycles continuously."""
    global active_deals
    logging.info("☁️ CLOUD BACKGROUND: Booting scout polling thread...")
    while True:
        try:
            raw_listings = get_real_listings()
            temp_deals = []
            new_deals_count = 0
            
            for listing, true_fmv in raw_listings:
                deal = evaluator.evaluate_listing(listing, true_fmv)
                temp_deals.append(deal)
                if deal.status == "Approved":
                    new_deals_count += 1
            
            # Thread-safe update
            active_deals = temp_deals
            logging.info(f"☁️ CLOUD BACKGROUND: Scan completed. Found {new_deals_count} approved deals.")
            
        except Exception as e:
            logging.error(f"❌ CLOUD BACKGROUND ERROR: {e}")
            
        # Poll every 60 seconds
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    """Starts the background scouting thread when Cloud Run container boots up."""
    asyncio.create_task(continuous_market_scout_loop())

@app.get("/")
def read_root():
    """Returns a beautiful status dashboard page to Cloud Run visitors."""
    roster_list = ["LeBron James", "Michael Jordan", "Stephen Curry", "Victor Wembanyama", "Kobe Bryant", "Luka Doncic", "Nikola Jokic", "Anthony Edwards"]
    html_content = f"""
    <html>
        <head>
            <title>Card Scout Cloud Service</title>
            <style>
                body {{ font-family: -apple-system, sans-serif; background: #030712; color: #f1f5f9; padding: 40px; text-align: center; }}
                .status {{ display: inline-block; padding: 8px 16px; background: rgba(16, 185, 129, 0.2); color: #34d399; border-radius: 9999px; font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 20px; }}
                h1 {{ color: #fff; margin-bottom: 5px; }}
                p {{ color: #9ca3af; margin-top: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); padding: 30px; border-radius: 24px; box-shadow: 0 8px 32px 0 rgba(0,0,0,0.25); }}
                .roster {{ text-align: left; background: rgba(255,255,255,0.01); padding: 15px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.03); margin-top: 20px; }}
                .roster li {{ color: #e2e8f0; font-size: 14px; margin-bottom: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <span class="status">● Active Scout Running</span>
                <h1>Card Scout API Gateway</h1>
                <p>Cloud service is running 24/7 on Google Cloud Run.</p>
                <div class="roster">
                    <h3 style="margin-top: 0; color: #6366f1;">Monitored NBA Roster</h3>
                    <ul>
                        {"".join(f"<li>{player}</li>" for player in roster_list)}
                    </ul>
                </div>
            </div>
        </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)

@app.get("/api/deals", response_model=List[DetectedDeal])
def get_deals():
    """Returns the list of detected sports card deals for the glassmorphic dashboard."""
    return active_deals

class ApprovalRequest(BaseModel):
    deal_id: str

@app.post("/api/approve")
def approve_deal(req: ApprovalRequest):
    """Sets a card deal's status to 'Approved' for immediate sniper bidding."""
    global active_deals
    for d in active_deals:
        if d.deal_id == req.deal_id:
            d.status = "Approved"
            logging.info(f"🎯 CLOUD SNIPER: Deal {req.deal_id} approved for 3s bidding.")
            return {"status": "success", "message": f"Deal {req.deal_id} approved for active sniping queue."}
    raise HTTPException(status_code=404, detail="Deal not found")

if __name__ == "__main__":
    # Cloud Run passes the port to bind to via the $PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
