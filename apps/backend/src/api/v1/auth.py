"""
Authentication API endpoints.

This module contains endpoints for user authentication, including login,
logout, token refresh, and 2FA verification.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import Session, select

from src.core.database import get_session
from src.core.password_security import PasswordSecurityService
from src.core.security import (
    TokenData,
    auth_service,
    get_current_user_token,
    pwd_context,
    security,
)
from src.core.totp import TOTPService
from src.models.user import User
from src.schemas.auth import (
    LoginRequest,
    LoginResponse,
    TokenRefreshResponse,
    TwoFALoginRequest,
    TwoFASetupResponse,
)
from src.schemas.common import SuccessResponse

router = APIRouter(prefix="/auth", tags=["authentication"])

# Initialize services
totp_service = TOTPService()
password_security_service = PasswordSecurityService()


def _get_client_ip(request: Request) -> str:
    """Extract client IP address considering proxies."""
    # Check for X-Forwarded-For header (proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    # Check for X-Real-IP header (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct client IP
    return request.client.host if request.client else "127.0.0.1"


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest, request: Request, session: Session = Depends(get_session)
):
    """
    Authenticate user and return JWT token.

    Args:
        login_data: User login credentials
        session: Database session

    Returns:
        LoginResponse: JWT token and user information or 2FA challenge

    Raises:
        HTTPException: If credentials are invalid
    """
    # Check for account lockout first
    if password_security_service.is_account_locked(login_data.email):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to too many failed login attempts",
        )

    # Get user by email
    user = session.exec(select(User).where(User.email == login_data.email)).first()

    if not user:
        # Record failed attempt even for non-existent users to prevent enumeration
        client_ip = _get_client_ip(request)
        password_security_service.record_login_attempt(login_data.email, client_ip, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    # Verify password
    if not pwd_context.verify(login_data.password, user.password_hash):
        # Record failed attempt
        client_ip = _get_client_ip(request)
        password_security_service.record_login_attempt(login_data.email, client_ip, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    # Password is correct - record successful attempt and clear any failed attempts
    client_ip = _get_client_ip(request)
    password_security_service.record_login_attempt(login_data.email, client_ip, success=True)
    password_security_service.clear_failed_attempts(login_data.email)

    # Update last login
    user.last_login = datetime.utcnow()
    session.add(user)
    session.commit()

    # Check if 2FA is enabled
    if user.totp_enabled and user.totp_secret:
        # Generate temporary session for 2FA
        session_id = auth_service.create_temp_session(
            user_id=str(user.user_id), user_role=user.role.value, user_email=user.email
        )

        return LoginResponse(
            success=True,
            access_token="",  # No token yet
            token_type="bearer",
            expires_in=0,
            user={},  # No user data yet
            requires_2fa=True,
            session_id=session_id,
        )
    else:
        # Direct login without 2FA
        token_data = auth_service.create_access_token(
            user_id=str(user.user_id), user_role=user.role.value, user_email=user.email
        )

        return LoginResponse(
            success=True,
            access_token=token_data["access_token"],
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
            user={
                "user_id": str(user.user_id),
                "email": user.email,
                "role": user.role.value,
                "is_active": user.is_active,
                "totp_enabled": user.totp_enabled,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            },
            requires_2fa=False,
            session_id=None,
        )


@router.post("/2fa/verify", response_model=LoginResponse)
async def verify_2fa(verify_data: TwoFALoginRequest, session: Session = Depends(get_session)):
    """
    Complete login with 2FA verification.

    Args:
        verify_data: 2FA verification data
        session: Database session

    Returns:
        LoginResponse: JWT token and user information

    Raises:
        HTTPException: If 2FA code is invalid
    """
    # Get temporary session
    temp_session = auth_service.get_temp_session(verify_data.session_id)
    if not temp_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session"
        )

    # Get user from database
    user = session.exec(select(User).where(User.email == temp_session.user_email)).first()
    if not user or not user.is_active:
        auth_service.revoke_temp_session(verify_data.session_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )

    # Verify TOTP code
    if not user.totp_secret or not totp_service.verify_totp(
        user.totp_secret, verify_data.totp_code
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 2FA code")

    # 2FA successful - revoke temporary session and create real session
    auth_service.revoke_temp_session(verify_data.session_id)

    # Create access token
    token_data = auth_service.create_access_token(
        user_id=str(user.user_id), user_role=user.role.value, user_email=user.email
    )

    return LoginResponse(
        success=True,
        access_token=token_data["access_token"],
        token_type=token_data["token_type"],
        expires_in=token_data["expires_in"],
        user={
            "user_id": str(user.user_id),
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active,
            "totp_enabled": user.totp_enabled,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        },
        requires_2fa=False,
        session_id=None,
    )


@router.post("/2fa/setup", response_model=TwoFASetupResponse)
async def setup_2fa(
    token_data: TokenData = Depends(get_current_user_token), session: Session = Depends(get_session)
):
    """
    Setup 2FA for the current user.

    Args:
        token_data: Current user token data
        session: Database session

    Returns:
        TwoFASetupResponse: TOTP secret, QR code, and backup codes

    Raises:
        HTTPException: If user not found or 2FA already enabled
    """
    # Get user from database
    user = session.exec(select(User).where(User.user_id == token_data.user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is already enabled for this user"
        )

    # Setup TOTP
    setup_data = totp_service.setup_totp(user.email)

    # Store TOTP secret and backup codes
    user.totp_secret = setup_data.secret
    user.totp_backup_codes = setup_data.backup_codes
    user.totp_enabled = True
    user.updated_at = datetime.utcnow()

    session.add(user)
    session.commit()

    return TwoFASetupResponse(
        secret=setup_data.secret,
        qr_code_url=setup_data.qr_code_url,
        backup_codes=setup_data.backup_codes,
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Refresh JWT token.

    Args:
        credentials: Current JWT token

    Returns:
        TokenRefreshResponse: New JWT token

    Raises:
        HTTPException: If token is invalid or expired
    """
    # Verify current token
    token_data = auth_service.verify_token(credentials.credentials)

    # Create new token
    new_token = auth_service.create_access_token(
        user_id=token_data.user_id, user_role=token_data.role, user_email=token_data.email
    )

    return TokenRefreshResponse(**new_token)


