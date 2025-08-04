"""
User-related Pydantic schemas.

This module contains schemas for user management operations,
including creation, updates, and search parameters.
"""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.models.user import UserRole


class UserSearchParams(BaseModel):
    """User search and filter parameters."""

    query: str | None = Field(None, description="Search by email")
    role: UserRole | None = Field(None, description="Filter by role")
    is_active: bool | None = Field(None, description="Filter by active status")


class UserCreateRequest(BaseModel):
    """User creation schema for API requests."""

    email: EmailStr = Field(..., description="User email address")
    role: UserRole = Field(..., description="User role (sysadmin, admin, user)")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    is_active: bool = Field(default=True, description="User active status")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Check for at least one uppercase, lowercase, digit, and special char
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")

        return v


class UserUpdateRequest(BaseModel):
    """User update schema for API requests."""

    email: EmailStr | None = Field(None, description="User email address")
    role: UserRole | None = Field(None, description="User role (sysadmin, admin, user)")
    is_active: bool | None = Field(None, description="User active status")
    password: str | None = Field(None, min_length=8, max_length=128, description="New password")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str | None) -> str | None:
        """Validate password strength requirements."""
        if v is not None:
            return UserCreateRequest.validate_password_strength(v)
        return v


class UserResponse(BaseModel):
    """User response schema."""

    user_id: UUID = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="User active status")
    totp_enabled: bool = Field(..., description="Whether 2FA is enabled")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    last_login: datetime | None = Field(None, description="Last login timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class UserListItem(BaseModel):
    """User list item schema for paginated responses."""

    user_id: UUID = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="User active status")
    totp_enabled: bool = Field(..., description="Whether 2FA is enabled")
    last_login: datetime | None = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
