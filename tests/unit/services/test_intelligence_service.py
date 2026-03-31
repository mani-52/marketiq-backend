"""Unit tests for IntelligenceService."""

import pytest
from datetime import datetime, timezone

from app.models.article import Article, SentimentLabel
from app.services.intelligence_service import IntelligenceService


@pytest.fixture(scope="module")
def svc():
    return IntelligenceService()


@pytest.fixture
def positive_article():
    return Article(
        id="pos1",
        title="Apple Reports Record Revenue Growth Exceeding Expectations",
        url="https://reuters.com/1",
        source="Reuters",
        source_url="https://reuters.com",
        published_at=datetime.now(tz=timezone.utc),
        summary="Strong earnings beat, record profit, milestone achievement.",
    )


@pytest.fixture
def negative_article():
    return Article(
        id="neg1",
        title="Apple Faces Lawsuit Over Data Breach Security Failure",
        url="https://ft.com/2",
        source="FT",
        source_url="https://ft.com",
        published_at=datetime.now(tz=timezone.utc),
        summary="Security breach investigation lawsuit regulatory fine violation.",
    )


def test_process_returns_same_count(svc, positive_article, negative_article):
    result = svc.process_articles([positive_article, negative_article], "Apple")
    assert len(result) == 2


def test_positive_sentiment_detected(svc, positive_article):
    result = svc.process_articles([positive_article], "Apple")
    assert result[0].sentiment == SentimentLabel.POSITIVE


def test_negative_sentiment_detected(svc, negative_article):
    result = svc.process_articles([negative_article], "Apple")
    assert result[0].sentiment == SentimentLabel.NEGATIVE


def test_risk_flag_set(svc, negative_article):
    result = svc.process_articles([negative_article], "Apple")
    assert result[0].is_risk is True


def test_innovation_signal_set(svc):
    art = Article(
        id="inn1",
        title="Apple Launches AI Breakthrough Platform",
        url="https://tc.com/3",
        source="TC",
        source_url="https://tc.com",
        published_at=datetime.now(tz=timezone.utc),
        summary="New platform launches funding round AI innovation breakthrough.",
    )
    result = svc.process_articles([art], "Apple")
    assert result[0].is_innovation is True


def test_domain_assigned(svc, positive_article):
    result = svc.process_articles([positive_article], "Apple")
    assert result[0].domain is not None


def test_confidence_score_range(svc, positive_article):
    result = svc.process_articles([positive_article], "Apple")
    assert 0.0 <= result[0].confidence_score <= 1.0


def test_signal_score_range(svc, positive_article):
    result = svc.process_articles([positive_article], "Apple")
    assert 0.0 <= result[0].signal_score <= 1.0


def test_aggregate_sentiment_positive(svc):
    arts = [
        Article(
            id=f"a{i}", title="Record revenue profit growth milestone",
            url=f"https://example.com/{i}", source="Test",
            source_url="https://example.com",
            published_at=datetime.now(tz=timezone.utc),
            summary="Strong growth beat expectations record profit.",
            sentiment=SentimentLabel.POSITIVE,
        ) for i in range(5)
    ]
    dominant, score = svc.aggregate_sentiment(arts)
    assert dominant == SentimentLabel.POSITIVE
    assert score > 50


def test_aggregate_sentiment_empty(svc):
    dominant, score = svc.aggregate_sentiment([])
    assert dominant == SentimentLabel.NEUTRAL
    assert score == 50
