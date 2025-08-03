"""
Custom middleware for IAM Dashboard FastAPI application.

This module contains middleware for CORS, logging, security headers,
authentication, rate limiting, and request/response processing.
"""

import json
import logging
import re
import time
import uuid
from collections.abc import Callable
from typing import Any, Awaitable

import redis
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .config import settings
from .security import auth_service

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if settings.LOG_FORMAT == "text"
    else '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security_audit")

# HTTP Bearer scheme for authentication middleware
security_scheme = HTTPBearer()


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication and role-based access control."""

    # Protected endpoints that require authentication
    PROTECTED_PATHS = [
        "/api/v1/users",
        "/api/v1/admin",
        "/api/v1/agents",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v1/auth/2fa",
    ]

    # Endpoints that bypass authentication
    PUBLIC_PATHS = [
        "/api/v1/auth/login",
        "/api/v1/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process authentication for protected endpoints."""
        path = request.url.path

        # Skip authentication for public endpoints
        if any(path.startswith(public_path) for public_path in self.PUBLIC_PATHS):
            return await call_next(request)

        # Check if path requires authentication
        requires_auth = any(
            path.startswith(protected_path) for protected_path in self.PROTECTED_PATHS
        )

        if requires_auth:
            try:
                # Extract token from Authorization header
                auth_header = request.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    self._log_security_event(
                        request, "MISSING_AUTH_HEADER", "No authorization header provided"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authorization header required",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                # Extract and verify token
                token = auth_header.split(" ")[1]
                token_data = auth_service.verify_token(token)

                # Add user data to request state
                request.state.user = token_data
                request.state.is_authenticated = True

                # Log successful authentication
                self._log_security_event(
                    request,
                    "AUTH_SUCCESS",
                    f"User {token_data.email} authenticated successfully",
                    {"user_id": str(token_data.user_id), "role": token_data.role},
                )

            except HTTPException as e:
                # Log authentication failure
                self._log_security_event(
                    request,
                    "AUTH_FAILURE",
                    f"Authentication failed: {e.detail}",
                    {"status_code": e.status_code},
                )
                raise

        else:
            # Mark as unauthenticated for non-protected endpoints
            request.state.user = None
            request.state.is_authenticated = False

        return await call_next(request)

    def _log_security_event(
        self,
        request: Request,
        event_type: str,
        message: str,
        extra_data: dict[str, Any] | None = None,
    ) -> None:
        """Log security events for audit purposes."""
        event_data = {
            "event_type": event_type,
            "timestamp": time.time(),
            "request_id": getattr(request.state, "request_id", "unknown"),
            "path": request.url.path,
            "method": request.method,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "message": message,
        }

        if extra_data:
            event_data.update(extra_data)

        security_logger.info(json.dumps(event_data))

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address considering proxies."""
        # Check for X-Forwarded-For header (proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in case of multiple proxies
            return forwarded_for.split(",")[0].strip()

        # Check for X-Real-IP header (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests per IP address."""

    def __init__(self, app: ASGIApp, redis_url: str | None = None, rate_limit: int = 100) -> None:
        super().__init__(app)
        self.rate_limit = rate_limit
        self.window_seconds = 60  # 1 minute window

        # Initialize Redis client for rate limiting
        try:
            self.redis_client = redis.from_url(
                redis_url or settings.REDIS_URL, decode_responses=True
            )  # type: ignore[no-untyped-call]
            self.redis_client.ping()
        except (redis.ConnectionError, redis.RedisError):
            # If Redis is unavailable, disable rate limiting
            self.redis_client = None

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Apply rate limiting based on client IP."""
        # Skip rate limiting if Redis is unavailable
        if not self.redis_client:
            return await call_next(request)

        # Get client IP for rate limiting
        client_ip = self._get_client_ip(request)

        # Check if path requires rate limiting (auth endpoints have stricter limits)
        is_auth_endpoint = request.url.path.startswith("/api/v1/auth/")
        rate_limit = 20 if is_auth_endpoint else self.rate_limit  # Stricter limit for auth

        # Create rate limit key
        rate_key = f"rate_limit:{client_ip}:{request.url.path.split('/')[1:3]}"  # Group by API version + first path segment

        try:
            # Get current request count
            current_count = self.redis_client.get(rate_key)

            if current_count is None:
                # First request in window
                self.redis_client.setex(rate_key, self.window_seconds, 1)
                remaining = rate_limit - 1
            else:
                count = int(current_count)
                if count >= rate_limit:
                    # Rate limit exceeded
                    self._log_rate_limit_exceeded(request, client_ip, count, rate_limit)
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded. Please try again later.",
                        headers={
                            "Retry-After": str(self.window_seconds),
                            "X-RateLimit-Limit": str(rate_limit),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(int(time.time()) + self.window_seconds),
                        },
                    )

                # Increment counter
                self.redis_client.incr(rate_key)
                remaining = rate_limit - count - 1

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.window_seconds)

            return response

        except redis.RedisError:
            # If Redis fails, allow request to proceed
            return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address considering proxies."""
        # Check for X-Forwarded-For header (proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Check for X-Real-IP header (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"

    def _log_rate_limit_exceeded(
        self, request: Request, client_ip: str, count: int, limit: int
    ) -> None:
        """Log rate limit exceeded events."""
        event_data = {
            "event_type": "RATE_LIMIT_EXCEEDED",
            "timestamp": time.time(),
            "client_ip": client_ip,
            "path": request.url.path,
            "method": request.method,
            "current_count": count,
            "limit": limit,
            "user_agent": request.headers.get("user-agent", "unknown"),
        }
        security_logger.warning(json.dumps(event_data))


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timer
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started - ID: {request_id}, Method: {request.method}, "
            f"URL: {request.url}, User-Agent: {request.headers.get('user-agent', 'unknown')}"
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed - ID: {request_id}, Status: {response.status_code}, "
                f"Processing Time: {process_time:.3f}s"
            )

            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time

            # Log error
            logger.error(
                f"Request failed - ID: {request_id}, Error: {str(e)}, "
                f"Processing Time: {process_time:.3f}s"
            )

            # Re-raise the exception
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding comprehensive security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)

        # Core security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Enhanced permissions policy with comprehensive restrictions
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), "
            "usb=(), magnetometer=(), gyroscope=(), speaker=(), "
            "vibrate=(), fullscreen=(), sync-xhr=()"
        )

        # Strict Transport Security (force HTTPS)
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Prevent MIME type sniffing
        response.headers["X-Download-Options"] = "noopen"

        # Cross-Origin policies
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # Content Security Policy (CSP) - comprehensive policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https:; "
            "media-src 'self'; "
            "object-src 'none'; "
            "child-src 'none'; "
            "frame-src 'none'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self'; "
            "upgrade-insecure-requests; "
            "report-uri /api/v1/security/csp-report"
        )

        # Apply stricter CSP in production
        if settings.ENVIRONMENT == "production":
            response.headers["Content-Security-Policy"] = csp_policy
        else:
            # More permissive CSP for development
            response.headers["Content-Security-Policy-Report-Only"] = csp_policy

        # Additional security headers for sensitive endpoints
        if request.url.path.startswith("/api/v1/auth/") or request.url.path.startswith(
            "/api/v1/admin/"
        ):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for request validation and input sanitization."""

    # Suspicious patterns that might indicate malicious input
    SUSPICIOUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",  # XSS attempts
        r"javascript:",  # JavaScript protocol
        r"vbscript:",  # VBScript protocol
        r"on\w+\s*=",  # Event handlers
        r"union\s+select",  # SQL injection
        r"drop\s+table",  # SQL injection
        r"insert\s+into",  # SQL injection
        r"delete\s+from",  # SQL injection
        r"\.\./",  # Directory traversal
        r"\\x[0-9a-f]{2}",  # Hex encoding
        r"%[0-9a-f]{2}",  # URL encoding suspicious
    ]

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.SUSPICIOUS_PATTERNS]

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Validate and sanitize incoming requests."""

        # Check request size (prevent DoS via large payloads)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            self._log_security_event(
                request, "LARGE_PAYLOAD", f"Request size {content_length} exceeds limit"
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request payload too large",
            )

        # CSRF protection for state-changing requests
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            await self._validate_csrf_token(request)

        # Validate request headers for suspicious content
        await self._validate_headers(request)

        # For JSON requests, validate body content
        if request.headers.get("content-type", "").startswith("application/json"):
            await self._validate_json_body(request)

        return await call_next(request)

    async def _validate_csrf_token(self, request: Request) -> None:
        """Validate CSRF token for state-changing requests."""
        # Skip CSRF check for public authentication endpoints
        if request.url.path.startswith("/api/v1/auth/login"):
            return

        # Check for CSRF token in headers
        csrf_token = request.headers.get("X-CSRF-Token")
        origin = request.headers.get("Origin")

        # For authenticated requests, validate origin/referer
        if (hasattr(request.state, "is_authenticated") and
            request.state.is_authenticated and
            not csrf_token and
            origin):
            allowed_origins = settings.ALLOWED_ORIGINS
            if origin not in allowed_origins:
                self._log_security_event(
                    request, "CSRF_INVALID_ORIGIN", f"Invalid origin: {origin}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Invalid origin"
                )

    async def _validate_headers(self, request: Request) -> None:
        """Validate request headers for suspicious content."""
        suspicious_headers = ["User-Agent", "Referer", "X-Forwarded-For"]

        for header_name in suspicious_headers:
            header_value = request.headers.get(header_name.lower(), "")
            if self._contains_suspicious_content(header_value):
                self._log_security_event(
                    request,
                    "SUSPICIOUS_HEADER",
                    f"Suspicious content in {header_name}: {header_value[:100]}",
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request headers"
                )

    async def _validate_json_body(self, request: Request) -> None:
        """Validate JSON request body for suspicious content."""
        try:
            # Read body (this will be cached by FastAPI)
            body = await request.body()
            if body:
                body_text = body.decode("utf-8")
                if self._contains_suspicious_content(body_text):
                    self._log_security_event(
                        request,
                        "SUSPICIOUS_PAYLOAD",
                        f"Suspicious content in request body: {body_text[:100]}",
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request content"
                    )
        except UnicodeDecodeError as e:
            self._log_security_event(request, "INVALID_ENCODING", "Non-UTF-8 request body")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request encoding"
            ) from e

    def _contains_suspicious_content(self, content: str) -> bool:
        """Check if content contains suspicious patterns."""
        if not content:
            return False

        return any(pattern.search(content) for pattern in self.patterns)

    def _log_security_event(self, request: Request, event_type: str, message: str) -> None:
        """Log security validation events."""
        event_data = {
            "event_type": event_type,
            "timestamp": time.time(),
            "path": request.url.path,
            "method": request.method,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "message": message,
        }
        security_logger.warning(json.dumps(event_data))

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address considering proxies."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        return request.client.host if request.client else "unknown"


def setup_cors_middleware(app: FastAPI) -> None:
    """Configure CORS middleware with appropriate settings."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Request-ID",
        ],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )


def setup_middleware(app: FastAPI) -> None:
    """Setup all comprehensive middleware for the FastAPI application."""
    # Add custom middleware (order matters - last added is executed first)
    # Security headers should be last to ensure they're always applied
    app.add_middleware(SecurityHeadersMiddleware)

    # Request validation should come before authentication
    app.add_middleware(RequestValidationMiddleware)

    # Authentication middleware
    app.add_middleware(AuthenticationMiddleware)

    # Rate limiting should be early to prevent abuse
    app.add_middleware(
        RateLimitMiddleware, redis_url=settings.REDIS_URL, rate_limit=settings.RATE_LIMIT_PER_MINUTE
    )

    # Request logging should be first to log everything
    app.add_middleware(RequestLoggingMiddleware)

    # Setup CORS
    setup_cors_middleware(app)
