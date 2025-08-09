"""Tests for password security service functionality."""

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

import src.core.password_security as ps_module
from src.core.password_security import (
    LoginAttempt,
    PasswordResetToken,
    PasswordSecurityService,
    password_security_service,
)
from src.core.security import auth_service


class TestPasswordSecurityService:
    """Test password security service functionality."""

    @pytest.fixture
    def password_security_service_instance(
        self, mock_redis_client: Any, monkeypatch: pytest.MonkeyPatch
    ) -> PasswordSecurityService:
        """Create PasswordSecurityService instance for testing."""
        # Mock the auth_service redis client
        monkeypatch.setattr(ps_module.auth_service, "redis_client", mock_redis_client)  # type: ignore[attr-defined]
        return PasswordSecurityService()

    def test_password_security_service_init(
        self, password_security_service_instance: PasswordSecurityService
    ) -> None:
        """Test PasswordSecurityService initialization."""
        assert password_security_service_instance.reset_token_expire_hours == 1
        assert password_security_service_instance.max_failed_attempts == 5
        assert password_security_service_instance.lockout_duration_minutes == 15
        assert password_security_service_instance.password_history_count == 5

    def test_generate_reset_token(
        self,
        password_security_service_instance: PasswordSecurityService,
        mock_redis_client: Any,
    ) -> None:
        """Test password reset token generation."""
        user_id = uuid4()
        user_email = "test@example.com"

        token = password_security_service_instance.generate_reset_token(user_id, user_email)

        # Token should be a URL-safe string
        assert isinstance(token, str)
        assert len(token) > 20

        # Token data should be stored in Redis
        token_key = f"password_reset:{token}"
        assert token_key in mock_redis_client.data

        # Verify stored data
        stored_data = PasswordResetToken.model_validate_json(mock_redis_client.data[token_key])
        assert stored_data.user_id == str(user_id)
        assert stored_data.email == user_email
        assert stored_data.token_type == "password_reset"

    def test_verify_reset_token_valid(
        self, password_security_service_instance: PasswordSecurityService
    ) -> None:
        """Test password reset token verification with valid token."""
        user_id = uuid4()
        user_email = "test@example.com"

        # Generate token
        token = password_security_service_instance.generate_reset_token(user_id, user_email)

        # Verify token
        token_data = password_security_service_instance.verify_reset_token(token)

        assert token_data is not None
        assert token_data.user_id == str(user_id)
        assert token_data.email == user_email

    def test_verify_reset_token_invalid(
        self, password_security_service_instance: PasswordSecurityService
    ) -> None:
        """Test password reset token verification with invalid token."""
        invalid_token = "invalid_token_123"

        token_data = password_security_service_instance.verify_reset_token(invalid_token)

        assert token_data is None

    def test_verify_reset_token_expired(
        self,
        password_security_service_instance: PasswordSecurityService,
        mock_redis_client: Any,
    ) -> None:
        """Test password reset token verification with expired token."""
        user_id = uuid4()
        user_email = "test@example.com"

        # Create expired token data
        expired_time = datetime.utcnow() - timedelta(hours=2)
        token_data = PasswordResetToken(
            user_id=str(user_id), email=user_email, expires_at=expired_time.isoformat()
        )

        token = "expired_token"
        mock_redis_client.data[f"password_reset:{token}"] = token_data.model_dump_json()

        # Should return None for expired token
        result = password_security_service_instance.verify_reset_token(token)
        assert result is None

    def test_revoke_reset_token(
        self,
        password_security_service_instance: PasswordSecurityService,
        mock_redis_client: Any,
    ) -> None:
        """Test password reset token revocation."""
        user_id = uuid4()
        user_email = "test@example.com"

        # Generate token
        token = password_security_service_instance.generate_reset_token(user_id, user_email)
        token_key = f"password_reset:{token}"

        # Verify token exists
        assert token_key in mock_redis_client.data

        # Revoke token
        password_security_service_instance.revoke_reset_token(token)

        # Token should be deleted
        assert token_key not in mock_redis_client.data

    def test_record_login_attempt(
        self,
        password_security_service_instance: PasswordSecurityService,
        mock_redis_client: Any,
    ) -> None:
        """Test login attempt recording."""
        email = "test@example.com"
        ip_address = "192.168.1.1"

        # Record failed attempt
        password_security_service_instance.record_login_attempt(email, ip_address, success=False)

        # Check if attempt was recorded
        attempts_key = f"login_attempts:{email}"
        assert attempts_key in mock_redis_client.lists
        assert len(mock_redis_client.lists[attempts_key]) == 1

        # Verify attempt data
        attempt_data = LoginAttempt.model_validate_json(mock_redis_client.lists[attempts_key][0])
        assert attempt_data.email == email
        assert attempt_data.ip_address == ip_address
        assert attempt_data.success is False

    def test_is_account_locked_not_locked(
        self, password_security_service_instance: PasswordSecurityService
    ) -> None:
        """Test account lock check when account is not locked."""
        email = "test@example.com"

        is_locked = password_security_service_instance.is_account_locked(email)

        assert is_locked is False

    def test_is_account_locked_after_max_attempts(
        self, password_security_service_instance: PasswordSecurityService
    ) -> None:
        """Test account lock after maximum failed attempts."""
        email = "test@example.com"
        ip_address = "192.168.1.1"

        # Record maximum failed attempts
        for _ in range(5):
            password_security_service_instance.record_login_attempt(
                email, ip_address, success=False
            )

        is_locked = password_security_service_instance.is_account_locked(email)

        assert is_locked is True

    def test_is_account_locked_successful_login_breaks_chain(
        self, password_security_service_instance: PasswordSecurityService
    ) -> None:
        """Test that successful login breaks the chain of failed attempts."""
        email = "test@example.com"
        ip_address = "192.168.1.1"

        # Record some failed attempts
        for _ in range(3):
            password_security_service_instance.record_login_attempt(
                email, ip_address, success=False
            )

        # Record successful login
        password_security_service_instance.record_login_attempt(email, ip_address, success=True)

        # Record more failed attempts (less than max)
        for _ in range(2):
            password_security_service_instance.record_login_attempt(
                email, ip_address, success=False
            )

        is_locked = password_security_service_instance.is_account_locked(email)

        # Should not be locked because successful login broke the chain
        assert is_locked is False

    def test_clear_failed_attempts(
        self,
        password_security_service_instance: PasswordSecurityService,
        mock_redis_client: Any,
    ) -> None:
        """Test clearing failed login attempts."""
        email = "test@example.com"
        ip_address = "192.168.1.1"

        # Record failed attempts
        for _ in range(3):
            password_security_service_instance.record_login_attempt(
                email, ip_address, success=False
            )

        attempts_key = f"login_attempts:{email}"
        assert attempts_key in mock_redis_client.lists

        # Clear attempts
        password_security_service_instance.clear_failed_attempts(email)

        # Attempts should be cleared
        assert attempts_key not in mock_redis_client.lists

    def test_store_password_hash(
        self,
        password_security_service_instance: PasswordSecurityService,
        mock_redis_client: Any,
    ) -> None:
        """Test password hash storage in history."""
        user_id = uuid4()
        password_hash = "$2b$12$test_hash"

        password_security_service_instance.store_password_hash(user_id, password_hash)

        # Check if hash was stored
        history_key = f"password_history:{user_id}"
        assert history_key in mock_redis_client.lists
        assert mock_redis_client.lists[history_key][0] == password_hash

    def test_store_password_hash_history_limit(
        self,
        password_security_service_instance: PasswordSecurityService,
        mock_redis_client: Any,
    ) -> None:
        """Test password history limit enforcement."""
        user_id = uuid4()

        # Store more than the limit
        for i in range(7):
            password_hash = f"$2b$12$test_hash_{i}"
            password_security_service_instance.store_password_hash(user_id, password_hash)

        # Check that only the limit is kept
        history_key = f"password_history:{user_id}"
        assert len(mock_redis_client.lists[history_key]) == 5

        # Most recent should be first
        assert mock_redis_client.lists[history_key][0] == "$2b$12$test_hash_6"

    def test_is_password_reused_true(
        self,
        password_security_service_instance: PasswordSecurityService,
    ) -> None:
        """Test password reuse detection when password is reused."""
        user_id = uuid4()
        password = "test_password"

        # Create a real password hash using the auth service
        password_hash = auth_service.get_password_hash(password)

        # Store the real password hash in history
        password_security_service_instance.store_password_hash(user_id, password_hash)

        # Check if the same password is reused (should return True)
        is_reused = password_security_service_instance.is_password_reused(user_id, password)

        assert is_reused is True

    def test_is_password_reused_false(
        self,
        password_security_service_instance: PasswordSecurityService,
    ) -> None:
        """Test password reuse detection when password is not reused."""
        user_id = uuid4()
        old_password = "old_password"
        new_password = "new_different_password"

        # Create a real password hash for the old password
        old_password_hash = auth_service.get_password_hash(old_password)

        # Store the old password hash in history
        password_security_service_instance.store_password_hash(user_id, old_password_hash)

        # Check if the new (different) password is reused (should return False)
        is_reused = password_security_service_instance.is_password_reused(user_id, new_password)

        assert is_reused is False

    def test_get_lockout_info_not_locked(
        self, password_security_service_instance: PasswordSecurityService
    ) -> None:
        """Test lockout info when account is not locked."""
        email = "test@example.com"

        lockout_info = password_security_service_instance.get_lockout_info(email)

        assert lockout_info is None

    def test_get_lockout_info_locked(
        self, password_security_service_instance: PasswordSecurityService
    ) -> None:
        """Test lockout info when account is locked."""
        email = "test@example.com"
        ip_address = "192.168.1.1"

        # Record maximum failed attempts
        for _ in range(5):
            password_security_service_instance.record_login_attempt(
                email, ip_address, success=False
            )

        lockout_info = password_security_service_instance.get_lockout_info(email)

        assert lockout_info is not None
        assert lockout_info["locked"] is True
        assert "unlock_in_minutes" in lockout_info
        assert lockout_info["failed_attempts"] == 5

    def test_global_password_security_service_exists(self) -> None:
        """Test that global password security service instance exists."""
        assert password_security_service is not None
        assert isinstance(password_security_service, PasswordSecurityService)


