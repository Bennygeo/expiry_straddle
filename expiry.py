"""
expiry.py — Expiry day detection for NIFTY (Thu) and SENSEX (Fri)

NSE sometimes shifts expiry to Wednesday when Thursday is a holiday,
and BSE shifts to Thursday when Friday is a holiday.
This module handles that correctly.
"""

from datetime import date, timedelta

import holidays

from logger import get_logger

log = get_logger(__name__)

_india_holidays = holidays.India()


def _is_market_holiday(d: date) -> bool:
    """True if `d` is a weekend or an Indian public holiday."""
    return d.weekday() >= 5 or d in _india_holidays


def _previous_trading_day(d: date) -> date:
    """Walk backwards until we find a trading day."""
    prev = d - timedelta(days=1)
    while _is_market_holiday(prev):
        prev -= timedelta(days=1)
    return prev


def get_current_expiry(index: str) -> date | None:
    """
    Return this week's expiry date for the given index.
    Returns None if today is not expiry week's expiry day
    (i.e. the agent shouldn't run today).

    Logic:
      - NIFTY: normally Thursday. If Thursday is holiday → Wednesday.
      - SENSEX: normally Friday. If Friday is holiday → Thursday.
    """
    today = date.today()
    target_weekday = 3 if index == "NIFTY" else 4   # Thu=3, Fri=4

    # Find the nominal expiry date for the current week
    # (Monday = 0, so Thursday = 3, Friday = 4)
    days_ahead = (target_weekday - today.weekday()) % 7
    nominal_expiry = today + timedelta(days=days_ahead)

    if _is_market_holiday(nominal_expiry):
        actual_expiry = _previous_trading_day(nominal_expiry)
        log.info(
            "%s nominal expiry %s is holiday → shifted to %s",
            index, nominal_expiry, actual_expiry,
        )
    else:
        actual_expiry = nominal_expiry

    return actual_expiry


def is_expiry_today(index: str) -> tuple[bool, date | None]:
    """
    Returns (True, expiry_date) if today is expiry day for the index.
    Returns (False, None) otherwise.
    """
    today = date.today()

    if _is_market_holiday(today):
        log.info("Today (%s) is a market holiday. Skipping.", today)
        return False, None

    expiry = get_current_expiry(index)

    if expiry == today:
        log.info("%s expiry is TODAY (%s). Scout will run.", index, today)
        return True, expiry

    log.info(
        "%s expiry this week is %s, not today (%s). Skipping.",
        index, expiry, today,
    )
    return False, None


def expiry_date_str(index: str) -> str | None:
    """
    Return expiry date formatted as NSE expects: '27-Jun-2024'
    """
    today = date.today()
    is_expiry, expiry = is_expiry_today(index)
    if not is_expiry:
        return None
    return expiry.strftime("%-d-%b-%Y")   # e.g. "27-Jun-2024"
