"""Permission management API endpoints."""

import logging
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from src.core.database import get_session
from src.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from src.core.permissions import require_admin_or_sysadmin
from src.core.security import TokenData, get_current_user_token
from src.models.permissions import AgentName
from src.models.user import User
from src.schemas.permissions import (
    BulkOperationResponse,
    BulkPermissionAssignRequest,
    BulkTemplateApplyRequest,
    PaginatedPermissionAuditResponse,
    PaginatedPermissionTemplatesResponse,
    PermissionAuditResponse,
    PermissionCheckResponse,
    PermissionStatsResponse,
    PermissionTemplateCreateRequest,
    PermissionTemplateResponse,
    PermissionTemplateUpdateRequest,
    PermissionValidationResponse,
    UserPermissionAssignRequest,
    UserPermissionMatrixResponse,
    UserPermissionResponse,
    UserPermissionUpdateRequest,
)
from src.services.permission_service import PermissionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/permissions", tags=["permissions"])


def get_permission_service(session: Annotated[Session, Depends(get_session)]) -> PermissionService:
    """Create PermissionService with database session dependency."""
    return PermissionService(session=session)


@router.get("/check", response_model=PermissionCheckResponse)
async def check_user_permission(
    user_id: UUID = Query(description="User ID to check"),
    agent_name: AgentName = Query(description="Agent name"),
    operation: str = Query(description="Operation to check"),
    current_user: User = require_admin_or_sysadmin(),
    service: PermissionService = Depends(get_permission_service),
) -> PermissionCheckResponse:
    """Check if a user has a specific permission."""
    logger.info(
        f"Checking permission for user {user_id}, agent {agent_name}, operation {operation}"
    )

    try:
        granted = await service.check_user_permission(user_id, agent_name, operation)
        return PermissionCheckResponse(
            user_id=user_id, agent_name=agent_name, operation=operation, granted=granted
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    finally:
        await service.close()


@router.get("/user/{user_id}", response_model=UserPermissionMatrixResponse)
async def get_user_permissions(
    user_id: UUID,
    current_user: User = require_admin_or_sysadmin(),
    service: PermissionService = Depends(get_permission_service),
) -> UserPermissionMatrixResponse:
    """Get complete permission matrix for a user."""
    logger.info(f"Getting permissions for user {user_id}")

    try:
        permissions = await service.get_user_permissions(user_id)
        return UserPermissionMatrixResponse(user_id=user_id, permissions=permissions)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    finally:
        await service.close()


@router.post("/assign", response_model=UserPermissionResponse)
async def assign_user_permission(
    request: UserPermissionAssignRequest,
    current_user: User = require_admin_or_sysadmin(),
    service: PermissionService = Depends(get_permission_service),
) -> UserPermissionResponse:
    """Assign permissions to a user."""
    logger.info(f"Assigning permissions to user {request.user_id} for agent {request.agent_name}")
    try:
        permission = await service.assign_permission(
            user_id=request.user_id,
            agent_name=request.agent_name,
            permissions=request.permissions,
            created_by_user_id=current_user.user_id,
            change_reason=request.change_reason,
        )
        return UserPermissionResponse.model_validate(permission)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    finally:
        await service.close()


@router.post("/assign-system")
async def assign_system_permissions(
    request: dict[str, Any],
    current_user: TokenData = Depends(get_current_user_token),
    service: PermissionService = Depends(get_permission_service),
) -> dict[str, str]:
    """Assign system-level permissions - restricted to sysadmin only."""
    logger.info(f"System permission assignment attempt by user {current_user.user_id}")

    # Only sysadmin can assign system permissions
    if current_user.role != "sysadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only system administrators can assign system permissions",
        )

    # For security testing - this endpoint should be protected
    # In a real system, this would integrate with system permission management
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="System permission assignment not implemented"
    )


@router.put("/user/{user_id}/agent/{agent_name}", response_model=UserPermissionResponse)
async def update_user_permission(
    user_id: UUID,
    agent_name: AgentName,
    request: UserPermissionUpdateRequest,
    current_user: User = require_admin_or_sysadmin(),
    service: PermissionService = Depends(get_permission_service),
) -> UserPermissionResponse:
    """Update permissions for a user and agent."""
    logger.info(f"Updating permissions for user {user_id} and agent {agent_name}")

    try:
        permission = await service.assign_permission(
            user_id=user_id,
            agent_name=agent_name,
            permissions=request.permissions,
            created_by_user_id=current_user.user_id,
            change_reason=request.change_reason,
        )
        return UserPermissionResponse.model_validate(permission)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    finally:
        await service.close()


