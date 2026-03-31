"""
spot_client.py — Live spot price via yfinance
"""

import yfinance as yf

from config import INDICES
from logger import get_logger

log = get_logger(__name__)


def get_spot_price(index: str) -> float | None:
    """
    Fetch the latest 1-minute candle close for the index.
    Returns None on failure.
    """
    ticker_sym = INDICES[index]["yf_ticker"]
    try:
        ticker = yf.Ticker(ticker_sym)
        hist = ticker.history(period="1d", interval="1m")
        if hist.empty:
            log.warning("yfinance returned empty data for %s", ticker_sym)
            return None
        spot = round(float(hist["Close"].iloc[-1]), 2)
        log.info("%s spot price: %s", index, spot)
        return spot
    except Exception as exc:
        log.error("Failed to fetch spot for %s: %s", index, exc)
        return None
