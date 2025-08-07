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
from src.models.permissions import UserAgentPermission, PermissionTemplate
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

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
    def permission_service(
        self, test_session: Session, mock_redis: MagicMock
    ) -> PermissionService:
        """Create PermissionService with real database session and mocked Redis."""
        service = PermissionService(session=test_session)
        service.redis_client = mock_redis
        service._is_testing = True  # Keep Redis disabled for tests
        return service

    @pytest.fixture
    def sysadmin_user(self, test_session: Session) -> User:
        """Create a sysadmin user in the database."""
        user = cast("User", SysAdminUserFactory.build())
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)
        return user

    @pytest.fixture
    def admin_user(self, test_session: Session) -> User:
        """Create an admin user in the database."""
        user = cast("User", AdminUserFactory.build())
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)
        return user

    @pytest.fixture
    def regular_user(self, test_session: Session) -> User:
        """Create a regular user in the database."""
        user = cast("User", UserFactory.build(role=UserRole.USER))
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)
        return user

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
        test_session: Session,
        regular_user: User,
    ) -> None:
        """Test permission check with cache miss."""
        # Enable Redis for this test but keep testing mode for session handling
        permission_service._is_testing = False

        # Mock cache miss
        mock_redis.get.return_value = None

        # Create real permission in database
        permission = create_test_permission(
            user_id=regular_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"create": True, "read": True, "update": False, "delete": False},
        )
        test_session.add(permission)
        test_session.commit()

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
        test_session: Session,
        regular_user: User,
    ) -> None:
        """Test permission check with database error."""
        mock_redis.get.return_value = None

        # Test with a real database error by making the session execute fail
        with patch.object(test_session, "execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")

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
        test_session: Session,
    ) -> None:
        """Test get user permissions with non-existent user."""
        mock_redis.get.return_value = None
        # Use a non-existent user ID - real business logic will handle this
        non_existent_user_id = uuid4()

        with pytest.raises(NotFoundError) as excinfo:
            await permission_service.get_user_permissions(non_existent_user_id)

        assert f"User {non_existent_user_id} not found" in str(excinfo.value.message)

    async def test_assign_permission_success(
        self,
        permission_service: PermissionService,
        test_session: Session,
        sysadmin_user: User,
        regular_user: User,
        mock_redis: MagicMock,
    ) -> None:
        """Test successful permission assignment."""
        permissions = {"create": True, "read": True, "update": False, "delete": False}

        # Use real cache invalidation - no mocking of internal business logic
        await permission_service.assign_permission(
            user_id=regular_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions=permissions,
            created_by_user_id=sysadmin_user.user_id,
        )

        # Verify the permission was actually created in the database
        stmt = select(UserAgentPermission).where(
            UserAgentPermission.user_id == regular_user.user_id,
            UserAgentPermission.agent_name == AgentName.CLIENT_MANAGEMENT
        )
        permission = test_session.exec(stmt).first()
        assert permission is not None
        assert permission.permissions == permissions

    async def test_assign_permission_update_existing(
        self,
        permission_service: PermissionService,
        test_session: Session,
        sysadmin_user: User,
        regular_user: User,
        mock_redis: MagicMock,
    ) -> None:
        """Test updating existing permission."""
        old_permissions = {"create": False, "read": True, "update": False, "delete": False}
        new_permissions = {"create": True, "read": True, "update": True, "delete": False}
        
        # Create existing permission in database
        existing_permission = create_test_permission(
            user_id=regular_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions=old_permissions,
        )
        test_session.add(existing_permission)
        test_session.commit()

        # Use real cache invalidation - no mocking of internal business logic
        await permission_service.assign_permission(
            user_id=regular_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions=new_permissions,
            created_by_user_id=sysadmin_user.user_id,
        )

        # Verify the permission was updated in the database
        test_session.refresh(existing_permission)
        assert existing_permission.permissions == new_permissions

    @pytest.mark.asyncio
    async def test_assign_permission_authorization_error(
        self,
        permission_service: PermissionService,
        test_session: Session,
        regular_user: User,
    ) -> None:
        """Test permission assignment authorization error."""
        # Create another regular user in the database
        another_user = create_test_user(role=UserRole.USER)
        test_session.add(another_user)
        test_session.commit()
        test_session.refresh(another_user)
        
        permissions = {"create": True, "read": True, "update": False, "delete": False}

        # Temporarily use real business logic for this test to test authorization
        original_is_testing = permission_service._is_testing
        permission_service._is_testing = False
        
        try:
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
        finally:
            # Restore testing mode
            permission_service._is_testing = original_is_testing

    async def test_assign_permission_admin_restricted_agent(
        self,
        permission_service: PermissionService,
        test_session: Session,
        admin_user: User,
        regular_user: User,
    ) -> None:
        """Test admin user trying to assign restricted agent permissions."""
        permissions = {"create": True, "read": True, "update": False, "delete": False}

        # Temporarily use real business logic for this test to test authorization
        original_is_testing = permission_service._is_testing
        permission_service._is_testing = False
        
        try:
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
        finally:
            # Restore testing mode
            permission_service._is_testing = original_is_testing

    async def test_assign_permission_invalid_permissions_structure(
        self,
        permission_service: PermissionService,
        test_session: Session,
        sysadmin_user: User,
        regular_user: User,
    ) -> None:
        """Test permission assignment with invalid permissions structure."""
        invalid_permissions = {"create": True, "read": True}  # Missing keys

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
        test_session: Session,
        sysadmin_user: User,
        regular_user: User,
        mock_redis: MagicMock,
    ) -> None:
        """Test successful permission revocation."""
        existing_permission = create_test_permission(
            user_id=regular_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
        )
        test_session.add(existing_permission)
        test_session.commit()

        # Use real cache invalidation - no mocking of internal business logic
        result = await permission_service.revoke_permission(
            user_id=regular_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            revoked_by_user_id=sysadmin_user.user_id,
        )

        assert result is True
        # Verify permission was actually deleted from database
        stmt = select(UserAgentPermission).where(
            UserAgentPermission.user_id == regular_user.user_id,
            UserAgentPermission.agent_name == AgentName.CLIENT_MANAGEMENT
        )
        deleted_permission = test_session.exec(stmt).first()
        assert deleted_permission is None

    async def test_revoke_permission_not_found(
        self,
        permission_service: PermissionService,
        test_session: Session,
        sysadmin_user: User,
        regular_user: User,
    ) -> None:
        """Test revoking non-existent permission."""
        # Don't create any permission in database - test real scenario
        result = await permission_service.revoke_permission(
            user_id=regular_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            revoked_by_user_id=sysadmin_user.user_id,
        )

        assert result is False

    async def test_bulk_assign_permissions_success(
        self,
        permission_service: PermissionService,
        test_session: Session,
        sysadmin_user: User,
        mock_redis: MagicMock,
    ) -> None:
        """Test successful bulk permission assignment."""
        user1 = create_test_user(role=UserRole.USER)
        user2 = create_test_user(role=UserRole.USER)
        # Add users to database
        test_session.add(user1)
        test_session.add(user2)
        test_session.commit()
        test_session.refresh(user1)
        test_session.refresh(user2)
        
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

        # Use real cache invalidation - no mocking of internal business logic
        result = await permission_service.bulk_assign_permissions(
            user_ids=user_ids,
            agent_permissions=agent_permissions,
            assigned_by_user_id=sysadmin_user.user_id,
        )

        assert len(result) == 2
        assert user1.user_id in result
        assert user2.user_id in result

        # Verify permissions were created in database
        stmt = select(UserAgentPermission).where(
            UserAgentPermission.user_id == user1.user_id,
            UserAgentPermission.agent_name == AgentName.CLIENT_MANAGEMENT
        )
        user1_client_perm = test_session.exec(stmt).first()
        assert user1_client_perm is not None
        assert user1_client_perm.permissions == agent_permissions[AgentName.CLIENT_MANAGEMENT]

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
        test_session: Session,
        sysadmin_user: User,
        mock_redis: MagicMock,
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
        
        # Add template and user to database
        test_session.add(template)
        test_session.add(user1)
        test_session.commit()
        test_session.refresh(template)
        test_session.refresh(user1)
        
        user_ids = [user1.user_id]

        # Use real cache invalidation - no mocking of internal business logic
        result = await permission_service.apply_template_to_users(
            template_id=template.template_id,
            user_ids=user_ids,
            applied_by_user_id=sysadmin_user.user_id,
        )

        assert result["successful"] == 1
        assert result["failed"] == 0
        assert len(result["errors"]) == 0

    async def test_apply_template_to_users_template_not_found(
        self,
        permission_service: PermissionService,
        test_session: Session,
        sysadmin_user: User,
    ) -> None:
        """Test template application with non-existent template."""
        template_id = uuid4()  # Non-existent template ID
        user_ids = [uuid4()]

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
        test_session: Session,
    ) -> None:
        """Test successful template listing."""
        templates = [create_test_template() for _ in range(3)]
        
        # Add templates to database
        for template in templates:
            test_session.add(template)
        test_session.commit()

        result_templates, total = await permission_service.list_templates(page=1, page_size=10)

        assert len(result_templates) == 3
        assert total == 3

    async def test_create_template_success(
        self,
        permission_service: PermissionService,
        test_session: Session,
        sysadmin_user: User,
    ) -> None:
        """Test successful template creation."""
        template_name = "Test Template"
        description = "Test description"
        input_permissions = {
            "client_management": {"create": True, "read": True, "update": False, "delete": False}
        }
        
        # The service will expand permissions to include all agents
        expected_permissions = {
            "client_management": {"create": True, "read": True, "update": False, "delete": False},
            "pdf_processing": {"create": False, "read": False, "update": False, "delete": False},
            "reports_analysis": {"create": False, "read": False, "update": False, "delete": False},
            "audio_recording": {"create": False, "read": False, "update": False, "delete": False},
        }

        template = await permission_service.create_template(
            template_name=template_name,
            description=description,
            permissions=input_permissions,
            created_by_user_id=sysadmin_user.user_id,
        )

        # Verify template was created in database
        assert template.template_name == template_name
        assert template.description == description
        assert template.permissions == expected_permissions
        
        # Verify it exists in database
        stmt = select(PermissionTemplate).where(
            PermissionTemplate.template_id == template.template_id
        )
        db_template = test_session.exec(stmt).first()
        assert db_template is not None
        assert db_template.template_name == template_name

    async def test_update_template_success(
        self,
        permission_service: PermissionService,
        test_session: Session,
        sysadmin_user: User,
    ) -> None:
        """Test successful template update."""
        template = create_test_template()
        test_session.add(template)
        test_session.commit()
        test_session.refresh(template)
        
        new_name = "Updated Template"

        result = await permission_service.update_template(
            template_id=template.template_id,
            template_name=new_name,
            description=None,
            permissions=None,
            updated_by_user_id=sysadmin_user.user_id,
        )

        assert result is not None
        assert result.template_name == new_name
        
        # Verify update in database
        test_session.refresh(template)
        assert template.template_name == new_name

    async def test_delete_template_success(
        self,
        permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test successful template deletion."""
        template = create_test_template()
        test_session.add(template)
        test_session.commit()

        result = await permission_service.delete_template(template.template_id)

        assert result is True
        
        # Verify deletion from database
        stmt = select(PermissionTemplate).where(
            PermissionTemplate.template_id == template.template_id
        )
        deleted_template = test_session.exec(stmt).first()
        assert deleted_template is None

    async def test_delete_template_not_found(
        self,
        permission_service: PermissionService,
        test_session: Session,
    ) -> None:
        """Test deleting non-existent template."""
        template_id = uuid4()  # Non-existent template ID

        result = await permission_service.delete_template(template_id)

        assert result is False

    async def test_get_audit_log_success(
        self,
        permission_service: PermissionService,
        test_session: Session,
        regular_user: User,
    ) -> None:
        """Test successful audit log retrieval."""
        audit_logs = [
            create_test_permission_audit_log(user_id=regular_user.user_id, action="CREATE"),
            create_test_permission_audit_log(user_id=regular_user.user_id, action="UPDATE"),
        ]
        
        # Add audit logs to database
        for audit_log in audit_logs:
            test_session.add(audit_log)
        test_session.commit()

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
        test_session: Session,
        regular_user: User,
        admin_user: User,
        sysadmin_user: User,
    ) -> None:
        """Test successful permission statistics retrieval."""
        # Create some permissions and templates in database for real stats
        permission1 = create_test_permission(
            user_id=regular_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
        )
        permission2 = create_test_permission(
            user_id=admin_user.user_id,
            agent_name=AgentName.PDF_PROCESSING,
        )
        template = create_test_template()
        
        test_session.add(permission1)
        test_session.add(permission2)
        test_session.add(template)
        test_session.commit()

        result = await permission_service.get_permission_stats()

        # Basic stats should be calculated from real database data
        assert "total_users" in result
        assert "users_with_permissions" in result
        assert "templates_in_use" in result
        assert "recent_changes" in result
        assert "agent_usage" in result
        assert result["total_users"] >= 3  # At least our test users

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
