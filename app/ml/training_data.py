"""Domain keywords, risk/innovation signals, and training data for ML classifier."""
from typing import List

DOMAIN_KEYWORDS = {
    "Finance": [
        "revenue", "earnings", "profit", "loss", "ebitda", "ipo", "stock", "shares",
        "valuation", "funding", "investment", "quarterly", "fiscal", "dividend",
        "cash flow", "debt", "bond", "financial results", "annual report", "margin",
        "forecast", "guidance", "analyst", "raise", "round", "series a", "series b",
    ],
    "Product": [
        "launch", "product", "feature", "update", "release", "version", "software",
        "app", "platform", "service", "tool", "sdk", "api", "beta", "upgrade",
        "new model", "hardware", "introduce", "unveil", "announce product",
    ],
    "Partnerships": [
        "partnership", "collaboration", "deal", "agreement", "alliance",
        "joint venture", "signed", "partner", "contract", "integration", "supplier",
        "vendor", "client", "strategic", "memorandum", "mou", "cooperate",
    ],
    "Legal": [
        "lawsuit", "litigation", "settlement", "court", "judge", "complaint",
        "fine", "penalty", "antitrust", "investigation", "probe", "sec", "ftc",
        "doj", "injunction", "verdict", "class action", "regulator", "compliance",
        "violation", "charged", "indicted",
    ],
    "Leadership": [
        "ceo", "cto", "cfo", "coo", "executive", "appointed", "resigned",
        "stepping down", "board", "director", "management", "leadership", "hire",
        "fired", "departure", "president", "chairman", "founder", "co-founder",
    ],
    "Technology": [
        "ai", "machine learning", "neural", "algorithm", "model", "deep learning",
        "llm", "gpu", "chip", "semiconductor", "cloud", "data center",
        "infrastructure", "patent", "research", "r&d", "innovation", "technology",
        "automation", "robotics", "quantum", "generative", "transformer",
    ],
    "Market": [
        "market share", "competitor", "competition", "industry", "sector", "growth",
        "expansion", "customer", "consumer", "demand", "supply", "price", "cost",
        "inflation", "recession", "market cap", "index", "benchmark", "economy",
        "trend", "forecast", "outlook",
    ],
    "ESG": [
        "sustainability", "carbon", "emissions", "climate", "environment", "esg",
        "diversity", "inclusion", "governance", "social", "green", "renewable",
        "net zero", "workforce", "safety", "community", "corporate responsibility",
        "scope 1", "scope 2",
    ],
    "M&A": [
        "acquisition", "merger", "acquired", "takeover", "buyout", "bid", "offer",
        "target", "stake", "purchase", "sell", "divest", "spin-off", "ipo",
        "strategic acquisition", "acquire",
    ],
}

RISK_KEYWORDS = {
    "HIGH": {
        "Legal/Regulatory": [
            "lawsuit filed", "criminal charges", "sec enforcement", "doj investigation",
            "fined", "fraud allegation", "class action", "antitrust violation", "arrested",
        ],
        "Financial": [
            "bankruptcy", "insolvency", "default", "debt crisis", "credit downgrade",
            "massive loss", "write-down", "revenue miss", "profit warning",
        ],
        "Reputational": [
            "scandal", "controversy", "backlash", "boycott", "data breach", "hack",
            "cybersecurity incident", "privacy violation",
        ],
    },
    "MEDIUM": {
        "Operational": [
            "supply chain disruption", "manufacturing halt", "recall", "outage",
            "delay", "shortage", "strike", "layoffs", "restructuring",
        ],
        "Financial": [
            "guidance cut", "earnings miss", "margin compression", "cost overrun",
            "slower growth", "valuation concerns",
        ],
        "Regulatory": [
            "under review", "investigation opened", "regulatory scrutiny", "subpoena",
            "compliance issue", "audit",
        ],
    },
    "LOW": {
        "Competitive": [
            "market share loss", "competition intensifying", "new entrant", "price war",
        ],
        "Leadership": [
            "executive departure", "management change", "board shake-up",
        ],
        "Macro": [
            "economic headwinds", "currency impact", "interest rate risk", "geopolitical",
        ],
    },
}

