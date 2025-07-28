"""Base agent class and plugin interface for autonomous agents."""

import logging
from abc import ABC, abstractmethod
from typing import Any

from agno.agent import Agent

logger = logging.getLogger(__name__)


class AgentPlugin(ABC):
    """Abstract base class for agent plugins."""

    def __init__(self, agent_id: str, config: dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self.name = config.get("name", agent_id)
        self.description = config.get("description", "")
        self.version = config.get("version", "1.0.0")
        self._initialized = False
        self._agent_instance: Agent | None = None

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the agent plugin.

        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        pass

    @abstractmethod
    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process data through the agent.

        Args:
            data: Input data to process

        Returns:
            Dict containing the processed results
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Perform a health check on the agent.

        Returns:
            bool: True if the agent is healthy, False otherwise.
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Get the capabilities of this agent.

        Returns:
            List of capability strings
        """
        pass

    @property
    def is_initialized(self) -> bool:
        """Check if the agent is initialized."""
        return self._initialized

    @property
    def agent_instance(self) -> Agent | None:
        """Get the underlying agent instance."""
        return self._agent_instance

    async def shutdown(self) -> None:
        """Shutdown the agent plugin and clean up resources."""
        try:
            logger.info(f"Shutting down agent plugin: {self.agent_id}")
            self._initialized = False
            self._agent_instance = None
        except Exception as e:
            logger.error(f"Error during shutdown of agent {self.agent_id}: {str(e)}")

    def get_metadata(self) -> dict[str, Any]:
        """Get agent metadata."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": self.get_capabilities(),
            "dependencies": self.config.get("dependencies", []),
            "initialized": self._initialized,
        }


class AgentPluginRegistry:
    """Registry for managing agent plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, type] = {}
        self._instances: dict[str, AgentPlugin] = {}

    def register_plugin(self, plugin_class: type) -> None:
        """Register an agent plugin class.

        Args:
            plugin_class: The plugin class to register
        """
        if not issubclass(plugin_class, AgentPlugin):
            raise ValueError("Plugin class must inherit from AgentPlugin")

        plugin_name = getattr(plugin_class, "PLUGIN_NAME", plugin_class.__name__)

        if plugin_name in self._plugins:
            logger.warning(f"Plugin {plugin_name} already registered, overwriting")

        self._plugins[plugin_name] = plugin_class
        logger.info(f"Registered plugin: {plugin_name}")

    def unregister_plugin(self, plugin_name: str) -> None:
        """Unregister an agent plugin.

        Args:
            plugin_name: Name of the plugin to unregister
        """
        if plugin_name in self._plugins:
            del self._plugins[plugin_name]
            logger.info(f"Unregistered plugin: {plugin_name}")
        else:
            logger.warning(f"Plugin {plugin_name} not found for unregistration")

    def get_plugin_class(self, plugin_name: str) -> type | None:
        """Get a plugin class by name.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin class or None if not found
        """
        return self._plugins.get(plugin_name)

    def list_plugins(self) -> list[str]:
        """List all registered plugin names.

        Returns:
            List of plugin names
        """
        return list(self._plugins.keys())

    def get_plugin_info(self, plugin_name: str) -> dict[str, Any] | None:
        """Get information about a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin information dictionary or None if not found
        """
        plugin_class = self._plugins.get(plugin_name)
        if not plugin_class:
            return None

        return {
            "name": plugin_name,
            "class": plugin_class.__name__,
            "module": plugin_class.__module__,
            "doc": plugin_class.__doc__,
            "version": getattr(plugin_class, "VERSION", "1.0.0"),
            "dependencies": getattr(plugin_class, "DEPENDENCIES", []),
        }

    async def create_instance(
        self, plugin_name: str, agent_id: str, config: dict[str, Any]
    ) -> AgentPlugin | None:
        """Create an instance of a plugin.

        Args:
            plugin_name: Name of the plugin
            agent_id: Unique ID for the agent instance
            config: Configuration for the agent

        Returns:
            Plugin instance or None if creation failed
        """
        try:
            plugin_class = self._plugins.get(plugin_name)
            if not plugin_class:
                logger.error(f"Plugin {plugin_name} not found")
                return None

            # Validate dependencies
            dependencies = config.get("dependencies", [])
            if not self._validate_dependencies(dependencies):
                logger.error(f"Dependencies not satisfied for plugin {plugin_name}")
                return None

            instance = plugin_class(agent_id, config)
            self._instances[agent_id] = instance

            logger.info(f"Created instance of plugin {plugin_name} with ID {agent_id}")
            return instance

        except Exception as e:
            logger.error(f"Failed to create instance of plugin {plugin_name}: {str(e)}")
            return None

    def get_instance(self, agent_id: str) -> AgentPlugin | None:
        """Get an agent instance by ID.

        Args:
            agent_id: ID of the agent instance

        Returns:
            Agent instance or None if not found
        """
        return self._instances.get(agent_id)

    def remove_instance(self, agent_id: str) -> None:
        """Remove an agent instance.

        Args:
            agent_id: ID of the agent instance to remove
        """
        if agent_id in self._instances:
            del self._instances[agent_id]
            logger.info(f"Removed agent instance: {agent_id}")

    def list_instances(self) -> list[str]:
        """List all agent instance IDs.

        Returns:
            List of agent instance IDs
        """
        return list(self._instances.keys())

    def _validate_dependencies(self, dependencies: list[str]) -> bool:
        """Validate that dependencies are satisfied.

        Args:
            dependencies: List of dependency names

        Returns:
            True if all dependencies are satisfied
        """
        # For now, assume all dependencies are satisfied
        # This can be expanded to check for actual dependency resolution
        for dep in dependencies:
            if dep not in self._plugins and dep not in self._instances:
                logger.warning(f"Dependency {dep} not found")
                # Continue for now, but log the warning

        return True


# Global plugin registry instance
plugin_registry = AgentPluginRegistry()
