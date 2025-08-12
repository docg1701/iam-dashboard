"""
Utility functions for secure cookie management.

Provides httpOnly cookie handling for production token storage
as specified in the authentication system story requirements.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import Response, Request
from fastapi.responses import JSONResponse
import structlog

from ..core.config import get_settings

logger = structlog.get_logger(__name__)


class SecureCookieManager:
    """
    Manager for secure cookie operations.
    
    Handles httpOnly cookies for production token storage with
    proper security configurations based on environment.
    """
    
    def __init__(self):
        self.settings = get_settings()
    
    def set_auth_cookies(
        self, 
        response: Response, 
        access_token: str, 
        refresh_token: str,
        expires_at: Optional[datetime] = None
    ) -> None:
        """
        Set authentication cookies in response.
        
        Args:
            response: FastAPI Response object
            access_token: JWT access token
            refresh_token: JWT refresh token
            expires_at: Optional expiration datetime
        """
        # Calculate expiration
        if not expires_at:
            expires_at = datetime.now() + timedelta(
                minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        # Common cookie settings
        cookie_settings = {
            "httponly": self.settings.SESSION_COOKIE_HTTPONLY,
            "secure": self.settings.SESSION_COOKIE_SECURE and not self.settings.DEBUG,
            "samesite": self.settings.SESSION_COOKIE_SAMESITE,
            "domain": self.settings.COOKIE_DOMAIN if not self.settings.DEBUG else None,
            "path": "/"
        }
        
        # Set access token cookie
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            max_age=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            expires=expires_at,
            **cookie_settings
        )
        
        # Set refresh token cookie (longer expiration)
        refresh_expires = datetime.now() + timedelta(
            days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        response.set_cookie(
            key="refresh_token",
            value=f"Bearer {refresh_token}",
            max_age=self.settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            expires=refresh_expires,
            **cookie_settings
        )
        
        logger.info(
            "Authentication cookies set",
            expires_at=expires_at.isoformat(),
            secure=cookie_settings["secure"],
            httponly=cookie_settings["httponly"],
            samesite=cookie_settings["samesite"]
        )
    
    def clear_auth_cookies(self, response: Response) -> None:
        """
        Clear authentication cookies from response.
        
        Args:
            response: FastAPI Response object
        """
        cookie_settings = {
            "httponly": self.settings.SESSION_COOKIE_HTTPONLY,
            "secure": self.settings.SESSION_COOKIE_SECURE and not self.settings.DEBUG,
            "samesite": self.settings.SESSION_COOKIE_SAMESITE,
            "domain": self.settings.COOKIE_DOMAIN if not self.settings.DEBUG else None,
            "path": "/"
        }
        
        # Clear cookies by setting them with past expiration
        response.set_cookie(
            key="access_token",
            value="",
            max_age=0,
            expires=datetime(1970, 1, 1),
            **cookie_settings
        )
        
        response.set_cookie(
            key="refresh_token",
            value="",
            max_age=0,
            expires=datetime(1970, 1, 1),
            **cookie_settings
        )
        
        logger.info("Authentication cookies cleared")
    
    def get_token_from_cookies(self, request: Request) -> Optional[str]:
        """
        Extract access token from cookies.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Token string if found, None otherwise
        """
        access_token_cookie = request.cookies.get("access_token")
        
        if access_token_cookie and access_token_cookie.startswith("Bearer "):
            token = access_token_cookie[7:]  # Remove "Bearer " prefix
            return token
        
        return None
    
    def get_refresh_token_from_cookies(self, request: Request) -> Optional[str]:
        """
        Extract refresh token from cookies.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Refresh token string if found, None otherwise
        """
        refresh_token_cookie = request.cookies.get("refresh_token")
        
        if refresh_token_cookie and refresh_token_cookie.startswith("Bearer "):
            token = refresh_token_cookie[7:]  # Remove "Bearer " prefix
            return token
        
        return None
    
    def create_secure_response(
        self, 
        content: Dict[str, Any], 
        status_code: int = 200,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None
    ) -> JSONResponse:
        """
        Create a secure JSON response with optional authentication cookies.
        
        Args:
            content: Response content
            status_code: HTTP status code
            access_token: Optional access token to set in cookies
            refresh_token: Optional refresh token to set in cookies
            
        Returns:
            JSONResponse with secure configuration
        """
        response = JSONResponse(
            content=content,
            status_code=status_code
        )
        
        # Set authentication cookies if tokens provided
        if access_token and refresh_token:
            self.set_auth_cookies(response, access_token, refresh_token)
        
        # Add security headers specific to JSON responses
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        
        # Cache control for sensitive data
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        return response


# Global instance
cookie_manager = SecureCookieManager()


def get_cookie_manager() -> SecureCookieManager:
    """
    Get the global cookie manager instance.
    
    Returns:
        SecureCookieManager instance
    """
    return cookie_manager


class CookieConfig:
    """
    Configuration class for cookie settings validation.
    
    Ensures cookie settings are properly configured for production security.
    """
    
    @staticmethod
    def validate_production_config() -> Dict[str, Any]:
        """
        Validate cookie configuration for production deployment.
        
        Returns:
            Validation results with recommendations
        """
        settings = get_settings()
        issues = []
        recommendations = []
        
        # Check secure cookie setting
        if not settings.DEBUG and not settings.SESSION_COOKIE_SECURE:
            issues.append("SESSION_COOKIE_SECURE should be True in production")
            recommendations.append("Set SESSION_COOKIE_SECURE=true in production environment")
        
        # Check httpOnly setting
        if not settings.SESSION_COOKIE_HTTPONLY:
            issues.append("SESSION_COOKIE_HTTPONLY should be True for security")
            recommendations.append("Set SESSION_COOKIE_HTTPONLY=true to prevent XSS attacks")
        
        # Check SameSite setting
        valid_samesite = ["strict", "lax", "none"]
        if settings.SESSION_COOKIE_SAMESITE.lower() not in valid_samesite:
            issues.append(f"Invalid SESSION_COOKIE_SAMESITE: {settings.SESSION_COOKIE_SAMESITE}")
            recommendations.append("Set SESSION_COOKIE_SAMESITE to 'strict', 'lax', or 'none'")
        
        # Check cookie domain for production
        if not settings.DEBUG and not settings.COOKIE_DOMAIN:
            recommendations.append("Consider setting COOKIE_DOMAIN for production deployment")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations,
            "current_config": {
                "secure": settings.SESSION_COOKIE_SECURE,
                "httponly": settings.SESSION_COOKIE_HTTPONLY,
                "samesite": settings.SESSION_COOKIE_SAMESITE,
                "domain": settings.COOKIE_DOMAIN,
                "debug_mode": settings.DEBUG
            }
        }


# Export commonly used functions
__all__ = [
    "SecureCookieManager",
    "cookie_manager",
    "get_cookie_manager",
    "CookieConfig"
]