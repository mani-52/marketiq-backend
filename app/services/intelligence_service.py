"""
Intelligence service — domain classification, sentiment, risk detection.
All analysis is based on real article content only — no fabrication.
"""
import re
import logging
from typing import List, Dict, Tuple
from app.ml.domain_classifier import classify_domain
from app.ml.training_data import DOMAIN_KEYWORDS, RISK_KEYWORDS, INNOVATION_KEYWORDS, DOMAIN_COLORS

logger = logging.getLogger(__name__)


def analyze_sentiment(title: str, content: str) -> Tuple[str, float]:
    """Lexical sentiment analysis with title weighting."""
    POSITIVE = [
        "growth", "profit", "record", "beat", "exceed", "strong", "surge", "rise",
        "gain", "rally", "outperform", "breakthrough", "launch", "partnership",
        "innovative", "expansion", "success", "positive", "upgrade", "milestone",
        "award", "leading", "best", "top", "win", "deal", "revenue up", "raised",
        "record high", "record revenue", "beats", "soars", "climbs", "jumps",
    ]
    NEGATIVE = [
        "loss", "decline", "miss", "fall", "drop", "fail", "cut", "risk", "warn",
        "concern", "problem", "issue", "lawsuit", "fine", "layoff", "bankruptcy",
        "downgrade", "investigation", "allegation", "breach", "hack", "scandal",
        "recall", "delay", "shortage", "crash", "fraud", "penalty", "worse",
        "plunges", "tumbles", "slides", "slumps", "disappoints",
    ]

    title_l = title.lower()
    content_l = content.lower()

    pos = sum(3 if w in title_l else 1 for w in POSITIVE if w in title_l or w in content_l[:600])
    neg = sum(3 if w in title_l else 1 for w in NEGATIVE if w in title_l or w in content_l[:600])

    total = pos + neg
    if total == 0:
        return "neutral", 0.5
    ratio = pos / total
    if ratio > 0.58:
        return "positive", round(min(0.95, ratio), 2)
    elif ratio < 0.42:
        return "negative", round(min(0.95, 1 - ratio), 2)
    return "neutral", 0.5


def detect_risk_flags(articles: List[Dict]) -> List[Dict]:
    """Detect risk flags from real article content."""
    flags = []
    seen = set()

    for article in articles:
        text = (article.get("title", "") + " " + article.get("summary", "")).lower()
        for severity, categories in RISK_KEYWORDS.items():
            for category, keywords in categories.items():
                for kw in keywords:
                    if kw in text and kw not in seen:
                        seen.add(kw)
                        desc = _extract_context(article.get("title", ""), article.get("summary", ""), kw)
                        flags.append({
                            "id": f"risk_{len(flags)}",
                            "severity": severity,
                            "category": category,
                            "description": desc,
                            "keywordMatched": kw,
                        })

    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    return sorted(flags, key=lambda x: order.get(x["severity"], 3))


def _extract_context(title: str, summary: str, keyword: str) -> str:
    """Extract the sentence containing the keyword as context."""
    text = title + ". " + summary
    sentences = re.split(r'[.!?]+', text)
    for sent in sentences:
        if keyword in sent.lower():
            s = sent.strip()
            if len(s) > 10:
                return s[:200].capitalize()
    return title[:200]


def detect_innovation_signals(articles: List[Dict]) -> int:
    """Count innovation signal mentions across articles."""
    count = 0
    for article in articles:
        text = (article.get("title", "") + " " + article.get("summary", "")).lower()
        count += sum(1 for kw in INNOVATION_KEYWORDS if kw in text)
    return count


def compute_domain_distribution(articles: List[Dict]) -> List[Dict]:
    """Compute domain distribution from classified articles."""
    counts: Dict[str, int] = {}
    for a in articles:
        d = a.get("domain", "Market")
        counts[d] = counts.get(d, 0) + 1

    total = max(sum(counts.values()), 1)
    return sorted([
        {
            "domain": domain,
            "count": count,
            "percentage": round(count / total * 100, 1),
            "color": DOMAIN_COLORS.get(domain, "#9ca3af"),
        }
        for domain, count in counts.items()
    ], key=lambda x: x["count"], reverse=True)


def compute_scores(articles: List[Dict], risk_flags: List[Dict], innovation_count: int) -> Dict:
    """Compute aggregate scores derived from real article data."""
    if not articles:
        return {"sentimentScore": 50, "velocityScore": 0, "relevanceScore": 0}

    sent_map = {"positive": 1, "neutral": 0, "negative": -1}
    raw_sent = sum(sent_map.get(a.get("sentiment", "neutral"), 0) for a in articles)
    sentiment_score = round((raw_sent / len(articles) + 1) / 2 * 100)

    velocity_score = min(100, round(len(articles) * 10))

    avg_conf = sum(a.get("confidenceScore", 50) for a in articles) / len(articles)
    relevance_score = round(avg_conf)

    return {
        "sentimentScore": max(0, min(100, sentiment_score)),
        "velocityScore": velocity_score,
        "relevanceScore": max(0, min(100, relevance_score)),
    }


def extract_key_themes(articles: List[Dict]) -> List[str]:
    """Extract key themes from article tags and domains."""
    tag_freq: Dict[str, int] = {}
    for a in articles:
        for tag in a.get("tags", []):
            t = tag.lower().strip()
            if t and len(t) > 2:
                tag_freq[t] = tag_freq.get(t, 0) + 1
    # Remove the company name itself (always first tag) from themes
    sorted_tags = [t for t, _ in sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)]
    return sorted_tags[:8]


def extract_risk_factors(risk_flags: List[Dict]) -> List[str]:
    """Extract unique risk categories from flags."""
    seen = set()
    result = []
    for f in risk_flags:
        cat = f.get("category", "")
        if cat and cat not in seen:
            seen.add(cat)
            result.append(cat)
    return result[:5]


def extract_opportunities(articles: List[Dict]) -> List[str]:
    """Extract positive themes as opportunities from real article content."""
    OPP_KEYWORDS = {
        "AI/ML investment": ["ai", "machine learning", "artificial intelligence", "generative"],
        "New market entry": ["expansion", "new market", "enter", "international", "global expansion"],
        "Product innovation": ["launch", "new product", "innovation", "release", "breakthrough"],
        "Strategic partnerships": ["partnership", "collaboration", "alliance", "joint venture"],
        "Revenue growth": ["revenue growth", "revenue up", "record revenue", "beats estimates"],
        "Cost efficiency": ["cost reduction", "efficiency", "optimization", "margin improvement"],
        "Funding secured": ["funding raised", "series", "investment round", "capital raised"],
    }
    found = []
    for opp, kws in OPP_KEYWORDS.items():
        for a in articles:
            text = (a.get("title", "") + " " + a.get("summary", "")).lower()
            if any(kw in text for kw in kws) and a.get("sentiment") != "negative":
                found.append(opp)
                break
    return found[:5]
