"""
User-related Pydantic schemas.

This module contains schemas for user management operations,
including creation, updates, and search parameters.
"""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserSearchParams(BaseModel):
    """User search and filter parameters."""
    name: str | None = Field(None, description="Search by user name")
    email: str | None = Field(None, description="Search by email")
    role: str | None = Field(None, description="Filter by role")
    status: str | None = Field(None, description="Filter by status")


class UserCreate(BaseModel):
    """User creation schema."""
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=2, max_length=255, description="User full name")
    role: str = Field(..., description="User role (sysadmin, admin, user)")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    is_active: bool = Field(default=True, description="User active status")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        """Validate user role."""
        allowed_roles = ["sysadmin", "admin", "user"]
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v


class UserUpdate(BaseModel):
    """User update schema."""
    email: EmailStr | None = Field(None, description="User email address")
    full_name: str | None = Field(None, min_length=2, max_length=255, description="User full name")
    role: str | None = Field(None, description="User role (sysadmin, admin, user)")
    is_active: bool | None = Field(None, description="User active status")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        """Validate user role."""
        if v is not None:
            allowed_roles = ["sysadmin", "admin", "user"]
            if v not in allowed_roles:
                raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v


class UserResponse(BaseModel):
    """User response schema."""
    user_id: UUID = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    full_name: str = Field(..., description="User full name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="User active status")
    is_verified: bool = Field(..., description="Email verification status")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    last_login_at: str | None = Field(None, description="Last login timestamp")


class UserList(BaseModel):
    """User list item schema (summary view)."""
    user_id: UUID = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    full_name: str = Field(..., description="User full name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="User active status")
    last_login_at: str | None = Field(None, description="Last login timestamp")
