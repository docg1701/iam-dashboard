"""
Unit tests for AuditLog model.

Tests audit log creation, action tracking, resource tracking, and factory methods.
"""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.models.audit import AuditAction, AuditLog
from tests.factories import AuditLogFactory, UserFactory


class TestAuditLogModel:
    """Test suite for AuditLog model."""

    def test_audit_log_creation_with_defaults(self):
        """Test creating an audit log with default values."""
        audit_log = AuditLogFactory.create_audit_log()

        assert audit_log.id is not None
        assert isinstance(audit_log.id, uuid.UUID)
        assert audit_log.action in AuditAction
        assert audit_log.resource_type == "test_resource"  # Factory default
        assert audit_log.actor_id is not None
        assert isinstance(audit_log.actor_id, uuid.UUID)
        assert audit_log.resource_id is not None
        assert isinstance(audit_log.resource_id, uuid.UUID)
        assert audit_log.ip_address is not None
        assert audit_log.user_agent is not None
        assert audit_log.session_id is not None
        assert isinstance(audit_log.timestamp, datetime)
        assert audit_log.old_values is None  # Default
        assert audit_log.new_values is None  # Default
        assert audit_log.description is None  # Default
        assert audit_log.additional_data is None  # Default

    def test_audit_log_creation_with_custom_values(self):
        """Test creating an audit log with custom field values."""
        actor_id = uuid.uuid4()
        resource_id = uuid.uuid4()
        action = AuditAction.UPDATE
        resource_type = "client"
        old_values = {"name": "Old Name"}
        new_values = {"name": "New Name"}
        ip_address = "192.168.1.100"
        user_agent = "Custom User Agent"
        session_id = "custom_session_123"
        description = "Custom audit description"
        additional_data = {"extra": "data"}

        audit_log = AuditLogFactory.create_audit_log(
            action=action,
            resource_type=resource_type,
            actor_id=actor_id,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            description=description,
            additional_data=additional_data,
        )

        assert audit_log.action == action
        assert audit_log.resource_type == resource_type
        assert audit_log.actor_id == actor_id
        assert audit_log.resource_id == resource_id
        assert audit_log.old_values == old_values
        assert audit_log.new_values == new_values
        assert audit_log.ip_address == ip_address
        assert audit_log.user_agent == user_agent
        assert audit_log.session_id == session_id
        assert audit_log.description == description
        assert audit_log.additional_data == additional_data

    def test_user_creation_audit(self):
        """Test creating an audit log for user creation."""
        actor = UserFactory.create_admin()
        user = UserFactory.create_user()

        audit_log = AuditLogFactory.create_user_creation_audit(
            actor_id=actor.id,
            user_id=user.id,
            user_email=user.email,
            user_role=user.role.value,
        )

        assert audit_log.action == AuditAction.CREATE
        assert audit_log.resource_type == "user"
        assert audit_log.actor_id == actor.id
        assert audit_log.resource_id == user.id
        assert audit_log.new_values is not None
        assert audit_log.new_values["email"] == user.email
        assert audit_log.new_values["role"] == user.role.value
        assert audit_log.new_values["is_active"] is True
        assert "Created user with email" in audit_log.description

    def test_user_update_audit(self):
        """Test creating an audit log for user update."""
        actor = UserFactory.create_admin()
        user = UserFactory.create_user()
        old_email = "old@example.com"
        new_email = "new@example.com"

        audit_log = AuditLogFactory.create_user_update_audit(
            actor_id=actor.id, user_id=user.id, old_email=old_email, new_email=new_email
        )

        assert audit_log.action == AuditAction.UPDATE
        assert audit_log.resource_type == "user"
        assert audit_log.actor_id == actor.id
        assert audit_log.resource_id == user.id
        assert audit_log.old_values == {"email": old_email}
        assert audit_log.new_values == {"email": new_email}
        assert old_email in audit_log.description
        assert new_email in audit_log.description

    def test_login_audit(self):
        """Test creating an audit log for user login."""
        user = UserFactory.create_user()
        ip_address = "10.0.0.1"
        session_id = "login_session_123"

        audit_log = AuditLogFactory.create_login_audit(
            user_id=user.id, ip_address=ip_address, session_id=session_id
        )

        assert audit_log.action == AuditAction.LOGIN
        assert audit_log.resource_type == "session"
        assert audit_log.actor_id == user.id
        assert audit_log.resource_id is None  # Login doesn't have resource_id
        assert audit_log.ip_address == ip_address
        assert audit_log.session_id == session_id
        assert "logged in successfully" in audit_log.description.lower()

    def test_logout_audit(self):
        """Test creating an audit log for user logout."""
        user = UserFactory.create_user()
        session_id = "logout_session_123"

        audit_log = AuditLogFactory.create_logout_audit(
            user_id=user.id, session_id=session_id
        )

        assert audit_log.action == AuditAction.LOGOUT
        assert audit_log.resource_type == "session"
        assert audit_log.actor_id == user.id
        assert audit_log.resource_id is None
        assert audit_log.session_id == session_id
        assert "logged out" in audit_log.description.lower()

    def test_client_creation_audit(self):
        """Test creating an audit log for client creation."""
        actor = UserFactory.create_admin()
        client_id = uuid.uuid4()
        client_name = "João Silva"
        client_cpf = "11144477735"

        audit_log = AuditLogFactory.create_client_creation_audit(
            actor_id=actor.id,
            client_id=client_id,
            client_name=client_name,
            client_cpf=client_cpf,
        )

        assert audit_log.action == AuditAction.CREATE
        assert audit_log.resource_type == "client"
        assert audit_log.actor_id == actor.id
        assert audit_log.resource_id == client_id
        assert audit_log.new_values is not None
        assert audit_log.new_values["name"] == client_name
        # CPF should be masked in audit
        assert "111.***." in audit_log.new_values["cpf"]
        assert "35" in audit_log.new_values["cpf"]
        assert client_name in audit_log.description

    def test_permission_change_audit(self):
        """Test creating an audit log for permission changes."""
        actor = UserFactory.create_admin()
        user = UserFactory.create_user()
        agent_name = "client_management"
        old_permissions = {"can_read": True}
        new_permissions = {"can_read": True, "can_create": True}

        audit_log = AuditLogFactory.create_permission_change_audit(
            actor_id=actor.id,
            user_id=user.id,
            agent_name=agent_name,
            old_permissions=old_permissions,
            new_permissions=new_permissions,
        )

        assert audit_log.action == AuditAction.PERMISSION_CHANGE
        assert audit_log.resource_type == "user_agent_permission"
        assert audit_log.actor_id == actor.id
        assert audit_log.resource_id == user.id
        assert audit_log.old_values["permissions"] == old_permissions
        assert audit_log.new_values["permissions"] == new_permissions
        assert audit_log.old_values["agent"] == agent_name
        assert audit_log.new_values["agent"] == agent_name
        assert agent_name in audit_log.description

    def test_delete_audit(self):
        """Test creating an audit log for resource deletion."""
        actor = UserFactory.create_admin()
        resource_id = uuid.uuid4()
        resource_type = "client"
        resource_data = {"name": "Deleted Client", "cpf": "111.***.*35"}

        audit_log = AuditLogFactory.create_delete_audit(
            actor_id=actor.id,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_data=resource_data,
        )

        assert audit_log.action == AuditAction.DELETE
        assert audit_log.resource_type == resource_type
        assert audit_log.actor_id == actor.id
        assert audit_log.resource_id == resource_id
        assert audit_log.old_values == resource_data
        assert audit_log.new_values is None
        assert f"Deleted {resource_type} resource" in audit_log.description

    def test_audit_trail_for_user_session(self):
        """Test creating a complete audit trail for user session."""
        user = UserFactory.create_user()
        session_duration = 2
        actions_count = 5

        audit_logs = AuditLogFactory.create_audit_trail_for_user_session(
            user_id=user.id,
            session_duration_hours=session_duration,
            actions_count=actions_count,
        )

        # Should have login + actions + logout
        expected_count = actions_count + 2
        assert len(audit_logs) == expected_count

        # First should be login
        assert audit_logs[0].action == AuditAction.LOGIN
        assert audit_logs[0].actor_id == user.id

        # Last should be logout
        assert audit_logs[-1].action == AuditAction.LOGOUT
        assert audit_logs[-1].actor_id == user.id

        # Middle ones should be various actions
        middle_actions = audit_logs[1:-1]
        assert len(middle_actions) == actions_count

        for action_log in middle_actions:
            assert action_log.actor_id == user.id
            assert action_log.action in [
                AuditAction.CREATE,
                AuditAction.READ,
                AuditAction.UPDATE,
                AuditAction.DELETE,
            ]

        # All should have same session ID
        session_ids = [log.session_id for log in audit_logs if log.session_id]
        assert len(set(session_ids)) == 1  # All same session ID

    def test_security_audit_logs(self):
        """Test creating security-related audit logs."""
        security_logs = AuditLogFactory.create_security_audit_logs()

        assert len(security_logs) >= 3  # At least 3 different security scenarios

        # Should include failed login
        failed_login = next(
            (
                log
                for log in security_logs
                if log.additional_data and log.additional_data.get("success") is False
            ),
            None,
        )
        assert failed_login is not None
        assert failed_login.action == AuditAction.LOGIN
        assert "invalid password" in failed_login.description.lower()

        # Should include suspicious activity
        suspicious_login = next(
            (
                log
                for log in security_logs
                if log.additional_data and log.additional_data.get("suspicious") is True
            ),
            None,
        )
        assert suspicious_login is not None

        # Should include permission escalation
        perm_change = next(
            (
                log
                for log in security_logs
                if log.action == AuditAction.PERMISSION_CHANGE
            ),
            None,
        )
        assert perm_change is not None

    def test_audit_log_id_uniqueness(self):
        """Test that audit log IDs are unique."""
        audit_logs = [AuditLogFactory.create_audit_log() for _ in range(10)]
        log_ids = [log.id for log in audit_logs]

        # All IDs should be unique
        assert len(set(log_ids)) == len(log_ids)

    def test_audit_log_timestamp_is_set(self):
        """Test that timestamp is automatically set."""
        audit_log = AuditLogFactory.create_audit_log()

        assert audit_log.timestamp is not None
        assert isinstance(audit_log.timestamp, datetime)

        # Should be recent timestamp
        now = datetime.now(UTC)
        assert (now - audit_log.timestamp).total_seconds() < 60


