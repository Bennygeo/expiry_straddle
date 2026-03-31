import os

EMAIL_SENDER     = os.environ["GMAIL_USER"]
EMAIL_PASSWORD   = os.environ["STRADDLE"]
EMAIL_RECIPIENTS = ["benny_gj@yahoo.co.in", "bennnygeo@gmail.com"]
SMTP_HOST        = "smtp.gmail.com"
SMTP_PORT        = 587

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")

INDICES = {
    "NIFTY": {
        "symbol":          "NIFTY",
        "yf_ticker":       "^NSEI",
        "lot_size":        50,
        "expiry_day":      3,
        "iv_threshold":    12.0,
        "max_premium_pct": 1.5,
        "run_times":       ["09:16", "09:30", "09:45"],
    },
    "SENSEX": {
        "symbol":          "SENSEX",
        "yf_ticker":       "^BSESN",
        "lot_size":        10,
        "expiry_day":      4,
        "iv_threshold":    12.0,
        "max_premium_pct": 1.5,
        "run_times":       ["09:16", "09:30", "09:45"],
    },
}

PCR_MIN = 0.7
PCR_MAX = 1.5

DB_PATH  = "scout_log.db"
LOG_FILE = "scout.log"

NSE_REQUEST_TIMEOUT = 15
NSE_RETRY_ATTEMPTS  = 3
NSE_RETRY_DELAY     = 5