@router.post("/revoke")
async def revoke_permission(
    request: dict[str, Any],
    current_user: User = require_admin_or_sysadmin(),
    service: PermissionService = Depends(get_permission_service),
) -> dict[str, str]:
    """Revoke permissions for a user and agent."""
    user_id = UUID(request["user_id"])
    agent_name = AgentName(request["agent_name"])
    change_reason = request.get("change_reason")

    logger.info(f"Revoking permissions for user {user_id} and agent {agent_name}")

    try:
        await service.revoke_permission(
            user_id=user_id,
            agent_name=agent_name,
            revoked_by_user_id=current_user.user_id,
            change_reason=change_reason,
        )
        return {"message": "Permission revoked successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    finally:
        await service.close()


@router.delete("/user/{user_id}/agent/{agent_name}")
async def revoke_user_permission(
    user_id: UUID,
    agent_name: AgentName,
    change_reason: str = Query(default=None, description="Reason for revoking permission"),
    current_user: User = require_admin_or_sysadmin(),
    service: PermissionService = Depends(get_permission_service),
) -> dict[str, str]:
    """Revoke permissions for a user and agent."""
    logger.info(f"Revoking permissions for user {user_id} and agent {agent_name}")

    try:
        await service.revoke_permission(
            user_id=user_id,
            agent_name=agent_name,
            revoked_by_user_id=current_user.user_id,
            change_reason=change_reason,
        )
        return {"message": "Permission revoked successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    finally:
        await service.close()


@router.post("/bulk-assign", response_model=BulkOperationResponse)
async def bulk_assign_permissions(
    request: BulkPermissionAssignRequest,
    current_user: User = require_admin_or_sysadmin(),
    service: PermissionService = Depends(get_permission_service),
) -> BulkOperationResponse:
    """Bulk assign permissions to multiple users."""
    logger.info(
        f"Bulk assigning permissions to {len(request.user_ids)} users for agent {request.agent_name}"
    )

    try:
        agent_permissions = {request.agent_name: request.permissions}
        result = await service.bulk_assign_permissions(
            user_ids=request.user_ids,
            agent_permissions=agent_permissions,
            assigned_by_user_id=current_user.user_id,
            change_reason=request.change_reason,
        )

        successful_count = len([user_id for user_id, permissions in result.items() if permissions])
        failed_count = len(request.user_ids) - successful_count

        return BulkOperationResponse(
            operation_id=f"bulk_assign_{datetime.utcnow().timestamp()}",
            total_users=len(request.user_ids),
            successful_updates=successful_count,
            failed_updates=failed_count,
            errors=[],
            completed_at=datetime.utcnow(),
        )
    finally:
        await service.close()


@router.post("/bulk-apply-template", response_model=BulkOperationResponse)
async def bulk_apply_template(
    request: BulkTemplateApplyRequest,
    current_user: User = require_admin_or_sysadmin(),
    service: PermissionService = Depends(get_permission_service),
) -> BulkOperationResponse:
    """Apply a permission template to multiple users."""
    logger.info(f"Applying template {request.template_id} to {len(request.user_ids)} users")

    try:
        result = await service.apply_template_to_users(
            template_id=request.template_id,
            user_ids=request.user_ids,
            applied_by_user_id=current_user.user_id,
            change_reason=request.change_reason,
        )

        return BulkOperationResponse(
            operation_id=f"template_apply_{datetime.utcnow().timestamp()}",
            total_users=len(request.user_ids),
            successful_updates=result["successful"],
            failed_updates=result["failed"],
            errors=result.get("errors", []),
            completed_at=datetime.utcnow(),
        )
    finally:
        await service.close()


@router.get("/templates", response_model=PaginatedPermissionTemplatesResponse)
async def list_permission_templates(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    system_only: bool = Query(default=False, description="Show only system templates"),
    current_user: User = require_admin_or_sysadmin(),
    service: PermissionService = Depends(get_permission_service),
) -> PaginatedPermissionTemplatesResponse:
    """List permission templates with pagination."""
    logger.info(f"Listing permission templates - page {page}, size {page_size}")

    try:
        templates, total = await service.list_templates(
            page=page, page_size=page_size, system_only=system_only
        )

        return PaginatedPermissionTemplatesResponse(
            items=[PermissionTemplateResponse.model_validate(t) for t in templates],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size,
        )
    finally:
        await service.close()


@router.post(
    "/templates", response_model=PermissionTemplateResponse, status_code=status.HTTP_201_CREATED
)
async def create_permission_template(
    request: PermissionTemplateCreateRequest,
    current_user: User = require_admin_or_sysadmin(),
    service: PermissionService = Depends(get_permission_service),
) -> PermissionTemplateResponse:
    """Create a new permission template."""
    logger.info(f"Creating permission template: {request.template_name}")

    try:
        template = await service.create_template(
            template_name=request.template_name,
            description=request.description,
            permissions=request.permissions,
            created_by_user_id=current_user.user_id,
        )
        return PermissionTemplateResponse.model_validate(template)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    finally:
        await service.close()


@router.put("/templates/{template_id}", response_model=PermissionTemplateResponse)
async def update_permission_template(
    template_id: UUID,
    request: PermissionTemplateUpdateRequest,
    current_user: User = require_admin_or_sysadmin(),
    service: PermissionService = Depends(get_permission_service),
) -> PermissionTemplateResponse:
    """Update a permission template."""
    logger.info(f"Updating permission template: {template_id}")

    try:
        template = await service.update_template(
            template_id=template_id,
            template_name=request.template_name,
            description=request.description,
            permissions=request.permissions,
            updated_by_user_id=current_user.user_id,
        )
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

        return PermissionTemplateResponse.model_validate(template)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    finally:
        await service.close()


@router.delete("/templates/{template_id}")
async def delete_permission_template(
    template_id: UUID,
    current_user: User = require_admin_or_sysadmin(),
    service: PermissionService = Depends(get_permission_service),
) -> dict[str, bool]:
    """Delete a permission template."""
    logger.info(f"Deleting permission template: {template_id}")

    try:
        success = await service.delete_template(template_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

        return {"success": True}
    finally:
        await service.close()


@router.get("/audit", response_model=PaginatedPermissionAuditResponse)
async def get_permission_audit_log(
    user_id: UUID = Query(default=None, description="Filter by user ID"),
    agent_name: AgentName = Query(default=None, description="Filter by agent name"),
    action: str = Query(default=None, description="Filter by action"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    current_user: User = require_admin_or_sysadmin(),
    service: PermissionService = Depends(get_permission_service),
) -> PaginatedPermissionAuditResponse:
    """Get permission audit log with filtering and pagination."""
    logger.info(f"Getting permission audit log - page {page}, size {page_size}")

    try:
        audit_entries, total = await service.get_audit_log(
            user_id=user_id, agent_name=agent_name, action=action, page=page, page_size=page_size
        )

        return PaginatedPermissionAuditResponse(
            items=[
                PermissionAuditResponse.model_validate(entry.model_dump())
                for entry in audit_entries
            ],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size,
        )
    finally:
        await service.close()


@router.get("/stats", response_model=PermissionStatsResponse)
async def get_permission_statistics(
    current_user: User = require_admin_or_sysadmin(),
    service: PermissionService = Depends(get_permission_service),
) -> PermissionStatsResponse:
    """Get permission system statistics."""
    logger.info("Getting permission statistics")

    try:
        stats = await service.get_permission_stats()
        return PermissionStatsResponse(**stats)
    finally:
        await service.close()


@router.post("/validate", response_model=PermissionValidationResponse)
async def validate_permissions(
    permissions: dict[str, Any],
    current_user: User = require_admin_or_sysadmin(),
    service: PermissionService = Depends(get_permission_service),
) -> PermissionValidationResponse:
    """Validate permission structure."""
    logger.info("Validating permission structure")

    errors = []
    warnings = []

    # Note: permissions is guaranteed to be a dict due to FastAPI type validation

    # Validate required operations
    required_operations = {"create", "read", "update", "delete"}
    for operation in required_operations:
        if operation not in permissions:
            errors.append(f"Missing required operation: {operation}")
        elif not isinstance(permissions[operation], bool):
            errors.append(f"Operation '{operation}' must be a boolean")

    # Check for dependency warnings
    if permissions.get("delete") and not permissions.get("read"):
        warnings.append("Delete permission typically requires read permission")

    if permissions.get("update") and not permissions.get("read"):
        warnings.append("Update permission typically requires read permission")

    return PermissionValidationResponse(valid=len(errors) == 0, errors=errors, warnings=warnings)
