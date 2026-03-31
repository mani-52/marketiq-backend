"""
Shared pytest fixtures.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.article import Article, ArticleDomain, SentimentLabel


# ── App fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    """Synchronous test client."""
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture
async def async_client():
    """Async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── Article fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def sample_article() -> Article:
    return Article(
        id="test123",
        title="Apple Reports Record Q3 Revenue, Beats Expectations",
        url="https://reuters.com/article/apple-q3",
        source="Reuters",
        source_url="https://reuters.com",
        published_at=datetime.now(tz=timezone.utc) - timedelta(days=1),
        summary=(
            "Apple Inc. delivered record quarterly revenue of $94.8 billion, "
            "surpassing analyst expectations by 8%. CEO Tim Cook cited strong "
            "iPhone 15 demand and services growth."
        ),
        tags=["Apple", "Finance"],
        confidence_score=0.88,
    )


@pytest.fixture
def risk_article() -> Article:
    return Article(
        id="risk456",
        title="Apple Faces EU Antitrust Investigation Over App Store Practices",
        url="https://ft.com/article/apple-antitrust",
        source="Financial Times",
        source_url="https://ft.com",
        published_at=datetime.now(tz=timezone.utc) - timedelta(days=2),
        summary=(
            "European regulators have launched a formal antitrust investigation "
            "into Apple's App Store policies, citing potential anti-competitive behaviour."
        ),
        tags=["Apple", "Legal"],
        confidence_score=0.82,
    )


@pytest.fixture
def sample_articles(sample_article, risk_article) -> list:
    articles = [sample_article, risk_article]
    # Add variety
    domains = [
        ("Apple Acquires AI Startup for $2B", "M&A", False, True),
        ("Apple CEO Appoints New CFO", "Leadership", False, False),
        ("Apple Launches M4 MacBook Pro Line", "Product", False, True),
        ("Apple Partners with Accenture for Enterprise AI", "Partnerships", False, False),
    ]
    for i, (title, _domain, is_risk, is_innov) in enumerate(domains):
        articles.append(Article(
            id=f"extra{i}",
            title=title,
            url=f"https://example.com/article-{i}",
            source="TechCrunch",
            source_url="https://techcrunch.com",
            published_at=datetime.now(tz=timezone.utc) - timedelta(days=i + 1),
            summary=f"Details about: {title}",
            tags=["Apple"],
            confidence_score=0.75,
            is_risk=is_risk,
            is_innovation=is_innov,
        ))
    return articles
