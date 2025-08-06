"""Pydantic schemas for permission API endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.permissions import AgentName


class PermissionCheckRequest(BaseModel):
    """Request schema for checking permissions."""

    user_id: UUID = Field(description="User ID to check permissions for")
    agent_name: AgentName = Field(description="Agent name to check")
    operation: str = Field(description="Operation to check (create, read, update, delete)")


class PermissionCheckResponse(BaseModel):
    """Response schema for permission checks."""

    user_id: UUID = Field(description="User ID that was checked")
    agent_name: AgentName = Field(description="Agent name that was checked")
    operation: str = Field(description="Operation that was checked")
    granted: bool = Field(description="Whether permission is granted")


class UserPermissionAssignRequest(BaseModel):
    """Request schema for assigning permissions to a user."""

    user_id: UUID = Field(description="User ID to assign permissions to")
    agent_name: AgentName = Field(description="Agent name for permission")
    permissions: dict[str, Any] = Field(description="Permissions structure with CRUD operations")
    change_reason: str | None = Field(default=None, description="Reason for permission change")


class UserPermissionUpdateRequest(BaseModel):
    """Request schema for updating user permissions."""

    permissions: dict[str, Any] = Field(description="Updated permissions structure")
    change_reason: str | None = Field(default=None, description="Reason for permission change")


class BulkPermissionAssignRequest(BaseModel):
    """Request schema for bulk permission assignment."""

    user_ids: list[UUID] = Field(
        min_length=1, description="List of user IDs to assign permissions to"
    )
    agent_name: AgentName = Field(description="Agent name for permissions")
    permissions: dict[str, Any] = Field(description="Permissions structure to assign")
    change_reason: str | None = Field(default=None, description="Reason for bulk permission change")


class BulkTemplateApplyRequest(BaseModel):
    """Request schema for applying template to multiple users."""

    user_ids: list[UUID] = Field(min_length=1, description="List of user IDs to apply template to")
    template_id: UUID = Field(description="Template ID to apply")
    change_reason: str | None = Field(default=None, description="Reason for template application")


class PermissionTemplateCreateRequest(BaseModel):
    """Request schema for creating permission templates."""

    template_name: str = Field(min_length=1, max_length=100, description="Template name")
    description: str | None = Field(default=None, description="Template description")
    permissions: dict[str, Any] = Field(description="Template permissions for all agents")


class PermissionTemplateUpdateRequest(BaseModel):
    """Request schema for updating permission templates."""

    template_name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None)
    permissions: dict[str, Any] | None = Field(default=None)


class UserPermissionMatrixResponse(BaseModel):
    """Response schema for user permission matrix."""

    user_id: UUID = Field(description="User ID")
    permissions: dict[str, dict[str, bool]] = Field(
        description="Permission matrix by agent and operation"
    )


class PermissionAuditResponse(BaseModel):
    """Response schema for permission audit entries."""

    audit_id: UUID = Field(description="Audit entry ID")
    user_id: UUID = Field(description="User whose permissions changed")
    agent_name: AgentName = Field(description="Agent affected by change")
    action: str = Field(description="Action performed")
    old_permissions: dict[str, Any] | None = Field(description="Previous permissions")
    new_permissions: dict[str, Any] | None = Field(description="New permissions")
    changed_by_user_id: UUID = Field(description="User who made the change")
    change_reason: str | None = Field(description="Reason for change")
    created_at: datetime = Field(description="Timestamp of change")


class PermissionStatsResponse(BaseModel):
    """Response schema for permission statistics."""

    total_users: int = Field(description="Total number of users")
    users_with_permissions: int = Field(description="Users with explicit permissions")
    templates_in_use: int = Field(description="Number of templates being used")
    recent_changes: int = Field(description="Permission changes in last 24h")
    agent_usage: dict[str, int] = Field(description="Permission count by agent")


class BulkOperationResponse(BaseModel):
    """Response schema for bulk operations."""

    operation_id: str = Field(description="Unique operation identifier")
    total_users: int = Field(description="Total users affected")
    successful_updates: int = Field(description="Number of successful updates")
    failed_updates: int = Field(description="Number of failed updates")
    errors: list[str] = Field(description="List of error messages")
    completed_at: datetime = Field(description="Operation completion timestamp")


class PermissionValidationResponse(BaseModel):
    """Response schema for permission validation."""

    valid: bool = Field(description="Whether permissions are valid")
    errors: list[str] = Field(description="List of validation errors")
    warnings: list[str] = Field(description="List of validation warnings")


# Response models that reuse existing model schemas
class UserPermissionResponse(BaseModel):
    """Response schema for user permissions."""

    permission_id: UUID
    user_id: UUID
    agent_name: AgentName
    permissions: dict[str, Any]
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime | None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class PermissionTemplateResponse(BaseModel):
    """Response schema for permission templates."""

    template_id: UUID
    template_name: str
    description: str | None
    permissions: dict[str, Any]
    is_system_template: bool
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime | None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


# Pagination schemas
class PaginatedResponse(BaseModel):
    """Base schema for paginated responses."""

    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    pages: int = Field(description="Total number of pages")


class PaginatedUserPermissionsResponse(PaginatedResponse):
    """Paginated response for user permissions."""

    items: list[UserPermissionResponse] = Field(description="User permission items")


class PaginatedPermissionTemplatesResponse(PaginatedResponse):
    """Paginated response for permission templates."""

    items: list[PermissionTemplateResponse] = Field(description="Permission template items")


class PaginatedPermissionAuditResponse(PaginatedResponse):
    """Paginated response for permission audit log."""

    items: list[PermissionAuditResponse] = Field(description="Permission audit items")


# Error response schemas
class PermissionErrorResponse(BaseModel):
    """Error response schema for permission operations."""

    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: dict[str, Any] | None = Field(default=None, description="Additional error details")


class ValidationErrorResponse(BaseModel):
    """Validation error response schema."""

    error: str = Field(default="validation_error")
    message: str = Field(description="Validation error message")
    field_errors: dict[str, list[str]] = Field(description="Field-specific errors")
