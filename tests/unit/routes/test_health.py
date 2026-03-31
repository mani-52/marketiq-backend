"""Tests for /health endpoint."""

import pytest


def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data
    assert "services" in data


def test_health_services_present(client):
    resp = client.get("/health")
    services = resp.json()["services"]
    assert "api" in services
    assert services["api"] == "ok"


def test_health_ml_fields(client):
    data = client.get("/health").json()
    assert "ml_models_loaded" in data
    assert "tavily_configured" in data
    assert isinstance(data["ml_models_loaded"], bool)


def test_health_response_schema(client):
    data = client.get("/health").json()
    required = {"status", "app", "version", "environment", "timestamp", "services"}
    assert required.issubset(set(data.keys()))
