"""
Tests for UserService.

This module tests the business logic layer for user management,
including CRUD operations, role validation, and audit logging.
Follows CLAUDE.md directives: Only mock external dependencies, never mock business logic.
"""

from typing import cast
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import Request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, select

from src.core.exceptions import ConflictError, DatabaseError, NotFoundError, ValidationError
from src.models.user import User, UserRole
from src.schemas.users import UserCreateRequest, UserSearchParams, UserUpdateRequest
from src.services.user_service import UserService
from src.tests.factories import UserFactory


class TestUserService:
    """Tests for UserService class."""

    # NOTE: Unit tests should NOT mock database sessions according to CLAUDE.md
    # Database operations are part of the business logic we need to test

    @pytest.fixture
    def mock_request(self) -> MagicMock:
        """Create a mock FastAPI request."""
        request = MagicMock(spec=Request)
        request.headers = {"User-Agent": "test-agent"}
        request.client.host = "127.0.0.1"
        return request

    @pytest.fixture
    def user_service(self, test_session: Session) -> UserService:
        """Create UserService instance with real test database session."""
        return UserService(test_session)

    @pytest.fixture
    def sysadmin_user(self) -> User:
        """Create a sysadmin user for testing."""
        return cast("User", UserFactory.build(role=UserRole.SYSADMIN))

    @pytest.fixture
    def admin_user(self) -> User:
        """Create an admin user for testing."""
        return cast("User", UserFactory.build(role=UserRole.ADMIN))

    @pytest.fixture
    def regular_user(self) -> User:
        """Create a regular user for testing."""
        return cast("User", UserFactory.build(role=UserRole.USER))

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
        test_session: Session,
    ) -> None:
        """Test successful user creation by sysadmin with real database operations."""
        # Add sysadmin to database first
        test_session.add(sysadmin_user)
        test_session.commit()
        
        # Mock ONLY external dependencies (password hashing, audit logging)
        with patch("src.services.user_service.log_database_action") as mock_audit:
            # Mock password hashing (external dependency)
            with patch.object(
                user_service.auth_service, "get_password_hash", return_value="hashed_password"
            ):
                # Call method - this will use real database operations
                result = await user_service.create_user(
                    user_data=user_create_request,
                    created_by_user_id=sysadmin_user.user_id,
                    request=mock_request,
                )

                # Verify user was created with real database operations
                assert result.email == user_create_request.email
                assert result.role == user_create_request.role
                assert result.is_active == user_create_request.is_active
                assert result.password_hash == "hashed_password"
                
                # Verify audit logging (external dependency) was called
                mock_audit.assert_called_once()

    async def test_create_user_duplicate_email(
        self,
        user_service: UserService,
        user_create_request: UserCreateRequest,
        sysadmin_user: User,
        regular_user: User,
        mock_request: MagicMock,
        test_session: Session,
    ) -> None:
        """Test user creation fails with duplicate email using real database operations."""
        # Set up real database state - add existing user with same email
        regular_user.email = user_create_request.email  # Same email
        test_session.add_all([sysadmin_user, regular_user])
        test_session.commit()

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
        test_session: Session,
    ) -> None:
        """Test user creation fails when non-sysadmin tries to create user using real database operations."""
        # Add admin user to database (not sysadmin)
        test_session.add(admin_user)
        test_session.commit()

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
        test_session: Session,
    ) -> None:
        """Test user can view their own profile using real database operations."""
        # Add user to database
        test_session.add(regular_user)
        test_session.commit()

        result = await user_service.get_user_by_id(
            user_id=regular_user.user_id,
            requesting_user_id=regular_user.user_id,
        )

        assert result.user_id == regular_user.user_id
        assert result.email == regular_user.email
        assert result.role == regular_user.role

    async def test_get_user_by_id_success_sysadmin_view_other(
        self,
        user_service: UserService,
        sysadmin_user: User,
        regular_user: User,
        test_session: Session,
    ) -> None:
        """Test sysadmin can view other users using real database operations."""
        # Add both users to database
        test_session.add_all([sysadmin_user, regular_user])
        test_session.commit()

        result = await user_service.get_user_by_id(
            user_id=regular_user.user_id,
            requesting_user_id=sysadmin_user.user_id,
        )

        assert result.user_id == regular_user.user_id
        assert result.email == regular_user.email
        assert result.role == regular_user.role

    @pytest.mark.asyncio
    async def test_get_user_by_id_permission_denied(
        self,
        user_service: UserService,
        admin_user: User,
        regular_user: User,
        test_session: Session,
    ) -> None:
        """Test non-sysadmin cannot view other users using real database operations."""
        # Add both users to database
        test_session.add_all([admin_user, regular_user])
        test_session.commit()

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
        test_session: Session,
    ) -> None:
        """Test user can update their own email and password using real database operations."""
        # Add user to database
        test_session.add(regular_user)
        test_session.commit()
        
        update_data = UserUpdateRequest(email="updated@example.com", password="NewSecurePass456!")

        with patch("src.services.user_service.log_database_action") as mock_audit:
            # Mock password hashing (external dependency)
            with patch.object(
                user_service.auth_service,
                "get_password_hash",
                return_value="new_hashed_password",
            ):
                result = await user_service.update_user(
                    user_id=regular_user.user_id,
                    user_data=update_data,
                    updated_by_user_id=regular_user.user_id,
                    request=mock_request,
                )

            # Verify user was updated with real database operations
            assert result.email == "updated@example.com"
            assert result.password_hash == "new_hashed_password"
            # Verify audit logging (external dependency) was called
            mock_audit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_role_permission_denied(
        self,
        user_service: UserService,
        regular_user: User,
        mock_request: MagicMock,
        test_session: Session,
    ) -> None:
        """Test user cannot update their own role using real database operations."""
        # Add user to database
        test_session.add(regular_user)
        test_session.commit()
        
        update_data = UserUpdateRequest(role=UserRole.ADMIN)

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

    # NOTE: Database error tests moved to integration tests since they require real database operations
    # Unit tests should focus on business logic, not database failure scenarios

    # NOTE: Integrity error tests moved to integration tests since they require real database constraints
    # Unit tests should focus on business logic validation, not database-level integrity errors


