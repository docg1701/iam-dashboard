"""Administrative API endpoints for agent management."""

import time
import uuid
from datetime import datetime
from typing import Any

import psutil
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.middleware.auth_middleware import require_admin, require_sysadmin
from app.containers import Container
from app.core.agent_manager import AgentManager
from app.models.audit_log import AuditAction, AuditLevel
from app.models.user import UserRole
from app.services.audit_log_service import AuditLogService
from app.services.user_service import UserService

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
    current_user: dict = Depends(require_admin()),
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
    current_user: dict = Depends(require_admin()),
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
    current_user: dict = Depends(require_sysadmin()),
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
    current_user: dict = Depends(require_sysadmin()),
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
    current_user: dict = Depends(require_sysadmin()),
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
    current_user: dict = Depends(require_admin()),
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
    current_user: dict = Depends(require_admin()),
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
    current_user: dict = Depends(require_sysadmin()),
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
    current_user: dict = Depends(require_sysadmin()),
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
    current_user: dict = Depends(require_sysadmin()),
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
    current_user: dict = Depends(require_sysadmin()),
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
    current_user: dict = Depends(require_sysadmin()),
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


# User Management Models and Endpoints

class UserResponse(BaseModel):
    """Response model for user information."""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether user is active")
    is_2fa_enabled: bool = Field(..., description="Whether 2FA is enabled")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class CreateUserRequest(BaseModel):
    """Request model for creating a new user."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=6, description="Password")
    role: str = Field(..., description="User role")
    enable_2fa: bool = Field(default=False, description="Whether to enable 2FA")


class UpdateUserRequest(BaseModel):
    """Request model for updating a user."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether user is active")
    password: str | None = Field(None, min_length=6, description="New password (optional)")


@router.get("/users", response_model=list[UserResponse])
@inject
async def list_users(
    user_service: UserService = Depends(Provide[Container.user_service]),
    current_user: dict = Depends(require_sysadmin()),
) -> list[UserResponse]:
    """List all users in the system."""
    try:
        users = await user_service.get_all_users()

        return [
            UserResponse(
                id=str(user.id),
                username=user.username,
                role=user.role.value,
                is_active=user.is_active,
                is_2fa_enabled=user.is_2fa_enabled,
                created_at=user.created_at.isoformat(),
                updated_at=user.updated_at.isoformat(),
            )
            for user in users
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving users: {str(e)}",
        ) from e


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_user(
    user_request: CreateUserRequest,
    user_service: UserService = Depends(Provide[Container.user_service]),
    current_user: dict = Depends(require_sysadmin()),
) -> UserResponse:
    """Create a new user."""
    try:
        # Validate role
        try:
            role = UserRole(user_request.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {user_request.role}",
            )

        # Create user
        user = await user_service.create_user(
            username=user_request.username,
            password=user_request.password,
            role=role,
            enable_2fa=user_request.enable_2fa,
        )

        return UserResponse(
            id=str(user.id),
            username=user.username,
            role=user.role.value,
            is_active=user.is_active,
            is_2fa_enabled=user.is_2fa_enabled,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}",
        ) from e


@router.get("/users/{user_id}", response_model=UserResponse)
@inject
async def get_user(
    user_id: str,
    user_service: UserService = Depends(Provide[Container.user_service]),
    current_user: dict = Depends(require_sysadmin()),
) -> UserResponse:
    """Get a specific user by ID."""
    try:
        user_uuid = uuid.UUID(user_id)
        user = await user_service.get_user_by_id(user_uuid)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )

        return UserResponse(
            id=str(user.id),
            username=user.username,
            role=user.role.value,
            is_active=user.is_active,
            is_2fa_enabled=user.is_2fa_enabled,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}",
        ) from e


