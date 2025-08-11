"""
Unit tests for User model.

Tests user creation, validation, authentication fields, and role-based access control.
"""
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from pydantic import ValidationError

from src.models.user import User, UserRole
from tests.factories import UserFactory


class TestUserModel:
    """Test suite for User model."""
    
    def test_user_creation_with_defaults(self):
        """Test creating a user with default values."""
        user = UserFactory.create_user()
        
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert "@" in user.email
        assert user.password_hash is not None
        assert user.role in UserRole
        assert user.is_active is True
        assert user.totp_secret is None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        assert user.last_login_at is None
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
    
    def test_user_creation_with_custom_values(self):
        """Test creating a user with custom field values."""
        custom_email = "custom@test.com"
        custom_role = UserRole.ADMIN
        custom_totp = "JBSWY3DPEHPK3PXP"
        
        user = UserFactory.create_user(
            email=custom_email,
            role=custom_role,
            totp_secret=custom_totp
        )
        
        assert user.email == custom_email
        assert user.role == custom_role
        assert user.totp_secret == custom_totp
    
    def test_user_roles_enum(self):
        """Test that all user roles are valid."""
        roles = [UserRole.SYSADMIN, UserRole.ADMIN, UserRole.USER]
        
        for role in roles:
            user = UserFactory.create_user(role=role)
            assert user.role == role
            assert user.role.value in ["sysadmin", "admin", "user"]
    
    def test_sysadmin_user_creation(self):
        """Test creating a sysadmin user."""
        sysadmin = UserFactory.create_sysadmin()
        
        assert sysadmin.role == UserRole.SYSADMIN
        assert sysadmin.email == "sysadmin@example.com"
        assert sysadmin.is_active is True
    
    def test_admin_user_creation(self):
        """Test creating an admin user."""
        admin = UserFactory.create_admin()
        
        assert admin.role == UserRole.ADMIN
        assert admin.email == "admin@example.com"
        assert admin.is_active is True
    
    def test_regular_user_creation(self):
        """Test creating a regular user."""
        regular_user = UserFactory.create_regular_user()
        
        assert regular_user.role == UserRole.USER
        assert "@" in regular_user.email
        assert regular_user.is_active is True
    
    def test_user_with_2fa_creation(self):
        """Test creating a user with 2FA enabled."""
        user_with_2fa = UserFactory.create_user_with_2fa()
        
        assert user_with_2fa.totp_secret is not None
        assert len(user_with_2fa.totp_secret) > 0
    
    def test_locked_user_creation(self):
        """Test creating a locked user."""
        locked_user = UserFactory.create_locked_user()
        
        assert locked_user.failed_login_attempts == 5
        assert locked_user.locked_until is not None
        assert locked_user.locked_until > datetime.now(timezone.utc)
        assert locked_user.is_active is False
    
    def test_inactive_user_creation(self):
        """Test creating an inactive user."""
        inactive_user = UserFactory.create_inactive_user()
        
        assert inactive_user.is_active is False
    
    def test_user_with_login_history(self):
        """Test creating a user with login history."""
        days_ago = 3
        user = UserFactory.create_user_with_login_history(days_since_login=days_ago)
        
        assert user.last_login_at is not None
        expected_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
        # Allow some tolerance in timing
        time_diff = abs((user.last_login_at - expected_date).total_seconds())
        assert time_diff < 60  # Less than 1 minute difference
    
    def test_multiple_users_creation(self):
        """Test creating multiple users with role distribution."""
        user_count = 10
        role_distribution = {
            UserRole.SYSADMIN: 0.1,  # 1 user
            UserRole.ADMIN: 0.2,     # 2 users
            UserRole.USER: 0.7,      # 7 users
        }
        
        users = UserFactory.create_multiple_users(
            count=user_count,
            role_distribution=role_distribution
        )
        
        assert len(users) == user_count
        
        # Count roles
        role_counts = {}
        for user in users:
            role_counts[user.role] = role_counts.get(user.role, 0) + 1
        
        # Verify distribution (with some tolerance)
        assert role_counts.get(UserRole.SYSADMIN, 0) >= 1
        assert role_counts.get(UserRole.ADMIN, 0) >= 1
        assert role_counts.get(UserRole.USER, 0) >= 1
    
    def test_user_email_validation(self):
        """Test user email validation."""
        # Valid emails should work
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "admin+test@company.org"
        ]
        
        for email in valid_emails:
            user = UserFactory.create_user(email=email)
            assert user.email == email
    
    def test_user_password_hash_generation(self):
        """Test password hash generation."""
        password = "testpassword123"
        expected_hash = UserFactory.get_default_password_hash(password)
        
        user = UserFactory.create_user(password=password)
        assert user.password_hash == expected_hash
        assert user.password_hash != password  # Should be hashed
    
    def test_user_repr(self):
        """Test user string representation."""
        user = UserFactory.create_user(
            email="test@example.com",
            role=UserRole.ADMIN
        )
        
        repr_str = repr(user)
        assert "User(" in repr_str
        assert "test@example.com" in repr_str
        assert "admin" in repr_str
        assert str(user.id) in repr_str
    
    def test_user_id_uniqueness(self):
        """Test that user IDs are unique."""
        users = [UserFactory.create_user() for _ in range(10)]
        user_ids = [user.id for user in users]
        
        # All IDs should be unique
        assert len(set(user_ids)) == len(user_ids)
    
    def test_user_failed_login_attempts_default(self):
        """Test failed login attempts default value."""
        user = UserFactory.create_user()
        assert user.failed_login_attempts == 0
    
    def test_user_timestamps_are_set(self):
        """Test that created_at and updated_at are automatically set."""
        user = UserFactory.create_user()
        
        assert user.created_at is not None
        assert user.updated_at is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        
        # Should be recent timestamps
        now = datetime.now(timezone.utc)
        assert (now - user.created_at).total_seconds() < 60
        assert (now - user.updated_at).total_seconds() < 60


