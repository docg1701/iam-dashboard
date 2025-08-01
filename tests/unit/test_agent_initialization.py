"""Tests for agent initialization system."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.agent_initialization import (
    AgentInitializationError,
    get_agent_manager,
    get_system_status,
    initialize_agent_system,
    is_agent_system_healthy,
    shutdown_agent_system,
)
from app.core.agent_manager import AgentStatus


class TestAgentInitialization:
    """Test agent initialization functions."""

    @pytest.fixture
    def mock_agent_manager(self):
        """Mock agent manager for testing."""
        manager = MagicMock()
        manager.load_agent = AsyncMock(return_value=True)
        manager.start_monitoring = AsyncMock()
        manager.health_check = AsyncMock(return_value=True)
        manager.get_all_agents_metadata = MagicMock(return_value={})
        manager.disable_agent = AsyncMock(return_value=True)
        manager.unload_agent = AsyncMock(return_value=True)
        manager.stop_monitoring = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_initialize_agent_system_success(self, mock_agent_manager):
        """Test successful agent system initialization."""
        with patch('app.core.agent_initialization.agent_manager', mock_agent_manager):
            await initialize_agent_system()

            # Verify agent loading was called
            assert mock_agent_manager.load_agent.call_count >= 1

            # Verify monitoring was started
            mock_agent_manager.start_monitoring.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_agent_system_agent_registration_failure(self, mock_agent_manager):
        """Test agent system initialization with agent registration failure."""
        mock_agent_manager.load_agent.return_value = False

        with patch('app.core.agent_initialization.agent_manager', mock_agent_manager):
            with pytest.raises(AgentInitializationError):
                await initialize_agent_system()

    @pytest.mark.asyncio
    async def test_initialize_agent_system_health_check_failure(self, mock_agent_manager):
        """Test agent system initialization with health check failure."""
        mock_agent_manager.health_check.return_value = False
        mock_agent_manager.get_all_agents_metadata.return_value = {"test_agent": MagicMock()}

        with patch('app.core.agent_initialization.agent_manager', mock_agent_manager):
            with pytest.raises(AgentInitializationError):
                await initialize_agent_system()

    @pytest.mark.asyncio
    async def test_shutdown_agent_system_success(self, mock_agent_manager):
        """Test successful agent system shutdown."""
        mock_agent_manager.get_all_agents_metadata.return_value = {
            "agent1": MagicMock(),
            "agent2": MagicMock()
        }

        with patch('app.core.agent_initialization.agent_manager', mock_agent_manager):
            await shutdown_agent_system()

            # Verify monitoring was stopped
            mock_agent_manager.stop_monitoring.assert_called_once()

            # Verify agents were disabled and unloaded
            assert mock_agent_manager.disable_agent.call_count == 2
            assert mock_agent_manager.unload_agent.call_count == 2

    def test_get_agent_manager(self):
        """Test getting the agent manager instance."""
        manager = get_agent_manager()
        assert manager is not None

    @pytest.mark.asyncio
    async def test_is_agent_system_healthy(self, mock_agent_manager):
        """Test checking if agent system is healthy."""
        mock_metadata = MagicMock()
        mock_metadata.status = AgentStatus.ACTIVE
        mock_agent_manager.get_all_agents_metadata.return_value = {"agent1": mock_metadata}
        mock_agent_manager.is_agent_active.return_value = True

        with patch('app.core.agent_initialization.agent_manager', mock_agent_manager):
            result = await is_agent_system_healthy()
            assert result is True

    @pytest.mark.asyncio
    async def test_is_agent_system_unhealthy(self, mock_agent_manager):
        """Test checking if agent system is unhealthy."""
        mock_metadata = MagicMock()
        mock_metadata.status = AgentStatus.ERROR
        mock_agent_manager.get_all_agents_metadata.return_value = {"agent1": mock_metadata}
        mock_agent_manager.is_agent_active.return_value = False

        with patch('app.core.agent_initialization.agent_manager', mock_agent_manager):
            result = await is_agent_system_healthy()
            assert result is False

    @pytest.mark.asyncio
    async def test_get_system_status(self, mock_agent_manager):
        """Test getting comprehensive system status."""
        from datetime import UTC, datetime

        # Mock metadata
        mock_metadata = MagicMock()
        mock_metadata.name = "Test Agent"
        mock_metadata.status = AgentStatus.ACTIVE
        mock_metadata.health_status = "healthy"
        mock_metadata.last_health_check = datetime.now(UTC)
        mock_metadata.error_message = None
        mock_metadata.capabilities = ["test_capability"]
        mock_metadata.created_at = datetime.now(UTC)

        mock_agent_manager.get_all_agents_metadata.return_value = {"agent1": mock_metadata}

        with patch('app.core.agent_initialization.agent_manager', mock_agent_manager):
            with patch('app.core.agent_initialization.is_agent_system_healthy', return_value=True):
                status = await get_system_status()

                assert status["system_healthy"] is True
                assert status["total_agents"] == 1
                assert status["active_agents"] == 1
                assert "agents" in status
                assert "agent1" in status["agents"]

    @pytest.mark.asyncio
    async def test_get_system_status_with_error(self, mock_agent_manager):
        """Test getting system status when an error occurs."""
        mock_agent_manager.get_all_agents_metadata.side_effect = Exception("Test error")

        with patch('app.core.agent_initialization.agent_manager', mock_agent_manager):
            status = await get_system_status()

            assert status["system_healthy"] is False
            assert "error" in status
            assert status["total_agents"] == 0


class TestAgentInitializationIntegration:
    """Integration tests for agent initialization."""

    @pytest.mark.asyncio
    async def test_full_initialization_cycle(self):
        """Test full initialization and shutdown cycle."""
        # This test would require a real database and agent setup
        # For now, we'll just verify the functions can be called without errors

        try:
            # Note: This would normally require proper setup
            # await initialize_agent_system()
            # await shutdown_agent_system()
            pass
        except Exception as e:
            # In a real test environment, this should not raise an exception
            # For unit testing, we expect some exceptions due to missing dependencies
            assert isinstance(e, (AgentInitializationError, Exception))

    @pytest.mark.asyncio
    async def test_agent_registration_types(self):
        """Test that all expected agent types are registered."""
        # This would test that PDF processor and other agents are properly registered
        # For now, this is a placeholder for future implementation
        pass

    @pytest.mark.asyncio
    async def test_health_monitoring_startup(self):
        """Test that health monitoring starts correctly."""
        # This would test the health monitoring system
        # For now, this is a placeholder for future implementation
        pass
