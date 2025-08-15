"""
Authentication service with JWT, bcrypt, and TOTP support.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import TypedDict

import pyotp
import redis
import structlog
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..core.config import get_settings


class TokenPayload(TypedDict):
    """JWT token payload structure."""

    sub: str
    role: str
    exp: float
    iat: float
    type: str
    jti: str | None


logger = structlog.get_logger(__name__)

# Password hashing context with bcrypt 12 rounds as per security requirements
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# JWT Bearer security
security = HTTPBearer()


class AuthService:
    """Authentication service handling JWT tokens, password hashing, and TOTP."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._redis_client: redis.Redis | None = None  # type: ignore[type-arg]

    @property
    def redis_client(self) -> redis.Redis:  # type: ignore[type-arg]
        """Lazy Redis connection to avoid connection issues on import."""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                self.settings.REDIS_URL,
                decode_responses=True,
                max_connections=20,  # Connection pooling
                retry_on_timeout=True,
            )
        return self._redis_client

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt with 12 rounds."""
        hashed = pwd_context.hash(password)
        return str(hashed)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return bool(pwd_context.verify(plain_password, hashed_password))

    def generate_totp_secret(self) -> str:
        """Generate a new TOTP secret for 2FA setup."""
        return pyotp.random_base32()

    def generate_totp_qr_url(self, email: str, secret: str) -> str:
        """Generate TOTP QR code URL for 2FA setup."""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(email, issuer_name="IAM Dashboard")

    def verify_totp(self, secret: str, token: str, window: int = 1) -> bool:
        """
        Verify TOTP token with 30-second window tolerance.
        Window of 1 allows for ±30 seconds (total 60 seconds).
        """
        if not secret or not token:
            return False

        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=window)

    def create_access_token(
        self, user_id: str, user_role: str, expires_delta: timedelta | None = None
    ) -> str:
        """Create JWT access token with 1-hour expiration."""
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(
                minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES or 60
            )

        to_encode = {
            "sub": str(user_id),
            "role": user_role,
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": "access",
        }

        encoded_jwt = jwt.encode(
            to_encode, self.settings.SECRET_KEY, algorithm=self.settings.ALGORITHM
        )

        # Store token in Redis for session tracking
        self._store_user_session(user_id, encoded_jwt, expire)

        return str(encoded_jwt)

    def create_refresh_token(
        self, user_id: str, expires_delta: timedelta | None = None
    ) -> str:
        """Create JWT refresh token with 30-day expiration."""
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(
                days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS or 30
            )

        # Generate unique JTI for refresh token tracking
        jti = str(uuid.uuid4())

        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": "refresh",
            "jti": jti,
        }

        encoded_jwt = jwt.encode(
            to_encode, self.settings.SECRET_KEY, algorithm=self.settings.ALGORITHM
        )

        # Store refresh token JTI in Redis
        self.redis_client.setex(
            f"refresh_token:{jti}",
            int(expire.timestamp() - datetime.now(UTC).timestamp()),
            str(user_id),
        )

        return str(encoded_jwt)

    def verify_token(self, token: str) -> TokenPayload:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, self.settings.SECRET_KEY, algorithms=[self.settings.ALGORITHM]
            )

            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token validation failed",
                )

            # Check if token is blacklisted (for logout)
            if self.redis_client.exists(f"blacklisted_token:{token}"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                )

            return payload  # type: ignore

        except JWTError as e:
            logger.error("JWT verification failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed",
            ) from e

    async def refresh_access_token(self, refresh_token: str) -> tuple[str, str]:
        """
        Refresh access token using refresh token.
        Returns new access token and new refresh token (automatic rotation).
        """
        try:
            payload = jwt.decode(
                refresh_token,
                self.settings.SECRET_KEY,
                algorithms=[self.settings.ALGORITHM],
            )

            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )

            user_id = payload.get("sub")
            jti = payload.get("jti")

            if not user_id or not jti:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

            # Check if refresh token JTI exists in Redis
            stored_user_id = self.redis_client.get(f"refresh_token:{jti}")
            if not stored_user_id or stored_user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token not found or invalid",
                )

            # Get user role from database with proper async handling
            user_role = await self._get_user_role_from_db(user_id)

            # Create new tokens
            new_access_token = self.create_access_token(user_id, user_role)
            new_refresh_token = self.create_refresh_token(user_id)

            # Invalidate old refresh token
            self.redis_client.delete(f"refresh_token:{jti}")

            return new_access_token, new_refresh_token

        except JWTError as e:
            logger.error("Refresh token verification failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            ) from e

    def blacklist_token(self, token: str) -> None:
        """Blacklist token for logout functionality."""
        try:
            payload = jwt.decode(
                token, self.settings.SECRET_KEY, algorithms=[self.settings.ALGORITHM]
            )

            exp = payload.get("exp")
            if exp:
                # Store token in blacklist until expiration
                ttl = exp - datetime.now(UTC).timestamp()
                if ttl > 0:
                    self.redis_client.setex(
                        f"blacklisted_token:{token}", int(ttl), "blacklisted"
                    )

        except JWTError:
            # If token is invalid, no need to blacklist
            pass

    def _store_user_session(self, user_id: str, token: str, expire: datetime) -> None:
        """Store user session in Redis for concurrent session tracking."""
        session_key = f"user_session:{user_id}"

        # Get current sessions
        current_sessions = self.redis_client.smembers(session_key)
        current_sessions_list = list(current_sessions)

        # Limit to 5 concurrent sessions per user as per requirements
        if len(current_sessions_list) >= 5:
            # Remove oldest session (simple FIFO approach)
            oldest_session = current_sessions_list[0]
            self.redis_client.srem(session_key, oldest_session)
            # Blacklist the old token
            self.redis_client.setex(
                f"blacklisted_token:{oldest_session}",
                3600,  # 1 hour TTL
                "session_limit_exceeded",
            )

        # Add new session
        self.redis_client.sadd(session_key, token)

        # Set expiration for the session set
        ttl = int(expire.timestamp() - datetime.now(UTC).timestamp())
        self.redis_client.expire(session_key, ttl)

    def logout_user(self, token: str, user_id: str) -> None:
        """Logout user by blacklisting token and removing from sessions."""
        # Blacklist the token
        self.blacklist_token(token)

        # Remove token from user sessions
        session_key = f"user_session:{user_id}"
        self.redis_client.srem(session_key, token)

        logger.info("User logged out successfully", user_id=user_id)

    def logout_all_sessions(self, user_id: str) -> None:
        """Logout user from all sessions."""
        session_key = f"user_session:{user_id}"

        # Get all user sessions
        sessions = self.redis_client.smembers(session_key)

        # Blacklist all tokens
        for token_bytes in sessions:
            token_str = (
                token_bytes if isinstance(token_bytes, str) else str(token_bytes)
            )
            self.blacklist_token(token_str)

        # Clear session set
        self.redis_client.delete(session_key)

        logger.info(
            "User logged out from all sessions",
            user_id=user_id,
            session_count=len(sessions),
        )

    async def _get_user_role_from_db(self, user_id: str) -> str:
        """
        Get user role from database.

        Args:
            user_id: User ID string

        Returns:
            User role as string

        Raises:
            HTTPException: If user not found or database error
        """
        try:
            import uuid

            from sqlmodel import select

            from ..core.database import get_session_maker
            from ..models.user import User

            # Get database session
            session_maker = get_session_maker()
            async with session_maker() as session:
                # Query user by ID
                statement = select(User).where(
                    User.id == uuid.UUID(user_id), User.is_active
                )
                result = await session.execute(statement)
                user = result.scalar_one_or_none()

                if not user:
                    logger.error("User not found during role lookup", user_id=user_id)
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found or inactive",
                    )

                logger.debug(
                    "User role retrieved successfully",
                    user_id=user_id,
                    role=user.role.value,
                )
                return user.role.value

        except ValueError as e:
            # Invalid UUID format
            logger.error(
                "Invalid user ID format during role lookup",
                user_id=user_id,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID"
            ) from e
        except Exception as e:
            logger.error(
                "Database error during user role lookup", user_id=user_id, error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user information",
            ) from e


# Global instance
auth_service = AuthService()
