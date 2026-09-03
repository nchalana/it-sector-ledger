#!/usr/bin/env python3
"""
Pulls quotes for the ~100 companies tracked in the IT Sector Ledger and
writes a single JSON snapshot to data/latest.json.

Universe spans four categories:
  - Indian IT majors (NSE)
  - Indian ER&D / OEM engineering-services firms (NSE)
  - Global System Integrators (GSI) - various exchanges
  - GCC-parent companies - global MNCs known for large India Global
    Capability Centres (the GCC itself isn't separately listed; this
    tracks the parent's stock)

Data source: Yahoo Finance (via the yfinance library) - free, no API key,
typically ~15-20 minutes delayed, and unofficial for most non-US exchanges.
At this larger scale, expect more per-run gaps than the original 9-ticker
version - the workflow just tries again on its next scheduled tick.

Prices stay in each company's own listing currency (no FX conversion) per
the "native currency" design choice - see README. One quirk handled
explicitly: the London Stock Exchange is quoted by Yahoo in pence (GBp),
not pounds, for tickers flagged `pence_quoted` below; those are divided by
100 so the displayed number is in GBP like everywhere else.
"""

import json
import sys
import time
from datetime import datetime, timezone, timedelta

import pandas as pd
import yfinance as yf

# ---------------------------------------------------------------------------
# Universe: 100 companies across 4 categories.
# ccy = the currency the price will be shown in (after any pence correction).
# pence_quoted = True only for the couple of LSE tickers Yahoo reports in GBp.
# ---------------------------------------------------------------------------

def co(ticker, name, full, category, ccy, pence_quoted=False):
    return {"ticker": ticker, "name": name, "full": full, "category": category,
            "ccy": ccy, "penceQuoted": pence_quoted}