class TestAuditLogFactoryMethod:
    """Test suite for AuditLog.create_audit_entry factory method."""

    def test_create_audit_entry_method(self):
        """Test the create_audit_entry class method."""
        actor_id = uuid.uuid4()
        resource_id = uuid.uuid4()
        action = AuditAction.CREATE
        resource_type = "test_resource"
        old_values = {"old": "value"}
        new_values = {"new": "value"}
        ip_address = "127.0.0.1"
        user_agent = "Test Agent"
        session_id = "test_session"
        description = "Test audit entry"
        additional_data = {"test": "data"}

        audit_log = AuditLog.create_audit_entry(
            action=action,
            resource_type=resource_type,
            actor_id=actor_id,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            description=description,
            additional_data=additional_data,
        )

        assert isinstance(audit_log, AuditLog)
        assert audit_log.action == action
        assert audit_log.resource_type == resource_type
        assert audit_log.actor_id == actor_id
        assert audit_log.resource_id == resource_id
        assert audit_log.old_values == old_values
        assert audit_log.new_values == new_values
        assert audit_log.ip_address == ip_address
        assert audit_log.user_agent == user_agent
        assert audit_log.session_id == session_id
        assert audit_log.description == description
        assert audit_log.additional_data == additional_data

    def test_create_audit_entry_with_minimal_args(self):
        """Test create_audit_entry with minimal required arguments."""
        action = AuditAction.READ
        resource_type = "user"

        audit_log = AuditLog.create_audit_entry(
            action=action, resource_type=resource_type
        )

        assert isinstance(audit_log, AuditLog)
        assert audit_log.action == action
        assert audit_log.resource_type == resource_type
        assert audit_log.actor_id is None
        assert audit_log.resource_id is None
        assert audit_log.old_values is None
        assert audit_log.new_values is None
        assert audit_log.ip_address is None
        assert audit_log.user_agent is None
        assert audit_log.session_id is None
        assert audit_log.description is None
        assert audit_log.additional_data is None


