"""Permission validation middleware and decorators for FastAPI."""

import asyncio
import logging
from collections.abc import Callable
from functools import wraps
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer

from src.core.exceptions import AuthorizationError
from src.models.permissions import AgentName
from src.models.user import User, UserRole
from src.services.permission_service import PermissionService

from .security import get_current_user

logger = logging.getLogger(__name__)
security = HTTPBearer()


class PermissionChecker:
    """Permission checker for FastAPI dependency injection."""

    def __init__(self, agent_name: AgentName, operation: str):
        """
        Initialize permission checker.

        Args:
            agent_name: Agent to check permissions for
            operation: Operation to check (create, read, update, delete)
        """
        self.agent_name = agent_name
        self.operation = operation

    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        permission_service: PermissionService = Depends(lambda: PermissionService()),
    ) -> User:
        """
        Check if current user has required permission.

        Args:
            current_user: Current authenticated user
            permission_service: Permission service instance

        Returns:
            User if permission check passes

        Raises:
            HTTPException: If user doesn't have required permission
        """
        try:
            has_permission = await permission_service.check_user_permission(
                current_user.user_id, self.agent_name, self.operation
            )

            if not has_permission:
                logger.warning(
                    f"Permission denied for user {current_user.user_id}: "
                    f"{self.agent_name.value}:{self.operation}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions for {self.agent_name.value} {self.operation}",
                )

            logger.debug(
                f"Permission granted for user {current_user.user_id}: "
                f"{self.agent_name.value}:{self.operation}"
            )
            return current_user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Permission check failed",
            ) from e
        finally:
            await permission_service.close()


def require_permission(agent_name: AgentName, operation: str) -> Callable:
    """
    Decorator to require specific permission for an endpoint.

    Args:
        agent_name: Agent to check permissions for
        operation: Operation to check (create, read, update, delete)

    Returns:
        FastAPI dependency that checks permissions

    Example:
        @router.post("/clients")
        @require_permission(AgentName.CLIENT_MANAGEMENT, "create")
        async def create_client(client_data: ClientCreate, user: User = Depends(get_current_user)):
            pass
    """
    return Depends(PermissionChecker(agent_name, operation))


def require_client_management_create() -> Callable:
    """Require client management create permission."""
    return require_permission(AgentName.CLIENT_MANAGEMENT, "create")


def require_client_management_read() -> Callable:
    """Require client management read permission."""
    return require_permission(AgentName.CLIENT_MANAGEMENT, "read")


def require_client_management_update() -> Callable:
    """Require client management update permission."""
    return require_permission(AgentName.CLIENT_MANAGEMENT, "update")


def require_client_management_delete() -> Callable:
    """Require client management delete permission."""
    return require_permission(AgentName.CLIENT_MANAGEMENT, "delete")


def require_pdf_processing_create() -> Callable:
    """Require PDF processing create permission."""
    return require_permission(AgentName.PDF_PROCESSING, "create")


def require_pdf_processing_read() -> Callable:
    """Require PDF processing read permission."""
    return require_permission(AgentName.PDF_PROCESSING, "read")


def require_pdf_processing_update() -> Callable:
    """Require PDF processing update permission."""
    return require_permission(AgentName.PDF_PROCESSING, "update")


def require_pdf_processing_delete() -> Callable:
    """Require PDF processing delete permission."""
    return require_permission(AgentName.PDF_PROCESSING, "delete")


def require_reports_analysis_create() -> Callable:
    """Require reports analysis create permission."""
    return require_permission(AgentName.REPORTS_ANALYSIS, "create")


def require_reports_analysis_read() -> Callable:
    """Require reports analysis read permission."""
    return require_permission(AgentName.REPORTS_ANALYSIS, "read")


def require_reports_analysis_update() -> Callable:
    """Require reports analysis update permission."""
    return require_permission(AgentName.REPORTS_ANALYSIS, "update")


def require_reports_analysis_delete() -> Callable:
    """Require reports analysis delete permission."""
    return require_permission(AgentName.REPORTS_ANALYSIS, "delete")


def require_audio_recording_create() -> Callable:
    """Require audio recording create permission."""
    return require_permission(AgentName.AUDIO_RECORDING, "create")


def require_audio_recording_read() -> Callable:
    """Require audio recording read permission."""
    return require_permission(AgentName.AUDIO_RECORDING, "read")


