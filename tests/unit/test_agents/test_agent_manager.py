"""Tests for AgentManager core component."""

from unittest.mock import AsyncMock, Mock

import pytest

from app.core.agent_manager import AgentManager, AgentMetadata, AgentStatus


class TestAgentManager:
    """Test suite for AgentManager class."""

    @pytest.fixture
    def agent_manager(self):
        """Create AgentManager instance for testing."""
        return AgentManager()

    @pytest.fixture
    def mock_agent(self):
        """Create mock agent for testing."""
        agent = Mock()
        agent.initialize = AsyncMock(return_value=True)
        agent.health_check = AsyncMock(return_value=True)
        return agent

    @pytest.fixture
    def sample_config(self):
        """Sample agent configuration."""
        return {
            "name": "Test Agent",
            "description": "Test agent for unit testing",
            "capabilities": ["test_capability"],
            "dependencies": []
        }

    @pytest.mark.asyncio
    async def test_load_agent_success(self, agent_manager, mock_agent, sample_config):
        """Test successful agent loading."""
        # Mock agent class
        mock_agent_class = Mock(return_value=mock_agent)

        # Load agent
        result = await agent_manager.load_agent("test_agent", mock_agent_class, sample_config)

        # Assertions
        assert result is True
        assert "test_agent" in agent_manager._agents
        assert "test_agent" in agent_manager._metadata

        metadata = agent_manager._metadata["test_agent"]
        assert metadata.agent_id == "test_agent"
        assert metadata.name == "Test Agent"
        assert metadata.status == AgentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_load_agent_failure(self, agent_manager):
        """Test agent loading failure."""
        # Mock agent class that raises exception
        mock_agent_class = Mock(side_effect=Exception("Load failed"))

        # Load agent
        result = await agent_manager.load_agent("test_agent", mock_agent_class, {})

        # Assertions
        assert result is False
        assert "test_agent" not in agent_manager._agents
        if "test_agent" in agent_manager._metadata:
            assert agent_manager._metadata["test_agent"].status == AgentStatus.ERROR

    @pytest.mark.asyncio
    async def test_enable_agent(self, agent_manager, mock_agent, sample_config):
        """Test enabling an agent."""
        # Load agent first
        mock_agent_class = Mock(return_value=mock_agent)
        await agent_manager.load_agent("test_agent", mock_agent_class, sample_config)

        # Set to disabled first
        agent_manager._metadata["test_agent"].status = AgentStatus.DISABLED

        # Enable agent
        result = await agent_manager.enable_agent("test_agent")

        # Assertions
        assert result is True
        assert agent_manager._metadata["test_agent"].status == AgentStatus.ACTIVE
        assert agent_manager._metadata["test_agent"].error_message is None

    @pytest.mark.asyncio
    async def test_enable_nonexistent_agent(self, agent_manager):
        """Test enabling a non-existent agent."""
        result = await agent_manager.enable_agent("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_disable_agent(self, agent_manager, mock_agent, sample_config):
        """Test disabling an agent."""
        # Load agent first
        mock_agent_class = Mock(return_value=mock_agent)
        await agent_manager.load_agent("test_agent", mock_agent_class, sample_config)

        # Disable agent
        result = await agent_manager.disable_agent("test_agent")

        # Assertions
        assert result is True
        assert agent_manager._metadata["test_agent"].status == AgentStatus.DISABLED

    @pytest.mark.asyncio
    async def test_unload_agent(self, agent_manager, mock_agent, sample_config):
        """Test unloading an agent."""
        # Load agent first
        mock_agent_class = Mock(return_value=mock_agent)
        await agent_manager.load_agent("test_agent", mock_agent_class, sample_config)

        # Unload agent
        result = await agent_manager.unload_agent("test_agent")

        # Assertions
        assert result is True
        assert "test_agent" not in agent_manager._agents
        assert "test_agent" not in agent_manager._metadata

    @pytest.mark.asyncio
    async def test_health_check_success(self, agent_manager, mock_agent, sample_config):
        """Test successful health check."""
        # Load agent first
        mock_agent_class = Mock(return_value=mock_agent)
        await agent_manager.load_agent("test_agent", mock_agent_class, sample_config)

        # Health check
        result = await agent_manager.health_check("test_agent")

        # Assertions
        assert result is True
        metadata = agent_manager._metadata["test_agent"]
        assert metadata.health_status == "healthy"
        assert metadata.last_health_check is not None

    @pytest.mark.asyncio
    async def test_health_check_failure(self, agent_manager, mock_agent, sample_config):
        """Test health check failure."""
        # Mock failed health check
        mock_agent.health_check = AsyncMock(return_value=False)

        # Load agent first
        mock_agent_class = Mock(return_value=mock_agent)
        await agent_manager.load_agent("test_agent", mock_agent_class, sample_config)

        # Health check
        result = await agent_manager.health_check("test_agent")

        # Assertions
        assert result is False
        metadata = agent_manager._metadata["test_agent"]
        assert metadata.health_status == "unhealthy"
        assert metadata.status == AgentStatus.ERROR

    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self, agent_manager):
        """Test monitoring system lifecycle."""
        # Start monitoring
        await agent_manager.start_monitoring()
        assert agent_manager._health_check_task is not None
        assert not agent_manager._health_check_task.done()

        # Stop monitoring
        await agent_manager.stop_monitoring()
        assert agent_manager._health_check_task is None

    def test_get_agent_metadata(self, agent_manager):
        """Test getting agent metadata."""
        # Create test metadata
        metadata = AgentMetadata(
            agent_id="test_agent",
            name="Test Agent",
            description="Test description",
            capabilities=["test"],
            dependencies=[]
        )
        agent_manager._metadata["test_agent"] = metadata

        # Get metadata
        result = agent_manager.get_agent_metadata("test_agent")

        # Assertions
        assert result is not None
        assert result.agent_id == "test_agent"
        assert result.name == "Test Agent"

    def test_get_all_agents_metadata(self, agent_manager):
        """Test getting all agents metadata."""
        # Create test metadata
        metadata1 = AgentMetadata("agent1", "Agent 1", "", [], [])
        metadata2 = AgentMetadata("agent2", "Agent 2", "", [], [])

        agent_manager._metadata["agent1"] = metadata1
        agent_manager._metadata["agent2"] = metadata2

        # Get all metadata
        result = agent_manager.get_all_agents_metadata()

        # Assertions
        assert len(result) == 2
        assert "agent1" in result
        assert "agent2" in result

    def test_is_agent_active(self, agent_manager):
        """Test checking if agent is active."""
        # Create test metadata
        metadata = AgentMetadata("test_agent", "Test", "", [], [])
        metadata.status = AgentStatus.ACTIVE
        agent_manager._metadata["test_agent"] = metadata

        # Check active status
        assert agent_manager.is_agent_active("test_agent") is True

        # Set to inactive
        metadata.status = AgentStatus.DISABLED
        assert agent_manager.is_agent_active("test_agent") is False

        # Non-existent agent
        assert agent_manager.is_agent_active("nonexistent") is False
