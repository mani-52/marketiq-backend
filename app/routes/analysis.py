"""
Main analysis route — orchestrates all intelligence pipeline steps.
All data is real — no dummy fallbacks, no fabrication.

Changes v3:
- days param now ge=1, le=30 (user-specified 1-30)
- Optional auth: if Authorization header present, email notifications fire
- Domain classification matrix integrated into response
"""
import asyncio
import logging
import time
import re
import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from cachetools import TTLCache

from app.config import settings
from app.services.tavily_service import (
    fetch_company_news,
    normalize_company_name,
    is_strictly_relevant_to_company,
)
from app.services.intelligence_service import (
    classify_domain,
    analyze_sentiment,
    detect_risk_flags,
    detect_innovation_signals,
    compute_domain_distribution,
    compute_scores,
    extract_key_themes,
    extract_risk_factors,
    extract_opportunities,
)
from app.services.insight_engine import generate_insights, build_competitor_matrix
from app.ml.training_data import DOMAIN_COLORS, get_domain_matrix

router = APIRouter()
logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

# 5-minute TTL cache
_cache = TTLCache(maxsize=256, ttl=300)


def _cache_key(company: str, days: int) -> str:
    return hashlib.md5(f"{company.lower().strip()}:{days}".encode()).hexdigest()


def _article_mentions_company(article: dict, company: str) -> bool:
    name_lower = company.lower().strip()
    name_normalized = normalize_company_name(company).lower()
    title = (article.get("title") or "").lower()
    summary = (article.get("summary") or "").lower()
    url = (article.get("url") or "").lower()
    combined = title + " " + summary + " " + url
    escaped = re.escape(name_lower)
    if re.search(rf'\b{escaped}\b', combined):
        return True
    if name_normalized and len(name_normalized) > 3:
        if re.search(rf'\b{re.escape(name_normalized)}\b', combined):
            return True
    return False


def _process_article(raw: dict, company: str, idx: int) -> Optional[dict]:
    title = (raw.get("title") or "").strip()
    url = (raw.get("url") or "").strip()
    content = (raw.get("content") or "")
    published_date = (raw.get("published_date") or "")

    if not title or not url:
        return None

    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        source = parsed.netloc.replace("www.", "").split(".")[0].title()
        source_url = f"https://{parsed.netloc}" if parsed.netloc else ""
    except Exception:
        source = "Unknown"
        source_url = ""

    summary = _extract_summary(content, title)
    domain, confidence = classify_domain(title, content)
    sentiment, sent_conf = analyze_sentiment(title, content)
    tags = _extract_tags(title, content, company)
    signal_score = round(confidence * 50 + sent_conf * 30 + 20)

    from app.ml.training_data import INNOVATION_KEYWORDS, RISK_KEYWORDS
    text_lower = (title + " " + content[:400]).lower()
    is_risk = any(
        kw in text_lower
        for severity in RISK_KEYWORDS.values()
        for kws in severity.values()
        for kw in kws
    )
    is_innovation = any(kw in text_lower for kw in INNOVATION_KEYWORDS)
    pub_at = _parse_date(published_date)

    return {
        "id": f"art_{idx}",
        "title": title,
        "source": source,
        "sourceUrl": source_url,
        "publishedAt": pub_at,
        "summary": summary,
        "domain": domain,
        "confidenceScore": round(confidence * 100),
        "sentiment": sentiment,
        "tags": tags,
        "url": url,
        "signalScore": min(100, signal_score),
        "isRisk": is_risk,
        "isInnovation": is_innovation,
    }


def _extract_summary(content: str, fallback: str) -> str:
    if not content:
        return fallback[:300]
    sentences = re.split(r'(?<=[.!?])\s+', content.strip())
    good = [s.strip() for s in sentences if len(s.strip()) > 30][:2]
    return " ".join(good) if good else content[:300]


def _extract_tags(title: str, content: str, company: str) -> list:
    text = (title + " " + content[:300]).lower()
    TAG_WORDS = [
        "ai", "earnings", "acquisition", "ipo", "lawsuit", "partnership",
        "launch", "expansion", "revenue", "layoffs", "funding", "quarterly",
        "merger", "regulatory", "patent", "sustainability", "investment",
        "product", "technology", "innovation",
    ]
    tags = [company]
    for w in TAG_WORDS:
        if w in text and w.lower() != company.lower():
            tags.append(w)
    return tags[:5]


def _parse_date(date_str: str) -> str:
    if not date_str:
        return datetime.now(timezone.utc).isoformat()
    try:
        from dateutil import parser as dateparser
        dt = dateparser.parse(date_str)
        if dt:
            return dt.isoformat()
    except Exception:
        pass
    return datetime.now(timezone.utc).isoformat()


