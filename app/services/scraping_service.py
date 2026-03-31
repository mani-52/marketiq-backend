"""
Web scraping service — optional, requires beautifulsoup4 + lxml.
Falls back gracefully if not installed.
"""
from __future__ import annotations
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

try:
    import httpx
    from bs4 import BeautifulSoup
    _SCRAPING_AVAILABLE = True
except ImportError:
    _SCRAPING_AVAILABLE = False
    logger.info("beautifulsoup4/lxml not installed — scraping disabled (Tavily is the primary source)")


class ScrapingService:
    def __init__(self, timeout: int = 12, max_html_bytes: int = 600_000, rps: float = 1.5) -> None:
        self.timeout = timeout

    async def scrape_urls(self, urls: List[str], company: str, max_pages: int = 5) -> list:
        if not _SCRAPING_AVAILABLE:
            return []
        # Minimal implementation — primary source is Tavily
        return []