class TestUserServiceIntegration:
    """Integration tests using real database session."""

    @pytest.mark.asyncio
    async def test_create_user_integration_success(self, test_session: Session) -> None:
        """Test user creation with real database session."""
        # Create a sysadmin user first
        sysadmin = UserFactory(role=UserRole.SYSADMIN)
        test_session.add(sysadmin)
        test_session.commit()
        test_session.refresh(sysadmin)

        # Create user service
        user_service = UserService(test_session)

        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"User-Agent": "test-agent"}
        mock_request.client.host = "127.0.0.1"

        # User creation data
        user_data = UserCreateRequest(
            email="integration@test.com",
            role=UserRole.ADMIN,
            password="SecurePass123!",
            is_active=True,
        )

        # Create user
        result = await user_service.create_user(
            user_data=user_data,
            created_by_user_id=sysadmin.user_id,
            request=mock_request,
        )

        # Verify result
        assert result.email == user_data.email
        assert result.role == user_data.role
        assert result.is_active == user_data.is_active
        assert result.password_hash is not None
        assert result.created_at is not None

        # Verify in database

        db_user = test_session.exec(select(User).where(User.user_id == result.user_id)).first()
        assert db_user is not None
        assert db_user.email == user_data.email

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_integration(self, test_session: Session) -> None:
        """Test user creation fails with duplicate email (real database)."""
        # Create a sysadmin user
        sysadmin = UserFactory(role=UserRole.SYSADMIN)
        test_session.add(sysadmin)

        # Create existing user
        existing_user = UserFactory(email="duplicate@example.com")
        test_session.add(existing_user)
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"User-Agent": "test-agent"}
        mock_request.client.host = "127.0.0.1"

        # Try to create user with same email
        user_data = UserCreateRequest(
            email="duplicate@example.com",
            role=UserRole.USER,
            password="SecurePass123!",
            is_active=True,
        )

        with pytest.raises(ConflictError) as exc_info:
            await user_service.create_user(
                user_data=user_data,
                created_by_user_id=sysadmin.user_id,
                request=mock_request,
            )

        assert "email already exists" in str(exc_info.value.message).lower()
        assert exc_info.value.error_code == "EMAIL_DUPLICATE"

    @pytest.mark.asyncio
    async def test_get_user_by_id_integration(self, test_session: Session) -> None:
        """Test get user by ID with real database."""


        # Create test user directly instead of using factory
        test_user = User(
            user_id=uuid4(),
            email="test@example.com",
            role=UserRole.USER,
            is_active=True,
            password_hash="test_hash",
            full_name="Test User",
        )
        test_session.add(test_user)
        test_session.commit()
        test_session.refresh(test_user)

        # Create user service
        user_service = UserService(test_session)

        # User should be able to view their own profile
        result = await user_service.get_user_by_id(
            user_id=test_user.user_id,
            requesting_user_id=test_user.user_id,
        )

        assert result.user_id == test_user.user_id
        assert result.email == test_user.email
        assert result.role == test_user.role

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found_integration(self, test_session: Session) -> None:
        """Test get user by ID with non-existent user."""
        # Create user service
        user_service = UserService(test_session)

        # Create a user to make the request
        requesting_user = UserFactory(role=UserRole.SYSADMIN)
        test_session.add(requesting_user)
        test_session.commit()

        # Try to get non-existent user
        non_existent_id = uuid4()

        with pytest.raises(NotFoundError) as exc_info:
            await user_service.get_user_by_id(
                user_id=non_existent_id,
                requesting_user_id=requesting_user.user_id,
            )

        assert "not found" in str(exc_info.value.message).lower()
        assert exc_info.value.error_code == "USER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_update_user_integration_success(self, test_session: Session) -> None:
        """Test user update with real database."""
        # Create test user directly to avoid factory issues


        test_user = User(
            user_id=uuid4(),
            email="original@example.com",
            role=UserRole.USER,
            is_active=True,
            password_hash="test_hash",
            full_name="Test User",
        )
        test_session.add(test_user)
        test_session.commit()
        test_session.refresh(test_user)

        # Create user service
        user_service = UserService(test_session)

        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"User-Agent": "test-agent"}
        mock_request.client.host = "127.0.0.1"

        # Update data (user updating their own email)
        update_data = UserUpdateRequest(email="updated@example.com")

        # Update user
        result = await user_service.update_user(
            user_id=test_user.user_id,
            user_data=update_data,
            updated_by_user_id=test_user.user_id,
            request=mock_request,
        )

        # Verify result
        assert result.email == "updated@example.com"
        assert result.updated_at is not None

        # Verify in database
        test_session.refresh(test_user)
        assert test_user.email == "updated@example.com"

    @pytest.mark.asyncio
    async def test_update_user_integration_sysadmin_change_role(
        self, test_session: Session
    ) -> None:
        """Test sysadmin can change another user's role."""
        # Create sysadmin and regular user
        sysadmin = UserFactory(role=UserRole.SYSADMIN)
        regular_user = UserFactory(role=UserRole.USER)
        test_session.add_all([sysadmin, regular_user])
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"User-Agent": "test-agent"}
        mock_request.client.host = "127.0.0.1"

        # Update data (change role to admin)
        update_data = UserUpdateRequest(role=UserRole.ADMIN)

        # Update user
        result = await user_service.update_user(
            user_id=regular_user.user_id,
            user_data=update_data,
            updated_by_user_id=sysadmin.user_id,
            request=mock_request,
        )

        # Verify result
        assert result.role == UserRole.ADMIN
        assert result.updated_at is not None

    @pytest.mark.asyncio
    async def test_deactivate_user_integration(self, test_session: Session) -> None:
        """Test user deactivation with real database."""
        # Create sysadmin and regular user
        sysadmin = UserFactory(role=UserRole.SYSADMIN)
        regular_user = UserFactory(role=UserRole.USER, is_active=True)
        test_session.add_all([sysadmin, regular_user])
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"User-Agent": "test-agent"}
        mock_request.client.host = "127.0.0.1"

        # Deactivate user
        result = await user_service.deactivate_user(
            user_id=regular_user.user_id,
            deactivated_by_user_id=sysadmin.user_id,
            request=mock_request,
        )

        # Verify result
        assert result.is_active is False
        assert result.updated_at is not None

        # Verify in database
        test_session.refresh(regular_user)
        assert regular_user.is_active is False

    @pytest.mark.asyncio
    async def test_list_users_integration(self, test_session: Session) -> None:
        """Test list users with real database."""
        # Create sysadmin and some users
        sysadmin = UserFactory(role=UserRole.SYSADMIN)
        users = [
            UserFactory(role=UserRole.USER, email="user1@example.com"),
            UserFactory(role=UserRole.ADMIN, email="admin@example.com"),
            UserFactory(role=UserRole.USER, email="user2@example.com", is_active=False),
        ]
        test_session.add(sysadmin)
        test_session.add_all(users)
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # Search parameters

        search_params = UserSearchParams()

        # List users
        result_items, total_count = await user_service.list_users(
            search_params=search_params,
            page=1,
            per_page=10,
            requesting_user_id=sysadmin.user_id,
        )

        # Verify results (should include sysadmin + 3 users = 4 total)
        assert total_count == 4
        assert len(result_items) == 4

    @pytest.mark.asyncio
    async def test_list_users_with_filters_integration(self, test_session: Session) -> None:
        """Test list users with search filters using real database."""
        # Create sysadmin and users
        sysadmin = UserFactory(role=UserRole.SYSADMIN)
        admin_user = UserFactory(role=UserRole.ADMIN, email="admin@example.com", is_active=True)
        regular_user1 = UserFactory(role=UserRole.USER, email="user1@example.com", is_active=True)
        regular_user2 = UserFactory(role=UserRole.USER, email="user2@example.com", is_active=False)

        test_session.add_all([sysadmin, admin_user, regular_user1, regular_user2])
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # Search for active users only

        search_params = UserSearchParams(is_active=True)

        result_items, total_count = await user_service.list_users(
            search_params=search_params,
            page=1,
            per_page=10,
            requesting_user_id=sysadmin.user_id,
        )

        # Should find 3 active users (sysadmin, admin, user1)
        assert total_count == 3
        assert len(result_items) == 3
        assert all(item.is_active for item in result_items)

        # Search for admins only
        search_params = UserSearchParams(role=UserRole.ADMIN)

        result_items, total_count = await user_service.list_users(
            search_params=search_params,
            page=1,
            per_page=10,
            requesting_user_id=sysadmin.user_id,
        )

        # Should find 1 admin user
        assert total_count == 1
        assert len(result_items) == 1
        assert result_items[0].role == UserRole.ADMIN

        # Search by email query
        search_params = UserSearchParams(query="admin")

        result_items, total_count = await user_service.list_users(
            search_params=search_params,
            page=1,
            per_page=10,
            requesting_user_id=sysadmin.user_id,
        )

        # Should find the admin user
        assert total_count == 1
        assert len(result_items) == 1
        assert "admin" in result_items[0].email

    @pytest.mark.asyncio
    async def test_list_users_pagination_integration(self, test_session: Session) -> None:
        """Test user listing pagination with real database."""
        # Create sysadmin and many users
        sysadmin = UserFactory(role=UserRole.SYSADMIN)
        users = [UserFactory(role=UserRole.USER) for _ in range(5)]
        test_session.add(sysadmin)
        test_session.add_all(users)
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # Search parameters

        search_params = UserSearchParams()

        # Get first page (2 items per page)
        result_items, total_count = await user_service.list_users(
            search_params=search_params,
            page=1,
            per_page=2,
            requesting_user_id=sysadmin.user_id,
        )

        # Should have 6 total users (1 sysadmin + 5 users)
        assert total_count == 6
        assert len(result_items) == 2  # First page with 2 items

        # Get second page
        result_items, total_count = await user_service.list_users(
            search_params=search_params,
            page=2,
            per_page=2,
            requesting_user_id=sysadmin.user_id,
        )

        assert total_count == 6
        assert len(result_items) == 2  # Second page with 2 items

        # Get third page
        result_items, total_count = await user_service.list_users(
            search_params=search_params,
            page=3,
            per_page=2,
            requesting_user_id=sysadmin.user_id,
        )

        assert total_count == 6
        assert len(result_items) == 2  # Third page with 2 items


