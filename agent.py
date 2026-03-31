"""
agent.py — Core agent orchestrator

Wires together:
  expiry check → spot fetch → options chain fetch →
  ATM extraction → signal evaluation → alert → DB log
"""

from logger import get_logger, log_run
from expiry import is_expiry_today
from spot_client import get_spot_price
from nse_client import fetch_options_chain, get_nearest_expiry as chain_nearest_expiry
from straddle_signal import get_atm_straddle, evaluate_signal, compute_breakeven
from alert import send_alerts

log = get_logger(__name__)


def run_scout(index: str) -> dict | None:
    """
    Full pipeline for one index on one run.
    Returns the result dict or None if skipped/failed.
    """
    log.info("═" * 55)
    log.info("Starting scout run for %s", index)
    log.info("═" * 55)

    # ── 1. Expiry check ───────────────────────────────────────────────────────
    is_expiry, expiry_date_obj = is_expiry_today(index)
    if not is_expiry:
        log.info("%s: not expiry day. Skipping.", index)
        return None

    expiry_str = expiry_date_obj.strftime("%-d-%b-%Y")
    log.info("%s expiry: %s", index, expiry_str)

    # ── 2. Spot price ─────────────────────────────────────────────────────────
    spot = get_spot_price(index)
    if spot is None:
        log.error("Could not fetch spot price for %s. Aborting run.", index)
        return None

    # ── 3. Options chain ──────────────────────────────────────────────────────
    chain_data = fetch_options_chain(index)
    if chain_data is None:
        log.error("Could not fetch options chain for %s. Aborting run.", index)
        return None

    # Use the nearest expiry from the chain (may differ slightly from calendar)
    expiry_in_chain = chain_nearest_expiry(chain_data)
    if expiry_in_chain is None:
        log.error("No expiry dates in options chain for %s.", index)
        return None

    log.info("Using chain expiry: %s", expiry_in_chain)

    # ── 4. ATM straddle ───────────────────────────────────────────────────────
    straddle = get_atm_straddle(chain_data, spot, expiry_in_chain)
    if straddle is None:
        log.error("Could not extract ATM straddle for %s.", index)
        return None

    # ── 5. Signal evaluation ──────────────────────────────────────────────────
    signal_result = evaluate_signal(straddle, spot, index)
    breakeven     = compute_breakeven(straddle)

    log.info(
        "Signal: %s | Premium: %s (%s%%) | IV: %s%% | PCR: %s",
        signal_result["signal"],
        straddle["total_premium"],
        signal_result["premium_pct"],
        straddle["iv"],
        straddle["pcr"],
    )

    if signal_result["reasons"]:
        for r in signal_result["reasons"]:
            log.info("  ↳ %s", r)

    # ── 6. Alert ──────────────────────────────────────────────────────────────
    alert_sent = send_alerts(
        index, spot, straddle, signal_result, breakeven, expiry_in_chain
    )

    # ── 7. Log to DB ──────────────────────────────────────────────────────────
    log_run(index, spot, straddle, signal_result, alert_sent)

    result = {
        "index":         index,
        "expiry":        expiry_in_chain,
        "spot":          spot,
        "straddle":      straddle,
        "signal_result": signal_result,
        "breakeven":     breakeven,
        "alert_sent":    alert_sent,
    }

    log.info("Scout run complete for %s. Alert sent: %s", index, alert_sent)
    return result
