"""Estimates fair market value from recent sold listings on eBay.

How (for Cooper):
1. Build a search URL for sold + completed listings of this exact card.
2. Download the search-results HTML.
3. Parse out the prices and dates with BeautifulSoup.
4. Drop comps outside our lookback window.
5. Compute median, mean, stdev. The MEDIAN is what we trust as fair value
   (one weird $50k sale doesn't move it; one weird sale ruins a mean).
6. The "coefficient of variation" (stdev/median) tells us how noisy the data is.
   High CV = comps disagree = low confidence = don't auto-flag as a deal.

Why scrape instead of using the API: eBay's Browse API only returns ACTIVE
listings. The Marketplace Insights API gives sold data but requires special
access. Scraping the public sold-listings page is the standard workaround.
It's fragile — eBay can change the HTML and break us. Treat it that way.
"""
from __future__ import annotations

import logging
import random
import re
import statistics
import time
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from .config import Config, load_config
from .db import cache_get, cache_put
from .models import CardModel, CompSummary, HistoricalComp

log = logging.getLogger("comp_engine")

SOLD_URL = "https://www.ebay.com/sch/i.html"

# Full browser-like header set. eBay 403s requests that look like Python
# even when User-Agent is set — they also check Accept, sec-ch-ua, etc.
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
        "image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": '"Chromium";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


_session: Optional[requests.Session] = None


def _get_session() -> requests.Session:
    """Persistent session — first request to ebay.com seeds cookies that
    subsequent search requests need to avoid 403."""
    global _session
    if _session is not None:
        return _session
    s = requests.Session()
    s.headers.update(BROWSER_HEADERS)
    try:
        s.get("https://www.ebay.com/", timeout=10)
    except requests.RequestException as exc:
        log.warning("session warm-up failed: %s", exc)
    _session = s
    return s



def _build_query(card: CardModel) -> str:
    parts = [str(card.year), card.brand, card.player_name, card.card_type]
    if card.graded and card.grader and card.grade is not None:
        grade_str = (
            str(int(card.grade)) if card.grade.is_integer() else str(card.grade)
        )
        parts.append(f"{card.grader} {grade_str}")
    return " ".join(parts)


def _parse_price(text: str) -> Optional[float]:
    # eBay shows "$1,234.56" or sometimes "$1,234.56 to $1,500.00" for ranges.
    m = re.search(r"\$([\d,]+\.\d{2})", text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


_DATE_RE = re.compile(r"Sold\s+(\w+ \d{1,2}, \d{4})", re.I)


def _parse_date(text: str) -> Optional[datetime]:
    m = _DATE_RE.search(text)
    if not m:
        return None
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(m.group(1), fmt)
        except ValueError:
            continue
    return None


def _fetch_with_retry(url: str, max_attempts: int = 3) -> Optional[requests.Response]:
    """GET with full browser headers + persistent session + backoff.
    Returns None if we ultimately fail; the caller decides what to do."""
    session = _get_session()
    for attempt in range(1, max_attempts + 1):
        try:
            # Random jitter so we don't hammer at predictable intervals.
            time.sleep(random.uniform(0.6, 1.4))
            resp = session.get(url, timeout=15)
        except requests.RequestException as exc:
            log.warning("comp request error (attempt %d): %s", attempt, exc)
            continue
        if resp.status_code == 200:
            return resp
        if resp.status_code in (429, 503):
            backoff = 2 ** attempt + random.random()
            log.warning("comp request %s; backing off %.1fs", resp.status_code, backoff)
            time.sleep(backoff)
            continue
        if resp.status_code == 403:
            log.warning("comp request 403 (attempt %d). May be bot-blocked.", attempt)
            # Drop the session so next attempt gets a fresh cookie warm-up.
            global _session
            _session = None
            continue
        log.warning("comp request unexpected status %s", resp.status_code)
        return None
    return None


def _fetch_from_ebay(query: str, lookback_days: int) -> List[HistoricalComp]:
    params = {
        "_nkw": query,
        "_sacat": "0",
        "LH_Sold": "1",
        "LH_Complete": "1",
        "_ipg": "60",
    }
    url = f"{SOLD_URL}?{urllib.parse.urlencode(params)}"
    log.info("scraping eBay sold comps: %s", query)
    resp = _fetch_with_retry(url)
    if resp is None:
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)
    comps: List[HistoricalComp] = []

    for item in soup.select("li.s-item"):
        title_el = item.select_one(".s-item__title")
        price_el = item.select_one(".s-item__price")
        date_el = item.select_one(".s-item__caption--signal, .s-item__title--tagblock")
        link_el = item.select_one("a.s-item__link")
        if not (title_el and price_el):
            continue
        title = title_el.get_text(strip=True)
        if title.lower().startswith("shop on ebay"):
            continue
        price = _parse_price(price_el.get_text())
        if price is None or price <= 0:
            continue
        date = _parse_date(item.get_text(" ", strip=True)) if not date_el else _parse_date(date_el.get_text())
        if date is None:
            # If we can't read the date, assume it's recent (within lookback) so we don't drop everything.
            date = datetime.utcnow()
        if date < cutoff:
            continue
        comps.append(
            HistoricalComp(
                sale_price=price,
                sale_date=date,
                title=title,
                url=link_el["href"] if link_el and link_el.has_attr("href") else None,
                source="eBay Sold",
            )
        )
    log.info("found %d comps for %r", len(comps), query)
    return comps


