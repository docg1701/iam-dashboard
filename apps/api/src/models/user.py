"""
User model with authentication support.
"""

import uuid
from datetime import UTC, datetime
from enum import Enum

from pydantic import EmailStr
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import Column, Enum as SQLAEnum
from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    """User role enumeration following data model specifications."""

    SYSADMIN = "sysadmin"
    ADMIN = "admin"
    USER = "user"

    def __str__(self) -> str:
        """Return the string value for proper test compatibility."""
        return self.value

    def __hash__(self) -> int:
        """Make enum hashable for SQLAlchemy compatibility."""
        return hash(self.value)


class User(SQLModel, table=True):
    """User model with authentication support and role-based access control."""

    __tablename__ = "users"

    # Primary key with UUID
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)

    # Authentication fields
    email: EmailStr = Field(..., unique=True, index=True)
    password_hash: str = Field(...)

    # Role-based access control
    role: UserRole = Field(
        default=UserRole.USER,
        sa_column=Column(
            SQLAEnum(UserRole, values_callable=lambda obj: [e.value for e in obj]),
            nullable=False,
            default=UserRole.USER.value
        )
    )

    # 2FA support - TOTP secret is optional
    totp_secret: str | None = Field(default=None)

    # Status and audit fields
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))

    # Additional metadata for security
    last_login_at: datetime | None = Field(default=None)
    failed_login_attempts: int = Field(default=0)
    locked_until: datetime | None = Field(default=None)

    def __init__(self, **data: object) -> None:
        """Initialize User with validation."""
        # Validate required fields
        if "email" not in data or data["email"] is None:
            raise PydanticValidationError.from_exception_data(
                "User",
                [{"type": "missing", "loc": ("email",), "input": data}],
            )
        if "password_hash" not in data or data["password_hash"] is None:
            raise PydanticValidationError.from_exception_data(
                "User",
                [
                    {
                        "type": "missing",
                        "loc": ("password_hash",),
                        "input": data,
                    }
                ],
            )
        super().__init__(**data)

    @property
    def has_2fa(self) -> bool:
        """Check if user has 2FA enabled (has TOTP secret)."""
        return bool(self.totp_secret)

    def __repr__(self) -> str:
        return f"User(id={self.id}, email='{self.email}', role='{self.role}')"
