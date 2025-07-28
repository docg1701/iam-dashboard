"""Tests for AgentPlugin interface and base classes."""

from unittest.mock import Mock

import pytest

from app.agents.base_agent import AgentPlugin, AgentPluginRegistry


class MockAgentPlugin(AgentPlugin):
    """Mock implementation of AgentPlugin for testing."""

    PLUGIN_NAME = "MockPlugin"
    VERSION = "1.0.0"

    async def initialize(self) -> bool:
        """Test implementation of initialize."""
        self._initialized = True
        return True

    async def process(self, data):
        """Test implementation of process."""
        return {"result": "processed", "input": data}

    async def health_check(self) -> bool:
        """Test implementation of health_check."""
        return self._initialized

    def get_capabilities(self):
        """Test implementation of get_capabilities."""
        return ["test_capability", "data_processing"]


class IncompleteAgentPlugin(AgentPlugin):
    """Incomplete plugin implementation for testing validation."""

    PLUGIN_NAME = "IncompletePlugin"

    # Missing required method implementations


class TestAgentPluginBase:
    """Test suite for AgentPlugin base class."""

    @pytest.fixture
    def test_config(self):
        """Sample configuration for testing."""
        return {
            "name": "Test Agent",
            "description": "Test agent for unit testing",
            "version": "1.0.0",
            "capabilities": ["test"],
            "dependencies": ["dep1"]
        }

    @pytest.fixture
    def test_plugin(self, test_config):
        """Create test plugin instance."""
        return MockAgentPlugin("test_agent", test_config)

    def test_plugin_initialization(self, test_plugin, test_config):
        """Test plugin initialization."""
        assert test_plugin.agent_id == "test_agent"
        assert test_plugin.name == "Test Agent"
        assert test_plugin.description == "Test agent for unit testing"
        assert test_plugin.version == "1.0.0"
        assert not test_plugin.is_initialized
        assert test_plugin.agent_instance is None

    @pytest.mark.asyncio
    async def test_initialize_plugin(self, test_plugin):
        """Test plugin initialization."""
        result = await test_plugin.initialize()

        assert result is True
        assert test_plugin.is_initialized is True

    @pytest.mark.asyncio
    async def test_process_data(self, test_plugin):
        """Test data processing."""
        await test_plugin.initialize()

        test_data = {"key": "value"}
        result = await test_plugin.process(test_data)

        assert result["result"] == "processed"
        assert result["input"] == test_data

    @pytest.mark.asyncio
    async def test_health_check(self, test_plugin):
        """Test health check functionality."""
        # Before initialization
        result = await test_plugin.health_check()
        assert result is False

        # After initialization
        await test_plugin.initialize()
        result = await test_plugin.health_check()
        assert result is True

    def test_get_capabilities(self, test_plugin):
        """Test capabilities retrieval."""
        capabilities = test_plugin.get_capabilities()

        assert "test_capability" in capabilities
        assert "data_processing" in capabilities

    def test_get_metadata(self, test_plugin):
        """Test metadata retrieval."""
        metadata = test_plugin.get_metadata()

        assert metadata["agent_id"] == "test_agent"
        assert metadata["name"] == "Test Agent"
        assert metadata["version"] == "1.0.0"
        assert metadata["initialized"] is False
        assert "test_capability" in metadata["capabilities"]

    @pytest.mark.asyncio
    async def test_shutdown(self, test_plugin):
        """Test plugin shutdown."""
        await test_plugin.initialize()
        assert test_plugin.is_initialized is True

        await test_plugin.shutdown()
        assert test_plugin.is_initialized is False
        assert test_plugin.agent_instance is None


class TestAgentPluginRegistry:
    """Test suite for AgentPluginRegistry."""

    @pytest.fixture
    def registry(self):
        """Create registry instance for testing."""
        return AgentPluginRegistry()

    @pytest.fixture
    def test_config(self):
        """Sample configuration for testing."""
        return {
            "name": "Test Agent",
            "description": "Test agent",
            "dependencies": []
        }

    def test_register_plugin(self, registry):
        """Test plugin registration."""
        registry.register_plugin(MockAgentPlugin)

        assert "MockPlugin" in registry.list_plugins()
        assert registry.get_plugin_class("MockPlugin") == MockAgentPlugin

    def test_register_invalid_plugin(self, registry):
        """Test registration of invalid plugin."""
        with pytest.raises(ValueError):
            registry.register_plugin(str)  # Not a subclass of AgentPlugin

    def test_unregister_plugin(self, registry):
        """Test plugin unregistration."""
        registry.register_plugin(MockAgentPlugin)
        assert "MockPlugin" in registry.list_plugins()

        registry.unregister_plugin("MockPlugin")
        assert "MockPlugin" not in registry.list_plugins()

    def test_get_plugin_info(self, registry):
        """Test getting plugin information."""
        registry.register_plugin(MockAgentPlugin)

        info = registry.get_plugin_info("MockPlugin")

        assert info is not None
        assert info["name"] == "MockPlugin"
        assert info["class"] == "MockAgentPlugin"
        assert info["version"] == "1.0.0"

    def test_get_nonexistent_plugin_info(self, registry):
        """Test getting info for non-existent plugin."""
        info = registry.get_plugin_info("NonExistent")
        assert info is None

    @pytest.mark.asyncio
    async def test_create_instance(self, registry, test_config):
        """Test creating plugin instance."""
        registry.register_plugin(MockAgentPlugin)

        instance = await registry.create_instance("MockPlugin", "test_agent", test_config)

        assert instance is not None
        assert isinstance(instance, MockAgentPlugin)
        assert instance.agent_id == "test_agent"
        assert "test_agent" in registry.list_instances()

    @pytest.mark.asyncio
    async def test_create_instance_nonexistent_plugin(self, registry, test_config):
        """Test creating instance of non-existent plugin."""
        instance = await registry.create_instance("NonExistent", "test_agent", test_config)
        assert instance is None

    def test_get_instance(self, registry):
        """Test getting plugin instance."""
        # Create mock instance
        mock_instance = Mock()
        registry._instances["test_agent"] = mock_instance

        result = registry.get_instance("test_agent")
        assert result == mock_instance

    def test_remove_instance(self, registry):
        """Test removing plugin instance."""
        # Create mock instance
        mock_instance = Mock()
        registry._instances["test_agent"] = mock_instance

        registry.remove_instance("test_agent")
        assert "test_agent" not in registry.list_instances()

    def test_plugin_validation_success(self, registry):
        """Test validation of valid plugin."""
        # Test that a valid plugin can be registered without errors
        try:
            registry.register_plugin(MockAgentPlugin)
            assert "MockPlugin" in registry.list_plugins()
        except Exception as e:
            pytest.fail(f"Valid plugin registration failed: {e}")

    def test_plugin_validation_failure(self, registry):
        """Test validation of invalid plugin."""
        # Test that invalid plugin registration fails
        with pytest.raises(ValueError):
            registry.register_plugin(str)  # Not a subclass of AgentPlugin

    def test_list_plugins(self, registry):
        """Test listing all plugins."""
        registry.register_plugin(MockAgentPlugin)

        plugins = registry.list_plugins()
        assert "MockPlugin" in plugins

    def test_list_instances(self, registry):
        """Test listing all instances."""
        mock_instance = Mock()
        registry._instances["test_agent"] = mock_instance

        instances = registry.list_instances()
        assert "test_agent" in instances
