"""Embedding service — optional, gracefully degrades without sentence-transformers."""
from __future__ import annotations
import logging
from typing import List
log = logging.getLogger(__name__)


class EmbeddingService:
    """Stub — not required for core functionality."""
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name

    @property
    def is_available(self) -> bool:
        return False

    def semantic_deduplicate(self, texts: List[str], threshold: float = 0.92) -> List[int]:
        return list(range(len(texts)))
