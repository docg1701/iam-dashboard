"""Central agent registry for tracking agent metadata, capabilities, and dependencies."""

import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.agent_manager import AgentMetadata, AgentStatus

logger = logging.getLogger(__name__)


class AgentCapability:
    """Represents an agent capability."""

    def __init__(
        self,
        name: str,
        description: str = "",
        category: str = "general",
        version: str = "1.0.0",
    ):
        self.name = name
        self.description = description
        self.category = category
        self.version = version


class AgentDependency:
    """Represents an agent dependency."""

    def __init__(
        self,
        name: str,
        version_requirement: str = "*",
        required: bool = True,
        description: str = "",
    ):
        self.name = name
        self.version_requirement = version_requirement
        self.required = required
        self.description = description


class RegistryEntry:
    """Registry entry for an agent."""

    def __init__(
        self,
        agent_id: str,
        metadata: AgentMetadata,
        capabilities: list[AgentCapability] | None = None,
        dependencies: list[AgentDependency] | None = None,
    ):
        self.agent_id = agent_id
        self.metadata = metadata
        self.capabilities = capabilities or []
        self.dependencies = dependencies or []
        self.registered_at = datetime.now(UTC)
        self.last_updated = datetime.now(UTC)
        self.usage_count = 0
        self.last_used = None

    def to_dict(self) -> dict[str, Any]:
        """Convert registry entry to dictionary."""
        return {
            "agent_id": self.agent_id,
            "metadata": {
                "name": self.metadata.name,
                "description": self.metadata.description,
                "capabilities": self.metadata.capabilities,
                "dependencies": self.metadata.dependencies,
                "status": self.metadata.status.value,
                "health_status": self.metadata.health_status,
                "last_health_check": self.metadata.last_health_check.isoformat()
                if self.metadata.last_health_check
                else None,
                "error_message": self.metadata.error_message,
                "created_at": self.metadata.created_at.isoformat(),
            },
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "category": cap.category,
                    "version": cap.version,
                }
                for cap in self.capabilities
            ],
            "dependencies": [
                {
                    "name": dep.name,
                    "version_requirement": dep.version_requirement,
                    "required": dep.required,
                    "description": dep.description,
                }
                for dep in self.dependencies
            ],
            "registered_at": self.registered_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
        }


