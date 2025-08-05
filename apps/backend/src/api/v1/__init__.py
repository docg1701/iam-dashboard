"""
API v1 router module.

This module aggregates all API v1 routes and provides a single router
that can be included in the main FastAPI application.
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .clients import router as clients_router
from .permissions import router as permissions_router
from .users import router as users_router

# Create the main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth_router)
api_router.include_router(clients_router)
api_router.include_router(permissions_router)
api_router.include_router(users_router)


@api_router.get("/")
async def api_root() -> dict[str, str]:
    """API root endpoint."""
    return {
        "message": "Multi-Agent IAM Dashboard API v1",
        "version": "1.0.0",
        "docs_url": "/api/docs",
    }


@api_router.get("/status")
async def api_status() -> dict[str, str]:
    """API status endpoint."""
    return {"status": "operational", "api_version": "v1"}