COMPANIES = [
    # --- Indian IT majors (NSE, INR) ---
    co("TCS.NS", "TCS", "Tata Consultancy Services", "Indian IT", "INR"),
    co("INFY.NS", "Infosys", "Infosys Ltd", "Indian IT", "INR"),
    co("WIPRO.NS", "Wipro", "Wipro Ltd", "Indian IT", "INR"),
    co("HCLTECH.NS", "HCL Technologies", "HCL Technologies Ltd", "Indian IT", "INR"),
    co("TECHM.NS", "Tech Mahindra", "Tech Mahindra Ltd", "Indian IT", "INR"),
    co("LTIM.NS", "LTIMindtree", "LTIMindtree Ltd", "Indian IT", "INR"),
    co("PERSISTENT.NS", "Persistent Systems", "Persistent Systems Ltd", "Indian IT", "INR"),
    co("COFORGE.NS", "Coforge", "Coforge Ltd", "Indian IT", "INR"),
    co("MPHASIS.NS", "Mphasis", "Mphasis Ltd", "Indian IT", "INR"),

    # --- Indian ER&D / OEM engineering-services firms (NSE, INR) ---
    co("LTTS.NS", "L&T Technology Services", "L&T Technology Services Ltd", "ER&D / OEM", "INR"),
    co("TATAELXSI.NS", "Tata Elxsi", "Tata Elxsi Ltd", "ER&D / OEM", "INR"),
    co("KPITTECH.NS", "KPIT Technologies", "KPIT Technologies Ltd", "ER&D / OEM", "INR"),
    co("CYIENT.NS", "Cyient", "Cyient Ltd", "ER&D / OEM", "INR"),
    co("TATATECH.NS", "Tata Technologies", "Tata Technologies Ltd", "ER&D / OEM", "INR"),
    co("MASTEK.NS", "Mastek", "Mastek Ltd", "ER&D / OEM", "INR"),
    co("ZENSARTECH.NS", "Zensar Technologies", "Zensar Technologies Ltd", "ER&D / OEM", "INR"),
    co("HAPPSTMNDS.NS", "Happiest Minds", "Happiest Minds Technologies Ltd", "ER&D / OEM", "INR"),
    co("SONATSOFTW.NS", "Sonata Software", "Sonata Software Ltd", "ER&D / OEM", "INR"),
    co("BSOFT.NS", "Birlasoft", "Birlasoft Ltd", "ER&D / OEM", "INR"),
    co("NEWGEN.NS", "Newgen Software", "Newgen Software Technologies Ltd", "ER&D / OEM", "INR"),
    co("INTELLECT.NS", "Intellect Design Arena", "Intellect Design Arena Ltd", "ER&D / OEM", "INR"),
    co("FSL.NS", "Firstsource Solutions", "Firstsource Solutions Ltd", "ER&D / OEM", "INR"),
    co("RSYSTEMS.NS", "R Systems International", "R Systems International Ltd", "ER&D / OEM", "INR"),
    co("DATAMATICS.NS", "Datamatics Global Services", "Datamatics Global Services Ltd", "ER&D / OEM", "INR"),

    # --- Global System Integrators (various exchanges) ---
    co("ACN", "Accenture", "Accenture plc", "GSI", "USD"),
    co("CTSH", "Cognizant", "Cognizant Technology Solutions", "GSI", "USD"),
    co("IBM", "IBM", "International Business Machines", "GSI", "USD"),
    co("DXC", "DXC Technology", "DXC Technology Company", "GSI", "USD"),
    co("KD", "Kyndryl", "Kyndryl Holdings Inc", "GSI", "USD"),
    co("G", "Genpact", "Genpact Ltd", "GSI", "USD"),
    co("WNS", "WNS Global Services", "WNS (Holdings) Ltd", "GSI", "USD"),
    co("EXLS", "ExlService (EXL)", "ExlService Holdings Inc", "GSI", "USD"),
    co("DOX", "Amdocs", "Amdocs Ltd", "GSI", "USD"),
    co("EPAM", "EPAM Systems", "EPAM Systems Inc", "GSI", "USD"),
    co("GLOB", "Globant", "Globant SA", "GSI", "USD"),
    co("DAVA", "Endava", "Endava plc", "GSI", "USD"),
    co("CNXC", "Concentrix", "Concentrix Corporation", "GSI", "USD"),
    co("UIS", "Unisys", "Unisys Corporation", "GSI", "USD"),
    co("GIB", "CGI Inc", "CGI Inc", "GSI", "USD"),
    co("CAP.PA", "Capgemini", "Capgemini SE", "GSI", "EUR"),
    co("ATO.PA", "Atos", "Atos SE", "GSI", "EUR"),
    co("SOP.PA", "Sopra Steria", "Sopra Steria Group", "GSI", "EUR"),
    co("6702.T", "Fujitsu", "Fujitsu Ltd", "GSI", "JPY"),
    co("6501.T", "Hitachi", "Hitachi Ltd", "GSI", "JPY"),
    co("6701.T", "NEC Corporation", "NEC Corporation", "GSI", "JPY"),

    # --- GCC-parent companies: BFSI ---
    co("JPM", "JPMorgan Chase", "JPMorgan Chase & Co", "GCC Parent", "USD"),
    co("GS", "Goldman Sachs", "The Goldman Sachs Group", "GCC Parent", "USD"),
    co("MS", "Morgan Stanley", "Morgan Stanley", "GCC Parent", "USD"),
    co("C", "Citigroup", "Citigroup Inc", "GCC Parent", "USD"),
    co("BAC", "Bank of America", "Bank of America Corp", "GCC Parent", "USD"),
    co("WFC", "Wells Fargo", "Wells Fargo & Company", "GCC Parent", "USD"),
    co("AXP", "American Express", "American Express Company", "GCC Parent", "USD"),
    co("BCS", "Barclays", "Barclays plc (US ADR)", "GCC Parent", "USD"),
    co("HSBC", "HSBC Holdings", "HSBC Holdings plc (US ADR)", "GCC Parent", "USD"),
    co("STAN.L", "Standard Chartered", "Standard Chartered plc", "GCC Parent", "GBP", pence_quoted=True),
    co("DBK.DE", "Deutsche Bank", "Deutsche Bank AG", "GCC Parent", "EUR"),
    co("UBS", "UBS Group", "UBS Group AG", "GCC Parent", "USD"),
    co("V", "Visa", "Visa Inc", "GCC Parent", "USD"),
    co("MA", "Mastercard", "Mastercard Inc", "GCC Parent", "USD"),
    co("PYPL", "PayPal", "PayPal Holdings Inc", "GCC Parent", "USD"),
    co("BLK", "BlackRock", "BlackRock Inc", "GCC Parent", "USD"),
    co("SCHW", "Charles Schwab", "The Charles Schwab Corporation", "GCC Parent", "USD"),

    # --- GCC-parent companies: Tech / Software ---
    co("MSFT", "Microsoft", "Microsoft Corporation", "GCC Parent", "USD"),
    co("GOOGL", "Alphabet (Google)", "Alphabet Inc", "GCC Parent", "USD"),
    co("AMZN", "Amazon", "Amazon.com Inc", "GCC Parent", "USD"),
    co("META", "Meta Platforms", "Meta Platforms Inc", "GCC Parent", "USD"),
    co("AAPL", "Apple", "Apple Inc", "GCC Parent", "USD"),
    co("ORCL", "Oracle", "Oracle Corporation", "GCC Parent", "USD"),
    co("CRM", "Salesforce", "Salesforce Inc", "GCC Parent", "USD"),
    co("NOW", "ServiceNow", "ServiceNow Inc", "GCC Parent", "USD"),
    co("ADBE", "Adobe", "Adobe Inc", "GCC Parent", "USD"),
    co("SAP", "SAP", "SAP SE (US ADR)", "GCC Parent", "USD"),
    co("INTU", "Intuit", "Intuit Inc", "GCC Parent", "USD"),
    co("NVDA", "Nvidia", "NVIDIA Corporation", "GCC Parent", "USD"),
    co("INTC", "Intel", "Intel Corporation", "GCC Parent", "USD"),
    co("QCOM", "Qualcomm", "Qualcomm Inc", "GCC Parent", "USD"),
    co("TXN", "Texas Instruments", "Texas Instruments Inc", "GCC Parent", "USD"),

    # --- GCC-parent companies: Telecom ---
    co("VZ", "Verizon", "Verizon Communications Inc", "GCC Parent", "USD"),
    co("T", "AT&T", "AT&T Inc", "GCC Parent", "USD"),
    co("NOK", "Nokia", "Nokia Corporation (US ADR)", "GCC Parent", "USD"),
    co("ERIC", "Ericsson", "Telefonaktiebolaget LM Ericsson (US ADR)", "GCC Parent", "USD"),

    # --- GCC-parent companies: Retail / Consumer ---
    co("WMT", "Walmart", "Walmart Inc", "GCC Parent", "USD"),
    co("TGT", "Target", "Target Corporation", "GCC Parent", "USD"),
    co("HD", "Home Depot", "The Home Depot Inc", "GCC Parent", "USD"),
    co("LOW", "Lowe's", "Lowe's Companies Inc", "GCC Parent", "USD"),
    co("NKE", "Nike", "Nike Inc", "GCC Parent", "USD"),
    co("SBUX", "Starbucks", "Starbucks Corporation", "GCC Parent", "USD"),

    # --- GCC-parent companies: Healthcare / Pharma ---
    co("UNH", "UnitedHealth Group", "UnitedHealth Group Inc", "GCC Parent", "USD"),
    co("PFE", "Pfizer", "Pfizer Inc", "GCC Parent", "USD"),
    co("NVS", "Novartis", "Novartis AG (US ADR)", "GCC Parent", "USD"),
    co("AZN", "AstraZeneca", "AstraZeneca plc (US ADR)", "GCC Parent", "USD"),
    co("MDT", "Medtronic", "Medtronic plc", "GCC Parent", "USD"),
    co("ABBV", "AbbVie", "AbbVie Inc", "GCC Parent", "USD"),

    # --- GCC-parent companies: Industrials / Diversified ---
    co("GE", "GE Aerospace", "GE Aerospace", "GCC Parent", "USD"),
    co("BA", "Boeing", "The Boeing Company", "GCC Parent", "USD"),
    co("AIR.PA", "Airbus", "Airbus SE", "GCC Parent", "EUR"),
    co("SIE.DE", "Siemens", "Siemens AG", "GCC Parent", "EUR"),
    co("PHIA.AS", "Philips", "Koninklijke Philips NV", "GCC Parent", "EUR"),
    co("HON", "Honeywell", "Honeywell International Inc", "GCC Parent", "USD"),
    co("CAT", "Caterpillar", "Caterpillar Inc", "GCC Parent", "USD"),
]

