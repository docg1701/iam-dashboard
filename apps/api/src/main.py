"""
Main FastAPI application entry point.
"""

from typing import TypedDict

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from .api.v1.router import api_v1_router
from .core.config import Settings, get_settings
from .core.database import init_database
from .middleware.logging import LoggingMiddleware
from .middleware.security import (
    CORSSecurityMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    limiter,
)


class HealthFeatures(TypedDict):
    """Features configuration for health check."""

    twofa_enabled: bool
    rate_limiting: bool
    security_headers: bool
    production_mode: bool


class HealthResponse(TypedDict):
    """Health check response structure."""

    status: str
    service: str
    version: str
    features: HealthFeatures


class RateLimits(TypedDict):
    """Rate limits configuration."""

    user: str
    admin: str
    sysadmin: str


class SessionConfig(TypedDict):
    """Session configuration."""

    max_sessions: int
    timeout_minutes: int
    secure_cookies: bool
    httponly_cookies: bool


class TwoFAConfig(TypedDict):
    """2FA configuration."""

    totp_validity: int
    backup_codes: int
    setup_token_expiry: int


class SecurityInfoResponse(TypedDict):
    """Security info response structure."""

    cors_origins: list[str]
    rate_limits: RateLimits
    session_config: SessionConfig
    twofa_config: TwoFAConfig


class SecurityInfoMessageResponse(TypedDict):
    """Security info message response for production."""

    message: str


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="Multi-agent IAM Dashboard API",
        description="Revolutionary permission management system with multi-agent architecture and 2FA security",
        version="1.3.0",
        openapi_url="/api/v1/openapi.json" if settings.DEBUG else None,
        docs_url="/api/v1/docs" if settings.DEBUG else None,
        redoc_url="/api/v1/redoc" if settings.DEBUG else None,
    )

    # Configure rate limiter with Redis storage
    try:
        # Update limiter storage to use Redis
        from slowapi.extension import storage_from_string

        limiter._storage = storage_from_string(settings.EFFECTIVE_RATE_LIMIT_STORAGE)
        logger.info(
            "Rate limiter configured with Redis storage",
            storage_uri=settings.EFFECTIVE_RATE_LIMIT_STORAGE,
        )
    except Exception as e:
        logger.warning(
            "Failed to configure Redis storage for rate limiter, using memory storage",
            error=str(e),
        )

    # Add rate limiting state
    app.state.limiter = limiter

    # Exception handlers
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(
        request: Request, exc: RateLimitExceeded
    ) -> JSONResponse:
        """Handle rate limit exceeded exceptions."""
        logger.warning(
            "Rate limit exceeded",
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded. Please try again later.",
                "type": "rate_limit_exceeded",
            },
            headers={"Retry-After": "60"},
        )

    # Security middleware (applied in reverse order)
    # 1. Security headers (outermost)
    app.add_middleware(SecurityHeadersMiddleware)

    # 2. Rate limiting
    app.add_middleware(RateLimitMiddleware)

    # 3. Custom CORS with security validation
    if not settings.DEBUG:
        # Production: Use secure CORS middleware
        app.add_middleware(CORSSecurityMiddleware)
    else:
        # Development: Use standard CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=[
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-RateLimit-Reset",
            ],
        )

    # 4. Trusted hosts validation
    if settings.ALLOWED_HOSTS:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

    # 5. Custom logging middleware (innermost, closest to routes)
    app.add_middleware(LoggingMiddleware)

    # Include API routers
    app.include_router(api_v1_router, prefix="/api/v1")

    # Use lifespan for better lifecycle management (FastAPI best practice)
    @app.on_event("startup")
    async def startup_event() -> None:
        """Initialize application on startup."""
        logger.info("Starting Multi-agent IAM Dashboard API")
        await init_database()
        logger.info("Database initialization completed")

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Clean up resources on shutdown."""
        logger.info("Shutting down Multi-agent IAM Dashboard API")

    @app.get("/health")
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "iam-dashboard-api",
            "version": "1.3.0",
            "features": {
                "twofa_enabled": True,
                "rate_limiting": True,
                "security_headers": settings.ENABLE_SECURITY_HEADERS,
                "production_mode": not settings.DEBUG,
            },
        }

    @app.get("/security-info")
    async def security_info() -> SecurityInfoResponse | SecurityInfoMessageResponse:
        """Security configuration information for debugging."""
        if settings.DEBUG:
            return {
                "cors_origins": settings.EFFECTIVE_CORS_ORIGINS,
                "rate_limits": {
                    "user": str(settings.USER_RATE_LIMIT_PER_MINUTE),
                    "admin": str(settings.ADMIN_RATE_LIMIT_PER_MINUTE),
                    "sysadmin": str(settings.SYSADMIN_RATE_LIMIT_PER_MINUTE),
                },
                "session_config": {
                    "max_sessions": settings.MAX_CONCURRENT_SESSIONS,
                    "timeout_minutes": settings.SESSION_TIMEOUT_MINUTES,
                    "secure_cookies": settings.SESSION_COOKIE_SECURE,
                    "httponly_cookies": settings.SESSION_COOKIE_HTTPONLY,
                },
                "twofa_config": {
                    "totp_validity": settings.TOTP_TOKEN_VALIDITY,
                    "backup_codes": settings.BACKUP_CODES_COUNT,
                    "setup_token_expiry": settings.MFA_SETUP_TOKEN_EXPIRE_MINUTES,
                },
            }
        else:
            return {"message": "Security info only available in debug mode"}

    return app


# Create FastAPI app instance (for uvicorn)
app = create_app()
