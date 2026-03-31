"""Unit tests for date filtering."""

import pytest
from datetime import datetime, timedelta, timezone

from app.utils.date_filter import (
    filter_by_days,
    is_within_days,
    parse_date,
    days_ago,
    format_iso,
)


def test_parse_date_iso():
    dt = parse_date("2024-03-15T10:30:00Z")
    assert dt is not None
    assert dt.year == 2024
    assert dt.month == 3


def test_parse_date_returns_none_for_garbage():
    assert parse_date("not-a-date") is None
    assert parse_date("") is None


def test_parse_date_adds_utc_if_naive():
    dt = parse_date("2024-01-01T12:00:00")
    assert dt is not None
    assert dt.tzinfo is not None


def test_is_within_days_recent():
    recent = datetime.now(tz=timezone.utc) - timedelta(days=3)
    assert is_within_days(recent, 7) is True


def test_is_within_days_old():
    old = datetime.now(tz=timezone.utc) - timedelta(days=30)
    assert is_within_days(old, 7) is False


def test_is_within_days_none():
    assert is_within_days(None, 7) is False


def test_filter_by_days_keeps_recent(sample_articles):
    recent_only = filter_by_days(sample_articles, days=30)
    assert len(recent_only) == len(sample_articles)  # all should be recent


def test_filter_by_days_removes_old():
    from app.models.article import Article

    old = Article(
        id="old1",
        title="Old Article",
        url="https://example.com/old",
        source="Test",
        source_url="https://test.com",
        published_at=datetime.now(tz=timezone.utc) - timedelta(days=60),
        summary="Old article content.",
    )
    recent = Article(
        id="new1",
        title="New Article",
        url="https://example.com/new",
        source="Test",
        source_url="https://test.com",
        published_at=datetime.now(tz=timezone.utc) - timedelta(days=2),
        summary="New article content.",
    )
    result = filter_by_days([old, recent], days=7)
    assert len(result) == 1
    assert result[0].id == "new1"


def test_days_ago_returns_correct_delta():
    now = datetime.now(tz=timezone.utc)
    result = days_ago(7)
    diff = now - result
    assert 6 <= diff.days <= 7


def test_format_iso():
    dt = datetime(2024, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
    iso = format_iso(dt)
    assert "2024-03-15" in iso
    assert "T" in iso
