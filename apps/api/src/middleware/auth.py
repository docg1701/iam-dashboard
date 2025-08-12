"""
Authentication and authorization middleware for FastAPI with JWT and permission validation.

This module provides:
- JWT token verification middleware  
- Permission validation using role-based access control
- Route dependencies for different access levels (sysadmin, admin, user)
- Redis session tracking with concurrent session limits
- Request context for current user and permissions
"""
import uuid
from typing import Optional, List, Dict, Any, Callable, Annotated
from datetime import datetime, timezone

from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from ..services.auth_service import auth_service
from ..models.user import User, UserRole
from ..models.permission import AgentName, UserAgentPermission
from ..core.config import get_settings

logger = structlog.get_logger(__name__)

# HTTP Bearer security instance
security = HTTPBearer()


class RequestContext:
    """Request context to store current user and permissions information."""
    
    def __init__(self):
        self.user_id: Optional[str] = None
        self.user_role: Optional[UserRole] = None
        self.permissions: Dict[AgentName, UserAgentPermission] = {}
        self.token: Optional[str] = None
        self.session_id: Optional[str] = None


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for automatic JWT token validation.
    
    This middleware handles:
    - Automatic token extraction and validation for protected routes
    - Request context population with user information
    - Session tracking and concurrent session management
    - Proper error handling and logging
    """
    
    def __init__(self, app, exclude_paths: List[str] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs", 
            "/redoc", 
            "/openapi.json", 
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """Process request with authentication validation."""
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Initialize request context
        request.state.auth_context = RequestContext()
        
        # Extract token from Authorization header
        authorization = request.headers.get("authorization")
        if not authorization or not authorization.startswith("Bearer "):
            # For non-excluded paths, token is required
            logger.warning(
                "Missing or invalid authorization header", 
                path=request.url.path,
                method=request.method
            )
            return await call_next(request)
        
        token = authorization.split(" ")[1]
        
        try:
            # Verify token and populate context
            payload = auth_service.verify_token(token)
            
            user_id = payload.get("sub")
            user_role = payload.get("role")
            
            # Populate request context
            request.state.auth_context.user_id = user_id
            request.state.auth_context.user_role = UserRole(user_role) if user_role else None
            request.state.auth_context.token = token
            request.state.auth_context.session_id = str(uuid.uuid4())
            
            logger.info(
                "Request authenticated",
                user_id=user_id,
                user_role=user_role,
                path=request.url.path,
                method=request.method
            )
            
        except HTTPException as e:
            logger.warning(
                "Authentication failed - invalid token",
                path=request.url.path,
                method=request.method,
                status_code=e.status_code,
                error_type="authentication_failed"
            )
            # Continue without authentication context for optional auth routes
            pass
        except Exception as e:
            logger.error(
                "Unexpected authentication error - service degraded",
                path=request.url.path,
                method=request.method,
                error=str(e),
                error_type="auth_service_error"
            )
            # Continue without authentication context but log for monitoring
            pass
        
        return await call_next(request)


# Dependency injection functions for route protection
async def get_current_user_optional(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)] = None
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication dependency.
    Returns user information if valid token is provided, None otherwise.
    """
    if not credentials:
        return None
    
    try:
        payload = auth_service.verify_token(credentials.credentials)
        return {
            "user_id": payload.get("sub"),
            "user_role": payload.get("role"),
            "token": credentials.credentials
        }
    except HTTPException:
        return None


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> Dict[str, Any]:
    """
    Required authentication dependency.
    Returns user information or raises HTTP 401 if invalid/missing token.
    """
    try:
        payload = auth_service.verify_token(credentials.credentials)
        user_data = {
            "user_id": payload.get("sub"),
            "user_role": payload.get("role"),
            "token": credentials.credentials
        }
        
        logger.debug(
            "User authenticated via dependency",
            user_id=user_data["user_id"],
            user_role=user_data["user_role"]
        )
        
        return user_data
        
    except HTTPException as e:
        logger.error(
            "Authentication dependency failed",
            error=str(e.detail)
        )
        raise e


async def require_role(required_role: UserRole):
    """
    Factory function to create role-based access dependencies.
    
    Args:
        required_role: Minimum required user role
        
    Returns:
        Dependency function that validates user has required role
    """
    async def role_dependency(
        current_user: Annotated[Dict[str, Any], Depends(get_current_user)]
    ) -> Dict[str, Any]:
        user_role = current_user.get("user_role")
        
        if not user_role:
            logger.error(
                "Missing user role in token",
                user_id=current_user.get("user_id")
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user role"
            )
        
        # Check role hierarchy: sysadmin > admin > user
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.ADMIN: 2, 
            UserRole.SYSADMIN: 3
        }
        
        user_role_enum = UserRole(user_role)
        user_level = role_hierarchy.get(user_role_enum, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            logger.warning(
                "Insufficient role privileges",
                user_id=current_user.get("user_id"),
                user_role=user_role,
                required_role=required_role.value
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role.value}"
            )
        
        logger.debug(
            "Role access granted",
            user_id=current_user.get("user_id"),
            user_role=user_role,
            required_role=required_role.value
        )
        
        return current_user
    
    return role_dependency


# Convenience dependencies for common role requirements
async def require_sysadmin(
    current_user: Annotated[Dict[str, Any], Depends(require_role(UserRole.SYSADMIN))]
) -> Dict[str, Any]:
    """Dependency requiring sysadmin role."""
    return current_user


