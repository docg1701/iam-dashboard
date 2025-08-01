"""Agent management API endpoints."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.agent_initialization import get_agent_manager, get_system_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentHealthResponse(BaseModel):
    """Response model for agent health check."""

    agent_id: str
    status: str
    health_status: str | None
    last_health_check: str | None
    error_message: str | None


class AgentCreateRequest(BaseModel):
    """Request model for creating an agent."""

    agent_type: str
    agent_id: str
    config: dict[str, Any] | None = None


class AgentExecuteRequest(BaseModel):
    """Request model for executing an agent."""

    input_data: dict[str, Any]


class SystemStatusResponse(BaseModel):
    """Response model for system status."""

    system_healthy: bool
    total_agents: int
    active_agents: int
    inactive_agents: int
    error_agents: int
    agents: dict[str, dict[str, Any]]


@router.get("/")
async def list_agents() -> dict[str, Any]:
    """List all registered agents with their metadata."""
    try:
        agent_manager = get_agent_manager()
        all_agents = agent_manager.get_all_agents_metadata()

        agents_data = {}
        for agent_id, metadata in all_agents.items():
            agents_data[agent_id] = {
                "name": metadata.name,
                "description": metadata.description,
                "status": metadata.status.value,
                "health_status": metadata.health_status,
                "last_health_check": metadata.last_health_check.isoformat() if metadata.last_health_check else None,
                "capabilities": metadata.capabilities,
                "dependencies": metadata.dependencies,
                "error_message": metadata.error_message,
                "created_at": metadata.created_at.isoformat()
            }

        return {
            "success": True,
            "total_agents": len(agents_data),
            "agents": agents_data
        }

    except Exception as e:
        logger.error(f"Failed to list agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}") from e


@router.get("/status")
async def get_agents_status() -> SystemStatusResponse:
    """Get comprehensive system status."""
    try:
        status = await get_system_status()
        return SystemStatusResponse(**status)

    except Exception as e:
        logger.error(f"Failed to get system status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}") from e


@router.get("/{agent_id}")
async def get_agent_details(agent_id: str) -> dict[str, Any]:
    """Get detailed information about a specific agent."""
    try:
        agent_manager = get_agent_manager()
        metadata = agent_manager.get_agent_metadata(agent_id)

        if not metadata:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        return {
            "success": True,
            "agent_id": agent_id,
            "name": metadata.name,
            "description": metadata.description,
            "status": metadata.status.value,
            "health_status": metadata.health_status,
            "last_health_check": metadata.last_health_check.isoformat() if metadata.last_health_check else None,
            "capabilities": metadata.capabilities,
            "dependencies": metadata.dependencies,
            "error_message": metadata.error_message,
            "created_at": metadata.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent details for {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent details: {str(e)}") from e


@router.get("/{agent_id}/health")
async def check_agent_health(agent_id: str) -> AgentHealthResponse:
    """Perform health check on a specific agent."""
    try:
        agent_manager = get_agent_manager()
        metadata = agent_manager.get_agent_metadata(agent_id)

        if not metadata:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # Perform health check
        await agent_manager.health_check(agent_id)

        # Get updated metadata after health check
        updated_metadata = agent_manager.get_agent_metadata(agent_id)

        return AgentHealthResponse(
            agent_id=agent_id,
            status=updated_metadata.status.value,
            health_status=updated_metadata.health_status,
            last_health_check=updated_metadata.last_health_check.isoformat() if updated_metadata.last_health_check else None,
            error_message=updated_metadata.error_message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed for agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}") from e


@router.post("/{agent_id}/execute")
async def execute_agent(agent_id: str, request: AgentExecuteRequest) -> dict[str, Any]:
    """Execute an agent with provided input data."""
    try:
        agent_manager = get_agent_manager()

        # Check if agent exists and is active
        if not agent_manager.is_agent_active(agent_id):
            raise HTTPException(
                status_code=400,
                detail=f"Agent {agent_id} is not active or does not exist"
            )

        # Get the agent instance
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # Execute the agent - this will depend on the specific agent implementation
        # For now, we'll return a placeholder response
        logger.info(f"Executing agent {agent_id} with input data")

        return {
            "success": True,
            "agent_id": agent_id,
            "execution_status": "completed",
            "message": f"Agent {agent_id} executed successfully",
            "input_data": request.input_data,
            "result": "Agent execution placeholder - implement specific agent logic"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent execution failed for {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}") from e


@router.post("/{agent_id}/enable")
async def enable_agent(agent_id: str) -> dict[str, Any]:
    """Enable a specific agent."""
    try:
        agent_manager = get_agent_manager()

        success = await agent_manager.enable_agent(agent_id)

        if success:
            return {
                "success": True,
                "message": f"Agent {agent_id} enabled successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to enable agent {agent_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to enable agent: {str(e)}") from e


@router.post("/{agent_id}/disable")
async def disable_agent(agent_id: str) -> dict[str, Any]:
    """Disable a specific agent."""
    try:
        agent_manager = get_agent_manager()

        success = await agent_manager.disable_agent(agent_id)

        if success:
            return {
                "success": True,
                "message": f"Agent {agent_id} disabled successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to disable agent {agent_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to disable agent: {str(e)}") from e


@router.delete("/{agent_id}")
async def unload_agent(agent_id: str) -> dict[str, Any]:
    """Unload a specific agent from the system."""
    try:
        agent_manager = get_agent_manager()

        success = await agent_manager.unload_agent(agent_id)

        if success:
            return {
                "success": True,
                "message": f"Agent {agent_id} unloaded successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to unload agent {agent_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unload agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to unload agent: {str(e)}") from e