class TestAuditLogRepr:
    """Test suite for AuditLog string representation."""

    def test_audit_log_repr(self):
        """Test audit log string representation."""
        actor_id = uuid.uuid4()
        resource_id = uuid.uuid4()
        action = AuditAction.UPDATE
        resource_type = "client"

        audit_log = AuditLogFactory.create_audit_log(
            action=action,
            resource_type=resource_type,
            actor_id=actor_id,
            resource_id=resource_id,
        )

        repr_str = repr(audit_log)
        assert "AuditLog(" in repr_str
        assert str(audit_log.id) in repr_str
        assert "update" in repr_str.lower()
        assert "client" in repr_str
        assert str(resource_id) in repr_str
        assert str(actor_id) in repr_str


class TestAuditActionEnum:
    """Test suite for AuditAction enumeration."""

    def test_audit_action_values(self):
        """Test AuditAction enum values."""
        assert AuditAction.CREATE.value == "create"
        assert AuditAction.READ.value == "read"
        assert AuditAction.UPDATE.value == "update"
        assert AuditAction.DELETE.value == "delete"
        assert AuditAction.LOGIN.value == "login"
        assert AuditAction.LOGOUT.value == "logout"
        assert AuditAction.PERMISSION_CHANGE.value == "permission_change"

    def test_audit_action_string_representation(self):
        """Test that AuditAction can be used as string."""
        assert str(AuditAction.CREATE) == "create"
        assert str(AuditAction.READ) == "read"
        assert str(AuditAction.UPDATE) == "update"
        assert str(AuditAction.DELETE) == "delete"
        assert str(AuditAction.LOGIN) == "login"
        assert str(AuditAction.LOGOUT) == "logout"
        assert str(AuditAction.PERMISSION_CHANGE) == "permission_change"

    def test_audit_action_comparison(self):
        """Test AuditAction enum comparison."""
        assert AuditAction.CREATE == AuditAction.CREATE
        assert AuditAction.UPDATE != AuditAction.DELETE
        assert AuditAction.LOGIN == "login"  # str enum equals its string value

    def test_audit_action_iteration(self):
        """Test that AuditAction enum can be iterated."""
        actions = list(AuditAction)
        assert len(actions) == 7
        assert AuditAction.CREATE in actions
        assert AuditAction.READ in actions
        assert AuditAction.UPDATE in actions
        assert AuditAction.DELETE in actions
        assert AuditAction.LOGIN in actions
        assert AuditAction.LOGOUT in actions
        assert AuditAction.PERMISSION_CHANGE in actions


