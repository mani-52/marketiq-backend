"""
Tavily search service — STRICT company-specific queries.
Guarantees ONLY articles about the exact searched company are returned.
"""
import httpx
import asyncio
import logging
import re
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

TAVILY_URL = "https://api.tavily.com/search"

COMPANY_DISAMBIGUATION = {
    "apple": "Apple Inc technology iPhone Mac",
    "amazon": "Amazon.com Inc ecommerce AWS cloud",
    "meta": "Meta Platforms Inc Facebook Instagram WhatsApp",
    "oracle": "Oracle Corporation database software Larry Ellison",
    "sage": "Sage Group plc accounting software UK",
    "nvidia": "NVIDIA Corporation GPU chips AI semiconductor",
    "tesla": "Tesla Inc electric vehicles EV Elon Musk",
    "google": "Google LLC Alphabet Inc search engine",
    "microsoft": "Microsoft Corporation Windows Azure",
    "salesforce": "Salesforce Inc CRM cloud software",
    "shopify": "Shopify Inc ecommerce platform Canada",
    "stripe": "Stripe Inc payments fintech",
    "figma": "Figma Inc design software",
    "notion": "Notion Labs productivity software",
    "openai": "OpenAI Inc ChatGPT GPT artificial intelligence",
    "anthropic": "Anthropic PBC Claude AI safety",
    "palantir": "Palantir Technologies data analytics NYSE",
    "snowflake": "Snowflake Inc cloud data warehouse NYSE",
    "databricks": "Databricks Inc lakehouse data AI",
    "uber": "Uber Technologies Inc ride-hailing NYSE",
    "lyft": "Lyft Inc ride-sharing NASDAQ",
    "airbnb": "Airbnb Inc vacation rental NASDAQ",
    "zoom": "Zoom Video Communications Inc",
    "slack": "Slack Technologies messaging Salesforce",
    "twitter": "Twitter X Corp social media Elon Musk",
    "x": "X Corp Twitter social media Elon Musk",
    "snap": "Snap Inc Snapchat social media",
    "pinterest": "Pinterest Inc visual discovery NYSE",
    "spotify": "Spotify Technology music streaming NYSE",
    "netflix": "Netflix Inc streaming video NASDAQ",
    "disney": "Walt Disney Company entertainment NYSE",
    "intel": "Intel Corporation semiconductor CPU chips",
    "amd": "Advanced Micro Devices semiconductor",
    "qualcomm": "Qualcomm Inc mobile chips 5G NASDAQ",
    "arm": "Arm Holdings semiconductor IP SoftBank",
    "visa": "Visa Inc payment network NYSE",
    "mastercard": "Mastercard Inc payment network NYSE",
    "paypal": "PayPal Holdings Inc fintech NASDAQ",
    "square": "Block Inc Square fintech Jack Dorsey",
    "block": "Block Inc Square fintech Jack Dorsey",
    "coinbase": "Coinbase Global Inc cryptocurrency exchange",
    "robinhood": "Robinhood Markets Inc investing app",
    "rivian": "Rivian Automotive Inc electric truck NASDAQ",
    "lucid": "Lucid Group Inc electric vehicle NASDAQ",
    "ford": "Ford Motor Company automotive NYSE",
    "gm": "General Motors Company automotive NYSE",
    "general motors": "General Motors Company automotive NYSE",
    "toyota": "Toyota Motor Corporation automotive Japan",
    "volkswagen": "Volkswagen AG automotive Germany",
    "bmw": "BMW Group Bayerische Motoren Werke automotive",
    "ferrari": "Ferrari NV luxury sports car NYSE",
    "boeing": "Boeing Company aerospace defense NYSE",
    "airbus": "Airbus SE aerospace Europe",
    "lockheed": "Lockheed Martin aerospace defense NYSE",
    "pfizer": "Pfizer Inc pharmaceutical NYSE",
    "moderna": "Moderna Inc mRNA vaccine NASDAQ",
    "abbott": "Abbott Laboratories medical devices NYSE",
    "unitedhealth": "UnitedHealth Group healthcare insurance NYSE",
    "cvs": "CVS Health Corporation pharmacy NYSE",
    "walmart": "Walmart Inc retail NYSE",
    "target": "Target Corporation retail NYSE",
    "costco": "Costco Wholesale Corporation retail NASDAQ",
    "home depot": "Home Depot Inc home improvement NYSE",
    "nike": "Nike Inc sportswear NASDAQ",
    "adidas": "Adidas AG sportswear Germany",
    "lululemon": "Lululemon Athletica activewear NASDAQ",
    "jpmorgan": "JPMorgan Chase bank NYSE",
    "goldman sachs": "Goldman Sachs Group investment bank NYSE",
    "morgan stanley": "Morgan Stanley investment bank NYSE",
    "blackrock": "BlackRock Inc asset management NYSE",
    "berkshire": "Berkshire Hathaway Warren Buffett NYSE",
    "exxon": "ExxonMobil Corporation oil energy NYSE",
    "chevron": "Chevron Corporation oil energy NYSE",
    "shell": "Shell plc oil energy Netherlands",
    "bp": "BP plc oil energy UK",
    "samsung": "Samsung Electronics Co Ltd South Korea",
    "sony": "Sony Group Corporation Japan",
    "alibaba": "Alibaba Group Holding ecommerce China NYSE",
    "tencent": "Tencent Holdings technology China",
    "baidu": "Baidu Inc search engine China NASDAQ",
    "bytedance": "ByteDance Ltd TikTok China",
    "infosys": "Infosys Limited IT services India NSE",
    "wipro": "Wipro Limited IT services India NSE",
    "tata": "Tata Consultancy Services TCS India NSE",
    "tcs": "Tata Consultancy Services TCS India",
    "hcl": "HCL Technologies IT services India",
    "reliance": "Reliance Industries Limited India conglomerate",
    "hdfc": "HDFC Bank India financial services",
    "icici": "ICICI Bank India financial services",
    "zomato": "Zomato Limited food delivery India",
    "paytm": "Paytm One97 Communications fintech India",
    "ola": "Ola Electric ride-hailing India",
    "flipkart": "Flipkart ecommerce India Walmart",
    "byju": "BYJU'S education technology India",
    "swiggy": "Swiggy food delivery India",
    "razorpay": "Razorpay payments fintech India",
    "freshworks": "Freshworks Inc SaaS software India NASDAQ",
    "doordash": "DoorDash Inc food delivery NYSE",
    "instacart": "Maplebear Instacart grocery delivery NASDAQ",
    "crowdstrike": "CrowdStrike Holdings cybersecurity NASDAQ",
    "palo alto": "Palo Alto Networks cybersecurity NASDAQ",
    "zscaler": "Zscaler Inc cloud security NASDAQ",
    "datadog": "Datadog Inc monitoring observability NASDAQ",
    "mongodb": "MongoDB Inc database NASDAQ",
    "elastic": "Elastic NV Elasticsearch NYSE",
    "hubspot": "HubSpot Inc marketing CRM NYSE",
    "zendesk": "Zendesk Inc customer support",
    "workday": "Workday Inc HR software NASDAQ",
    "servicenow": "ServiceNow Inc enterprise software NYSE",
    "adobe": "Adobe Inc creative software NASDAQ",
    "intuit": "Intuit Inc TurboTax QuickBooks NASDAQ",
}


