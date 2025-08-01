"""FastAPI authorization middleware for role-based access control."""

from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth import ENDPOINT_ROLE_MAPPING, AuthManager
from app.models.user import UserRole

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """FastAPI dependency to get current authenticated user."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = AuthManager.verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get additional user data from session if available
    user_data = {
        "user_id": payload["user_id"],
        "username": payload["username"],
    }

    # Try to get role and other data from NiceGUI session if available
    try:
        session_user = AuthManager.get_current_user()
        if session_user:
            user_data.update(session_user)
    except Exception:
        # If session is not available (API-only access), role will need to be
        # fetched from database or included in JWT token
        pass

    return user_data


def require_role(allowed_roles: list[UserRole]) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Dependency to require specific roles for endpoint access."""
    def role_checker(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        user_role = AuthManager.get_user_role(current_user)

        if not user_role or user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )

        return current_user

    return role_checker


def require_permission(resource: str, action: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Dependency to require specific permission for endpoint access."""
    def permission_checker(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if not AuthManager.check_permission(current_user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions for {resource}:{action}"
            )

        return current_user

    return permission_checker


def require_admin() -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Dependency to require admin access (SYSADMIN or ADMIN_USER)."""
    return require_role([UserRole.SYSADMIN, UserRole.ADMIN_USER])


def require_sysadmin() -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Dependency to require system administrator access."""
    return require_role([UserRole.SYSADMIN])


class AuthorizationMiddleware:
    """Middleware class for automatic endpoint authorization based on path."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> Any:
        """Process request and check authorization if needed."""
        # Only process HTTP requests
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        # Create a Request object from scope to get path and headers
        from starlette.requests import Request
        request = Request(scope, receive)
        path = request.url.path

        # Skip authorization for certain paths
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/login", "/health"]
        if any(path.startswith(skip_path) for skip_path in skip_paths):
            await self.app(scope, receive, send)
            return

        # Check if path requires specific role authorization
        required_roles = ENDPOINT_ROLE_MAPPING.get(path)
        if required_roles:
            # Extract token from Authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                # Send 401 response
                response = {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [
                        [b"content-type", b"application/json"],
                        [b"www-authenticate", b"Bearer"],
                    ],
                }
                await send(response)
                await send({
                    "type": "http.response.body",
                    "body": b'{"detail":"Authentication required"}',
                })
                return

            token = auth_header.split(" ")[1]
            payload = AuthManager.verify_token(token)
            if not payload:
                # Send 401 response
                response = {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [
                        [b"content-type", b"application/json"],
                        [b"www-authenticate", b"Bearer"],
                    ],
                }
                await send(response)
                await send({
                    "type": "http.response.body",
                    "body": b'{"detail":"Invalid or expired token"}',
                })
                return

            # Get user role (this might need database lookup in pure API context)
            # For now, we'll need the role to be included in the token or session
            user_data = {"user_id": payload["user_id"], "username": payload["username"]}

            try:
                session_user = AuthManager.get_current_user()
                if session_user:
                    user_data.update(session_user)
            except Exception:
                pass

            user_role = AuthManager.get_user_role(user_data)
            if not user_role or user_role not in required_roles:
                # Send 403 response
                required_roles_str = [role.value for role in required_roles]
                response = {
                    "type": "http.response.start",
                    "status": 403,
                    "headers": [[b"content-type", b"application/json"]],
                }
                await send(response)
                await send({
                    "type": "http.response.body",
                    "body": f'{{"detail":"Access denied. Required roles: {required_roles_str}"}}'.encode(),
                })
                return

        # If authorization passes or is not required, continue to the app
        await self.app(scope, receive, send)
