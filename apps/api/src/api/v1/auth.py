"""
Authentication API endpoints.
"""
from datetime import datetime, timezone
from typing import Dict, Any
import uuid
import secrets
import structlog

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ...core.database import get_async_session
from ...models.user import User, UserRole
from ...models.permission import UserAgentPermission
from ...schemas.auth import (
    LoginRequest, LoginResponse, UserInfo, TokenResponse, RefreshTokenRequest,
    Setup2FAResponse, Verify2FARequest, Enable2FARequest, PasswordResetRequest,
    ChangePasswordRequest, MessageResponse
)
from ...services.auth_service import auth_service, security

logger = structlog.get_logger(__name__)

router = APIRouter()


async def get_user_by_email(email: str, session: AsyncSession) -> User:
    """Get user by email from database."""
    statement = select(User).where(User.email == email, User.is_active == True)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    return user


async def get_user_permissions(user_id: uuid.UUID, session: AsyncSession) -> Dict[str, Any]:
    """Get user permissions from database."""
    statement = select(UserAgentPermission).where(UserAgentPermission.user_id == user_id)
    result = await session.execute(statement)
    permissions = result.scalars().all()
    
    # Group permissions by agent
    user_permissions = {}
    for perm in permissions:
        user_permissions[perm.agent_name] = {
            "create": perm.can_create,
            "read": perm.can_read,
            "update": perm.can_update,
            "delete": perm.can_delete
        }
    
    return user_permissions


