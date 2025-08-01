"""Tests for agent management API endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.agents import router as agents_router
from app.core.agent_manager import AgentMetadata, AgentStatus


class TestAgentsAPI:
    """Test agent management API endpoints."""

    @pytest.fixture
    def client(self):
        """Test client for API endpoints."""
        # Create a clean FastAPI app for testing without NiceGUI middleware
        test_app = FastAPI(title="Test IAM Dashboard API")
        test_app.include_router(agents_router)
        return TestClient(test_app)

    @pytest.fixture
    def mock_agent_metadata(self):
        """Mock agent metadata for testing."""
        return AgentMetadata(
            agent_id="test_agent",
            name="Test Agent",
            description="Test agent description",
            capabilities=["test_capability"],
            dependencies=["test_dependency"],
            status=AgentStatus.ACTIVE,
            health_status="healthy",
            last_health_check=datetime.now(UTC),
            error_message=None
        )

    @pytest.fixture
    def mock_agent_manager(self, mock_agent_metadata):
        """Mock agent manager for testing."""
        manager = MagicMock()
        manager.get_all_agents_metadata.return_value = {"test_agent": mock_agent_metadata}
        manager.get_agent_metadata.return_value = mock_agent_metadata
        manager.health_check = AsyncMock(return_value=True)
        manager.is_agent_active.return_value = True
        manager.get_agent.return_value = MagicMock()
        manager.enable_agent = AsyncMock(return_value=True)
        manager.disable_agent = AsyncMock(return_value=True)
        manager.unload_agent = AsyncMock(return_value=True)
        return manager

    def test_list_agents_success(self, client, mock_agent_manager):
        """Test successful agent listing."""
        with patch('app.api.agents.get_agent_manager', return_value=mock_agent_manager):
            response = client.get("/api/agents/")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["total_agents"] == 1
            assert "test_agent" in data["agents"]

    def test_list_agents_error(self, client):
        """Test agent listing with error."""
        with patch('app.api.agents.get_agent_manager', side_effect=Exception("Manager error")):
            response = client.get("/api/agents/")

            assert response.status_code == 500
            assert "Failed to list agents" in response.json()["detail"]

    def test_get_agents_status_success(self, client):
        """Test successful system status retrieval."""
        mock_status = {
            "system_healthy": True,
            "total_agents": 1,
            "active_agents": 1,
            "inactive_agents": 0,
            "error_agents": 0,
            "agents": {"test_agent": {"status": "active"}}
        }

        with patch('app.api.agents.get_system_status', return_value=mock_status):
            response = client.get("/api/agents/status")

            assert response.status_code == 200
            data = response.json()
            assert data["system_healthy"] is True
            assert data["total_agents"] == 1

    def test_get_agent_details_success(self, client, mock_agent_manager):
        """Test successful agent details retrieval."""
        with patch('app.api.agents.get_agent_manager', return_value=mock_agent_manager):
            response = client.get("/api/agents/test_agent")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["agent_id"] == "test_agent"
            assert data["name"] == "Test Agent"

    def test_get_agent_details_not_found(self, client, mock_agent_manager):
        """Test agent details retrieval for non-existent agent."""
        mock_agent_manager.get_agent_metadata.return_value = None

        with patch('app.api.agents.get_agent_manager', return_value=mock_agent_manager):
            response = client.get("/api/agents/nonexistent_agent")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_check_agent_health_success(self, client, mock_agent_manager):
        """Test successful agent health check."""
        with patch('app.api.agents.get_agent_manager', return_value=mock_agent_manager):
            response = client.get("/api/agents/test_agent/health")

            assert response.status_code == 200
            data = response.json()
            assert data["agent_id"] == "test_agent"
            assert data["status"] == "active"
            assert data["health_status"] == "healthy"

    def test_check_agent_health_not_found(self, client, mock_agent_manager):
        """Test health check for non-existent agent."""
        mock_agent_manager.get_agent_metadata.return_value = None

        with patch('app.api.agents.get_agent_manager', return_value=mock_agent_manager):
            response = client.get("/api/agents/nonexistent_agent/health")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_execute_agent_success(self, client, mock_agent_manager):
        """Test successful agent execution."""
        with patch('app.api.agents.get_agent_manager', return_value=mock_agent_manager):
            request_data = {"input_data": {"test": "data"}}
            response = client.post("/api/agents/test_agent/execute", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["agent_id"] == "test_agent"

    def test_execute_agent_inactive(self, client, mock_agent_manager):
        """Test agent execution when agent is inactive."""
        mock_agent_manager.is_agent_active.return_value = False

        with patch('app.api.agents.get_agent_manager', return_value=mock_agent_manager):
            request_data = {"input_data": {"test": "data"}}
            response = client.post("/api/agents/test_agent/execute", json=request_data)

            assert response.status_code == 400
            assert "not active" in response.json()["detail"]

    def test_execute_agent_not_found(self, client, mock_agent_manager):
        """Test agent execution when agent is not found."""
        mock_agent_manager.get_agent.return_value = None

        with patch('app.api.agents.get_agent_manager', return_value=mock_agent_manager):
            request_data = {"input_data": {"test": "data"}}
            response = client.post("/api/agents/test_agent/execute", json=request_data)

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_enable_agent_success(self, client, mock_agent_manager):
        """Test successful agent enabling."""
        with patch('app.api.agents.get_agent_manager', return_value=mock_agent_manager):
            response = client.post("/api/agents/test_agent/enable")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "enabled successfully" in data["message"]

    def test_enable_agent_failure(self, client, mock_agent_manager):
        """Test agent enabling failure."""
        mock_agent_manager.enable_agent.return_value = False

        with patch('app.api.agents.get_agent_manager', return_value=mock_agent_manager):
            response = client.post("/api/agents/test_agent/enable")

            assert response.status_code == 400
            assert "Failed to enable" in response.json()["detail"]

    def test_disable_agent_success(self, client, mock_agent_manager):
        """Test successful agent disabling."""
        with patch('app.api.agents.get_agent_manager', return_value=mock_agent_manager):
            response = client.post("/api/agents/test_agent/disable")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "disabled successfully" in data["message"]

    def test_disable_agent_failure(self, client, mock_agent_manager):
        """Test agent disabling failure."""
        mock_agent_manager.disable_agent.return_value = False

        with patch('app.api.agents.get_agent_manager', return_value=mock_agent_manager):
            response = client.post("/api/agents/test_agent/disable")

            assert response.status_code == 400
            assert "Failed to disable" in response.json()["detail"]

    def test_unload_agent_success(self, client, mock_agent_manager):
        """Test successful agent unloading."""
        with patch('app.api.agents.get_agent_manager', return_value=mock_agent_manager):
            response = client.delete("/api/agents/test_agent")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "unloaded successfully" in data["message"]

    def test_unload_agent_failure(self, client, mock_agent_manager):
        """Test agent unloading failure."""
        mock_agent_manager.unload_agent.return_value = False

        with patch('app.api.agents.get_agent_manager', return_value=mock_agent_manager):
            response = client.delete("/api/agents/test_agent")

            assert response.status_code == 400
            assert "Failed to unload" in response.json()["detail"]


class TestAgentsAPIIntegration:
    """Integration tests for agents API."""

    @pytest.fixture
    def client(self):
        """Test client for API endpoints."""
        # Create a clean FastAPI app for testing without NiceGUI middleware
        test_app = FastAPI(title="Test IAM Dashboard API")
        test_app.include_router(agents_router)
        return TestClient(test_app)

    def test_api_endpoints_exist(self, client):
        """Test that all agent API endpoints exist."""
        # This test verifies that the routes are properly registered
        # without requiring full system initialization

        endpoints_to_test = [
            ("/api/agents/", "GET"),
            ("/api/agents/status", "GET"),
        ]

        for endpoint, method in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)

            # We expect either 200 (success) or 500 (internal error due to missing setup)
            # but not 404 (route not found)
            assert response.status_code != 404, f"Endpoint {method} {endpoint} not found"

    def test_agent_health_endpoint_format(self, client):
        """Test that agent health endpoint returns proper format."""
        # Mock a simple health check response to test format
        mock_metadata = MagicMock()
        mock_metadata.status = AgentStatus.ACTIVE
        mock_metadata.health_status = "healthy"
        mock_metadata.last_health_check = datetime.now(UTC)
        mock_metadata.error_message = None

        mock_manager = MagicMock()
        mock_manager.get_agent_metadata.return_value = mock_metadata
        mock_manager.health_check = AsyncMock(return_value=True)

        with patch('app.api.agents.get_agent_manager', return_value=mock_manager):
            response = client.get("/api/agents/test_agent/health")

            if response.status_code == 200:
                data = response.json()
                required_fields = ["agent_id", "status", "health_status", "last_health_check"]
                for field in required_fields:
                    assert field in data, f"Missing required field: {field}"

    def test_system_status_endpoint_format(self, client):
        """Test that system status endpoint returns proper format."""
        mock_status = {
            "system_healthy": True,
            "total_agents": 0,
            "active_agents": 0,
            "inactive_agents": 0,
            "error_agents": 0,
            "agents": {}
        }

        with patch('app.api.agents.get_system_status', return_value=mock_status):
            response = client.get("/api/agents/status")

            assert response.status_code == 200
            data = response.json()

            required_fields = ["system_healthy", "total_agents", "active_agents", "inactive_agents", "error_agents", "agents"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
