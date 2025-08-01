"""Authentication and session management utilities."""

import os
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from jose import JWTError, jwt
from nicegui import app

from app.models.user import UserRole

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Role permissions hierarchy
ROLE_PERMISSIONS = {
    UserRole.SYSADMIN: {
        "agent_management": ["create", "delete", "configure", "hot_deploy", "execute", "monitor"],
        "user_management": ["create", "read", "update", "delete", "manage"],
        "admin_panel": ["full_access"],
        "system_admin": ["full_access"],
        "monitoring": ["full_access"],
        "configuration": ["full_access"]
    },
    UserRole.ADMIN_USER: {
        "agent_management": ["execute", "monitor"],
        "user_management": ["read", "update"],
        "admin_panel": ["limited_access"]
    },
    UserRole.COMMON_USER: {
        "agent_management": ["execute"],
        "admin_panel": ["no_access"]
    }
}

# Endpoint role mappings
ENDPOINT_ROLE_MAPPING = {
    "/admin": [UserRole.SYSADMIN],
    "/admin/users": [UserRole.SYSADMIN],
    "/admin/system": [UserRole.SYSADMIN],
    "/admin/agents": [UserRole.SYSADMIN, UserRole.ADMIN_USER]
}


class AuthManager:
    """Authentication and session management."""

    @staticmethod
    def create_access_token(user_id: str, username: str) -> str:
        """Create a JWT access token."""
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": user_id,
            "username": username,
            "exp": expire,
            "iat": datetime.now(UTC),
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> dict[str, Any] | None:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            username = payload.get("username")

            if user_id is None or username is None:
                return None

            return {"user_id": user_id, "username": username}
        except JWTError:
            return None

    @staticmethod
    def login_user(
        user_id: str,
        username: str,
        role: str | UserRole | None = None,
        is_active: bool = True,
        is_2fa_enabled: bool = False,
    ) -> str:
        """Login a user and store session data."""
        # Create JWT token
        token = AuthManager.create_access_token(str(user_id), username)

        # Ensure role is stored as string value for session
        role_value = None
        if role:
            if isinstance(role, UserRole):
                role_value = role.value
            elif isinstance(role, str):
                role_value = role

        # Store in NiceGUI session
        app.storage.user.update(
            {
                "authenticated": True,
                "user_id": str(user_id),
                "username": username,
                "token": token,
                "role": role_value,
                "is_active": is_active,
                "is_2fa_enabled": is_2fa_enabled,
                "login_time": datetime.now(UTC).isoformat(),
            }
        )

        return token

    @staticmethod
    def logout_user() -> None:
        """Logout the current user."""
        app.storage.user.clear()

    @staticmethod
    def get_current_user() -> dict[str, Any] | None:
        """Get the current authenticated user from session."""
        if not app.storage.user.get("authenticated"):
            return None

        token = app.storage.user.get("token")
        if not token:
            return None

        # Verify token is still valid
        payload = AuthManager.verify_token(token)
        if not payload:
            # Token invalid, clear session
            AuthManager.logout_user()
            return None

        # Return basic session data (can be enhanced to fetch full user data if needed)
        return {
            "user_id": app.storage.user.get("user_id"),
            "username": app.storage.user.get("username"),
            "login_time": app.storage.user.get("login_time"),
            "role": app.storage.user.get("role", "Não disponível"),
            "is_active": app.storage.user.get("is_active", True),
            "is_2fa_enabled": app.storage.user.get("is_2fa_enabled", False),
        }

    @staticmethod
    def is_authenticated() -> bool:
        """Check if current user is authenticated."""
        return AuthManager.get_current_user() is not None

    @staticmethod
    def require_auth() -> bool:
        """Decorator/middleware to require authentication."""
        if not AuthManager.is_authenticated():
            from nicegui import ui

            ui.navigate.to("/login")
            return False
        return True

    @staticmethod
    def get_user_role(current_user: dict[str, Any] | None = None) -> UserRole | None:
        """Get the current user's role as UserRole enum."""
        if current_user is None:
            try:
                current_user = AuthManager.get_current_user()
            except RuntimeError:
                # Handle cases where NiceGUI context is not available (e.g., tests)
                return None

        if not current_user:
            return None

        role_str = current_user.get("role")
        if not role_str:
            return None

        try:
            # Handle both string values and enum names
            if isinstance(role_str, str):
                # Try to match by value first
                for role in UserRole:
                    if role.value == role_str:
                        return role
                # Try to match by name if value match fails
                return UserRole[role_str]
            return role_str if isinstance(role_str, UserRole) else None
        except (KeyError, ValueError):
            return None

    @staticmethod
    def check_permission(current_user: dict[str, Any] | None, resource: str, action: str) -> bool:
        """Check if user has permission for a specific resource and action."""
        user_role = AuthManager.get_user_role(current_user)
        if not user_role:
            return False

        role_perms = ROLE_PERMISSIONS.get(user_role, {})
        resource_perms = role_perms.get(resource, [])

        return action in resource_perms

    @staticmethod
    def check_endpoint_access(current_user: dict[str, Any] | None, endpoint: str) -> bool:
        """Check if user has access to a specific endpoint."""
        user_role = AuthManager.get_user_role(current_user)
        if not user_role:
            return False

        allowed_roles = ENDPOINT_ROLE_MAPPING.get(endpoint, [])
        return user_role in allowed_roles

    @staticmethod
    def has_admin_access(current_user: dict[str, Any] | None = None) -> bool:
        """Check if user has admin access (SYSADMIN or ADMIN_USER)."""
        user_role = AuthManager.get_user_role(current_user)
        return user_role in [UserRole.SYSADMIN, UserRole.ADMIN_USER]

    @staticmethod
    def is_sysadmin(current_user: dict[str, Any] | None = None) -> bool:
        """Check if user is a system administrator."""
        user_role = AuthManager.get_user_role(current_user)
        return user_role == UserRole.SYSADMIN

    @staticmethod
    def require_permission(resource: str, action: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to require specific permission for a function."""
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                current_user = AuthManager.get_current_user()
                if not AuthManager.check_permission(current_user, resource, action):
                    raise HTTPException(status_code=403, detail="Insufficient permissions")
                return func(*args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def require_admin() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to require admin access."""
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                current_user = AuthManager.get_current_user()
                if not AuthManager.has_admin_access(current_user):
                    raise HTTPException(status_code=403, detail="Admin access required")
                return func(*args, **kwargs)
            return wrapper
        return decorator
