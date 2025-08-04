"""
Client service layer for business logic operations.

This module contains the ClientService class that handles client management
operations including creation, validation, and audit logging.
"""

from datetime import datetime
from uuid import UUID

from fastapi import Request
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, select

from src.core.exceptions import ConflictError, DatabaseError, NotFoundError, ValidationError
from src.models.audit import AuditAction
from src.models.client import Client, ClientRead, ClientStatus
from src.schemas.clients import ClientCreate as ClientCreateSchema
from src.schemas.clients import ClientSearchParams, ClientUpdate
from src.utils.audit import log_database_action, prepare_audit_data


class ClientService:
    """Service class for client management operations."""

    def __init__(self, session: Session):
        """Initialize ClientService with database session.

        Args:
            session: SQLModel database session
        """
        self.session = session

    async def create_client(
        self,
        client_data: ClientCreateSchema,
        user_id: UUID,
        request: Request,
    ) -> Client:
        """Create a new client with comprehensive validation and audit logging.

        Args:
            client_data: Client creation data from API request
            user_id: ID of user creating the client
            request: FastAPI request object for audit logging

        Returns:
            Client: Created client data

        Raises:
            ValidationError: If client data validation fails
            ConflictError: If SSN already exists
            DatabaseError: If database operation fails
        """
        try:
            # Check for existing SSN to prevent duplicates
            await self._check_ssn_uniqueness(client_data.ssn)

            # Create SQLModel instance from schema data
            client = Client(
                full_name=client_data.full_name,
                ssn=client_data.ssn,
                birth_date=client_data.birth_date,
                notes=client_data.notes,
                created_by=user_id,
                updated_by=user_id,
            )

            # Add to session and commit
            self.session.add(client)
            self.session.commit()
            self.session.refresh(client)

            # Create audit log
            await log_database_action(
                session=self.session,
                action=AuditAction.CREATE,
                table_name="clients",
                record_id=str(client.client_id),
                user_id=user_id,
                request=request,
                new_data=prepare_audit_data(client),
            )

            # Return the client model
            return client

        except IntegrityError as e:
            self.session.rollback()
            if "ssn" in str(e.orig):
                raise ConflictError(
                    message="A client with this SSN already exists",
                    error_code="SSN_DUPLICATE",
                    details={"ssn": client_data.ssn},
                ) from e
            raise DatabaseError(
                message="Failed to create client due to database constraint",
                error_code="CONSTRAINT_VIOLATION",
                original_error=e,
            ) from e

        except PydanticValidationError as e:
            self.session.rollback()
            raise ValidationError(
                message="Client data validation failed",
                error_code="VALIDATION_ERROR",
                details={"validation_errors": e.errors()},
            ) from e

        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(
                message="Database operation failed during client creation",
                error_code="DATABASE_ERROR",
                original_error=e,
            ) from e

    async def get_client_by_id(
        self, client_id: UUID, user_id: UUID, request: Request
    ) -> ClientRead:
        """Get client by ID with audit logging.

        Args:
            client_id: UUID of the client to retrieve
            user_id: ID of user requesting the client
            request: FastAPI request object for audit logging

        Returns:
            Client: Client data

        Raises:
            NotFoundError: If client not found
            DatabaseError: If database operation fails
        """
        try:
            # Query for client
            statement = select(Client).where(Client.client_id == client_id)
            result = self.session.exec(statement)
            client = result.first()

            if not client:
                raise NotFoundError(
                    message=f"Client with ID {client_id} not found",
                    error_code="CLIENT_NOT_FOUND",
                    details={"client_id": str(client_id)},
                )

            # Log view action
            await log_database_action(
                session=self.session,
                action=AuditAction.VIEW,
                table_name="clients",
                record_id=str(client.client_id),
                user_id=user_id,
                request=request,
            )

            return ClientRead.from_orm(client)

        except SQLAlchemyError as e:
            raise DatabaseError(
                message="Database operation failed during client retrieval",
                error_code="DATABASE_ERROR",
                original_error=e,
            ) from e

    async def update_client(
        self,
        client_id: UUID,
        client_data: ClientUpdate,
        user_id: UUID,
        request: Request,
    ) -> Client:
        """Update existing client with validation and audit logging.

        Args:
            client_id: UUID of the client to update
            client_data: Client update data
            user_id: ID of user updating the client
            request: FastAPI request object for audit logging

        Returns:
            Client: Updated client data

        Raises:
            NotFoundError: If client not found
            ConflictError: If SSN already exists (for different client)
            ValidationError: If update data validation fails
            DatabaseError: If database operation fails
        """
        try:
            # Get existing client
            statement = select(Client).where(Client.client_id == client_id)
            result = self.session.exec(statement)
            client = result.first()

            if not client:
                raise NotFoundError(
                    message=f"Client with ID {client_id} not found",
                    error_code="CLIENT_NOT_FOUND",
                    details={"client_id": str(client_id)},
                )

            # Store old values for audit
            old_data = prepare_audit_data(client)

            # Check SSN uniqueness if SSN is being updated
            if client_data.ssn and client_data.ssn != client.ssn:
                await self._check_ssn_uniqueness(client_data.ssn, exclude_client_id=client_id)

            # Update fields that are provided
            update_data = client_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(client, field):
                    setattr(client, field, value)

            # Update audit fields
            client.updated_by = user_id
            client.updated_at = datetime.utcnow()

            # Commit changes
            self.session.add(client)
            self.session.commit()
            self.session.refresh(client)

            # Create audit log
            await log_database_action(
                session=self.session,
                action=AuditAction.UPDATE,
                table_name="clients",
                record_id=str(client.client_id),
                user_id=user_id,
                request=request,
                old_data=old_data,
                new_data=prepare_audit_data(client),
            )

            return client

        except IntegrityError as e:
            self.session.rollback()
            if "ssn" in str(e.orig):
                raise ConflictError(
                    message="A client with this SSN already exists",
                    error_code="SSN_DUPLICATE",
                    details={"ssn": client_data.ssn},
                ) from e
            raise DatabaseError(
                message="Failed to update client due to database constraint",
                error_code="CONSTRAINT_VIOLATION",
                original_error=e,
            ) from e

        except PydanticValidationError as e:
            self.session.rollback()
            raise ValidationError(
                message="Client update data validation failed",
                error_code="VALIDATION_ERROR",
                details={"validation_errors": e.errors()},
            ) from e

        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(
                message="Database operation failed during client update",
                error_code="DATABASE_ERROR",
                original_error=e,
            ) from e

    async def delete_client(
        self,
        client_id: UUID,
        user_id: UUID,
        request: Request,
    ) -> bool:
        """Soft delete client by setting status to archived.

        Args:
            client_id: UUID of the client to delete
            user_id: ID of user deleting the client
            request: FastAPI request object for audit logging

        Returns:
            bool: True if deletion successful

        Raises:
            NotFoundError: If client not found
            DatabaseError: If database operation fails
        """
        try:
            # Get existing client
            statement = select(Client).where(Client.client_id == client_id)
            result = self.session.exec(statement)
            client = result.first()

            if not client:
                raise NotFoundError(
                    message=f"Client with ID {client_id} not found",
                    error_code="CLIENT_NOT_FOUND",
                    details={"client_id": str(client_id)},
                )

            # Store old values for audit
            old_data = prepare_audit_data(client)

            # Soft delete by archiving
            client.status = ClientStatus.ARCHIVED
            client.updated_by = user_id
            client.updated_at = datetime.utcnow()

            # Commit changes
            self.session.add(client)
            self.session.commit()
            self.session.refresh(client)

            # Create audit log
            await log_database_action(
                session=self.session,
                action=AuditAction.DELETE,
                table_name="clients",
                record_id=str(client.client_id),
                user_id=user_id,
                request=request,
                old_data=old_data,
                new_data=prepare_audit_data(client),
            )

            return True

        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(
                message="Database operation failed during client deletion",
                error_code="DATABASE_ERROR",
                original_error=e,
            ) from e

    async def list_clients(
        self,
        search_params: ClientSearchParams,
        page: int,
        per_page: int,
        user_id: UUID,
        request: Request,
    ) -> tuple[list[Client], dict]:
        """List clients with search, filtering, and pagination.

        Args:
            search_params: Search and filter parameters
            page: Page number for pagination
            per_page: Number of items per page
            user_id: ID of user requesting the list
            request: FastAPI request object for audit logging

        Returns:
            Tuple of (clients list, pagination info)

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Base query
            statement = select(Client)

            # Apply filters if provided
            if hasattr(search_params, "full_name") and search_params.full_name:
                statement = statement.where(Client.full_name.ilike(f"%{search_params.full_name}%"))

            if hasattr(search_params, "status") and search_params.status:
                statement = statement.where(Client.status == search_params.status)

            # Calculate total count for pagination
            total_statement = statement
            total_result = self.session.exec(total_statement)
            total_count = len(list(total_result))

            # Apply pagination
            offset = (page - 1) * per_page
            statement = statement.offset(offset).limit(per_page)

            # Execute query
            result = self.session.exec(statement)
            clients = list(result)

            # Calculate pagination info
            total_pages = (total_count + per_page - 1) // per_page
            pagination_info = {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }

            # Log view action (for listing)
            await log_database_action(
                session=self.session,
                action=AuditAction.VIEW,
                table_name="clients",
                record_id="list_operation",
                user_id=user_id,
                request=request,
            )

            return clients, pagination_info

        except SQLAlchemyError as e:
            raise DatabaseError(
                message="Database operation failed during client listing",
                error_code="DATABASE_ERROR",
                original_error=e,
            ) from e

    async def _check_ssn_uniqueness(self, ssn: str, exclude_client_id: UUID | None = None) -> None:
        """Check if SSN is unique in the database.

        Args:
            ssn: SSN to check for uniqueness
            exclude_client_id: Optional client ID to exclude from check (for updates)

        Raises:
            ConflictError: If SSN already exists
        """
        statement = select(Client).where(Client.ssn == ssn)
        if exclude_client_id:
            statement = statement.where(Client.client_id != exclude_client_id)

        result = self.session.exec(statement)
        existing_client = result.first()

        if existing_client:
            raise ConflictError(
                message="A client with this SSN already exists",
                error_code="SSN_DUPLICATE",
                details={"ssn": ssn, "existing_client_id": str(existing_client.client_id)},
            )
