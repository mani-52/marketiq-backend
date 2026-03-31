"""
Deduplication utilities — URL-based and title-based.
rapidfuzz is optional; falls back to simple string comparison.
"""
from __future__ import annotations
import logging
from typing import List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

try:
    from rapidfuzz import fuzz as _fuzz
    def _similar(a: str, b: str, threshold: int) -> bool:
        return _fuzz.token_sort_ratio(a, b) >= threshold
except ImportError:
    def _similar(a: str, b: str, threshold: int) -> bool:
        # Simple fallback: check if one is substring of the other
        a, b = a.lower()[:60], b.lower()[:60]
        return a == b or (len(a) > 10 and (a in b or b in a))


def normalise_url(url: str) -> str:
    try:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/").lower()
    except Exception:
        return url.lower().strip()


def deduplicate_by_url(articles: list) -> list:
    seen: set = set()
    result = []
    for a in articles:
        url = a.get("url", "") if isinstance(a, dict) else getattr(a, "url", "")
        key = normalise_url(url)
        if key not in seen:
            seen.add(key)
            result.append(a)
    return result


def deduplicate_by_title(articles: list, threshold: int = 86) -> list:
    result = []
    for candidate in articles:
        t = candidate.get("title", "") if isinstance(candidate, dict) else getattr(candidate, "title", "")
        if not any(_similar(t, (k.get("title", "") if isinstance(k, dict) else getattr(k, "title", "")), threshold)
                   for k in result):
            result.append(candidate)
    return result


def full_deduplication(articles: list, embedder=None) -> list:
    articles = deduplicate_by_url(articles)
    articles = deduplicate_by_title(articles)
    return articles
