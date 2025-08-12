"""
Integration example for authentication middleware.

This file demonstrates how to integrate the auth middleware into the main FastAPI application
and provides usage examples for route protection with different access levels.
"""
from typing import List
from fastapi import FastAPI, Depends, APIRouter
from fastapi.responses import JSONResponse

from ..middleware.auth import (
    AuthMiddleware,
    get_current_user,
    require_sysadmin,
    require_admin,
    require_user,
    require_agent_permission,
    get_user_session_info,
    invalidate_user_sessions,
)
from ..models.permission import AgentName


def setup_auth_middleware(app: FastAPI) -> None:
    """
    Add authentication middleware to FastAPI application.
    
    Add this to your main.py create_app() function:
    
    Example:
        from .middleware.integration_example import setup_auth_middleware
        
        def create_app() -> FastAPI:
            app = FastAPI(...)
            
            # Add other middleware first (CORS, etc.)
            
            # Add auth middleware (should be one of the last middleware added)
            setup_auth_middleware(app)
            
            return app
    """
    # Define paths that don't require authentication
    exclude_paths = [
        "/docs",
        "/redoc", 
        "/openapi.json",
        "/health",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
    ]
    
    # Add authentication middleware
    app.add_middleware(AuthMiddleware, exclude_paths=exclude_paths)


# Example router demonstrating different access levels
example_router = APIRouter(prefix="/example", tags=["example"])


@example_router.get("/public")
async def public_endpoint():
    """Public endpoint - no authentication required."""
    return {"message": "This is a public endpoint"}


@example_router.get("/user")
async def user_endpoint(current_user: dict = Depends(require_user)):
    """User endpoint - requires any authenticated user."""
    return {
        "message": "Hello authenticated user",
        "user_id": current_user["user_id"],
        "user_role": current_user["user_role"]
    }


@example_router.get("/admin")
async def admin_endpoint(current_user: dict = Depends(require_admin)):
    """Admin endpoint - requires admin role or higher."""
    return {
        "message": "Hello admin user",
        "user_id": current_user["user_id"],
        "user_role": current_user["user_role"]
    }


@example_router.get("/sysadmin")
async def sysadmin_endpoint(current_user: dict = Depends(require_sysadmin)):
    """Sysadmin endpoint - requires sysadmin role."""
    return {
        "message": "Hello system administrator",
        "user_id": current_user["user_id"], 
        "user_role": current_user["user_role"]
    }


@example_router.get("/client-management/read")
async def client_management_read(
    current_user: dict = Depends(require_agent_permission(AgentName.CLIENT_MANAGEMENT, "read"))
):
    """Client management read endpoint - requires specific agent permission."""
    return {
        "message": "Client management data",
        "user_id": current_user["user_id"],
        "permission": "client_management.read"
    }


@example_router.post("/client-management/create")
async def client_management_create(
    current_user: dict = Depends(require_agent_permission(AgentName.CLIENT_MANAGEMENT, "create"))
):
    """Client management create endpoint - requires create permission."""
    return {
        "message": "Client created successfully",
        "user_id": current_user["user_id"],
        "permission": "client_management.create"
    }


@example_router.get("/session-info")
async def get_session_info(current_user: dict = Depends(get_current_user)):
    """Get current user session information."""
    user_id = current_user["user_id"]
    session_info = await get_user_session_info(user_id)
    
    return {
        "user_id": user_id,
        "session_info": session_info
    }


@example_router.post("/logout-other-sessions")
async def logout_other_sessions(current_user: dict = Depends(get_current_user)):
    """Logout user from all sessions except current."""
    user_id = current_user["user_id"]
    current_token = current_user["token"]
    
    invalidated_count = await invalidate_user_sessions(
        user_id=user_id, 
        keep_current_token=current_token
    )
    
    return {
        "message": f"Logged out from {invalidated_count} other sessions",
        "user_id": user_id,
        "invalidated_sessions": invalidated_count
    }


# Example error handlers for authentication/authorization errors
def setup_auth_error_handlers(app: FastAPI) -> None:
    """
    Setup custom error handlers for authentication/authorization errors.
    
    Add this to your main.py create_app() function after creating the FastAPI app.
    """
    
    @app.exception_handler(401)
    async def auth_exception_handler(request, exc):
        """Handle authentication errors."""
        return JSONResponse(
            status_code=401,
            content={
                "error": "Authentication required",
                "message": "Please provide a valid access token",
                "type": "authentication_error"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    @app.exception_handler(403)
    async def authorization_exception_handler(request, exc):
        """Handle authorization errors.""" 
        return JSONResponse(
            status_code=403,
            content={
                "error": "Access forbidden", 
                "message": "Insufficient permissions for this operation",
                "type": "authorization_error"
            }
        )


# Route dependency examples for common patterns
def create_protected_routes():
    """
    Examples of different route protection patterns.
    
    Use these patterns in your actual route definitions.
    """
    
    # Pattern 1: Basic authentication required
    @example_router.get("/pattern1")
    async def basic_auth_required(current_user: dict = Depends(get_current_user)):
        return {"authenticated": True, "user": current_user}
    
    # Pattern 2: Role-based access with custom validation
    @example_router.get("/pattern2")
    async def custom_role_validation(current_user: dict = Depends(get_current_user)):
        # Custom validation logic can be added here
        if current_user["user_role"] not in ["admin", "sysadmin"]:
            return JSONResponse(status_code=403, content={"error": "Admin access required"})
        return {"message": "Admin access granted"}
    
    # Pattern 3: Agent permission with operation validation
    @example_router.get("/pattern3")
    async def agent_permission_with_validation(
        current_user: dict = Depends(require_agent_permission(AgentName.PDF_PROCESSING, "read"))
    ):
        # Additional business logic validation
        return {"message": "PDF processing access granted"}
    
    # Pattern 4: Optional authentication (for mixed public/private content)
    @example_router.get("/pattern4")
    async def optional_authentication(current_user: dict = Depends(get_current_user)):
        # This endpoint works with or without authentication
        if current_user:
            return {"message": "Hello authenticated user", "user": current_user}
        else:
            return {"message": "Hello anonymous user"}


"""
Integration checklist for adding auth middleware to your FastAPI app:

1. Import the middleware setup function:
   from .middleware.integration_example import setup_auth_middleware, setup_auth_error_handlers

2. Add to your create_app() function:
   def create_app() -> FastAPI:
       app = FastAPI(...)
       
       # Add CORS and other middleware first
       
       # Add authentication middleware (near the end)
       setup_auth_middleware(app)
       
       # Add error handlers
       setup_auth_error_handlers(app)
       
       return app

3. Use dependencies in your routes:
   from ..middleware.auth import require_user, require_admin, require_sysadmin
   
   @router.get("/protected")
   async def protected_route(current_user: dict = Depends(require_user)):
       return {"user": current_user}

4. For agent-specific permissions:
   from ..middleware.auth import require_agent_permission
   from ..models.permission import AgentName
   
   @router.get("/client-data")
   async def get_client_data(
       current_user: dict = Depends(require_agent_permission(AgentName.CLIENT_MANAGEMENT, "read"))
   ):
       return {"data": "client information"}

5. Session management:
   from ..middleware.auth import get_user_session_info, invalidate_user_sessions
   
   # Use these functions to manage user sessions programmatically
"""