@router.post("/logout", response_model=SuccessResponse)
async def logout(token_data: TokenData = Depends(get_current_user_token)):
    """
    Logout user and invalidate token.

    Args:
        token_data: Current user token data

    Returns:
        SuccessResponse: Confirmation message
    """
    try:
        # Blacklist the token if jti is available
        if token_data.jti:
            # Calculate token expiration for blacklist TTL
            # Tokens expire in 15 minutes by default
            exp_timestamp = int(datetime.utcnow().timestamp()) + (15 * 60)
            auth_service.blacklist_token(token_data.jti, exp_timestamp)

        # Revoke session if session_id is available
        if token_data.session_id:
            auth_service.revoke_session(token_data.session_id)

    except Exception as e:
        # Log error but don't fail logout
        print(f"Warning: Logout cleanup failed: {e}")

    return SuccessResponse(success=True, message="Logged out successfully")


@router.get("/me", response_model=dict)
async def get_current_user(
    token_data: TokenData = Depends(get_current_user_token), session: Session = Depends(get_session)
):
    """
    Get current user information from database.

    Args:
        token_data: Current user token data
        session: Database session

    Returns:
        dict: User information
    """
    # Get full user data from database
    user = session.exec(select(User).where(User.user_id == token_data.user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {
        "user_id": str(user.user_id),
        "email": user.email,
        "role": user.role.value,
        "is_active": user.is_active,
        "totp_enabled": user.totp_enabled,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }
