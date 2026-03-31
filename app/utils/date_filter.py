"""Date-range filtering utilities."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import List, Optional, TypeVar
import logging

logger = logging.getLogger(__name__)
T = TypeVar("T")


def utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        from dateutil import parser as dateparser
        dt = dateparser.parse(date_str)
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def is_within_days(dt: Optional[datetime], days: int) -> bool:
    if dt is None:
        return False
    cutoff = utcnow() - timedelta(days=days)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt >= cutoff


def filter_by_days(items: List[T], days: int, date_attr: str = "published_at") -> List[T]:
    result = []
    cutoff = utcnow() - timedelta(days=days)
    for item in items:
        dt = getattr(item, date_attr, None) if not isinstance(item, dict) else item.get(date_attr)
        if dt is None:
            result.append(item)
            continue
        if isinstance(dt, str):
            dt = parse_date(dt)
        if dt is None:
            result.append(item)
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if dt >= cutoff:
            result.append(item)
    return result


def days_ago(days: int) -> datetime:
    return utcnow() - timedelta(days=days)


def format_iso(dt: datetime) -> str:
    return dt.isoformat()
