"""
Authentication-related Pydantic schemas.

This module contains schemas for authentication requests and responses,
including login, token refresh, and user session data.
"""

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    """User response schema for authentication."""

    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="User active status")
    totp_enabled: bool = Field(..., description="2FA enabled status")
    last_login: str | None = Field(default=None, description="Last login timestamp")
    created_at: str = Field(..., description="User creation timestamp")
    updated_at: str | None = Field(default=None, description="User update timestamp")


class LoginRequest(BaseModel):
    """User login request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")
    remember_me: bool = Field(default=False, description="Remember user session")


class LoginResponse(BaseModel):
    """User login response schema."""

    success: bool = True
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse | None = Field(default=None, description="User information")
    requires_2fa: bool = Field(default=False, description="Whether 2FA is required")
    session_id: str | None = Field(default=None, description="Session ID for 2FA flow")


class TokenRefreshResponse(BaseModel):
    """Token refresh response schema."""

    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TwoFactorRequest(BaseModel):
    """Two-factor authentication request schema."""

    temp_token: str = Field(..., description="Temporary token from login")
    code: str = Field(..., min_length=6, max_length=6, description="2FA verification code")


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")

    def validate_passwords_match(self) -> "ChangePasswordRequest":
        """Validate that new passwords match."""
        if self.new_password != self.confirm_password:
            raise ValueError("New passwords do not match")
        return self


class TwoFASetupResponse(BaseModel):
    """Schema for 2FA setup response."""

    secret: str = Field(description="Base32 TOTP secret")
    qr_code_url: str = Field(description="QR code as data URL")
    backup_codes: list[str] = Field(description="List of backup codes")


class TwoFAVerifyRequest(BaseModel):
    """Schema for 2FA verification during setup."""

    secret: str = Field(description="TOTP secret to verify against")
    totp_code: str = Field(min_length=6, max_length=6, description="6-digit TOTP code")


class TwoFALoginRequest(BaseModel):
    """Schema for 2FA login completion."""

    session_id: str = Field(description="Session ID from initial login")
    totp_code: str = Field(min_length=6, max_length=6, description="6-digit TOTP code")


class TwoFADisableRequest(BaseModel):
    """Schema for disabling 2FA."""

    current_password: str = Field(description="Current password for verification")
    totp_code: str | None = Field(default=None, description="TOTP code (if available)")


class BackupCodeVerifyRequest(BaseModel):
    """Schema for backup code verification."""

    session_id: str = Field(description="Session ID from initial login")
    backup_code: str = Field(description="Backup code for 2FA")


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(description="Refresh token")


class LogoutRequest(BaseModel):
    """Schema for logout request."""

    session_id: str | None = Field(default=None, description="Session ID to revoke")
