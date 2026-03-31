import os

# ── Email settings ────────────────────────────────────────────────────────────
EMAIL_SENDER     = os.environ["GMAIL_USER"]
EMAIL_PASSWORD   = os.environ["STRADDLE"]         # Gmail App Password
EMAIL_RECIPIENTS = ["benny_gj@yahoo.co.in", "bennnygeo@gmail.com"]
SMTP_HOST        = "smtp.gmail.com"
SMTP_PORT        = 587

# ── Telegram (optional — set to None to disable) ─────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")   # None if not set
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")     # None if not set

# ── Index settings ────────────────────────────────────────────────────────────
INDICES = {
    "NIFTY": {
        "symbol":          "NIFTY",
        "yf_ticker":       "^NSEI",
        "lot_size":        50,
        "expiry_day":      3,           # Thursday (0=Mon ... 6=Sun)
        "iv_threshold":    12.0,        # Min IV% for entry
        "max_premium_pct": 1.5,         # Max straddle premium as % of spot
        "run_times":       ["09:16", "09:30", "09:45"],
    },
    "SENSEX": {
        "symbol":          "SENSEX",
        "yf_ticker":       "^BSESN",
        "lot_size":        10,
        "expiry_day":      4,           # Friday
        "iv_threshold":    12.0,
        "max_premium_pct": 1.5,
        "run_times":       ["09:16", "09:30", "09:45"],
    },
}

# ── Signal thresholds ─────────────────────────────────────────────────────────
PCR_MIN = 0.7
PCR_MAX = 1.5

# ── Logging / Storage ─────────────────────────────────────────────────────────
DB_PATH  = "scout_log.db"
LOG_FILE = "scout.log"

# ── NSE session ───────────────────────────────────────────────────────────────
NSE_REQUEST_TIMEOUT = 15
NSE_RETRY_ATTEMPTS  = 3
NSE_RETRY_DELAY     = 5
