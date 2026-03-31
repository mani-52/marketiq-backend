"""Unit tests for domain classifier."""

import pytest
from pathlib import Path
import tempfile

from app.ml.domain_classifier import DomainClassifier


@pytest.fixture(scope="module")
def classifier(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("models")
    clf = DomainClassifier(model_dir=tmp)
    clf.load_or_train()
    return clf


def test_classifier_loads(classifier):
    assert classifier.is_loaded


def test_predict_returns_tuple(classifier):
    label, conf = classifier.predict("Apple reports record quarterly revenue earnings")
    assert isinstance(label, str)
    assert isinstance(conf, float)
    assert 0.0 <= conf <= 1.0


def test_predict_finance(classifier):
    label, conf = classifier.predict(
        "quarterly earnings beat analyst expectations revenue profit margin"
    )
    assert label == "Finance"
    assert conf > 0.5


def test_predict_legal(classifier):
    label, conf = classifier.predict(
        "lawsuit filed court ruling litigation antitrust investigation"
    )
    assert label == "Legal"


def test_predict_ai(classifier):
    label, conf = classifier.predict(
        "artificial intelligence generative AI large language model GPT transformer"
    )
    assert label == "AI"


def test_predict_cybersecurity(classifier):
    label, conf = classifier.predict(
        "cybersecurity breach hack ransomware malware security incident"
    )
    assert label == "Cybersecurity"


def test_predict_batch(classifier):
    texts = [
        "quarterly revenue earnings profit",
        "product launch new feature release",
        "lawsuit antitrust court ruling",
    ]
    results = classifier.predict_batch(texts)
    assert len(results) == 3
    for label, conf in results:
        assert isinstance(label, str)
        assert 0.0 <= conf <= 1.0


def test_get_top_domains(classifier):
    top = classifier.get_top_domains("AI machine learning startup funding")
    assert isinstance(top, list)
    assert len(top) >= 1
    assert "domain" in top[0]
    assert "confidence" in top[0]


def test_predict_empty_string(classifier):
    label, conf = classifier.predict("")
    assert isinstance(label, str)


def test_classifier_persists(tmp_path):
    """Test save → load cycle."""
    clf1 = DomainClassifier(model_dir=tmp_path)
    clf1.load_or_train()
    assert clf1.is_loaded

    clf2 = DomainClassifier(model_dir=tmp_path)
    clf2.load_or_train()
    assert clf2.is_loaded

    label1, conf1 = clf1.predict("quarterly earnings revenue growth profit")
    label2, conf2 = clf2.predict("quarterly earnings revenue growth profit")
    assert label1 == label2
