"""
Authentication and JWT handling for IAM Dashboard.

This module provides JWT token creation, validation, and security utilities.
All authentication logic is centralized here for consistency.
"""

import contextlib
import secrets
from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import UUID

import jwt
import redis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel

from .config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer scheme for JWT tokens
security = HTTPBearer()


class TokenData(BaseModel):
    """Token payload data structure."""

    user_id: UUID
    role: str
    email: str
    session_id: str | None = None
    jti: str | None = None


class SessionData(BaseModel):
    """Session data stored in Redis."""

    user_id: str
    user_role: str
    user_email: str
    created_at: str
    last_activity: str


class TokenResponse(BaseModel):
    """Token response data structure."""

    access_token: str
    token_type: str
    expires_in: int
    session_id: str


class SecureAuthService:
    """Enhanced authentication service with session tracking and JWT blacklisting."""

    def __init__(self) -> None:
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.session_expire_hours = 24

        # Initialize Redis client
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)  # type: ignore[no-untyped-call]
            # Test connection
            self.redis_client.ping()
        except (redis.ConnectionError, redis.RedisError) as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis connection failed"
            ) from e

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a plain password."""
        return pwd_context.hash(password)

    def create_access_token(
        self, user_id: UUID, user_role: str, user_email: str, session_id: str | None = None
    ) -> TokenResponse:
        """Create secure JWT token with session tracking."""
        if session_id is None:
            session_id = secrets.token_hex(16)

        jti = secrets.token_hex(16)  # JWT ID for blacklisting
        now = datetime.utcnow()

        payload = {
            "sub": str(user_id),
            "role": user_role,
            "email": user_email,
            "session_id": session_id,
            "iat": now,
            "exp": now + timedelta(minutes=self.access_token_expire_minutes),
            "jti": jti,
        }

        access_token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        # Store session in Redis
        session_data = SessionData(
            user_id=str(user_id),
            user_role=user_role,
            user_email=user_email,
            created_at=now.isoformat(),
            last_activity=now.isoformat(),
        )

        try:
            self.redis_client.setex(
                f"session:{session_id}",
                timedelta(hours=self.session_expire_hours),
                session_data.model_dump_json(),
            )
        except redis.RedisError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Session storage failed"
            ) from e

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60,
            session_id=session_id,
        )

    def create_refresh_token(self, user_id: UUID, session_id: str) -> str:
        """Create a refresh token for token renewal."""
        payload = {
            "sub": str(user_id),
            "session_id": session_id,
            "type": "refresh",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            "jti": secrets.token_hex(16),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str, check_session: bool = True) -> TokenData:
        """Verify and decode JWT token with session validation."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and self._is_token_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            user_id = UUID(payload["sub"])
            role = payload["role"]
            email = payload["email"]
            session_id = payload.get("session_id")

            # Validate session if required
            if check_session and session_id:
                self._validate_session(session_id, str(user_id))

            return TokenData(
                user_id=user_id, role=role, email=email, session_id=session_id, jti=jti
            )

        except jwt.ExpiredSignatureError as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from err
        except (
            jwt.InvalidSignatureError,
            jwt.DecodeError,
            jwt.InvalidTokenError,
            KeyError,
            ValueError,
        ) as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from err

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Refresh an access token using a valid refresh token."""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])

            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
                )

            # Check if refresh token is blacklisted
            jti = payload.get("jti")
            if jti and self._is_token_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token has been revoked",
                )

            user_id = UUID(payload["sub"])
            session_id = payload["session_id"]

            # Validate session
            session_data = self._get_session_data(session_id)
            if not session_data or session_data.user_id != str(user_id):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
                )

            # Create new access token
            return self.create_access_token(
                user_id=user_id,
                user_role=session_data.user_role,
                user_email=session_data.user_email,
                session_id=session_id,
            )

        except jwt.ExpiredSignatureError as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            ) from err
        except (
            jwt.InvalidSignatureError,
            jwt.DecodeError,
            jwt.InvalidTokenError,
        ) as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from err

    def blacklist_token(self, jti: str, exp_timestamp: int) -> None:
        """Add a token to the blacklist."""
        if not jti:
            return

        try:
            # Store in blacklist until token would naturally expire
            ttl = max(exp_timestamp - int(datetime.utcnow().timestamp()), 0)
            if ttl > 0:
                self.redis_client.setex(f"blacklist:{jti}", ttl, "1")
        except redis.RedisError:
            # If Redis is unavailable, log the error but don't fail the logout
            pass

    def create_temp_session(self, user_id: str, user_role: str, user_email: str) -> str:
        """Create a temporary session for 2FA flow."""
        session_id = secrets.token_hex(16)

        # Create temporary session data (expires in 15 minutes)
        session_data = SessionData(
            user_id=user_id,
            user_role=user_role,
            user_email=user_email,
            created_at=datetime.utcnow().isoformat(),
            last_activity=datetime.utcnow().isoformat(),
        )

        try:
            # Store temporary session with short expiration for 2FA
            self.redis_client.setex(
                f"temp_session:{session_id}",
                timedelta(minutes=15),  # Short expiration for security
                session_data.model_dump_json(),
            )
        except redis.RedisError as err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Session storage unavailable",
            ) from err

        return session_id

    def get_temp_session(self, session_id: str) -> SessionData | None:
        """Get temporary session data."""
        try:
            session_json = self.redis_client.get(f"temp_session:{session_id}")
            if session_json:
                return SessionData.model_validate_json(session_json)
        except (redis.RedisError, ValueError):
            pass
        return None

    def revoke_temp_session(self, session_id: str) -> None:
        """Revoke a temporary session."""
        with contextlib.suppress(redis.RedisError):
            self.redis_client.delete(f"temp_session:{session_id}")

    def revoke_session(self, session_id: str) -> None:
        """Revoke a user session."""
        with contextlib.suppress(redis.RedisError):
            self.redis_client.delete(f"session:{session_id}")

    def _is_token_blacklisted(self, jti: str) -> bool:
        """Check if a token is blacklisted."""
        try:
            return bool(self.redis_client.exists(f"blacklist:{jti}"))
        except redis.RedisError:
            # If Redis is unavailable, assume token is not blacklisted
            return False

    def _validate_session(self, session_id: str, user_id: str) -> None:
        """Validate that a session exists and belongs to the user."""
        session_data = self._get_session_data(session_id)
        if not session_data or session_data.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

        # Update last activity
        try:
            session_data.last_activity = datetime.utcnow().isoformat()
            self.redis_client.setex(
                f"session:{session_id}",
                timedelta(hours=self.session_expire_hours),
                session_data.model_dump_json(),
            )
        except redis.RedisError:
            pass

    def _get_session_data(self, session_id: str) -> SessionData | None:
        """Get session data from Redis."""
        try:
            session_json = self.redis_client.get(f"session:{session_id}")
            if session_json:
                return SessionData.model_validate_json(session_json)
        except (redis.RedisError, ValueError):
            pass
        return None


# Maintain backward compatibility
AuthService = SecureAuthService


# Global auth service instance
auth_service = AuthService()


def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """
    Dependency to get current user from JWT token.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        TokenData: Decoded token data

    Raises:
        HTTPException: If token is invalid
    """
    return auth_service.verify_token(credentials.credentials)


def require_role(required_role: str) -> Callable[[TokenData], TokenData]:
    """
    Dependency factory for role-based access control.

    Args:
        required_role: Required user role

    Returns:
        Dependency function that checks user role
    """

    def check_role(token_data: TokenData) -> TokenData:
        if token_data.role not in (required_role, "sysadmin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return token_data

    return check_role


def require_any_role(required_roles: list[str]) -> Callable[[TokenData], TokenData]:
    """
    Dependency factory for multi-role access control.

    Args:
        required_roles: List of acceptable user roles

    Returns:
        Dependency function that checks user role
    """

    def check_roles(token_data: TokenData) -> TokenData:
        if token_data.role not in required_roles and token_data.role != "sysadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return token_data

    return check_roles


def require_sysadmin(token_data: TokenData = Depends(get_current_user_token)) -> TokenData:
    """
    Dependency to require sysadmin role.

    Args:
        token_data: Current user token data

    Returns:
        TokenData: Token data if user is sysadmin

    Raises:
        HTTPException: If user is not sysadmin
    """
    if token_data.role != "sysadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Sysadmin access required"
        )
    return token_data


def require_admin_or_above(token_data: TokenData = Depends(get_current_user_token)) -> TokenData:
    """
    Dependency to require admin or sysadmin role.

    Args:
        token_data: Current user token data

    Returns:
        TokenData: Token data if user is admin or sysadmin

    Raises:
        HTTPException: If user is not admin or sysadmin
    """
    if token_data.role not in ["admin", "sysadmin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return token_data


def require_authenticated(token_data: TokenData = Depends(get_current_user_token)) -> TokenData:
    """
    Dependency to require any authenticated user.

    Args:
        token_data: Current user token data

    Returns:
        TokenData: Token data for authenticated user
    """
    return token_data


def check_user_permission(user_id: UUID, required_user_id: UUID, token_data: TokenData) -> bool:
    """
    Check if user can access another user's data.

    Args:
        user_id: ID of the user being accessed
        required_user_id: ID of the user required for access
        token_data: Current user token data

    Returns:
        bool: True if access is allowed
    """
    # Sysadmin can access any user's data
    if token_data.role == "sysadmin":
        return True

    # Admin can access any regular user's data but not other admins
    if token_data.role == "admin":
        return True  # We'd need to check the target user's role in a real implementation

    # Users can only access their own data
    return token_data.user_id == user_id


def get_user_permissions(role: str) -> set[str]:
    """
    Get the set of permissions for a given role.

    Args:
        role: User role

    Returns:
        set[str]: Set of permission strings
    """
    permissions: dict[str, set[str]] = {
        "user": {
            "read:own_profile",
            "update:own_profile",
            "read:own_data",
        },
        "admin": {
            "read:own_profile",
            "update:own_profile",
            "read:own_data",
            "read:users",
            "create:users",
            "update:users",
            "read:agents",
            "manage:clients",
            "read:reports",
        },
        "sysadmin": {
            "read:own_profile",
            "update:own_profile",
            "read:own_data",
            "read:users",
            "create:users",
            "update:users",
            "delete:users",
            "read:agents",
            "create:agents",
            "update:agents",
            "delete:agents",
            "manage:clients",
            "read:reports",
            "system:config",
            "system:logs",
        },
    }

    return permissions.get(role, set())


def has_permission(token_data: TokenData, required_permission: str) -> bool:
    """
    Check if user has a specific permission.

    Args:
        token_data: Current user token data
        required_permission: Required permission string

    Returns:
        bool: True if user has permission
    """
    user_permissions = get_user_permissions(token_data.role)
    return required_permission in user_permissions


def require_permission(required_permission: str) -> Callable[[], TokenData]:
    """
    Dependency factory for permission-based access control.

    Args:
        required_permission: Required permission string

    Returns:
        Dependency function that checks user permission
    """

    def check_permission(token_data: TokenData = Depends(get_current_user_token)) -> TokenData:
        if not has_permission(token_data, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission}' required",
            )
        return token_data

    return check_permission
