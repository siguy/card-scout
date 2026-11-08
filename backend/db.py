"""SQLite persistence. Small and explicit.

Why SQLite for v1 (for Cooper): one file, no server to run, opens in any DB
browser, fine for tens of thousands of listings. We'd move to Postgres only
when we have multiple machines hitting the same data.
"""
import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator, List, Optional

from .config import db_path
from .models import BidOutcome, DetectedDeal

_lock = threading.Lock()
_SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
    listing_id TEXT PRIMARY KEY,
    payload    TEXT NOT NULL,
    seen_at    TEXT NOT NULL,
    end_time   TEXT
);

CREATE TABLE IF NOT EXISTS deals (
    deal_id    TEXT PRIMARY KEY,
    listing_id TEXT NOT NULL,
    payload    TEXT NOT NULL,
    status     TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS deals_status ON deals(status);

CREATE TABLE IF NOT EXISTS outcomes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id     TEXT NOT NULL,
    payload     TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS comp_cache (
    cache_key  TEXT PRIMARY KEY,
    payload    TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);
"""


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(db_path()))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init() -> None:
    with connect() as conn:
        conn.executescript(_SCHEMA)


def upsert_deal(deal: DetectedDeal) -> None:
    now = datetime.utcnow().isoformat()
    payload = deal.model_dump_json()
    with _lock, connect() as conn:
        conn.execute(
            """
            INSERT INTO listings (listing_id, payload, seen_at, end_time)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(listing_id) DO UPDATE SET
                payload=excluded.payload,
                seen_at=excluded.seen_at,
                end_time=excluded.end_time
            """,
            (
                deal.listing.listing_id,
                deal.listing.model_dump_json(),
                now,
                deal.listing.end_time.isoformat() if deal.listing.end_time else None,
            ),
        )
        existing = conn.execute(
            "SELECT status FROM deals WHERE deal_id = ?", (deal.deal_id,)
        ).fetchone()
        # Preserve human-set status (approved/rejected/snipe_queued) across re-scans.
        keep_statuses = {"approved", "rejected", "snipe_queued", "won", "lost"}
        status = (
            existing["status"]
            if existing and existing["status"] in keep_statuses
            else deal.status
        )
        conn.execute(
            """
            INSERT INTO deals (deal_id, listing_id, payload, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(deal_id) DO UPDATE SET
                payload=excluded.payload,
                status=excluded.status,
                updated_at=excluded.updated_at
            """,
            (deal.deal_id, deal.listing.listing_id, payload, status, now, now),
        )


def get_deal(deal_id: str) -> Optional[DetectedDeal]:
    with connect() as conn:
        row = conn.execute(
            "SELECT payload, status FROM deals WHERE deal_id = ?", (deal_id,)
        ).fetchone()
    if not row:
        return None
    deal = DetectedDeal.model_validate_json(row["payload"])
    deal.status = row["status"]
    return deal


def set_deal_status(deal_id: str, status: str) -> bool:
    now = datetime.utcnow().isoformat()
    with _lock, connect() as conn:
        cur = conn.execute(
            "UPDATE deals SET status = ?, updated_at = ? WHERE deal_id = ?",
            (status, now, deal_id),
        )
        return cur.rowcount > 0


def list_deals(statuses: Optional[List[str]] = None) -> List[DetectedDeal]:
    sql = "SELECT payload, status FROM deals"
    params: tuple = ()
    if statuses:
        sql += f" WHERE status IN ({','.join('?' * len(statuses))})"
        params = tuple(statuses)
    sql += " ORDER BY updated_at DESC"
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    out = []
    for r in rows:
        d = DetectedDeal.model_validate_json(r["payload"])
        d.status = r["status"]
        out.append(d)
    return out


def record_outcome(outcome: BidOutcome) -> None:
    with _lock, connect() as conn:
        conn.execute(
            "INSERT INTO outcomes (deal_id, payload, recorded_at) VALUES (?, ?, ?)",
            (outcome.deal_id, outcome.model_dump_json(), outcome.recorded_at.isoformat()),
        )


def cache_get(key: str, max_age_seconds: int) -> Optional[dict]:
    with connect() as conn:
        row = conn.execute(
            "SELECT payload, fetched_at FROM comp_cache WHERE cache_key = ?", (key,)
        ).fetchone()
    if not row:
        return None
    age = (datetime.utcnow() - datetime.fromisoformat(row["fetched_at"])).total_seconds()
    if age > max_age_seconds:
        return None
    return json.loads(row["payload"])


def cache_put(key: str, payload: dict) -> None:
    with _lock, connect() as conn:
        conn.execute(
            """
            INSERT INTO comp_cache (cache_key, payload, fetched_at)
            VALUES (?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                payload=excluded.payload,
                fetched_at=excluded.fetched_at
            """,
            (key, json.dumps(payload), datetime.utcnow().isoformat()),
        )
