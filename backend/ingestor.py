"""Pulls live auctions from eBay, normalizes, evaluates, persists.

One run of `scan_once()`:
    for each player in watchlist:
        for each query for that player:
            ask eBay Browse API for active auctions
            parse each result into a CardModel + ActiveListing
            call DealEvaluator (which pulls comps)
            save the DetectedDeal to SQLite
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from . import db
from .config import Config, load_config, load_watchlist
from .deal_evaluator import DealEvaluator
from .ebay_client import EbayClient
from .models import ActiveListing, DetectedDeal
from .title_parser import parse_title

log = logging.getLogger("ingestor")


def _parse_end_time(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _seconds_remaining(end: Optional[datetime]) -> Optional[float]:
    if not end:
        return None
    now = datetime.now(tz=end.tzinfo or timezone.utc)
    return (end - now).total_seconds()


def _to_listing(item: dict, hint_player: str) -> Optional[ActiveListing]:
    try:
        price = float(item.get("price", {}).get("value", "0") or 0)
    except (TypeError, ValueError):
        return None
    if price <= 0:
        return None
    shipping = 0.0
    options = item.get("shippingOptions") or []
    if options:
        try:
            shipping = float(options[0].get("shippingCost", {}).get("value", "0") or 0)
        except (TypeError, ValueError):
            shipping = 0.0
    title = item.get("title", "") or ""
    return ActiveListing(
        listing_id=item.get("itemId") or item.get("legacyItemId") or title[:40],
        title=title,
        card=parse_title(title, hint_player),
        current_price=price,
        shipping_cost=shipping,
        end_time=_parse_end_time(item.get("itemEndDate")),
        url=item.get("itemWebUrl", "https://www.ebay.com"),
        image_url=(item.get("image") or {}).get("imageUrl"),
    )


def scan_once(config: Optional[Config] = None) -> List[DetectedDeal]:
    cfg = config or load_config()
    watch = load_watchlist()
    client = EbayClient()
    if not client.authenticate():
        log.warning("eBay auth failed; ingestor will not pull live data this cycle.")
        return []

    evaluator = DealEvaluator(cfg)
    results: List[DetectedDeal] = []
    seen_ids: set[str] = set()

    for player in watch.players:
        for query in player.queries:
            items = client.search_auctions(query, limit=cfg.ingestor.per_query_limit)
            for item in items:
                listing = _to_listing(item, hint_player=player.name)
                if not listing:
                    continue
                if listing.listing_id in seen_ids:
                    continue
                seen_ids.add(listing.listing_id)
                seconds_left = _seconds_remaining(listing.end_time)
                if (
                    seconds_left is not None
                    and seconds_left > cfg.ingestor.max_seconds_remaining
                ):
                    continue
                # Skip cards we couldn't parse a year for — comp engine will be useless.
                if listing.card.year == 0:
                    continue
                deal = evaluator.evaluate(listing)
                db.upsert_deal(deal)
                results.append(deal)
    log.info(
        "scan complete: %d listings ingested, %d approved",
        len(results),
        sum(1 for d in results if d.status == "approved"),
    )
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    db.init()
    scan_once()
