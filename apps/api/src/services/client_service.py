"""
Client service with business logic for client management.

This service handles all client-related business operations including
creation, retrieval, updates, and soft deletion with proper validation,
audit logging, and database transaction handling.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import func
from sqlmodel import select

from ..core.database import get_session_maker
from ..models.audit import AuditAction, AuditLog
from ..models.client import Client
from ..schemas.client import (
    ClientCreateRequest,
    ClientListResponse,
    ClientResponse,
    ClientUpdateRequest,
)

logger = structlog.get_logger(__name__)


class ClientService:
    """
    Client service handling business logic for client management.

    Provides methods for creating, retrieving, updating, and deleting clients
    with proper validation, audit logging, and database transaction handling.
    """

    def __init__(self) -> None:
        """Initialize the client service."""
        self.session_maker = get_session_maker()

    async def create_client(
        self,
        client_data: ClientCreateRequest,
        created_by: uuid.UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
    ) -> ClientResponse:
        """
        Create a new client with validation and audit logging.

        Args:
            client_data: Client creation data from request
            created_by: UUID of the user creating the client
            ip_address: Client IP address for audit
            user_agent: Client user agent for audit
            session_id: Session ID for audit tracking

        Returns:
            ClientResponse: Created client data

        Raises:
            HTTPException: If validation fails or CPF already exists
        """
        async with self.session_maker() as session:
            try:
                # Check for duplicate CPF
                existing_client = await self._get_client_by_cpf(
                    session, client_data.cpf
                )
                if existing_client:
                    logger.warning(
                        "Attempted to create client with duplicate CPF",
                        cpf_partial=f"{client_data.cpf[:3]}***{client_data.cpf[-2:]}",
                        created_by=created_by,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="CPF already exists in the system",
                    )

                # Create client instance with validation
                client = Client(
                    name=client_data.name,
                    cpf=client_data.cpf,
                    birth_date=client_data.birth_date,
                    created_by=created_by,
                )

                # Add to session and flush to get ID
                session.add(client)
                await session.flush()

                # Create audit log entry
                audit_entry = AuditLog.create_audit_entry(
                    action=AuditAction.CREATE,
                    resource_type="client",
                    actor_id=created_by,
                    resource_id=client.id,
                    new_values={
                        "name": client.name,
                        "cpf": f"{client.cpf[:3]}***{client.cpf[-2:]}",  # Masked CPF for audit
                        "birth_date": client.birth_date.isoformat(),
                        "is_active": client.is_active,
                    },
                    ip_address=ip_address,
                    user_agent=user_agent,
                    session_id=session_id,
                    description=f"Created client: {client.name}",
                )
                session.add(audit_entry)

                # Commit transaction
                await session.commit()

                logger.info(
                    "Client created successfully",
                    client_id=client.id,
                    created_by=created_by,
                    cpf_partial=f"{client.cpf[:3]}***{client.cpf[-2:]}",
                )

                return ClientResponse.model_validate(client)

            except ValidationError as e:
                await session.rollback()
                logger.error(
                    "Client validation failed",
                    errors=e.errors(),
                    created_by=created_by,
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Validation error: {str(e)}",
                ) from e

            except Exception as e:
                await session.rollback()
                logger.error(
                    "Failed to create client",
                    error=str(e),
                    created_by=created_by,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create client",
                ) from e

    async def get_client(self, client_id: uuid.UUID) -> ClientResponse:
        """
        Retrieve a client by ID.

        Args:
            client_id: UUID of the client to retrieve

        Returns:
            ClientResponse: Client data

        Raises:
            HTTPException: If client not found or not active
        """
        async with self.session_maker() as session:
            try:
                statement = select(Client).where(
                    Client.id == client_id,
                    Client.is_active == True,  # noqa: E712
                )
                result = await session.execute(statement)
                client = result.scalar_one_or_none()

                if not client:
                    logger.warning("Client not found or inactive", client_id=client_id)
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Client not found",
                    )

                logger.debug("Client retrieved successfully", client_id=client_id)
                return ClientResponse.model_validate(client)

            except HTTPException:
                raise
            except Exception as e:
                logger.error(
                    "Failed to retrieve client",
                    error=str(e),
                    client_id=client_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve client",
                ) from e

    async def list_clients(
        self,
        page: int = 1,
        per_page: int = 10,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> ClientListResponse:
        """
        List clients with pagination and optional filtering.

        Args:
            page: Page number (1-based)
            per_page: Number of clients per page (max 100)
            search: Optional search term for name or CPF
            is_active: Optional filter by active status

        Returns:
            ClientListResponse: Paginated list of clients

        Raises:
            HTTPException: If page parameters are invalid
        """
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be positive",
            )
        if per_page < 1 or per_page > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Per page must be between 1 and 100",
            )

        async with self.session_maker() as session:
            try:
                # Build base query
                query = select(Client)
                count_query = select(func.count(Client.id))

                # Apply filters
                if is_active is not None:
                    query = query.where(Client.is_active == is_active)
                    count_query = count_query.where(Client.is_active == is_active)
                else:
                    # Default to active clients only
                    query = query.where(Client.is_active == True)  # noqa: E712
                    count_query = count_query.where(Client.is_active == True)  # noqa: E712

                if search:
                    search_filter = Client.name.ilike(f"%{search}%")
                    query = query.where(search_filter)
                    count_query = count_query.where(search_filter)

                # Get total count
                total_result = await session.execute(count_query)
                total = total_result.scalar() or 0

                # Apply pagination and ordering
                offset = (page - 1) * per_page
                query = (
                    query.order_by(Client.created_at.desc())
                    .offset(offset)
                    .limit(per_page)
                )

                # Execute query
                result = await session.execute(query)
                clients = result.scalars().all()

                # Calculate pagination metadata
                total_pages = (total + per_page - 1) // per_page

                logger.debug(
                    "Clients listed successfully",
                    page=page,
                    per_page=per_page,
                    total=total,
                    search=search,
                    is_active=is_active,
                )

                return ClientListResponse(
                    clients=[
                        ClientResponse.model_validate(client) for client in clients
                    ],
                    total=total,
                    page=page,
                    per_page=per_page,
                    total_pages=total_pages,
                )

            except Exception as e:
                logger.error(
                    "Failed to list clients",
                    error=str(e),
                    page=page,
                    per_page=per_page,
                    search=search,
                    is_active=is_active,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve clients",
                ) from e

    async def update_client(
        self,
        client_id: uuid.UUID,
        client_data: ClientUpdateRequest,
        updated_by: uuid.UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
    ) -> ClientResponse:
        """
        Update an existing client with validation and audit logging.

        Args:
            client_id: UUID of the client to update
            client_data: Client update data from request
            updated_by: UUID of the user updating the client
            ip_address: Client IP address for audit
            user_agent: Client user agent for audit
            session_id: Session ID for audit tracking

        Returns:
            ClientResponse: Updated client data

        Raises:
            HTTPException: If client not found, validation fails, or CPF conflict
        """
        async with self.session_maker() as session:
            try:
                # Get existing client
                statement = select(Client).where(
                    Client.id == client_id,
                    Client.is_active == True,  # noqa: E712
                )
                result = await session.execute(statement)
                client = result.scalar_one_or_none()

                if not client:
                    logger.warning("Client not found for update", client_id=client_id)
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Client not found",
                    )

                # Store old values for audit
                old_values = {
                    "name": client.name,
                    "cpf": f"{client.cpf[:3]}***{client.cpf[-2:]}",  # Masked CPF for audit
                    "birth_date": client.birth_date.isoformat(),
                    "is_active": client.is_active,
                }

                # Check for CPF conflict if CPF is being updated
                if client_data.cpf and client_data.cpf != client.cpf:
                    existing_client = await self._get_client_by_cpf(
                        session, client_data.cpf
                    )
                    if existing_client and existing_client.id != client_id:
                        logger.warning(
                            "Attempted to update client with duplicate CPF",
                            client_id=client_id,
                            cpf_partial=f"{client_data.cpf[:3]}***{client_data.cpf[-2:]}",
                            updated_by=updated_by,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="CPF already exists in the system",
                        )

                # Apply updates
                updates_made = []
                if client_data.name is not None:
                    client.name = client_data.name
                    updates_made.append("name")

                if client_data.cpf is not None:
                    client.cpf = client_data.cpf
                    updates_made.append("cpf")

                if client_data.birth_date is not None:
                    client.birth_date = client_data.birth_date
                    updates_made.append("birth_date")

                if client_data.is_active is not None:
                    client.is_active = client_data.is_active
                    updates_made.append("is_active")

                # Update timestamp
                client.updated_at = datetime.now(UTC).replace(tzinfo=None)

                # Validate the updated client
                client._validate_fields()

                # Store new values for audit
                new_values = {
                    "name": client.name,
                    "cpf": f"{client.cpf[:3]}***{client.cpf[-2:]}",  # Masked CPF for audit
                    "birth_date": client.birth_date.isoformat(),
                    "is_active": client.is_active,
                }

                # Create audit log entry
                audit_entry = AuditLog.create_audit_entry(
                    action=AuditAction.UPDATE,
                    resource_type="client",
                    actor_id=updated_by,
                    resource_id=client.id,
                    old_values=old_values,
                    new_values=new_values,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    session_id=session_id,
                    description=f"Updated client: {client.name} (fields: {', '.join(updates_made)})",
                )
                session.add(audit_entry)

                # Commit transaction
                await session.commit()

                logger.info(
                    "Client updated successfully",
                    client_id=client_id,
                    updated_by=updated_by,
                    updates=updates_made,
                )

                return ClientResponse.model_validate(client)

            except ValidationError as e:
                await session.rollback()
                logger.error(
                    "Client update validation failed",
                    errors=e.errors(),
                    client_id=client_id,
                    updated_by=updated_by,
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Validation error: {str(e)}",
                ) from e

            except HTTPException:
                await session.rollback()
                raise

            except Exception as e:
                await session.rollback()
                logger.error(
                    "Failed to update client",
                    error=str(e),
                    client_id=client_id,
                    updated_by=updated_by,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update client",
                ) from e

    async def delete_client(
        self,
        client_id: uuid.UUID,
        deleted_by: uuid.UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
    ) -> None:
        """
        Soft delete a client (set is_active to False).

        Args:
            client_id: UUID of the client to delete
            deleted_by: UUID of the user deleting the client
            ip_address: Client IP address for audit
            user_agent: Client user agent for audit
            session_id: Session ID for audit tracking

        Raises:
            HTTPException: If client not found or already deleted
        """
        async with self.session_maker() as session:
            try:
                # Get existing client
                statement = select(Client).where(Client.id == client_id)
                result = await session.execute(statement)
                client = result.scalar_one_or_none()

                if not client:
                    logger.warning("Client not found for deletion", client_id=client_id)
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Client not found",
                    )

                if not client.is_active:
                    logger.warning(
                        "Attempted to delete already inactive client",
                        client_id=client_id,
                        deleted_by=deleted_by,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Client is already deleted",
                    )

                # Store old values for audit
                old_values = {
                    "name": client.name,
                    "cpf": f"{client.cpf[:3]}***{client.cpf[-2:]}",  # Masked CPF for audit
                    "birth_date": client.birth_date.isoformat(),
                    "is_active": client.is_active,
                }

                # Soft delete
                client.is_active = False
                client.updated_at = datetime.now(UTC).replace(tzinfo=None)

                # Store new values for audit
                new_values = {
                    "name": client.name,
                    "cpf": f"{client.cpf[:3]}***{client.cpf[-2:]}",  # Masked CPF for audit
                    "birth_date": client.birth_date.isoformat(),
                    "is_active": client.is_active,
                }

                # Create audit log entry
                audit_entry = AuditLog.create_audit_entry(
                    action=AuditAction.DELETE,
                    resource_type="client",
                    actor_id=deleted_by,
                    resource_id=client.id,
                    old_values=old_values,
                    new_values=new_values,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    session_id=session_id,
                    description=f"Soft deleted client: {client.name}",
                )
                session.add(audit_entry)

                # Commit transaction
                await session.commit()

                logger.info(
                    "Client soft deleted successfully",
                    client_id=client_id,
                    deleted_by=deleted_by,
                    client_name=client.name,
                )

            except HTTPException:
                await session.rollback()
                raise

            except Exception as e:
                await session.rollback()
                logger.error(
                    "Failed to delete client",
                    error=str(e),
                    client_id=client_id,
                    deleted_by=deleted_by,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete client",
                ) from e

    async def _get_client_by_cpf(self, session: Any, cpf: str) -> Client | None:
        """
        Helper method to get client by CPF.

        Args:
            session: Database session
            cpf: CPF to search for

        Returns:
            Client or None if not found
        """
        statement = select(Client).where(Client.cpf == cpf, Client.is_active == True)  # noqa: E712
        result = await session.execute(statement)
        return result.scalar_one_or_none()


# Global instance
client_service = ClientService()
