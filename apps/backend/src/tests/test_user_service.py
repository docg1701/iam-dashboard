"""
Tests for UserService.

This module tests the business logic layer for user management,
including CRUD operations, role validation, and audit logging.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session

from src.core.exceptions import ConflictError, DatabaseError, ValidationError
from src.models.user import User, UserRole
from src.schemas.users import UserCreateRequest, UserSearchParams, UserUpdateRequest
from src.services.user_service import UserService
from src.tests.factories import UserFactory


class TestUserService:
    """Tests for UserService class."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_request(self) -> MagicMock:
        """Create a mock FastAPI request."""
        request = MagicMock(spec=Request)
        request.headers = {"User-Agent": "test-agent"}
        request.client.host = "127.0.0.1"
        return request

    @pytest.fixture
    def user_service(self, mock_session: MagicMock) -> UserService:
        """Create UserService instance with mocked session."""
        return UserService(mock_session)

    @pytest.fixture
    def sysadmin_user(self) -> User:
        """Create a sysadmin user for testing."""
        return UserFactory.build(role=UserRole.SYSADMIN)

    @pytest.fixture
    def admin_user(self) -> User:
        """Create an admin user for testing."""
        return UserFactory.build(role=UserRole.ADMIN)

    @pytest.fixture
    def regular_user(self) -> User:
        """Create a regular user for testing."""
        return UserFactory.build(role=UserRole.USER)

    @pytest.fixture
    def user_create_request(self) -> UserCreateRequest:
        """Create a valid user creation request."""
        return UserCreateRequest(
            email="newuser@example.com",
            role=UserRole.ADMIN,
            password="SecurePass123!",
            is_active=True,
        )

    async def test_create_user_success(
        self,
        user_service: UserService,
        user_create_request: UserCreateRequest,
        sysadmin_user: User,
        mock_request: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test successful user creation by sysadmin."""
        # Mock dependencies
        with patch("src.services.user_service.log_database_action") as mock_audit:
            # Mock email uniqueness check (no existing user)
            mock_session.exec.return_value.first.side_effect = [None, sysadmin_user]

            # Mock password hashing
            with patch.object(user_service.auth_service, "get_password_hash", return_value="hashed_password"):
                # Call method
                _result = await user_service.create_user(
                    user_data=user_create_request,
                    created_by_user_id=sysadmin_user.user_id,
                    request=mock_request,
                )

                # Verify user was added to session
                mock_session.add.assert_called_once()
                mock_session.commit.assert_called_once()
                mock_session.refresh.assert_called_once()

                # Verify audit logging
                mock_audit.assert_called_once()

    async def test_create_user_duplicate_email(
        self,
        user_service: UserService,
        user_create_request: UserCreateRequest,
        sysadmin_user: User,
        regular_user: User,
        mock_request: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test user creation fails with duplicate email."""
        # Mock existing user with same email
        mock_session.exec.return_value.first.side_effect = [regular_user, sysadmin_user]

        with pytest.raises(ConflictError) as excinfo:
            await user_service.create_user(
                user_data=user_create_request,
                created_by_user_id=sysadmin_user.user_id,
                request=mock_request,
            )

        assert "email already exists" in str(excinfo.value.message)
        assert excinfo.value.error_code == "EMAIL_DUPLICATE"

    async def test_create_user_permission_denied(
        self,
        user_service: UserService,
        user_create_request: UserCreateRequest,
        admin_user: User,
        mock_request: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test user creation fails when non-sysadmin tries to create user."""
        # Mock no existing user with email, but admin user making request
        mock_session.exec.return_value.first.side_effect = [None, admin_user]

        with pytest.raises(ValidationError) as excinfo:
            await user_service.create_user(
                user_data=user_create_request,
                created_by_user_id=admin_user.user_id,
                request=mock_request,
            )

        assert "Only system administrators" in str(excinfo.value.message)
        assert excinfo.value.error_code == "PERMISSION_DENIED"

    async def test_get_user_by_id_success_own_profile(
        self,
        user_service: UserService,
        regular_user: User,
        mock_session: MagicMock,
    ) -> None:
        """Test user can view their own profile."""
        # Mock user lookup - service makes two calls, first for requesting user, then for target user (even if same)
        mock_session.exec.return_value.first.return_value = regular_user

        result = await user_service.get_user_by_id(
            user_id=regular_user.user_id,
            requesting_user_id=regular_user.user_id,
        )

        assert result == regular_user
        assert mock_session.exec.call_count == 2  # Two queries (requesting user + target user)

    async def test_get_user_by_id_success_sysadmin_view_other(
        self,
        user_service: UserService,
        sysadmin_user: User,
        regular_user: User,
        mock_session: MagicMock,
    ) -> None:
        """Test sysadmin can view other users."""
        # Mock user lookups - first for requesting user, then for target user
        mock_session.exec.return_value.first.side_effect = [sysadmin_user, regular_user]

        result = await user_service.get_user_by_id(
            user_id=regular_user.user_id,
            requesting_user_id=sysadmin_user.user_id,
        )

        assert result == regular_user
        assert mock_session.exec.call_count == 2

    @pytest.mark.asyncio
    async def test_get_user_by_id_permission_denied(
        self,
        user_service: UserService,
        admin_user: User,
        regular_user: User,
        mock_session: MagicMock,
    ) -> None:
        """Test non-sysadmin cannot view other users."""
        # Mock requesting user lookup
        mock_session.exec.return_value.first.return_value = admin_user

        with pytest.raises(ValidationError) as excinfo:
            await user_service.get_user_by_id(
                user_id=regular_user.user_id,
                requesting_user_id=admin_user.user_id,
            )

        assert "Insufficient permissions" in str(excinfo.value.message)
        assert excinfo.value.error_code == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_update_user_success_own_profile(
        self,
        user_service: UserService,
        regular_user: User,
        mock_request: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test user can update their own email and password."""
        update_data = UserUpdateRequest(
            email="updated@example.com",
            password="NewSecurePass456!"
        )

        with patch("src.services.user_service.log_database_action") as mock_audit:
            # Mock user lookups with more generous returns - for this test we just return user for all
            mock_session.exec.return_value.first.return_value = regular_user

            # Mock the email uniqueness check separately to return None to avoid conflict
            with (
                patch.object(user_service, "_check_email_uniqueness", return_value=None),
                patch.object(user_service.auth_service, "get_password_hash", return_value="new_hashed_password"),
            ):
                _result = await user_service.update_user(
                    user_id=regular_user.user_id,
                    user_data=update_data,
                    updated_by_user_id=regular_user.user_id,
                    request=mock_request,
                )

            # Verify commit and audit
            mock_session.commit.assert_called_once()
            mock_audit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_role_permission_denied(
        self,
        user_service: UserService,
        regular_user: User,
        mock_request: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test user cannot update their own role."""
        update_data = UserUpdateRequest(role=UserRole.ADMIN)

        # Mock user lookup
        mock_session.exec.return_value.first.return_value = regular_user

        with pytest.raises(ValidationError) as excinfo:
            await user_service.update_user(
                user_id=regular_user.user_id,
                user_data=update_data,
                updated_by_user_id=regular_user.user_id,
                request=mock_request,
            )

        assert "cannot modify their own role" in str(excinfo.value.message)
        assert excinfo.value.error_code == "SELF_MODIFICATION_DENIED"

    @pytest.mark.asyncio
    async def test_deactivate_user_success(
        self,
        user_service: UserService,
        sysadmin_user: User,
        regular_user: User,
        mock_request: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test sysadmin can deactivate user."""
        with patch("src.services.user_service.log_database_action") as mock_audit:
            # Mock user lookups
            mock_session.exec.return_value.first.side_effect = [regular_user, sysadmin_user]

            _result = await user_service.deactivate_user(
                user_id=regular_user.user_id,
                deactivated_by_user_id=sysadmin_user.user_id,
                request=mock_request,
            )

            # Verify user was deactivated
            assert regular_user.is_active is False
            mock_session.commit.assert_called_once()
            mock_audit.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_user_self_deactivation_denied(
        self,
        user_service: UserService,
        sysadmin_user: User,
        mock_request: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test user cannot deactivate themselves."""
        # Mock user lookup
        mock_session.exec.return_value.first.return_value = sysadmin_user

        with pytest.raises(ValidationError) as excinfo:
            await user_service.deactivate_user(
                user_id=sysadmin_user.user_id,
                deactivated_by_user_id=sysadmin_user.user_id,
                request=mock_request,
            )

        assert "Cannot deactivate your own account" in str(excinfo.value.message)
        assert excinfo.value.error_code == "SELF_DEACTIVATION_DENIED"

    @pytest.mark.asyncio
    async def test_deactivate_user_permission_denied(
        self,
        user_service: UserService,
        admin_user: User,
        regular_user: User,
        mock_request: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test non-sysadmin cannot deactivate users."""
        # Mock user lookups
        mock_session.exec.return_value.first.side_effect = [regular_user, admin_user]

        with pytest.raises(ValidationError) as excinfo:
            await user_service.deactivate_user(
                user_id=regular_user.user_id,
                deactivated_by_user_id=admin_user.user_id,
                request=mock_request,
            )

        assert "Only system administrators" in str(excinfo.value.message)
        assert excinfo.value.error_code == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_list_users_success(
        self,
        user_service: UserService,
        sysadmin_user: User,
        mock_session: MagicMock,
    ) -> None:
        """Test listing users with pagination."""
        # Mock requesting user and user list
        users_list = [UserFactory.build() for _ in range(5)]
        mock_session.exec.return_value.first.return_value = sysadmin_user
        mock_session.exec.return_value.all.side_effect = [
            [user.user_id for user in users_list],  # count query
            users_list,  # actual query
        ]

        search_params = UserSearchParams()
        result_items, total_count = await user_service.list_users(
            search_params=search_params,
            page=1,
            per_page=10,
            requesting_user_id=sysadmin_user.user_id,
        )

        assert len(result_items) == 5
        assert total_count == 5

    @pytest.mark.asyncio
    async def test_list_users_with_filters(
        self,
        user_service: UserService,
        sysadmin_user: User,
        mock_session: MagicMock,
    ) -> None:
        """Test listing users with search filters."""
        filtered_users = [UserFactory.build(role=UserRole.ADMIN)]
        mock_session.exec.return_value.first.return_value = sysadmin_user
        mock_session.exec.return_value.all.side_effect = [
            [user.user_id for user in filtered_users],  # count query
            filtered_users,  # actual query
        ]

        search_params = UserSearchParams(
            query="admin@example.com",
            role=UserRole.ADMIN,
            is_active=True,
        )

        result_items, total_count = await user_service.list_users(
            search_params=search_params,
            page=1,
            per_page=10,
            requesting_user_id=sysadmin_user.user_id,
        )

        assert len(result_items) == 1
        assert total_count == 1
        assert result_items[0].role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_list_users_permission_denied(
        self,
        user_service: UserService,
        regular_user: User,
        mock_session: MagicMock,
    ) -> None:
        """Test non-admin cannot list users."""
        # Mock requesting user
        mock_session.exec.return_value.first.return_value = regular_user

        search_params = UserSearchParams()

        with pytest.raises(ValidationError) as excinfo:
            await user_service.list_users(
                search_params=search_params,
                page=1,
                per_page=10,
                requesting_user_id=regular_user.user_id,
            )

        assert "Insufficient permissions" in str(excinfo.value.message)
        assert excinfo.value.error_code == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_database_error_handling(
        self,
        user_service: UserService,
        sysadmin_user: User,
        mock_request: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test database error handling."""
        user_create_request = UserCreateRequest(
            email="test@example.com",
            role=UserRole.USER,
            password="SecurePass123!",
            is_active=True,
        )

        # Mock database error
        mock_session.exec.side_effect = SQLAlchemyError("Database connection failed")

        with pytest.raises(DatabaseError) as excinfo:
            await user_service.create_user(
                user_data=user_create_request,
                created_by_user_id=sysadmin_user.user_id,
                request=mock_request,
            )

        # First database error occurs during email uniqueness check
        assert "Failed to check email uniqueness" in str(excinfo.value.message) or "Failed to create user" in str(excinfo.value.message)
        assert excinfo.value.error_code == "DATABASE_ERROR"

    @pytest.mark.asyncio
    async def test_integrity_error_handling(
        self,
        user_service: UserService,
        user_create_request: UserCreateRequest,
        sysadmin_user: User,
        mock_request: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test integrity error handling for duplicate email."""
        # Mock no existing user for uniqueness check, but integrity error on commit
        mock_session.exec.return_value.first.side_effect = [None, sysadmin_user]

        # Mock integrity error with "email" in message
        integrity_error = IntegrityError("email constraint", None, None)
        integrity_error.orig = "email constraint violation"
        mock_session.commit.side_effect = integrity_error

        with patch.object(user_service.auth_service, "get_password_hash", return_value="hashed_password"):
            with pytest.raises(ConflictError) as excinfo:
                await user_service.create_user(
                    user_data=user_create_request,
                    created_by_user_id=sysadmin_user.user_id,
                    request=mock_request,
                )

            assert "email already exists" in str(excinfo.value.message)
            assert excinfo.value.error_code == "EMAIL_DUPLICATE"
            mock_session.rollback.assert_called_once()
