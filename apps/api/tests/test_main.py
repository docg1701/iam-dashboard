"""
Test main application functionality.
"""

import pytest
from fastapi.testclient import TestClient


class TestMainApplication:
    """Test main application endpoints and configuration."""

    def test_health_check(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "iam-dashboard-api"

    def test_api_v1_health_check(self, client: TestClient):
        """Test the API v1 health check endpoint."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "v1"

    @pytest.mark.integration
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are properly configured."""
        response = client.options("/health")

        # Check that CORS headers are present
        assert "access-control-allow-origin" in response.headers

    def test_openapi_docs_in_debug(self, client: TestClient):
        """Test that OpenAPI docs are available in debug mode."""
        # Note: This test assumes DEBUG is True in test environment
        response = client.get("/api/v1/docs")

        # Should not return 404 in debug mode
        assert response.status_code != 404

    def test_request_id_header(self, client: TestClient):
        """Test that request ID header is added to responses."""
        response = client.get("/health")

        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    @pytest.mark.slow
    def test_application_startup(self, app):
        """Test application startup without errors."""
        # Test that the app can be created without exceptions
        assert app is not None
        assert hasattr(app, "routes")

        # Check that routes are properly configured
        route_paths = [route.path for route in app.routes if hasattr(route, "path")]
        expected_paths = ["/health", "/api/v1/health"]

        for path in expected_paths:
            assert any(path in route_path for route_path in route_paths)
