"""Unit tests for InsightEngine."""

import pytest
from datetime import datetime, timezone, timedelta

from app.models.article import Article, ArticleDomain, SentimentLabel
from app.services.insight_engine import InsightEngine


@pytest.fixture(scope="module")
def engine():
    return InsightEngine()


@pytest.fixture
def enriched_articles():
    articles = []
    configs = [
        ("Apple Earnings Beat Expectations", ArticleDomain.FINANCE, SentimentLabel.POSITIVE, False, False),
        ("Apple Launches AI Platform", ArticleDomain.PRODUCT, SentimentLabel.POSITIVE, False, True),
        ("Apple Faces EU Antitrust Probe", ArticleDomain.LEGAL, SentimentLabel.NEGATIVE, True, False),
        ("Apple Acquires AI Startup", ArticleDomain.MERGERS, SentimentLabel.POSITIVE, False, True),
        ("Apple CFO Departs", ArticleDomain.LEADERSHIP, SentimentLabel.NEUTRAL, False, False),
        ("Apple Cloud Partnership", ArticleDomain.PARTNERSHIPS, SentimentLabel.POSITIVE, False, False),
        ("Apple ESG Commitment", ArticleDomain.ESG, SentimentLabel.POSITIVE, False, False),
    ]
    for i, (title, domain, sentiment, is_risk, is_innov) in enumerate(configs):
        articles.append(Article(
            id=f"eng{i}",
            title=title,
            url=f"https://example.com/{i}",
            source="Reuters",
            source_url="https://reuters.com",
            published_at=datetime.now(tz=timezone.utc) - timedelta(days=i),
            summary=f"Summary of: {title}",
            domain=domain,
            sentiment=sentiment,
            is_risk=is_risk,
            is_innovation=is_innov,
            confidence_score=0.82,
            signal_score=0.78,
        ))
    return articles


def test_generate_returns_result(engine, enriched_articles):
    result = engine.generate(
        company="Apple",
        articles=enriched_articles,
        days=7,
        data_sources=["Tavily"],
    )
    assert result.company == "Apple"
    assert result.total_articles == len(enriched_articles)


def test_domain_distribution_populated(engine, enriched_articles):
    result = engine.generate("Apple", enriched_articles, 7, ["Tavily"])
    assert len(result.domain_distribution) > 0
    total = sum(d.count for d in result.domain_distribution)
    assert total == len(enriched_articles)


def test_insights_generated(engine, enriched_articles):
    result = engine.generate("Apple", enriched_articles, 7, ["Tavily"])
    assert len(result.insights) > 0


def test_risk_flags_detected(engine, enriched_articles):
    result = engine.generate("Apple", enriched_articles, 7, ["Tavily"])
    assert len(result.risk_flags) > 0
    # Risk articles should produce flags
    severities = {f.severity for f in result.risk_flags}
    assert severities.issubset({"high", "medium", "low"})


def test_summary_fields(engine, enriched_articles):
    result = engine.generate("Apple", enriched_articles, 7, ["Tavily"])
    s = result.summary
    assert 0 <= s.sentiment_score <= 100
    assert 0 <= s.velocity_score <= 100
    assert 0 <= s.relevance_score <= 100
    assert s.overall_sentiment in ("positive", "neutral", "negative")


def test_competitor_matrix_built(engine, enriched_articles):
    result = engine.generate("Apple", enriched_articles, 7, ["Tavily"])
    assert result.competitor_matrix is not None
    assert result.competitor_matrix.company == "Apple"
    assert len(result.competitor_matrix.domains_covered) > 0


def test_empty_articles(engine):
    result = engine.generate("Unknown", [], 7, [])
    assert result.total_articles == 0
    assert result.domain_distribution == []


def test_processing_time_recorded(engine, enriched_articles):
    result = engine.generate("Apple", enriched_articles, 7, ["Tavily"], processing_time_ms=123.4)
    assert result.processing_time_ms == 123.4
