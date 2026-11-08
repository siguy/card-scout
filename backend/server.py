"""FastAPI server: scheduler + REST endpoints for the dashboard.

Run locally:
    uvicorn backend.server:app --reload --port 8080
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from . import db
from .config import load_config
from .ingestor import scan_once
from .models import BidOutcome, DetectedDeal
from .sniper import make_sniper

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger("server")

config = load_config()
sniper = make_sniper(config)

app = FastAPI(title="Card Scout", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _scout_loop():
    log.info("scout loop starting (every %ss)", config.ingestor.poll_seconds)
    while True:
        try:
            await asyncio.to_thread(scan_once, config)
        except Exception:
            log.exception("scan_once failed")
        await asyncio.sleep(config.ingestor.poll_seconds)


@app.on_event("startup")
async def on_startup():
    db.init()
    if os.getenv("CARD_SCOUT_DISABLE_LOOP") != "1":
        asyncio.create_task(_scout_loop())


@app.get("/", response_class=HTMLResponse)
def root():
    return HTMLResponse(
        "<h1>Card Scout API</h1>"
        "<p>See <code>/api/deals</code>, <code>/api/refresh</code>, <code>/docs</code>.</p>"
    )


@app.get("/api/deals", response_model=List[DetectedDeal])
def get_deals(status: Optional[str] = None):
    statuses = [s.strip() for s in status.split(",")] if status else None
    return db.list_deals(statuses)


@app.get("/api/deals/{deal_id}", response_model=DetectedDeal)
def get_deal(deal_id: str):
    deal = db.get_deal(deal_id)
    if not deal:
        raise HTTPException(404, "deal not found")
    return deal


@app.post("/api/refresh")
async def refresh():
    deals = await asyncio.to_thread(scan_once, config)
    return {"scanned": len(deals), "approved": sum(1 for d in deals if d.status == "approved")}


class StatusChange(BaseModel):
    status: str  # approved | rejected | snipe_queued


@app.post("/api/deals/{deal_id}/status")
def change_status(deal_id: str, change: StatusChange):
    allowed = {"approved", "rejected", "snipe_queued", "detected"}
    if change.status not in allowed:
        raise HTTPException(400, f"status must be one of {allowed}")
    if not db.set_deal_status(deal_id, change.status):
        raise HTTPException(404, "deal not found")
    return {"deal_id": deal_id, "status": change.status}


class SnipeRequest(BaseModel):
    max_bid: Optional[float] = None  # if omitted, uses deal.max_bid


@app.post("/api/deals/{deal_id}/snipe")
def snipe(deal_id: str, req: SnipeRequest):
    deal = db.get_deal(deal_id)
    if not deal:
        raise HTTPException(404, "deal not found")
    max_bid = req.max_bid if req.max_bid is not None else deal.max_bid
    if max_bid > config.risk.max_bid_per_card:
        raise HTTPException(
            400, f"max_bid ${max_bid:.2f} exceeds risk cap ${config.risk.max_bid_per_card:.2f}"
        )
    result = sniper.queue(deal, max_bid)
    db.set_deal_status(deal_id, "snipe_queued")
    return result


@app.post("/api/deals/{deal_id}/outcome")
def record_outcome(deal_id: str, outcome: BidOutcome):
    outcome.deal_id = deal_id
    db.record_outcome(outcome)
    if outcome.won is True:
        db.set_deal_status(deal_id, "won")
    elif outcome.won is False:
        db.set_deal_status(deal_id, "lost")
    return {"ok": True}


@app.get("/api/config")
def get_config():
    return config.model_dump()


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("backend.server:app", host="0.0.0.0", port=port, reload=False)
