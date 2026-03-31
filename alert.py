"""
alert.py — Email and Telegram alert delivery

Supports:
  - Gmail SMTP (TLS)
  - Telegram Bot API (optional)
"""

import smtplib
import textwrap
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from config import (
    EMAIL_SENDER,
    EMAIL_PASSWORD,
    EMAIL_RECIPIENTS,
    SMTP_HOST,
    SMTP_PORT,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from logger import get_logger

log = get_logger(__name__)


# ── Message builders ──────────────────────────────────────────────────────────

def _build_subject(index: str, signal: str) -> str:
    icon = "✅" if signal == "ENTER_STRADDLE" else "🚫"
    return f"{icon} Straddle Scout | {index} | {signal} | {datetime.now().strftime('%d %b %Y %H:%M')}"


def _build_plain_body(
    index: str,
    spot: float,
    straddle: dict,
    signal_result: dict,
    breakeven: dict,
    expiry_date: str,
) -> str:
    reasons_str = (
        "\n    • " + "\n    • ".join(signal_result["reasons"])
        if signal_result["reasons"]
        else "    All checks passed ✓"
    )

    return textwrap.dedent(f"""
    ╔══════════════════════════════════════════════╗
         Expiry Day Straddle Scout — {index}
    ╚══════════════════════════════════════════════╝

    Run at      : {datetime.now().strftime('%d %b %Y  %H:%M:%S IST')}
    Expiry      : {expiry_date}

    ── Market Snapshot ───────────────────────────
    Spot Price  : {spot:,.2f}
    ATM Strike  : {straddle['strike']:,.2f}

    ── Straddle Premium ──────────────────────────
    CE Premium  : {straddle['ce']:,.2f}
    PE Premium  : {straddle['pe']:,.2f}
    Total       : {straddle['total_premium']:,.2f}  ({signal_result['premium_pct']}% of spot)

    ── Greeks / Sentiment ────────────────────────
    IV (CE)     : {straddle['iv']}%
    PCR (OI)    : {straddle['pcr']}
    CE OI       : {straddle['ce_oi']:,}
    PE OI       : {straddle['pe_oi']:,}

    ── Breakeven ─────────────────────────────────
    Upper BE    : {breakeven['upper_breakeven']:,.2f}
    Lower BE    : {breakeven['lower_breakeven']:,.2f}
    BE Range    : ±{straddle['total_premium']:,.2f} pts

    ── Signal ────────────────────────────────────
    {signal_result['signal']}
    {reasons_str}

    ─────────────────────────────────────────────
    This is an automated signal. Always apply your
    own risk management before entering a trade.
    ─────────────────────────────────────────────
    """).strip()


def _build_html_body(
    index: str,
    spot: float,
    straddle: dict,
    signal_result: dict,
    breakeven: dict,
    expiry_date: str,
) -> str:
    signal      = signal_result["signal"]
    signal_color = "#16a34a" if signal == "ENTER_STRADDLE" else "#dc2626"
    signal_bg    = "#dcfce7" if signal == "ENTER_STRADDLE" else "#fee2e2"
    reasons_html = (
        "<ul>" +
        "".join(f"<li>{r}</li>" for r in signal_result["reasons"]) +
        "</ul>"
    ) if signal_result["reasons"] else "<p style='color:#16a34a'>All checks passed ✓</p>"

    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#1e293b">
    <div style="background:#1e40af;color:#fff;padding:16px 24px;border-radius:8px 8px 0 0">
      <h2 style="margin:0">🔍 Straddle Scout — {index}</h2>
      <p style="margin:4px 0 0;font-size:13px">{datetime.now().strftime('%d %b %Y  %H:%M:%S IST')} &nbsp;|&nbsp; Expiry: {expiry_date}</p>
    </div>
    <div style="border:1px solid #e2e8f0;border-top:none;padding:20px 24px;border-radius:0 0 8px 8px">

      <table width="100%" cellpadding="6" style="border-collapse:collapse;font-size:14px">
        <tr style="background:#f1f5f9"><th colspan="2" style="text-align:left;padding:8px">Market Snapshot</th></tr>
        <tr><td>Spot Price</td><td><b>{spot:,.2f}</b></td></tr>
        <tr style="background:#f8fafc"><td>ATM Strike</td><td><b>{straddle['strike']:,.2f}</b></td></tr>

        <tr style="background:#f1f5f9"><th colspan="2" style="text-align:left;padding:8px">Straddle Premium</th></tr>
        <tr><td>CE Premium</td><td>{straddle['ce']:,.2f}</td></tr>
        <tr style="background:#f8fafc"><td>PE Premium</td><td>{straddle['pe']:,.2f}</td></tr>
        <tr><td><b>Total Premium</b></td><td><b>{straddle['total_premium']:,.2f}</b> ({signal_result['premium_pct']}% of spot)</td></tr>

        <tr style="background:#f1f5f9"><th colspan="2" style="text-align:left;padding:8px">Greeks / Sentiment</th></tr>
        <tr><td>IV (CE)</td><td>{straddle['iv']}%</td></tr>
        <tr style="background:#f8fafc"><td>PCR (OI)</td><td>{straddle['pcr']}</td></tr>
        <tr><td>CE OI</td><td>{straddle['ce_oi']:,}</td></tr>
        <tr style="background:#f8fafc"><td>PE OI</td><td>{straddle['pe_oi']:,}</td></tr>

        <tr style="background:#f1f5f9"><th colspan="2" style="text-align:left;padding:8px">Breakeven</th></tr>
        <tr><td>Upper BE</td><td>{breakeven['upper_breakeven']:,.2f}</td></tr>
        <tr style="background:#f8fafc"><td>Lower BE</td><td>{breakeven['lower_breakeven']:,.2f}</td></tr>
        <tr><td>BE Range</td><td>±{straddle['total_premium']:,.2f} pts</td></tr>
      </table>

      <div style="margin-top:20px;padding:14px 18px;background:{signal_bg};border-radius:6px;border-left:4px solid {signal_color}">
        <h3 style="margin:0;color:{signal_color};font-size:16px">{signal}</h3>
        {reasons_html}
      </div>

      <p style="margin-top:20px;font-size:11px;color:#94a3b8">
        This is an automated signal. Always apply your own risk management before entering a trade.
      </p>
    </div>
    </body></html>
    """


# ── Delivery ──────────────────────────────────────────────────────────────────

def send_email(
    index: str,
    spot: float,
    straddle: dict,
    signal_result: dict,
    breakeven: dict,
    expiry_date: str,
) -> bool:
    subject   = _build_subject(index, signal_result["signal"])
    plain     = _build_plain_body(index, spot, straddle, signal_result, breakeven, expiry_date)
    html_body = _build_html_body(index, spot, straddle, signal_result, breakeven, expiry_date)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = ", ".join(EMAIL_RECIPIENTS)
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENTS, msg.as_string())
        log.info("Email sent to %s", EMAIL_RECIPIENTS)
        return True
    except Exception as exc:
        log.error("Email send failed: %s", exc)
        return False


def send_telegram(
    index: str,
    spot: float,
    straddle: dict,
    signal_result: dict,
    breakeven: dict,
    expiry_date: str,
) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    signal = signal_result["signal"]
    icon   = "✅" if signal == "ENTER_STRADDLE" else "🚫"
    reasons = "\n• ".join(signal_result["reasons"]) if signal_result["reasons"] else "All checks passed ✓"

    text = (
        f"{icon} *Straddle Scout — {index}*\n"
        f"Expiry: `{expiry_date}`\n\n"
        f"*Spot*: `{spot:,.2f}`  |  *Strike*: `{straddle['strike']:,.2f}`\n"
        f"*CE*: `{straddle['ce']}`  |  *PE*: `{straddle['pe']}`  |  *Total*: `{straddle['total_premium']}`\n"
        f"*IV*: `{straddle['iv']}%`  |  *PCR*: `{straddle['pcr']}`\n"
        f"*BE*: `{breakeven['lower_breakeven']}` → `{breakeven['upper_breakeven']}`\n\n"
        f"*Signal*: `{signal}`\n{reasons}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       text,
            "parse_mode": "Markdown",
        }, timeout=10)
        resp.raise_for_status()
        log.info("Telegram alert sent.")
        return True
    except Exception as exc:
        log.error("Telegram send failed: %s", exc)
        return False


def send_alerts(
    index: str,
    spot: float,
    straddle: dict,
    signal_result: dict,
    breakeven: dict,
    expiry_date: str,
) -> bool:
    """Send via all configured channels."""
    email_ok    = send_email(index, spot, straddle, signal_result, breakeven, expiry_date)
    telegram_ok = send_telegram(index, spot, straddle, signal_result, breakeven, expiry_date)
    return email_ok or telegram_ok
