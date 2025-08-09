"""Client model for client management."""

import re
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Optional
from uuid import UUID, uuid4

from pydantic import Field as PydanticField
from pydantic import field_validator
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


class ClientStatus(str, Enum):
    """Client status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ClientBase(SQLModel):
    """Base client fields shared between models."""

    full_name: str = Field(min_length=2, max_length=255, description="Client's full legal name")
    cpf: str = Field(
        regex=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$",
        description="Client's Brazilian CPF in XXX.XXX.XXX-XX format",
    )
    birth_date: date = Field(description="Client's date of birth")
    status: ClientStatus = Field(
        default=ClientStatus.ACTIVE, description="Current status of the client"
    )
    notes: str | None = Field(
        default=None, max_length=1000, description="Additional notes about the client"
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        """Validate client full name."""
        # Trim whitespace and check minimum length
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Full name must be at least 2 characters after trimming")

        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-ZÀ-ÿ\s\-']+$", v):
            raise ValueError("Full name can only contain letters, spaces, hyphens, and apostrophes")

        return v

    @field_validator("cpf")
    @classmethod
    def validate_cpf_format(cls, v: str) -> str:
        """Validate Brazilian CPF format and check digits."""
        from src.utils.validation import validate_cpf

        # Check format
        if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", v):
            raise ValueError("CPF must be in XXX.XXX.XXX-XX format")

        # Validate CPF using utility function
        if not validate_cpf(v):
            raise ValueError("Invalid CPF: failed check digit validation")

        return v

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, v: date) -> date:
        """Validate birth date is within reasonable range."""
        # Must be at least 13 years old (minimum age for account)
        min_date = date(1900, 1, 1)
        max_date = date.today().replace(year=date.today().year - 13)

        if v < min_date:
            raise ValueError("Birth date cannot be before 1900-01-01")
        if v > max_date:
            raise ValueError("Client must be at least 13 years old")

        return v


class Client(ClientBase, table=True):
    """Client database model for Agent 1."""

    __tablename__ = "agent1_clients"

    # Primary key field
    client_id: UUID = Field(
        default_factory=uuid4, primary_key=True, description="Unique client identifier"
    )

    # Base timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when the record was created"
    )
    updated_at: datetime | None = Field(
        default=None, description="Timestamp when the record was last updated"
    )

    # Audit fields - who created/updated this client
    created_by: UUID = Field(
        foreign_key="users.user_id", description="ID of user who created this client"
    )
    updated_by: UUID = Field(
        foreign_key="users.user_id", description="ID of user who last updated this client"
    )

    # Relationships
    creator: Optional["User"] = Relationship(
        back_populates="created_clients",
        sa_relationship_kwargs={"foreign_keys": "Client.created_by"},
    )
    updater: Optional["User"] = Relationship(
        back_populates="updated_clients",
        sa_relationship_kwargs={"foreign_keys": "Client.updated_by"},
    )

    class Config:
        """SQLModel configuration for Client."""

        json_schema_extra = {
            "indexes": [
                {"fields": ["cpf"], "unique": True},
                {"fields": ["full_name"]},
                {"fields": ["status"]},
                {"fields": ["created_at"]},
                {"fields": ["created_by"]},
                {"fields": ["updated_by"]},
            ]
        }


class ClientCreate(ClientBase):
    """Schema for creating a new client."""

    pass


class ClientUpdate(SQLModel):
    """Schema for updating an existing client."""

    full_name: str | None = Field(
        default=None, min_length=2, max_length=255, description="Updated client full name"
    )
    cpf: Annotated[str, PydanticField(pattern=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")] | None = Field(
        default=None, description="Updated CPF in XXX.XXX.XXX-XX format"
    )
    birth_date: date | None = Field(default=None, description="Updated birth date")
    status: ClientStatus | None = Field(default=None, description="Updated client status")
    notes: str | None = Field(default=None, max_length=1000, description="Updated notes")

    # Validators are inherited from ClientBase automatically


class ClientSearch(SQLModel):
    """Schema for client search operations."""

    full_name: str | None = Field(default=None, description="Search by full name (partial match)")
    cpf: str | None = Field(default=None, description="Search by exact CPF")
    status: ClientStatus | None = Field(default=None, description="Filter by client status")
    created_after: date | None = Field(
        default=None, description="Filter clients created after this date"
    )
    created_before: date | None = Field(
        default=None, description="Filter clients created before this date"
    )


class ClientRead(ClientBase):
    """Schema for reading client data."""

    client_id: UUID = Field(description="Unique client identifier")
    created_by: UUID = Field(description="User who created this client")
    updated_by: UUID = Field(description="User who last updated this client")
    created_at: datetime = Field(description="Client creation timestamp")
    updated_at: datetime | None = Field(description="Last update timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
