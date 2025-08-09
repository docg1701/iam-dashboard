"""
Authentication API endpoints.

This module contains endpoints for user authentication, including login,
logout, token refresh, and 2FA verification.
"""

import asyncio
import logging
import time
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
    BackupCodeVerifyRequest,
    LoginRequest,
    LoginResponse,
    TokenRefreshResponse,
    TwoFALoginRequest,
    TwoFASetupResponse,
    UserResponse,
)
from src.schemas.common import SuccessResponse
from src.services.security_monitoring import (
    SecurityEventType,
    SeverityLevel,
    security_monitor,
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Initialize services
totp_service = TOTPService()
password_security_service = PasswordSecurityService()
logger = logging.getLogger(__name__)


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


async def _ensure_consistent_timing(start_time: float, min_duration: float = 0.2) -> None:
    """
    Ensure consistent response timing to prevent timing attacks.
    
    Args:
        start_time: When the operation started
        min_duration: Minimum duration in seconds
    """
    elapsed = time.time() - start_time
    if elapsed < min_duration:
        await asyncio.sleep(min_duration - elapsed)


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest, request: Request, session: Session = Depends(get_session)
) -> LoginResponse:
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
    # Timing attack resistance: Start timing measurement
    start_time = time.time()
    
    client_ip = _get_client_ip(request)
    
    # Check for rate limiting first
    if password_security_service.is_rate_limited(login_data.email, client_ip):
        # Ensure consistent timing even for rate limited requests
        await _ensure_consistent_timing(start_time)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )
    
    # Record this attempt for rate limiting
    password_security_service.record_rate_limit_attempt(client_ip)

    # Get user by email first (needed for database-based lockout check)
    user = session.exec(select(User).where(User.email == login_data.email)).first()

    # Check for account lockout (with user info if available)
    if password_security_service.is_account_locked(login_data.email, user):
        # Ensure consistent timing for locked account responses
        await _ensure_consistent_timing(start_time)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to too many failed login attempts",
        )

    if not user:
        # Record failed attempt even for non-existent users to prevent enumeration
        password_security_service.record_login_attempt(login_data.email, client_ip, success=False)
        
        # Log security event
        security_monitor.log_security_event(
            event_type=SecurityEventType.LOGIN_FAILED,
            severity=SeverityLevel.MEDIUM,
            ip_address=client_ip,
            details={"email": login_data.email, "reason": "user_not_found"},
            risk_score=0.4
        )
        
        # Ensure consistent timing to prevent user enumeration
        await _ensure_consistent_timing(start_time)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    # Check if user is active
    if not user.is_active:
        # Ensure consistent timing for inactive accounts
        await _ensure_consistent_timing(start_time)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    # Verify password
    if not pwd_context.verify(login_data.password, user.password_hash):
        # Record failed attempt with user and session for database tracking
        password_security_service.record_login_attempt(login_data.email, client_ip, success=False, user=user, session=session)
        
        # Log security event
        security_monitor.log_security_event(
            event_type=SecurityEventType.LOGIN_FAILED,
            severity=SeverityLevel.MEDIUM,
            user_id=str(user.user_id),
            ip_address=client_ip,
            details={"email": login_data.email, "reason": "invalid_password"},
            risk_score=0.5
        )
        
        # Check if account is now locked after this attempt
        if password_security_service.is_account_locked(login_data.email, user):
            # Log account lockout
            security_monitor.log_security_event(
                event_type=SecurityEventType.LOGIN_LOCKED,
                severity=SeverityLevel.HIGH,
                user_id=str(user.user_id),
                ip_address=client_ip,
                details={"email": login_data.email, "reason": "too_many_failed_attempts"},
                risk_score=0.8
            )
            
            # Ensure consistent timing for newly locked accounts
            await _ensure_consistent_timing(start_time)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to too many failed login attempts",
            )
        else:
            # Ensure consistent timing for failed password attempts
            await _ensure_consistent_timing(start_time)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
            )

    # Password is correct - record successful attempt and clear any failed attempts
    password_security_service.record_login_attempt(login_data.email, client_ip, success=True, user=user, session=session)
    password_security_service.clear_failed_attempts(login_data.email)
    
    # Log successful login
    security_monitor.log_security_event(
        event_type=SecurityEventType.LOGIN_SUCCESS,
        severity=SeverityLevel.LOW,
        user_id=str(user.user_id),
        ip_address=client_ip,
        details={"email": login_data.email, "method": "password"},
        risk_score=0.0
    )

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

        response = LoginResponse(
            success=True,
            access_token="",  # No token yet
            token_type="bearer",
            expires_in=0,
            user=None,  # No user data yet
            requires_2fa=True,
            session_id=session_id,
        )
        
        # Ensure consistent timing to prevent timing attacks
        await _ensure_consistent_timing(start_time)
        return response
    else:
        # Direct login without 2FA
        token_data = auth_service.create_access_token(
            user_id=user.user_id, user_role=user.role.value, user_email=user.email
        )

        response = LoginResponse(
            success=True,
            access_token=token_data.access_token,
            token_type=token_data.token_type,
            expires_in=token_data.expires_in,
            user=UserResponse(
                user_id=str(user.user_id),
                email=user.email,
                role=user.role.value,
                is_active=user.is_active,
                totp_enabled=user.totp_enabled,
                last_login=user.last_login.isoformat() if user.last_login else None,
                created_at=user.created_at.isoformat(),
                updated_at=user.updated_at.isoformat() if user.updated_at else None,
            ),
            requires_2fa=False,
            session_id=None,
        )
        
        # Ensure consistent timing to prevent timing attacks
        await _ensure_consistent_timing(start_time)
        return response


