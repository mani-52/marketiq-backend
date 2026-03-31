"""Model registry stub — not used in current simplified pipeline."""
from __future__ import annotations
import logging
log = logging.getLogger(__name__)

class ModelRegistry:
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_ready(self) -> bool:
        return True
