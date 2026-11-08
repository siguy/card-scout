# Card Scout — TODO / Roadmap

Living list of what's next, grouped by horizon. Things at the top are
small enough for a session; things at the bottom are real projects.

## Near-term polish (a session each)

- [ ] **Wire CompsModal to real comp samples.** Backend already returns
  `deal.comps.samples` (up to 10). The modal currently renders whatever
  was passed in; show price, date, title, link, and a tiny histogram.
- [ ] **Outcome capture in the dashboard.** When a snipe-queued deal's
  auction has ended, prompt: "Did you win? Final price?" → POST to
  `/api/deals/{id}/outcome`. Without this the learning loop has no data.
- [ ] **Filter / sort the deal list.** Filters: confidence (high only),
  status (approved / detected / snipe_queued), time-to-close (<1h, <24h).
  Sort: discount %, time remaining, fmv.
- [ ] **Persist roster edits.** Right now adding/removing a player from
  the dashboard is UI-only. Either save to `watchlist.yaml` server-side
  or make the watchlist DB-backed.
- [ ] **Skip BIN listings cleanly.** `search_auctions` already filters
  to auctions, but BIN-with-best-offer can sneak in; ingestor should
  drop them since the sniper assumes a close time.
- [ ] **Backoff + rate limiting on the sold-comps scraper.** A scan can
  hit eBay 20+ times in a minute. Add 1–2s jitter between requests and
  retry-with-backoff on 429/503. Right now we'd get blocked under load.
- [ ] **Better title parser misclass logging.** When `year == 0` or
  `brand == "Unknown"`, log the raw title to a `parse_failures` table
  so we can review and improve the regex.

## Sniper

- [ ] **Gixen integration** (`backend/sniper.py → GixenSniper.queue`).
  Sign up at gixen.com, get API URL + your eBay-linked credentials,
  POST listing + max bid. Set `config.yaml → sniper.mode: gixen` to
  enable. Keep ManualSniper as a fallback.
- [ ] **Snipe queue worker.** Today the manual sniper just records intent.
  Add a background task that, for each `snipe_queued` deal where
  `T-60s` has arrived, writes a row to a `pings` table the UI surfaces
  as a toast/notification.
- [ ] **Browser-push notifications** so you don't have to keep the
  dashboard tab open to see the T-60s ping. (Service worker + Notification API.)

## Comps / valuation

- [ ] **Card Ladder as a second source** (paid API). Blend with eBay
  median; weight by recency and per-source confidence.
- [ ] **130point.com fallback.** Free, aggregates eBay sold data nicely;
  good redundancy if eBay's HTML breaks our scraper.
- [ ] **Per-parallel comp matching.** Today "Silver Prizm" comps include
  any silver. Need to distinguish base / silver / red / gold / etc., and
  serial-numbered parallels (#/99, #/25). Big lift; biggest accuracy win.
- [ ] **Apply for eBay Marketplace Insights API access.** Cleanest sold
  data, no scraping. Approval is slow (weeks); apply early.

## Learning loop (needs real data first)

- [ ] **Calibration report.** Once we have ≥50 outcomes, write
  `analysis/calibration.py`: for each (player, brand, grade) bucket,
  compare predicted FMV vs actual final auction price. Report bias
  (do we systematically over/under-value?) and variance.
- [ ] **Adaptive `max_cv` per bucket.** Some cards naturally trade with
  high variance; others tight. Per-bucket confidence thresholds beat
  one global cutoff.
- [ ] **Predicted-resale tracker.** 30/60/90 days after a win, re-check
  the comp engine and record actual fluctuation. Tells us if our FMV
  estimate held up.

## Bigger pieces (real projects, not sessions)

- [ ] **Photo-based gradeability agent.** For raw cards: pull listing
  photos, run a vision model to score centering / corners / edges /
  surface, estimate P(PSA 10). Lets us value raw cards against graded
  comps instead of only raw comps. **Good Cooper project — concrete,
  tactile, lots to learn about CV.**
- [ ] **Whatnot exploration.** No public API; live video auctions.
  Probably starts as a scraper of the public-discovery pages, then
  decision on whether the engineering pain is worth it vs eBay's volume.
- [ ] **Watchlist-suggestion agent.** Watches NBA performance + card
  market velocity (rising volume, rising median) and proposes players
  to add. Outputs a weekly digest; humans approve before changes land
  in `watchlist.yaml`.
- [ ] **Multi-sport.** Extend the watchlist + parser for MLB / NFL /
  soccer. Brand+year heuristics differ a lot; not a free extension.

## Infrastructure / ops

- [ ] **Auth on the API.** Right now anyone who hits `/api/snipe` can
  queue a bid. Add a simple bearer token before deploying anywhere
  beyond localhost.
- [ ] **Persistent storage in Cloud Run.** Cold starts reset SQLite
  today. Either mount a volume or migrate to Postgres / Firestore.
- [ ] **Structured logging + metrics.** Count scans, listings ingested,
  deals approved, snipes queued. Useful when debugging "why no deals?"
- [ ] **GitHub Actions CI.** Run `pytest backend/tests` + `npm run build`
  on every PR. Today nothing runs.

## Things we intentionally are NOT doing

(Keep this list honest — it's the reason this project will ship.)

- Direct eBay bid placement via API. eBay doesn't allow it; we'd get
  account-banned. Manual + Gixen are the only sane paths.
- Real-time scraping with browser automation against eBay/Whatnot from
  a server. High account risk, captcha, ToS issues. Only as a local
  power-user tool, never as the default.
- Fancy ML before we have data. Calibrate the rules-based scorer first.
- A general-purpose "agent framework" layer. FastAPI + a scheduler does
  the job; adding LangChain/Antigravity/etc. just adds breakage surface.
