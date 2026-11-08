# Card Scout

A small system that watches eBay for undervalued NBA cards, scores them
against recent sold comps, and queues good deals for a manual snipe bid.

Built by Simon + Cooper (age 12½) as a learning project. Code is meant to be
read top-to-bottom by a smart kid — clear modules, real math, no fake magic.

## How it works

```
watchlist.yaml ──► Ingestor ──► eBay Browse API (live auctions)
                         │
                         ▼
                  Comp Engine ──► scrape eBay sold listings (last 90d)
                         │
                         ▼
                  Deal Evaluator ──► fair value, max bid, confidence
                         │
                         ▼
                     SQLite ──► /api/deals ──► React dashboard
                                                │
                                                ▼
                                          You approve
                                                │
                                                ▼
                                      Sniper (manual): pings you
                                      at T-60s, opens eBay link
                                      pre-filled with your max bid
```

## Honest scope

- **eBay only.** Whatnot has no public API and is deferred.
- **Graded + raw.** Raw cards are valued against raw comps only; we don't
  predict grading outcomes yet.
- **Manual sniper.** eBay doesn't expose a public bidding API. We ping you
  when an approved auction is closing; eBay's own proxy bidding handles the
  last-second math once you place your max bid. (See `backend/sniper.py`
  for the full explanation, including how we'd wire up Gixen later.)
- **No learning loop yet.** Every decision and outcome is recorded in SQLite
  so we can analyze later, but the comp engine doesn't self-tune.

## Setup

```bash
# 1. Backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. eBay credentials (production keys; sandbox is mostly empty for cards)
cp .env.example .env
# Fill in EBAY_CLIENT_ID and EBAY_CLIENT_SECRET from
# https://developer.ebay.com/my/keys

# 3. Run the backend
.venv/bin/uvicorn backend.server:app --reload --port 8080

# 4. In another terminal, run the dashboard
npm install
npm run dev
# Dashboard → http://localhost:5173
```

The backend starts a background scout loop (every 120s by default; tunable
in `config.yaml`). You can also force a scan from the dashboard ("Scan now")
or via `POST /api/refresh`.

## Tests

```bash
.venv/bin/pytest backend/tests -q
```

## Files

```
backend/
  config.py          load watchlist.yaml + config.yaml
  models.py          shared Pydantic types
  db.py              SQLite schema + helpers
  ebay_client.py     OAuth + Browse API
  title_parser.py    eBay title → CardModel (regex; imperfect; logged)
  comp_engine.py     scrape sold listings, median + confidence
  deal_evaluator.py  margin math, max bid, status
  ingestor.py        the scan loop
  sniper.py          ManualSniper (today) + GixenSniper (stub)
  server.py          FastAPI app + scheduler
  tests/             pure-Python tests, no network
config.yaml          margin %, comp settings, risk caps, sniper mode
watchlist.yaml       players + eBay search queries
data/                SQLite DB (gitignored)
```

## Configuration knobs you'll actually touch

- `config.yaml → target_margin`: default 0.30. A deal must be at least 30%
  below comp median (after shipping) to auto-approve.
- `config.yaml → comps.min_comps`: default 5. Below this, we mark confidence
  "low" and never auto-approve.
- `config.yaml → risk.max_bid_per_card`: hard cap on any suggested max bid.
- `watchlist.yaml`: the players + search queries. Edit freely.

## What's intentionally missing (and where to add it)

- **Gixen integration.** Stub in `backend/sniper.py`. Wire up once you have
  an account. Replace `GixenSniper.queue()` with a POST to their API.
- **Outcome-driven learning.** Outcomes table exists; analysis script does
  not. Once we have a few months of data, write `analysis/calibration.py`
  that scores predicted-vs-actual FMV by bucket.
- **Real auth.** The API is wide open. Fine for `localhost`; lock down
  before deploying anywhere public.
- **Photo-based gradeability scoring** for raw cards. Real ML work; v2.

## Cloud deploy (optional)

`deploy_cloud_run.sh` still exists from the original template. The Dockerfile
has been updated to use the real dependencies. If you want to run this
24/7 you'll also need to set `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET` as
secrets in Cloud Run, and mount a persistent disk for `data/card_scout.db`
(otherwise the DB resets on every cold start).
