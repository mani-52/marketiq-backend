"""
Integration tests — exercises the full pipeline end-to-end
using mock data (no external API calls).
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

from app.models.article import Article, ArticleDomain, SentimentLabel
from app.services.intelligence_service import IntelligenceService
from app.services.insight_engine import InsightEngine


def make_articles(company: str, count: int = 8) -> list:
    domains = [
        ArticleDomain.FINANCE, ArticleDomain.PRODUCT, ArticleDomain.LEGAL,
        ArticleDomain.MERGERS, ArticleDomain.LEADERSHIP, ArticleDomain.PARTNERSHIPS,
        ArticleDomain.ESG, ArticleDomain.TECHNOLOGY,
    ]
    titles = [
        f"{company} Reports Record Q3 Revenue",
        f"{company} Launches AI-Powered Platform",
        f"{company} Faces Antitrust Investigation",
        f"{company} Acquires AI Startup for $2B",
        f"{company} Appoints New CTO",
        f"{company} Partners with AWS",
        f"{company} Commits to Net Zero",
        f"{company} Expands Cloud Infrastructure",
    ]
    arts = []
    for i in range(min(count, len(titles))):
        arts.append(Article(
            id=f"int{i}",
            title=titles[i],
            url=f"https://example.com/{company.lower()}-{i}",
            source="Reuters",
            source_url="https://reuters.com",
            published_at=datetime.now(tz=timezone.utc) - timedelta(days=i),
            summary=f"Detailed content about: {titles[i]}. Analysis shows significant impact.",
            domain=domains[i],
            tags=[company],
            confidence_score=0.80,
        ))
    return arts


@pytest.mark.asyncio
async def test_full_pipeline_stripe():
    """Full pipeline test for Stripe."""
    articles = make_articles("Stripe", 8)
    intel_svc = IntelligenceService()
    engine = InsightEngine()

    processed = intel_svc.process_articles(articles, "Stripe")
    assert len(processed) == 8

    # All articles should have domain, sentiment, scores
    for art in processed:
        assert art.domain is not None
        assert art.sentiment in (SentimentLabel.POSITIVE, SentimentLabel.NEUTRAL, SentimentLabel.NEGATIVE)
        assert 0.0 <= art.confidence_score <= 1.0

    result = engine.generate("Stripe", processed, 7, ["Tavily"])
    assert result.company == "Stripe"
    assert result.total_articles == 8
    assert len(result.domain_distribution) > 0
    assert len(result.insights) > 0


@pytest.mark.asyncio
async def test_risk_detection_pipeline():
    """Articles with risk keywords should produce risk flags."""
    arts = make_articles("NVIDIA", 4)
    # Inject a clear risk article
    arts[2].title = "NVIDIA Faces Major Class Action Lawsuit Over Securities Fraud"
    arts[2].summary = "Lawsuit filed alleging securities fraud and data breach violations."
    arts[2].is_risk = True

    engine = InsightEngine()
    result = engine.generate("NVIDIA", arts, 7, ["Tavily"])

    assert len(result.risk_flags) > 0


@pytest.mark.asyncio
async def test_innovation_insight_generated():
    """Innovation articles should trigger innovation insight."""
    arts = make_articles("OpenAI", 4)
    arts[0].title = "OpenAI Announces Major AI Breakthrough and New Product Launch"
    arts[0].summary = "Revolutionary AI breakthrough launches new platform with startup funding."
    arts[0].is_innovation = True

    engine = InsightEngine()
    result = engine.generate("OpenAI", arts, 7, ["Tavily"])

    insight_types = [i.type for i in result.insights]
    assert "innovation" in insight_types or "trend" in insight_types


@pytest.mark.asyncio
async def test_end_to_end_api_call(async_client):
    """Test full API call with mock-backed services."""
    resp = await async_client.get("/analyze?company=Anthropic&days=14")
    assert resp.status_code == 200

    data = resp.json()
    assert data["company"] == "Anthropic"
    assert data["daysAnalyzed"] == 14
    assert len(data["articles"]) > 0
    assert len(data["insights"]) > 0
    assert data["summary"]["sentimentScore"] >= 0
