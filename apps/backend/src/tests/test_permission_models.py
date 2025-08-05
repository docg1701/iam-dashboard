"""
Tests for Permission Models.

This module tests the permission models including validation,
constraints, relationships, and database operations.
"""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from src.models.permissions import (
    AgentName,
    PermissionActions,
    PermissionAuditLog,
    PermissionTemplate,
    UserAgentPermission,
    UserAgentPermissionBase,
    UserAgentPermissionCreate,
    UserAgentPermissionUpdate,
)
from src.tests.factories import (
    create_test_permission,
    create_test_template,
    create_test_user,
)


class TestAgentName:
    """Tests for AgentName enum."""

    def test_agent_name_values(self) -> None:
        """Test that all expected agent names are available."""
        expected_agents = {
            "client_management",
            "pdf_processing",
            "reports_analysis",
            "audio_recording",
        }

        actual_agents = {agent.value for agent in AgentName}
        assert actual_agents == expected_agents

    def test_agent_name_enum_creation(self) -> None:
        """Test creating AgentName enum instances."""
        agent = AgentName.CLIENT_MANAGEMENT
        assert agent.value == "client_management"
        assert str(agent) == "client_management"

    def test_agent_name_from_string(self) -> None:
        """Test creating AgentName from string values."""
        agent = AgentName("pdf_processing")
        assert agent == AgentName.PDF_PROCESSING

    def test_invalid_agent_name(self) -> None:
        """Test creating AgentName with invalid value."""
        with pytest.raises(ValueError):
            AgentName("invalid_agent")


class TestPermissionActions:
    """Tests for PermissionActions model."""

    def test_permission_actions_defaults(self) -> None:
        """Test PermissionActions default values."""
        actions = PermissionActions()

        assert actions.create is False
        assert actions.read is False
        assert actions.update is False
        assert actions.delete is False

    def test_permission_actions_explicit_values(self) -> None:
        """Test PermissionActions with explicit values."""
        actions = PermissionActions(
            create=True,
            read=True,
            update=False,
            delete=True,
        )

        assert actions.create is True
        assert actions.read is True
        assert actions.update is False
        assert actions.delete is True

    def test_permission_actions_model_validation(self) -> None:
        """Test PermissionActions model validation."""
        # Valid data
        valid_data = {
            "create": True,
            "read": False,
            "update": True,
            "delete": False,
        }
        actions = PermissionActions(**valid_data)
        assert actions.create is True
        assert actions.update is True

    def test_permission_actions_serialization(self) -> None:
        """Test PermissionActions serialization to dict."""
        actions = PermissionActions(create=True, read=True, update=False, delete=False)
        data = actions.model_dump()

        expected = {
            "create": True,
            "read": True,
            "update": False,
            "delete": False,
        }
        assert data == expected


class TestUserAgentPermissionBase:
    """Tests for UserAgentPermissionBase model."""

    def test_permission_base_valid_permissions(self) -> None:
        """Test UserAgentPermissionBase with valid permissions."""
        user_id = uuid4()
        permissions = {"create": True, "read": True, "update": False, "delete": False}

        permission_base = UserAgentPermissionBase(
            user_id=user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions=permissions,
        )

        assert permission_base.user_id == user_id
        assert permission_base.agent_name == AgentName.CLIENT_MANAGEMENT
        assert permission_base.permissions == permissions

    def test_permission_base_default_permissions(self) -> None:
        """Test UserAgentPermissionBase with default permissions."""
        user_id = uuid4()

        permission_base = UserAgentPermissionBase(
            user_id=user_id,
            agent_name=AgentName.PDF_PROCESSING,
        )

        expected_default = {"create": False, "read": False, "update": False, "delete": False}
        assert permission_base.permissions == expected_default

    def test_permission_base_validation_missing_keys(self) -> None:
        """Test UserAgentPermissionBase validation with missing permission keys."""
        user_id = uuid4()
        invalid_permissions = {"create": True, "read": True}  # Missing update, delete

        with pytest.raises(ValidationError) as excinfo:
            UserAgentPermissionBase(
                user_id=user_id,
                agent_name=AgentName.CLIENT_MANAGEMENT,
                permissions=invalid_permissions,
            )

        assert "Permissions must contain all keys" in str(excinfo.value)

    def test_permission_base_validation_invalid_values(self) -> None:
        """Test UserAgentPermissionBase validation with non-boolean values."""
        user_id = uuid4()
        invalid_permissions = {"create": "yes", "read": True, "update": False, "delete": False}

        with pytest.raises(ValidationError) as excinfo:
            UserAgentPermissionBase(
                user_id=user_id,
                agent_name=AgentName.CLIENT_MANAGEMENT,
                permissions=invalid_permissions,
            )

        assert "Permission 'create' must be a boolean value" in str(excinfo.value)

    def test_permission_base_validation_not_dict(self) -> None:
        """Test UserAgentPermissionBase validation with non-dict permissions."""
        user_id = uuid4()

        with pytest.raises(ValidationError) as excinfo:
            UserAgentPermissionBase(
                user_id=user_id,
                agent_name=AgentName.CLIENT_MANAGEMENT,
                permissions="invalid",
            )

        assert "Input should be a valid dictionary" in str(excinfo.value)

    def test_permission_base_extra_keys_allowed(self) -> None:
        """Test UserAgentPermissionBase allows extra permission keys."""
        user_id = uuid4()
        permissions_with_extra = {
            "create": True,
            "read": True,
            "update": False,
            "delete": False,
            "extra_permission": True,  # Extra key should be allowed
        }

        permission_base = UserAgentPermissionBase(
            user_id=user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions=permissions_with_extra,
        )

        assert permission_base.permissions["extra_permission"] is True


