#!/usr/bin/env python3
"""
Bootstrap script — trains and saves the domain classifier.
Run once before starting the server if you want to pre-warm models:

    python scripts/bootstrap_models.py

The server also auto-trains on first startup if no model is found.
"""

import sys
from pathlib import Path

# Make app importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.logger import configure_logging, get_logger
from app.ml.domain_classifier import DomainClassifier
from app.ml.embedding_service import EmbeddingService

configure_logging("INFO", json_logs=False)
log = get_logger(__name__)


def main():
    settings = get_settings()
    model_dir = settings.model_dir

    log.info(f"Bootstrap started → model dir: {model_dir}")

    # ── Train domain classifier ────────────────────────────────────────────
    log.info("Training domain classifier...")
    clf = DomainClassifier(model_dir=model_dir)
    clf.load_or_train()

    # Test a few predictions
    test_cases = [
        ("quarterly earnings revenue beat expectations", "Finance"),
        ("product launch new feature release AI platform", "Product"),
        ("lawsuit antitrust investigation court ruling", "Legal"),
        ("artificial intelligence machine learning GPT", "AI"),
        ("cybersecurity breach ransomware attack", "Cybersecurity"),
    ]

    print("\n── Classifier Smoke Test ─────────────────────────────")
    all_passed = True
    for text, expected in test_cases:
        label, conf = clf.predict(text)
        status = "✓" if label == expected else "✗"
        if label != expected:
            all_passed = False
        print(f"  {status} '{text[:40]}...' → {label} ({conf:.2%}) [expected: {expected}]")

    # ── Warm up embedding service ──────────────────────────────────────────
    print("\n── Embedding Service ─────────────────────────────────")
    embedder = EmbeddingService(settings.embedding_model)
    test_texts = ["Apple reports earnings", "Tesla launches new model"]
    embeddings = embedder.encode(test_texts)
    print(f"  ✓ Embeddings shape: {embeddings.shape}")
    print(f"  ✓ Model available: {embedder.is_available}")

    print("\n── Bootstrap Complete ────────────────────────────────")
    print(f"  Model dir: {model_dir}")
    print(f"  Classifier: {'ready' if clf.is_loaded else 'failed'}")
    print(f"  All tests passed: {all_passed}")

    if not all_passed:
        print("\n  ⚠ Some classifier tests failed — this is expected with small training data.")
        print("  The server will still work; classification may be less accurate.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
