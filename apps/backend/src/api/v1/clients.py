"""
Client management API endpoints.

This module contains endpoints for CRUD operations on clients,
including search, filtering, and bulk operations.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session

from src.core.database import get_session
from src.core.exceptions import DashboardException, dashboard_exception_to_http
from src.core.security import TokenData, require_client_management_access
from src.schemas.clients import (
    ClientCreate,
    ClientListItem,
    ClientResponse,
    ClientSearchParams,
    ClientUpdate,
)
from src.schemas.common import PaginatedResponse, SuccessResponse
from src.services.client_service import ClientService

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=PaginatedResponse[ClientListItem])
async def list_clients(
    request: Request,
    params: ClientSearchParams = Depends(),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    session: Session = Depends(get_session),
    token_data: TokenData = require_client_management_access("read"),
) -> PaginatedResponse[ClientListItem]:
    """
    List clients with optional search and pagination.

    This endpoint supports comprehensive filtering and search capabilities:
    - Full name search (partial, case-insensitive)
    - Exact CPF search
    - Status filtering (active, inactive, archived)
    - Date range filtering (created_after, created_before)
    - Pagination with configurable page size

    Args:
        params: Search and filter parameters from query string
        page: Page number for pagination (1-based)
        per_page: Number of items per page (max 100)
        request: FastAPI request object for audit logging
        session: Database session dependency
        token_data: Current user token data for authorization

    Returns:
        PaginatedResponse[ClientListItem]: Paginated list of clients with metadata

    Raises:
        HTTPException: 400 for validation errors, 500 for server errors
    """
    try:
        # Initialize client service
        client_service = ClientService(session)

        # Get clients with search filters and pagination
        clients, pagination_info = await client_service.list_clients(
            search_params=params,
            page=page,
            per_page=per_page,
            user_id=token_data.user_id,
            request=request,
        )

        # Convert Client models to ClientListItem schemas
        client_list_items = []
        for client in clients:
            # Create masked CPF for list view
            masked_cpf = (
                f"***.***.*{client.cpf[-2:]}-{client.cpf[-2:]}"
                if len(client.cpf) >= 4
                else "***.***.**-**"
            )

            client_list_item = ClientListItem(
                client_id=client.client_id,
                full_name=client.full_name,
                cpf_masked=masked_cpf,
                status=client.status,
                created_at=client.created_at,
            )
            client_list_items.append(client_list_item)

        # Return paginated response
        return PaginatedResponse[ClientListItem](data=client_list_items, pagination=pagination_info)

    except DashboardException as e:
        # Convert custom exceptions to HTTP exceptions
        raise dashboard_exception_to_http(e) from e
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An unexpected error occurred during client listing",
                "error_code": "INTERNAL_ERROR",
            },
        ) from e


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    request: Request,
    session: Session = Depends(get_session),
    token_data: TokenData = require_client_management_access("create"),
) -> ClientResponse:
    """
    Create a new client with comprehensive validation and audit logging.

    This endpoint validates client data including:
    - CPF format validation (XXX.XXX.XXX-XX)
    - Duplicate CPF prevention
    - Birth date validation (minimum 13 years old)
    - Full name format validation
    - Input sanitization for all fields

    Args:
        client_data: Client creation data with validation
        request: FastAPI request object for audit logging
        session: Database session dependency
        token_data: Current user token data for authorization

    Returns:
        ClientResponse: Created client information with masked CPF

    Raises:
        HTTPException: 400 for validation errors, 409 for conflicts, 500 for server errors
    """
    try:
        # Initialize client service
        client_service = ClientService(session)

        # Create client with service layer handling validation and audit
        client_read = await client_service.create_client(
            client_data=client_data,
            user_id=token_data.user_id,
            request=request,
        )

        # Convert Client model to response schema
        return ClientResponse(
            client_id=client_read.client_id,
            full_name=client_read.full_name,
            cpf=client_read.cpf,  # Will be masked by validator
            birth_date=client_read.birth_date,
            status=client_read.status,
            notes=client_read.notes,
            created_at=client_read.created_at,
            updated_at=client_read.updated_at,
            created_by=client_read.created_by,
            updated_by=client_read.updated_by,
        )

    except DashboardException as e:
        # Convert custom exceptions to HTTP exceptions
        raise dashboard_exception_to_http(e) from e
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An unexpected error occurred during client creation",
                "error_code": "INTERNAL_ERROR",
            },
        ) from e


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    token_data: TokenData = require_client_management_access("read"),
) -> ClientResponse:
    """
    Get client by ID with audit logging.

    Args:
        client_id: Client unique identifier
        request: FastAPI request object for audit logging
        session: Database session dependency
        token_data: Current user token data

    Returns:
        ClientResponse: Client information with masked CPF

    Raises:
        HTTPException: 404 if client not found, 500 for server errors
    """
    try:
        # Initialize client service
        client_service = ClientService(session)

        # Get client with service layer handling audit logging
        client_read = await client_service.get_client_by_id(
            client_id=client_id,
            user_id=token_data.user_id,
            request=request,
        )

        # Convert Client model to response schema
        return ClientResponse(
            client_id=client_read.client_id,
            full_name=client_read.full_name,
            cpf=client_read.cpf,  # Will be masked by validator
            birth_date=client_read.birth_date,
            status=client_read.status,
            notes=client_read.notes,
            created_at=client_read.created_at,
            updated_at=client_read.updated_at,
            created_by=client_read.created_by,
            updated_by=client_read.updated_by,
        )

    except DashboardException as e:
        # Convert custom exceptions to HTTP exceptions
        raise dashboard_exception_to_http(e) from e
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An unexpected error occurred during client retrieval",
                "error_code": "INTERNAL_ERROR",
            },
        ) from e


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    client_data: ClientUpdate,
    request: Request,
    session: Session = Depends(get_session),
    token_data: TokenData = require_client_management_access("update"),
) -> ClientResponse:
    """
    Update client information with comprehensive validation and audit logging.

    This endpoint allows updating client data including:
    - Full name with validation
    - CPF format validation and uniqueness check
    - Birth date validation (minimum 13 years old)
    - Status changes
    - Notes updates
    - Input sanitization for all fields

    Args:
        client_id: Client unique identifier
        client_data: Client update data with validation
        request: FastAPI request object for audit logging
        session: Database session dependency
        token_data: Current user token data for authorization

    Returns:
        ClientResponse: Updated client information with masked CPF

    Raises:
        HTTPException: 400 for validation errors, 404 if not found, 409 for conflicts, 500 for server errors
    """
    try:
        # Initialize client service
        client_service = ClientService(session)

        # Update client with service layer handling validation and audit
        updated_client = await client_service.update_client(
            client_id=client_id,
            client_data=client_data,
            user_id=token_data.user_id,
            request=request,
        )

        # Convert Client model to response schema
        return ClientResponse(
            client_id=updated_client.client_id,
            full_name=updated_client.full_name,
            cpf=updated_client.cpf,  # Will be masked by validator
            birth_date=updated_client.birth_date,
            status=updated_client.status,
            notes=updated_client.notes,
            created_at=updated_client.created_at,
            updated_at=updated_client.updated_at,
            created_by=updated_client.created_by,
            updated_by=updated_client.updated_by,
        )

    except DashboardException as e:
        # Convert custom exceptions to HTTP exceptions
        raise dashboard_exception_to_http(e) from e
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An unexpected error occurred during client update",
                "error_code": "INTERNAL_ERROR",
            },
        ) from e


@router.delete("/{client_id}", response_model=SuccessResponse)
async def delete_client(
    client_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    token_data: TokenData = require_client_management_access("delete"),
) -> SuccessResponse:
    """
    Delete client (soft delete by archiving) with audit logging.

    This endpoint performs a soft delete by setting the client status to ARCHIVED.
    The client data is preserved in the database for audit purposes and compliance.
    Only users with admin role can delete clients.

    Args:
        client_id: Client unique identifier
        request: FastAPI request object for audit logging
        session: Database session dependency
        token_data: Current user token data (admin role required)

    Returns:
        SuccessResponse: Confirmation message with client details

    Raises:
        HTTPException: 404 if client not found, 403 if insufficient permissions, 500 for server errors
    """
    try:
        # Initialize client service
        client_service = ClientService(session)

        # Delete (archive) client with service layer handling audit
        success = await client_service.delete_client(
            client_id=client_id,
            user_id=token_data.user_id,
            request=request,
        )

        if success:
            return SuccessResponse(
                message=f"Client {client_id} has been successfully archived",
                details={
                    "client_id": str(client_id),
                    "action": "soft_delete",
                    "status": "archived",
                    "deleted_by": str(token_data.user_id),
                },
            )
        else:
            # This should not happen if service layer works correctly
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": "Client deletion completed but returned unexpected result",
                    "error_code": "DELETION_INCOMPLETE",
                },
            )

    except DashboardException as e:
        # Convert custom exceptions to HTTP exceptions
        raise dashboard_exception_to_http(e) from e
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An unexpected error occurred during client deletion",
                "error_code": "INTERNAL_ERROR",
            },
        ) from e


@router.post("/batch", response_model=dict)
async def batch_update_clients(
    batch_data: dict,
    request: Request,
    session: Session = Depends(get_session),
    token_data: TokenData = require_client_management_access("update"),
) -> dict:
    """
    Batch update operation for clients with ownership validation.

    This endpoint performs batch operations on multiple clients while ensuring
    that only resources owned by the current user are processed.

    Args:
        batch_data: Batch operation data including client_ids and operation
        request: FastAPI request object for audit logging
        session: Database session dependency
        token_data: Current user token data for authorization and ownership validation

    Returns:
        dict: Batch operation results with processed and unauthorized clients

    Raises:
        HTTPException: 403 for unauthorized resources, 400 for validation errors
    """
    try:
        client_ids = batch_data.get("client_ids", [])
        operation = batch_data.get("operation", "")
        operation_data = batch_data.get("data", {})

        if not client_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No client IDs provided for batch operation",
            )

        if not operation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No operation specified for batch operation",
            )

        # Initialize client service
        client_service = ClientService(session)

        # Validate ownership for each client - only process owned clients
        processed = []
        unauthorized = []

        for client_id in client_ids:
            try:
                # Check if user owns this client by trying to get it
                client = await client_service.get_client_by_id(
                    client_id=UUID(client_id),
                    user_id=token_data.user_id,
                    request=request,
                )

                # If we get here, user owns the client
                if operation == "update":
                    # Perform update operation
                    updated_client = await client_service.update_client(
                        client_id=UUID(client_id),
                        client_data=ClientUpdate(**operation_data),
                        user_id=token_data.user_id,
                        request=request,
                    )
                    processed.append(str(client_id))

            except (DashboardException, HTTPException, ValueError):
                # Client not found or not owned by user
                unauthorized.append(str(client_id))
                continue

        # Return batch operation results
        return {
            "operation": operation,
            "total_requested": len(client_ids),
            "processed": processed,
            "unauthorized": unauthorized,
            "success_count": len(processed),
            "unauthorized_count": len(unauthorized),
        }

    except DashboardException as e:
        # Convert custom exceptions to HTTP exceptions
        raise dashboard_exception_to_http(e) from e
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An unexpected error occurred during batch operation",
                "error_code": "INTERNAL_ERROR",
            },
        ) from e