OUTPUT_PATH = "data/latest.json"
HISTORY_OUTPUT_PATH = "data/history.json"
SCENARIO_WINDOW_DAYS = 504  # ~2 trading years
HISTORY_WINDOW_DAYS = 504  # ~2 trading years of daily closes, for the compare/correlate view
REQUEST_PAUSE_SECONDS = 0.25  # be gentle with Yahoo's unofficial endpoint at this scale


def pct_return(hist: pd.DataFrame, days: int):
    if hist.empty:
        return None
    latest_ts = hist.index[-1]
    target_ts = latest_ts - timedelta(days=days)
    past = hist[hist.index <= target_ts]
    if past.empty:
        return None
    past_price = float(past["Close"].iloc[-1])
    latest_price = float(hist["Close"].iloc[-1])
    if past_price == 0:
        return None
    return round((latest_price - past_price) / past_price * 100, 2)


def summarize(series: pd.Series):
    series = series.dropna()
    if series.empty:
        return None
    return {
        "min": round(float(series.min()), 1),
        "p10": round(float(series.quantile(0.10)), 1),
        "median": round(float(series.median()), 1),
        "p90": round(float(series.quantile(0.90)), 1),
        "max": round(float(series.max()), 1),
    }


def scenario_stats(hist: pd.DataFrame):
    window = hist.tail(SCENARIO_WINDOW_DAYS)["Close"]
    if len(window) < 30:
        return None
    daily = window.pct_change().dropna() * 100
    weekly = window.pct_change(5).dropna() * 100
    two_week = window.pct_change(10).dropna() * 100
    return {
        "day": summarize(daily),
        "week": summarize(weekly),
        "twoWeek": summarize(two_week),
        "sampleDays": int(len(window)),
    }


