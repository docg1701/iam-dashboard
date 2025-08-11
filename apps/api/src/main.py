"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog

from .core.config import get_settings
from .core.database import init_database
from .middleware.logging import LoggingMiddleware
from .api.v1.router import api_v1_router

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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="Multi-agent IAM Dashboard API",
        description="Revolutionary permission management system with multi-agent architecture",
        version="1.0.0",
        openapi_url="/api/v1/openapi.json" if settings.DEBUG else None,
        docs_url="/api/v1/docs" if settings.DEBUG else None,
        redoc_url="/api/v1/redoc" if settings.DEBUG else None,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )
    
    # Configure trusted hosts
    if settings.ALLOWED_HOSTS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )
    
    # Add custom logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Include API routers
    app.include_router(api_v1_router, prefix="/api/v1")
    
    # Use lifespan for better lifecycle management (FastAPI best practice)
    @app.on_event("startup")
    async def startup_event():
        """Initialize application on startup."""
        logger.info("Starting Multi-agent IAM Dashboard API")
        await init_database()
        logger.info("Database initialization completed")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up resources on shutdown."""
        logger.info("Shutting down Multi-agent IAM Dashboard API")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "iam-dashboard-api"}
    
    return app

# Create FastAPI app instance (for uvicorn)
app = create_app()