@router.post("/2fa/verify", response_model=LoginResponse)
async def verify_2fa(
    verify_data: TwoFALoginRequest, session: Session = Depends(get_session)
) -> LoginResponse:
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
        # Log failed 2FA attempt
        security_monitor.log_security_event(
            event_type=SecurityEventType.TWO_FA_FAILED,
            severity=SeverityLevel.MEDIUM,
            user_id=str(user.user_id),
            details={"email": user.email, "method": "totp"},
            risk_score=0.5
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 2FA code")

    # 2FA successful - revoke temporary session and create real session
    auth_service.revoke_temp_session(verify_data.session_id)
    
    # Log successful 2FA
    security_monitor.log_security_event(
        event_type=SecurityEventType.TWO_FA_SUCCESS,
        severity=SeverityLevel.LOW,
        user_id=str(user.user_id),
        details={"email": user.email, "method": "totp"},
        risk_score=0.0
    )

    # Create access token
    token_data = auth_service.create_access_token(
        user_id=user.user_id, user_role=user.role.value, user_email=user.email
    )

    return LoginResponse(
        success=True,
        access_token=token_data.access_token,
        token_type=token_data.token_type,
        expires_in=token_data.expires_in,
        user=UserResponse(
            user_id=str(user.user_id),
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
            totp_enabled=user.totp_enabled,
            last_login=user.last_login.isoformat() if user.last_login else None,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat() if user.updated_at else None,
        ),
        requires_2fa=False,
        session_id=None,
    )


@router.post("/2fa/verify-backup", response_model=LoginResponse)
async def verify_2fa_backup_code(
    verify_data: BackupCodeVerifyRequest, session: Session = Depends(get_session)
) -> LoginResponse:
    """
    Complete login with 2FA backup code verification.

    Args:
        verify_data: Backup code verification data
        session: Database session

    Returns:
        LoginResponse: JWT token and user information

    Raises:
        HTTPException: If backup code is invalid
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

    # Verify backup code with enhanced security
    is_valid, updated_codes, error_message = totp_service.verify_backup_code(
        user.totp_backup_codes or [],
        verify_data.backup_code,
        user_id=str(user.user_id)
    )
    
    if not is_valid:
        # Log security event for failed backup code attempt
        logger.warning(f"Failed backup code attempt for user {user.email}: {error_message}")
        security_monitor.log_security_event(
            event_type=SecurityEventType.BACKUP_CODE_FAILED,
            severity=SeverityLevel.MEDIUM,
            user_id=str(user.user_id),
            details={"email": user.email, "error": error_message},
            risk_score=0.6
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=error_message or "Invalid backup code"
        )

    # Update backup codes (remove used code)
    user.totp_backup_codes = updated_codes
    session.add(user)
    session.commit()
    
    # Log successful backup code usage
    security_monitor.log_security_event(
        event_type=SecurityEventType.BACKUP_CODE_USED,
        severity=SeverityLevel.MEDIUM,  # Medium since backup codes should be used sparingly
        user_id=str(user.user_id),
        details={"email": user.email, "remaining_codes": len(updated_codes)},
        risk_score=0.3
    )

    # Backup code successful - revoke temporary session and create real session
    auth_service.revoke_temp_session(verify_data.session_id)

    # Create access token
    token_data = auth_service.create_access_token(
        user_id=user.user_id, user_role=user.role.value, user_email=user.email
    )

    return LoginResponse(
        success=True,
        access_token=token_data.access_token,
        token_type=token_data.token_type,
        expires_in=token_data.expires_in,
        user=UserResponse(
            user_id=str(user.user_id),
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
            totp_enabled=user.totp_enabled,
            last_login=user.last_login.isoformat() if user.last_login else None,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat() if user.updated_at else None,
        ),
        requires_2fa=False,
        session_id=None,
    )


@router.post("/2fa/setup", response_model=TwoFASetupResponse)
async def setup_2fa(
    token_data: TokenData = Depends(get_current_user_token), session: Session = Depends(get_session)
) -> TwoFASetupResponse:
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
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenRefreshResponse:
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

    return TokenRefreshResponse(
        access_token=new_token.access_token,
        token_type=new_token.token_type,
        expires_in=new_token.expires_in,
    )


@router.post("/logout", response_model=SuccessResponse)
async def logout(token_data: TokenData = Depends(get_current_user_token)) -> SuccessResponse:
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
            auth_service.blacklist_token(token_data.jti, exp_timestamp, reason="user_logout")

        # Revoke session if session_id is available
        if token_data.session_id:
            auth_service.revoke_session(token_data.session_id)
        
        # Log logout event
        security_monitor.log_security_event(
            event_type=SecurityEventType.LOGOUT,
            severity=SeverityLevel.LOW,
            user_id=token_data.user_id,
            session_id=token_data.session_id,
            details={"method": "user_initiated"},
            risk_score=0.0
        )

    except Exception as e:
        # Log error but don't fail logout
        logger.warning(f"Logout cleanup failed: {e}")

    return SuccessResponse(success=True, message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token_data: TokenData = Depends(get_current_user_token), session: Session = Depends(get_session)
) -> UserResponse:
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

    return UserResponse(
        user_id=str(user.user_id),
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        totp_enabled=user.totp_enabled,
        last_login=user.last_login.isoformat() if user.last_login else None,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat() if user.updated_at else None,
    )