@router.post("/login", response_model=LoginResponse, summary="User login with optional 2FA")
async def login(
    login_request: LoginRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Authenticate user with email/password and optional TOTP 2FA code.
    Returns JWT tokens and user information with permissions.
    """
    try:
        # Get user by email
        user = await get_user_by_email(login_request.email, session)
        
        # Verify password
        if not auth_service.verify_password(login_request.password, user.password_hash):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59)
            await session.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to multiple failed login attempts"
            )
        
        # Check 2FA if enabled
        if user.totp_secret:
            if not login_request.totp_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="2FA code required"
                )
            
            if not auth_service.verify_totp(user.totp_secret, login_request.totp_code):
                user.failed_login_attempts += 1
                await session.commit()
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid 2FA code"
                )
        
        # Reset failed login attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await session.commit()
        
        # Create JWT tokens
        access_token = auth_service.create_access_token(
            user_id=str(user.id),
            user_role=user.role.value
        )
        refresh_token = auth_service.create_refresh_token(user_id=str(user.id))
        
        # Get user permissions
        permissions = await get_user_permissions(user.id, session)
        
        # Prepare user info
        user_info = UserInfo(
            id=str(user.id),
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
            has_2fa=bool(user.totp_secret)
        )
        
        logger.info(
            "User logged in successfully", 
            user_id=str(user.id), 
            email=user.email,
            has_2fa=bool(user.totp_secret)
        )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=60 * (auth_service.settings.ACCESS_TOKEN_EXPIRE_MINUTES or 60),
            user=user_info,
            permissions=permissions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Refresh access token using refresh token.
    Returns new access and refresh tokens (automatic rotation).
    """
    try:
        new_access_token, new_refresh_token = await auth_service.refresh_access_token(
            refresh_request.refresh_token
        )
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=60 * (auth_service.settings.ACCESS_TOKEN_EXPIRE_MINUTES or 60)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", response_model=MessageResponse, summary="Logout current session")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Logout user from current session.
    Blacklists the access token and removes from session tracking.
    """
    try:
        # Verify token and get user info
        payload = auth_service.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        # Logout user
        auth_service.logout_user(credentials.credentials, user_id)
        
        logger.info("User logged out", user_id=user_id)
        
        return MessageResponse(message="Logout successful")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Logout failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/logout-all", response_model=MessageResponse, summary="Logout all sessions")
async def logout_all_sessions(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Logout user from all sessions.
    Blacklists all access tokens for the user.
    """
    try:
        # Verify token and get user info
        payload = auth_service.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        # Logout from all sessions
        auth_service.logout_all_sessions(user_id)
        
        logger.info("User logged out from all sessions", user_id=user_id)
        
        return MessageResponse(message="Logged out from all sessions successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Logout all sessions failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout from all sessions failed"
        )


@router.get("/setup-2fa", response_model=Setup2FAResponse, summary="Setup 2FA for user")
async def setup_2fa(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Generate TOTP secret and QR code for 2FA setup.
    Returns secret, QR code URL, and backup codes.
    """
    try:
        # Verify token and get user info
        payload = auth_service.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        # Get user from database
        statement = select(User).where(User.id == uuid.UUID(user_id))
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate TOTP secret
        secret = auth_service.generate_totp_secret()
        qr_url = auth_service.generate_totp_qr_url(user.email, secret)
        
        # Generate backup codes (8 codes of 8 digits each)
        backup_codes = [
            ''.join([str(secrets.randbelow(10)) for _ in range(8)])
            for _ in range(8)
        ]
        
        # Store temporary secret in Redis for verification
        auth_service.redis_client.setex(
            f"totp_setup:{user_id}",
            600,  # 10 minutes
            secret
        )
        
        logger.info("2FA setup initiated", user_id=user_id)
        
        return Setup2FAResponse(
            secret=secret,
            qr_code_url=qr_url,
            backup_codes=backup_codes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("2FA setup failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA setup failed"
        )


@router.post("/enable-2fa", response_model=MessageResponse, summary="Enable 2FA for user")
async def enable_2fa(
    enable_request: Enable2FARequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Enable 2FA for user after verifying TOTP code.
    """
    try:
        # Verify token and get user info
        payload = auth_service.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        # Get temporary secret from Redis
        secret = auth_service.redis_client.get(f"totp_setup:{user_id}")
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA setup session expired. Please restart setup."
            )
        
        # Verify TOTP code
        if not auth_service.verify_totp(secret, enable_request.totp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid TOTP code"
            )
        
        # Get user from database
        statement = select(User).where(User.id == uuid.UUID(user_id))
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Enable 2FA by saving secret
        user.totp_secret = secret
        await session.commit()
        
        # Clean up temporary secret
        auth_service.redis_client.delete(f"totp_setup:{user_id}")
        
        logger.info("2FA enabled for user", user_id=user_id)
        
        return MessageResponse(message="2FA enabled successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("2FA enable failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable 2FA"
        )


@router.delete("/disable-2fa", response_model=MessageResponse, summary="Disable 2FA for user")
async def disable_2fa(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Disable 2FA for user.
    """
    try:
        # Verify token and get user info
        payload = auth_service.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        # Get user from database
        statement = select(User).where(User.id == uuid.UUID(user_id))
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Disable 2FA by removing secret
        user.totp_secret = None
        await session.commit()
        
        logger.info("2FA disabled for user", user_id=user_id)
        
        return MessageResponse(message="2FA disabled successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("2FA disable failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable 2FA"
        )


@router.get("/me", response_model=LoginResponse, summary="Get current user information")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get current authenticated user information with permissions.
    Validates JWT token and returns user data, similar to login response.
    """
    try:
        # Verify token and get user info
        payload = auth_service.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get user from database
        statement = select(User).where(User.id == uuid.UUID(user_id), User.is_active == True)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or inactive"
            )
        
        # Get user permissions
        permissions = await get_user_permissions(user.id, session)
        
        # Prepare user info
        user_info = UserInfo(
            id=str(user.id),
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
            has_2fa=bool(user.totp_secret)
        )
        
        # Get token expiration from payload for expires_in calculation
        exp = payload.get("exp", 0)
        current_time = datetime.now(timezone.utc).timestamp()
        expires_in = max(0, int(exp - current_time)) if exp > current_time else 0
        
        logger.info(
            "User info retrieved successfully", 
            user_id=str(user.id), 
            email=user.email
        )
        
        # Return response in same format as login for frontend compatibility
        return LoginResponse(
            access_token=credentials.credentials,  # Return the current token
            refresh_token="",  # Empty since we don't return refresh tokens in /me endpoint
            token_type="bearer",
            expires_in=expires_in,
            user=user_info,
            permissions=permissions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get current user failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )