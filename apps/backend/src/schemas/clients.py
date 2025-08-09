"""
Client-related Pydantic schemas for API requests and responses.

This module contains schemas for client management operations,
including creation, updates, search parameters, and responses.
Aligns with SQLModel definitions in models/client.py.
"""

import re
from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ClientStatus(str, Enum):
    """Client status enumeration - mirrors models.client.ClientStatus."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ClientSearchParams(BaseModel):
    """Client search and filter parameters for query string parsing."""

    full_name: str | None = Field(None, description="Search by client full name (partial match)")
    cpf: str | None = Field(None, description="Search by exact CPF")
    status: ClientStatus | None = Field(None, description="Filter by client status")
    created_after: date | None = Field(None, description="Filter clients created after this date")
    created_before: date | None = Field(None, description="Filter clients created before this date")


class ClientCreate(BaseModel):
    """Client creation schema with comprehensive validation matching SQLModel."""

    full_name: str = Field(min_length=2, max_length=255, description="Client's full legal name")
    cpf: str = Field(
        pattern=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$",
        description="Client's Brazilian CPF in XXX.XXX.XXX-XX format",
    )
    birth_date: date = Field(description="Client's date of birth")
    notes: str | None = Field(
        default=None, max_length=1000, description="Additional notes about the client"
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        """Validate client full name with same rules as SQLModel."""
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
        """Validate Brazilian CPF format and check digits with same rules as SQLModel."""
        # Import validation utility
        import os
        import sys

        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
        """Validate birth date is within reasonable range with same rules as SQLModel."""
        # Must be at least 13 years old (minimum age for account)
        min_date = date(1900, 1, 1)
        max_date = date.today().replace(year=date.today().year - 13)

        if v < min_date:
            raise ValueError("Birth date cannot be before 1900-01-01")
        if v > max_date:
            raise ValueError("Client must be at least 13 years old")

        return v


class ClientUpdate(BaseModel):
    """Client update schema for partial updates."""

    full_name: str | None = Field(
        default=None, min_length=2, max_length=255, description="Updated client full name"
    )
    cpf: str | None = Field(
        default=None,
        pattern=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$",
        description="Updated CPF in XXX.XXX.XXX-XX format",
    )
    birth_date: date | None = Field(default=None, description="Updated birth date")
    status: ClientStatus | None = Field(default=None, description="Updated client status")
    notes: str | None = Field(default=None, max_length=1000, description="Updated notes")

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str | None) -> str | None:
        """Validate client full name if provided."""
        if v is None:
            return v

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
    def validate_cpf_format(cls, v: str | None) -> str | None:
        """Validate Brazilian CPF format if provided."""
        if v is None:
            return v

        # Import validation utility
        import os
        import sys

        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    def validate_birth_date(cls, v: date | None) -> date | None:
        """Validate birth date if provided."""
        if v is None:
            return v

        # Must be at least 13 years old (minimum age for account)
        min_date = date(1900, 1, 1)
        max_date = date.today().replace(year=date.today().year - 13)

        if v < min_date:
            raise ValueError("Birth date cannot be before 1900-01-01")
        if v > max_date:
            raise ValueError("Client must be at least 13 years old")

        return v


class ClientResponse(BaseModel):
    """Client response schema for API responses."""

    client_id: UUID = Field(description="Client unique identifier")
    full_name: str = Field(description="Client full name")
    cpf: str = Field(description="Client Brazilian CPF")
    birth_date: date = Field(description="Client birth date")
    status: ClientStatus = Field(description="Client status")
    notes: str | None = Field(description="Additional notes about the client")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime | None = Field(description="Last update timestamp")
    created_by: UUID = Field(description="ID of user who created this client")
    updated_by: UUID = Field(description="ID of user who last updated this client")

    model_config = {"from_attributes": True}

    @field_validator("cpf")
    @classmethod
    def mask_cpf(cls, v: str) -> str:
        """Mask CPF for security (show only last 2 digits)."""
        if len(v) >= 14 and v[11] == "-":  # Valid CPF format XXX.XXX.XXX-XX
            # Extract the last 2 digits (check digits)
            last_two = v[12:14]  # Characters after the hyphen
            return f"***.***.***-{last_two}"
        return "***.***.***-**"


class ClientListItem(BaseModel):
    """Client list item schema for summary view in lists."""

    client_id: UUID = Field(description="Client unique identifier")
    full_name: str = Field(description="Client full name")
    cpf_masked: str = Field(description="Masked CPF for security")
    status: ClientStatus = Field(description="Client status")
    created_at: datetime = Field(description="Creation timestamp")

    model_config = {"from_attributes": True}


class ClientErrorResponse(BaseModel):
    """Error response schema for client operations."""

    error: str = Field(description="Error type identifier")
    message: str = Field(description="Human-readable error message")
    details: dict[str, str] | None = Field(default=None, description="Additional error details")
    field_errors: dict[str, list[str]] | None = Field(
        default=None, description="Field-specific validation errors"
    )
