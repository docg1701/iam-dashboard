"""
Example usage of security features for 2FA authentication system.

This file demonstrates how to use the new security middleware,
rate limiting, and cookie management in API routes.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from ..core.config import get_settings
from ..middleware.auth import UserDict, get_current_user, require_sysadmin
from ..middleware.security import get_rate_limit_by_role, limiter
from ..models.user import UserRole
from ..utils.cookie_utils import cookie_manager

# Example router
router = APIRouter(prefix="/api/v1/security-examples", tags=["Security Examples"])


# Rate limiting key function
def get_user_rate_limit_key(request: Request) -> str:
    """Get rate limit key based on authenticated user."""
    # This would get the user from the request context
    client_host = request.client.host if request.client else "unknown"
    return f"user:example:{client_host}"


@router.get("/rate-limit-test")
@limiter.limit("5/minute")  # Fixed rate limit for this endpoint
async def rate_limit_test(request: Request) -> dict[str, Any]:
    """
    Endpoint to test rate limiting functionality.
    Limited to 5 requests per minute regardless of user role.
    """
    return {
        "message": "Rate limiting is working!",
        "timestamp": datetime.now().isoformat(),
        "client_ip": request.client.host if request.client else "unknown",
    }


@router.get("/role-based-rate-limit")
async def role_based_rate_limit_test(
    request: Request, current_user: UserDict = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Endpoint demonstrating role-based rate limiting.
    Rate limits are applied based on user role by the middleware.
    """
    user_role_value = current_user.get("user_role")
    user_role = UserRole(user_role_value) if user_role_value else None
    rate_limit = get_rate_limit_by_role(user_role)

    return {
        "message": "Role-based rate limiting active",
        "user_role": user_role.value if user_role else "unknown",
        "rate_limit": rate_limit,
        "user_id": current_user.get("user_id"),
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/secure-login-example")
@limiter.limit("10/minute")  # Login attempts are more strictly limited
async def secure_login_example(request: Request) -> JSONResponse:
    """
    Example of how to implement secure login with httpOnly cookies.

    This demonstrates:
    1. Rate limiting for login attempts
    2. Setting secure httpOnly cookies
    3. Proper security headers
    """
    # In a real implementation, you would:
    # 1. Validate credentials
    # 2. Generate JWT tokens
    # 3. Set tokens in httpOnly cookies

    # Mock tokens for demonstration
    mock_access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.example"
    mock_refresh_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.refresh"

    # Create secure response with cookies
    response_data: dict[str, str | int | bool | list[str] | dict[str, str]] = {
        "message": "Login successful",
        "user_id": "example-user-id",
        "requires_2fa": True,  # In real app, check user's 2FA status
        "session_expires": datetime.now().isoformat(),
    }

    # Use cookie manager to create secure response
    response = cookie_manager.create_secure_response(
        content=response_data,
        status_code=200,
        access_token=mock_access_token,
        refresh_token=mock_refresh_token,
    )

    return response


@router.post("/secure-logout-example")
async def secure_logout_example(request: Request) -> JSONResponse:
    """
    Example of secure logout that clears httpOnly cookies.
    """
    response_data = {
        "message": "Logout successful",
        "timestamp": datetime.now().isoformat(),
    }

    # Create response and clear cookies
    response = JSONResponse(content=response_data)
    cookie_manager.clear_auth_cookies(response)

    return response


@router.get("/sysadmin-only")
async def sysadmin_only_endpoint(
    current_user: UserDict = Depends(require_sysadmin),
) -> dict[str, Any]:
    """
    Example endpoint that requires sysadmin role.
    Demonstrates role-based access control.
    """
    return {
        "message": "You have sysadmin access!",
        "user_id": current_user.get("user_id"),
        "user_role": current_user.get("user_role"),
        "high_privilege_data": "This data is only for sysadmins",
    }


@router.get("/security-headers-test")
async def security_headers_test() -> dict[str, Any]:
    """
    Endpoint to test security headers.
    Check the response headers to see security headers added by middleware.
    """
    return {
        "message": "Check the response headers for security configurations",
        "expected_headers": [
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Referrer-Policy",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
        ],
    }


@router.get("/2fa-setup-example")
async def two_factor_setup_example(
    request: Request, current_user: UserDict = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Example endpoint for 2FA setup workflow.
    In a real implementation, this would generate TOTP secrets and QR codes.
    """
    settings = get_settings()

    return {
        "message": "2FA setup initiated",
        "user_id": current_user.get("user_id"),
        "totp_config": {
            "issuer": settings.TOTP_ISSUER_NAME,
            "validity_window": settings.TOTP_TOKEN_VALIDITY,
            "backup_codes_count": settings.BACKUP_CODES_COUNT,
            "setup_token_expiry": settings.MFA_SETUP_TOKEN_EXPIRE_MINUTES,
        },
        "next_steps": [
            "Generate TOTP secret",
            "Create QR code",
            "Verify TOTP token",
            "Generate backup codes",
            "Store 2FA configuration",
        ],
    }


@router.get("/session-info")
async def session_info_example(
    request: Request, current_user: UserDict = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Example endpoint showing session management information.
    """
    settings = get_settings()

    # Extract token from cookies (if using httpOnly cookies)
    token_from_cookies = cookie_manager.get_token_from_cookies(request)

    return {
        "message": "Session information",
        "user_id": current_user.get("user_id"),
        "user_role": current_user.get("user_role"),
        "has_cookie_token": token_from_cookies is not None,
        "session_config": {
            "max_concurrent_sessions": settings.MAX_CONCURRENT_SESSIONS,
            "session_timeout_minutes": settings.SESSION_TIMEOUT_MINUTES,
            "refresh_threshold_minutes": settings.SESSION_REFRESH_THRESHOLD_MINUTES,
            "secure_cookies": settings.SESSION_COOKIE_SECURE,
            "httponly_cookies": settings.SESSION_COOKIE_HTTPONLY,
        },
    }


# Export the router
__all__ = ["router"]