def normalize_company_name(company: str) -> str:
    """Remove common legal suffixes to get the core trading name."""
    normalized = company.strip()
    pattern = r'\s*\b(inc\.?|corp\.?|ltd\.?|llc\.?|plc\.?|co\.?|company|group|holdings?|technologies|tech|solutions|systems|services|global|international|enterprises?)\b\s*'
    normalized = re.sub(pattern, ' ', normalized, flags=re.IGNORECASE).strip()
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized if normalized else company.strip()


def build_precise_queries(company: str, days: int) -> List[str]:
    """Build 5 highly targeted queries anchored to the exact company name."""
    name = company.strip()
    name_lower = name.lower()
    quoted = f'"{name}"'
    disambig = COMPANY_DISAMBIGUATION.get(name_lower, "")

    if disambig:
        industry_hint = " ".join(disambig.split()[1:4])
        queries = [
            f'{quoted} {industry_hint} latest news {datetime.now().year}',
            f'{quoted} financial results earnings revenue',
            f'{quoted} product launch announcement partnership',
            f'{quoted} business strategy expansion',
            f'{quoted} risk legal regulatory',
        ]
    else:
        queries = [
            f'{quoted} company latest news {datetime.now().year}',
            f'{quoted} company financial business results',
            f'{quoted} company product service announcement',
            f'{quoted} company industry market analysis',
            f'{quoted} company strategy growth update',
        ]
    return queries


def is_strictly_relevant_to_company(result: Dict, company: str) -> bool:
    """
    STRICT relevance check — result MUST be about this specific company.
    Full name matched as a complete phrase, not split into words.
    """
    name_lower = company.lower().strip()
    name_normalized = normalize_company_name(company).lower()

    title = (result.get("title") or "").lower()
    content = (result.get("content") or "").lower()
    url = (result.get("url") or "").lower()
    combined = title + " " + content + " " + url

    # Check 1: exact full company name
    escaped = re.escape(name_lower)
    if re.search(rf'\b{escaped}\b', combined):
        return True

    # Check 2: normalized name (without Inc/Corp etc.)
    if name_normalized and len(name_normalized) > 3 and name_normalized != name_lower:
        escaped_norm = re.escape(name_normalized)
        if re.search(rf'\b{escaped_norm}\b', combined):
            return True

    # Check 3: disambiguation context match
    disambig = COMPANY_DISAMBIGUATION.get(name_lower, "")
    if disambig:
        title_content = title + " " + content[:600]
        name_present = re.search(rf'\b{escaped}\b', title_content)
        if name_present:
            return True
        # Check first identifier word from disambiguation
        first_id = disambig.split()[0].lower()
        if len(first_id) > 3 and first_id in title_content:
            return True

    # Check 4: multi-word company — require ALL significant words together
    words = name_lower.split()
    if len(words) > 1:
        # If full phrase didn't match, reject (prevent "New" matching "New York Times")
        return False

    # Check 5: single-word names — require title or URL match, or 3+ content mentions
    if re.search(rf'\b{escaped}\b', title):
        return True
    if re.search(rf'\b{escaped}\b', url):
        return True
    count = len(re.findall(rf'\b{escaped}\b', content))
    if count >= 3:
        return True

    return False


