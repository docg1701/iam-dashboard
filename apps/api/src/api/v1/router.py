"""
Main API v1 router configuration.
"""
from fastapi import APIRouter
from .auth import router as auth_router

# Initialize the main API v1 router
api_v1_router = APIRouter()

# Health check endpoint
@api_v1_router.get("/health")
async def health_check():
    """API health check endpoint."""
    return {"status": "healthy", "version": "v1"}

# Include authentication router
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# TODO: Add additional routers as they are implemented
# from .clients import clients_router
# from .permissions import permissions_router
# 
# api_v1_router.include_router(clients_router, prefix="/clients", tags=["Client Management"])
# api_v1_router.include_router(permissions_router, prefix="/permissions", tags=["Permissions"])