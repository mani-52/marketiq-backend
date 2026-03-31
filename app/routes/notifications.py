# app/routes/notifications.py

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from zoneinfo import ZoneInfo  # ✅ IST support

from app.services.email_service import send_reminder_notification

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])

# 🇮🇳 IST TIMEZONE
IST = ZoneInfo("Asia/Kolkata")

DEFAULT_EMAIL = "pavankumarsharavath148@gmail.com"

_NOTIFICATIONS: list[dict] = []
_SENT_LOG: list[dict] = []
_SCHEDULER_RUNNING = False


# =========================
# USER ID
# =========================
def _get_user_id(_: Request) -> str:
    return "local_user"


# =========================
# MODEL
# =========================
class CreateNotificationRequest(BaseModel):
    title: str
    message: str
    company: Optional[str] = ""
    fire_at: Optional[str] = None  # ISO string
    fire_in_seconds: Optional[int] = None
    repeat: Optional[str] = None
    notify_type: str = "reminder"
    user_name: Optional[str] = "User"


# =========================
# ROUTES
# =========================
@router.get("")
async def list_notifications(request: Request):
    uid = _get_user_id(request)
    return {
        "notifications": [n for n in _NOTIFICATIONS if n["user_id"] == uid],
        "sent_count": sum(1 for s in _SENT_LOG if s["user_id"] == uid),
    }


@router.post("")
async def create_notification(body: CreateNotificationRequest, request: Request):
    uid = _get_user_id(request)

    print("🔥 CREATE NOTIFICATION CALLED")

    # =========================
    # 🔥 TIME HANDLING (IST SAFE)
    # =========================
    if body.fire_at:
        try:
            # Parse and convert to IST
            dt = datetime.fromisoformat(body.fire_at)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=IST)
            dt_ist = dt.astimezone(IST)

            fire_ts = dt_ist.timestamp()

        except Exception:
            raise HTTPException(status_code=400, detail="Invalid datetime format")

    else:
        seconds = body.fire_in_seconds or 20
        seconds = max(5, min(seconds, 300))  # 5 sec to 5 min safe
        fire_ts = time.time() + seconds

    notif = {
        "id": str(uuid.uuid4()),
        "user_id": uid,
        "user_email": DEFAULT_EMAIL,
        "user_name": body.user_name or "User",
        "title": body.title,
        "message": body.message,
        "company": body.company or "",
        "fire_ts": fire_ts,
        "fire_at": datetime.fromtimestamp(fire_ts, IST).isoformat(),
        "repeat": body.repeat,
        "status": "scheduled",
    }

    _NOTIFICATIONS.append(notif)
    _ensure_scheduler_running()

    return notif


# =========================
# SCHEDULER
# =========================
def _ensure_scheduler_running():
    global _SCHEDULER_RUNNING
    if not _SCHEDULER_RUNNING:
        _SCHEDULER_RUNNING = True
        asyncio.create_task(_scheduler_loop())


async def _scheduler_loop():
    logger.info("[Scheduler] Started")

    while True:
        await asyncio.sleep(2)

        now = time.time()
        now_ist = datetime.now(IST)

        print(f"⏱ Checking IST: {now_ist}")

        for notif in list(_NOTIFICATIONS):
            if notif["status"] != "scheduled":
                continue

            if notif["fire_ts"] <= now:
                await _fire_notification(notif)


# =========================
# EMAIL TRIGGER
# =========================
async def _fire_notification(notif: dict):
    try:
        print("🔥 FIRE TRIGGERED", notif)

        email = DEFAULT_EMAIL
        logger.info(f"[EMAIL] Sending to {email}")

        sent = await send_reminder_notification(
            to=email,
            user_name=notif["user_name"],
            company=notif["company"],
            message=notif["message"],
            notification_title=notif["title"],
        )

        print("✅ EMAIL SENT:", sent)

        _SENT_LOG.append({
            "id": notif["id"],
            "user_id": notif["user_id"],
            "title": notif["title"],
            "sent_to": email,
            "success": sent,
            "sent_at": datetime.now(IST).isoformat(),
        })

        # =========================
        # 🔁 REPEAT LOGIC
        # =========================
        if notif.get("repeat") == "daily":
            notif["fire_ts"] += 86400
        elif notif.get("repeat") == "weekly":
            notif["fire_ts"] += 7 * 86400
        else:
            notif["status"] = "sent"

        notif["fire_at"] = datetime.fromtimestamp(notif["fire_ts"], IST).isoformat()

    except Exception as e:
        print("❌ EMAIL ERROR:", e)
        logger.error(f"EMAIL FAILED: {e}")
        notif["status"] = "failed"