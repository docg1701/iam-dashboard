"""Permission models for user agent access control."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import JSON, CheckConstraint, Column, Index
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


class AgentName(str, Enum):
    """Available agent names for permission assignment."""

    CLIENT_MANAGEMENT = "client_management"
    PDF_PROCESSING = "pdf_processing"
    REPORTS_ANALYSIS = "reports_analysis"
    AUDIO_RECORDING = "audio_recording"

    def __str__(self) -> str:
        """Return the value instead of the full enum representation."""
        return self.value


class PermissionActions(SQLModel):
    """JSONB structure for CRUD permissions."""

    create: bool = Field(default=False, description="Permission to create resources")
    read: bool = Field(default=False, description="Permission to read resources")
    update: bool = Field(default=False, description="Permission to update resources")
    delete: bool = Field(default=False, description="Permission to delete resources")


class UserAgentPermissionBase(SQLModel):
    """Base user agent permission fields."""

    user_id: UUID = Field(foreign_key="users.user_id", description="User receiving permissions")
    agent_name: AgentName = Field(description="Agent name for permission assignment")
    permissions: dict[str, Any] = Field(
        default_factory=lambda: {"create": False, "read": False, "update": False, "delete": False},
        description="JSONB permissions structure with CRUD operations",
        sa_column=Column(JSON),
    )

    @field_validator("permissions")
    @classmethod
    def validate_permissions_structure(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate permissions JSONB structure."""
        required_keys = {"create", "read", "update", "delete"}
        if not isinstance(v, dict):
            raise ValueError("Permissions must be a dictionary")

        if not required_keys.issubset(set(v.keys())):
            raise ValueError(f"Permissions must contain all keys: {required_keys}")

        for key in required_keys:
            if not isinstance(v[key], bool):
                raise ValueError(f"Permission '{key}' must be a boolean value")

        return v


class UserAgentPermission(UserAgentPermissionBase, table=True):
    """User agent permission database model."""

    __tablename__ = "user_agent_permissions"

    # Primary key
    permission_id: UUID = Field(
        default_factory=uuid4, primary_key=True, description="Unique permission identifier"
    )

    # Audit fields
    created_by_user_id: UUID = Field(
        foreign_key="users.user_id", description="User who created this permission"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Permission creation timestamp"
    )
    updated_at: datetime | None = Field(
        default=None, description="Permission last update timestamp"
    )

    # Relationships
    user: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[UserAgentPermission.user_id]"}
    )
    created_by: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[UserAgentPermission.created_by_user_id]"}
    )

    # Table constraints and indexes
    __table_args__ = (
        # Unique constraint on user_id + agent_name
        Index("ix_user_agent_permissions_user_agent", "user_id", "agent_name", unique=True),
        # Performance indexes
        Index("ix_user_agent_permissions_user_id", "user_id"),
        Index("ix_user_agent_permissions_agent_name", "agent_name"),
        Index("ix_user_agent_permissions_created_at", "created_at"),
        # JSONB structure constraint
        CheckConstraint(
            """
            jsonb_typeof(permissions) = 'object' AND
            permissions ? 'create' AND jsonb_typeof(permissions->'create') = 'boolean' AND
            permissions ? 'read' AND jsonb_typeof(permissions->'read') = 'boolean' AND
            permissions ? 'update' AND jsonb_typeof(permissions->'update') = 'boolean' AND
            permissions ? 'delete' AND jsonb_typeof(permissions->'delete') = 'boolean'
            """,
            name="permissions_jsonb_structure",
        ),
    )


