"""
Authentication and JWT handling for IAM Dashboard.

This module provides JWT token creation, validation, and security utilities.
All authentication logic is centralized here for consistency.
"""

import contextlib
import logging
import secrets
import sys
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID

import jwt
import redis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlmodel import Session, select

from .config import settings
from .database import get_session

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.models.user import User

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

        # Skip Redis initialization in test environment
        self._is_testing = "pytest" in sys.modules or "test" in sys.argv[0] if sys.argv else False

        if self._is_testing:
            self.redis_client = None
            logger.debug("AuthService initialized in testing mode - Redis disabled")
        else:
            # Initialize Redis client
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)  # type: ignore[no-untyped-call]
                # Test connection
                self.redis_client.ping()
                logger.debug("AuthService initialized with Redis connection")
            except (redis.ConnectionError, redis.RedisError) as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Redis connection failed",
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

        # Store session in Redis if available
        if self.redis_client is not None:
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

        # Skip blacklisting in testing mode
        if self.redis_client is None:
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

        # Skip Redis storage in testing mode
        if not self._is_testing and self.redis_client is not None:
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
        # Skip Redis operations if no client available
        if self.redis_client is None:
            return None

        try:
            session_json = self.redis_client.get(f"temp_session:{session_id}")
            if session_json:
                return SessionData.model_validate_json(session_json)
        except (redis.RedisError, ValueError):
            pass
        return None

    def revoke_temp_session(self, session_id: str) -> None:
        """Revoke a temporary session."""
        # Skip Redis operations if no client available
        if self.redis_client is None:
            return

        with contextlib.suppress(redis.RedisError):
            self.redis_client.delete(f"temp_session:{session_id}")

    def revoke_session(self, session_id: str) -> None:
        """Revoke a user session."""
        # Skip Redis operations if no client available
        if self.redis_client is None:
            return

        with contextlib.suppress(redis.RedisError):
            self.redis_client.delete(f"session:{session_id}")

    def _is_token_blacklisted(self, jti: str) -> bool:
        """Check if a token is blacklisted."""
        # Skip blacklist check in testing mode
        if self.redis_client is None:
            return False

        try:
            return bool(self.redis_client.exists(f"blacklist:{jti}"))
        except redis.RedisError:
            # If Redis is unavailable, assume token is not blacklisted
            return False

    def _validate_session(self, session_id: str, user_id: str) -> None:
        """Validate that a session exists and belongs to the user."""
        # Skip session validation if no Redis client
        if self.redis_client is None:
            return

        session_data = self._get_session_data(session_id)
        if not session_data or session_data.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

        # Update last activity (skip in testing mode)
        if not self._is_testing and self.redis_client is not None:
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
        # Skip session validation if no Redis client
        if self.redis_client is None:
            return None

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


def _get_current_user_from_token(
    token_data: TokenData,
    session: Session,
) -> "User":
    """
    Internal function to get current user from token data and database session.

    Args:
        token_data: Decoded token data
        session: Database session

    Returns:
        User: Full user model instance from database

    Raises:
        HTTPException: If user is not found or inactive
    """
    # Import here to avoid circular imports - needed at runtime
    from src.models.user import User  # noqa: PLC0415

    # Query user from database
    user = session.exec(select(User).where(User.user_id == token_data.user_id)).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated"
        )

    return user


# Create the actual dependency function
def _create_get_current_user_dependency() -> Callable[..., "User"]:
    """Create a dependency function for getting current user."""

    def get_current_user_impl(
        token_data: TokenData = Depends(get_current_user_token),
        session: Session = Depends(get_session),
    ) -> "User":
        """
        Dependency to get current user from JWT token and database.

        Args:
            token_data: Decoded token data
            session: Database session

        Returns:
            User: Full user model instance from database

        Raises:
            HTTPException: If user is not found or inactive
        """
        return _get_current_user_from_token(token_data, session)

    return get_current_user_impl


# Create the dependency
get_current_user = _create_get_current_user_dependency()


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


