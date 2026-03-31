"""
config.py — Central configuration for Straddle Scout
Edit these values before running the agent.
"""

# ── Email settings ────────────────────────────────────────────────────────────
import os


EMAIL_SENDER     = os.environ["GMAIL_USER"]
EMAIL_PASSWORD   = os.environ["STRADDLE"]        # Use Gmail App Password, not your real password
EMAIL_RECIPIENTS = ["benny_gj@yahoo.co.in"]   # Can be a list for multiple recipients
SMTP_HOST        = "smtp.gmail.com"
SMTP_PORT        = 587

# ── Telegram (optional — set to None to disable) ─────────────────────────────
TELEGRAM_BOT_TOKEN = None   # e.g. "123456:ABCdef..."
TELEGRAM_CHAT_ID   = None   # e.g. "-100123456789"

# ── Index settings ────────────────────────────────────────────────────────────
INDICES = {
    "NIFTY": {
        "symbol":       "NIFTY",
        "yf_ticker":    "^NSEI",
        "lot_size":     50,
        "expiry_day":   3,          # Thursday (0=Mon … 6=Sun)
        "iv_threshold": 12.0,       # Min IV% for entry
        "max_premium_pct": 1.5,     # Max straddle premium as % of spot
        "run_times":    ["09:16", "09:30", "09:45"],  # IST — multiple checks
    },
    "SENSEX": {
        "symbol":       "SENSEX",
        "yf_ticker":    "^BSESN",
        "lot_size":     10,
        "expiry_day":   4,          # Friday
        "iv_threshold": 12.0,
        "max_premium_pct": 1.5,
        "run_times":    ["09:16", "09:30", "09:45"],
    },
}

# ── Signal thresholds ─────────────────────────────────────────────────────────
PCR_MIN = 0.7    # Put-Call Ratio lower bound (below = extreme bearish, skip)
PCR_MAX = 1.5    # Put-Call Ratio upper bound (above = extreme bullish, skip)

# ── Logging / Storage ─────────────────────────────────────────────────────────
DB_PATH  = "scout_log.db"   # SQLite database file
LOG_FILE = "scout.log"

# ── NSE session ───────────────────────────────────────────────────────────────
NSE_REQUEST_TIMEOUT = 15   # seconds
NSE_RETRY_ATTEMPTS  = 3
NSE_RETRY_DELAY     = 5    # seconds between retries
