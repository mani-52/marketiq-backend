"""Tests for /analyze endpoint."""

import pytest
from unittest.mock import AsyncMock, patch

from app.models.article import Article, ArticleDomain, SentimentLabel
from datetime import datetime, timezone


def test_analyze_missing_company(client):
    resp = client.get("/analyze")
    assert resp.status_code == 422


def test_analyze_days_too_large(client):
    resp = client.get("/analyze?company=Apple&days=999")
    assert resp.status_code == 422


def test_analyze_days_zero(client):
    resp = client.get("/analyze?company=Apple&days=0")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_analyze_returns_schema(async_client):
    """Test that the response matches the expected schema."""
    resp = await async_client.get("/analyze?company=TestCorp&days=7")
    assert resp.status_code == 200
    data = resp.json()

    # Top-level fields
    required = {"company", "analyzedAt", "totalArticles", "articles",
                 "insights", "summary", "domainDistribution", "riskFlags"}
    assert required.issubset(set(data.keys()))

    assert data["company"] == "TestCorp"
    assert data["daysAnalyzed"] == 7
    assert isinstance(data["articles"], list)
    assert isinstance(data["insights"], list)
    assert isinstance(data["domainDistribution"], list)
    assert isinstance(data["riskFlags"], list)


@pytest.mark.asyncio
async def test_analyze_article_schema(async_client):
    """Each article must have the fields the frontend expects."""
    resp = await async_client.get("/analyze?company=Stripe&days=7")
    assert resp.status_code == 200
    data = resp.json()

    if data["articles"]:
        art = data["articles"][0]
        required_fields = {
            "id", "title", "source", "sourceUrl", "publishedAt",
            "summary", "domain", "confidenceScore", "sentiment", "tags", "url"
        }
        assert required_fields.issubset(set(art.keys()))
        assert isinstance(art["confidenceScore"], int)
        assert 0 <= art["confidenceScore"] <= 100
        assert art["sentiment"] in ("positive", "neutral", "negative")


@pytest.mark.asyncio
async def test_analyze_summary_schema(async_client):
    resp = await async_client.get("/analyze?company=Apple&days=7")
    summary = resp.json()["summary"]
    required = {
        "overallSentiment", "keyThemes", "riskFactors",
        "opportunities", "sentimentScore", "velocityScore", "relevanceScore"
    }
    assert required.issubset(set(summary.keys()))
    assert 0 <= summary["sentimentScore"] <= 100
    assert 0 <= summary["velocityScore"] <= 100


@pytest.mark.asyncio
async def test_analyze_cache_hit(async_client):
    """Second identical request should be served from cache."""
    await async_client.get("/analyze?company=CacheTest&days=7")
    resp2 = await async_client.get("/analyze?company=CacheTest&days=7")
    assert resp2.status_code == 200
    assert resp2.json()["cacheHit"] is True


@pytest.mark.asyncio
async def test_analyze_root_redirects(async_client):
    resp = await async_client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "docs" in data
    assert "analyze" in data
