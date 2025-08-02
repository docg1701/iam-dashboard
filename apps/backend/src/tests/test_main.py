"""
Tests for the main FastAPI application.

This module tests the core application functionality including
health checks and basic endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


def test_health_endpoint(client: TestClient):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Multi-Agent IAM Dashboard"
    assert data["version"] == "1.0.0"
    assert "environment" in data


def test_api_root(client: TestClient):
    """Test the API root endpoint."""
    response = client.get("/api/v1/")
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Multi-Agent IAM Dashboard API v1"
    assert data["version"] == "1.0.0"
    assert data["docs_url"] == "/api/docs"


def test_api_status(client: TestClient):
    """Test the API status endpoint."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "operational"
    assert data["api_version"] == "v1"


def test_not_found_endpoint(client: TestClient):
    """Test 404 handler."""
    response = client.get("/non-existent-endpoint")
    assert response.status_code == 404

    data = response.json()
    assert data["detail"] == "Resource not found"


@pytest.mark.asyncio
async def test_application_startup():
    """Test that the application starts up correctly."""
    # This test ensures the application can be imported and initialized
    assert app is not None
    assert app.title == "Multi-Agent IAM Dashboard"