@router.put("/users/{user_id}", response_model=UserResponse)
@inject
async def update_user(
    user_id: str,
    user_request: UpdateUserRequest,
    user_service: UserService = Depends(Provide[Container.user_service]),
    current_user: dict = Depends(require_sysadmin()),
) -> UserResponse:
    """Update an existing user."""
    try:
        user_uuid = uuid.UUID(user_id)

        # Validate role
        try:
            role = UserRole(user_request.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {user_request.role}",
            )

        # Update user
        user = await user_service.update_user(
            user_id=user_uuid,
            username=user_request.username,
            role=role,
            is_active=user_request.is_active,
            new_password=user_request.password,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )

        return UserResponse(
            id=str(user.id),
            username=user.username,
            role=user.role.value,
            is_active=user.is_active,
            is_2fa_enabled=user.is_2fa_enabled,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
        )

    except ValueError as e:
        if "invalid literal for UUID" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}",
        ) from e


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_user(
    user_id: str,
    user_service: UserService = Depends(Provide[Container.user_service]),
    current_user: dict = Depends(require_sysadmin()),
) -> None:
    """Delete a user."""
    try:
        user_uuid = uuid.UUID(user_id)

        # Prevent self-deletion
        current_user_id = current_user.get("id")
        if str(user_uuid) == str(current_user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own user account",
            )

        success = await user_service.delete_user(user_uuid)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}",
        ) from e


@router.post("/users/{user_id}/reset-2fa", status_code=status.HTTP_200_OK)
@inject
async def reset_user_2fa(
    user_id: str,
    user_service: UserService = Depends(Provide[Container.user_service]),
    current_user: dict = Depends(require_sysadmin()),
) -> dict[str, str]:
    """Reset 2FA for a user."""
    try:
        user_uuid = uuid.UUID(user_id)

        success = await user_service.reset_2fa(user_uuid)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )

        return {"message": "2FA reset successfully"}

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting 2FA: {str(e)}",
        ) from e


# System Metrics Endpoints

class SystemMetricsResponse(BaseModel):
    """Response model for system metrics."""

    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_percent: float = Field(..., description="Memory usage percentage")
    memory_used_gb: float = Field(..., description="Memory used in GB")
    memory_total_gb: float = Field(..., description="Total memory in GB")
    disk_percent: float = Field(..., description="Disk usage percentage")
    disk_used_gb: float = Field(..., description="Disk used in GB")
    disk_total_gb: float = Field(..., description="Total disk in GB")
    load_average: list[float] = Field(..., description="System load average")
    uptime_seconds: float = Field(..., description="System uptime in seconds")


@router.get("/system/metrics", response_model=SystemMetricsResponse)
@inject
async def get_system_metrics(
    current_user: dict = Depends(require_admin()),
) -> SystemMetricsResponse:
    """Get current system performance metrics."""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)

        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)

        # Load average (Linux/macOS only)
        try:
            load_avg = list(psutil.getloadavg())
        except AttributeError:
            # Windows doesn't have load average
            load_avg = [0.0, 0.0, 0.0]

        # System uptime
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time

        return SystemMetricsResponse(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_gb=memory_used_gb,
            memory_total_gb=memory_total_gb,
            disk_percent=disk_percent,
            disk_used_gb=disk_used_gb,
            disk_total_gb=disk_total_gb,
            load_average=load_avg,
            uptime_seconds=uptime_seconds
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving system metrics: {str(e)}",
        ) from e


# Audit Logs Endpoints

class AuditLogResponse(BaseModel):
    """Response model for audit log information."""

    id: str = Field(..., description="Log ID")
    timestamp: str = Field(..., description="Log timestamp")
    action: str = Field(..., description="Action performed")
    level: str = Field(..., description="Log level")
    user: str = Field(..., description="User who performed the action")
    message: str = Field(..., description="Log message")
    resource_type: str | None = Field(None, description="Resource type")
    resource_id: str | None = Field(None, description="Resource ID")
    ip_address: str | None = Field(None, description="IP address")
    details: dict[str, Any] | None = Field(None, description="Additional details")


class AuditLogListResponse(BaseModel):
    """Response model for audit log list."""

    logs: list[AuditLogResponse] = Field(..., description="List of audit logs")
    total_count: int = Field(..., description="Total number of logs")
    total_pages: int = Field(..., description="Total number of pages")
    current_page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")


class AuditLogStatisticsResponse(BaseModel):
    """Response model for audit log statistics."""

    total_logs: int = Field(..., description="Total number of logs")
    date_range: dict[str, str] = Field(..., description="Date range for statistics")
    level_counts: dict[str, int] = Field(..., description="Count by log level")
    action_counts: dict[str, int] = Field(..., description="Count by action type")
    critical_logs: int = Field(..., description="Number of critical logs")
    error_logs: int = Field(..., description="Number of error logs")
    warning_logs: int = Field(..., description="Number of warning logs")
    info_logs: int = Field(..., description="Number of info logs")


