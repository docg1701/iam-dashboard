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
    ssn: str | None = Field(None, description="Search by exact SSN")
    status: ClientStatus | None = Field(None, description="Filter by client status")
    created_after: date | None = Field(None, description="Filter clients created after this date")
    created_before: date | None = Field(None, description="Filter clients created before this date")


class ClientCreate(BaseModel):
    """Client creation schema with comprehensive validation matching SQLModel."""

    full_name: str = Field(min_length=2, max_length=255, description="Client's full legal name")
    ssn: str = Field(
        pattern=r"^\d{3}-\d{2}-\d{4}$",
        description="Client's Social Security Number in XXX-XX-XXXX format",
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

    @field_validator("ssn")
    @classmethod
    def validate_ssn_format(cls, v: str) -> str:
        """Validate SSN format and check sum with same rules as SQLModel."""
        # Check format
        if not re.match(r"^\d{3}-\d{2}-\d{4}$", v):
            raise ValueError("SSN must be in XXX-XX-XXXX format")

        # Extract digits for validation
        digits = v.replace("-", "")

        # Check for invalid SSN patterns
        if digits == "000000000":
            raise ValueError("SSN cannot be all zeros")
        if digits[:3] == "000":
            raise ValueError("SSN area number cannot be 000")
        if digits[3:5] == "00":
            raise ValueError("SSN group number cannot be 00")
        if digits[5:] == "0000":
            raise ValueError("SSN serial number cannot be 0000")

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
    ssn: str | None = Field(
        default=None,
        pattern=r"^\d{3}-\d{2}-\d{4}$",
        description="Updated SSN in XXX-XX-XXXX format",
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

    @field_validator("ssn")
    @classmethod
    def validate_ssn_format(cls, v: str | None) -> str | None:
        """Validate SSN format if provided."""
        if v is None:
            return v

        # Check format
        if not re.match(r"^\d{3}-\d{2}-\d{4}$", v):
            raise ValueError("SSN must be in XXX-XX-XXXX format")

        # Extract digits for validation
        digits = v.replace("-", "")

        # Check for invalid SSN patterns
        if digits == "000000000":
            raise ValueError("SSN cannot be all zeros")
        if digits[:3] == "000":
            raise ValueError("SSN area number cannot be 000")
        if digits[3:5] == "00":
            raise ValueError("SSN group number cannot be 00")
        if digits[5:] == "0000":
            raise ValueError("SSN serial number cannot be 0000")

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
    ssn: str = Field(description="Client Social Security Number")
    birth_date: date = Field(description="Client birth date")
    status: ClientStatus = Field(description="Client status")
    notes: str | None = Field(description="Additional notes about the client")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime | None = Field(description="Last update timestamp")
    created_by: UUID = Field(description="ID of user who created this client")
    updated_by: UUID = Field(description="ID of user who last updated this client")

    model_config = {"from_attributes": True}

    @field_validator("ssn")
    @classmethod
    def mask_ssn(cls, v: str) -> str:
        """Mask SSN for security (show only last 4 digits)."""
        if len(v) >= 4:
            return f"***-**-{v[-4:]}"
        return "***-**-****"


class ClientListItem(BaseModel):
    """Client list item schema for summary view in lists."""

    client_id: UUID = Field(description="Client unique identifier")
    full_name: str = Field(description="Client full name")
    ssn_masked: str = Field(description="Masked SSN for security")
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
