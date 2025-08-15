"""Middleware modules."""

from .auth import (
    AuthMiddleware,
    PermissionService,
    RequestContext,
    get_current_user,
    get_current_user_id,
    get_current_user_optional,
    get_current_user_role,
    get_request_context,
    get_user_session_info,
    invalidate_user_sessions,
    permission_service,
    require_admin,
    require_agent_permission,
    require_role,
    require_sysadmin,
    require_user,
)
from .logging import LoggingMiddleware

__all__ = [
    "AuthMiddleware",
    "RequestContext",
    "PermissionService",
    "get_current_user",
    "get_current_user_optional",
    "require_role",
    "require_sysadmin",
    "require_admin",
    "require_user",
    "require_agent_permission",
    "permission_service",
    "get_user_session_info",
    "invalidate_user_sessions",
    "get_request_context",
    "get_current_user_id",
    "get_current_user_role",
    "LoggingMiddleware",
]
