"""Sniper interface, pluggable.

Honest answer about why we don't auto-bid (Cooper, read this):

eBay does NOT expose a public API for placing bids on auctions from a server.
The "Trading API" (PlaceOffer) is legacy and requires a per-user OAuth token
that you have to renew through a manual browser flow every 18 months. It's
also against eBay's terms to operate it without their explicit approval.

Real options:
  1. MANUAL: this app pings you when an approved auction is <60s from close.
     You open the eBay listing and place the bid yourself. eBay's own
     "proxy bidding" then bids on your behalf up to your max. Safe, legal,
     zero account risk. This is what we do for v1.

  2. THIRD-PARTY SNIPER (e.g. Gixen, AuctionSniper). EBay tolerates these.
     They log in as you and place the bid in the last few seconds. We'd POST
     the listing + max-bid to their API. Gixen is free for casual use.

  3. BROWSER AUTOMATION (Playwright on your own machine, logged in as you).
     Works, but risks captcha + account flags. Only for advanced users.

The ManualSniper class below = option 1. GixenSniper = option 2 (stub).
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from .config import Config, load_config
from .models import DetectedDeal

log = logging.getLogger("sniper")


class Sniper(ABC):
    @abstractmethod
    def queue(self, deal: DetectedDeal, max_bid: float) -> dict:
        """Record intent to bid. Returns a status dict for the API/UI."""


class ManualSniper(Sniper):
    """Records the intent locally; UI surfaces a 'Bid now on eBay' button."""

    def __init__(self, ping_seconds_before_close: int):
        self.ping_seconds_before_close = ping_seconds_before_close

    def queue(self, deal: DetectedDeal, max_bid: float) -> dict:
        end = deal.listing.end_time
        seconds_left: Optional[float] = None
        if end:
            now = datetime.now(tz=end.tzinfo or timezone.utc)
            seconds_left = max(0.0, (end - now).total_seconds())
        log.info(
            "MANUAL SNIPE queued: %s, max_bid=$%.2f, %s",
            deal.listing.title,
            max_bid,
            f"closes in {seconds_left:.0f}s" if seconds_left is not None else "BIN/no close time",
        )
        return {
            "mode": "manual",
            "deal_id": deal.deal_id,
            "max_bid": max_bid,
            "seconds_left": seconds_left,
            "ping_at_seconds_left": self.ping_seconds_before_close,
            "bid_url": deal.listing.url,
            "instructions": (
                f"When this auction is <{self.ping_seconds_before_close}s from close, "
                f"open the eBay link and place a bid of ${max_bid:.2f}. "
                "eBay's proxy bidding will then bid for you up to that ceiling."
            ),
        }


class GixenSniper(Sniper):
    """Stub. Wire up once you have a Gixen account + API key.

    Endpoint reference: https://www.gixen.com/main/api.php
    """

    def queue(self, deal: DetectedDeal, max_bid: float) -> dict:
        log.warning("GixenSniper not implemented; falling back to manual.")
        return ManualSniper(ping_seconds_before_close=60).queue(deal, max_bid)


def make_sniper(config: Optional[Config] = None) -> Sniper:
    cfg = config or load_config()
    if cfg.sniper.mode == "gixen":
        return GixenSniper()
    return ManualSniper(cfg.sniper.ping_seconds_before_close)
