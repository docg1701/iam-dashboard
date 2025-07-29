"""Unit tests for admin API endpoints."""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.admin import router as admin_router
from app.containers import Container


@pytest.fixture
def mock_agent_manager():
    """Mock AgentManager for testing."""
    return MagicMock()


@pytest.fixture
def mock_agent_metadata():
    """Mock agent metadata."""
    metadata = MagicMock()
    metadata.name = "Test Agent"
    metadata.description = "Test agent description"
    metadata.status.value = "active"
    metadata.capabilities = ["test_capability"]
    metadata.health_status = "healthy"
    metadata.last_health_check = None
    metadata.error_message = None
    return metadata


@pytest.fixture
def container():
    """Create container for testing."""
    return Container()


@pytest.fixture
def client(mock_agent_manager, container):
    """Create test client with mocked dependencies."""
    # Create a clean FastAPI app for testing
    app = FastAPI()
    app.include_router(admin_router)

    # Override the container provider
    container.agent_manager.override(mock_agent_manager)
    container.wire(modules=["app.api.admin"])

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    container.unwire()
    container.reset_override()


class TestAgentListing:
    """Test agent listing endpoints."""

    def test_list_all_agents_success(
        self, client, mock_agent_manager, mock_agent_metadata
    ):
        """Test successfully listing all agents."""
        # Setup mocks
        mock_agent_manager.get_all_agents_metadata.return_value = {
            "test_agent": mock_agent_metadata
        }

        # Make request
        response = client.get("/v1/admin/agents")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["agent_id"] == "test_agent"
        assert data[0]["name"] == "Test Agent"
        assert data[0]["status"] == "active"
        assert data[0]["capabilities"] == ["test_capability"]

    def test_list_all_agents_empty(self, client, mock_agent_manager):
        """Test listing agents when no agents exist."""
        # Setup mocks
        mock_agent_manager.get_all_agents_metadata.return_value = {}

        # Make request
        response = client.get("/v1/admin/agents")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0

    def test_get_agent_details_success(
        self, client, mock_agent_manager, mock_agent_metadata
    ):
        """Test getting details for a specific agent."""
        # Setup mocks
        mock_agent_manager.get_agent_metadata.return_value = mock_agent_metadata

        # Make request
        response = client.get("/v1/admin/agents/test_agent")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["agent_id"] == "test_agent"
        assert data["name"] == "Test Agent"
        assert data["status"] == "active"

    def test_get_agent_details_not_found(self, client, mock_agent_manager):
        """Test getting details for non-existent agent."""
        # Setup mocks
        mock_agent_manager.get_agent_metadata.return_value = None

        # Make request
        response = client.get("/v1/admin/agents/nonexistent_agent")

        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"]


class TestAgentOperations:
    """Test agent operation endpoints."""

    def test_start_agent_success(self, client, mock_agent_manager):
        """Test successfully starting an agent."""
        # Setup mocks
        mock_agent_manager.enable_agent.return_value = True

        # Make request
        response = client.post("/v1/admin/agents/test_agent/start")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["agent_id"] == "test_agent"
        assert "started successfully" in data["message"]

    def test_start_agent_failure(self, client, mock_agent_manager):
        """Test starting an agent that fails to start."""
        # Setup mocks
        mock_agent_manager.enable_agent.return_value = False

        # Make request
        response = client.post("/v1/admin/agents/test_agent/start")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert data["agent_id"] == "test_agent"
        assert "failed to start" in data["message"]

    def test_stop_agent_success(self, client, mock_agent_manager):
        """Test successfully stopping an agent."""
        # Setup mocks
        mock_agent_manager.disable_agent.return_value = True

        # Make request
        response = client.post("/v1/admin/agents/test_agent/stop")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["agent_id"] == "test_agent"
        assert "stopped successfully" in data["message"]

    def test_stop_agent_failure(self, client, mock_agent_manager):
        """Test stopping an agent that fails to stop."""
        # Setup mocks
        mock_agent_manager.disable_agent.return_value = False

        # Make request
        response = client.post("/v1/admin/agents/test_agent/stop")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert data["agent_id"] == "test_agent"
        assert "failed to stop" in data["message"]

    def test_restart_agent_success(self, client, mock_agent_manager):
        """Test successfully restarting an agent."""
        # Setup mocks
        mock_agent_manager.disable_agent.return_value = True
        mock_agent_manager.enable_agent.return_value = True

        # Make request
        response = client.post("/v1/admin/agents/test_agent/restart")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["agent_id"] == "test_agent"
        assert "restarted successfully" in data["message"]

    def test_restart_agent_stop_failure(self, client, mock_agent_manager):
        """Test restarting an agent when stop fails."""
        # Setup mocks
        mock_agent_manager.disable_agent.return_value = False

        # Make request
        response = client.post("/v1/admin/agents/test_agent/restart")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert data["agent_id"] == "test_agent"
        assert "Failed to stop" in data["message"]

    def test_restart_agent_start_failure(self, client, mock_agent_manager):
        """Test restarting an agent when start fails."""
        # Setup mocks
        mock_agent_manager.disable_agent.return_value = True
        mock_agent_manager.enable_agent.return_value = False

        # Make request
        response = client.post("/v1/admin/agents/test_agent/restart")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert data["agent_id"] == "test_agent"
        assert "failed to restart" in data["message"]


