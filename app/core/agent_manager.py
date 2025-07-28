"""Core agent management infrastructure for autonomous agents."""

import asyncio
import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from agno.agent import Agent

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status enumeration."""

    UNKNOWN = "unknown"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DISABLED = "disabled"


class AgentMetadata:
    """Agent metadata container."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        capabilities: list[str],
        dependencies: list[str],
        status: AgentStatus = AgentStatus.UNKNOWN,
        health_status: str | None = None,
        last_health_check: datetime | None = None,
        error_message: str | None = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.dependencies = dependencies
        self.status = status
        self.health_status = health_status
        self.last_health_check = last_health_check
        self.error_message = error_message
        self.created_at = datetime.now(UTC)


class AgentManager:
    """Central agent management system for lifecycle operations."""

    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}
        self._metadata: dict[str, AgentMetadata] = {}
        self._health_check_interval = 60  # seconds
        self._health_check_task: asyncio.Task[None] | None = None

    async def load_agent(
        self, agent_id: str, agent_class: type, config: dict[str, Any]
    ) -> bool:
        """Load and initialize an agent."""
        try:
            logger.info(f"Loading agent: {agent_id}")

            # Create agent instance
            agent = agent_class(**config)

            # Initialize agent
            await self._initialize_agent(agent_id, agent)

            # Store agent and metadata
            self._agents[agent_id] = agent

            # Create metadata
            metadata = AgentMetadata(
                agent_id=agent_id,
                name=config.get("name", agent_id),
                description=config.get("description", ""),
                capabilities=config.get("capabilities", []),
                dependencies=config.get("dependencies", []),
                status=AgentStatus.ACTIVE,
            )
            self._metadata[agent_id] = metadata

            logger.info(f"Successfully loaded agent: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to load agent {agent_id}: {str(e)}")
            self._set_agent_error(agent_id, str(e))
            return False

    async def enable_agent(self, agent_id: str) -> bool:
        """Enable an agent."""
        try:
            if agent_id not in self._agents:
                logger.error(f"Agent {agent_id} not found")
                return False

            logger.info(f"Enabling agent: {agent_id}")

            # Update status
            self._metadata[agent_id].status = AgentStatus.ACTIVE
            self._metadata[agent_id].error_message = None

            logger.info(f"Successfully enabled agent: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to enable agent {agent_id}: {str(e)}")
            self._set_agent_error(agent_id, str(e))
            return False

    async def disable_agent(self, agent_id: str) -> bool:
        """Disable an agent."""
        try:
            if agent_id not in self._agents:
                logger.error(f"Agent {agent_id} not found")
                return False

            logger.info(f"Disabling agent: {agent_id}")

            # Update status
            self._metadata[agent_id].status = AgentStatus.DISABLED

            logger.info(f"Successfully disabled agent: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to disable agent {agent_id}: {str(e)}")
            self._set_agent_error(agent_id, str(e))
            return False

    async def unload_agent(self, agent_id: str) -> bool:
        """Unload an agent from the system."""
        try:
            if agent_id not in self._agents:
                logger.error(f"Agent {agent_id} not found")
                return False

            logger.info(f"Unloading agent: {agent_id}")

            # Clean up resources
            await self._cleanup_agent(agent_id)

            # Remove from registry
            del self._agents[agent_id]
            del self._metadata[agent_id]

            logger.info(f"Successfully unloaded agent: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload agent {agent_id}: {str(e)}")
            return False

    async def health_check(self, agent_id: str) -> bool:
        """Perform health check on specific agent."""
        try:
            if agent_id not in self._agents:
                return False

            agent = self._agents[agent_id]
            metadata = self._metadata[agent_id]

            # Perform health check
            is_healthy = await self._perform_health_check(agent)

            # Update metadata
            metadata.health_status = "healthy" if is_healthy else "unhealthy"
            metadata.last_health_check = datetime.now(UTC)

            if not is_healthy and metadata.status == AgentStatus.ACTIVE:
                metadata.status = AgentStatus.ERROR
                metadata.error_message = "Health check failed"

            return is_healthy

        except Exception as e:
            logger.error(f"Health check failed for agent {agent_id}: {str(e)}")
            self._set_agent_error(agent_id, str(e))
            return False

    async def start_monitoring(self) -> None:
        """Start the agent monitoring system."""
        if self._health_check_task and not self._health_check_task.done():
            logger.warning("Monitoring already running")
            return

        logger.info("Starting agent monitoring")
        self._health_check_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self) -> None:
        """Stop the agent monitoring system."""
        if self._health_check_task:
            logger.info("Stopping agent monitoring")
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None

    def get_agent_metadata(self, agent_id: str) -> AgentMetadata | None:
        """Get metadata for a specific agent."""
        return self._metadata.get(agent_id)

    def get_all_agents_metadata(self) -> dict[str, AgentMetadata]:
        """Get metadata for all agents."""
        return self._metadata.copy()

    def get_agent(self, agent_id: str) -> Agent | None:
        """Get agent instance by ID."""
        return self._agents.get(agent_id)

    def is_agent_active(self, agent_id: str) -> bool:
        """Check if agent is active."""
        metadata = self._metadata.get(agent_id)
        return metadata is not None and metadata.status == AgentStatus.ACTIVE

    async def _initialize_agent(self, agent_id: str, agent: Agent) -> None:
        """Initialize an agent instance."""
        try:
            # Set agent status to initializing
            if agent_id in self._metadata:
                self._metadata[agent_id].status = AgentStatus.INITIALIZING

            # Perform agent-specific initialization
            # This will be expanded when we implement the AgentPlugin interface

        except Exception as e:
            logger.error(f"Failed to initialize agent {agent_id}: {str(e)}")
            raise

    async def _cleanup_agent(self, agent_id: str) -> None:
        """Clean up agent resources."""
        try:
            agent = self._agents.get(agent_id)
            if agent:
                # Perform cleanup operations
                # This will be expanded when we implement the AgentPlugin interface
                pass

        except Exception as e:
            logger.error(f"Failed to cleanup agent {agent_id}: {str(e)}")

    async def _perform_health_check(self, agent: Agent) -> bool:
        """Perform health check on an agent."""
        try:
            # Call the agent's health check method if it exists
            if hasattr(agent, "health_check") and callable(agent.health_check):
                result = await agent.health_check()
                return result if isinstance(result, bool) else True

            # Default health check - assume healthy if no method
            return True

        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return False

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop for health checks."""
        while True:
            try:
                for agent_id in list(self._agents.keys()):
                    if self.is_agent_active(agent_id):
                        await self.health_check(agent_id)

                await asyncio.sleep(self._health_check_interval)

            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(self._health_check_interval)

    def _set_agent_error(self, agent_id: str, error_message: str) -> None:
        """Set agent to error state."""
        if agent_id in self._metadata:
            self._metadata[agent_id].status = AgentStatus.ERROR
            self._metadata[agent_id].error_message = error_message
