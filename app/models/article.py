"""Core domain model for a news article."""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Article(BaseModel):
    id: str
    title: str
    url: str
    source: str = "Unknown"
    source_url: str = ""
    published_at: datetime
    summary: str = ""
    full_content: str = Field(default="", exclude=True)
    domain: str = "Market"
    confidence_score: float = 0.5
    sentiment: str = "neutral"
    tags: List[str] = Field(default_factory=list)
    signal_score: float = 0.0
    is_risk: bool = False
    is_innovation: bool = False

    class Config:
        use_enum_values = True