@router.get("/analyze")
async def analyze(
    company: str = Query(..., min_length=1, max_length=200, description="Company name to analyze"),
    days: int = Query(7, ge=1, le=30, description="Number of days to look back (1-30)"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    company = company.strip()
    if not company:
        raise HTTPException(status_code=400, detail="Company name cannot be empty")

    # Optionally decode current user for notification hooks
    current_user = None
    if credentials:
        try:
            from app.routes.auth import decode_token
            current_user = decode_token(credentials.credentials)
        except Exception:
            pass  # Auth is optional on this endpoint

    cache_key = _cache_key(company, days)
    if cache_key in _cache:
        logger.info(f"Cache hit for '{company}'")
        result = dict(_cache[cache_key])
        result["cacheHit"] = True
        return result

    if not settings.has_tavily:
        raise HTTPException(
            status_code=503,
            detail=(
                "No Tavily API key configured. This API only returns real data. "
                "Add TAVILY_API_KEY=tvly-... to your backend .env file."
            ),
        )

    start = time.time()
    logger.info(f"Analyzing '{company}' for {days} days")

    try:
        raw_results = await fetch_company_news(settings.TAVILY_API_KEY, company, days)
    except Exception as e:
        logger.error(f"Tavily fetch failed for '{company}': {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch news: {str(e)}")

    if not raw_results:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No news found for '{company}' in the last {days} days. "
                "Try a longer time window or check the company name spelling."
            ),
        )

    articles = []
    for i, raw in enumerate(raw_results):
        processed = _process_article(raw, company, i)
        if processed is None:
            continue
        if not _article_mentions_company(processed, company):
            continue
        articles.append(processed)

    if not articles:
        raise HTTPException(
            status_code=404,
            detail=f"No verified articles about '{company}' found. Try a different name or longer window.",
        )

    logger.info(f"[{company}] Verified {len(articles)} articles (from {len(raw_results)} raw)")

    risk_flags = detect_risk_flags(articles)
    domain_dist = compute_domain_distribution(articles)
    innovation_count = detect_innovation_signals(articles)
    scores = compute_scores(articles, risk_flags, innovation_count)
    insights = generate_insights(company, articles, risk_flags, domain_dist, scores)
    competitor_matrix = build_competitor_matrix(company, articles, domain_dist)

    pos = sum(1 for a in articles if a["sentiment"] == "positive")
    neg = sum(1 for a in articles if a["sentiment"] == "negative")
    overall = "positive" if pos > neg else "negative" if neg > pos else "neutral"

    sources = list({a["source"] for a in articles if a["source"] != "Unknown"})[:10]

    # Enrich domain distribution with matrix metadata
    matrix = get_domain_matrix()
    for dd in domain_dist:
        d = dd["domain"]
        dd["riskWeight"] = matrix["dimensions"]["risk_weight"].get(d, 0.5)
        dd["innovationWeight"] = matrix["dimensions"]["innovation_weight"].get(d, 0.5)
        dd["volatilityWeight"] = matrix["dimensions"]["volatility_weight"].get(d, 0.5)
        dd["growthSignal"] = matrix["dimensions"]["growth_signal"].get(d, 0.5)
        dd["description"] = matrix["description"].get(d, "")

    result = {
        "company": company,
        "analyzedAt": datetime.now(timezone.utc).isoformat(),
        "totalArticles": len(articles),
        "daysAnalyzed": days,
        "cacheHit": False,
        "processingTimeMs": round((time.time() - start) * 1000),
        "dataSourcesUsed": sources,
        "articles": articles,
        "summary": {
            "overallSentiment": overall,
            "keyThemes": extract_key_themes(articles),
            "riskFactors": extract_risk_factors(risk_flags),
            "opportunities": extract_opportunities(articles),
            "sentimentScore": scores["sentimentScore"],
            "velocityScore": scores["velocityScore"],
            "relevanceScore": scores["relevanceScore"],
            "dominantDomain": domain_dist[0]["domain"] if domain_dist else "Market",
            "competitorMentions": [],
        },
        "domainDistribution": domain_dist,
        "domainMatrix": matrix,
        "riskFlags": risk_flags,
        "insights": insights,
        "competitorMatrix": competitor_matrix,
    }

    _cache[cache_key] = result

    # Fire post-analysis notifications if user is authenticated
    if current_user:
        asyncio.create_task(_post_analysis_notifications(
            current_user, company, len(articles), overall, days, risk_flags
        ))

    return result


async def _post_analysis_notifications(
    user: dict,
    company: str,
    total_articles: int,
    sentiment: str,
    days: int,
    risk_flags: list,
):
    from app.routes.notifications import notify_analysis_done, notify_risk_alert
    uid = user.get("sub", "")
    email = user.get("email", "")
    name = user.get("name", "User")

    if not email:
        return

    await notify_analysis_done(uid, email, name, company, total_articles, sentiment, days)

    high_risks = [r for r in risk_flags if r.get("severity", "").upper() == "HIGH"]
    if high_risks:
        await notify_risk_alert(uid, email, name, company, len(high_risks), high_risks[0].get("description", "Risk detected"))