def moving_averages(hist: pd.DataFrame, divisor: float):
    close = hist["Close"]
    ma50 = round(float(close.tail(50).mean()) / divisor, 2) if len(close) >= 50 else None
    ma200 = round(float(close.tail(200).mean()) / divisor, 2) if len(close) >= 200 else None
    return ma50, ma200


def rsi14(hist: pd.DataFrame, period: int = 14):
    """Wilder's RSI over the trailing `period` sessions. Returns None if there
    isn't enough history yet."""
    close = hist["Close"]
    if len(close) < period + 1:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    last_gain, last_loss = float(avg_gain.iloc[-1]), float(avg_loss.iloc[-1])
    if last_loss == 0:
        return 100.0 if last_gain > 0 else None
    rs = last_gain / last_loss
    value = 100 - (100 / (1 + rs))
    return round(value, 1) if not pd.isna(value) else None


def fundamentals(info: dict):
    """ROE / net margin / debt-equity from yfinance's `.info`, each left as
    None (never guessed) when the field isn't available for a given ticker -
    coverage is inconsistent outside the US and India."""
    roe = info.get("returnOnEquity")
    margin = info.get("profitMargins")
    d2e = info.get("debtToEquity")
    return {
        "roePct": round(roe * 100, 2) if roe is not None else None,
        "netMarginPct": round(margin * 100, 2) if margin is not None else None,
        # yfinance reports debtToEquity as a percentage of equity (e.g. 145.3
        # means 1.45x) - convert to a plain ratio so the UI can show "1.45x".
        "debtEquity": round(d2e / 100, 2) if d2e is not None else None,
    }


