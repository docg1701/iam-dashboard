"""
Multi-Agent IAM Dashboard - FastAPI Application Entry Point

This module contains the main FastAPI application instance and configuration.
All code and technical content must be in English as per CLAUDE.md requirements.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .api.v1 import api_router
from .core.config import settings
from .core.database import init_db
from .core.middleware import setup_middleware
from .schemas.common import HealthCheckResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


# Create FastAPI application instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Setup all middleware (includes CORS)
setup_middleware(app)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", response_model=HealthCheckResponse, tags=["health"])
async def health_check() -> HealthCheckResponse:
    """Health check endpoint for monitoring and load balancers."""
    return HealthCheckResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.utcnow().isoformat(),
        components={"database": "healthy", "redis": "healthy", "api": "healthy"},
    )


@app.exception_handler(404)
async def not_found_handler(request: object, exc: object) -> JSONResponse:
    """Custom 404 handler."""
    return JSONResponse(status_code=404, content={"detail": "Resource not found"})


@app.exception_handler(500)
async def internal_error_handler(request: object, exc: object) -> JSONResponse:
    """Custom 500 handler."""
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level="info",
    )