class TestPasswordResetToken:
    """Test PasswordResetToken model."""

    def test_password_reset_token_creation(self) -> None:
        """Test PasswordResetToken model creation."""
        user_id = str(uuid4())
        email = "test@example.com"
        expires_at = datetime.utcnow().isoformat()

        token_data = PasswordResetToken(user_id=user_id, email=email, expires_at=expires_at)

        assert token_data.user_id == user_id
        assert token_data.email == email
        assert token_data.expires_at == expires_at
        assert token_data.token_type == "password_reset"

    def test_password_reset_token_json_serialization(self) -> None:
        """Test PasswordResetToken JSON serialization."""
        user_id = str(uuid4())
        token_data = PasswordResetToken(
            user_id=user_id, email="test@example.com", expires_at="2025-08-02T10:00:00"
        )

        json_str = token_data.model_dump_json()
        assert f'"user_id":"{user_id}"' in json_str
        assert '"token_type":"password_reset"' in json_str

        # Test deserialization
        restored = PasswordResetToken.model_validate_json(json_str)
        assert restored.user_id == token_data.user_id
        assert restored.token_type == token_data.token_type


class TestLoginAttempt:
    """Test LoginAttempt model."""

    def test_login_attempt_creation(self) -> None:
        """Test LoginAttempt model creation."""
        email = "test@example.com"
        ip_address = "192.168.1.1"
        attempted_at = datetime.utcnow().isoformat()

        attempt = LoginAttempt(
            email=email, ip_address=ip_address, attempted_at=attempted_at, success=False
        )

        assert attempt.email == email
        assert attempt.ip_address == ip_address
        assert attempt.attempted_at == attempted_at
        assert attempt.success is False

    def test_login_attempt_json_serialization(self) -> None:
        """Test LoginAttempt JSON serialization."""
        attempt = LoginAttempt(
            email="test@example.com",
            ip_address="192.168.1.1",
            attempted_at="2025-08-02T10:00:00",
            success=True,
        )

        json_str = attempt.model_dump_json()
        assert '"email":"test@example.com"' in json_str
        assert '"success":true' in json_str

        # Test deserialization
        restored = LoginAttempt.model_validate_json(json_str)
        assert restored.email == attempt.email
        assert restored.success == attempt.success
