"""
Search Service — not used in the primary analysis pipeline.
The analysis route calls tavily_service.fetch_company_news directly.
This file is kept for compatibility.
"""
from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
