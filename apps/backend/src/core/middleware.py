"""
Custom middleware for IAM Dashboard FastAPI application.

This module contains middleware for CORS, logging, security headers,
and request/response processing.
"""

import logging
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if settings.LOG_FORMAT == "text"
    else '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
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
    """Middleware for adding security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Add CSP header for production
        if settings.ENVIRONMENT == "production":
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            )

        return response


def setup_cors_middleware(app):
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


def setup_middleware(app):
    """Setup all middleware for the FastAPI application."""
    # Add custom middleware (order matters - last added is executed first)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # Setup CORS
    setup_cors_middleware(app)
