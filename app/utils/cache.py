"""Simple TTL in-memory cache for analysis results."""
from __future__ import annotations
import logging
from typing import Any, Optional
from cachetools import TTLCache
from app.config import get_settings

logger = logging.getLogger(__name__)


class AnalysisCache:
    def __init__(self) -> None:
        s = get_settings()
        self._cache: TTLCache = TTLCache(
            maxsize=s.cache_max_size,
            ttl=s.cache_ttl_seconds,
        )

    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value

    def delete(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)
