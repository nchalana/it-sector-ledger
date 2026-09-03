# IT Sector Ledger — Live

A personal, read-only dashboard tracking 100 IT-linked, publicly listed
companies worldwide. Prices and returns refresh automatically from a free
data feed; no server, no paid API, no trading. Available in English and
Hindi.

**The 100 companies, in four categories:**
- **Indian IT (9)** — TCS, Infosys, Wipro, HCL Technologies, Tech Mahindra,
  LTIMindtree, Persistent Systems, Coforge, Mphasis.
- **ER&D / OEM (15)** — Indian engineering-R&D / product-engineering firms,
  e.g. LTTS, Tata Elxsi, KPIT, Cyient, Tata Technologies, Mastek, Zensar,
  Happiest Minds, Sonata, Birlasoft, Newgen, Intellect Design, Firstsource,
  R Systems, Datamatics.
- **GSI (21)** — Global system integrators / IT services majors, e.g.
  Accenture, Cognizant, IBM, DXC, Kyndryl, Genpact, WNS, ExlService, Amdocs,
  EPAM, Globant, Endava, Concentrix, Unisys, Capgemini, Atos, Sopra Steria,
  Fujitsu, NEC, NTT Data.
- **GCC Parent (55)** — global MNCs whose large India Global Capability
  Centres make them relevant to the sector (not the GCC itself, the parent
  company), spanning BFSI, tech, telecom, retail, healthcare and
  industrials — e.g. JPMorgan, Goldman Sachs, HSBC, Standard Chartered,
  Deutsche Bank, Visa, Mastercard, Microsoft, Google, Amazon, Meta, Apple,
  Oracle, Salesforce, SAP, Nvidia, Verizon, Walmart, Target, Nike, Pfizer,
  AstraZeneca, GE, Boeing, Siemens, Honeywell, Caterpillar, and more.

**Each stock trades in its own native currency — there's no currency
conversion.** Indian tickers show ₹, US tickers show $, European tickers
show €, Japanese tickers show ¥, and the one London-listed stock (Standard
Chartered) shows £ — corrected for the fact that Yahoo Finance quotes LSE
stocks in pence, not pounds. Amounts across different currencies are
intentionally never added together or compared 1:1.

It has four views:
- **The board** — live price, day change, 1/3/5-year returns, ROE, net
  margin, debt/equity, a price-vs-moving-average trend badge, and a 14-day
  RSI reading. Click any column header to sort; star a row to add it to
  your watchlist (saved in your browser), and check "Watchlist only" to
  filter down to it. A category filter and search box work the whole list.
  Trend and RSI are descriptive (where the price sits relative to its own
  history) — not a buy/sell signal.
- **"If you invest 10,000 today"** — a short-term (1-day / 1-week / 2-week)
  view. This deliberately does **not** predict a return. No feed or model
  can tell you what you'll get "for sure" over a day or a week — short-term
  price moves are dominated by volatility, not predictable patterns. Instead
  it shows the *real historical range* of outcomes that holding period has
  actually produced over roughly the last two years (worst case, the middle
  80% of outcomes, and best case), so you can see the actual risk you'd be
  taking rather than a false promise. This view only shows companies that
  have a real fetched price history — no fabricated ranges for the 91
  companies still waiting on their first data pull (see "Known limitations").
- **Compare & correlate** — pick 2 or 3 companies to see their combined
  price trend (indexed to 100 so different price levels/currencies are
  comparable by shape) and the pairwise correlation of their daily returns.
  Useful for sanity-checking how much two stocks actually move together
  before treating them as diversified. Needs the separate daily history
  workflow to have run at least once (see below).
- **Company notes** — manual analyst-snapshot commentary, English only,
  covering just the original 9 Indian majors.

