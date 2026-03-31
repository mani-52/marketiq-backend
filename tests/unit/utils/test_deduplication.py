"""Unit tests for deduplication utilities."""

import pytest
from datetime import datetime, timezone

from app.models.article import Article
from app.utils.deduplication import (
    deduplicate_by_title,
    deduplicate_by_url,
    full_deduplication,
    normalise_url,
)


def make_article(id_, title, url):
    return Article(
        id=id_,
        title=title,
        url=url,
        source="Test",
        source_url="https://test.com",
        published_at=datetime.now(tz=timezone.utc),
        summary="Test summary content for article deduplication testing.",
    )


def test_normalise_url_strips_query():
    url = "https://reuters.com/article/1?ref=twitter&utm_source=feed"
    assert normalise_url(url) == "https://reuters.com/article/1"


def test_normalise_url_strips_fragment():
    url = "https://reuters.com/article/1#section-2"
    assert normalise_url(url) == "https://reuters.com/article/1"


def test_url_dedup_removes_duplicates():
    articles = [
        make_article("1", "Title A", "https://reuters.com/article/1"),
        make_article("2", "Title B", "https://reuters.com/article/1?ref=x"),  # same
        make_article("3", "Title C", "https://reuters.com/article/2"),
    ]
    result = deduplicate_by_url(articles)
    assert len(result) == 2


def test_url_dedup_preserves_order():
    articles = [
        make_article("1", "First", "https://site.com/a"),
        make_article("2", "Second", "https://site.com/b"),
    ]
    result = deduplicate_by_url(articles)
    assert result[0].id == "1"
    assert result[1].id == "2"


def test_title_dedup_removes_similar_titles():
    articles = [
        make_article("1", "Apple Reports Record Revenue Beating Expectations", "https://a.com/1"),
        make_article("2", "Apple Record Revenue Beats Expectations Report", "https://b.com/2"),  # near-dup
        make_article("3", "Tesla Launches New Electric Vehicle Model", "https://c.com/3"),
    ]
    result = deduplicate_by_title(articles, threshold=85)
    assert len(result) == 2


def test_title_dedup_keeps_distinct_titles():
    articles = [
        make_article("1", "Apple Q3 Earnings Beat", "https://a.com/1"),
        make_article("2", "Tesla Self-Driving Update", "https://b.com/2"),
        make_article("3", "Microsoft Azure Revenue Growth", "https://c.com/3"),
    ]
    result = deduplicate_by_title(articles)
    assert len(result) == 3


def test_full_dedup_pipeline():
    articles = [
        make_article("1", "Apple Reports Strong Earnings Growth", "https://reuters.com/1"),
        make_article("2", "Apple Reports Strong Earnings Growth", "https://reuters.com/1"),  # exact dup
        make_article("3", "Tesla New Model Launch Announcement", "https://tc.com/1"),
    ]
    result = full_deduplication(articles)
    assert len(result) == 2


def test_dedup_empty_list():
    assert deduplicate_by_url([]) == []
    assert deduplicate_by_title([]) == []
    assert full_deduplication([]) == []
