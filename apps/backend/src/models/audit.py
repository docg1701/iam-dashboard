"""Audit log model for tracking all data modifications."""

import ipaddress
import json
import re
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlmodel import Field, SQLModel, JSON, Column


class AuditAction(str, Enum):
    """Audit action enumeration."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    VIEW = "VIEW"


class AuditLog(SQLModel, table=True):
    """Audit log model for tracking all data modifications."""

    __tablename__ = "audit_logs"

    # Primary key field
    audit_id: UUID = Field(
        default_factory=uuid4, primary_key=True, description="Unique audit log identifier"
    )

    # Base timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when the record was created"
    )
    updated_at: datetime | None = Field(
        default=None, description="Timestamp when the record was last updated"
    )

    # What was modified
    table_name: str = Field(
        max_length=100, description="Name of the database table that was modified"
    )
    record_id: str = Field(max_length=100, description="ID of the record that was modified")
    action: AuditAction = Field(description="Type of action performed")

    # Data change tracking
    old_values: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Previous values before modification (JSON)",
    )
    new_values: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON), description="New values after modification (JSON)"
    )

    # User and session tracking
    user_id: UUID = Field(
        foreign_key="users.user_id", description="ID of user who performed the action"
    )
    ip_address: str = Field(
        max_length=45,  # IPv6 can be up to 45 characters
        description="IP address from which the action was performed",
    )
    user_agent: str = Field(max_length=500, description="User agent string from the request")

    # Override timestamp field for audit logs
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Exact timestamp when the action occurred"
    )

    class Config:
        """SQLModel configuration for AuditLog."""

        json_schema_extra = {
            "indexes": [
                {"fields": ["table_name", "record_id"]},
                {"fields": ["user_id"]},
                {"fields": ["timestamp"]},
                {"fields": ["action"]},
                {"fields": ["table_name", "timestamp"]},
            ]
        }

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        """Validate table name format."""
        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError("Table name must be lowercase with underscores only")
        return v

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, v: str) -> str:
        """Validate IP address format."""
        try:
            ipaddress.ip_address(v)
        except ValueError as e:
            raise ValueError("Invalid IP address format") from e
        return v

    @field_validator("old_values", "new_values")
    @classmethod
    def validate_json_data(cls, v: dict[str, object] | None) -> dict[str, object] | None:
        """Validate JSON data structure."""
        if v is not None:
            # Ensure values are JSON serializable
            try:
                json.dumps(v)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Values must be JSON serializable: {e}") from e
        return v


class AuditLogCreate(SQLModel):
    """Schema for creating audit log entries."""

    table_name: str = Field(max_length=100, description="Name of the table being audited")
    record_id: str = Field(max_length=100, description="ID of the record being audited")
    action: AuditAction = Field(description="Action being performed")
    old_values: dict[str, Any] | None = Field(
        default=None, description="Previous values (for UPDATE/DELETE)"
    )
    new_values: dict[str, Any] | None = Field(
        default=None, description="New values (for CREATE/UPDATE)"
    )
    user_id: UUID = Field(description="User performing the action")
    ip_address: str = Field(max_length=45, description="IP address of the request")
    user_agent: str = Field(max_length=500, description="User agent of the request")


class AuditLogRead(SQLModel):
    """Schema for reading audit log data."""

    audit_id: UUID = Field(description="Unique audit log identifier")
    table_name: str = Field(description="Table that was modified")
    record_id: str = Field(description="Record that was modified")
    action: AuditAction = Field(description="Action performed")
    old_values: dict[str, Any] | None = Field(default=None, description="Previous values")
    new_values: dict[str, Any] | None = Field(default=None, description="New values")
    user_id: UUID = Field(description="User who performed action")
    ip_address: str = Field(description="IP address")
    user_agent: str = Field(description="User agent")
    timestamp: datetime = Field(description="When action occurred")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class AuditLogSearch(SQLModel):
    """Schema for audit log search operations."""

    table_name: str | None = Field(default=None, description="Filter by table name")
    record_id: str | None = Field(default=None, description="Filter by specific record ID")
    action: AuditAction | None = Field(default=None, description="Filter by action type")
    user_id: UUID | None = Field(default=None, description="Filter by user who performed action")
    start_date: datetime | None = Field(
        default=None, description="Filter actions after this timestamp"
    )
    end_date: datetime | None = Field(
        default=None, description="Filter actions before this timestamp"
    )
    limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum number of results to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
