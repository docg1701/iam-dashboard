"""
User service layer for business logic operations.

This module contains the UserService class that handles user management
operations including creation, updates, role validation, and audit logging.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import Request
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import desc, func, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, and_, select

from src.core.exceptions import ConflictError, DatabaseError, NotFoundError, ValidationError
from src.core.security import SecureAuthService
from src.models.audit import AuditAction
from src.models.user import User, UserCreate, UserRole
from src.schemas.users import (
    UserCreateRequest,
    UserListItem,
    UserSearchParams,
    UserUpdateRequest,
)
from src.utils.audit import log_database_action, prepare_audit_data


class UserService:
    """Service class for user management operations."""

    def __init__(self, session: Session):
        """Initialize UserService with database session.

        Args:
            session: SQLModel database session
        """
        self.session = session
        self.auth_service = SecureAuthService()

    async def create_user(
        self,
        user_data: UserCreateRequest,
        created_by_user_id: UUID,
        request: Request,
    ) -> User:
        """Create a new user with comprehensive validation and audit logging.

        Args:
            user_data: User creation data from API request
            created_by_user_id: ID of user creating the new user
            request: FastAPI request object for audit logging

        Returns:
            User: Created user data

        Raises:
            ValidationError: If user data validation fails
            ConflictError: If email already exists
            DatabaseError: If database operation fails
        """
        try:
            # Check for existing email to prevent duplicates
            await self._check_email_uniqueness(user_data.email)

            # Validate role assignment permissions
            await self._validate_role_assignment(created_by_user_id, user_data.role)

            # Hash the password
            password_hash = self.auth_service.get_password_hash(user_data.password)

            # Create SQLModel instance from schema data
            user_create = UserCreate(
                email=user_data.email,
                role=user_data.role,
                is_active=user_data.is_active,
                password=user_data.password,  # UserCreate will handle hashing validation
                totp_enabled=False,
                last_login=None,
            )

            # Create User instance for database
            user = User(
                email=user_create.email,
                role=user_create.role,
                is_active=user_create.is_active,
                totp_enabled=user_create.totp_enabled,
                last_login=user_create.last_login,
                password_hash=password_hash,
                totp_secret=None,
                totp_backup_codes=None,
                created_at=datetime.utcnow(),
                updated_at=None,
            )

            # Add to session and commit
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)

            # Create audit log
            await log_database_action(
                session=self.session,
                action=AuditAction.CREATE,
                table_name="users",
                record_id=str(user.user_id),
                user_id=created_by_user_id,
                request=request,
                new_data=prepare_audit_data(user),
            )

            return user

        except IntegrityError as e:
            self.session.rollback()
            if "email" in str(e.orig):
                raise ConflictError(
                    message="A user with this email already exists",
                    error_code="EMAIL_DUPLICATE",
                    details={"email": str(user_data.email)},
                ) from e
            raise DatabaseError(
                message="Failed to create user due to database constraint",
                error_code="CONSTRAINT_VIOLATION",
                original_error=e,
            ) from e

        except PydanticValidationError as e:
            self.session.rollback()
            raise ValidationError(
                message="User data validation failed",
                error_code="VALIDATION_ERROR",
                details={"validation_errors": e.errors()},
            ) from e

        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(
                message="Failed to create user due to database error",
                error_code="DATABASE_ERROR",
                original_error=e,
            ) from e

    async def get_user_by_id(self, user_id: UUID, requesting_user_id: UUID) -> User:
        """Retrieve a user by ID with permission checking.

        Args:
            user_id: ID of user to retrieve
            requesting_user_id: ID of user making the request

        Returns:
            User: User data

        Raises:
            NotFoundError: If user doesn't exist
            ValidationError: If user lacks permission to view user
        """
        # Get requesting user to check permissions
        requesting_user = await self._get_user_by_id_internal(requesting_user_id)

        # Users can view their own profile, sysadmins can view all
        if user_id != requesting_user_id and requesting_user.role != UserRole.SYSADMIN:
            raise ValidationError(
                message="Insufficient permissions to view user",
                error_code="PERMISSION_DENIED",
                details={"required_role": "sysadmin", "user_role": requesting_user.role},
            )

        return await self._get_user_by_id_internal(user_id)

    async def update_user(
        self,
        user_id: UUID,
        user_data: UserUpdateRequest,
        updated_by_user_id: UUID,
        request: Request,
    ) -> User:
        """Update user information with validation and audit logging.

        Args:
            user_id: ID of user to update
            user_data: User update data
            updated_by_user_id: ID of user performing the update
            request: FastAPI request object for audit logging

        Returns:
            User: Updated user data

        Raises:
            NotFoundError: If user doesn't exist
            ConflictError: If email already exists
            ValidationError: If update data is invalid or permission denied
            DatabaseError: If database operation fails
        """
        try:
            # Get existing user
            existing_user = await self._get_user_by_id_internal(user_id)
            old_data = prepare_audit_data(existing_user)

            # Check permissions for user updates
            await self._validate_user_update_permissions(updated_by_user_id, user_id, user_data)

            # Check email uniqueness if email is being changed
            if user_data.email and user_data.email != existing_user.email:
                await self._check_email_uniqueness(user_data.email, exclude_user_id=user_id)

            # Validate role assignment if role is being changed
            if user_data.role and user_data.role != existing_user.role:
                await self._validate_role_assignment(updated_by_user_id, user_data.role)

            # Update fields directly on the user object
            if user_data.email:
                existing_user.email = user_data.email
            if user_data.role:
                existing_user.role = user_data.role
            if user_data.is_active is not None:
                existing_user.is_active = user_data.is_active
            if user_data.password:
                existing_user.password_hash = self.auth_service.get_password_hash(
                    user_data.password
                )

            # Add updated timestamp
            existing_user.updated_at = datetime.utcnow()

            self.session.commit()
            self.session.refresh(existing_user)

            # Create audit log
            await log_database_action(
                session=self.session,
                action=AuditAction.UPDATE,
                table_name="users",
                record_id=str(user_id),
                user_id=updated_by_user_id,
                request=request,
                old_data=old_data,
                new_data=prepare_audit_data(existing_user),
            )

            return existing_user

        except IntegrityError as e:
            self.session.rollback()
            if "email" in str(e.orig):
                raise ConflictError(
                    message="A user with this email already exists",
                    error_code="EMAIL_DUPLICATE",
                    details={"email": str(user_data.email) if user_data.email else None},
                ) from e
            raise DatabaseError(
                message="Failed to update user due to database constraint",
                error_code="CONSTRAINT_VIOLATION",
                original_error=e,
            ) from e

        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(
                message="Failed to update user due to database error",
                error_code="DATABASE_ERROR",
                original_error=e,
            ) from e

    async def deactivate_user(
        self,
        user_id: UUID,
        deactivated_by_user_id: UUID,
        request: Request,
    ) -> User:
        """Deactivate a user account (soft delete).

        Args:
            user_id: ID of user to deactivate
            deactivated_by_user_id: ID of user performing the deactivation
            request: FastAPI request object for audit logging

        Returns:
            User: Deactivated user data

        Raises:
            NotFoundError: If user doesn't exist
            ValidationError: If permission denied or trying to deactivate self
            DatabaseError: If database operation fails
        """
        try:
            # Get existing user
            existing_user = await self._get_user_by_id_internal(user_id)

            # Prevent self-deactivation
            if user_id == deactivated_by_user_id:
                raise ValidationError(
                    message="Cannot deactivate your own account",
                    error_code="SELF_DEACTIVATION_DENIED",
                    details={"user_id": str(user_id)},
                )

            # Check permissions (only sysadmin can deactivate users)
            deactivating_user = await self._get_user_by_id_internal(deactivated_by_user_id)
            if deactivating_user.role != UserRole.SYSADMIN:
                raise ValidationError(
                    message="Only system administrators can deactivate users",
                    error_code="PERMISSION_DENIED",
                    details={"required_role": "sysadmin", "user_role": deactivating_user.role},
                )

            old_data = prepare_audit_data(existing_user)

            # Deactivate user
            existing_user.is_active = False
            existing_user.updated_at = datetime.utcnow()

            self.session.commit()
            self.session.refresh(existing_user)

            # Create audit log
            await log_database_action(
                session=self.session,
                action=AuditAction.DELETE,  # Soft delete
                table_name="users",
                record_id=str(user_id),
                user_id=deactivated_by_user_id,
                request=request,
                old_data=old_data,
                new_data=prepare_audit_data(existing_user),
            )

            return existing_user

        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(
                message="Failed to deactivate user due to database error",
                error_code="DATABASE_ERROR",
                original_error=e,
            ) from e

    async def list_users(
        self,
        search_params: UserSearchParams,
        page: int = 1,
        per_page: int = 20,
        requesting_user_id: UUID | None = None,
    ) -> tuple[list[UserListItem], int]:
        """List users with search, filtering, and pagination.

        Args:
            search_params: Search and filter parameters
            page: Page number (1-based)
            per_page: Number of items per page
            requesting_user_id: ID of user making the request (for permission checking)

        Returns:
            tuple[list[UserListItem], int]: List of users and total count

        Raises:
            ValidationError: If requesting user lacks permission
        """
        try:
            # Check permissions (only sysadmin and admin can list users)
            if requesting_user_id:
                requesting_user = await self._get_user_by_id_internal(requesting_user_id)
                if requesting_user.role not in [UserRole.SYSADMIN, UserRole.ADMIN]:
                    raise ValidationError(
                        message="Insufficient permissions to list users",
                        error_code="PERMISSION_DENIED",
                        details={"required_role": "admin", "user_role": requesting_user.role},
                    )

            # Build query
            query = select(User)

            # Apply filters
            conditions: list[Any] = []

            if search_params.query:
                conditions.append(func.lower(User.email).contains(search_params.query.lower()))

            if search_params.role:
                conditions.append(User.role == search_params.role)

            if search_params.is_active is not None:
                conditions.append(User.is_active == search_params.is_active)

            if conditions:
                query = query.where(and_(*conditions))

            # Get total count
            if conditions:
                count_query = select(User.user_id).where(and_(*conditions))
            else:
                count_query = select(User.user_id)
            total_count = len(self.session.exec(count_query).all())

            # Apply pagination and ordering
            offset = (page - 1) * per_page
            query = query.order_by(desc(text("created_at"))).offset(offset).limit(per_page)

            # Execute query
            users = self.session.exec(query).all()

            # Convert to list items
            user_items = [
                UserListItem(
                    user_id=user.user_id,
                    email=user.email,
                    role=user.role,
                    is_active=user.is_active,
                    totp_enabled=user.totp_enabled,
                    last_login=user.last_login,
                    created_at=user.created_at,
                )
                for user in users
            ]

            return user_items, total_count

        except SQLAlchemyError as e:
            raise DatabaseError(
                message="Failed to list users due to database error",
                error_code="DATABASE_ERROR",
                original_error=e,
            ) from e

    async def _get_user_by_id_internal(self, user_id: UUID) -> User:
        """Internal method to get user by ID without permission checking.

        Args:
            user_id: ID of user to retrieve

        Returns:
            User: User data

        Raises:
            NotFoundError: If user doesn't exist
        """
        try:
            statement = select(User).where(User.user_id == user_id)
            user = self.session.exec(statement).first()

            if not user:
                raise NotFoundError(
                    message="User not found",
                    error_code="USER_NOT_FOUND",
                    details={"user_id": str(user_id)},
                )

            return user

        except SQLAlchemyError as e:
            raise DatabaseError(
                message="Failed to retrieve user due to database error",
                error_code="DATABASE_ERROR",
                original_error=e,
            ) from e

    async def _check_email_uniqueness(
        self, email: str, exclude_user_id: UUID | None = None
    ) -> None:
        """Check if email is unique in the database.

        Args:
            email: Email to check
            exclude_user_id: User ID to exclude from check (for updates)

        Raises:
            ConflictError: If email already exists
        """
        try:
            statement = select(User).where(User.email == email)
            if exclude_user_id:
                statement = statement.where(User.user_id != exclude_user_id)

            existing_user = self.session.exec(statement).first()

            if existing_user:
                raise ConflictError(
                    message="A user with this email already exists",
                    error_code="EMAIL_DUPLICATE",
                    details={"email": email},
                )

        except SQLAlchemyError as e:
            raise DatabaseError(
                message="Failed to check email uniqueness",
                error_code="DATABASE_ERROR",
                original_error=e,
            ) from e

    async def _validate_role_assignment(
        self, assigning_user_id: UUID, target_role: UserRole
    ) -> None:
        """Validate that user has permission to assign the target role.

        Args:
            assigning_user_id: ID of user assigning the role
            target_role: Role being assigned

        Raises:
            ValidationError: If user lacks permission to assign role
        """
        assigning_user = await self._get_user_by_id_internal(assigning_user_id)

        # Only sysadmin can assign any role
        if assigning_user.role != UserRole.SYSADMIN:
            raise ValidationError(
                message="Only system administrators can create or modify user accounts",
                error_code="PERMISSION_DENIED",
                details={
                    "required_role": "sysadmin",
                    "user_role": assigning_user.role,
                    "target_role": target_role,
                },
            )

    async def _validate_user_update_permissions(
        self,
        updating_user_id: UUID,
        target_user_id: UUID,
        update_data: UserUpdateRequest,
    ) -> None:
        """Validate permissions for user update operations.

        Args:
            updating_user_id: ID of user performing the update
            target_user_id: ID of user being updated
            update_data: Data being updated

        Raises:
            ValidationError: If user lacks permission for the update
        """
        updating_user = await self._get_user_by_id_internal(updating_user_id)

        # Users can update their own email and password (but not role or active status)
        if updating_user_id == target_user_id:
            if update_data.role is not None or update_data.is_active is not None:
                raise ValidationError(
                    message="Users cannot modify their own role or account status",
                    error_code="SELF_MODIFICATION_DENIED",
                    details={"user_id": str(target_user_id)},
                )
            return

        # Only sysadmin can update other users
        if updating_user.role != UserRole.SYSADMIN:
            raise ValidationError(
                message="Only system administrators can modify other user accounts",
                error_code="PERMISSION_DENIED",
                details={
                    "required_role": "sysadmin",
                    "user_role": updating_user.role,
                },
            )
