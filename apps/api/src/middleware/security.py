"""
Security middleware for FastAPI application.

Provides rate limiting, security headers, and production security configurations.
"""

import re
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import redis.asyncio as redis
import structlog
from fastapi import HTTPException, Request, Response, status

if TYPE_CHECKING:
    from fastapi import FastAPI
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import get_settings
from ..middleware.auth import get_current_user_role
from ..models.user import UserRole

logger = structlog.get_logger(__name__)


# Rate limit storage
def get_rate_limit_storage() -> redis.Redis:  # type: ignore[type-arg]
    """Get rate limit storage backend."""
    settings = get_settings()
    return redis.from_url(settings.EFFECTIVE_RATE_LIMIT_STORAGE, decode_responses=True)


# Rate limiter with custom key function
def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit key based on user role and IP.

    Different rate limits for different user roles:
    - Regular users: 100 req/min
    - Admins: 500 req/min
    - Sysadmins: 1000 req/min
    - Anonymous: IP-based limiting at 50 req/min
    """
    # Get user role from request context
    user_role = get_current_user_role(request)

    if user_role:
        # Get user ID from auth context
        auth_context = getattr(request.state, "auth_context", None)
        user_id = auth_context.user_id if auth_context else None

        if user_id:
            # Use user ID as key for authenticated users
            role_prefix = (
                user_role.value if isinstance(user_role, UserRole) else str(user_role)
            )
            return f"user:{role_prefix}:{user_id}"

    # Fallback to IP-based limiting for anonymous users
    return f"ip:{get_remote_address(request)}"


# Create limiter instance with default memory storage
# Will be reconfigured with proper Redis storage in create_app()
limiter = Limiter(
    key_func=get_rate_limit_key,
    storage_uri="memory://",  # Default fallback
    default_limits=["100/minute"],  # Default for regular users
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security headers middleware.

    Adds security headers to all responses:
    - HSTS (HTTP Strict Transport Security)
    - CSP (Content Security Policy)
    - X-Frame-Options
    - X-Content-Type-Options
    - Referrer-Policy
    - X-XSS-Protection
    """

    def __init__(self, app: "FastAPI") -> None:
        super().__init__(app)
        self.settings = get_settings()

    async def dispatch(
        self, request: Request, call_next: Callable[..., Awaitable[Response]]
    ) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        if self.settings.ENABLE_SECURITY_HEADERS:
            # HSTS - Force HTTPS
            if not self.settings.DEBUG:
                response.headers["Strict-Transport-Security"] = (
                    f"max-age={self.settings.HSTS_MAX_AGE}; includeSubDomains; preload"
                )

            # Content Security Policy
            response.headers["Content-Security-Policy"] = self.settings.CSP_POLICY

            # Prevent clickjacking
            response.headers["X-Frame-Options"] = "DENY"

            # Prevent MIME type sniffing
            response.headers["X-Content-Type-Options"] = "nosniff"

            # Referrer Policy
            response.headers["Referrer-Policy"] = self.settings.REFERRER_POLICY

            # XSS Protection (legacy but still useful)
            response.headers["X-XSS-Protection"] = "1; mode=block"

            # Permissions Policy (feature policy)
            response.headers["Permissions-Policy"] = (
                "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), speaker=(), vibrate=()"
            )

            # Cross-Origin Resource Policy
            response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

            # Cross-Origin Embedder Policy
            response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"

            # Cross-Origin Opener Policy
            response.headers["Cross-Origin-Opener-Policy"] = "same-origin"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with role-based limits.

    Applies different rate limits based on user roles:
    - SYSADMIN: 1000 requests/minute
    - ADMIN: 500 requests/minute
    - USER: 100 requests/minute
    - Anonymous: 50 requests/minute (IP-based)
    """

    def __init__(self, app: "FastAPI") -> None:
        super().__init__(app)
        self.settings = get_settings()
        self.redis_client = get_rate_limit_storage()

        # Rate limits per role
        self.rate_limits = {
            UserRole.SYSADMIN: self.settings.SYSADMIN_RATE_LIMIT_PER_MINUTE,
            UserRole.ADMIN: self.settings.ADMIN_RATE_LIMIT_PER_MINUTE,
            UserRole.USER: self.settings.USER_RATE_LIMIT_PER_MINUTE,
            "anonymous": 50,  # For non-authenticated users
        }

    async def dispatch(
        self, request: Request, call_next: Callable[..., Awaitable[Response]]
    ) -> Response:
        """Apply rate limiting based on user role."""
        # Skip rate limiting for health checks and docs
        skip_paths = ["/health", "/docs", "/redoc", "/openapi.json"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        # Get rate limit key and determine limit
        rate_limit_key = get_rate_limit_key(request)
        user_role = get_current_user_role(request)

        # Determine rate limit based on role
        if user_role and user_role in self.rate_limits:
            rate_limit = self.rate_limits[user_role]
            limit_window = 60  # 1 minute
        else:
            rate_limit = self.rate_limits["anonymous"]
            limit_window = 60  # 1 minute

        try:
            # Check rate limit
            current_count = await self._check_rate_limit(
                rate_limit_key, rate_limit, limit_window
            )

            # Add rate limit headers
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, rate_limit - current_count)
            )
            response.headers["X-RateLimit-Reset"] = str(
                int((datetime.now() + timedelta(seconds=limit_window)).timestamp())
            )

            return response

        except RateLimitExceeded:
            logger.warning(
                "Rate limit exceeded",
                key=rate_limit_key,
                limit=rate_limit,
                path=request.url.path,
                method=request.method,
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Limit: {rate_limit} requests per minute",
                headers={
                    "X-RateLimit-Limit": str(rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(limit_window),
                },
            ) from None

    async def _check_rate_limit(self, key: str, limit: int, window: int) -> int:
        """
        Check rate limit using sliding window algorithm.

        Args:
            key: Rate limit key
            limit: Maximum requests allowed
            window: Time window in seconds

        Returns:
            Current request count in window

        Raises:
            HTTPException: If rate limit is exceeded (status 429)
        """
        now = datetime.now()
        pipeline = self.redis_client.pipeline()

        # Use sliding window with Redis sorted sets
        window_start = (now - timedelta(seconds=window)).timestamp()

        # Remove old entries
        pipeline.zremrangebyscore(key, 0, window_start)

        # Count current requests in window
        pipeline.zcard(key)

        # Add current request
        pipeline.zadd(key, {str(now.timestamp()): now.timestamp()})

        # Set expiration
        pipeline.expire(key, window + 10)

        # Execute pipeline
        results = await pipeline.execute()
        current_count = results[1] if len(results) > 1 else 0

        if current_count >= limit:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": "60"},
            )

        return current_count + 1


def get_rate_limit_by_role(role: UserRole | None) -> str:
    """
    Get rate limit string for slowapi based on user role.

    Args:
        role: User role

    Returns:
        Rate limit string (e.g., "100/minute")
    """
    settings = get_settings()

    if role == UserRole.SYSADMIN:
        return f"{settings.SYSADMIN_RATE_LIMIT_PER_MINUTE}/minute"
    elif role == UserRole.ADMIN:
        return f"{settings.ADMIN_RATE_LIMIT_PER_MINUTE}/minute"
    elif role == UserRole.USER:
        return f"{settings.USER_RATE_LIMIT_PER_MINUTE}/minute"
    else:
        # Anonymous users
        return "50/minute"


# Rate limit decorators for specific endpoints
def role_based_rate_limit() -> Callable[..., Any]:
    """
    Decorator for role-based rate limiting on specific endpoints.

    Usage:
        @app.get("/endpoint")
        @role_based_rate_limit()
        async def endpoint(request: Request):
            pass
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Awaitable[Any]]:
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            user_role = get_current_user_role(request)
            rate_limit = get_rate_limit_by_role(user_role)

            # Apply rate limit using slowapi
            limiter.limit(rate_limit)(func)

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CORS middleware with security considerations.

    Provides stricter CORS handling for production environments
    with proper origin validation and credential handling.
    """

    def __init__(self, app: "FastAPI") -> None:
        super().__init__(app)
        self.settings = get_settings()
        self.allowed_origins = set(self.settings.EFFECTIVE_CORS_ORIGINS)

        # Compile regex patterns for wildcard origins
        self.origin_patterns = []
        for origin in self.allowed_origins:
            if "*" in origin:
                # Convert wildcard to regex pattern
                pattern = origin.replace("*", r"[a-zA-Z0-9\-]+")
                self.origin_patterns.append(re.compile(f"^{pattern}$"))

    def _is_origin_allowed(self, origin: str) -> bool:
        """
        Check if origin is allowed.

        Args:
            origin: Request origin

        Returns:
            True if origin is allowed
        """
        if not origin:
            return False

        # Check exact matches first
        if origin in self.allowed_origins:
            return True

        # Check regex patterns for wildcard origins
        for pattern in self.origin_patterns:
            if pattern.match(origin):
                return True

        return False

    async def dispatch(
        self, request: Request, call_next: Callable[..., Awaitable[Response]]
    ) -> Response:
        """Handle CORS with security validation."""
        origin = request.headers.get("origin")

        # Handle preflight requests
        if request.method == "OPTIONS":
            if not origin or not self._is_origin_allowed(origin):
                # Reject preflight for unauthorized origins
                return Response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    headers={"Content-Length": "0"},
                )

            # Return successful preflight response
            response = Response(status_code=status.HTTP_200_OK)
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, PATCH, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Requested-With"
            )
            response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours
            response.headers["Vary"] = "Origin"

            return response

        # Process actual request
        response = await call_next(request)

        # Add CORS headers to response
        if origin and self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"

        return response


# Export middleware instances
security_headers_middleware = SecurityHeadersMiddleware
rate_limit_middleware = RateLimitMiddleware
cors_security_middleware = CORSSecurityMiddleware
