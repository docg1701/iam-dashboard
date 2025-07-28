"""Tests for container integration with agent management."""

import pytest
from dependency_injector import providers

from app.agents.plugin_discovery import PluginDiscovery
from app.containers import Container
from app.core.agent_config import ConfigManager
from app.core.agent_manager import AgentManager
from app.core.agent_registry import AgentRegistry


class TestContainerIntegration:
    """Test container integration with agent infrastructure."""

    @pytest.fixture
    def container(self):
        """Create container instance for testing."""
        return Container()

    def test_container_has_agent_providers(self, container):
        """Test that container has all required agent providers."""
        # Check that agent management providers exist
        assert hasattr(container, "agent_config_manager")
        assert hasattr(container, "agent_registry_service")
        assert hasattr(container, "agent_manager")
        assert hasattr(container, "plugin_discovery_service")

    def test_agent_config_manager_provider(self, container):
        """Test agent config manager provider."""
        provider = container.agent_config_manager

        assert isinstance(provider, providers.Object)

        # Get instance
        config_manager = provider()
        assert isinstance(config_manager, ConfigManager)

    def test_agent_registry_service_provider(self, container):
        """Test agent registry service provider."""
        provider = container.agent_registry_service

        assert isinstance(provider, providers.Object)

        # Get instance
        registry = provider()
        assert isinstance(registry, AgentRegistry)

    def test_agent_manager_provider(self, container):
        """Test agent manager provider."""
        provider = container.agent_manager

        assert isinstance(provider, providers.Singleton)

        # Get instance
        manager = provider()
        assert isinstance(manager, AgentManager)

        # Singleton behavior - should return same instance
        manager2 = provider()
        assert manager is manager2

    def test_plugin_discovery_service_provider(self, container):
        """Test plugin discovery service provider."""
        provider = container.plugin_discovery_service

        assert isinstance(provider, providers.Object)

        # Get instance
        discovery = provider()
        assert isinstance(discovery, PluginDiscovery)

    def test_wiring_configuration_includes_agents(self, container):
        """Test that wiring configuration includes agent modules."""
        wiring_config = container.wiring_config

        # Check that agent manager is in wiring config
        assert "app.core.agent_manager" in wiring_config.modules

    def test_container_provides_all_dependencies(self, container):
        """Test that container can provide all agent-related dependencies."""
        # Test that we can get all instances without errors
        config_manager = container.agent_config_manager()
        registry = container.agent_registry_service()
        agent_manager = container.agent_manager()
        discovery = container.plugin_discovery_service()

        # Verify types
        assert isinstance(config_manager, ConfigManager)
        assert isinstance(registry, AgentRegistry)
        assert isinstance(agent_manager, AgentManager)
        assert isinstance(discovery, PluginDiscovery)

    def test_backward_compatibility(self, container):
        """Test that existing providers still work."""
        # Ensure existing services are not affected
        assert hasattr(container, "database_session")
        assert hasattr(container, "client_repository")
        assert hasattr(container, "user_repository")
        assert hasattr(container, "client_service")
        assert hasattr(container, "user_service")

        # Test that they can be instantiated
        client_service = container.client_service()
        user_service = container.user_service()

        # These should work (though they might need database session)
        assert client_service is not None
        assert user_service is not None

    def test_container_reset_with_agents(self, container):
        """Test container reset functionality with agent providers."""
        # Get initial instances
        initial_manager = container.agent_manager()

        # Reset container
        container.reset_singletons()

        # Get new instances
        new_manager = container.agent_manager()

        # Should be different instances after reset
        assert initial_manager is not new_manager

    @pytest.mark.asyncio
    async def test_agent_integration_workflow(self, container):
        """Test complete agent integration workflow through container."""
        # Get services from container
        config_manager = container.agent_config_manager()
        agent_manager = container.agent_manager()
        registry = container.agent_registry_service()
        discovery = container.plugin_discovery_service()

        # Test configuration loading
        config = config_manager.load_config()
        assert config is not None

        # Test plugin discovery
        plugins = await discovery.discover_plugins()
        assert isinstance(plugins, dict)

        # Test agent manager initialization
        assert len(agent_manager._agents) == 0
        assert len(agent_manager._metadata) == 0

        # Test registry initialization
        agents_list = registry.list_agents()
        assert isinstance(agents_list, list)

    def test_container_provider_dependencies(self, container):
        """Test that providers have correct dependency relationships."""
        # Agent manager should be singleton (stateful)
        assert isinstance(container.agent_manager, providers.Singleton)

        # Config, registry, and discovery should be object providers (singletons via module globals)
        assert isinstance(container.agent_config_manager, providers.Object)
        assert isinstance(container.agent_registry_service, providers.Object)
        assert isinstance(container.plugin_discovery_service, providers.Object)