**Language:** an EN / हिं toggle in the top-right switches all interface
text (labels, captions, the disclaimer) between English and Hindi. Company
names, tickers, and all numbers stay as-is in both languages — translating
those would risk introducing errors. The "Company notes" section (the nine
original Indian majors' analyst commentary) also stays English-only, since
it's a manual research snapshot rather than generated UI text.

## How it works

- `scripts/fetch_quotes.py` pulls all 100 tickers from Yahoo Finance (via
  the `yfinance` library), computes price/returns, the historical
  1-day/1-week/2-week return distribution, 50/200-day moving averages,
  14-day RSI, and (where Yahoo has them) ROE/net margin/debt-equity, then
  writes one snapshot to `data/latest.json`. At 100 tickers the run takes a
  few minutes (there's a small pause between requests to stay polite to
  Yahoo's free feed) — that's normal, not a hang.
- `.github/workflows/update-quotes.yml` runs that script every 30 minutes
  during NSE trading hours (Mon–Fri) using GitHub Actions, and commits the
  updated JSON back to the repo. That schedule was set for the original
  9 NSE-listed companies — it does **not** line up with US, European, or
  Japanese market hours, so the 91 globally-listed additions will typically
  show a stale/previous-close price rather than a same-day one. See
  "Known limitations" and "Extending it later" if you want to widen the
  schedule.
- `scripts/fetch_quotes.py --with-history` (the same script, one extra
  flag) additionally trims each ticker's price history to the trailing
  ~2 years and writes `data/history.json`, which only the Compare &
  correlate view reads. `.github/workflows/update-history.yml` runs this
  once a day at 01:00 UTC — deliberately outside the 30-minute job's
  03:45–10:15 UTC window, so the two workflows never race to push at the
  same time. It's daily rather than every 30 minutes so 100 tickers × ~500
  daily prices doesn't bloat the repo with commits.
- `index.html` is a static page that fetches `data/latest.json` (and, for
  the Compare view, `data/history.json`) in the browser and renders all
  four views, in English or Hindi — no backend required.
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

4. **Run both workflows once by hand.** Go to the **Actions** tab:
   - Open "Update stock quotes" → **Run workflow**, for live prices.
   - Open "Update price history (daily)" → **Run workflow**, so the Compare
     & correlate view has something to show right away instead of waiting
     for its first scheduled run.

   Refresh your Pages URL afterward — the "Live prices as of…" badge should
   update, and Compare & correlate should render a chart once you pick 2-3
   companies.

After that, it runs itself: every 30 minutes during trading hours the price
workflow fetches fresh quotes and commits `data/latest.json`; once a day the
history workflow refreshes `data/history.json`. The page picks up changes
next time it's opened (or on manual refresh).

## Known limitations

- **Not tick-by-tick.** Yahoo Finance's free data typically runs
  15–20 minutes behind the actual market, and GitHub's scheduler can add a
  few more minutes of jitter under load. This is a research tool, not a
  trading terminal.
- **The schedule only lines up with NSE hours.** It fires every 30 minutes,
  Mon–Fri, ~9:15am–3:45pm IST. The 9 Indian majors refresh live through
  that window; the other 91 (US, European, Japanese listings) will show
  whatever their price was at the most recent run rather than a same-day
  quote, since their own markets are mostly closed while the workflow runs.
  Widen the cron schedule in `.github/workflows/update-quotes.yml` if you
  want closer-to-live coverage for those too (see "Extending it later").
- **Unofficial feed.** Yahoo Finance can occasionally return missing data
  for a run, especially at 100-ticker scale — the page just shows "No data
  this run" for that row and tries again next cycle.
- **91 of the 100 companies start as placeholders.** Only the original 9
  Indian majors ship with seed data. The other 91 show "Pending first
  fetch" until the workflow has run at least once in your repo and pulled
  real numbers for them — that's expected, not a bug.
- **ROE, margin, D/E, moving averages, and RSI all start blank for all 100
  companies, including the original 9.** These are newly added fields —
  even the 9 majors' seed data predates them. They fill in the first time
  the updated `fetch_quotes.py` runs in your repo. Coverage for ROE/margin/
  D-E will stay patchy outside the US and India even after that — Yahoo
  Finance's fundamentals data is inconsistent for other markets, and a
  missing value always shows "—", never a guess.
- **Compare & correlate needs the daily history workflow to have run.**
  Until then (or for a company it hasn't reached yet), picking that company
  shows an honest "no history data yet" message rather than a chart.
  `data/history.json` ships as an empty scaffold for the same reason the
  91 placeholders don't have invented numbers.
- **Sell-side signals and company notes are still manual, and only cover
  the original 9.** Analyst ratings, price targets, and earnings commentary
  aren't available from any free API for any of the 100 — the notes on the
  page are a snapshot from 1 Sep 2026 for the Indian majors only, and need
  a periodic manual (or separately scheduled) refresh, not this pipeline.
- **Hindi covers the interface, not the data or the notes.** Company
  names, tickers, and the "Company notes" section stay in English in both
  languages.
- **GitHub may pause scheduled workflows** after ~60 days with zero commits
  to the repo. In practice the workflow's own commits count as activity, so
  this shouldn't come up — but if the badge ever looks stale for days, check
  the Actions tab and re-run manually.
- This dashboard is informational only — see the disclaimer in the page
  footer. It doesn't place trades and isn't a substitute for advice from a
  registered investment adviser.

## Updating an existing deployment

If you already set this up once and are pulling in a newer version of
these files (e.g. sorting/watchlist, the new board columns, Compare &
correlate), you don't need to recreate the repo — just replace the
contents of the changed files in place:

- For `index.html`, `requirements.txt`, or `README.md`: Code tab → open the
  file → pencil/edit icon → select all → paste the new version → commit.
- For `scripts/fetch_quotes.py`, `data/latest.json`, and `data/history.json`
  (new file): navigate into the `scripts/` (or `data/`) folder first, then
  **Add file → Upload files** and drag in the single updated/new file —
  this is the reliable method if whole-folder drag-and-drop has given you
  trouble before.
- **New this round:** also add `.github/workflows/update-history.yml` the
  same way (navigate into `.github/workflows/`, Add file → Upload files).
  Without it, `data/history.json` never gets populated and Compare &
  correlate will keep showing the "no history data yet" message.

Then re-run both workflows once by hand (Actions → "Update stock quotes" →
Run workflow, and Actions → "Update price history (daily)" → Run workflow)
so everything gets its first real data pull instead of waiting for the
next scheduled tick.

## Extending it later

- **Automate the qualitative layer:** a second, slower scheduled job (e.g.
  a Claude-run daily/weekly task) could refresh the sell-side notes and
  write them into a second JSON file the page also reads.
- **Closer-to-live coverage for non-NSE listings:** add a second scheduled
  workflow (or widen the existing cron) to also run during US/European
  market hours, e.g. `cron: "*/30 13-21 * * 1-5"` for US hours in UTC.
- **More tickers or categories:** add entries to `COMPANIES` in
  `fetch_quotes.py` (and to `META` in `index.html` if you want sell-side
  commentary for them too).
- **More languages:** add another key alongside `en`/`hi` in the `I18N`
  object in `index.html` and a matching toggle button in `#lang-toggle`.
- **More than 3 in Compare & correlate:** the picker caps at 3 so the chart
  and correlation table stay readable and the color palette stays
  colorblind-safe; raising the cap means adding another validated series
  color and re-checking contrast before using it.
- **A shared watchlist across devices:** today's watchlist lives in one
  browser's `localStorage`, so it won't follow you to another device. A
  synced version would need somewhere to store it (e.g. a GitHub Gist via
  a simple auth flow) — a bigger change than this project's $0/no-backend
  scope currently covers.