class PermissionTemplateBase(SQLModel):
    """Base permission template fields."""

    template_name: str = Field(
        min_length=1, max_length=100, unique=True, description="Template name"
    )
    description: str | None = Field(default=None, description="Template description")
    permissions: dict[str, Any] = Field(
        description="JSONB permissions structure for all agents", sa_column=Column(JSON)
    )
    is_system_template: bool = Field(
        default=False, description="Whether this is a system-defined template"
    )

    @field_validator("permissions")
    @classmethod
    def validate_template_permissions(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate template permissions structure."""
        if not isinstance(v, dict):
            raise ValueError("Template permissions must be a dictionary")

        # Each agent should have CRUD permissions
        for agent_name in AgentName:
            if agent_name.value not in v:
                v[agent_name.value] = {
                    "create": False,
                    "read": False,
                    "update": False,
                    "delete": False,
                }

            agent_perms = v[agent_name.value]
            required_keys = {"create", "read", "update", "delete"}

            if not isinstance(agent_perms, dict):
                raise ValueError(f"Permissions for {agent_name.value} must be a dictionary")

            if not required_keys.issubset(set(agent_perms.keys())):
                raise ValueError(f"Agent {agent_name.value} must contain all keys: {required_keys}")

            for key in required_keys:
                if not isinstance(agent_perms[key], bool):
                    raise ValueError(f"Permission '{key}' for {agent_name.value} must be boolean")

        return v


class PermissionTemplate(PermissionTemplateBase, table=True):
    """Permission template database model."""

    __tablename__ = "permission_templates"

    # Primary key
    template_id: UUID = Field(
        default_factory=uuid4, primary_key=True, description="Unique template identifier"
    )

    # Audit fields
    created_by_user_id: UUID = Field(
        foreign_key="users.user_id", description="User who created this template"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Template creation timestamp"
    )
    updated_at: datetime | None = Field(default=None, description="Template last update timestamp")

    # Relationships
    created_by: "User" = Relationship(back_populates=None)

    # Table constraints and indexes
    __table_args__ = (
        Index("ix_permission_templates_name", "template_name", unique=True),
        Index("ix_permission_templates_system", "is_system_template"),
        Index("ix_permission_templates_created_at", "created_at"),
    )


class PermissionAuditLogBase(SQLModel):
    """Base permission audit log fields."""

    user_id: UUID = Field(foreign_key="users.user_id", description="User whose permissions changed")
    agent_name: AgentName = Field(description="Agent affected by permission change")
    action: str = Field(
        max_length=50, description="Action performed (CREATE, UPDATE, DELETE, BULK_ASSIGN)"
    )
    old_permissions: dict[str, Any] | None = Field(
        default=None, description="Previous permissions before change", sa_column=Column(JSON)
    )
    new_permissions: dict[str, Any] | None = Field(
        default=None, description="New permissions after change", sa_column=Column(JSON)
    )
    changed_by_user_id: UUID = Field(
        foreign_key="users.user_id", description="User who made the permission change"
    )
    change_reason: str | None = Field(
        default=None, max_length=255, description="Reason for permission change"
    )


class PermissionAuditLog(PermissionAuditLogBase, table=True):
    """Permission audit log database model."""

    __tablename__ = "permission_audit_log"

    # Primary key
    audit_id: UUID = Field(
        default_factory=uuid4, primary_key=True, description="Unique audit log identifier"
    )

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Audit log timestamp")

    # Relationships
    user: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[PermissionAuditLog.user_id]"}
    )
    changed_by: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[PermissionAuditLog.changed_by_user_id]"}
    )

    # Table constraints and indexes
    __table_args__ = (
        Index("ix_permission_audit_user_id", "user_id"),
        Index("ix_permission_audit_agent_name", "agent_name"),
        Index("ix_permission_audit_action", "action"),
        Index("ix_permission_audit_changed_by", "changed_by_user_id"),
        Index("ix_permission_audit_created_at", "created_at"),
        # Composite index for user + agent audit queries
        Index("ix_permission_audit_user_agent", "user_id", "agent_name"),
    )


# Permission schemas for API endpoints
class UserAgentPermissionCreate(UserAgentPermissionBase):
    """Schema for creating user agent permissions."""

    created_by_user_id: UUID = Field(description="User creating the permission")


class UserAgentPermissionUpdate(SQLModel):
    """Schema for updating user agent permissions."""

    permissions: dict[str, Any] | None = Field(default=None, description="Updated permissions structure")

    @field_validator("permissions")
    @classmethod
    def validate_permissions_structure(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Validate permissions JSONB structure."""
        if v is not None:
            return UserAgentPermissionBase.validate_permissions_structure(v)
        return v


class UserAgentPermissionRead(UserAgentPermissionBase):
    """Schema for reading user agent permissions."""

    permission_id: UUID = Field(description="Unique permission identifier")
    created_by_user_id: UUID = Field(description="User who created the permission")
    created_at: datetime = Field(description="Permission creation timestamp")
    updated_at: datetime | None = Field(description="Permission last update timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class PermissionTemplateCreate(PermissionTemplateBase):
    """Schema for creating permission templates."""

    created_by_user_id: UUID = Field(description="User creating the template")


class PermissionTemplateUpdate(SQLModel):
    """Schema for updating permission templates."""

    template_name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None)
    permissions: dict[str, Any] | None = Field(default=None)

    @field_validator("permissions")
    @classmethod
    def validate_template_permissions(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Validate template permissions structure."""
        if v is not None:
            return PermissionTemplateBase.validate_template_permissions(v)
        return v


class PermissionTemplateRead(PermissionTemplateBase):
    """Schema for reading permission templates."""

    template_id: UUID = Field(description="Unique template identifier")
    created_by_user_id: UUID = Field(description="User who created the template")
    created_at: datetime = Field(description="Template creation timestamp")
    updated_at: datetime | None = Field(description="Template last update timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
