"""
Gemini AI Insights — generates analyst-quality interpretations from analysis data.
Uses Google Gemini API (gemini-1.5-flash) for fast, high-quality analysis.
Falls back gracefully if API key not configured.
"""
from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


class InsightRequest(BaseModel):
    company: str
    total_articles: int
    days: int
    overall_sentiment: str
    sentiment_score: int
    velocity_score: int
    relevance_score: int
    dominant_domain: str
    key_themes: list[str]
    risk_factors: list[str]
    opportunities: list[str]
    risk_flag_count: int
    high_risk_count: int
    domain_distribution: list[dict]
    top_insights: list[dict]


class GeminiInsightResponse(BaseModel):
    executive_summary: str
    market_position: str
    bullish_signals: list[str]
    bearish_signals: list[str]
    key_risks: list[str]
    opportunities: list[str]
    analyst_verdict: str
    actionable_recommendations: list[str]
    confidence_note: str
    generated_by: str


def _build_prompt(data: InsightRequest) -> str:
    domain_text = ", ".join(
        f"{d['domain']} ({d['percentage']}%)"
        for d in sorted(data.domain_distribution, key=lambda x: -x.get('percentage', 0))[:4]
    )
    themes_text = ", ".join(data.key_themes[:6]) if data.key_themes else "None identified"
    risks_text  = "; ".join(data.risk_factors[:4]) if data.risk_factors else "None identified"
    opps_text   = "; ".join(data.opportunities[:4]) if data.opportunities else "None identified"
    insights_text = "\n".join(
        f"- [{i.get('type','').upper()}] {i.get('title','')}: {i.get('description','')[:120]}"
        for i in data.top_insights[:5]
    ) if data.top_insights else "No insights available"

    return f"""You are a senior equity research analyst at a top-tier investment bank.
Analyze the following market intelligence data for {data.company} and produce a structured analyst report.

DATA SUMMARY:
- Company: {data.company}
- Analysis period: {data.days} days
- Articles analyzed: {data.total_articles}
- Overall sentiment: {data.overall_sentiment} (score: {data.sentiment_score}/100)
- News velocity score: {data.velocity_score}/100
- Relevance score: {data.relevance_score}/100
- Dominant news domain: {data.dominant_domain}
- Domain breakdown: {domain_text}
- Key themes: {themes_text}
- Risk factors identified: {risks_text}
- Risk flags: {data.risk_flag_count} total, {data.high_risk_count} HIGH severity
- Opportunities: {opps_text}

AI-DETECTED SIGNALS:
{insights_text}

Produce your analysis as a valid JSON object with EXACTLY these keys:
{{
  "executive_summary": "2-3 sentence executive summary of the current market position",
  "market_position": "1-2 sentence assessment of competitive/market position",
  "bullish_signals": ["signal 1", "signal 2", "signal 3"],
  "bearish_signals": ["signal 1", "signal 2", "signal 3"],
  "key_risks": ["risk 1 with reasoning", "risk 2 with reasoning"],
  "opportunities": ["opportunity 1 with context", "opportunity 2 with context"],
  "analyst_verdict": "BUY/HOLD/SELL/WATCH with 1 sentence rationale",
  "actionable_recommendations": ["specific action 1", "specific action 2", "specific action 3"],
  "confidence_note": "Brief note on data quality and confidence level"
}}

Rules:
- Be specific to {data.company}, not generic
- Use actual data points from the analysis
- Write like a Bloomberg/Reuters analyst, not a chatbot
- Each list item should be 1 concise sentence
- Return ONLY the JSON object, no markdown, no preamble"""


