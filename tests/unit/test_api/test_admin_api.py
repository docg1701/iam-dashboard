"""Unit tests for admin API endpoints."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.admin import router as admin_router
from app.api.middleware.auth_middleware import (
    get_current_user,
    require_admin,
    require_sysadmin,
)
from app.containers import Container


@pytest.fixture
def mock_agent_manager():
    """Mock AgentManager for testing."""
    manager = MagicMock()
    # Make async methods return coroutines
    manager.enable_agent = AsyncMock(return_value=True)
    manager.disable_agent = AsyncMock(return_value=True)
    manager.health_check = AsyncMock(return_value=True)
    return manager


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
def sysadmin_user():
    """Mock SYSADMIN user."""
    return {"user_id": "123", "username": "sysadmin", "role": "sysadmin"}


@pytest.fixture
def admin_user():
    """Mock ADMIN_USER user."""
    return {"user_id": "124", "username": "admin", "role": "admin_user"}


@pytest.fixture
def common_user():
    """Mock COMMON_USER user."""
    return {"user_id": "125", "username": "user", "role": "common_user"}


def create_authenticated_client(mock_agent_manager, container, user_role="sysadmin"):
    """Create test client with proper authentication mocking."""
    app = FastAPI()

    # Mock users for different roles
    def mock_sysadmin_user():
        return {"user_id": "123", "username": "sysadmin", "role": "sysadmin"}

    def mock_admin_user():
        return {"user_id": "124", "username": "admin", "role": "admin_user"}

    def mock_common_user():
        return {"user_id": "125", "username": "user", "role": "common_user"}

    # Choose the appropriate user mock
    user_mocks = {
        "sysadmin": mock_sysadmin_user,
        "admin_user": mock_admin_user,
        "common_user": mock_common_user
    }

    current_user_mock = user_mocks.get(user_role, mock_sysadmin_user)

    # Override authentication dependencies
    app.dependency_overrides[get_current_user] = current_user_mock

    # Override role-based dependencies based on user role
    if user_role in ["sysadmin", "admin_user"]:
        app.dependency_overrides[require_admin()] = current_user_mock
    if user_role == "sysadmin":
        app.dependency_overrides[require_sysadmin()] = current_user_mock

    app.include_router(admin_router)

    # Override the container provider
    container.agent_manager.override(mock_agent_manager)
    container.wire(modules=["app.api.admin"])

    return TestClient(app), container


@pytest.fixture
def client(mock_agent_manager, container):
    """Create test client with SYSADMIN authentication by default."""
    test_client, test_container = create_authenticated_client(mock_agent_manager, container, "sysadmin")

    with test_client as client:
        yield client

    # Clean up
    test_container.unwire()
    test_container.reset_override()


@pytest.fixture
def authorized_client(mock_agent_manager, container, sysadmin_user):
    """Create test client with SYSADMIN authorization."""
    app = FastAPI()

    # Override auth dependencies to return mocked user
    app.dependency_overrides[get_current_user] = lambda: sysadmin_user
    app.dependency_overrides[require_admin()] = lambda: sysadmin_user
    app.dependency_overrides[require_sysadmin()] = lambda: sysadmin_user

    app.include_router(admin_router)

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
        self, authorized_client, mock_agent_manager, mock_agent_metadata
    ):
        """Test successfully listing all agents."""
        # Setup mocks
        mock_agent_manager.get_all_agents_metadata.return_value = {
            "test_agent": mock_agent_metadata
        }

        # Make request
        response = authorized_client.get("/v1/admin/agents")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["agent_id"] == "test_agent"
        assert data[0]["name"] == "Test Agent"
        assert data[0]["status"] == "active"
        assert data[0]["capabilities"] == ["test_capability"]

    def test_list_all_agents_empty(self, authorized_client, mock_agent_manager):
        """Test listing agents when no agents exist."""
        # Setup mocks
        mock_agent_manager.get_all_agents_metadata.return_value = {}

        # Make request
        response = authorized_client.get("/v1/admin/agents")

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
        mock_agent_manager.enable_agent = AsyncMock(return_value=True)

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
        mock_agent_manager.enable_agent = AsyncMock(return_value=False)

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
        mock_agent_manager.disable_agent = AsyncMock(return_value=True)

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
        mock_agent_manager.disable_agent = AsyncMock(return_value=False)

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
        mock_agent_manager.disable_agent = AsyncMock(return_value=True)
        mock_agent_manager.enable_agent = AsyncMock(return_value=True)

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
        mock_agent_manager.disable_agent = AsyncMock(return_value=False)

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
        mock_agent_manager.disable_agent = AsyncMock(return_value=True)
        mock_agent_manager.enable_agent = AsyncMock(return_value=False)

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
        mock_agent_manager.health_check = AsyncMock(return_value=True)
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
        mock_agent_manager.health_check = AsyncMock(return_value=False)
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
        mock_agent_manager.health_check = AsyncMock(return_value=True)

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
        mock_agent_manager.health_check = AsyncMock(return_value=False)

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
        mock_agent_manager.disable_agent = AsyncMock(return_value=True)
        mock_agent_manager.enable_agent = AsyncMock(return_value=True)

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
        mock_agent_manager.disable_agent = AsyncMock(side_effect=[True, False])
        mock_agent_manager.enable_agent = AsyncMock(return_value=True)

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


class TestAdminAPIAuthorization:
    """Test authorization for admin API endpoints."""

    def test_list_agents_requires_admin_access(self, mock_agent_manager, container):
        """Test that listing agents requires admin access."""
        app = FastAPI()

        def mock_common_user():
            return {"user_id": "125", "username": "user", "role": "common_user"}

        # Override to return common user
        app.dependency_overrides[get_current_user] = mock_common_user
        app.include_router(admin_router)

        container.agent_manager.override(mock_agent_manager)
        container.wire(modules=["app.api.admin"])

        with TestClient(app) as client:
            response = client.get("/v1/admin/agents")
            # Should be forbidden for common user
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_user_can_list_agents(self, mock_agent_manager, container, mock_agent_metadata):
        """Test that ADMIN_USER can list agents."""
        app = FastAPI()

        def mock_admin_user():
            return {"user_id": "124", "username": "admin", "role": "admin_user"}

        app.dependency_overrides[get_current_user] = mock_admin_user
        app.dependency_overrides[require_admin()] = mock_admin_user
        app.include_router(admin_router)

        container.agent_manager.override(mock_agent_manager)
        container.wire(modules=["app.api.admin"])

        mock_agent_manager.get_all_agents_metadata.return_value = {"test": mock_agent_metadata}

        with TestClient(app) as client:
            response = client.get("/v1/admin/agents")
            assert response.status_code == status.HTTP_200_OK

    def test_sysadmin_operations_require_sysadmin_access(self, mock_agent_manager, container):
        """Test that SYSADMIN operations require SYSADMIN access."""
        app = FastAPI()

        def mock_admin_user():
            return {"user_id": "124", "username": "admin", "role": "admin_user"}

        app.dependency_overrides[get_current_user] = mock_admin_user
        app.dependency_overrides[require_admin()] = mock_admin_user
        app.include_router(admin_router)

        container.agent_manager.override(mock_agent_manager)
        container.wire(modules=["app.api.admin"])

        with TestClient(app) as client:
            # ADMIN_USER should not be able to start agents (SYSADMIN only)
            response = client.post("/v1/admin/agents/test_agent/start")
            assert response.status_code == status.HTTP_403_FORBIDDEN

            # ADMIN_USER should not be able to stop agents (SYSADMIN only)
            response = client.post("/v1/admin/agents/test_agent/stop")
            assert response.status_code == status.HTTP_403_FORBIDDEN

            # ADMIN_USER should not be able to restart all agents (SYSADMIN only)
            response = client.post("/v1/admin/system/restart-all")
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sysadmin_can_perform_all_operations(self, mock_agent_manager, container, mock_agent_metadata):
        """Test that SYSADMIN can perform all operations."""
        app = FastAPI()

        def mock_sysadmin_user():
            return {"user_id": "123", "username": "sysadmin", "role": "sysadmin"}

        app.dependency_overrides[get_current_user] = mock_sysadmin_user
        app.dependency_overrides[require_admin()] = mock_sysadmin_user
        app.dependency_overrides[require_sysadmin()] = mock_sysadmin_user
        app.include_router(admin_router)

        container.agent_manager.override(mock_agent_manager)
        container.wire(modules=["app.api.admin"])

        # Setup mocks
        mock_agent_manager.enable_agent = AsyncMock(return_value=True)
        mock_agent_manager.disable_agent = AsyncMock(return_value=True)
        mock_agent_manager.get_all_agents_metadata.return_value = {"test": mock_agent_metadata}

        with TestClient(app) as client:
            # SYSADMIN should be able to start agents
            response = client.post("/v1/admin/agents/test_agent/start")
            assert response.status_code == status.HTTP_200_OK

            # SYSADMIN should be able to stop agents
            response = client.post("/v1/admin/agents/test_agent/stop")
            assert response.status_code == status.HTTP_200_OK

            # SYSADMIN should be able to restart all agents
            response = client.post("/v1/admin/system/restart-all")
            assert response.status_code == status.HTTP_200_OK

    def test_configuration_operations_require_sysadmin(self, mock_agent_manager, container):
        """Test that configuration operations require SYSADMIN access."""
        app = FastAPI()

        def mock_admin_user():
            return {"user_id": "124", "username": "admin", "role": "admin_user"}

        app.dependency_overrides[get_current_user] = mock_admin_user
        app.dependency_overrides[require_admin()] = mock_admin_user
        app.include_router(admin_router)

        container.agent_manager.override(mock_agent_manager)
        container.wire(modules=["app.api.admin"])

        with TestClient(app) as client:
            # Configuration endpoints should require SYSADMIN
            response = client.get("/v1/admin/agents/test_agent/config")
            assert response.status_code == status.HTTP_403_FORBIDDEN

            response = client.put("/v1/admin/agents/test_agent/config",
                                json={"config": {"test": "value"}})
            assert response.status_code == status.HTTP_403_FORBIDDEN

            response = client.post("/v1/admin/agents/test_agent/config/validate",
                                 json={"config": {"test": "value"}})
            assert response.status_code == status.HTTP_403_FORBIDDEN

            response = client.post("/v1/admin/agents/test_agent/config/rollback")
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_access_denied(self, mock_agent_manager, container):
        """Test that unauthenticated requests are denied."""
        app = FastAPI()
        app.include_router(admin_router)

        container.agent_manager.override(mock_agent_manager)
        container.wire(modules=["app.api.admin"])

        with TestClient(app) as client:
            # All endpoints should require authentication (403 because dependencies fail)
            response = client.get("/v1/admin/agents")
            assert response.status_code == status.HTTP_403_FORBIDDEN

            response = client.post("/v1/admin/agents/test/start")
            assert response.status_code == status.HTTP_403_FORBIDDEN

            response = client.get("/v1/admin/system/health")
            assert response.status_code == status.HTTP_403_FORBIDDEN