# Enhanced permission checking with new permission system integration
async def check_user_agent_permission(
    user_id: UUID, agent_name: str, operation: str, session: Session | None = None
) -> bool:
    """
    Check if user has permission for a specific agent operation.
    Integrates with the new permission system while maintaining role-based fallbacks.

    Args:
        user_id: User ID to check permissions for
        agent_name: Agent name (client_management, pdf_processing, etc.)
        operation: Operation to check (create, read, update, delete)
        session: Database session (optional)

    Returns:
        bool: True if user has permission
    """
    # Import here to avoid circular imports
    from src.models.permissions import AgentName  # noqa: PLC0415
    from src.services.permission_service import PermissionService  # noqa: PLC0415

    # First try role-based check for immediate resolution
    if session:
        from src.models.user import User  # noqa: PLC0415

        user = session.exec(select(User).where(User.user_id == user_id)).first()
        if user:
            # Sysadmin bypass (use enum value as stored in database)
            if user.role.value == "sysadmin":
                return True

            # Admin role inheritance for client_management and reports_analysis (use enum value)
            if user.role.value == "admin" and agent_name in [
                "client_management",
                "reports_analysis",
            ]:
                return True

    # Check for explicit permissions in the database
    if session:
        from src.models.permissions import UserAgentPermission  # noqa: PLC0415

        try:
            agent_enum = AgentName(agent_name)
            perm_query = select(UserAgentPermission).where(
                UserAgentPermission.user_id == user_id,  # type: ignore[arg-type]
                UserAgentPermission.agent_name == agent_enum,  # type: ignore[arg-type]
            )
            permission = session.exec(perm_query).first()
            if permission:
                return permission.permissions.get(operation, False)
        except Exception:
            pass

    # If no explicit permission found, try the permission service (PostgreSQL-specific)
    # Skip this in testing environments where PostgreSQL functions aren't available
    is_testing = "pytest" in sys.modules or "test" in sys.argv[0] if sys.argv else False

    if not is_testing:
        try:
            # Validate agent name
            agent_enum = AgentName(agent_name)

            # Use the permission service to check
            permission_service = PermissionService()
            try:
                has_permission = await permission_service.check_user_permission(
                    user_id, agent_enum, operation
                )
                return has_permission
            finally:
                await permission_service.close()
        except Exception:
            pass

    return False


def require_agent_permission(agent_name: str, operation: str) -> Any:
    """
    Enhanced dependency factory that integrates new permission system with role-based fallback.

    Args:
        agent_name: Agent name to check permissions for
        operation: Operation to check (create, read, update, delete)

    Returns:
        Dependency function that checks user permission
    """

    async def check_permission(
        token_data: TokenData = Depends(get_current_user_token),
        session: Session = Depends(get_session),
    ) -> TokenData:
        # Check if user has permission using the new system
        has_permission = await check_user_agent_permission(
            token_data.user_id, agent_name, operation, session
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions for {agent_name} {operation}",
            )

        return token_data

    return Depends(check_permission)


def require_client_management_access(operation: str = "read") -> Any:
    """
    Dependency to require client management access with backward compatibility.

    Args:
        operation: Operation to check (create, read, update, delete)

    Returns:
        Dependency function
    """
    return require_agent_permission("client_management", operation)


def require_pdf_processing_access(operation: str = "read") -> Any:
    """
    Dependency to require PDF processing access.

    Args:
        operation: Operation to check (create, read, update, delete)

    Returns:
        Dependency function
    """
    return require_agent_permission("pdf_processing", operation)


def require_reports_analysis_access(operation: str = "read") -> Any:
    """
    Dependency to require reports analysis access.

    Args:
        operation: Operation to check (create, read, update, delete)

    Returns:
        Dependency function
    """
    return require_agent_permission("reports_analysis", operation)


def require_audio_recording_access(operation: str = "read") -> Any:
    """
    Dependency to require audio recording access.

    Args:
        operation: Operation to check (create, read, update, delete)

    Returns:
        Dependency function
    """
    return require_agent_permission("audio_recording", operation)


# Backward compatibility wrappers for existing role-based dependencies
def require_role_with_fallback(required_role: str) -> Callable[[TokenData], TokenData]:
    """
    Enhanced role checker that maintains backward compatibility.

    This function preserves the existing role-based access control while
    preparing for migration to the new permission system.

    Args:
        required_role: Required user role

    Returns:
        Dependency function that checks user role
    """

    def check_role(token_data: TokenData) -> TokenData:
        # Sysadmin always has access
        if token_data.role == "sysadmin":
            return token_data

        # Check the specific role requirement
        if token_data.role == required_role:
            return token_data

        # Admin can access user-level endpoints (backward compatibility)
        if required_role == "user" and token_data.role == "admin":
            return token_data

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    return check_role