class TestUserAgentPermission:
    """Tests for UserAgentPermission database model."""

    def test_user_agent_permission_creation(self, test_session: Session) -> None:
        """Test creating UserAgentPermission instance."""
        user = create_test_user()
        test_session.add(user)
        test_session.commit()

        permission = create_test_permission(
            user_id=user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"create": True, "read": True, "update": False, "delete": False},
            created_by_user_id=user.user_id,
        )

        assert permission.user_id == user.user_id
        assert permission.agent_name == AgentName.CLIENT_MANAGEMENT
        assert permission.permissions["create"] is True
        assert permission.created_by_user_id == user.user_id
        assert isinstance(permission.created_at, datetime)

    def test_user_agent_permission_database_persistence(self, test_session: Session) -> None:
        """Test UserAgentPermission database persistence."""
        user = create_test_user()
        test_session.add(user)
        test_session.commit()

        permission = create_test_permission(
            user_id=user.user_id,
            agent_name=AgentName.PDF_PROCESSING,
            created_by_user_id=user.user_id,
        )

        test_session.add(permission)
        test_session.commit()
        test_session.refresh(permission)

        # Verify it was saved and can be retrieved
        retrieved = test_session.get(UserAgentPermission, permission.permission_id)
        assert retrieved is not None
        assert retrieved.user_id == user.user_id
        assert retrieved.agent_name == AgentName.PDF_PROCESSING

    def test_user_agent_permission_unique_constraint(self, test_session: Session) -> None:
        """Test unique constraint on user_id + agent_name."""
        user = create_test_user()
        test_session.add(user)
        test_session.commit()

        # Create first permission
        permission1 = create_test_permission(
            user_id=user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            created_by_user_id=user.user_id,
        )
        test_session.add(permission1)
        test_session.commit()

        # Try to create duplicate permission
        permission2 = create_test_permission(
            user_id=user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,  # Same agent
            created_by_user_id=user.user_id,
        )
        test_session.add(permission2)

        with pytest.raises(IntegrityError):
            test_session.commit()

    def test_user_agent_permission_relationships(self, test_session: Session) -> None:
        """Test UserAgentPermission relationships with User model."""
        user = create_test_user()
        creator = create_test_user()
        test_session.add_all([user, creator])
        test_session.commit()

        permission = create_test_permission(
            user_id=user.user_id,
            agent_name=AgentName.REPORTS_ANALYSIS,
            created_by_user_id=creator.user_id,
        )
        test_session.add(permission)
        test_session.commit()
        test_session.refresh(permission)

        # Test relationships (if implemented)
        # Note: Actual relationship testing depends on SQLModel relationship configuration
        assert permission.user_id == user.user_id
        assert permission.created_by_user_id == creator.user_id

    def test_user_agent_permission_update_timestamp(self, test_session: Session) -> None:
        """Test that updated_at timestamp works correctly."""
        user = create_test_user()
        test_session.add(user)
        test_session.commit()

        permission = create_test_permission(
            user_id=user.user_id,
            agent_name=AgentName.AUDIO_RECORDING,
            created_by_user_id=user.user_id,
        )
        test_session.add(permission)
        test_session.commit()

        original_updated_at = permission.updated_at

        # Update the permission
        permission.permissions = {"create": False, "read": True, "update": True, "delete": False}
        permission.updated_at = datetime.utcnow()
        test_session.commit()

        assert permission.updated_at != original_updated_at

    def test_user_agent_permission_indexes(self) -> None:
        """Test that proper indexes are defined."""
        # This test verifies the table configuration
        table_args = UserAgentPermission.__table_args__

        # Check that indexes are defined
        assert table_args is not None
        assert len(table_args) > 0

        # Convert to string for inspection
        table_args_str = str(table_args)
        assert "ix_user_agent_permissions_user_id" in table_args_str
        assert "ix_user_agent_permissions_agent_name" in table_args_str
        assert "ix_user_agent_permissions_created_at" in table_args_str


