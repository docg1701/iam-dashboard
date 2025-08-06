"""
Tests for PermissionService.

This module tests the permission service business logic including
CRUD operations, caching, Redis integration, and performance requirements.
"""

import asyncio
import json
import time
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from src.core.exceptions import (
    AuthorizationError,
    DatabaseError,
    NotFoundError,
    ValidationError,
)
from src.models.permissions import AgentName
from src.models.user import User, UserRole
from src.services.permission_service import PermissionService
from src.tests.factories import (
    AdminUserFactory,
    SysAdminUserFactory,
    UserFactory,
    create_test_permission,
    create_test_permission_audit_log,
    create_test_template,
    create_test_user,
)


class TestPermissionService:
    """Tests for PermissionService class."""

    @pytest.fixture
    def mock_redis(self) -> MagicMock:
        """Create a mock Redis client."""
        redis_mock = MagicMock()
        redis_mock.get = AsyncMock()
        redis_mock.setex = AsyncMock()
        redis_mock.delete = AsyncMock()
        redis_mock.keys = AsyncMock()
        redis_mock.close = AsyncMock()
        return redis_mock

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock database session."""
        session = MagicMock(spec=Session)
        session.execute.return_value.scalar.return_value = True
        session.execute.return_value.scalar_one_or_none.return_value = None
        session.execute.return_value.scalars.return_value = []
        session.execute.return_value.fetchall.return_value = []
        session.close = MagicMock()
        return session

    @pytest.fixture
    def permission_service(
        self, mock_redis: MagicMock, mock_session: MagicMock
    ) -> PermissionService:
        """Create PermissionService with mocked Redis and database session."""
        service = PermissionService(session=mock_session)
        service.redis_client = mock_redis
        service._is_testing = True  # Ensure testing mode is enabled
        return service

    @pytest.fixture
    def sysadmin_user(self) -> User:
        """Create a sysadmin user for testing."""
        return cast("User", SysAdminUserFactory.build())

    @pytest.fixture
    def admin_user(self) -> User:
        """Create an admin user for testing."""
        return cast("User", AdminUserFactory.build())

    @pytest.fixture
    def regular_user(self) -> User:
        """Create a regular user for testing."""
        return cast("User", UserFactory.build(role=UserRole.USER))

    async def test_check_user_permission_cache_hit(
        self,
        permission_service: PermissionService,
        mock_redis: MagicMock,
        regular_user: User,
    ) -> None:
        """Test permission check with cache hit."""
        # Enable Redis for this test
        permission_service._is_testing = False

        # Mock cache hit
        permissions = {"create": True, "read": True, "update": False, "delete": False}
        mock_redis.get.return_value = json.dumps(permissions)

        result = await permission_service.check_user_permission(
            user_id=regular_user.user_id, agent_name=AgentName.CLIENT_MANAGEMENT, operation="create"
        )

        assert result is True
        mock_redis.get.assert_called_once()
        # Should not access database on cache hit - verify by checking no DB calls were made
        expected_cache_key = f"permission:user:{regular_user.user_id}:agent:client_management"
        mock_redis.get.assert_called_with(expected_cache_key)

    async def test_check_user_permission_cache_miss(
        self,
        permission_service: PermissionService,
        mock_redis: MagicMock,
        mock_session: MagicMock,
        regular_user: User,
    ) -> None:
        """Test permission check with cache miss."""
        # Enable Redis for this test but keep testing mode for session handling
        permission_service._is_testing = False

        # Mock cache miss
        mock_redis.get.return_value = None

        # Since we injected the session in the fixture, it will be used directly
        # Mock permission query
        permission = create_test_permission(
            user_id=regular_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"create": True, "read": True, "update": False, "delete": False},
        )

        # Setup multiple return values for the two execute calls in sequence
        mock_session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=True)),  # First call: database function
            MagicMock(
                scalar_one_or_none=MagicMock(return_value=permission)
            ),  # Second call: permission query
        ]

        result = await permission_service.check_user_permission(
            user_id=regular_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            operation="create",
        )

        assert result is True
        mock_redis.get.assert_called_once()
        mock_redis.setex.assert_called_once()  # Should cache the result

    async def test_check_user_permission_invalid_operation(
        self,
        permission_service: PermissionService,
        regular_user: User,
    ) -> None:
        """Test permission check with invalid operation."""
        with pytest.raises(ValidationError) as excinfo:
            await permission_service.check_user_permission(
                user_id=regular_user.user_id,
                agent_name=AgentName.CLIENT_MANAGEMENT,
                operation="invalid_operation",
            )

        assert "Invalid operation" in str(excinfo.value.message)

    async def test_check_user_permission_database_error(
        self,
        permission_service: PermissionService,
        mock_redis: MagicMock,
        mock_session: MagicMock,
        regular_user: User,
    ) -> None:
        """Test permission check with database error."""
        mock_redis.get.return_value = None

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.execute.side_effect = SQLAlchemyError("Database error")

            with pytest.raises(DatabaseError) as excinfo:
                await permission_service.check_user_permission(
                    user_id=regular_user.user_id,
                    agent_name=AgentName.CLIENT_MANAGEMENT,
                    operation="create",
                )

            assert "Failed to check user permission" in str(excinfo.value.message)

    async def test_get_user_permissions_cache_hit(
        self,
        permission_service: PermissionService,
        mock_redis: MagicMock,
        regular_user: User,
    ) -> None:
        """Test get user permissions with cache hit."""
        # Enable Redis for this test
        permission_service._is_testing = False

        expected_permissions = {
            "client_management": {"create": True, "read": True, "update": False, "delete": False},
            "pdf_processing": {"create": False, "read": True, "update": False, "delete": False},
        }
        mock_redis.get.return_value = json.dumps(expected_permissions)

        result = await permission_service.get_user_permissions(regular_user.user_id)

        assert result == expected_permissions
        mock_redis.get.assert_called_once()
        expected_cache_key = f"permission:user:{regular_user.user_id}:matrix"
        mock_redis.get.assert_called_with(expected_cache_key)

    async def test_get_user_permissions_user_not_found(
        self,
        permission_service: PermissionService,
        mock_redis: MagicMock,
        mock_session: MagicMock,
        regular_user: User,
    ) -> None:
        """Test get user permissions with non-existent user."""
        mock_redis.get.return_value = None

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.execute.return_value.scalar_one_or_none.return_value = None

            with pytest.raises(NotFoundError) as excinfo:
                await permission_service.get_user_permissions(regular_user.user_id)

            assert f"User {regular_user.user_id} not found" in str(excinfo.value.message)

    async def test_assign_permission_success(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
        sysadmin_user: User,
        regular_user: User,
    ) -> None:
        """Test successful permission assignment."""
        permissions = {"create": True, "read": True, "update": False, "delete": False}

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock users exist
            users = {regular_user.user_id: regular_user, sysadmin_user.user_id: sysadmin_user}
            mock_session.execute.return_value.scalars.return_value = users.values()

            # Mock no existing permission
            mock_session.execute.return_value.scalar_one_or_none.return_value = None

            with patch.object(permission_service, "_invalidate_user_cache") as mock_invalidate:
                await permission_service.assign_permission(
                    user_id=regular_user.user_id,
                    agent_name=AgentName.CLIENT_MANAGEMENT,
                    permissions=permissions,
                    created_by_user_id=sysadmin_user.user_id,
                )

                # Should add both the permission and its audit log
                assert mock_session.add.call_count == 2
                mock_session.commit.assert_called_once()
                mock_invalidate.assert_called_once_with(regular_user.user_id)

    async def test_assign_permission_update_existing(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
        sysadmin_user: User,
        regular_user: User,
    ) -> None:
        """Test updating existing permission."""
        new_permissions = {"create": True, "read": True, "update": True, "delete": False}
        existing_permission = create_test_permission(
            user_id=regular_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"create": False, "read": True, "update": False, "delete": False},
        )

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock users exist
            users = {regular_user.user_id: regular_user, sysadmin_user.user_id: sysadmin_user}
            mock_session.execute.return_value.scalars.return_value = users.values()

            # Mock existing permission
            mock_session.execute.return_value.scalar_one_or_none.return_value = existing_permission

            with patch.object(permission_service, "_invalidate_user_cache") as mock_invalidate:
                await permission_service.assign_permission(
                    user_id=regular_user.user_id,
                    agent_name=AgentName.CLIENT_MANAGEMENT,
                    permissions=new_permissions,
                    created_by_user_id=sysadmin_user.user_id,
                )

                # Should only add the audit log, not a new permission
                assert mock_session.add.call_count == 1
                mock_session.commit.assert_called_once()
                mock_invalidate.assert_called_once_with(regular_user.user_id)
                assert existing_permission.permissions == new_permissions

    async def test_assign_permission_authorization_error(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
        regular_user: User,
    ) -> None:
        """Test permission assignment authorization error."""
        another_user = create_test_user(role=UserRole.USER)
        permissions = {"create": True, "read": True, "update": False, "delete": False}

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock users exist
            users = {regular_user.user_id: regular_user, another_user.user_id: another_user}
            mock_session.execute.return_value.scalars.return_value = users.values()

            with pytest.raises(AuthorizationError) as excinfo:
                await permission_service.assign_permission(
                    user_id=regular_user.user_id,
                    agent_name=AgentName.CLIENT_MANAGEMENT,
                    permissions=permissions,
                    created_by_user_id=another_user.user_id,
                )

            assert "Only sysadmin or admin users can assign permissions" in str(
                excinfo.value.message
            )

    async def test_assign_permission_admin_restricted_agent(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
        admin_user: User,
        regular_user: User,
    ) -> None:
        """Test admin user trying to assign restricted agent permissions."""
        permissions = {"create": True, "read": True, "update": False, "delete": False}

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock users exist
            users = {regular_user.user_id: regular_user, admin_user.user_id: admin_user}
            mock_session.execute.return_value.scalars.return_value = users.values()

            with pytest.raises(AuthorizationError) as excinfo:
                await permission_service.assign_permission(
                    user_id=regular_user.user_id,
                    agent_name=AgentName.PDF_PROCESSING,  # Admin can't assign this
                    permissions=permissions,
                    created_by_user_id=admin_user.user_id,
                )

            assert (
                "Admin users can only assign permissions for client_management and reports_analysis"
                in str(excinfo.value.message)
            )

    async def test_assign_permission_invalid_permissions_structure(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
        sysadmin_user: User,
        regular_user: User,
    ) -> None:
        """Test permission assignment with invalid permissions structure."""
        invalid_permissions = {"create": True, "read": True}  # Missing keys

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            users = {regular_user.user_id: regular_user, sysadmin_user.user_id: sysadmin_user}
            mock_session.execute.return_value.scalars.return_value = users.values()

            with pytest.raises(ValidationError) as excinfo:
                await permission_service.assign_permission(
                    user_id=regular_user.user_id,
                    agent_name=AgentName.CLIENT_MANAGEMENT,
                    permissions=invalid_permissions,
                    created_by_user_id=sysadmin_user.user_id,
                )

            assert "Permissions must contain all keys" in str(excinfo.value.message)

    async def test_revoke_permission_success(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
        sysadmin_user: User,
        regular_user: User,
    ) -> None:
        """Test successful permission revocation."""
        existing_permission = create_test_permission(
            user_id=regular_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
        )

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock users exist
            users = {regular_user.user_id: regular_user, sysadmin_user.user_id: sysadmin_user}
            mock_session.execute.return_value.scalars.return_value = users.values()

            # Mock existing permission
            mock_session.execute.return_value.scalar_one_or_none.return_value = existing_permission

            with patch.object(permission_service, "_invalidate_user_cache") as mock_invalidate:
                result = await permission_service.revoke_permission(
                    user_id=regular_user.user_id,
                    agent_name=AgentName.CLIENT_MANAGEMENT,
                    revoked_by_user_id=sysadmin_user.user_id,
                )

                assert result is True
                mock_session.delete.assert_called_once_with(existing_permission)
                mock_session.commit.assert_called_once()
                mock_invalidate.assert_called_once_with(regular_user.user_id)

    async def test_revoke_permission_not_found(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
        sysadmin_user: User,
        regular_user: User,
    ) -> None:
        """Test revoking non-existent permission."""
        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock users exist
            users = {regular_user.user_id: regular_user, sysadmin_user.user_id: sysadmin_user}
            mock_session.execute.return_value.scalars.return_value = users.values()

            # Mock no existing permission
            mock_session.execute.return_value.scalar_one_or_none.return_value = None

            result = await permission_service.revoke_permission(
                user_id=regular_user.user_id,
                agent_name=AgentName.CLIENT_MANAGEMENT,
                revoked_by_user_id=sysadmin_user.user_id,
            )

            assert result is False
            mock_session.delete.assert_not_called()
            mock_session.commit.assert_not_called()

    async def test_bulk_assign_permissions_success(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
        sysadmin_user: User,
    ) -> None:
        """Test successful bulk permission assignment."""
        user1 = create_test_user(role=UserRole.USER)
        user2 = create_test_user(role=UserRole.USER)
        user_ids = [user1.user_id, user2.user_id]

        agent_permissions = {
            AgentName.CLIENT_MANAGEMENT: {
                "create": True,
                "read": True,
                "update": False,
                "delete": False,
            },
            AgentName.REPORTS_ANALYSIS: {
                "create": False,
                "read": True,
                "update": False,
                "delete": False,
            },
        }

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock all users exist
            all_users = [user1, user2, sysadmin_user]
            mock_session.execute.return_value.scalars.return_value = all_users

            # Mock no existing permissions
            mock_session.execute.return_value.scalars.side_effect = [all_users, [], []]

            with patch.object(permission_service, "_invalidate_user_cache") as mock_invalidate:
                result = await permission_service.bulk_assign_permissions(
                    user_ids=user_ids,
                    agent_permissions=agent_permissions,
                    assigned_by_user_id=sysadmin_user.user_id,
                )

                assert len(result) == 2
                assert user1.user_id in result
                assert user2.user_id in result

                # Should add 4 permissions + 4 audit logs (2 users × 2 agents × 2 records each)
                assert mock_session.add.call_count == 8
                mock_session.commit.assert_called_once()

                # Should invalidate cache for both users
                assert mock_invalidate.call_count == 2

    async def test_bulk_assign_permissions_empty_list(
        self,
        permission_service: PermissionService,
        sysadmin_user: User,
    ) -> None:
        """Test bulk assignment with empty user list."""
        result = await permission_service.bulk_assign_permissions(
            user_ids=[],
            agent_permissions={},
            assigned_by_user_id=sysadmin_user.user_id,
        )

        assert result == {}

    async def test_apply_template_to_users_success(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
        sysadmin_user: User,
    ) -> None:
        """Test successful template application."""
        template = create_test_template(
            template_name="Test Template",
            permissions={
                "client_management": {
                    "create": True,
                    "read": True,
                    "update": False,
                    "delete": False,
                },
                "reports_analysis": {
                    "create": False,
                    "read": True,
                    "update": False,
                    "delete": False,
                },
            },
        )
        user1 = create_test_user(role=UserRole.USER)
        user_ids = [user1.user_id]

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock template exists
            mock_session.execute.return_value.scalar_one_or_none.side_effect = [
                template,
                sysadmin_user,
                None,
                None,
            ]

            with patch.object(permission_service, "_invalidate_user_cache") as mock_invalidate:
                result = await permission_service.apply_template_to_users(
                    template_id=template.template_id,
                    user_ids=user_ids,
                    applied_by_user_id=sysadmin_user.user_id,
                )

                assert result["successful"] == 1
                assert result["failed"] == 0
                assert len(result["errors"]) == 0
                mock_invalidate.assert_called_once_with(user1.user_id)

    async def test_apply_template_to_users_template_not_found(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
        sysadmin_user: User,
    ) -> None:
        """Test template application with non-existent template."""
        template_id = uuid4()
        user_ids = [uuid4()]

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock template not found
            mock_session.execute.return_value.scalar_one_or_none.return_value = None

            with pytest.raises(NotFoundError) as excinfo:
                await permission_service.apply_template_to_users(
                    template_id=template_id,
                    user_ids=user_ids,
                    applied_by_user_id=sysadmin_user.user_id,
                )

            assert f"Template {template_id} not found" in str(excinfo.value.message)

    async def test_list_templates_success(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
    ) -> None:
        """Test successful template listing."""
        templates = [create_test_template() for _ in range(3)]

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock total count and templates
            mock_session.execute.return_value.scalar.return_value = 3
            mock_session.execute.return_value.scalars.return_value = templates

            result_templates, total = await permission_service.list_templates(page=1, page_size=10)

            assert len(result_templates) == 3
            assert total == 3

    async def test_create_template_success(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
        sysadmin_user: User,
    ) -> None:
        """Test successful template creation."""
        template_name = "Test Template"
        description = "Test description"
        permissions = {
            "client_management": {"create": True, "read": True, "update": False, "delete": False}
        }

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            await permission_service.create_template(
                template_name=template_name,
                description=description,
                permissions=permissions,
                created_by_user_id=sysadmin_user.user_id,
            )

            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()

    async def test_update_template_success(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
        sysadmin_user: User,
    ) -> None:
        """Test successful template update."""
        template = create_test_template()
        new_name = "Updated Template"

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock template exists
            mock_session.execute.return_value.scalar_one_or_none.return_value = template

            result = await permission_service.update_template(
                template_id=template.template_id,
                template_name=new_name,
                description=None,
                permissions=None,
                updated_by_user_id=sysadmin_user.user_id,
            )

            assert result is not None
            assert template.template_name == new_name
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()

    async def test_delete_template_success(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
    ) -> None:
        """Test successful template deletion."""
        template = create_test_template()

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock template exists
            mock_session.execute.return_value.scalar_one_or_none.return_value = template

            result = await permission_service.delete_template(template.template_id)

            assert result is True
            mock_session.delete.assert_called_once_with(template)
            mock_session.commit.assert_called_once()

    async def test_delete_template_not_found(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
    ) -> None:
        """Test deleting non-existent template."""
        template_id = uuid4()

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock template not found
            mock_session.execute.return_value.scalar_one_or_none.return_value = None

            result = await permission_service.delete_template(template_id)

            assert result is False
            mock_session.delete.assert_not_called()
            mock_session.commit.assert_not_called()

    async def test_get_audit_log_success(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
        regular_user: User,
    ) -> None:
        """Test successful audit log retrieval."""
        audit_logs = [
            create_test_permission_audit_log(user_id=regular_user.user_id, action="CREATE"),
            create_test_permission_audit_log(user_id=regular_user.user_id, action="UPDATE"),
        ]

        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock total count and audit logs
            mock_session.execute.return_value.scalar.return_value = 2
            mock_session.execute.return_value.scalars.return_value = audit_logs

            result_logs, total = await permission_service.get_audit_log(
                user_id=regular_user.user_id,
                page=1,
                page_size=10,
            )

            assert len(result_logs) == 2
            assert total == 2

    async def test_get_permission_stats_success(
        self,
        permission_service: PermissionService,
        mock_session: MagicMock,
    ) -> None:
        """Test successful permission statistics retrieval."""
        with patch.object(permission_service, "get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock various statistics queries
            mock_session.execute.return_value.scalar.side_effect = [
                100,
                75,
                5,
                20,
            ]  # total_users, users_with_perms, templates, recent_changes

            # Mock agent usage
            class MockRow:
                def __init__(self, agent_name: str, permission_count: int):
                    self.agent_name = agent_name
                    self.permission_count = permission_count

            mock_session.execute.return_value.__iter__.return_value = [
                MockRow("client_management", 50),
                MockRow("pdf_processing", 25),
            ]

            result = await permission_service.get_permission_stats()

            assert result["total_users"] == 100
            assert result["users_with_permissions"] == 75
            assert result["templates_in_use"] == 5
            assert result["recent_changes"] == 20
            assert "agent_usage" in result

    async def test_cache_invalidation(
        self,
        permission_service: PermissionService,
        mock_redis: MagicMock,
        regular_user: User,
    ) -> None:
        """Test cache invalidation functionality."""
        # Enable Redis for this test
        permission_service._is_testing = False

        keys_to_delete = [
            f"permission:user:{regular_user.user_id}:agent:client_management",
            f"permission:user:{regular_user.user_id}:matrix",
        ]
        mock_redis.keys.return_value = keys_to_delete

        await permission_service._invalidate_user_cache(regular_user.user_id)

        mock_redis.keys.assert_called_once_with(f"permission:user:{regular_user.user_id}:*")
        mock_redis.delete.assert_called_once_with(*keys_to_delete)

    async def test_cache_invalidation_error_handling(
        self,
        permission_service: PermissionService,
        mock_redis: MagicMock,
        regular_user: User,
    ) -> None:
        """Test cache invalidation with Redis error."""
        # Enable Redis for this test
        permission_service._is_testing = False

        mock_redis.keys.side_effect = Exception("Redis connection failed")

        # Should not raise exception
        await permission_service._invalidate_user_cache(regular_user.user_id)

        mock_redis.keys.assert_called_once_with(f"permission:user:{regular_user.user_id}:*")

    async def test_permission_checking_performance(
        self,
        permission_service: PermissionService,
        mock_redis: MagicMock,
        regular_user: User,
    ) -> None:
        """Test permission checking meets <50ms performance requirement."""
        # Enable Redis for this test
        permission_service._is_testing = False

        # Mock cache hit for fastest path
        permissions = {"create": True, "read": True, "update": False, "delete": False}
        mock_redis.get.return_value = json.dumps(permissions)

        start_time = time.time()

        # Test multiple operations
        tasks = []
        for _ in range(10):
            task = permission_service.check_user_permission(
                user_id=regular_user.user_id,
                agent_name=AgentName.CLIENT_MANAGEMENT,
                operation="create",
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Each operation should be well under 50ms
        avg_time_ms = ((end_time - start_time) / len(tasks)) * 1000
        assert avg_time_ms < 50, f"Average permission check took {avg_time_ms}ms, should be <50ms"
        assert all(results), "All permission checks should return True"

    async def test_close_redis_connection(
        self,
        permission_service: PermissionService,
        mock_redis: MagicMock,
    ) -> None:
        """Test Redis connection cleanup."""
        await permission_service.close()
        mock_redis.close.assert_called_once()
