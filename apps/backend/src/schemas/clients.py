"""
Client-related Pydantic schemas.

This module contains schemas for client management operations,
including creation, updates, and search parameters.
"""

import re
from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ClientSearchParams(BaseModel):
    """Client search and filter parameters."""

    name: str | None = Field(None, description="Search by client name")
    ssn: str | None = Field(None, description="Search by SSN")
    status: str | None = Field(None, description="Filter by status")
    created_after: date | None = Field(None, description="Filter by creation date")
    created_before: date | None = Field(None, description="Filter by creation date")


class ClientCreate(BaseModel):
    """Client creation schema."""

    full_name: str = Field(..., min_length=2, max_length=255, description="Client full name")
    ssn: str = Field(..., description="Social Security Number (XXX-XX-XXXX format)")
    birth_date: date = Field(..., description="Client birth date")
    notes: str | None = Field(None, max_length=1000, description="Additional notes")

    @field_validator("ssn")
    @classmethod
    def validate_ssn(cls, v: str) -> str:
        """Validate SSN format."""
        if not re.match(r"^\d{3}-\d{2}-\d{4}$", v):
            raise ValueError("SSN must be in format XXX-XX-XXXX")
        return v

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, v: date) -> date:
        """Validate birth date is not in the future."""
        if v > date.today():
            raise ValueError("Birth date cannot be in the future")
        return v


class ClientUpdate(BaseModel):
    """Client update schema."""

    full_name: str | None = Field(
        None, min_length=2, max_length=255, description="Client full name"
    )
    ssn: str | None = Field(None, description="Social Security Number (XXX-XX-XXXX format)")
    birth_date: date | None = Field(None, description="Client birth date")
    status: str | None = Field(None, description="Client status")
    notes: str | None = Field(None, max_length=1000, description="Additional notes")

    @field_validator("ssn")
    @classmethod
    def validate_ssn(cls, v: str | None) -> str | None:
        """Validate SSN format."""
        if v is not None and not re.match(r"^\d{3}-\d{2}-\d{4}$", v):
            raise ValueError("SSN must be in format XXX-XX-XXXX")
        return v

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, v: date | None) -> date | None:
        """Validate birth date is not in the future."""
        if v is not None and v > date.today():
            raise ValueError("Birth date cannot be in the future")
        return v


class ClientResponse(BaseModel):
    """Client response schema."""

    client_id: UUID = Field(..., description="Client unique identifier")
    full_name: str = Field(..., description="Client full name")
    ssn: str = Field(..., description="Social Security Number (masked)")
    birth_date: date = Field(..., description="Client birth date")
    status: str = Field(..., description="Client status")
    notes: str | None = Field(None, description="Additional notes")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    created_by: str = Field(..., description="Creator user name")

    @field_validator("ssn")
    @classmethod
    def mask_ssn(cls, v: str) -> str:
        """Mask SSN for security (show only last 4 digits)."""
        if len(v) >= 4:
            return f"***-**-{v[-4:]}"
        return "***-**-****"


class ClientList(BaseModel):
    """Client list item schema (summary view)."""

    client_id: UUID = Field(..., description="Client unique identifier")
    full_name: str = Field(..., description="Client full name")
    ssn_masked: str = Field(..., description="Masked SSN")
    status: str = Field(..., description="Client status")
    created_at: str = Field(..., description="Creation timestamp")
