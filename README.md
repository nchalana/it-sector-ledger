# IT Sector Ledger — Live

A personal, read-only dashboard tracking nine NSE-listed Indian IT majors
(TCS, Infosys, Wipro, HCL Technologies, Tech Mahindra, LTIMindtree,
Persistent Systems, Coforge, Mphasis). Prices and returns refresh
automatically from a free data feed; no server, no paid API, no trading.

## How it works

- `scripts/fetch_quotes.py` pulls each ticker from Yahoo Finance (via the
  `yfinance` library) and writes one snapshot to `data/latest.json`.
- `.github/workflows/update-quotes.yml` runs that script every 30 minutes
  during NSE trading hours (Mon–Fri) using GitHub Actions, and commits the
  updated JSON back to the repo.
- `index.html` is a static page that fetches `data/latest.json` in the
  browser and renders the table — no backend required.
- GitHub Pages serves `index.html` straight from the repo.

Total running cost: **$0**, within GitHub's free tier at this scale.

## Setup (one-time, ~10 minutes)

1. **Create a repo.** On github.com, create a new **public** repository
   (private also works, but Pages is easiest on the free tier with a public
   repo). Push everything in this folder to it:
   ```
   git init
   git add .
   git commit -m "Initial commit: IT Sector Ledger live dashboard"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```

2. **Allow the workflow to push commits.** In the repo, go to
   **Settings → Actions → General → Workflow permissions** and select
   **"Read and write permissions."** Without this, the scheduled job can
   fetch prices but will fail to save them back to the repo.

3. **Turn on GitHub Pages.** Go to **Settings → Pages**, set
   **Source: Deploy from a branch**, branch **main**, folder **/ (root)**,
   and save. GitHub will give you a URL like
   `https://<your-username>.github.io/<repo-name>/` — that's your live
   dashboard.

4. **Run it once by hand.** Go to the **Actions** tab, open "Update stock
   quotes," and click **Run workflow** to trigger it immediately rather than
   waiting for the next scheduled tick. Refresh your Pages URL afterward —
   the "Live prices as of…" badge should update.

After that, it runs itself: every 30 minutes during trading hours, the
workflow fetches fresh quotes, commits `data/latest.json`, and the page
picks up the change next time it's opened (or on manual refresh).

## Known limitations

- **Not tick-by-tick.** Yahoo Finance's free NSE data typically runs
  15–20 minutes behind the actual market, and GitHub's scheduler can add a
  few more minutes of jitter under load. This is a research tool, not a
  trading terminal.
- **Unofficial feed.** Yahoo Finance doesn't officially support NSE and can
  occasionally return missing data for a run (the page just shows "No data
  this run" for that row and tries again next cycle).
- **Sell-side signals and company notes are still manual.** Analyst
  ratings, price targets, and earnings commentary aren't available from any
  free API — the notes on the page are a snapshot from 1 Sep 2026 and need
  a periodic manual (or separately scheduled) refresh, not this pipeline.
- **GitHub may pause scheduled workflows** after ~60 days with zero commits
  to the repo. In practice the workflow's own commits count as activity, so
  this shouldn't come up — but if the badge ever looks stale for days, check
  the Actions tab and re-run manually.
- This dashboard is informational only — see the disclaimer in the page
  footer. It doesn't place trades and isn't a substitute for advice from a
  registered investment adviser.

## Extending it later

- **More history for real sparklines:** have the workflow also append each
  day's close to a running CSV/JSON so the page can chart actual trend
  lines instead of point-in-time returns.
- **Automate the qualitative layer:** a second, slower scheduled job (e.g.
  a Claude-run daily/weekly task) could refresh the sell-side notes and
  write them into a second JSON file the page also reads.
- **More tickers:** add entries to `COMPANIES` in `fetch_quotes.py` and to
  the `META` object in `index.html`.
