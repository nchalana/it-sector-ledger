#!/usr/bin/env python3
"""
Pulls quotes for the nine NSE-listed IT majors tracked in the IT Sector
Ledger and writes a single JSON snapshot to data/latest.json.

Data source: Yahoo Finance (via the yfinance library) - free, no API key,
typically ~15-20 minutes delayed for NSE tickers. This is a personal
research tool; Yahoo Finance's Indian-market coverage is unofficial and can
occasionally be missing or stale for a given run - the workflow just tries
again on its next scheduled tick.
"""

import json
import sys
from datetime import datetime, timezone, timedelta

import pandas as pd
import yfinance as yf

COMPANIES = [
    {"ticker": "TCS.NS", "name": "TCS", "full": "Tata Consultancy Services"},
    {"ticker": "INFY.NS", "name": "Infosys", "full": "Infosys Ltd"},
    {"ticker": "WIPRO.NS", "name": "Wipro", "full": "Wipro Ltd"},
    {"ticker": "HCLTECH.NS", "name": "HCL Technologies", "full": "HCL Technologies Ltd"},
    {"ticker": "TECHM.NS", "name": "Tech Mahindra", "full": "Tech Mahindra Ltd"},
    {"ticker": "LTIM.NS", "name": "LTIMindtree", "full": "LTIMindtree Ltd"},
    {"ticker": "PERSISTENT.NS", "name": "Persistent Systems", "full": "Persistent Systems Ltd"},
    {"ticker": "COFORGE.NS", "name": "Coforge", "full": "Coforge Ltd"},
    {"ticker": "MPHASIS.NS", "name": "Mphasis", "full": "Mphasis Ltd"},
]

OUTPUT_PATH = "data/latest.json"


def pct_return(hist: pd.DataFrame, days: int):
    """% change from the close ~`days` ago to the latest close."""
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


def fetch_one(company: dict) -> dict:
    ticker = company["ticker"]
    row = {**company, "ok": False}
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5y", auto_adjust=False)
        if hist.empty:
            row["error"] = "no price history returned"
            return row

        latest_price = float(hist["Close"].iloc[-1])
        prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else latest_price
        day_change_pct = round((latest_price - prev_close) / prev_close * 100, 2) if prev_close else None

        last_252 = hist.tail(252)  # ~1 trading year, for the 52-week band
        week52_high = round(float(last_252["High"].max()), 2)
        week52_low = round(float(last_252["Low"].min()), 2)

        info = {}
        try:
            info = t.info or {}
        except Exception:
            info = {}

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
            "divYieldPct": round(info.get("dividendYield") * 100, 2) if info.get("dividendYield") else None,
            "asOf": hist.index[-1].strftime("%Y-%m-%d"),
        })
    except Exception as exc:  # keep going even if one ticker fails
        row["error"] = str(exc)
    return row


def main() -> int:
    results = [fetch_one(c) for c in COMPANIES]
    ok_count = sum(1 for r in results if r["ok"])

    snapshot = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Yahoo Finance (yfinance) - unofficial, ~15-20 min delayed for NSE",
        "companies": results,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)

    print(f"Wrote {OUTPUT_PATH}: {ok_count}/{len(COMPANIES)} tickers fetched successfully.")
    return 0 if ok_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
