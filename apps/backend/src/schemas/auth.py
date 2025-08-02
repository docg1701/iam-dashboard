"""
Authentication-related Pydantic schemas.

This module contains schemas for authentication requests and responses,
including login, token refresh, and user session data.
"""

from pydantic import BaseModel, EmailStr, Field


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
    user: dict = Field(..., description="User information")


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
