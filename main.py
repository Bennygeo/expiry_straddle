"""
main.py — Scheduler entrypoint

Runs the Straddle Scout on expiry days at multiple times (9:16, 9:30, 9:45 IST)
so you get a fresh read at different points after market open.

Usage:
    python main.py              # Start the scheduler (runs forever)
    python main.py --now NIFTY  # Manual one-shot run for NIFTY (ignores expiry check)
    python main.py --now SENSEX # Manual one-shot run for SENSEX
    python main.py --history    # Print last 20 runs from the DB
"""

import argparse
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config import INDICES
from logger import get_logger, init_db, get_recent_runs
from agent import run_scout

log = get_logger("main")


def _schedule_index(scheduler: BlockingScheduler, index: str):
    cfg        = INDICES[index]
    expiry_day = cfg["expiry_day"]   # 0=Mon … 6=Sun
    day_names  = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    day_name   = day_names[expiry_day]

    for run_time in cfg["run_times"]:
        hour, minute = map(int, run_time.split(":"))
        scheduler.add_job(
            func     = run_scout,
            trigger  = CronTrigger(
                day_of_week = day_name,
                hour        = hour,
                minute      = minute,
                timezone    = "Asia/Kolkata",
            ),
            args     = [index],
            id       = f"{index}_{run_time.replace(':', '')}",
            name     = f"{index} scout @ {run_time} IST",
            replace_existing = True,
        )
        log.info("Scheduled %s scout at %s IST every %s", index, run_time, day_name.upper())


def start_scheduler():
    scheduler = BlockingScheduler(timezone="Asia/Kolkata")

    for index in INDICES:
        _schedule_index(scheduler, index)

    log.info("Scheduler started. Waiting for expiry days…")
    log.info("Press Ctrl+C to stop.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped.")


def print_history():
    rows = get_recent_runs(20)
    if not rows:
        print("No runs logged yet.")
        return

    print(f"\n{'#':<4} {'Time':<20} {'Index':<8} {'Spot':<10} {'Strike':<10} "
          f"{'Premium':<10} {'IV%':<7} {'PCR':<6} {'Signal':<18} {'Alert':<6}")
    print("─" * 105)
    for r in rows:
        print(
            f"{r['id']:<4} {r['run_at']:<20} {r['index_name']:<8} "
            f"{r['spot'] or '—':<10} {r['atm_strike'] or '—':<10} "
            f"{r['total_premium'] or '—':<10} {r['iv'] or '—':<7} "
            f"{r['pcr'] or '—':<6} {r['signal'] or '—':<18} "
            f"{'yes' if r['alert_sent'] else 'no':<6}"
        )
    print()


def manual_run(index: str):
    """Force a run regardless of expiry day (useful for testing)."""
    from unittest.mock import patch
    from expiry import is_expiry_today
    from datetime import date

    log.info("Manual run triggered for %s (bypassing expiry check).", index)

    # Temporarily patch is_expiry_today to always return True
    with patch("agent.is_expiry_today", return_value=(True, date.today())):
        result = run_scout(index)

    if result:
        print("\n── Result ──")
        print(f"  Signal  : {result['signal_result']['signal']}")
        print(f"  Spot    : {result['spot']}")
        print(f"  Strike  : {result['straddle']['strike']}")
        print(f"  Premium : {result['straddle']['total_premium']}")
        print(f"  IV      : {result['straddle']['iv']}%")
        print(f"  PCR     : {result['straddle']['pcr']}")
        be = result["breakeven"]
        print(f"  BE      : {be['lower_breakeven']} ↔ {be['upper_breakeven']}")
    else:
        print("Run returned no result (check logs).")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()

    parser = argparse.ArgumentParser(description="Straddle Scout")
    parser.add_argument(
        "--now",
        metavar="INDEX",
        help="Run immediately for INDEX (NIFTY or SENSEX), ignoring expiry check.",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Print last 20 scout runs from the database.",
    )
    args = parser.parse_args()

    if args.history:
        print_history()
        sys.exit(0)

    if args.now:
        index = args.now.upper()
        if index not in INDICES:
            print(f"Unknown index '{index}'. Choose from: {', '.join(INDICES.keys())}")
            sys.exit(1)
        manual_run(index)
        sys.exit(0)

    # Default: start the scheduler
    start_scheduler()
