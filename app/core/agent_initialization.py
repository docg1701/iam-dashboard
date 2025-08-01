"""Agent system initialization for startup sequence."""

import logging
from typing import Any

from app.agents.pdf_processor_agent import PDFProcessorAgent
from app.core.agent_manager import AgentManager

logger = logging.getLogger(__name__)


class AgentInitializationError(Exception):
    """Raised when agent system initialization fails."""

    pass


# Global agent manager instance
agent_manager = AgentManager()


async def initialize_agent_system() -> None:
    """Initialize the complete agent system following the architecture pattern.

    Phase 1: AgentManager initialization
    Phase 2: Agent type registration
    Phase 3: Create default instances
    Phase 4: Health checks and monitoring startup

    Raises:
        AgentInitializationError: If any phase of initialization fails
    """
    try:
        logger.info("Starting agent system initialization")

        # Phase 1: AgentManager initialization
        logger.info("Phase 1: Initializing AgentManager")
        # AgentManager is already initialized via constructor

        # Phase 2: Agent type registration
        logger.info("Phase 2: Registering agent types")
        await _register_agent_types()

        # Phase 3: Create default instances
        logger.info("Phase 3: Creating default agent instances")
        await _create_default_agents()

        # Phase 4: Health checks and start monitoring
        logger.info("Phase 4: Starting health monitoring")
        await _perform_startup_health_checks()
        await agent_manager.start_monitoring()

        logger.info("Agent system initialization completed successfully")

    except Exception as e:
        error_msg = f"Agent system initialization failed: {str(e)}"
        logger.error(error_msg)
        raise AgentInitializationError(error_msg) from e


async def _register_agent_types() -> None:
    """Register all available agent types with the AgentManager."""
    try:
        # Register PDF Processor Agent
        pdf_config = {
            "name": "PDF Processor Agent",
            "description": "Processes PDF documents with OCR and vector storage",
            "capabilities": [
                "pdf_text_extraction",
                "ocr_processing",
                "vector_embedding_generation",
                "document_storage",
                "metadata_extraction"
            ],
            "dependencies": ["postgresql", "pgvector", "gemini_api"],
            "model": "gemini-2.5-pro",
            "max_file_size_mb": 50,
            "embedding_model": "gemini-embedding-001",
            "chunk_size": 1000,
            "ocr_confidence": 50.0,
            "ocr_preprocessing": True
        }

        success = await agent_manager.load_agent(
            "pdf_processor",
            PDFProcessorAgent,
            pdf_config
        )

        if not success:
            raise AgentInitializationError("Failed to register PDF processor agent type")

        logger.info("Successfully registered pdf_processor agent type")

    except Exception as e:
        logger.error(f"Failed to register agent types: {str(e)}")
        raise


async def _create_default_agents() -> None:
    """Create default agent instances."""
    try:
        # Create default PDF processor agent
        default_pdf_config = {
            "name": "Default PDF Processor",
            "description": "Default instance for PDF document processing",
            "capabilities": [
                "pdf_text_extraction",
                "ocr_processing",
                "vector_embedding_generation",
                "document_storage",
                "metadata_extraction"
            ],
            "dependencies": ["postgresql", "pgvector", "gemini_api"],
            "model": "gemini-2.5-pro",
            "max_file_size_mb": 50,
            "embedding_model": "gemini-embedding-001",
            "chunk_size": 1000,
            "ocr_confidence": 50.0,
            "ocr_preprocessing": True
        }

        success = await agent_manager.load_agent(
            "default_pdf_processor",
            PDFProcessorAgent,
            default_pdf_config
        )

        if not success:
            raise AgentInitializationError("Failed to create default PDF processor agent")

        logger.info("Successfully created default_pdf_processor agent instance")

    except Exception as e:
        logger.error(f"Failed to create default agents: {str(e)}")
        raise


async def _perform_startup_health_checks() -> None:
    """Perform health checks on all agents during startup."""
    try:
        # Get all agents and perform health checks
        all_agents = agent_manager.get_all_agents_metadata()

        failed_agents = []
        for agent_id in all_agents:
            try:
                health_status = await agent_manager.health_check(agent_id)
                if not health_status:
                    failed_agents.append(agent_id)
                    logger.warning(f"Agent {agent_id} failed startup health check")
                else:
                    logger.info(f"Agent {agent_id} passed startup health check")
            except Exception as h_error:
                failed_agents.append(agent_id)
                logger.error(f"Health check error for agent {agent_id}: {str(h_error)}")

        if failed_agents:
            error_msg = f"Agent startup health checks failed for: {', '.join(failed_agents)}"
            raise AgentInitializationError(error_msg)

        logger.info("All agents passed startup health checks")

    except Exception as e:
        logger.error(f"Startup health checks failed: {str(e)}")
        raise


async def shutdown_agent_system() -> None:
    """Gracefully shutdown the agent system."""
    try:
        logger.info("Starting agent system shutdown")

        # Stop monitoring
        await agent_manager.stop_monitoring()

        # Get all active agents
        all_agents = agent_manager.get_all_agents_metadata()

        # Disable and unload all agents
        for agent_id in all_agents:
            try:
                await agent_manager.disable_agent(agent_id)
                await agent_manager.unload_agent(agent_id)
                logger.info(f"Successfully shutdown agent: {agent_id}")
            except Exception as e:
                logger.error(f"Error shutting down agent {agent_id}: {str(e)}")

        logger.info("Agent system shutdown completed")

    except Exception as e:
        logger.error(f"Agent system shutdown failed: {str(e)}")


def get_agent_manager() -> AgentManager:
    """Get the global agent manager instance.

    Returns:
        AgentManager: The global agent manager instance
    """
    return agent_manager


async def get_agent(agent_id: str) -> Any:
    """Get an agent instance by ID.

    Args:
        agent_id: The ID of the agent to retrieve

    Returns:
        Agent instance or None if not found
    """
    return agent_manager.get_agent(agent_id)


async def is_agent_system_healthy() -> bool:
    """Check if the agent system is healthy.

    Returns:
        bool: True if all agents are healthy, False otherwise
    """
    try:
        all_agents = agent_manager.get_all_agents_metadata()

        for agent_id in all_agents:
            if not agent_manager.is_agent_active(agent_id):
                return False

        return True
    except Exception:
        return False


async def get_system_status() -> dict[str, Any]:
    """Get comprehensive system status information.

    Returns:
        Dictionary containing system status details
    """
    try:
        all_agents = agent_manager.get_all_agents_metadata()

        status = {
            "system_healthy": await is_agent_system_healthy(),
            "total_agents": len(all_agents),
            "active_agents": 0,
            "inactive_agents": 0,
            "error_agents": 0,
            "agents": {}
        }

        for agent_id, metadata in all_agents.items():
            agent_status = {
                "name": metadata.name,
                "status": metadata.status.value,
                "health_status": metadata.health_status,
                "last_health_check": metadata.last_health_check.isoformat() if metadata.last_health_check else None,
                "error_message": metadata.error_message,
                "capabilities": metadata.capabilities,
                "created_at": metadata.created_at.isoformat()
            }

            status["agents"][agent_id] = agent_status

            # Count by status
            if metadata.status.value == "active":
                status["active_agents"] += 1
            elif metadata.status.value == "error":
                status["error_agents"] += 1
            else:
                status["inactive_agents"] += 1

        return status

    except Exception as e:
        logger.error(f"Failed to get system status: {str(e)}")
        return {
            "system_healthy": False,
            "error": str(e),
            "total_agents": 0,
            "active_agents": 0,
            "inactive_agents": 0,
            "error_agents": 0,
            "agents": {}
        }