class TestAuditLogValidation:
    """Test suite for AuditLog validation."""

    def test_audit_log_requires_action(self):
        """Test that action is required."""
        with pytest.raises((ValidationError, TypeError)):
            AuditLog(resource_type="test")

    def test_audit_log_requires_resource_type(self):
        """Test that resource_type is required."""
        with pytest.raises((ValidationError, TypeError)):
            AuditLog(action=AuditAction.CREATE)

    def test_audit_log_optional_fields_can_be_none(self):
        """Test that optional fields can be None."""
        audit_log = AuditLog(
            action=AuditAction.READ,
            resource_type="test",
            actor_id=None,
            resource_id=None,
            old_values=None,
            new_values=None,
            ip_address=None,
            user_agent=None,
            session_id=None,
            description=None,
            additional_data=None,
        )

        assert audit_log.actor_id is None
        assert audit_log.resource_id is None
        assert audit_log.old_values is None
        assert audit_log.new_values is None
        assert audit_log.ip_address is None
        assert audit_log.user_agent is None
        assert audit_log.session_id is None
        assert audit_log.description is None
        assert audit_log.additional_data is None

    def test_audit_log_json_fields_accept_dict(self):
        """Test that JSON fields accept dictionary values."""
        old_values = {"key1": "value1", "key2": 123}
        new_values = {"key1": "value2", "key2": 456, "key3": True}
        additional_data = {"metadata": {"nested": "value"}, "count": 5}

        audit_log = AuditLogFactory.create_audit_log(
            old_values=old_values,
            new_values=new_values,
            additional_data=additional_data,
        )

        assert audit_log.old_values == old_values
        assert audit_log.new_values == new_values
        assert audit_log.additional_data == additional_data

    def test_audit_log_string_field_length_limits(self):
        """Test string field length limits."""
        # These should work within limits
        audit_log = AuditLogFactory.create_audit_log(
            resource_type="x" * 50,  # Max 50
            ip_address="192.168.1.1",  # Max 45 (IPv6)
            user_agent="x" * 500,  # Max 500
            session_id="x" * 128,  # Max 128
            description="x" * 500,  # Max 500
        )

        assert len(audit_log.resource_type) == 50
        assert len(audit_log.user_agent) == 500
        assert len(audit_log.session_id) == 128
        assert len(audit_log.description) == 500