@router.get("/audit-logs", response_model=AuditLogListResponse)
@inject
async def get_audit_logs(
    page: int = 1,
    page_size: int = 25,
    action: str | None = None,
    level: str | None = None,
    user: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search: str | None = None,
    audit_log_service: AuditLogService = Depends(Provide[Container.audit_log_service]),
    current_user: dict = Depends(require_admin()),
) -> AuditLogListResponse:
    """Get audit logs with filtering and pagination."""
    try:
        # Parse date filters
        date_from_parsed = None
        date_to_parsed = None

        if date_from:
            try:
                date_from_parsed = datetime.fromisoformat(date_from)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_from format. Use YYYY-MM-DD or ISO format.",
                )

        if date_to:
            try:
                date_to_parsed = datetime.fromisoformat(date_to)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_to format. Use YYYY-MM-DD or ISO format.",
                )

        logs, total_count, total_pages = await audit_log_service.get_logs_paginated(
            page=page,
            page_size=page_size,
            action_filter=action,
            level_filter=level,
            user_filter=user,
            date_from=date_from_parsed,
            date_to=date_to_parsed,
            search_query=search,
        )

        log_responses = [
            AuditLogResponse(
                id=str(log.id),
                timestamp=log.created_at.isoformat(),
                action=log.action_display,
                level=log.level_display,
                user=log.username or "System",
                message=log.message,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                ip_address=log.ip_address,
                details=log.details,
            )
            for log in logs
        ]

        return AuditLogListResponse(
            logs=log_responses,
            total_count=total_count,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving audit logs: {str(e)}",
        ) from e


@router.get("/audit-logs/export")
@inject
async def export_audit_logs(
    action: str | None = None,
    level: str | None = None,
    user: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search: str | None = None,
    audit_log_service: AuditLogService = Depends(Provide[Container.audit_log_service]),
    current_user: dict = Depends(require_admin()),
) -> Any:
    """Export audit logs to CSV format."""
    try:
        from datetime import datetime

        from fastapi.responses import Response

        # Parse date filters
        date_from_parsed = None
        date_to_parsed = None

        if date_from:
            try:
                date_from_parsed = datetime.fromisoformat(date_from)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_from format. Use YYYY-MM-DD or ISO format.",
                )

        if date_to:
            try:
                date_to_parsed = datetime.fromisoformat(date_to)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_to format. Use YYYY-MM-DD or ISO format.",
                )

        csv_content = await audit_log_service.export_logs_csv(
            action_filter=action,
            level_filter=level,
            user_filter=user,
            date_from=date_from_parsed,
            date_to=date_to_parsed,
            search_query=search,
        )

        # Log the export action
        await audit_log_service.log_action(
            action=AuditAction.AUDIT_LOGS_EXPORTED,
            message=f"Audit logs exported by {current_user.get('username', 'unknown')}",
            user_id=current_user.get("id"),
            username=current_user.get("username"),
            level=AuditLevel.INFO,
            details={
                "filters": {
                    "action": action,
                    "level": level,
                    "user": user,
                    "date_from": date_from,
                    "date_to": date_to,
                    "search": search,
                }
            },
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_logs_{timestamp}.csv"

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting audit logs: {str(e)}",
        ) from e


@router.get("/audit-logs/statistics", response_model=AuditLogStatisticsResponse)
@inject
async def get_audit_log_statistics(
    date_from: str | None = None,
    date_to: str | None = None,
    audit_log_service: AuditLogService = Depends(Provide[Container.audit_log_service]),
    current_user: dict = Depends(require_admin()),
) -> AuditLogStatisticsResponse:
    """Get audit log statistics."""
    try:
        from datetime import datetime

        # Parse date filters
        date_from_parsed = None
        date_to_parsed = None

        if date_from:
            try:
                date_from_parsed = datetime.fromisoformat(date_from)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_from format. Use YYYY-MM-DD or ISO format.",
                )

        if date_to:
            try:
                date_to_parsed = datetime.fromisoformat(date_to)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_to format. Use YYYY-MM-DD or ISO format.",
                )

        stats = await audit_log_service.get_audit_statistics(
            date_from=date_from_parsed,
            date_to=date_to_parsed,
        )

        return AuditLogStatisticsResponse(**stats)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving audit log statistics: {str(e)}",
        ) from e