class TestPermissionTemplate:
    """Tests for PermissionTemplate model."""

    def test_permission_template_creation(self) -> None:
        """Test creating PermissionTemplate instance."""
        template = create_test_template(
            template_name="Test Template",
            description="Test description",
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

        assert template.template_name == "Test Template"
        assert template.description == "Test description"
        assert "client_management" in template.permissions
        assert "pdf_processing" in template.permissions
        assert isinstance(template.created_at, datetime)

    def test_permission_template_database_persistence(self, test_session: Session) -> None:
        """Test PermissionTemplate database persistence."""
        user = create_test_user()
        test_session.add(user)
        test_session.commit()

        template = create_test_template(
            template_name="Database Test Template",
            created_by_user_id=user.user_id,
        )

        test_session.add(template)
        test_session.commit()
        test_session.refresh(template)

        # Verify it was saved and can be retrieved
        retrieved = test_session.get(PermissionTemplate, template.template_id)
        assert retrieved is not None
        assert retrieved.template_name == "Database Test Template"
        assert retrieved.created_by_user_id == user.user_id

    def test_permission_template_system_template(self) -> None:
        """Test system template functionality."""
        system_template = create_test_template(
            template_name="System Template",
            is_system=True,
        )

        assert system_template.is_system_template is True

        user_template = create_test_template(
            template_name="User Template",
            is_system=False,
        )

        assert user_template.is_system_template is False

    def test_permission_template_validation(self) -> None:
        """Test PermissionTemplate validation."""
        # Test with valid data
        valid_permissions = {
            "client_management": {"create": True, "read": True, "update": False, "delete": False},
        }

        template = create_test_template(
            template_name="Valid Template",
            permissions=valid_permissions,
        )

        assert template.permissions == valid_permissions

    def test_permission_template_empty_permissions(self) -> None:
        """Test PermissionTemplate with empty permissions gets filled with defaults."""
        template = create_test_template(
            template_name="Empty Template",
            permissions={},
        )

        # Empty permissions should be filled with default values for all agents
        expected_agents = {
            "client_management",
            "pdf_processing",
            "reports_analysis",
            "audio_recording",
        }
        assert set(template.permissions.keys()) == expected_agents

        # All agents should have default CRUD permissions
        for agent_perms in template.permissions.values():
            assert set(agent_perms.keys()) == {"create", "read", "update", "delete"}
            assert all(isinstance(v, bool) for v in agent_perms.values())

    def test_permission_template_update_timestamp(self, test_session: Session) -> None:
        """Test PermissionTemplate update timestamp."""
        user = create_test_user()
        test_session.add(user)
        test_session.commit()

        template = create_test_template(created_by_user_id=user.user_id)
        test_session.add(template)
        test_session.commit()

        original_updated_at = template.updated_at

        # Update the template
        template.description = "Updated description"
        template.updated_at = datetime.utcnow()
        test_session.commit()

        assert template.updated_at != original_updated_at


class TestPermissionAuditLog:
    """Tests for PermissionAuditLog model."""

    def test_permission_audit_log_creation(self) -> None:
        """Test creating PermissionAuditLog instance."""
        from src.tests.factories import create_test_permission_audit_log

        user_id = uuid4()
        changed_by_id = uuid4()

        audit_log = create_test_permission_audit_log(
            user_id=user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            action="CREATE",
            changed_by_user_id=changed_by_id,
            change_reason="Initial setup",
        )

        assert audit_log.user_id == user_id
        assert audit_log.agent_name == AgentName.CLIENT_MANAGEMENT
        assert audit_log.action == "CREATE"
        assert audit_log.changed_by_user_id == changed_by_id
        assert audit_log.change_reason == "Initial setup"
        assert isinstance(audit_log.created_at, datetime)

    def test_permission_audit_log_database_persistence(self, test_session: Session) -> None:
        """Test PermissionAuditLog database persistence."""
        from src.tests.factories import create_test_permission_audit_log

        user = create_test_user()
        test_session.add(user)
        test_session.commit()

        audit_log = create_test_permission_audit_log(
            user_id=user.user_id,
            agent_name=AgentName.PDF_PROCESSING,
            action="UPDATE",
            changed_by_user_id=user.user_id,
        )

        test_session.add(audit_log)
        test_session.commit()
        test_session.refresh(audit_log)

        # Verify it was saved
        retrieved = test_session.get(PermissionAuditLog, audit_log.audit_id)
        assert retrieved is not None
        assert retrieved.user_id == user.user_id
        assert retrieved.action == "UPDATE"

    def test_permission_audit_log_with_permissions_data(self) -> None:
        """Test PermissionAuditLog with old and new permissions."""
        from src.tests.factories import create_test_permission_audit_log

        old_permissions = {"create": False, "read": True, "update": False, "delete": False}
        new_permissions = {"create": True, "read": True, "update": True, "delete": False}

        audit_log = create_test_permission_audit_log(
            action="UPDATE",
            old_permissions=old_permissions,
            new_permissions=new_permissions,
        )

        assert audit_log.old_permissions == old_permissions
        assert audit_log.new_permissions == new_permissions

    def test_permission_audit_log_delete_action(self) -> None:
        """Test PermissionAuditLog for DELETE action."""
        from src.tests.factories import create_test_permission_audit_log

        old_permissions = {"create": True, "read": True, "update": False, "delete": False}

        audit_log = create_test_permission_audit_log(
            action="DELETE",
            old_permissions=old_permissions,
            new_permissions=None,  # No new permissions for delete
        )

        assert audit_log.action == "DELETE"
        assert audit_log.old_permissions == old_permissions
        assert audit_log.new_permissions is None

    def test_permission_audit_log_indexes(self) -> None:
        """Test PermissionAuditLog has proper indexes."""
        table_args = PermissionAuditLog.__table_args__

        # Check that indexes are defined
        assert table_args is not None
        table_args_str = str(table_args)

        # Check for specific index names that should exist
        expected_indexes = [
            "ix_permission_audit_user_id",
            "ix_permission_audit_agent_name",
            "ix_permission_audit_action",
            "ix_permission_audit_changed_by",
            "ix_permission_audit_created_at",
            "ix_permission_audit_user_agent",
        ]
        for index_name in expected_indexes:
            assert index_name in table_args_str


class TestPermissionSchemas:
    """Tests for permission schema models."""

    def test_user_agent_permission_create_schema(self) -> None:
        """Test UserAgentPermissionCreate schema."""
        user_id = uuid4()
        created_by_id = uuid4()
        permissions = {"create": True, "read": True, "update": False, "delete": False}

        create_data = UserAgentPermissionCreate(
            user_id=user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions=permissions,
            created_by_user_id=created_by_id,
        )

        assert create_data.user_id == user_id
        assert create_data.agent_name == AgentName.CLIENT_MANAGEMENT
        assert create_data.permissions == permissions
        assert create_data.created_by_user_id == created_by_id

    def test_user_agent_permission_update_schema(self) -> None:
        """Test UserAgentPermissionUpdate schema."""
        new_permissions = {"create": False, "read": True, "update": True, "delete": False}

        update_data = UserAgentPermissionUpdate(permissions=new_permissions)

        assert update_data.permissions == new_permissions

    def test_user_agent_permission_update_optional_fields(self) -> None:
        """Test UserAgentPermissionUpdate with optional fields."""
        # Test with minimal data
        update_data = UserAgentPermissionUpdate()

        # All fields should be optional/None
        assert update_data.permissions is None


class TestPermissionModelIntegration:
    """Integration tests for permission models."""

    def test_permission_full_lifecycle(self, test_session: Session) -> None:
        """Test complete permission lifecycle: create, update, audit, delete."""
        # Create users
        user = create_test_user()
        admin = create_test_user()
        test_session.add_all([user, admin])
        test_session.commit()

        # Create permission
        permission = create_test_permission(
            user_id=user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"create": False, "read": True, "update": False, "delete": False},
            created_by_user_id=admin.user_id,
        )
        test_session.add(permission)
        test_session.commit()

        # Update permission
        permission.permissions = {"create": True, "read": True, "update": True, "delete": False}
        permission.updated_at = datetime.utcnow()
        test_session.commit()

        # Create audit log
        from src.tests.factories import create_test_permission_audit_log

        audit_log = create_test_permission_audit_log(
            user_id=user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            action="UPDATE",
            old_permissions={"create": False, "read": True, "update": False, "delete": False},
            new_permissions={"create": True, "read": True, "update": True, "delete": False},
            changed_by_user_id=admin.user_id,
        )
        test_session.add(audit_log)
        test_session.commit()

        # Verify all components exist
        assert test_session.get(UserAgentPermission, permission.permission_id) is not None
        assert test_session.get(PermissionAuditLog, audit_log.audit_id) is not None

        # Delete permission
        test_session.delete(permission)
        test_session.commit()

        # Verify permission is deleted but audit log remains
        assert test_session.get(UserAgentPermission, permission.permission_id) is None
        assert test_session.get(PermissionAuditLog, audit_log.audit_id) is not None

    def test_template_application_simulation(self, test_session: Session) -> None:
        """Test simulating template application to users."""
        # Create users and admin
        users = [create_test_user() for _ in range(3)]
        admin = create_test_user()
        test_session.add_all(users + [admin])
        test_session.commit()

        # Create template
        template = create_test_template(
            template_name="Standard User Template",
            permissions={
                "client_management": {
                    "create": False,
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
            created_by_user_id=admin.user_id,
        )
        test_session.add(template)
        test_session.commit()

        # Apply template to users (simulate)
        permissions_created = []
        for user in users:
            for agent_name_str, perms in template.permissions.items():
                agent_name = AgentName(agent_name_str)
                permission = create_test_permission(
                    user_id=user.user_id,
                    agent_name=agent_name,
                    permissions=perms,
                    created_by_user_id=admin.user_id,
                )
                permissions_created.append(permission)

        test_session.add_all(permissions_created)
        test_session.commit()

        # Verify all permissions were created
        assert len(permissions_created) == 6  # 3 users × 2 agents

        # Verify permissions can be queried
        query = select(UserAgentPermission).where(
            UserAgentPermission.user_id.in_([u.user_id for u in users])
        )
        result = test_session.exec(query)
        retrieved_permissions = list(result)

        assert len(retrieved_permissions) == 6

    def test_model_serialization(self) -> None:
        """Test that models can be properly serialized."""
        permission = create_test_permission(
            agent_name=AgentName.PDF_PROCESSING,
            permissions={"create": True, "read": True, "update": False, "delete": False},
        )

        # Test model_dump (Pydantic serialization)
        data = permission.model_dump()

        assert "permission_id" in data
        assert "user_id" in data
        assert "agent_name" in data
        assert "permissions" in data
        assert data["agent_name"] == "pdf_processing"
        assert data["permissions"]["create"] is True

    def test_model_validation_edge_cases(self) -> None:
        """Test model validation with edge cases."""
        # Test very long template name
        long_name = "x" * 1000
        template = create_test_template(template_name=long_name)
        assert template.template_name == long_name

        # Test template with complex nested permissions
        complex_permissions = {
            "client_management": {
                "create": True,
                "read": True,
                "update": False,
                "delete": False,
                "custom_action": True,  # Extra permission
            },
            "pdf_processing": {
                "create": False,
                "read": True,
                "update": False,
                "delete": False,
                "batch_process": True,  # Another extra permission
            },
        }

        template = create_test_template(permissions=complex_permissions)
        assert template.permissions == complex_permissions
