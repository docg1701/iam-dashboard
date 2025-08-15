"""
Client management API endpoints.

This module provides REST API endpoints for client management operations
including creation, retrieval, updates, and soft deletion with proper
JWT authentication and permission validation.
"""

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ...core.database import get_async_session
from ...middleware.auth import UserDict, get_current_user
from ...models.permission import AgentName, UserAgentPermission
from ...schemas.auth import MessageResponse
from ...schemas.client import (
    ClientCreateRequest,
    ClientListResponse,
    ClientResponse,
    ClientUpdateRequest,
)
from ...services.client_service import client_service

logger = structlog.get_logger(__name__)

router = APIRouter()


async def verify_client_management_permission(
    user_id: str, operation: str, session: AsyncSession
) -> bool:
    """
    Verify if user has client_management permission for the specified operation.

    Args:
        user_id: UUID of the user
        operation: Operation type (create, read, update, delete)
        session: Database session

    Returns:
        True if user has permission, False otherwise
    """
    try:
        # Get user permissions for client_management agent
        statement = select(UserAgentPermission).where(
            UserAgentPermission.user_id == uuid.UUID(user_id),
            UserAgentPermission.agent_name == AgentName.CLIENT_MANAGEMENT,
            UserAgentPermission.is_active == True,  # noqa: E712
        )
        result = await session.execute(statement)
        permission = result.scalar_one_or_none()

        if not permission or not permission.is_valid:
            return False

        # Check specific operation permission
        if operation == "create":
            return permission.can_create
        elif operation == "read":
            return permission.can_read
        elif operation == "update":
            return permission.can_update
        elif operation == "delete":
            return permission.can_delete
        else:
            return False

    except Exception as e:
        logger.error(
            "Permission check failed",
            user_id=user_id,
            operation=operation,
            error=str(e),
        )
        return False


def require_client_permission(operation: str):
    """
    Dependency factory for client management permission validation.

    Args:
        operation: Required operation (create, read, update, delete)

    Returns:
        Dependency function that validates user has client_management permission
    """

    async def permission_dependency(
        current_user: Annotated[UserDict, Depends(get_current_user)],
        session: AsyncSession = Depends(get_async_session),
    ) -> UserDict:
        user_id = current_user["user_id"]

        # Verify permission
        has_permission = await verify_client_management_permission(
            user_id, operation, session
        )

        if not has_permission:
            logger.warning(
                "Client management permission denied",
                user_id=user_id,
                operation=operation,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied for client_management {operation}",
            )

        logger.debug(
            "Client management permission granted",
            user_id=user_id,
            operation=operation,
        )

        return current_user

    return permission_dependency


@router.post(
    "",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new client",
    description="Create a new client with validation and audit logging. Requires client_management create permission.",
)
async def create_client(
    request: Request,
    client_data: ClientCreateRequest,
    current_user: Annotated[UserDict, Depends(require_client_permission("create"))],
    session: AsyncSession = Depends(get_async_session),
) -> ClientResponse:
    """
    Create a new client with validation and audit logging.

    **Required Permission:** client_management agent with can_create = true

    **Request Body:**
    - name: Client name (2-100 characters)
    - cpf: Brazilian CPF (11 digits, validated with algorithm)
    - birth_date: Birth date (minimum 16 years old)

    **Returns:**
    - Created client data with ID and timestamps
    - HTTP 201 Created on success

    **Error Responses:**
    - 400: Invalid request data or validation errors
    - 403: Insufficient permissions
    - 409: CPF already exists in system
    - 422: Data validation failed
    - 500: Internal server error
    """
    try:
        # Extract audit context
        user_id = uuid.UUID(current_user["user_id"])
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Create client using service
        client = await client_service.create_client(
            client_data=client_data,
            created_by=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.info(
            "Client created via API",
            client_id=client.id,
            created_by=user_id,
        )

        return client

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Client creation failed via API",
            error=str(e),
            created_by=current_user["user_id"],
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create client",
        ) from e


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Get client by ID",
    description="Retrieve a specific client by ID. Requires client_management read permission.",
)
async def get_client(
    client_id: uuid.UUID,
    current_user: Annotated[UserDict, Depends(require_client_permission("read"))],
) -> ClientResponse:
    """
    Retrieve a specific client by ID.

    **Required Permission:** client_management agent with can_read = true

    **Path Parameters:**
    - client_id: UUID of the client to retrieve

    **Returns:**
    - Client data including all fields and timestamps

    **Error Responses:**
    - 403: Insufficient permissions
    - 404: Client not found or inactive
    - 500: Internal server error
    """
    try:
        client = await client_service.get_client(client_id)

        logger.info(
            "Client retrieved via API",
            client_id=client_id,
            requested_by=current_user["user_id"],
        )

        return client

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Client retrieval failed via API",
            error=str(e),
            client_id=client_id,
            requested_by=current_user["user_id"],
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve client",
        ) from e


