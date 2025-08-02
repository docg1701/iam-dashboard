"""User model for authentication and authorization."""

import re
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import EmailStr, field_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .client import Client


class UserRole(str, Enum):
    """User role enumeration."""

    SYSADMIN = "sysadmin"
    ADMIN = "admin"
    USER = "user"


class UserBase(SQLModel):
    """Base user fields shared between models."""

    email: EmailStr = Field(
        unique=True, index=True, max_length=255, description="User email address for authentication"
    )
    role: UserRole = Field(default=UserRole.USER, description="User role for authorization")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    totp_enabled: bool = Field(
        default=False, description="Whether TOTP 2FA is enabled for this user"
    )
    last_login: datetime | None = Field(
        default=None, description="Timestamp of the user's last login"
    )


class User(UserBase, table=True):
    """User database model."""

    __tablename__ = "users"

    # Primary key field
    user_id: UUID = Field(
        default_factory=uuid4, primary_key=True, description="Unique user identifier"
    )

    # Base timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when the record was created"
    )
    updated_at: datetime | None = Field(
        default=None, description="Timestamp when the record was last updated"
    )

    # Authentication fields
    password_hash: str = Field(
        min_length=60, max_length=100, description="Bcrypt password hash (60 characters minimum)"
    )
    totp_secret: str | None = Field(
        default=None, min_length=32, max_length=32, description="Base32 TOTP secret key for 2FA"
    )
    totp_backup_codes: list[str] | None = Field(
        default=None, description="List of backup codes for 2FA recovery", sa_column=Column(JSON)
    )

    # Relationships
    created_clients: list["Client"] = Relationship(
        back_populates="creator", sa_relationship_kwargs={"foreign_keys": "Client.created_by"}
    )
    updated_clients: list["Client"] = Relationship(
        back_populates="updater", sa_relationship_kwargs={"foreign_keys": "Client.updated_by"}
    )

    # Add indexes for performance
    class Config:
        """SQLModel configuration for User."""

        json_schema_extra = {
            "indexes": [
                {"fields": ["email"], "unique": True},
                {"fields": ["role"]},
                {"fields": ["is_active"]},
                {"fields": ["created_at"]},
            ]
        }

    @field_validator("password_hash")
    @classmethod
    def validate_password_hash(cls, v):
        """Validate password hash format."""
        if not v.startswith("$2b$"):
            raise ValueError("Password hash must be bcrypt format")
        return v

    @field_validator("totp_secret")
    @classmethod
    def validate_totp_secret(cls, v):
        """Validate TOTP secret format."""
        if v is not None and not re.match(r"^[A-Z2-7]{32}$", v):
            raise ValueError("TOTP secret must be 32 character Base32 string")
        return v


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(
        min_length=8, max_length=128, description="Plain text password (will be hashed)"
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
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


class UserUpdate(SQLModel):
    """Schema for updating an existing user."""

    email: EmailStr | None = Field(
        default=None, max_length=255, description="Updated email address"
    )
    role: UserRole | None = Field(default=None, description="Updated user role")
    is_active: bool | None = Field(default=None, description="Updated active status")
    totp_enabled: bool | None = Field(default=None, description="Updated 2FA status")
    password: str | None = Field(
        default=None, min_length=8, max_length=128, description="New password (will be hashed)"
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength requirements."""
        if v is not None:
            return UserCreate.validate_password_strength(v)
        return v


class UserRead(UserBase):
    """Schema for reading user data (excludes sensitive fields)."""

    user_id: UUID = Field(description="Unique user identifier")
    created_at: datetime = Field(description="Account creation timestamp")
    updated_at: datetime | None = Field(description="Last update timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
