"""Scraping guardrails — rate limiting and domain blocking."""
from __future__ import annotations
import asyncio
import time
from collections import defaultdict
from typing import Dict, Tuple
from urllib.parse import urlparse

BLOCKED_DOMAINS = {
    "facebook.com", "twitter.com", "x.com", "instagram.com",
    "tiktok.com", "pinterest.com", "reddit.com", "youtube.com",
}


class DomainRateLimiter:
    def __init__(self, rps: float = 1.5) -> None:
        self.interval = 1.0 / max(rps, 0.1)
        self._last: Dict[str, float] = defaultdict(float)
        self._lock = asyncio.Lock()

    async def acquire(self, domain: str) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self.interval - (now - self._last[domain])
            if wait > 0:
                await asyncio.sleep(wait)
            self._last[domain] = time.monotonic()


class ScrapingGuardrails:
    def __init__(self, timeout: int = 12, max_html_bytes: int = 600_000, rps: float = 1.5) -> None:
        self.timeout = timeout
        self.max_html_bytes = max_html_bytes
        self.rate_limiter = DomainRateLimiter(rps)

    def extract_domain(self, url: str) -> str:
        try:
            return urlparse(url).netloc.lstrip("www.").lower()
        except Exception:
            return ""

    def is_blocked(self, url: str) -> bool:
        return self.extract_domain(url) in BLOCKED_DOMAINS

    async def check(self, url: str) -> Tuple[bool, str]:
        if self.is_blocked(url):
            return False, "blocked domain"
        domain = self.extract_domain(url)
        await self.rate_limiter.acquire(domain)
        return True, "ok"