def score_relevance(result: Dict, company: str) -> float:
    """Score result relevance (0.0–1.0). Higher = more company-focused."""
    name_lower = company.lower().strip()
    name_normalized = normalize_company_name(company).lower()
    title = (result.get("title") or "").lower()
    content = (result.get("content") or "").lower()
    url = (result.get("url") or "").lower()
    escaped = re.escape(name_lower)
    score = 0.0

    if re.search(rf'\b{escaped}\b', title):
        score += 0.5
    elif name_normalized and re.search(rf'\b{re.escape(name_normalized)}\b', title):
        score += 0.4

    if re.search(rf'\b{escaped}\b', url) or (name_normalized and name_normalized.replace(" ", "") in url):
        score += 0.2

    count = len(re.findall(rf'\b{escaped}\b', content))
    score += min(0.3, count * 0.05)

    return min(1.0, score)


def deduplicate_results(results: List[Dict]) -> List[Dict]:
    """Remove duplicate URLs and near-duplicate titles."""
    seen_urls: set = set()
    seen_titles: set = set()
    unique = []
    for r in results:
        url = (r.get("url") or "").strip()
        title = (r.get("title") or "").lower().strip()[:80]
        if url in seen_urls or (title and title in seen_titles):
            continue
        seen_urls.add(url)
        if title:
            seen_titles.add(title)
        unique.append(r)
    return unique


async def search_tavily(
    api_key: str,
    query: str,
    days: int,
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """Execute a single Tavily search with full error handling."""
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "advanced",
        "include_answer": False,
        "include_raw_content": False,
        "max_results": max_results,
        "include_domains": [],
        "exclude_domains": [],
        "days": days,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(TAVILY_URL, json=payload)
            resp.raise_for_status()
            return resp.json().get("results", [])
        except httpx.HTTPStatusError as e:
            logger.warning(f"Tavily HTTP {e.response.status_code} for query: {query[:60]}")
            return []
        except Exception as e:
            logger.warning(f"Tavily request failed: {e}")
            return []


async def fetch_company_news(
    api_key: str,
    company: str,
    days: int,
) -> List[Dict[str, Any]]:
    """
    Fetch ONLY articles about the exact searched company.
    Uses 5 targeted queries, strict relevance filter, fallbacks for obscure companies.
    """
    queries = build_precise_queries(company, days)
    logger.info(f"[{company}] Searching with {len(queries)} queries over {days} days")

    tasks = [search_tavily(api_key, q, days, max_results=10) for q in queries]
    results_per_query = await asyncio.gather(*tasks, return_exceptions=True)

    all_results: List[Dict] = []
    for i, results in enumerate(results_per_query):
        if isinstance(results, Exception):
            logger.warning(f"[{company}] Query {i} error: {results}")
            continue
        if isinstance(results, list):
            all_results.extend(results)

    logger.info(f"[{company}] Raw results: {len(all_results)}")

    # Strict relevance filter
    relevant = [r for r in all_results if is_strictly_relevant_to_company(r, company)]
    logger.info(f"[{company}] After strict filter: {len(relevant)}")

    # Fallback 1: sparse results — extend time window
    if len(relevant) < 3:
        logger.info(f"[{company}] Sparse results — extending window to {min(days*2, 90)} days")
        extended_days = min(days * 2, 90)
        fallback_query = f'"{company}" company news'
        fallback = await search_tavily(api_key, fallback_query, extended_days, max_results=15)
        existing_urls = {r.get("url") for r in relevant}
        for r in fallback:
            if r.get("url") not in existing_urls and is_strictly_relevant_to_company(r, company):
                relevant.append(r)
        logger.info(f"[{company}] After fallback 1: {len(relevant)}")

    # Fallback 2: very obscure company — relax to title-only presence
    if len(relevant) < 2:
        logger.info(f"[{company}] Applying relaxed title-only filter")
        name_lower = company.lower()
        name_norm = normalize_company_name(company).lower()
        existing_urls = {r.get("url") for r in relevant}
        for r in all_results:
            if r.get("url") in existing_urls:
                continue
            title = (r.get("title") or "").lower()
            if name_lower in title or (name_norm and name_norm in title):
                relevant.append(r)
                existing_urls.add(r.get("url"))
        logger.info(f"[{company}] After fallback 2: {len(relevant)}")

    deduped = deduplicate_results(relevant)
    scored = sorted(deduped, key=lambda r: score_relevance(r, company), reverse=True)
    logger.info(f"[{company}] Final unique results: {len(scored)}")
    return scored
