"""
API v1 router module.

This module aggregates all API v1 routes and provides a single router
that can be included in the main FastAPI application.
"""

from fastapi import APIRouter

# Create the main API router
api_router = APIRouter()


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