class TestUserServicePrivateMethods:
    """Test private methods of UserService."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_internal_success(self, test_session: Session) -> None:
        """Test internal get user by ID method."""
        # Create test user directly to avoid factory issues


        test_user = User(
            user_id=uuid4(),
            email="test@example.com",
            role=UserRole.USER,
            is_active=True,
            password_hash="test_hash",
            full_name="Test User",
        )
        test_session.add(test_user)
        test_session.commit()
        test_session.refresh(test_user)

        # Create user service
        user_service = UserService(test_session)

        # Get user by ID (internal method)
        result = await user_service._get_user_by_id_internal(test_user.user_id)

        assert result.user_id == test_user.user_id
        assert result.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_id_internal_not_found(self, test_session: Session) -> None:
        """Test internal get user by ID method with non-existent user."""
        # Create user service
        user_service = UserService(test_session)

        # Try to get non-existent user
        non_existent_id = uuid4()

        with pytest.raises(NotFoundError) as exc_info:
            await user_service._get_user_by_id_internal(non_existent_id)

        assert "not found" in str(exc_info.value.message).lower()
        assert exc_info.value.error_code == "USER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_check_email_uniqueness_success(self, test_session: Session) -> None:
        """Test email uniqueness check with unique email."""
        # Create user service
        user_service = UserService(test_session)

        # Check unique email (should not raise exception)
        try:
            await user_service._check_email_uniqueness("unique@example.com")
        except ConflictError:
            pytest.fail("Email uniqueness check should pass for unique email")

    @pytest.mark.asyncio
    async def test_check_email_uniqueness_duplicate(self, test_session: Session) -> None:
        """Test email uniqueness check with duplicate email."""
        # Create existing user
        existing_user = UserFactory(email="duplicate@example.com")
        test_session.add(existing_user)
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # Check duplicate email
        with pytest.raises(ConflictError) as exc_info:
            await user_service._check_email_uniqueness("duplicate@example.com")

        assert "email already exists" in str(exc_info.value.message).lower()
        assert exc_info.value.error_code == "EMAIL_DUPLICATE"

    @pytest.mark.asyncio
    async def test_check_email_uniqueness_with_exclusion(self, test_session: Session) -> None:
        """Test email uniqueness check with user exclusion for updates."""
        # Create existing user
        existing_user = UserFactory(email="test@example.com")
        test_session.add(existing_user)
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # Check email uniqueness excluding the same user (should pass)
        try:
            await user_service._check_email_uniqueness(
                "test@example.com", exclude_user_id=existing_user.user_id
            )
        except ConflictError:
            pytest.fail("Email uniqueness check should pass when excluding the same user")

    @pytest.mark.asyncio
    async def test_validate_role_assignment_sysadmin(self, test_session: Session) -> None:
        """Test role assignment validation for sysadmin."""
        # Create sysadmin user
        sysadmin = UserFactory(role=UserRole.SYSADMIN)
        test_session.add(sysadmin)
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # Sysadmin should be able to assign any role
        try:
            await user_service._validate_role_assignment(sysadmin.user_id, UserRole.ADMIN)
            await user_service._validate_role_assignment(sysadmin.user_id, UserRole.USER)
            await user_service._validate_role_assignment(sysadmin.user_id, UserRole.SYSADMIN)
        except ValidationError:
            pytest.fail("Sysadmin should be able to assign any role")

    @pytest.mark.asyncio
    async def test_validate_role_assignment_non_sysadmin(self, test_session: Session) -> None:
        """Test role assignment validation for non-sysadmin."""
        # Create admin user
        admin = UserFactory(role=UserRole.ADMIN)
        test_session.add(admin)
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # Admin should not be able to assign roles
        with pytest.raises(ValidationError) as exc_info:
            await user_service._validate_role_assignment(admin.user_id, UserRole.USER)

        assert "Only system administrators" in str(exc_info.value.message)
        assert exc_info.value.error_code == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_validate_user_update_permissions_self_allowed(
        self, test_session: Session
    ) -> None:
        """Test user update permission validation for self updates."""
        # Create regular user
        user = UserFactory(role=UserRole.USER)
        test_session.add(user)
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # User should be able to update their own email and password
        update_data = UserUpdateRequest(email="new@example.com", password="NewPass123!")

        try:
            await user_service._validate_user_update_permissions(
                user.user_id, user.user_id, update_data
            )
        except ValidationError:
            pytest.fail("User should be able to update their own email and password")

    @pytest.mark.asyncio
    async def test_validate_user_update_permissions_self_role_denied(
        self, test_session: Session
    ) -> None:
        """Test user update permission validation for self role change."""
        # Create regular user
        user = UserFactory(role=UserRole.USER)
        test_session.add(user)
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # User should not be able to update their own role
        update_data = UserUpdateRequest(role=UserRole.ADMIN)

        with pytest.raises(ValidationError) as exc_info:
            await user_service._validate_user_update_permissions(
                user.user_id, user.user_id, update_data
            )

        assert "cannot modify their own role" in str(exc_info.value.message).lower()
        assert exc_info.value.error_code == "SELF_MODIFICATION_DENIED"

    @pytest.mark.asyncio
    async def test_validate_user_update_permissions_other_user_sysadmin(
        self, test_session: Session
    ) -> None:
        """Test sysadmin can update other users."""
        # Create sysadmin and regular user
        sysadmin = UserFactory(role=UserRole.SYSADMIN)
        regular_user = UserFactory(role=UserRole.USER)
        test_session.add_all([sysadmin, regular_user])
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # Sysadmin should be able to update other users
        update_data = UserUpdateRequest(role=UserRole.ADMIN)

        try:
            await user_service._validate_user_update_permissions(
                sysadmin.user_id, regular_user.user_id, update_data
            )
        except ValidationError:
            pytest.fail("Sysadmin should be able to update other users")

    @pytest.mark.asyncio
    async def test_validate_user_update_permissions_other_user_non_sysadmin(
        self, test_session: Session
    ) -> None:
        """Test non-sysadmin cannot update other users."""
        # Create admin and regular user
        admin = UserFactory(role=UserRole.ADMIN)
        regular_user = UserFactory(role=UserRole.USER)
        test_session.add_all([admin, regular_user])
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # Admin should not be able to update other users
        update_data = UserUpdateRequest(email="new@example.com")

        with pytest.raises(ValidationError) as exc_info:
            await user_service._validate_user_update_permissions(
                admin.user_id, regular_user.user_id, update_data
            )

        assert "Only system administrators" in str(exc_info.value.message)
        assert exc_info.value.error_code == "PERMISSION_DENIED"


class TestUserServiceErrorHandling:
    """Test error handling scenarios in UserService."""

    @pytest.mark.asyncio
    async def test_create_user_database_error_during_commit(self, test_session: Session) -> None:
        """Test database error handling during user creation commit."""
        # Create sysadmin user
        sysadmin = UserFactory(role=UserRole.SYSADMIN)
        test_session.add(sysadmin)
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"User-Agent": "test-agent"}
        mock_request.client.host = "127.0.0.1"

        # User creation data
        user_data = UserCreateRequest(
            email="error@test.com",
            role=UserRole.USER,
            password="SecurePass123!",
            is_active=True,
        )

        # Mock session commit to raise SQLAlchemy error
        with patch.object(test_session, "commit", side_effect=SQLAlchemyError("Database error")):
            with pytest.raises(DatabaseError) as exc_info:
                await user_service.create_user(
                    user_data=user_data,
                    created_by_user_id=sysadmin.user_id,
                    request=mock_request,
                )

            assert "Failed to create user" in str(exc_info.value.message)
            assert exc_info.value.error_code == "DATABASE_ERROR"

    @pytest.mark.asyncio
    async def test_update_user_database_error(self, test_session: Session) -> None:
        """Test database error handling during user update."""
        # Create test user
        test_user = UserFactory(role=UserRole.USER)
        test_session.add(test_user)
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"User-Agent": "test-agent"}
        mock_request.client.host = "127.0.0.1"

        # Update data
        update_data = UserUpdateRequest(email="updated@example.com")

        # Mock session commit to raise SQLAlchemy error
        with patch.object(test_session, "commit", side_effect=SQLAlchemyError("Database error")):
            with pytest.raises(DatabaseError) as exc_info:
                await user_service.update_user(
                    user_id=test_user.user_id,
                    user_data=update_data,
                    updated_by_user_id=test_user.user_id,
                    request=mock_request,
                )

            assert "Failed to update user" in str(exc_info.value.message)
            assert exc_info.value.error_code == "DATABASE_ERROR"

    @pytest.mark.asyncio
    async def test_deactivate_user_database_error(self, test_session: Session) -> None:
        """Test database error handling during user deactivation."""
        # Create sysadmin and regular user
        sysadmin = UserFactory(role=UserRole.SYSADMIN)
        regular_user = UserFactory(role=UserRole.USER)
        test_session.add_all([sysadmin, regular_user])
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"User-Agent": "test-agent"}
        mock_request.client.host = "127.0.0.1"

        # Mock session commit to raise SQLAlchemy error
        with patch.object(test_session, "commit", side_effect=SQLAlchemyError("Database error")):
            with pytest.raises(DatabaseError) as exc_info:
                await user_service.deactivate_user(
                    user_id=regular_user.user_id,
                    deactivated_by_user_id=sysadmin.user_id,
                    request=mock_request,
                )

            assert "Failed to deactivate user" in str(exc_info.value.message)
            assert exc_info.value.error_code == "DATABASE_ERROR"

    @pytest.mark.asyncio
    async def test_list_users_database_error(self, test_session: Session) -> None:
        """Test database error handling during user listing."""
        # Create sysadmin user
        sysadmin = UserFactory(role=UserRole.SYSADMIN)
        test_session.add(sysadmin)
        test_session.commit()

        # Create user service
        user_service = UserService(test_session)

        # Mock session exec to raise SQLAlchemy error

        search_params = UserSearchParams()

        with patch.object(test_session, "exec", side_effect=SQLAlchemyError("Database error")):
            with pytest.raises(DatabaseError) as exc_info:
                await user_service.list_users(
                    search_params=search_params,
                    page=1,
                    per_page=10,
                    requesting_user_id=sysadmin.user_id,
                )

            assert "Failed to retrieve user due to database error" in str(exc_info.value.message)
            assert exc_info.value.error_code == "DATABASE_ERROR"

    @pytest.mark.asyncio
    async def test_internal_get_user_database_error(self, test_session: Session) -> None:
        """Test database error in internal get user method."""
        # Create user service
        user_service = UserService(test_session)

        # Mock session exec to raise SQLAlchemy error
        user_id = uuid4()

        with patch.object(test_session, "exec", side_effect=SQLAlchemyError("Database error")):
            with pytest.raises(DatabaseError) as exc_info:
                await user_service._get_user_by_id_internal(user_id)

            assert "Failed to retrieve user" in str(exc_info.value.message)
            assert exc_info.value.error_code == "DATABASE_ERROR"

    @pytest.mark.asyncio
    async def test_check_email_uniqueness_database_error(self, test_session: Session) -> None:
        """Test database error in email uniqueness check."""
        # Create user service
        user_service = UserService(test_session)

        # Mock session exec to raise SQLAlchemy error
        with patch.object(test_session, "exec", side_effect=SQLAlchemyError("Database error")):
            with pytest.raises(DatabaseError) as exc_info:
                await user_service._check_email_uniqueness("test@example.com")

            assert "Failed to check email uniqueness" in str(exc_info.value.message)
            assert exc_info.value.error_code == "DATABASE_ERROR"