def require_audio_recording_update() -> Callable:
    """Require audio recording update permission."""
    return require_permission(AgentName.AUDIO_RECORDING, "update")


def require_audio_recording_delete() -> Callable:
    """Require audio recording delete permission."""
    return require_permission(AgentName.AUDIO_RECORDING, "delete")


class PermissionMiddleware:
    """Middleware for handling permission-based route protection."""

    def __init__(self, app):
        """Initialize permission middleware."""
        self.app = app

    async def __call__(self, request: Request, call_next):
        """
        Process request and check permissions if required.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response
        """
        # Add permission service to request state for easy access
        request.state.permission_service = PermissionService()

        try:
            response = await call_next(request)
            return response
        finally:
            # Ensure permission service is closed
            if hasattr(request.state, "permission_service"):
                await request.state.permission_service.close()


def check_user_permission_sync(user_id: UUID, agent_name: AgentName, operation: str) -> Callable:
    """
    Synchronous permission checker for use in non-async contexts.

    Args:
        user_id: User ID to check permissions for
        agent_name: Agent to check permissions for
        operation: Operation to check

    Returns:
        Function that performs the permission check

    Note:
        This is mainly for use in templates or other sync contexts.
        For async FastAPI endpoints, use the async versions.
    """

    def checker() -> bool:
        """Check permission synchronously (requires running event loop)."""
        async def _check():
            service = PermissionService()
            try:
                return await service.check_user_permission(user_id, agent_name, operation)
            finally:
                await service.close()

        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we can't use run_until_complete
                logger.warning(
                    "Synchronous permission check called from async context. "
                    "Use async version instead."
                )
                return False
            else:
                return loop.run_until_complete(_check())
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(_check())

    return checker


def permission_required(agent_name: AgentName, operation: str):
    """
    Function decorator for permission checking.

    Args:
        agent_name: Agent to check permissions for
        operation: Operation to check

    Returns:
        Decorator function

    Example:
        @permission_required(AgentName.CLIENT_MANAGEMENT, "create")
        async def create_client_handler(user_id: UUID, client_data: dict):
            # Function will only execute if user has permission
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id from function arguments
            user_id = None

            # Look for user_id in kwargs first
            if "user_id" in kwargs:
                user_id = kwargs["user_id"]
            # Look for user object with user_id attribute
            elif "user" in kwargs and hasattr(kwargs["user"], "user_id"):
                user_id = kwargs["user"].user_id
            # Look in args (assuming first arg might be user_id or user object)
            elif args:
                if isinstance(args[0], UUID):
                    user_id = args[0]
                elif hasattr(args[0], "user_id"):
                    user_id = args[0].user_id

            if not user_id:
                raise ValueError(
                    "Could not extract user_id from function arguments. "
                    "Ensure user_id is passed as kwarg or user object with user_id attribute."
                )

            # Check permission
            service = PermissionService()
            try:
                has_permission = await service.check_user_permission(user_id, agent_name, operation)

                if not has_permission:
                    raise AuthorizationError(
                        f"User {user_id} does not have {operation} permission for {agent_name.value}"
                    )

                return await func(*args, **kwargs)
            finally:
                await service.close()

        return wrapper

    return decorator


# Utility functions for common permission patterns
async def check_admin_or_sysadmin(user: User) -> bool:
    """
    Check if user is admin or sysadmin.

    Args:
        user: User to check

    Returns:
        True if user is admin or sysadmin
    """
    return user.role in [UserRole.ADMIN, UserRole.SYSADMIN]


async def check_sysadmin_only(user: User) -> bool:
    """
    Check if user is sysadmin.

    Args:
        user: User to check

    Returns:
        True if user is sysadmin
    """
    return user.role == UserRole.SYSADMIN


def require_admin_or_sysadmin() -> Callable:
    """
    Dependency to require admin or sysadmin role.

    Returns:
        FastAPI dependency
    """

    async def check_role(current_user: User = Depends(get_current_user)) -> User:
        if not await check_admin_or_sysadmin(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or sysadmin role required",
            )
        return current_user

    return Depends(check_role)


def require_sysadmin_only() -> Callable:
    """
    Dependency to require sysadmin role.

    Returns:
        FastAPI dependency
    """

    async def check_role(current_user: User = Depends(get_current_user)) -> User:
        if not await check_sysadmin_only(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sysadmin role required",
            )
        return current_user

    return Depends(check_role)
