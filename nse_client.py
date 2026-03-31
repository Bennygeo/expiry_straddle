"""
nse_client.py — NSE options chain fetcher

NSE blocks cold API calls — this module:
  1. Seeds a session by hitting the NSE homepage (gets cookies + headers).
  2. Retries with backoff on failure.
  3. Returns a clean dict with the raw options chain data.
"""

import time

import requests

from config import NSE_REQUEST_TIMEOUT, NSE_RETRY_ATTEMPTS, NSE_RETRY_DELAY
from logger import get_logger

log = get_logger(__name__)

_BASE_URL    = "https://www.nseindia.com"
_CHAIN_URL   = "https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer":         "https://www.nseindia.com/option-chain",
    "Connection":      "keep-alive",
}


def _make_session() -> requests.Session:
    """Create a session seeded with NSE cookies."""
    session = requests.Session()
    session.headers.update(_HEADERS)
    try:
        session.get(_BASE_URL, timeout=NSE_REQUEST_TIMEOUT)
        log.debug("NSE session seeded (cookies obtained).")
    except Exception as exc:
        log.warning("Could not seed NSE session: %s", exc)
    return session


def fetch_options_chain(symbol: str) -> dict | None:
    """
    Fetch full options chain for `symbol` (e.g. 'NIFTY', 'SENSEX').
    Returns the raw JSON dict or None on failure.
    """
    session = _make_session()
    url = _CHAIN_URL.format(symbol=symbol)

    for attempt in range(1, NSE_RETRY_ATTEMPTS + 1):
        try:
            resp = session.get(url, timeout=NSE_REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            log.info("Options chain fetched for %s (attempt %d).", symbol, attempt)
            return data
        except requests.HTTPError as exc:
            log.warning("HTTP error on attempt %d for %s: %s", attempt, symbol, exc)
        except Exception as exc:
            log.warning("Error on attempt %d for %s: %s", attempt, symbol, exc)

        if attempt < NSE_RETRY_ATTEMPTS:
            log.info("Retrying in %ds…", NSE_RETRY_DELAY)
            time.sleep(NSE_RETRY_DELAY)

    log.error("All %d attempts failed for %s.", NSE_RETRY_ATTEMPTS, symbol)
    return None


def get_available_expiries(chain_data: dict) -> list[str]:
    """Return sorted list of available expiry date strings from chain data."""
    try:
        return chain_data["records"]["expiryDates"]
    except (KeyError, TypeError):
        return []


def get_nearest_expiry(chain_data: dict) -> str | None:
    """Return the nearest expiry date string (first in the list)."""
    expiries = get_available_expiries(chain_data)
    return expiries[0] if expiries else None
