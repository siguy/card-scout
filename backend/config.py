"""Loads watchlist.yaml and config.yaml. Single source of truth for runtime config."""
import os
from pathlib import Path
from typing import List
import yaml
import pydantic

ROOT = Path(__file__).resolve().parent.parent


class PlayerWatch(pydantic.BaseModel):
    name: str
    queries: List[str]


class Watchlist(pydantic.BaseModel):
    players: List[PlayerWatch]


class CompsConfig(pydantic.BaseModel):
    lookback_days: int = 90
    min_comps: int = 5
    max_cv: float = 0.35
    cache_minutes: int = 60


class RiskConfig(pydantic.BaseModel):
    max_bid_per_card: float = 5000
    daily_budget: float = 5000


class IngestorConfig(pydantic.BaseModel):
    poll_seconds: int = 120
    per_query_limit: int = 10
    max_seconds_remaining: int = 172800


class SniperConfig(pydantic.BaseModel):
    mode: str = "manual"
    ping_seconds_before_close: int = 60


class Config(pydantic.BaseModel):
    target_margin: float = 0.30
    comps: CompsConfig = CompsConfig()
    risk: RiskConfig = RiskConfig()
    ingestor: IngestorConfig = IngestorConfig()
    sniper: SniperConfig = SniperConfig()


def load_config() -> Config:
    path = Path(os.getenv("CARD_SCOUT_CONFIG", ROOT / "config.yaml"))
    with open(path) as f:
        return Config(**yaml.safe_load(f))


def load_watchlist() -> Watchlist:
    path = Path(os.getenv("CARD_SCOUT_WATCHLIST", ROOT / "watchlist.yaml"))
    with open(path) as f:
        return Watchlist(**yaml.safe_load(f))


def db_path() -> Path:
    p = Path(os.getenv("CARD_SCOUT_DB", ROOT / "data" / "card_scout.db"))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
