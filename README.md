# Straddle Scout 🔍

Automated expiry-day straddle entry signal agent for **NIFTY** and **SENSEX**.

Runs every Thursday (NIFTY) and Friday (SENSEX) at 9:16, 9:30, and 9:45 IST.
Sends an email (and optionally Telegram) alert with the ATM straddle analysis
and an entry signal.

---

## Project structure

```
straddle-scout/
├── main.py          # Scheduler + CLI entrypoint
├── agent.py         # Core pipeline orchestrator
├── config.py        # All settings — edit this first
├── expiry.py        # Expiry day detection (handles holidays)
├── spot_client.py   # Live spot price via yfinance
├── nse_client.py    # NSE options chain (unofficial API)
├── signal.py        # ATM strike, premium, IV, PCR, signal logic
├── alert.py         # Email (SMTP) + Telegram delivery
├── logger.py        # File/console logger + SQLite trade log
└── requirements.txt
```

---

## Setup

```bash
# 1. Clone / copy the project
cd straddle-scout

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
#    Edit config.py — set your email credentials and thresholds
```

### Gmail setup

1. Enable 2FA on your Google account.
2. Go to **Google Account → Security → App Passwords**.
3. Create an app password for "Mail".
4. Paste it into `EMAIL_PASSWORD` in `config.py` — **not** your real Gmail password.

### Telegram setup (optional)

1. Message `@BotFather` on Telegram → `/newbot` → copy the token.
2. Add the bot to a group/channel, send a message, then fetch:
   `https://api.telegram.org/bot<TOKEN>/getUpdates` to get the `chat_id`.
3. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `config.py`.

---

## Usage

```bash
# Start the scheduler (runs forever, fires on expiry days)
python main.py

# Test immediately — bypasses expiry check
python main.py --now NIFTY
python main.py --now SENSEX

# View last 20 runs from the database
python main.py --history
```

---

## Signal logic

| Check | Pass condition |
|---|---|
| IV | CE implied volatility ≥ `iv_threshold` (default 12%) |
| Premium width | Total premium ≤ `max_premium_pct`% of spot (default 1.5%) |
| PCR | Put-Call Ratio between `PCR_MIN` (0.7) and `PCR_MAX` (1.5) |

All three must pass → `ENTER_STRADDLE`.
Any failure → `NO_TRADE` with reasons listed.

---

## Tuning thresholds

Edit `config.py`:

```python
INDICES = {
    "NIFTY": {
        "iv_threshold":    12.0,   # increase for stricter IV filter
        "max_premium_pct": 1.5,    # tighten to avoid wide straddles
        ...
    }
}
PCR_MIN = 0.7   # below = skip (extreme fear)
PCR_MAX = 1.5   # above = skip (extreme greed)
```

---

## Database

Runs are logged to `scout_log.db` (SQLite). Query it directly:

```bash
sqlite3 scout_log.db "SELECT * FROM scout_runs ORDER BY id DESC LIMIT 10;"
```

Or use `python main.py --history` for a formatted table.

---

## Phase 2 ideas

- [ ] Intraday exit signal (50% premium decay alert)
- [ ] Greeks tracking (delta, theta) every 15 min
- [ ] Monthly backtest runner on historical chain data
- [ ] Webhook → Zerodha / Upstox order placement
- [ ] Streamlit dashboard for historical P&L

---

## Disclaimer

This tool generates informational signals only. It is not financial advice.
Always apply your own risk management before entering any trade.