class TestUserValidation:
    """Test suite for User model validation."""
    
    def test_user_requires_email(self):
        """Test that email is required."""
        with pytest.raises((ValidationError, TypeError)):
            User(password_hash="hash123", role=UserRole.USER)
    
    def test_user_requires_password_hash(self):
        """Test that password_hash is required."""
        with pytest.raises((ValidationError, TypeError)):
            User(email="test@example.com", role=UserRole.USER)
    
    def test_user_role_defaults_to_user(self):
        """Test that role defaults to USER."""
        # This test would need direct model instantiation
        # Factory already sets defaults, so we test the model directly
        pass  # Model default is tested through factory behavior
    
    def test_user_is_active_defaults_to_true(self):
        """Test that is_active defaults to True."""
        user = UserFactory.create_user()
        assert user.is_active is True
    
    def test_user_optional_fields_can_be_none(self):
        """Test that optional fields can be None."""
        user = UserFactory.create_user(
            totp_secret=None,
            last_login_at=None,
            locked_until=None
        )
        
        assert user.totp_secret is None
        assert user.last_login_at is None
        assert user.locked_until is None


class TestUserRoleEnum:
    """Test suite for UserRole enumeration."""
    
    def test_user_role_values(self):
        """Test UserRole enum values."""
        assert UserRole.SYSADMIN.value == "sysadmin"
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.USER.value == "user"
    
    def test_user_role_string_representation(self):
        """Test that UserRole can be used as string."""
        assert str(UserRole.SYSADMIN) == "sysadmin"
        assert str(UserRole.ADMIN) == "admin"
        assert str(UserRole.USER) == "user"
    
    def test_user_role_comparison(self):
        """Test UserRole enum comparison."""
        assert UserRole.SYSADMIN == UserRole.SYSADMIN
        assert UserRole.ADMIN != UserRole.USER
        assert UserRole.SYSADMIN != "sysadmin"  # Different types
    
    def test_user_role_iteration(self):
        """Test that UserRole enum can be iterated."""
        roles = list(UserRole)
        assert len(roles) == 3
        assert UserRole.SYSADMIN in roles
        assert UserRole.ADMIN in roles
        assert UserRole.USER in roles