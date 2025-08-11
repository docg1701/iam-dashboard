"""
Unit tests for UserAgentPermission model.

Tests permission creation, CRUD flags, agent types, and permission logic.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.models.permission import UserAgentPermission, AgentName
from tests.factories import UserAgentPermissionFactory, UserFactory


class TestUserAgentPermissionModel:
    """Test suite for UserAgentPermission model."""
    
    def test_permission_creation_with_defaults(self):
        """Test creating a permission with default values."""
        permission = UserAgentPermissionFactory.create_permission()
        
        assert permission.id is not None
        assert isinstance(permission.id, uuid.UUID)
        assert permission.user_id is not None
        assert isinstance(permission.user_id, uuid.UUID)
        assert permission.agent_name in AgentName
        assert permission.can_create is False  # Default
        assert permission.can_read is False   # Default
        assert permission.can_update is False # Default
        assert permission.can_delete is False # Default
        assert permission.granted_by is not None
        assert isinstance(permission.granted_at, datetime)
        assert permission.expires_at is None
        assert permission.is_active is True
        assert isinstance(permission.created_at, datetime)
        assert isinstance(permission.updated_at, datetime)
    
    def test_permission_creation_with_custom_values(self):
        """Test creating a permission with custom field values."""
        user_id = uuid.uuid4()
        granted_by = uuid.uuid4()
        agent_name = AgentName.CLIENT_MANAGEMENT
        expires_at = datetime.utcnow() + timedelta(days=30)
        
        permission = UserAgentPermissionFactory.create_permission(
            user_id=user_id,
            agent_name=agent_name,
            can_create=True,
            can_read=True,
            can_update=True,
            can_delete=True,
            granted_by=granted_by,
            expires_at=expires_at
        )
        
        assert permission.user_id == user_id
        assert permission.agent_name == agent_name
        assert permission.can_create is True
        assert permission.can_read is True
        assert permission.can_update is True
        assert permission.can_delete is True
        assert permission.granted_by == granted_by
        assert permission.expires_at == expires_at
    
    def test_full_access_permission_creation(self):
        """Test creating a permission with full CRUD access."""
        permission = UserAgentPermissionFactory.create_full_access_permission()
        
        assert permission.can_create is True
        assert permission.can_read is True
        assert permission.can_update is True
        assert permission.can_delete is True
    
    def test_read_only_permission_creation(self):
        """Test creating a permission with read-only access."""
        permission = UserAgentPermissionFactory.create_read_only_permission()
        
        assert permission.can_create is False
        assert permission.can_read is True
        assert permission.can_update is False
        assert permission.can_delete is False
    
    def test_read_write_permission_creation(self):
        """Test creating a permission with read-write access."""
        permission = UserAgentPermissionFactory.create_read_write_permission()
        
        assert permission.can_create is True
        assert permission.can_read is True
        assert permission.can_update is True
        assert permission.can_delete is False
    
    def test_expired_permission_creation(self):
        """Test creating an expired permission."""
        days_expired = 5
        permission = UserAgentPermissionFactory.create_expired_permission(
            days_expired=days_expired
        )
        
        assert permission.expires_at is not None
        assert permission.expires_at < datetime.utcnow()
        
        # Verify it's properly expired
        expected_expiry = datetime.utcnow() - timedelta(days=days_expired)
        time_diff = abs((permission.expires_at - expected_expiry).total_seconds())
        assert time_diff < 60  # Less than 1 minute difference
    
    def test_expiring_permission_creation(self):
        """Test creating a permission that expires in the future."""
        days_until_expiry = 7
        permission = UserAgentPermissionFactory.create_expiring_permission(
            days_until_expiry=days_until_expiry
        )
        
        assert permission.expires_at is not None
        assert permission.expires_at > datetime.utcnow()
        
        # Verify expiry date
        expected_expiry = datetime.utcnow() + timedelta(days=days_until_expiry)
        time_diff = abs((permission.expires_at - expected_expiry).total_seconds())
        assert time_diff < 60  # Less than 1 minute difference
    
    def test_inactive_permission_creation(self):
        """Test creating an inactive permission."""
        permission = UserAgentPermissionFactory.create_inactive_permission()
        
        assert permission.is_active is False
        assert permission.can_read is True  # Should still have the permission
    
    def test_agent_permissions_for_user(self):
        """Test creating permissions for all agents for a user."""
        user = UserFactory.create_user()
        admin = UserFactory.create_admin()
        
        permissions = UserAgentPermissionFactory.create_agent_permissions_for_user(
            user_id=user.id,
            granted_by=admin.id,
            permission_type="full"
        )
        
        # Should create one permission for each agent
        assert len(permissions) == len(AgentName)
        
        # Verify all agents are covered
        agent_names = [p.agent_name for p in permissions]
        for agent in AgentName:
            assert agent in agent_names
        
        # All should have full access
        for permission in permissions:
            assert permission.user_id == user.id
            assert permission.granted_by == admin.id
            assert permission.can_create is True
            assert permission.can_read is True
            assert permission.can_update is True
            assert permission.can_delete is True
    
    def test_permission_scenarios(self):
        """Test creating common permission scenarios."""
        scenarios = UserAgentPermissionFactory.create_permission_scenarios()
        
        assert "full_access_user" in scenarios
        assert "read_only_user" in scenarios
        assert "mixed_permissions" in scenarios
        assert "expired_permissions" in scenarios
        
        # Verify full access scenario
        full_access = scenarios["full_access_user"]
        assert len(full_access) == len(AgentName)
        for permission in full_access:
            assert permission.can_create is True
            assert permission.can_read is True
            assert permission.can_update is True
            assert permission.can_delete is True
        
        # Verify read-only scenario
        read_only = scenarios["read_only_user"]
        assert len(read_only) == len(AgentName)
        for permission in read_only:
            assert permission.can_create is False
            assert permission.can_read is True
            assert permission.can_update is False
            assert permission.can_delete is False
        
        # Verify mixed permissions scenario
        mixed = scenarios["mixed_permissions"]
        assert len(mixed) == 3  # Should have 3 different permission types
        
        # Verify expired permissions
        expired = scenarios["expired_permissions"]
        for permission in expired:
            assert permission.expires_at < datetime.utcnow()
    
    def test_permission_matrix(self):
        """Test creating a permission matrix for multiple users."""
        users = [UserFactory.create_user() for _ in range(6)]
        admin = UserFactory.create_admin()
        
        user_ids = [user.id for user in users]
        
        permissions = UserAgentPermissionFactory.create_permission_matrix(
            users=user_ids,
            admin_id=admin.id
        )
        
        # Should have permissions for all users and all agents
        expected_count = len(user_ids) * len(AgentName)
        assert len(permissions) == expected_count
        
        # Verify all users have permissions
        permission_user_ids = [p.user_id for p in permissions]
        for user_id in user_ids:
            assert user_id in permission_user_ids
        
        # Verify different permission types are used
        permission_types = set()
        for permission in permissions:
            if permission.can_create and permission.can_read and permission.can_update and permission.can_delete:
                permission_types.add("full")
            elif permission.can_create and permission.can_read and permission.can_update and not permission.can_delete:
                permission_types.add("read_write")
            elif not permission.can_create and permission.can_read and not permission.can_update and not permission.can_delete:
                permission_types.add("read_only")
        
        # Should have variety in permission types
        assert len(permission_types) >= 2
    
    def test_permission_id_uniqueness(self):
        """Test that permission IDs are unique."""
        permissions = [UserAgentPermissionFactory.create_permission() for _ in range(10)]
        permission_ids = [p.id for p in permissions]
        
        # All IDs should be unique
        assert len(set(permission_ids)) == len(permission_ids)
    
    def test_permission_timestamps_are_set(self):
        """Test that timestamps are automatically set."""
        permission = UserAgentPermissionFactory.create_permission()
        
        assert permission.granted_at is not None
        assert permission.created_at is not None
        assert permission.updated_at is not None
        assert isinstance(permission.granted_at, datetime)
        assert isinstance(permission.created_at, datetime)
        assert isinstance(permission.updated_at, datetime)
        
        # Should be recent timestamps
        now = datetime.utcnow()
        assert (now - permission.granted_at).total_seconds() < 60
        assert (now - permission.created_at).total_seconds() < 60
        assert (now - permission.updated_at).total_seconds() < 60


class TestUserAgentPermissionProperties:
    """Test suite for UserAgentPermission property methods."""
    
    def test_has_any_permission_property(self):
        """Test has_any_permission property."""
        # No permissions
        no_permissions = UserAgentPermissionFactory.create_permission()
        assert no_permissions.has_any_permission is False
        
        # Has create permission
        create_permission = UserAgentPermissionFactory.create_permission(can_create=True)
        assert create_permission.has_any_permission is True
        
        # Has read permission
        read_permission = UserAgentPermissionFactory.create_permission(can_read=True)
        assert read_permission.has_any_permission is True
        
        # Has update permission
        update_permission = UserAgentPermissionFactory.create_permission(can_update=True)
        assert update_permission.has_any_permission is True
        
        # Has delete permission
        delete_permission = UserAgentPermissionFactory.create_permission(can_delete=True)
        assert delete_permission.has_any_permission is True
        
        # Has multiple permissions
        multiple_permissions = UserAgentPermissionFactory.create_permission(
            can_read=True, can_update=True
        )
        assert multiple_permissions.has_any_permission is True
    
    def test_has_full_access_property(self):
        """Test has_full_access property."""
        # No permissions
        no_permissions = UserAgentPermissionFactory.create_permission()
        assert no_permissions.has_full_access is False
        
        # Partial permissions
        partial_permissions = UserAgentPermissionFactory.create_permission(
            can_read=True, can_update=True
        )
        assert partial_permissions.has_full_access is False
        
        # Full permissions
        full_permissions = UserAgentPermissionFactory.create_full_access_permission()
        assert full_permissions.has_full_access is True
        
        # Missing one permission
        missing_delete = UserAgentPermissionFactory.create_permission(
            can_create=True, can_read=True, can_update=True
        )
        assert missing_delete.has_full_access is False
    
    def test_is_expired_property(self):
        """Test is_expired property."""
        # No expiration date
        no_expiry = UserAgentPermissionFactory.create_permission()
        assert no_expiry.is_expired is False
        
        # Future expiration
        future_expiry = UserAgentPermissionFactory.create_expiring_permission()
        assert future_expiry.is_expired is False
        
        # Past expiration
        past_expiry = UserAgentPermissionFactory.create_expired_permission()
        assert past_expiry.is_expired is True
        
        # Expired just now (edge case)
        just_expired = UserAgentPermissionFactory.create_permission(
            expires_at=datetime.utcnow() - timedelta(seconds=1)
        )
        assert just_expired.is_expired is True
    
    def test_is_valid_property(self):
        """Test is_valid property (active and not expired)."""
        # Active and not expired
        valid_permission = UserAgentPermissionFactory.create_permission()
        assert valid_permission.is_valid is True
        
        # Inactive but not expired
        inactive_permission = UserAgentPermissionFactory.create_inactive_permission()
        assert inactive_permission.is_valid is False
        
        # Active but expired
        expired_permission = UserAgentPermissionFactory.create_expired_permission()
        assert expired_permission.is_valid is False
        
        # Inactive and expired
        inactive_expired = UserAgentPermissionFactory.create_expired_permission(is_active=False)
        assert inactive_expired.is_valid is False
        
        # Active and expires in future
        future_expiry = UserAgentPermissionFactory.create_expiring_permission()
        assert future_expiry.is_valid is True


class TestUserAgentPermissionRepr:
    """Test suite for UserAgentPermission string representation."""
    
    def test_permission_repr(self):
        """Test permission string representation."""
        user_id = uuid.uuid4()
        agent_name = AgentName.CLIENT_MANAGEMENT
        
        permission = UserAgentPermissionFactory.create_permission(
            user_id=user_id,
            agent_name=agent_name,
            can_create=True,
            can_read=True,
            can_update=False,
            can_delete=False
        )
        
        repr_str = repr(permission)
        assert "UserAgentPermission(" in repr_str
        assert str(user_id) in repr_str
        assert "client_management" in repr_str
        assert "CR" in repr_str  # Should show Create and Read permissions
        assert "U" not in repr_str or "D" not in repr_str  # Should not show Update/Delete
    
    def test_permission_repr_full_access(self):
        """Test repr with full CRUD access."""
        permission = UserAgentPermissionFactory.create_full_access_permission()
        
        repr_str = repr(permission)
        assert "CRUD" in repr_str  # Should show all four permissions
    
    def test_permission_repr_no_permissions(self):
        """Test repr with no permissions."""
        permission = UserAgentPermissionFactory.create_permission()
        
        repr_str = repr(permission)
        assert "UserAgentPermission(" in repr_str
        # Should not contain C, R, U, or D
        permission_chars = set(repr_str) & {"C", "R", "U", "D"}
        assert len(permission_chars) == 0


class TestAgentNameEnum:
    """Test suite for AgentName enumeration."""
    
    def test_agent_name_values(self):
        """Test AgentName enum values."""
        assert AgentName.CLIENT_MANAGEMENT.value == "client_management"
        assert AgentName.PDF_PROCESSING.value == "pdf_processing"
        assert AgentName.REPORTS_ANALYSIS.value == "reports_analysis"
        assert AgentName.AUDIO_RECORDING.value == "audio_recording"
    
    def test_agent_name_string_representation(self):
        """Test that AgentName can be used as string."""
        assert str(AgentName.CLIENT_MANAGEMENT) == "client_management"
        assert str(AgentName.PDF_PROCESSING) == "pdf_processing"
        assert str(AgentName.REPORTS_ANALYSIS) == "reports_analysis"
        assert str(AgentName.AUDIO_RECORDING) == "audio_recording"
    
    def test_agent_name_comparison(self):
        """Test AgentName enum comparison."""
        assert AgentName.CLIENT_MANAGEMENT == AgentName.CLIENT_MANAGEMENT
        assert AgentName.PDF_PROCESSING != AgentName.AUDIO_RECORDING
        assert AgentName.CLIENT_MANAGEMENT != "client_management"  # Different types
    
    def test_agent_name_iteration(self):
        """Test that AgentName enum can be iterated."""
        agents = list(AgentName)
        assert len(agents) == 4
        assert AgentName.CLIENT_MANAGEMENT in agents
        assert AgentName.PDF_PROCESSING in agents
        assert AgentName.REPORTS_ANALYSIS in agents
        assert AgentName.AUDIO_RECORDING in agents


class TestUserAgentPermissionValidation:
    """Test suite for UserAgentPermission validation."""
    
    def test_permission_requires_user_id(self):
        """Test that user_id is required."""
        with pytest.raises((ValidationError, TypeError)):
            UserAgentPermission(
                agent_name=AgentName.CLIENT_MANAGEMENT,
                granted_by=uuid.uuid4()
            )
    
    def test_permission_requires_agent_name(self):
        """Test that agent_name is required."""
        with pytest.raises((ValidationError, TypeError)):
            UserAgentPermission(
                user_id=uuid.uuid4(),
                granted_by=uuid.uuid4()
            )
    
    def test_permission_requires_granted_by(self):
        """Test that granted_by is required."""
        with pytest.raises((ValidationError, TypeError)):
            UserAgentPermission(
                user_id=uuid.uuid4(),
                agent_name=AgentName.CLIENT_MANAGEMENT
            )
    
    def test_permission_crud_defaults_to_false(self):
        """Test that CRUD permissions default to False."""
        permission = UserAgentPermissionFactory.create_permission()
        assert permission.can_create is False
        assert permission.can_read is False
        assert permission.can_update is False
        assert permission.can_delete is False
    
    def test_permission_is_active_defaults_to_true(self):
        """Test that is_active defaults to True."""
        permission = UserAgentPermissionFactory.create_permission()
        assert permission.is_active is True
    
    def test_permission_expires_at_can_be_none(self):
        """Test that expires_at can be None."""
        permission = UserAgentPermissionFactory.create_permission(expires_at=None)
        assert permission.expires_at is None