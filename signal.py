"""
signal.py — ATM straddle computation + entry signal evaluation

Steps:
  1. Find the ATM strike (nearest to spot).
  2. Extract CE/PE premiums and IV for that strike on the nearest expiry.
  3. Compute PCR (Put-Call Ratio by OI) to detect extreme sentiment.
  4. Apply entry filters → produce a signal: ENTER / NO_TRADE + reasons.
"""

from config import INDICES, PCR_MIN, PCR_MAX
from logger import get_logger

log = get_logger(__name__)


# ── ATM straddle extraction ───────────────────────────────────────────────────

def get_atm_straddle(chain_data: dict, spot: float, expiry_date: str) -> dict | None:
    """
    Walk the options chain records and return a dict with:
      strike, ce, pe, total_premium, iv, ce_oi, pe_oi, pcr
    Returns None if the strike cannot be found.
    """
    try:
        records = chain_data["records"]["data"]
    except (KeyError, TypeError):
        log.error("Malformed chain data — cannot extract records.")
        return None

    # Collect all strikes for this expiry
    strikes = sorted(set(
        r["strikePrice"]
        for r in records
        if r.get("expiryDate") == expiry_date
    ))

    if not strikes:
        log.error("No strikes found for expiry %s.", expiry_date)
        return None

    atm_strike = min(strikes, key=lambda x: abs(x - spot))
    log.info("Spot: %s → ATM strike: %s", spot, atm_strike)

    ce_data = pe_data = None
    for record in records:
        if record.get("strikePrice") == atm_strike and record.get("expiryDate") == expiry_date:
            ce_data = record.get("CE", {})
            pe_data = record.get("PE", {})
            break

    if ce_data is None or pe_data is None:
        log.error("CE/PE data missing for ATM strike %s.", atm_strike)
        return None

    ce_premium = ce_data.get("lastPrice", 0) or 0
    pe_premium = pe_data.get("lastPrice", 0) or 0
    iv         = ce_data.get("impliedVolatility", 0) or 0
    ce_oi      = ce_data.get("openInterest", 0) or 0
    pe_oi      = pe_data.get("openInterest", 0) or 0
    pcr        = round(pe_oi / ce_oi, 3) if ce_oi > 0 else 0

    result = {
        "strike":        atm_strike,
        "ce":            round(ce_premium, 2),
        "pe":            round(pe_premium, 2),
        "total_premium": round(ce_premium + pe_premium, 2),
        "iv":            round(iv, 2),
        "ce_oi":         ce_oi,
        "pe_oi":         pe_oi,
        "pcr":           pcr,
    }
    log.info("Straddle: %s", result)
    return result


# ── Entry signal evaluation ───────────────────────────────────────────────────

def evaluate_signal(straddle: dict, spot: float, index: str) -> dict:
    """
    Apply entry filters and return:
      { signal: "ENTER_STRADDLE" | "NO_TRADE", reasons: [...], premium_pct: float }
    """
    cfg      = INDICES[index]
    reasons  = []

    # 1. IV check
    if straddle["iv"] < cfg["iv_threshold"]:
        reasons.append(
            f"IV too low: {straddle['iv']}% < threshold {cfg['iv_threshold']}%"
        )

    # 2. Premium width check (as % of spot)
    premium_pct = round((straddle["total_premium"] / spot) * 100, 3) if spot else 0
    if premium_pct > cfg["max_premium_pct"]:
        reasons.append(
            f"Premium too wide: {premium_pct}% > max {cfg['max_premium_pct']}%"
        )

    # 3. PCR extreme sentiment check
    if straddle["pcr"] < PCR_MIN:
        reasons.append(
            f"PCR too low (extreme bearish): {straddle['pcr']} < {PCR_MIN}"
        )
    elif straddle["pcr"] > PCR_MAX:
        reasons.append(
            f"PCR too high (extreme bullish): {straddle['pcr']} > {PCR_MAX}"
        )

    # 4. Sanity: zero premium means bad data
    if straddle["total_premium"] == 0:
        reasons.append("Total premium is 0 — likely stale/no-trade data.")

    signal = "NO_TRADE" if reasons else "ENTER_STRADDLE"

    return {
        "signal":      signal,
        "reasons":     reasons,
        "premium_pct": premium_pct,
    }


# ── Breakeven calculation ─────────────────────────────────────────────────────

def compute_breakeven(straddle: dict) -> dict:
    """Upper and lower breakeven levels for the straddle."""
    strike  = straddle["strike"]
    premium = straddle["total_premium"]
    return {
        "upper_breakeven": round(strike + premium, 2),
        "lower_breakeven": round(strike - premium, 2),
    }