@router.get(
    "",
    response_model=ClientListResponse,
    summary="List clients with pagination",
    description="List clients with pagination and optional filtering. Requires client_management read permission.",
)
async def list_clients(
    current_user: Annotated[UserDict, Depends(require_client_permission("read"))],
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    per_page: Annotated[
        int, Query(ge=1, le=100, description="Items per page (1-100)")
    ] = 10,
    search: Annotated[
        str | None, Query(description="Search term for client name")
    ] = None,
    is_active: Annotated[
        bool | None, Query(description="Filter by active status")
    ] = None,
) -> ClientListResponse:
    """
    List clients with pagination and optional filtering.

    **Required Permission:** client_management agent with can_read = true

    **Query Parameters:**
    - page: Page number (default: 1, minimum: 1)
    - per_page: Items per page (default: 10, range: 1-100)
    - search: Optional search term for client name (case-insensitive)
    - is_active: Optional filter by active status (default: active clients only)

    **Returns:**
    - Paginated list of clients with metadata
    - Total count and pagination information

    **Error Responses:**
    - 400: Invalid pagination parameters
    - 403: Insufficient permissions
    - 500: Internal server error
    """
    try:
        clients = await client_service.list_clients(
            page=page,
            per_page=per_page,
            search=search,
            is_active=is_active,
        )

        logger.info(
            "Clients listed via API",
            page=page,
            per_page=per_page,
            total=clients.total,
            search=search,
            requested_by=current_user["user_id"],
        )

        return clients

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Client listing failed via API",
            error=str(e),
            page=page,
            per_page=per_page,
            requested_by=current_user["user_id"],
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve clients",
        ) from e


@router.put(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Update client",
    description="Update an existing client with validation and audit logging. Requires client_management update permission.",
)
async def update_client(
    request: Request,
    client_id: uuid.UUID,
    client_data: ClientUpdateRequest,
    current_user: Annotated[UserDict, Depends(require_client_permission("update"))],
) -> ClientResponse:
    """
    Update an existing client with validation and audit logging.

    **Required Permission:** client_management agent with can_update = true

    **Path Parameters:**
    - client_id: UUID of the client to update

    **Request Body (all fields optional for partial updates):**
    - name: Client name (2-100 characters)
    - cpf: Brazilian CPF (11 digits, validated with algorithm)
    - birth_date: Birth date (minimum 16 years old)
    - is_active: Active status (for deactivation/reactivation)

    **Returns:**
    - Updated client data with new timestamps

    **Error Responses:**
    - 400: Invalid request data or client already deleted
    - 403: Insufficient permissions
    - 404: Client not found
    - 409: CPF already exists in system (if changing CPF)
    - 422: Data validation failed
    - 500: Internal server error
    """
    try:
        # Extract audit context
        user_id = uuid.UUID(current_user["user_id"])
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Update client using service
        client = await client_service.update_client(
            client_id=client_id,
            client_data=client_data,
            updated_by=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.info(
            "Client updated via API",
            client_id=client_id,
            updated_by=user_id,
        )

        return client

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Client update failed via API",
            error=str(e),
            client_id=client_id,
            updated_by=current_user["user_id"],
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update client",
        ) from e


@router.delete(
    "/{client_id}",
    response_model=MessageResponse,
    summary="Soft delete client",
    description="Soft delete a client (set is_active to False). Requires client_management delete permission.",
)
async def delete_client(
    request: Request,
    client_id: uuid.UUID,
    current_user: Annotated[UserDict, Depends(require_client_permission("delete"))],
) -> MessageResponse:
    """
    Soft delete a client (set is_active to False).

    **Required Permission:** client_management agent with can_delete = true

    **Path Parameters:**
    - client_id: UUID of the client to delete

    **Returns:**
    - Success message

    **Note:** This is a soft delete operation - the client record is preserved
    but marked as inactive. The client can be reactivated using the update endpoint.

    **Error Responses:**
    - 400: Client already deleted
    - 403: Insufficient permissions
    - 404: Client not found
    - 500: Internal server error
    """
    try:
        # Extract audit context
        user_id = uuid.UUID(current_user["user_id"])
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Delete client using service
        await client_service.delete_client(
            client_id=client_id,
            deleted_by=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.info(
            "Client deleted via API",
            client_id=client_id,
            deleted_by=user_id,
        )

        return MessageResponse(message="Client deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Client deletion failed via API",
            error=str(e),
            client_id=client_id,
            deleted_by=current_user["user_id"],
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete client",
        ) from e
