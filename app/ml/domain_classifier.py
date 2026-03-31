"""
Domain classifier: keyword-based with optional sklearn ML fallback.
Works without sklearn installed — pure keyword matching is robust enough.
"""
from __future__ import annotations
import re
import logging
from typing import Tuple

from app.ml.training_data import DOMAIN_KEYWORDS

log = logging.getLogger(__name__)


def classify_domain(title: str, content: str) -> Tuple[str, float]:
    """
    Keyword-based domain classification with confidence score.
    Title keywords count double (stronger signal).
    """
    text_full = (title + " " + content).lower()
    text_title = title.lower()
    scores: dict = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in text_title:
                score += 3  # title match = strong signal
            elif kw in text_full:
                score += 1
        if score > 0:
            scores[domain] = score

    if not scores:
        return "Market", 0.4

    best = max(scores, key=scores.get)
    total = sum(scores.values())
    confidence = min(0.95, scores[best] / max(total, 1) * 2.5)
    return best, round(confidence, 2)


# Optional: try to use sklearn ML classifier if available
_ml_classifier = None
_ml_tried = False


def _try_load_ml_classifier():
    """Attempt to load/train sklearn classifier. Returns None if unavailable."""
    global _ml_classifier, _ml_tried
    if _ml_tried:
        return _ml_classifier
    _ml_tried = True
    try:
        from pathlib import Path
        from app.ml.training_data import get_training_texts, get_training_labels
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline

        texts = get_training_texts()
        labels = get_training_labels()

        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000, sublinear_tf=True)),
            ("clf", LogisticRegression(C=2.0, max_iter=300, solver="lbfgs", class_weight="balanced", random_state=42)),
        ])
        pipeline.fit(texts, labels)
        _ml_classifier = pipeline
        log.info("ML domain classifier trained successfully")
    except Exception as e:
        log.info(f"sklearn not available, using keyword classifier: {e}")
        _ml_classifier = None
    return _ml_classifier
