"""
API response schemas — must match exactly what the Next.js frontend expects.
See: frontend/src/types/index.ts
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ── Article response ──────────────────────────────────────────────────────────

class ArticleResponse(BaseModel):
    id: str
    title: str
    source: str
    sourceUrl: str
    publishedAt: str           # ISO string — frontend uses date-fns to parse
    summary: str
    domain: str
    confidenceScore: int       # 0-100 int, frontend renders as percentage
    sentiment: str             # "positive" | "neutral" | "negative"
    tags: List[str]
    url: str
    imageUrl: Optional[str] = None
    signalScore: int = 0       # bonus field for advanced UI use
    isRisk: bool = False
    isInnovation: bool = False


# ── Insight response ──────────────────────────────────────────────────────────

class InsightResponse(BaseModel):
    id: str
    type: str                  # "trend" | "risk" | "opportunity" | "alert" | "innovation"
    title: str
    description: str
    confidence: int            # 0-100
    createdAt: str             # ISO string


# ── Summary response ─────────────────────────────────────────────────────────

class CompanySummaryResponse(BaseModel):
    overallSentiment: str
    keyThemes: List[str]
    riskFactors: List[str]
    opportunities: List[str]
    sentimentScore: int
    velocityScore: int
    relevanceScore: int
    dominantDomain: str = ""
    competitorMentions: List[str] = Field(default_factory=list)


# ── Risk flag ─────────────────────────────────────────────────────────────────

class RiskFlagResponse(BaseModel):
    id: str
    severity: str              # "high" | "medium" | "low"
    category: str
    description: str
    keywordMatched: str


# ── Domain distribution ───────────────────────────────────────────────────────

class DomainDistributionResponse(BaseModel):
    domain: str
    count: int
    percentage: float
    color: str


# ── Competitor matrix (bonus) ─────────────────────────────────────────────────

class CompetitorMatrixResponse(BaseModel):
    company: str
    domainsCovered: List[str]
    domainScores: Dict[str, float]
    vsMarketAvg: Dict[str, float]


# ── Top-level analysis response ───────────────────────────────────────────────

class AnalyzeResponse(BaseModel):
    """Root response — matches frontend AnalyzeResponse type."""

    company: str
    analyzedAt: str
    totalArticles: int
    articles: List[ArticleResponse]
    insights: List[InsightResponse]
    summary: CompanySummaryResponse
    domainDistribution: List[DomainDistributionResponse]
    riskFlags: List[RiskFlagResponse]
    competitorMatrix: Optional[CompetitorMatrixResponse] = None
    processingTimeMs: float = 0.0
    dataSourcesUsed: List[str] = Field(default_factory=list)
    cacheHit: bool = False
    daysAnalyzed: int = 7


# ── Health response ───────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    app: str
    version: str
    environment: str
    timestamp: str
    services: Dict[str, str] = Field(default_factory=dict)
    ml_models_loaded: bool = False
    tavily_configured: bool = False


# ── Error response ────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    message: str
    request_id: str
    timestamp: str
    path: Optional[str] = None