async def require_admin(
    current_user: Annotated[Dict[str, Any], Depends(require_role(UserRole.ADMIN))]
) -> Dict[str, Any]:
    """Dependency requiring admin role or higher."""
    return current_user


async def require_user(
    current_user: Annotated[Dict[str, Any], Depends(require_role(UserRole.USER))]
) -> Dict[str, Any]:
    """Dependency requiring user role or higher (any authenticated user)."""
    return current_user


class PermissionService:
    """
    Permission service for agent-based access control.
    
    This service will be integrated with the database layer to provide
    fine-grained permission validation for different agents and operations.
    
    TODO: Integrate with database layer for permission lookup
    """
    
    def __init__(self):
        self.settings = get_settings()
    
    async def check_agent_permission(
        self, 
        user_id: str, 
        agent_name: AgentName, 
        operation: str
    ) -> bool:
        """
        Check if user has permission for specific agent operation.
        
        Args:
            user_id: User UUID
            agent_name: Agent name enum
            operation: Operation type (create, read, update, delete)
            
        Returns:
            True if user has permission, False otherwise
            
        TODO: Implement database lookup for user permissions
        """
        # Placeholder implementation - will be replaced with database lookup
        logger.debug(
            "Permission check requested",
            user_id=user_id,
            agent_name=agent_name.value,
            operation=operation
        )
        
        # For now, return True for basic operations
        # This will be replaced with actual permission validation
        return True
    
    async def get_user_permissions(
        self, 
        user_id: str
    ) -> Dict[AgentName, UserAgentPermission]:
        """
        Get all permissions for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            Dictionary mapping agent names to permission objects
            
        TODO: Implement database lookup for all user permissions
        """
        # Placeholder implementation
        logger.debug(
            "User permissions lookup requested",
            user_id=user_id
        )
        
        # Return empty permissions for now
        return {}


# Global permission service instance
permission_service = PermissionService()


async def require_agent_permission(
    agent_name: AgentName, 
    operation: str
):
    """
    Factory function to create agent permission dependencies.
    
    Args:
        agent_name: Required agent name
        operation: Required operation (create, read, update, delete)
        
    Returns:
        Dependency function that validates user has agent permission
    """
    async def permission_dependency(
        current_user: Annotated[Dict[str, Any], Depends(get_current_user)]
    ) -> Dict[str, Any]:
        user_id = current_user.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user context"
            )
        
        # Check agent permission
        has_permission = await permission_service.check_agent_permission(
            user_id=user_id,
            agent_name=agent_name,
            operation=operation
        )
        
        if not has_permission:
            logger.warning(
                "Agent permission denied",
                user_id=user_id,
                agent_name=agent_name.value,
                operation=operation
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied for {agent_name.value} {operation}"
            )
        
        logger.debug(
            "Agent permission granted",
            user_id=user_id,
            agent_name=agent_name.value,
            operation=operation
        )
        
        return current_user
    
    return permission_dependency


# Session management functions
async def get_user_session_info(user_id: str) -> Dict[str, Any]:
    """
    Get current session information for a user.
    
    Args:
        user_id: User UUID
        
    Returns:
        Dictionary with session information
    """
    try:
        session_key = f"user_session:{user_id}"
        sessions = auth_service.redis_client.smembers(session_key)
        
        return {
            "user_id": user_id,
            "active_sessions": len(sessions),
            "max_sessions": 5,
            "session_tokens": list(sessions)
        }
        
    except Exception as e:
        logger.error(
            "Failed to get user session info",
            user_id=user_id,
            error=str(e)
        )
        return {
            "user_id": user_id,
            "active_sessions": 0,
            "max_sessions": 5,
            "session_tokens": []
        }


async def invalidate_user_sessions(user_id: str, keep_current_token: Optional[str] = None) -> int:
    """
    Invalidate all user sessions except optionally keeping current token.
    
    Args:
        user_id: User UUID
        keep_current_token: Optional token to keep active
        
    Returns:
        Number of sessions invalidated
    """
    try:
        session_key = f"user_session:{user_id}"
        sessions = auth_service.redis_client.smembers(session_key)
        
        invalidated_count = 0
        for token in sessions:
            if token != keep_current_token:
                # Blacklist the token
                auth_service.blacklist_token(token)
                # Remove from session set
                auth_service.redis_client.srem(session_key, token)
                invalidated_count += 1
        
        logger.info(
            "User sessions invalidated",
            user_id=user_id,
            invalidated_count=invalidated_count,
            kept_current=keep_current_token is not None
        )
        
        return invalidated_count
        
    except Exception as e:
        logger.error(
            "Failed to invalidate user sessions",
            user_id=user_id,
            error=str(e)
        )
        return 0


# Request context helper functions
def get_request_context(request: Request) -> Optional[RequestContext]:
    """
    Get authentication context from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        RequestContext if available, None otherwise
    """
    return getattr(request.state, "auth_context", None)


def get_current_user_id(request: Request) -> Optional[str]:
    """
    Get current user ID from request context.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User ID if available, None otherwise
    """
    context = get_request_context(request)
    return context.user_id if context else None


def get_current_user_role(request: Request) -> Optional[UserRole]:
    """
    Get current user role from request context.
    
    Args:
        request: FastAPI request object
        
    Returns:
        UserRole if available, None otherwise
    """
    context = get_request_context(request)
    return context.user_role if context else None