INNOVATION_KEYWORDS = [
    "breakthrough", "launch", "new product", "first", "pioneering", "revolutionary",
    "disruptive", "patent", "r&d", "research", "ai model", "new platform",
    "world's first", "industry first", "cutting edge", "next generation",
    "innovation", "prototype", "demo", "unveil",
]

# ── Domain Classification Matrix ─────────────────────────────────────────────
# A structured matrix that maps domains to their coverage dimensions,
# enabling cross-domain comparison and market positioning analysis.

DOMAIN_CLASSIFICATION_MATRIX = {
    "domains": list(DOMAIN_KEYWORDS.keys()),
    "dimensions": {
        "risk_weight": {
            "Finance": 0.90,
            "Legal": 0.95,
            "Technology": 0.60,
            "Market": 0.65,
            "Product": 0.50,
            "Partnerships": 0.45,
            "Leadership": 0.55,
            "ESG": 0.40,
            "M&A": 0.75,
        },
        "innovation_weight": {
            "Finance": 0.30,
            "Legal": 0.10,
            "Technology": 0.95,
            "Market": 0.55,
            "Product": 0.90,
            "Partnerships": 0.60,
            "Leadership": 0.35,
            "ESG": 0.50,
            "M&A": 0.40,
        },
        "volatility_weight": {
            "Finance": 0.85,
            "Legal": 0.80,
            "Technology": 0.70,
            "Market": 0.75,
            "Product": 0.50,
            "Partnerships": 0.40,
            "Leadership": 0.65,
            "ESG": 0.35,
            "M&A": 0.90,
        },
        "growth_signal": {
            "Finance": 0.75,
            "Legal": 0.20,
            "Technology": 0.85,
            "Market": 0.80,
            "Product": 0.85,
            "Partnerships": 0.70,
            "Leadership": 0.50,
            "ESG": 0.60,
            "M&A": 0.80,
        },
        "sentiment_bias": {
            # Typical baseline sentiment polarity for each domain (-1 to 1)
            "Finance": 0.10,
            "Legal": -0.40,
            "Technology": 0.30,
            "Market": 0.05,
            "Product": 0.35,
            "Partnerships": 0.40,
            "Leadership": -0.10,
            "ESG": 0.15,
            "M&A": 0.20,
        },
    },
    "color_map": {
        "Finance": "#10b981",
        "Legal": "#ef4444",
        "Technology": "#6366f1",
        "Market": "#f59e0b",
        "Product": "#3b82f6",
        "Partnerships": "#8b5cf6",
        "Leadership": "#ec4899",
        "ESG": "#14b8a6",
        "M&A": "#f97316",
    },
    "description": {
        "Finance": "Revenue, earnings, funding, stock performance and fiscal results",
        "Legal": "Lawsuits, regulatory investigations, compliance and court actions",
        "Technology": "AI, R&D, patents, cloud, chips and infrastructure developments",
        "Market": "Market share, competition, consumer demand and macroeconomic trends",
        "Product": "Product launches, feature updates, software and hardware releases",
        "Partnerships": "Strategic deals, alliances, contracts and joint ventures",
        "Leadership": "Executive changes, board decisions and management appointments",
        "ESG": "Sustainability, climate, diversity, governance and social responsibility",
        "M&A": "Mergers, acquisitions, divestitures and strategic buyouts",
    },
}

DOMAIN_COLORS = DOMAIN_CLASSIFICATION_MATRIX["color_map"]


def get_domain_matrix() -> dict:
    """Return the full domain classification matrix."""
    return DOMAIN_CLASSIFICATION_MATRIX


# ── Training data helpers ─────────────────────────────────────────────────────

def get_training_texts() -> List[str]:
    texts = []
    for domain, kws in DOMAIN_KEYWORDS.items():
        for kw in kws:
            texts.append(f"{kw} {kw} company {domain.lower()} news report")
    return texts


def get_training_labels() -> List[str]:
    labels = []
    for domain, kws in DOMAIN_KEYWORDS.items():
        for _ in kws:
            labels.append(domain)
    return labels
