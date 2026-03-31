"""Unit tests for scraping guardrails."""

import pytest
from app.utils.scraping_guardrails import ScrapingGuardrails, BLOCKED_DOMAINS, ALLOWED_DOMAINS


@pytest.fixture
def guardrails():
    return ScrapingGuardrails(timeout=5, max_html_bytes=100_000, rps=10.0)


def test_blocked_domain_rejected(guardrails):
    assert guardrails.is_allowed_domain("https://facebook.com/page") is False
    assert guardrails.is_allowed_domain("https://twitter.com/news") is False
    assert guardrails.is_allowed_domain("https://reddit.com/r/finance") is False


def test_allowed_news_domain_passes(guardrails):
    assert guardrails.is_allowed_domain("https://reuters.com/article/1") is True
    assert guardrails.is_allowed_domain("https://techcrunch.com/2024/article") is True


def test_extract_domain(guardrails):
    assert guardrails.extract_domain("https://www.reuters.com/article") == "reuters.com"
    assert guardrails.extract_domain("https://techcrunch.com/news") == "techcrunch.com"


def test_all_blocked_domains_rejected(guardrails):
    for domain in BLOCKED_DOMAINS:
        url = f"https://{domain}/some-path"
        assert guardrails.is_allowed_domain(url) is False, f"Should block {domain}"


@pytest.mark.asyncio
async def test_check_blocked_domain_returns_false(guardrails):
    allowed, reason = await guardrails.check("https://facebook.com/article")
    assert allowed is False
    assert "blocked" in reason.lower()


@pytest.mark.asyncio
async def test_rate_limiter_allows_first_request():
    """Rate limiter should immediately allow the first request per domain."""
    from app.utils.scraping_guardrails import DomainRateLimiter
    import time
    limiter = DomainRateLimiter(rps=100.0)  # fast
    t0 = time.monotonic()
    await limiter.acquire("example.com")
    elapsed = time.monotonic() - t0
    assert elapsed < 0.5  # should be near-instant
