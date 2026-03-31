"""
Email service — ENTERPRISE READY VERSION (Clean UI + Gmail Safe)
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


# =========================
# HTML TEMPLATE (PROFESSIONAL)
# =========================
def _build_html(subject: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background:#f5f7fb;
    margin:0;
    padding:0;
    color:#111827;
  }}

  .wrapper {{
    max-width:600px;
    margin:40px auto;
    background:#ffffff;
    border-radius:12px;
    overflow:hidden;
    border:1px solid #e5e7eb;
  }}

  .header {{
    background:linear-gradient(135deg,#6366f1,#8b5cf6);
    padding:28px;
    text-align:center;
    color:#ffffff;
  }}

  .header h1 {{
    margin:0;
    font-size:22px;
    font-weight:600;
  }}

  .header p {{
    margin-top:6px;
    font-size:13px;
    opacity:0.9;
  }}

  .body {{
    padding:28px;
  }}

  .body p {{
    font-size:14px;
    line-height:1.6;
    color:#374151;
  }}

  .card {{
    background:#f9fafb;
    border:1px solid #e5e7eb;
    border-radius:8px;
    padding:14px;
    margin:14px 0;
    color:#111827;
    font-weight:500;
  }}

  .btn {{
    display:inline-block;
    background:#6366f1;
    color:#ffffff !important;
    padding:12px 20px;
    border-radius:8px;
    text-decoration:none;
    font-size:14px;
    margin-top:16px;
  }}

  .footer {{
    text-align:center;
    font-size:12px;
    color:#9ca3af;
    padding:16px;
    border-top:1px solid #e5e7eb;
  }}
</style>
</head>

<body>
<div class="wrapper">

  <div class="header">
    <h1>📊 MarketIQ</h1>
    <p>{subject}</p>
  </div>

  <div class="body">
    {body_html}

    <a href="http://localhost:3000/dashboard" class="btn">
      Open Dashboard →
    </a>
  </div>

  <div class="footer">
    © MarketIQ • AI Market Intelligence Platform
  </div>

</div>
</body>
</html>
"""


# =========================
# CORE EMAIL FUNCTION
# =========================
async def send_email(to: str, subject: str, body_html: str) -> bool:
    """Send email safely"""

    if not settings.has_email:
        logger.warning(f"[Email] SMTP not configured → {to}")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to
    msg.attach(MIMEText(body_html, "html"))

    def _send():
        try:
            ctx = ssl.create_default_context()

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as srv:
                srv.ehlo()
                srv.starttls(context=ctx)
                srv.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                srv.sendmail(settings.SMTP_USER, [to], msg.as_string())

        except Exception as e:
            print("❌ SMTP ERROR:", e)
            raise e

    try:
        await asyncio.to_thread(_send)
        logger.info(f"[Email] Sent → {to}")
        return True

    except Exception as e:
        logger.error(f"[Email] Failed to send to {to}: {e}")
        return False


# =========================
# REMINDER EMAIL
# =========================
async def send_reminder_notification(
    to: str,
    user_name: str,
    company: str,
    message: str,
    notification_title: str,
) -> bool:

    subject = f"⏰ Reminder: {notification_title}"

    body = f"""
<p>Hi <strong>{user_name}</strong>,</p>

<p>This is your reminder:</p>

<div class="card">
  <strong>{notification_title}</strong>
</div>

{'<div class="card"><strong>Company:</strong> ' + company + '</div>' if company else ''}

<p>{message}</p>
"""

    return await send_email(to, subject, _build_html(subject, body))


# =========================
# ANALYSIS EMAIL
# =========================
async def send_analysis_complete_notification(
    to: str,
    user_name: str,
    company: str,
    total_articles: int,
    sentiment: str,
    days: int,
) -> bool:

    subject = f"✅ Analysis Complete: {company}"

    body = f"""
<p>Hi <strong>{user_name}</strong>,</p>

<p>Your analysis is ready.</p>

<div class="card">
  <strong>{company}</strong><br/>
  {total_articles} articles • {days} days<br/>
  Sentiment: <strong>{sentiment}</strong>
</div>
"""

    return await send_email(to, subject, _build_html(subject, body))


# =========================
# RISK ALERT EMAIL
# =========================
async def send_risk_alert_notification(
    to: str,
    user_name: str,
    company: str,
    risk_count: int,
    top_risk: str,
) -> bool:

    subject = f"🚨 Risk Alert: {company}"

    body = f"""
<p>Hi <strong>{user_name}</strong>,</p>

<p>{risk_count} risk(s) detected.</p>

<div class="card">
  ⚠️ {top_risk}
</div>
"""

    return await send_email(to, subject, _build_html(subject, body))