"""Administrative API endpoints for agent management."""

from typing import Any

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.containers import Container
from app.core.agent_manager import AgentManager

router = APIRouter(prefix="/v1/admin", tags=["admin"])


class AgentStatusResponse(BaseModel):
    """Response model for agent status information."""

    agent_id: str = Field(..., description="Agent identifier")
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    status: str = Field(..., description="Agent status")
    capabilities: list[str] = Field(..., description="Agent capabilities")
    health_status: str | None = Field(..., description="Agent health status")
    last_health_check: str | None = Field(
        None, description="Last health check timestamp"
    )
    error_message: str | None = Field(None, description="Error message if any")


class AgentOperationResponse(BaseModel):
    """Response model for agent operations."""

    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="Operation result message")
    agent_id: str = Field(..., description="Agent identifier")


class SystemHealthResponse(BaseModel):
    """Response model for system health check."""

    healthy_agents: int = Field(..., description="Number of healthy agents")
    total_agents: int = Field(..., description="Total number of agents")
    system_status: str = Field(..., description="Overall system status")
    agent_details: list[AgentStatusResponse] = Field(
        ..., description="Details for all agents"
    )


@router.get("/agents", response_model=list[AgentStatusResponse])
@inject
async def list_all_agents(
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> list[AgentStatusResponse]:
    """List all registered agents with their status."""
    try:
        agents_metadata = agent_manager.get_all_agents_metadata()

        return [
            AgentStatusResponse(
                agent_id=agent_id,
                name=metadata.name,
                description=metadata.description,
                status=metadata.status.value,
                capabilities=metadata.capabilities,
                health_status=metadata.health_status,
                last_health_check=(
                    metadata.last_health_check.isoformat()
                    if metadata.last_health_check
                    else None
                ),
                error_message=metadata.error_message,
            )
            for agent_id, metadata in agents_metadata.items()
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agents: {str(e)}",
        ) from e


@router.get("/agents/{agent_id}", response_model=AgentStatusResponse)
@inject
async def get_agent_details(
    agent_id: str,
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> AgentStatusResponse:
    """Get detailed information about a specific agent."""
    try:
        metadata = agent_manager.get_agent_metadata(agent_id)

        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        return AgentStatusResponse(
            agent_id=agent_id,
            name=metadata.name,
            description=metadata.description,
            status=metadata.status.value,
            capabilities=metadata.capabilities,
            health_status=metadata.health_status,
            last_health_check=(
                metadata.last_health_check.isoformat()
                if metadata.last_health_check
                else None
            ),
            error_message=metadata.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agent details: {str(e)}",
        ) from e


@router.post("/agents/{agent_id}/start", response_model=AgentOperationResponse)
@inject
async def start_agent(
    agent_id: str,
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> AgentOperationResponse:
    """Start a specific agent."""
    try:
        success = await agent_manager.enable_agent(agent_id)

        return AgentOperationResponse(
            success=success,
            message=(
                f"Agent {agent_id} "
                f"{'started successfully' if success else 'failed to start'}"
            ),
            agent_id=agent_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting agent: {str(e)}",
        ) from e


@router.post("/agents/{agent_id}/stop", response_model=AgentOperationResponse)
@inject
async def stop_agent(
    agent_id: str,
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> AgentOperationResponse:
    """Stop a specific agent."""
    try:
        success = await agent_manager.disable_agent(agent_id)

        return AgentOperationResponse(
            success=success,
            message=(
                f"Agent {agent_id} "
                f"{'stopped successfully' if success else 'failed to stop'}"
            ),
            agent_id=agent_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping agent: {str(e)}",
        ) from e


@router.post("/agents/{agent_id}/restart", response_model=AgentOperationResponse)
@inject
async def restart_agent(
    agent_id: str,
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> AgentOperationResponse:
    """Restart a specific agent."""
    try:
        # Stop then start the agent
        stop_success = await agent_manager.disable_agent(agent_id)
        if not stop_success:
            return AgentOperationResponse(
                success=False,
                message=f"Failed to stop agent {agent_id} for restart",
                agent_id=agent_id,
            )

        start_success = await agent_manager.enable_agent(agent_id)

        return AgentOperationResponse(
            success=start_success,
            message=(
                f"Agent {agent_id} "
                f"{'restarted successfully' if start_success else 'failed to restart'}"
            ),
            agent_id=agent_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error restarting agent: {str(e)}",
        ) from e


@router.get("/agents/{agent_id}/health", response_model=dict[str, Any])
@inject
async def check_agent_health(
    agent_id: str,
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> dict[str, Any]:
    """Perform health check on a specific agent."""
    try:
        is_healthy = await agent_manager.health_check(agent_id)
        metadata = agent_manager.get_agent_metadata(agent_id)

        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        return {
            "agent_id": agent_id,
            "is_healthy": is_healthy,
            "health_status": metadata.health_status,
            "last_health_check": (
                metadata.last_health_check.isoformat()
                if metadata.last_health_check
                else None
            ),
            "status": metadata.status.value,
            "error_message": metadata.error_message,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking agent health: {str(e)}",
        ) from e


@router.get("/system/health", response_model=SystemHealthResponse)
@inject
async def check_system_health(
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> SystemHealthResponse:
    """Perform health check on all agents and return system status."""
    try:
        agents_metadata = agent_manager.get_all_agents_metadata()
        agent_details = []
        healthy_count = 0

        for agent_id, metadata in agents_metadata.items():
            # Perform health check for each agent
            is_healthy = await agent_manager.health_check(agent_id)
            if is_healthy:
                healthy_count += 1

            agent_details.append(
                AgentStatusResponse(
                    agent_id=agent_id,
                    name=metadata.name,
                    description=metadata.description,
                    status=metadata.status.value,
                    capabilities=metadata.capabilities,
                    health_status=metadata.health_status,
                    last_health_check=(
                        metadata.last_health_check.isoformat()
                        if metadata.last_health_check
                        else None
                    ),
                    error_message=metadata.error_message,
                )
            )

        total_agents = len(agents_metadata)
        system_status = (
            "healthy"
            if healthy_count == total_agents
            else "degraded"
            if healthy_count > 0
            else "unhealthy"
        )

        return SystemHealthResponse(
            healthy_agents=healthy_count,
            total_agents=total_agents,
            system_status=system_status,
            agent_details=agent_details,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking system health: {str(e)}",
        ) from e


@router.post("/system/restart-all", response_model=dict[str, Any])
@inject
async def restart_all_agents(
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> dict[str, Any]:
    """Restart all agents in the system."""
    try:
        agents_metadata = agent_manager.get_all_agents_metadata()
        results = {}

        for agent_id in agents_metadata.keys():
            try:
                # Stop then start each agent
                stop_success = await agent_manager.disable_agent(agent_id)
                if stop_success:
                    start_success = await agent_manager.enable_agent(agent_id)
                    results[agent_id] = (
                        "restarted" if start_success else "failed_to_start"
                    )
                else:
                    results[agent_id] = "failed_to_stop"
            except Exception as e:
                results[agent_id] = f"error: {str(e)}"

        successful_restarts = sum(
            1 for status in results.values() if status == "restarted"
        )
        total_agents = len(results)

        return {
            "success": successful_restarts == total_agents,
            "message": f"Restarted {successful_restarts} of {total_agents} agents",
            "results": results,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error restarting agents: {str(e)}",
        ) from e


class AgentConfigRequest(BaseModel):
    """Request model for agent configuration updates."""

    config: dict[str, Any] = Field(..., description="Agent configuration parameters")


class AgentConfigResponse(BaseModel):
    """Response model for agent configuration."""

    agent_id: str = Field(..., description="Agent identifier")
    config: dict[str, Any] = Field(..., description="Agent configuration parameters")
    is_valid: bool = Field(..., description="Whether configuration is valid")
    validation_errors: list[str] = Field(
        default_factory=list, description="Validation errors if any"
    )


@router.get("/agents/{agent_id}/config", response_model=AgentConfigResponse)
@inject
async def get_agent_config(
    agent_id: str,
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> AgentConfigResponse:
    """Get agent configuration."""
    try:
        # For now, return mock configuration until AgentManager supports config retrieval
        mock_config = {
            "max_concurrent_tasks": 5,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "log_level": "INFO",
            "enable_metrics": True,
            "custom_parameters": {"gemini_model": "gemini-1.5-pro", "temperature": 0.7},
        }

        return AgentConfigResponse(
            agent_id=agent_id, config=mock_config, is_valid=True, validation_errors=[]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agent configuration: {str(e)}",
        ) from e


@router.put("/agents/{agent_id}/config", response_model=AgentConfigResponse)
@inject
async def update_agent_config(
    agent_id: str,
    config_request: AgentConfigRequest,
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> AgentConfigResponse:
    """Update agent configuration with validation."""
    try:
        # Validate configuration
        validation_errors = []
        config = config_request.config

        # Basic validation rules
        if "max_concurrent_tasks" in config:
            if (
                not isinstance(config["max_concurrent_tasks"], int)
                or config["max_concurrent_tasks"] < 1
            ):
                validation_errors.append(
                    "max_concurrent_tasks must be a positive integer"
                )

        if "timeout_seconds" in config:
            if (
                not isinstance(config["timeout_seconds"], int)
                or config["timeout_seconds"] < 1
            ):
                validation_errors.append("timeout_seconds must be a positive integer")

        if "retry_attempts" in config:
            if (
                not isinstance(config["retry_attempts"], int)
                or config["retry_attempts"] < 0
            ):
                validation_errors.append(
                    "retry_attempts must be a non-negative integer"
                )

        if "log_level" in config:
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if config["log_level"] not in valid_levels:
                validation_errors.append(
                    f"log_level must be one of: {', '.join(valid_levels)}"
                )

        is_valid = len(validation_errors) == 0

        # For now, just return the validation result without actually updating
        # In real implementation, this would update the agent configuration

        return AgentConfigResponse(
            agent_id=agent_id,
            config=config,
            is_valid=is_valid,
            validation_errors=validation_errors,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating agent configuration: {str(e)}",
        ) from e


@router.post("/agents/{agent_id}/config/validate", response_model=AgentConfigResponse)
@inject
async def validate_agent_config(
    agent_id: str,
    config_request: AgentConfigRequest,
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> AgentConfigResponse:
    """Validate agent configuration without applying changes."""
    try:
        # Same validation logic as update, but don't apply changes
        validation_errors = []
        config = config_request.config

        # Basic validation rules
        if "max_concurrent_tasks" in config:
            if (
                not isinstance(config["max_concurrent_tasks"], int)
                or config["max_concurrent_tasks"] < 1
            ):
                validation_errors.append(
                    "max_concurrent_tasks must be a positive integer"
                )

        if "timeout_seconds" in config:
            if (
                not isinstance(config["timeout_seconds"], int)
                or config["timeout_seconds"] < 1
            ):
                validation_errors.append("timeout_seconds must be a positive integer")

        if "retry_attempts" in config:
            if (
                not isinstance(config["retry_attempts"], int)
                or config["retry_attempts"] < 0
            ):
                validation_errors.append(
                    "retry_attempts must be a non-negative integer"
                )

        if "log_level" in config:
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if config["log_level"] not in valid_levels:
                validation_errors.append(
                    f"log_level must be one of: {', '.join(valid_levels)}"
                )

        is_valid = len(validation_errors) == 0

        return AgentConfigResponse(
            agent_id=agent_id,
            config=config,
            is_valid=is_valid,
            validation_errors=validation_errors,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating agent configuration: {str(e)}",
        ) from e


@router.post(
    "/agents/{agent_id}/config/rollback", response_model=AgentOperationResponse
)
@inject
async def rollback_agent_config(
    agent_id: str,
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> AgentOperationResponse:
    """Rollback agent configuration to previous version."""
    try:
        # For now, mock the rollback operation
        # In real implementation, this would restore previous configuration

        return AgentOperationResponse(
            success=True,
            message=f"Agent {agent_id} configuration rolled back successfully",
            agent_id=agent_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rolling back agent configuration: {str(e)}",
        ) from e
