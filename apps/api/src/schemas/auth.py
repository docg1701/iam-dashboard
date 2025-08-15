"""
Authentication schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field


class PermissionSet(BaseModel):
    """Individual permission set for an agent."""

    create: bool = Field(default=False, description="Create permission")
    read: bool = Field(default=False, description="Read permission")
    update: bool = Field(default=False, description="Update permission")
    delete: bool = Field(default=False, description="Delete permission")


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")
    totp_code: str | None = Field(
        None, min_length=6, max_length=6, description="TOTP 2FA code"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "admin@example.com",
                "password": "SecurePassword123!",
                "totp_code": "123456",
            }
        }
    }


class TokenResponse(BaseModel):
    """JWT token response schema."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
            }
        }
    }


class UserInfo(BaseModel):
    """User information schema for token response."""

    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="User active status")
    has_2fa: bool = Field(..., description="2FA enabled status")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "admin@example.com",
                "role": "admin",
                "is_active": True,
                "has_2fa": True,
            }
        }
    }


class LoginResponse(BaseModel):
    """Complete login response schema."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")
    user: UserInfo = Field(..., description="User information")
    permissions: dict[str, PermissionSet] = Field(..., description="User permissions")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "admin@example.com",
                    "role": "admin",
                    "is_active": True,
                    "has_2fa": True,
                },
                "permissions": {
                    "client_management": {
                        "create": True,
                        "read": True,
                        "update": True,
                        "delete": False,
                    }
                },
            }
        }
    }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str = Field(..., description="JWT refresh token")

    model_config = {
        "json_schema_extra": {
            "example": {"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
        }
    }


class Setup2FAResponse(BaseModel):
    """2FA setup response schema."""

    secret: str = Field(..., description="TOTP secret key")
    qr_code_url: str = Field(..., description="QR code URL for TOTP setup")
    backup_codes: list[str] = Field(..., description="Backup recovery codes")

    model_config = {
        "json_schema_extra": {
            "example": {
                "secret": "JBSWY3DPEHPK3PXP",
                "qr_code_url": "otpauth://totp/IAM%20Dashboard:admin@example.com?secret=JBSWY3DPEHPK3PXP&issuer=IAM%20Dashboard",
                "backup_codes": ["12345678", "87654321", "11223344"],
            }
        }
    }


class Verify2FARequest(BaseModel):
    """2FA verification request schema."""

    totp_code: str = Field(..., min_length=6, max_length=6, description="TOTP 2FA code")

    model_config = {"json_schema_extra": {"example": {"totp_code": "123456"}}}


class Enable2FARequest(BaseModel):
    """Enable 2FA request schema."""

    totp_code: str = Field(
        ..., min_length=6, max_length=6, description="TOTP 2FA code for verification"
    )

    model_config = {"json_schema_extra": {"example": {"totp_code": "123456"}}}


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr = Field(..., description="User email address")

    model_config = {"json_schema_extra": {"example": {"email": "admin@example.com"}}}


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""

    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(
        ..., min_length=12, description="New password (minimum 12 characters)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePassword123!",
            }
        }
    }


class MessageResponse(BaseModel):
    """Generic message response schema."""

    message: str = Field(..., description="Response message")

    model_config = {
        "json_schema_extra": {
            "example": {"message": "Operation completed successfully"}
        }
    }