async def _call_gemini(prompt: str, api_key: str) -> dict:
    import httpx, json
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()

    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    # Strip markdown code blocks if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def _fallback_insights(data: InsightRequest) -> dict:
    """Rule-based fallback when Gemini is not available."""
    sentiment_label = {
        "positive": "constructive", "negative": "cautious", "neutral": "neutral"
    }.get(data.overall_sentiment, "neutral")

    bull = []
    bear = []

    if data.sentiment_score > 60:
        bull.append(f"Positive sentiment momentum at {data.sentiment_score}/100 across {data.total_articles} articles")
    else:
        bear.append(f"Subdued sentiment score of {data.sentiment_score}/100 warrants monitoring")

    if data.velocity_score > 60:
        bull.append(f"High news velocity ({data.velocity_score}/100) indicates elevated market attention")
    
    if data.high_risk_count > 0:
        bear.append(f"{data.high_risk_count} high-severity risk flag(s) detected — requires immediate attention")

    for opp in data.opportunities[:2]:
        bull.append(opp)
    for risk in data.risk_factors[:2]:
        bear.append(risk)

    verdict = "WATCH"
    if data.sentiment_score >= 70 and data.high_risk_count == 0:
        verdict = "BUY — positive signals with manageable risk profile"
    elif data.high_risk_count >= 2 or data.sentiment_score < 35:
        verdict = "SELL/REDUCE — elevated risk flags and negative sentiment"
    elif data.sentiment_score >= 55:
        verdict = "HOLD — balanced risk/reward at current levels"
    else:
        verdict = "WATCH — insufficient signal clarity for conviction"

    return {
        "executive_summary": (
            f"{data.company} shows {sentiment_label} market dynamics over the past {data.days} days. "
            f"Analysis of {data.total_articles} articles reveals {data.dominant_domain}-dominated coverage "
            f"with a sentiment score of {data.sentiment_score}/100."
        ),
        "market_position": (
            f"Coverage is concentrated in {data.dominant_domain} with {data.risk_flag_count} risk flags identified. "
            f"News velocity of {data.velocity_score}/100 suggests {'elevated' if data.velocity_score > 60 else 'moderate'} market attention."
        ),
        "bullish_signals": bull[:3] if bull else ["Insufficient positive signals detected in this window"],
        "bearish_signals": bear[:3] if bear else ["No material negative signals detected"],
        "key_risks": [r for r in data.risk_factors[:3]] if data.risk_factors else ["Monitor for emerging regulatory or operational risks"],
        "opportunities": [o for o in data.opportunities[:3]] if data.opportunities else ["Identify catalysts in the next earnings cycle"],
        "analyst_verdict": verdict,
        "actionable_recommendations": [
            f"Monitor {data.dominant_domain.lower()} news flow for next 7 days",
            "Set alerts for high-severity risk escalations",
            f"Review sentiment trajectory before significant position changes",
        ],
        "confidence_note": f"Based on {data.total_articles} articles over {data.days} days. {'Gemini AI unavailable — rule-based analysis.' if True else ''}",
    }


@router.post("/insights", response_model=GeminiInsightResponse)
async def generate_ai_insights(body: InsightRequest):
    """Generate AI analyst insights using Gemini 1.5 Flash."""
    import os
    api_key = os.environ.get("GEMINI_API_KEY", "")

    if api_key:
        try:
            prompt = _build_prompt(body)
            raw = await _call_gemini(prompt, api_key)
            return GeminiInsightResponse(
                executive_summary       = raw.get("executive_summary", ""),
                market_position         = raw.get("market_position", ""),
                bullish_signals         = raw.get("bullish_signals", []),
                bearish_signals         = raw.get("bearish_signals", []),
                key_risks               = raw.get("key_risks", []),
                opportunities           = raw.get("opportunities", []),
                analyst_verdict         = raw.get("analyst_verdict", "WATCH"),
                actionable_recommendations = raw.get("actionable_recommendations", []),
                confidence_note         = raw.get("confidence_note", ""),
                generated_by            = "gemini-1.5-flash",
            )
        except Exception as e:
            logger.warning(f"Gemini call failed ({e}), using rule-based fallback")

    # Fallback
    fb = _fallback_insights(body)
    return GeminiInsightResponse(**fb, generated_by="rule-based-fallback")