class AgentRegistry:
    """Central registry for tracking all agents and their metadata."""

    def __init__(self, persistence_path: str | None = None):
        """Initialize the agent registry.

        Args:
            persistence_path: Optional path to persist registry data
        """
        self._entries: dict[str, RegistryEntry] = {}
        self._capability_index: dict[str, set[str]] = {}  # capability -> agent_ids
        self._dependency_graph: dict[str, set[str]] = {}  # agent_id -> dependencies
        self._dependents_graph: dict[str, set[str]] = {}  # agent_id -> dependents
        self._persistence_path = persistence_path
        self._lock = asyncio.Lock()

    async def register_agent(
        self,
        agent_id: str,
        metadata: AgentMetadata,
        capabilities: list[str] | None = None,
        dependencies: list[str] | None = None,
    ) -> bool:
        """Register an agent in the registry.

        Args:
            agent_id: Unique identifier for the agent
            metadata: Agent metadata
            capabilities: List of agent capabilities
            dependencies: List of agent dependencies

        Returns:
            True if registration was successful
        """
        async with self._lock:
            try:
                logger.info(f"Registering agent: {agent_id}")

                # Create capability objects
                agent_capabilities = [
                    AgentCapability(name=cap) for cap in (capabilities or [])
                ]

                # Create dependency objects
                agent_dependencies = [
                    AgentDependency(name=dep) for dep in (dependencies or [])
                ]

                # Create registry entry
                entry = RegistryEntry(
                    agent_id=agent_id,
                    metadata=metadata,
                    capabilities=agent_capabilities,
                    dependencies=agent_dependencies,
                )

                # Validate dependencies
                if not await self._validate_dependencies(agent_id, dependencies or []):
                    logger.error(f"Dependency validation failed for agent: {agent_id}")
                    return False

                # Store entry
                self._entries[agent_id] = entry

                # Update indexes
                self._update_capability_index(agent_id, capabilities or [])
                self._update_dependency_graph(agent_id, dependencies or [])

                # Persist if configured
                await self._persist_registry()

                logger.info(f"Successfully registered agent: {agent_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to register agent {agent_id}: {str(e)}")
                return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the registry.

        Args:
            agent_id: ID of the agent to unregister

        Returns:
            True if unregistration was successful
        """
        async with self._lock:
            try:
                if agent_id not in self._entries:
                    logger.warning(f"Agent {agent_id} not found in registry")
                    return False

                logger.info(f"Unregistering agent: {agent_id}")

                # Check for dependents
                dependents = self._dependents_graph.get(agent_id, set())
                if dependents:
                    logger.warning(f"Agent {agent_id} has dependents: {dependents}")
                    # Could optionally fail here or handle dependent cleanup

                # Remove from indexes
                entry = self._entries[agent_id]
                for cap in entry.capabilities:
                    self._capability_index.get(cap.name, set()).discard(agent_id)

                # Clean up dependency graph
                if agent_id in self._dependency_graph:
                    for dep in self._dependency_graph[agent_id]:
                        self._dependents_graph.get(dep, set()).discard(agent_id)
                    del self._dependency_graph[agent_id]

                if agent_id in self._dependents_graph:
                    del self._dependents_graph[agent_id]

                # Remove entry
                del self._entries[agent_id]

                # Persist changes
                await self._persist_registry()

                logger.info(f"Successfully unregistered agent: {agent_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to unregister agent {agent_id}: {str(e)}")
                return False

    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update the status of an agent.

        Args:
            agent_id: ID of the agent
            status: New status

        Returns:
            True if update was successful
        """
        async with self._lock:
            try:
                if agent_id not in self._entries:
                    logger.error(f"Agent {agent_id} not found in registry")
                    return False

                entry = self._entries[agent_id]
                entry.metadata.status = status
                entry.last_updated = datetime.now(UTC)

                await self._persist_registry()
                return True

            except Exception as e:
                logger.error(f"Failed to update agent status for {agent_id}: {str(e)}")
                return False

    def get_agent_info(self, agent_id: str) -> RegistryEntry | None:
        """Get information about a specific agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Registry entry or None if not found
        """
        return self._entries.get(agent_id)

    def list_agents(
        self, status_filter: AgentStatus | None = None
    ) -> list[RegistryEntry]:
        """List all registered agents.

        Args:
            status_filter: Optional status filter

        Returns:
            List of registry entries
        """
        entries = list(self._entries.values())

        if status_filter:
            entries = [e for e in entries if e.metadata.status == status_filter]

        return entries

    def find_agents_by_capability(self, capability: str) -> list[str]:
        """Find agents that provide a specific capability.

        Args:
            capability: Capability name to search for

        Returns:
            List of agent IDs that provide the capability
        """
        return list(self._capability_index.get(capability, set()))

    def get_agent_dependencies(self, agent_id: str) -> list[str]:
        """Get dependencies for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            List of dependency agent IDs
        """
        return list(self._dependency_graph.get(agent_id, set()))

    def get_agent_dependents(self, agent_id: str) -> list[str]:
        """Get agents that depend on the given agent.

        Args:
            agent_id: ID of the agent

        Returns:
            List of dependent agent IDs
        """
        return list(self._dependents_graph.get(agent_id, set()))

    def get_capabilities_summary(self) -> dict[str, list[str]]:
        """Get a summary of all capabilities and their providers.

        Returns:
            Dictionary mapping capabilities to provider agent IDs
        """
        return {
            capability: list(agents)
            for capability, agents in self._capability_index.items()
        }

    def get_dependency_graph(self) -> dict[str, list[str]]:
        """Get the complete dependency graph.

        Returns:
            Dictionary mapping agent IDs to their dependencies
        """
        return {
            agent_id: list(deps) for agent_id, deps in self._dependency_graph.items()
        }

    async def validate_dependency_chain(self, agent_id: str) -> bool:
        """Validate that all dependencies in the chain are satisfied.

        Args:
            agent_id: ID of the agent to validate

        Returns:
            True if all dependencies are satisfied
        """
        visited = set()

        def _check_dependencies(current_agent_id: str) -> bool:
            if current_agent_id in visited:
                logger.error(
                    f"Circular dependency detected involving: {current_agent_id}"
                )
                return False

            visited.add(current_agent_id)

            dependencies = self._dependency_graph.get(current_agent_id, set())
            for dep in dependencies:
                if dep not in self._entries:
                    logger.error(
                        f"Missing dependency: {dep} for agent: {current_agent_id}"
                    )
                    return False

                if not _check_dependencies(dep):
                    return False

            visited.remove(current_agent_id)
            return True

        return _check_dependencies(agent_id)

    async def record_agent_usage(self, agent_id: str) -> None:
        """Record usage of an agent.

        Args:
            agent_id: ID of the agent that was used
        """
        async with self._lock:
            if agent_id in self._entries:
                entry = self._entries[agent_id]
                entry.usage_count += 1
                entry.last_used = datetime.now(UTC)

    def _update_capability_index(self, agent_id: str, capabilities: list[str]) -> None:
        """Update the capability index for an agent."""
        for capability in capabilities:
            if capability not in self._capability_index:
                self._capability_index[capability] = set()
            self._capability_index[capability].add(agent_id)

    def _update_dependency_graph(self, agent_id: str, dependencies: list[str]) -> None:
        """Update the dependency graph for an agent."""
        self._dependency_graph[agent_id] = set(dependencies)

        # Update dependents graph
        for dep in dependencies:
            if dep not in self._dependents_graph:
                self._dependents_graph[dep] = set()
            self._dependents_graph[dep].add(agent_id)

    async def _validate_dependencies(
        self, agent_id: str, dependencies: list[str]
    ) -> bool:
        """Validate that dependencies exist and don't create cycles."""
        # Check if dependencies exist (can be registered later)
        # For now, we'll allow registration even if dependencies don't exist yet

        # Check for circular dependencies
        temp_graph = self._dependency_graph.copy()
        temp_graph[agent_id] = set(dependencies)

        def _has_cycle(node: str, path: set[str]) -> bool:
            if node in path:
                return True

            path.add(node)
            for dep in temp_graph.get(node, set()):
                if _has_cycle(dep, path):
                    return True
            path.remove(node)
            return False

        return not _has_cycle(agent_id, set())

    async def _persist_registry(self) -> None:
        """Persist registry data to file if configured."""
        if not self._persistence_path:
            return

        try:
            registry_data = {
                "entries": {
                    agent_id: entry.to_dict()
                    for agent_id, entry in self._entries.items()
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }

            path = Path(self._persistence_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(registry_data, f, indent=2)

            logger.debug(f"Registry persisted to: {self._persistence_path}")

        except Exception as e:
            logger.error(f"Failed to persist registry: {str(e)}")

    async def load_registry(self) -> bool:
        """Load registry data from file if it exists.

        Returns:
            True if loading was successful
        """
        if not self._persistence_path:
            return True

        try:
            path = Path(self._persistence_path)
            if not path.exists():
                logger.info("No persisted registry found, starting with empty registry")
                return True

            with open(path, encoding="utf-8") as f:
                registry_data = json.load(f)

            # Reconstruct registry from persisted data
            # This is a simplified version - full implementation would reconstruct all objects
            logger.info(
                f"Loaded registry with {len(registry_data.get('entries', {}))} entries"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to load registry: {str(e)}")
            return False


# Global registry instance
agent_registry = AgentRegistry(persistence_path="app/data/agent_registry.json")