def fetch_sold_listings(query: str, lookback_days: int) -> List[HistoricalComp]:
    """Public entry. Tries eBay first; future fallback sources can chain here.

    If eBay returns 403 consistently (bot detection), see TODO.md — the next
    step is wiring 130point.com as a secondary source.
    """
    return _fetch_from_ebay(query, lookback_days)


def _drop_outliers(prices: List[float]) -> List[float]:
    """Remove obvious garbage. We use the IQR fence — standard, robust."""
    if len(prices) < 4:
        return prices
    s = sorted(prices)
    q1 = s[len(s) // 4]
    q3 = s[(3 * len(s)) // 4]
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return [p for p in prices if lo <= p <= hi]


def summarize(comps: List[HistoricalComp], min_comps: int, max_cv: float) -> CompSummary:
    if not comps:
        return CompSummary(n=0, median=0, mean=0, stdev=0, cv=0, confidence="none", samples=[])
    prices = _drop_outliers([c.sale_price for c in comps])
    n = len(prices)
    if n == 0:
        return CompSummary(n=0, median=0, mean=0, stdev=0, cv=0, confidence="none", samples=comps)
    median = statistics.median(prices)
    mean = statistics.fmean(prices)
    stdev = statistics.pstdev(prices) if n > 1 else 0.0
    cv = stdev / median if median else 0.0
    if n < min_comps or cv > max_cv:
        confidence = "low"
    else:
        confidence = "high"
    return CompSummary(
        n=n,
        median=round(median, 2),
        mean=round(mean, 2),
        stdev=round(stdev, 2),
        cv=round(cv, 3),
        confidence=confidence,
        samples=comps[:10],
    )


def fair_value(card: CardModel, config: Optional[Config] = None) -> CompSummary:
    """Public entry point. Cached by card.comp_key()."""
    cfg = config or load_config()
    key = card.comp_key()
    cached = cache_get(key, cfg.comps.cache_minutes * 60)
    if cached:
        return CompSummary.model_validate(cached)
    try:
        comps = fetch_sold_listings(_build_query(card), cfg.comps.lookback_days)
    except Exception as exc:  # network or HTML changes
        log.warning("comp fetch failed for %s: %s", card.identifier(), exc)
        return CompSummary(n=0, median=0, mean=0, stdev=0, cv=0, confidence="none", samples=[])
    summary = summarize(comps, cfg.comps.min_comps, cfg.comps.max_cv)
    cache_put(key, summary.model_dump(mode="json"))
    return summary
