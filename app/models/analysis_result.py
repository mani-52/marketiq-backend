"""Analysis result model."""
from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    company: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    days_analyzed: int
    total_articles: int
    articles: list = Field(default_factory=list)
    insights: list = Field(default_factory=list)
    risk_flags: list = Field(default_factory=list)
    domain_distribution: list = Field(default_factory=list)
    processing_time_ms: float = 0.0
    data_sources_used: List[str] = Field(default_factory=list)
    cache_hit: bool = False