def trimmed_history(hist: pd.DataFrame, divisor: float, days: int = HISTORY_WINDOW_DAYS):
    window = hist.tail(days)["Close"].dropna()
    if window.empty:
        return None
    return {
        "dates": [ts.strftime("%Y-%m-%d") for ts in window.index],
        "close": [round(float(c) / divisor, 2) for c in window],
    }


def fetch_one(company: dict, with_history: bool = False):
    """Returns (row, hist_dataframe_or_None, divisor). The dataframe is
    handed back so main() can build data/history.json from the same fetch
    instead of hitting Yahoo a second time."""
    ticker = company["ticker"]
    row = {**company, "ok": False}
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5y", auto_adjust=False)
        if hist.empty:
            row["error"] = "no price history returned"
            return row, None, 1.0

        divisor = 100.0 if company.get("penceQuoted") else 1.0

        latest_price = float(hist["Close"].iloc[-1]) / divisor
        prev_close = (float(hist["Close"].iloc[-2]) / divisor) if len(hist) > 1 else latest_price
        day_change_pct = round((latest_price - prev_close) / prev_close * 100, 2) if prev_close else None

        last_252 = hist.tail(252)
        week52_high = round(float(last_252["High"].max()) / divisor, 2)
        week52_low = round(float(last_252["Low"].min()) / divisor, 2)

        info = {}
        try:
            info = t.info or {}
        except Exception:
            info = {}

        ma50, ma200 = moving_averages(hist, divisor)

        row.update({
            "ok": True,
            "price": round(latest_price, 2),
            "dayChangePct": day_change_pct,
            "week52High": week52_high,
            "week52Low": week52_low,
            "return1y": pct_return(hist, 365),
            "return3y": pct_return(hist, 365 * 3),
            "return5y": pct_return(hist, 365 * 5),
            "pe": info.get("trailingPE"),
            "divYieldPct": round(info.get("dividendYield"), 2) if info.get("dividendYield") else None,
            "ma50": ma50,
            "ma200": ma200,
            "rsi14": rsi14(hist),
            "asOf": hist.index[-1].strftime("%Y-%m-%d"),
            "scenario": scenario_stats(hist),
        })
        row.update(fundamentals(info))
        return row, (hist if with_history else None), divisor
    except Exception as exc:
        row["error"] = str(exc)
        return row, None, 1.0


def main() -> int:
    with_history = "--with-history" in sys.argv

    results = []
    histories = {}
    for c in COMPANIES:
        row, hist, divisor = fetch_one(c, with_history=with_history)
        results.append(row)
        if with_history and hist is not None:
            h = trimmed_history(hist, divisor)
            if h:
                histories[c["ticker"]] = h
        time.sleep(REQUEST_PAUSE_SECONDS)

    ok_count = sum(1 for r in results if r["ok"])

    snapshot = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Yahoo Finance (yfinance) - unofficial, ~15-20 min delayed; native currency per listing",
        "companies": results,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)

    print(f"Wrote {OUTPUT_PATH}: {ok_count}/{len(COMPANIES)} tickers fetched successfully.")

    if with_history:
        history_snapshot = {
            "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "windowTradingDays": HISTORY_WINDOW_DAYS,
            "companies": histories,
        }
        with open(HISTORY_OUTPUT_PATH, "w") as f:
            json.dump(history_snapshot, f)
        print(f"Wrote {HISTORY_OUTPUT_PATH}: {len(histories)}/{len(COMPANIES)} tickers.")

    return 0 if ok_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
