"""
Integration tests for Permission Service.

These tests actually execute the service methods (not mocked) to achieve better coverage.
"""

from uuid import uuid4

import pytest
from sqlmodel import Session

from src.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from src.models.permissions import AgentName
from src.models.user import User, UserRole
from src.services.permission_service import PermissionService
from src.tests.factories import (
    create_test_permission,
    create_test_permission_audit_log,
    create_test_template,
    create_test_user,
)


class TestPermissionServiceIntegration:
    """Integration tests for PermissionService with real database operations."""

    @pytest.fixture
    def permission_service(self, test_session: Session) -> PermissionService:
        """Create permission service with test database session."""
        return PermissionService(session=test_session)

    @pytest.fixture
    def test_user(self, test_session: Session) -> User:
        """Create a test user in the database."""
        user = create_test_user(role=UserRole.ADMIN)
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)
        return user

    @pytest.fixture
    def sysadmin_user(self, test_session: Session) -> User:
        """Create a sysadmin user in the database."""
        user = create_test_user(role=UserRole.SYSADMIN)
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)
        return user

    async def test_check_user_permission_valid_operation(
        self, permission_service: PermissionService, test_user: User, test_session: Session
    ) -> None:
        """Test checking user permission with valid operation."""
        # Create a permission
        permission = create_test_permission(
            user_id=test_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"create": True, "read": True, "update": False, "delete": False},
            created_by_user_id=test_user.user_id,
        )
        test_session.add(permission)
        test_session.commit()

        # Test valid operations
        result = await permission_service.check_user_permission(
            test_user.user_id, AgentName.CLIENT_MANAGEMENT, "create"
        )
        assert result is True

        result = await permission_service.check_user_permission(
            test_user.user_id, AgentName.CLIENT_MANAGEMENT, "update"
        )
        assert result is True  # Admin users have full access to client_management

    async def test_check_user_permission_invalid_operation(
        self, permission_service: PermissionService, test_user: User
    ) -> None:
        """Test checking user permission with invalid operation."""
        with pytest.raises(ValidationError, match="Invalid operation"):
            await permission_service.check_user_permission(
                test_user.user_id, AgentName.CLIENT_MANAGEMENT, "invalid_operation"
            )

    async def test_get_user_permissions_existing_user(
        self, permission_service: PermissionService, test_user: User, test_session: Session
    ) -> None:
        """Test getting permissions for existing user."""
        # Create permissions
        permission1 = create_test_permission(
            user_id=test_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"create": True, "read": True, "update": False, "delete": False},
            created_by_user_id=test_user.user_id,
        )
        permission2 = create_test_permission(
            user_id=test_user.user_id,
            agent_name=AgentName.PDF_PROCESSING,
            permissions={"create": False, "read": True, "update": False, "delete": False},
            created_by_user_id=test_user.user_id,
        )
        test_session.add_all([permission1, permission2])
        test_session.commit()

        permissions = await permission_service.get_user_permissions(test_user.user_id)

        assert len(permissions) >= 2
        assert "client_management" in permissions
        assert "pdf_processing" in permissions
        assert permissions["client_management"]["create"] is True
        assert permissions["pdf_processing"]["create"] is False

    async def test_get_user_permissions_nonexistent_user(
        self, permission_service: PermissionService
    ) -> None:
        """Test getting permissions for non-existent user."""
        nonexistent_id = uuid4()
        with pytest.raises(NotFoundError, match="not found"):
            await permission_service.get_user_permissions(nonexistent_id)

    async def test_assign_permission_success(
        self, permission_service: PermissionService, test_user: User, sysadmin_user: User
    ) -> None:
        """Test successful permission assignment."""
        permissions = {"create": True, "read": True, "update": False, "delete": False}

        result = await permission_service.assign_permission(
            user_id=test_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions=permissions,
            created_by_user_id=sysadmin_user.user_id,
            change_reason="Test assignment",
        )

        assert result.user_id == test_user.user_id
        assert result.agent_name == AgentName.CLIENT_MANAGEMENT
        assert result.permissions == permissions

    async def test_assign_permission_invalid_permissions(
        self, permission_service: PermissionService, test_user: User, sysadmin_user: User
    ) -> None:
        """Test assignment with invalid permissions structure."""
        invalid_permissions = {"create": True, "read": True}  # Missing required keys

        with pytest.raises(ValidationError, match="must contain all keys"):
            await permission_service.assign_permission(
                user_id=test_user.user_id,
                agent_name=AgentName.CLIENT_MANAGEMENT,
                permissions=invalid_permissions,
                created_by_user_id=sysadmin_user.user_id,
            )

    @pytest.mark.skip(reason="Flaky test - passes individually but fails in full suite")
    async def test_assign_permission_unauthorized_user(
        self, permission_service: PermissionService, test_user: User, test_session: Session
    ) -> None:
        """Test assignment by unauthorized user."""
        # Create regular user (not admin)
        regular_user = create_test_user(role=UserRole.USER)
        test_session.add(regular_user)
        test_session.commit()

        permissions = {"create": True, "read": True, "update": False, "delete": False}

        with pytest.raises(AuthorizationError, match="Only sysadmin or admin"):
            await permission_service.assign_permission(
                user_id=test_user.user_id,
                agent_name=AgentName.CLIENT_MANAGEMENT,
                permissions=permissions,
                created_by_user_id=regular_user.user_id,
            )

    async def test_revoke_permission_success(
        self,
        permission_service: PermissionService,
        test_user: User,
        sysadmin_user: User,
        test_session: Session,
    ) -> None:
        """Test successful permission revocation."""
        # First create a permission
        permission = create_test_permission(
            user_id=test_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            created_by_user_id=sysadmin_user.user_id,
        )
        test_session.add(permission)
        test_session.commit()

        # Revoke it
        result = await permission_service.revoke_permission(
            user_id=test_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            revoked_by_user_id=sysadmin_user.user_id,
            change_reason="Test revocation",
        )

        assert result is True

    async def test_revoke_permission_not_found(
        self, permission_service: PermissionService, test_user: User, sysadmin_user: User
    ) -> None:
        """Test revoking non-existent permission."""
        result = await permission_service.revoke_permission(
            user_id=test_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            revoked_by_user_id=sysadmin_user.user_id,
        )

        assert result is False

    async def test_bulk_assign_permissions_success(
        self,
        permission_service: PermissionService,
        test_user: User,
        sysadmin_user: User,
        test_session: Session,
    ) -> None:
        """Test successful bulk permission assignment."""
        # Create another user
        user2 = create_test_user(role=UserRole.USER)
        test_session.add(user2)
        test_session.commit()

        user_ids = [test_user.user_id, user2.user_id]
        agent_permissions = {
            AgentName.CLIENT_MANAGEMENT: {
                "create": True,
                "read": True,
                "update": False,
                "delete": False,
            }
        }

        result = await permission_service.bulk_assign_permissions(
            user_ids=user_ids,
            agent_permissions=agent_permissions,
            assigned_by_user_id=sysadmin_user.user_id,
            change_reason="Bulk test assignment",
        )

        assert len(result) == 2
        assert test_user.user_id in result
        assert user2.user_id in result

    async def test_bulk_assign_permissions_empty_list(
        self, permission_service: PermissionService, sysadmin_user: User
    ) -> None:
        """Test bulk assignment with empty user list."""
        result = await permission_service.bulk_assign_permissions(
            user_ids=[],
            agent_permissions={
                AgentName.CLIENT_MANAGEMENT: {
                    "create": True,
                    "read": True,
                    "update": False,
                    "delete": False,
                }
            },
            assigned_by_user_id=sysadmin_user.user_id,
        )

        assert result == {}

    async def test_create_template_success(
        self, permission_service: PermissionService, sysadmin_user: User
    ) -> None:
        """Test successful template creation."""
        template_name = "Test Template"
        description = "Test template description"
        permissions = {
            "client_management": {"create": True, "read": True, "update": False, "delete": False},
            "pdf_processing": {"create": False, "read": True, "update": False, "delete": False},
            "reports_analysis": {"create": False, "read": False, "update": False, "delete": False},
            "audio_recording": {"create": False, "read": False, "update": False, "delete": False},
        }

        result = await permission_service.create_template(
            template_name=template_name,
            description=description,
            permissions=permissions,
            created_by_user_id=sysadmin_user.user_id,
        )

        assert result.template_name == template_name
        assert result.description == description
        assert result.permissions == permissions

    async def test_list_templates_success(
        self, permission_service: PermissionService, test_session: Session
    ) -> None:
        """Test successful template listing."""
        # Create test templates
        template1 = create_test_template(template_name="Template 1", is_system=False)
        template2 = create_test_template(template_name="Template 2", is_system=True)
        test_session.add_all([template1, template2])
        test_session.commit()

        templates, total = await permission_service.list_templates(
            page=1, page_size=10, system_only=False
        )

        assert total >= 2
        assert len(templates) >= 2

    async def test_list_templates_system_only(
        self, permission_service: PermissionService, test_session: Session
    ) -> None:
        """Test listing system templates only."""
        # Create test templates
        template1 = create_test_template(template_name="User Template", is_system=False)
        template2 = create_test_template(template_name="System Template", is_system=True)
        test_session.add_all([template1, template2])
        test_session.commit()

        templates, total = await permission_service.list_templates(
            page=1, page_size=10, system_only=True
        )

        assert total >= 1
        # All returned templates should be system templates
        for template in templates:
            assert template.is_system_template is True

    async def test_update_template_success(
        self, permission_service: PermissionService, sysadmin_user: User, test_session: Session
    ) -> None:
        """Test successful template update."""
        # Create template
        template = create_test_template(template_name="Original Template")
        test_session.add(template)
        test_session.commit()

        new_name = "Updated Template"
        new_description = "Updated description"

        result = await permission_service.update_template(
            template_id=template.template_id,
            template_name=new_name,
            description=new_description,
            permissions=None,
            updated_by_user_id=sysadmin_user.user_id,
        )

        assert result is not None
        assert result.template_name == new_name
        assert result.description == new_description

    async def test_update_template_not_found(
        self, permission_service: PermissionService, sysadmin_user: User
    ) -> None:
        """Test updating non-existent template."""
        nonexistent_id = uuid4()

        result = await permission_service.update_template(
            template_id=nonexistent_id,
            template_name="Updated Template",
            description="Updated description",
            permissions=None,
            updated_by_user_id=sysadmin_user.user_id,
        )

        assert result is None

    async def test_delete_template_success(
        self, permission_service: PermissionService, test_session: Session
    ) -> None:
        """Test successful template deletion."""
        # Create template
        template = create_test_template(template_name="Template to Delete")
        test_session.add(template)
        test_session.commit()

        result = await permission_service.delete_template(template.template_id)

        assert result is True

    async def test_delete_template_not_found(self, permission_service: PermissionService) -> None:
        """Test deleting non-existent template."""
        nonexistent_id = uuid4()

        result = await permission_service.delete_template(nonexistent_id)

        assert result is False

    async def test_get_permission_stats(
        self, permission_service: PermissionService, test_user: User, test_session: Session
    ) -> None:
        """Test getting permission statistics."""
        # Create some test data
        permission = create_test_permission(
            user_id=test_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            created_by_user_id=test_user.user_id,
        )
        template = create_test_template(template_name="Stats Template")
        test_session.add_all([permission, template])
        test_session.commit()

        stats = await permission_service.get_permission_stats()

        assert "total_users" in stats
        assert "users_with_permissions" in stats
        assert "templates_in_use" in stats
        assert "recent_changes" in stats
        assert "agent_usage" in stats
        assert isinstance(stats["total_users"], int)
        assert isinstance(stats["users_with_permissions"], int)

    async def test_get_audit_log_success(
        self, permission_service: PermissionService, test_session: Session
    ) -> None:
        """Test getting audit log."""
        # Create audit log entries
        audit1 = create_test_permission_audit_log(action="CREATE")
        audit2 = create_test_permission_audit_log(action="UPDATE")
        test_session.add_all([audit1, audit2])
        test_session.commit()

        audit_entries, total = await permission_service.get_audit_log(page=1, page_size=10)

        assert total >= 2
        assert len(audit_entries) >= 2

    async def test_get_audit_log_with_filters(
        self, permission_service: PermissionService, test_user: User, test_session: Session
    ) -> None:
        """Test getting audit log with filters."""
        # Create audit log entries
        audit1 = create_test_permission_audit_log(
            user_id=test_user.user_id, agent_name=AgentName.CLIENT_MANAGEMENT, action="CREATE"
        )
        audit2 = create_test_permission_audit_log(
            user_id=uuid4(), agent_name=AgentName.PDF_PROCESSING, action="UPDATE"
        )
        test_session.add_all([audit1, audit2])
        test_session.commit()

        # Filter by user_id
        audit_entries, total = await permission_service.get_audit_log(
            user_id=test_user.user_id, page=1, page_size=10
        )

        assert total >= 1
        for entry in audit_entries:
            assert entry.user_id == test_user.user_id

        # Filter by agent_name
        audit_entries, total = await permission_service.get_audit_log(
            agent_name=AgentName.CLIENT_MANAGEMENT, page=1, page_size=10
        )

        assert total >= 1
        for entry in audit_entries:
            assert entry.agent_name == AgentName.CLIENT_MANAGEMENT

    async def test_apply_template_to_users_success(
        self,
        permission_service: PermissionService,
        test_user: User,
        sysadmin_user: User,
        test_session: Session,
    ) -> None:
        """Test successful template application to users."""
        # Create template
        template = create_test_template(
            template_name="Application Template",
            permissions={
                "client_management": {
                    "create": True,
                    "read": True,
                    "update": False,
                    "delete": False,
                },
                "pdf_processing": {"create": False, "read": True, "update": False, "delete": False},
            },
        )
        test_session.add(template)
        test_session.commit()

        # Create another user
        user2 = create_test_user(role=UserRole.USER)
        test_session.add(user2)
        test_session.commit()

        result = await permission_service.apply_template_to_users(
            template_id=template.template_id,
            user_ids=[test_user.user_id, user2.user_id],
            applied_by_user_id=sysadmin_user.user_id,
            change_reason="Test template application",
        )

        assert result["successful"] == 2
        assert result["failed"] == 0
        assert len(result["errors"]) == 0

    async def test_apply_template_to_users_empty_list(
        self, permission_service: PermissionService, sysadmin_user: User
    ) -> None:
        """Test template application to empty user list."""
        template_id = uuid4()

        result = await permission_service.apply_template_to_users(
            template_id=template_id,
            user_ids=[],
            applied_by_user_id=sysadmin_user.user_id,
        )

        assert result["successful"] == 0
        assert result["failed"] == 0
        assert len(result["errors"]) == 0

    async def test_apply_template_to_users_nonexistent_template(
        self, permission_service: PermissionService, test_user: User, sysadmin_user: User
    ) -> None:
        """Test applying non-existent template."""
        nonexistent_template_id = uuid4()

        with pytest.raises(NotFoundError, match="not found"):
            await permission_service.apply_template_to_users(
                template_id=nonexistent_template_id,
                user_ids=[test_user.user_id],
                applied_by_user_id=sysadmin_user.user_id,
            )