class TestHealthChecks:
    """Test health check endpoints."""

    def test_check_agent_health_success(
        self, client, mock_agent_manager, mock_agent_metadata
    ):
        """Test successful agent health check."""
        # Setup mocks
        mock_agent_manager.health_check.return_value = True
        mock_agent_manager.get_agent_metadata.return_value = mock_agent_metadata

        # Make request
        response = client.get("/v1/admin/agents/test_agent/health")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["agent_id"] == "test_agent"
        assert data["is_healthy"] is True
        assert data["health_status"] == "healthy"
        assert data["status"] == "active"

    def test_check_agent_health_not_found(self, client, mock_agent_manager):
        """Test health check for non-existent agent."""
        # Setup mocks
        mock_agent_manager.health_check.return_value = False
        mock_agent_manager.get_agent_metadata.return_value = None

        # Make request
        response = client.get("/v1/admin/agents/nonexistent/health")

        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"]

    def test_check_system_health(self, client, mock_agent_manager, mock_agent_metadata):
        """Test system health check."""
        # Setup mocks
        mock_agent_manager.get_all_agents_metadata.return_value = {
            "agent1": mock_agent_metadata,
            "agent2": mock_agent_metadata,
        }
        mock_agent_manager.health_check.return_value = True

        # Make request
        response = client.get("/v1/admin/system/health")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["healthy_agents"] == 2
        assert data["total_agents"] == 2
        assert data["system_status"] == "healthy"
        assert len(data["agent_details"]) == 2

    def test_check_system_health_degraded(
        self, client, mock_agent_manager, mock_agent_metadata
    ):
        """Test system health check with some unhealthy agents."""
        # Setup mocks
        mock_agent_manager.get_all_agents_metadata.return_value = {
            "agent1": mock_agent_metadata,
            "agent2": mock_agent_metadata,
        }
        # First agent healthy, second unhealthy
        mock_agent_manager.health_check.side_effect = [True, False]

        # Make request
        response = client.get("/v1/admin/system/health")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["healthy_agents"] == 1
        assert data["total_agents"] == 2
        assert data["system_status"] == "degraded"

    def test_check_system_health_unhealthy(
        self, client, mock_agent_manager, mock_agent_metadata
    ):
        """Test system health check with all agents unhealthy."""
        # Setup mocks
        mock_agent_manager.get_all_agents_metadata.return_value = {
            "agent1": mock_agent_metadata
        }
        mock_agent_manager.health_check.return_value = False

        # Make request
        response = client.get("/v1/admin/system/health")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["healthy_agents"] == 0
        assert data["total_agents"] == 1
        assert data["system_status"] == "unhealthy"


class TestSystemOperations:
    """Test system-wide operations."""

    def test_restart_all_agents_success(
        self, client, mock_agent_manager, mock_agent_metadata
    ):
        """Test successfully restarting all agents."""
        # Setup mocks
        mock_agent_manager.get_all_agents_metadata.return_value = {
            "agent1": mock_agent_metadata,
            "agent2": mock_agent_metadata,
        }
        mock_agent_manager.disable_agent.return_value = True
        mock_agent_manager.enable_agent.return_value = True

        # Make request
        response = client.post("/v1/admin/system/restart-all")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "Restarted 2 of 2 agents" in data["message"]
        assert data["results"]["agent1"] == "restarted"
        assert data["results"]["agent2"] == "restarted"

    def test_restart_all_agents_partial_failure(
        self, client, mock_agent_manager, mock_agent_metadata
    ):
        """Test restarting all agents with some failures."""
        # Setup mocks
        mock_agent_manager.get_all_agents_metadata.return_value = {
            "agent1": mock_agent_metadata,
            "agent2": mock_agent_metadata,
        }
        # First agent succeeds, second fails to stop
        mock_agent_manager.disable_agent.side_effect = [True, False]
        mock_agent_manager.enable_agent.return_value = True

        # Make request
        response = client.post("/v1/admin/system/restart-all")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert "Restarted 1 of 2 agents" in data["message"]
        assert data["results"]["agent1"] == "restarted"
        assert data["results"]["agent2"] == "failed_to_stop"

    def test_restart_all_agents_no_agents(self, client, mock_agent_manager):
        """Test restarting all agents when no agents exist."""
        # Setup mocks
        mock_agent_manager.get_all_agents_metadata.return_value = {}

        # Make request
        response = client.post("/v1/admin/system/restart-all")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "Restarted 0 of 0 agents" in data["message"]
        assert data["results"] == {}


class TestErrorHandling:
    """Test error handling in admin endpoints."""

    def test_agent_manager_exception(self, client, mock_agent_manager):
        """Test handling of agent manager exceptions."""
        # Setup mocks to raise exception
        mock_agent_manager.get_all_agents_metadata.side_effect = Exception(
            "Agent manager error"
        )

        # Make request
        response = client.get("/v1/admin/agents")

        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Error retrieving agents" in data["detail"]

    def test_enable_agent_exception(self, client, mock_agent_manager):
        """Test handling of exceptions during agent enable."""
        # Setup mocks to raise exception
        mock_agent_manager.enable_agent.side_effect = Exception("Enable error")

        # Make request
        response = client.post("/v1/admin/agents/test_agent/start")

        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Error starting agent" in data["detail"]
