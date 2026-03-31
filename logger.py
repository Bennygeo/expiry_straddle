"""
logger.py — Logging setup + SQLite trade log
"""

import logging
import sqlite3
from datetime import datetime

from config import LOG_FILE, DB_PATH


# ── Console + file logger ─────────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


# ── SQLite trade log ──────────────────────────────────────────────────────────

def init_db():
    """Create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scout_runs (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at         TEXT NOT NULL,
            index_name     TEXT NOT NULL,
            spot           REAL,
            atm_strike     REAL,
            ce_premium     REAL,
            pe_premium     REAL,
            total_premium  REAL,
            premium_pct    REAL,
            iv             REAL,
            pcr            REAL,
            signal         TEXT,
            reasons        TEXT,
            alert_sent     INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def log_run(
    index_name: str,
    spot: float,
    straddle: dict,
    signal_result: dict,
    alert_sent: bool,
):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO scout_runs
            (run_at, index_name, spot, atm_strike, ce_premium, pe_premium,
             total_premium, premium_pct, iv, pcr, signal, reasons, alert_sent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        index_name,
        spot,
        straddle.get("strike"),
        straddle.get("ce"),
        straddle.get("pe"),
        straddle.get("total_premium"),
        signal_result.get("premium_pct"),
        straddle.get("iv"),
        straddle.get("pcr"),
        signal_result.get("signal"),
        "; ".join(signal_result.get("reasons", [])),
        int(alert_sent),
    ))
    conn.commit()
    conn.close()


def get_recent_runs(limit: int = 20) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM scout_runs ORDER BY id DESC LIMIT ?", (limit,)
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
