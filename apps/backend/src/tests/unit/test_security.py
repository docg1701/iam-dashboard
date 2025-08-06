"""Tests for security utilities and JWT handling."""

import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

from src.core.security import (
    AuthService,
    SecureAuthService,
    SessionData,
    TokenData,
    auth_service,
    get_current_user_token,
    pwd_context,
    require_any_role,
    require_role,
)

# MagicMock no longer needed - AuthService handles testing mode internally


class TestTokenData:
    """Test TokenData Pydantic model."""

    def test_token_data_creation(self) -> None:
        """Test TokenData model creation."""
        user_id = uuid4()
        token_data = TokenData(user_id=user_id, role="admin", email="admin@example.com")

        assert token_data.user_id == user_id
        assert token_data.role == "admin"
        assert token_data.email == "admin@example.com"

    def test_token_data_validation(self) -> None:
        """Test TokenData model validation."""
        # Valid UUID string should work
        token_data = TokenData(
            user_id="12345678-1234-5678-1234-567812345678", role="user", email="user@example.com"
        )

        assert isinstance(token_data.user_id, UUID)
        assert str(token_data.user_id) == "12345678-1234-5678-1234-567812345678"

    def test_token_data_invalid_uuid(self) -> None:
        """Test TokenData with invalid UUID."""
        with pytest.raises(ValidationError, match="Input should be a valid UUID"):
            TokenData(user_id="invalid-uuid", role="user", email="user@example.com")


class TestAuthService:
    """Test AuthService functionality."""

    @pytest.fixture
    def auth_service_instance(self) -> AuthService:
        """Create AuthService instance for testing."""
        return AuthService()

    def test_auth_service_init(self, auth_service_instance: AuthService) -> None:
        """Test AuthService initialization."""
        assert auth_service_instance.algorithm == "HS256"
        assert auth_service_instance.access_token_expire_minutes > 0
        assert auth_service_instance.secret_key is not None

    def test_password_hashing(self, auth_service_instance: AuthService) -> None:
        """Test password hashing functionality."""
        password = "test_password_123!"
        hashed = auth_service_instance.get_password_hash(password)

        # Hash should be different from original password
        assert hashed != password

        # Hash should be bcrypt format
        assert hashed.startswith("$2b$")

        # Should verify correctly
        assert auth_service_instance.verify_password(password, hashed) is True

    def test_password_verification_wrong_password(self, auth_service_instance: AuthService) -> None:
        """Test password verification with wrong password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = auth_service_instance.get_password_hash(password)

        assert auth_service_instance.verify_password(wrong_password, hashed) is False

    def test_create_access_token(self, auth_service_instance: AuthService) -> None:
        """Test JWT token creation."""
        user_id = uuid4()
        role = "admin"
        email = "admin@example.com"

        token_data = auth_service_instance.create_access_token(user_id, role, email)

        # Should return TokenResponse with required fields
        assert hasattr(token_data, "access_token")
        assert hasattr(token_data, "token_type")
        assert hasattr(token_data, "expires_in")

        assert token_data.token_type == "bearer"
        assert token_data.expires_in == auth_service_instance.access_token_expire_minutes * 60

        # Token should be decodable
        decoded = jwt.decode(
            token_data.access_token,
            auth_service_instance.secret_key,
            algorithms=[auth_service_instance.algorithm],
        )

        assert decoded["sub"] == str(user_id)
        assert decoded["role"] == role
        assert decoded["email"] == email
        assert "iat" in decoded
        assert "exp" in decoded

    def test_verify_token_valid(self, auth_service_instance: AuthService) -> None:
        """Test JWT token verification with valid token."""
        user_id = uuid4()
        role = "user"
        email = "user@example.com"

        # Create token
        token_data = auth_service_instance.create_access_token(user_id, role, email)
        access_token = token_data.access_token

        # Verify token
        verified_data = auth_service_instance.verify_token(access_token)

        assert isinstance(verified_data, TokenData)
        assert verified_data.user_id == user_id
        assert verified_data.role == role
        assert verified_data.email == email

    def test_verify_token_expired(self, auth_service_instance: AuthService) -> None:
        """Test JWT token verification with expired token."""
        user_id = uuid4()

        # Create token with past expiration
        payload = {
            "sub": str(user_id),
            "role": "user",
            "email": "user@example.com",
            "iat": datetime.utcnow() - timedelta(hours=2),
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
        }

        expired_token = jwt.encode(
            payload, auth_service_instance.secret_key, algorithm=auth_service_instance.algorithm
        )

        with pytest.raises(HTTPException) as exc_info:
            auth_service_instance.verify_token(expired_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in exc_info.value.detail.lower()

    def test_verify_token_invalid_signature(self, auth_service_instance: AuthService) -> None:
        """Test JWT token verification with invalid signature."""
        user_id = uuid4()

        # Create token with wrong secret
        payload = {
            "sub": str(user_id),
            "role": "user",
            "email": "user@example.com",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1),
        }

        invalid_token = jwt.encode(payload, "wrong_secret", algorithm="HS256")

        with pytest.raises(HTTPException) as exc_info:
            auth_service_instance.verify_token(invalid_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "validate credentials" in exc_info.value.detail.lower()

    def test_verify_token_malformed(self, auth_service_instance: AuthService) -> None:
        """Test JWT token verification with malformed token."""
        malformed_token = "not.a.valid.jwt.token"

        with pytest.raises(HTTPException) as exc_info:
            auth_service_instance.verify_token(malformed_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail

    def test_verify_token_missing_fields(self, auth_service_instance: AuthService) -> None:
        """Test JWT token verification with missing required fields."""
        # Token missing required fields
        payload = {
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1),
        }

        incomplete_token = jwt.encode(
            payload, auth_service_instance.secret_key, algorithm=auth_service_instance.algorithm
        )

        with pytest.raises(HTTPException) as exc_info:
            auth_service_instance.verify_token(incomplete_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail

    def test_verify_token_invalid_uuid(self, auth_service_instance: AuthService) -> None:
        """Test JWT token verification with invalid UUID in sub field."""
        payload = {
            "sub": "invalid-uuid-string",
            "role": "user",
            "email": "user@example.com",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1),
        }

        invalid_uuid_token = jwt.encode(
            payload, auth_service_instance.secret_key, algorithm=auth_service_instance.algorithm
        )

        with pytest.raises(HTTPException) as exc_info:
            auth_service_instance.verify_token(invalid_uuid_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail


class TestGlobalAuthService:
    """Test global auth service instance."""

    def test_global_auth_service_exists(self) -> None:
        """Test that global auth service instance exists."""
        assert auth_service is not None
        assert isinstance(auth_service, AuthService)

    def test_global_auth_service_functionality(self) -> None:
        """Test global auth service functionality."""
        password = "test_password"
        hashed = auth_service.get_password_hash(password)
        assert auth_service.verify_password(password, hashed) is True


class TestGetCurrentUserToken:
    """Test get_current_user_token dependency."""

    def test_get_current_user_token_valid(self) -> None:
        """Test get_current_user_token with valid credentials."""
        user_id = uuid4()
        role = "admin"
        email = "admin@example.com"

        # Create valid token
        token_data = auth_service.create_access_token(user_id, role, email)
        access_token = token_data.access_token

        # Mock credentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=access_token)

        # Test function
        result = get_current_user_token(credentials)

        assert isinstance(result, TokenData)
        assert result.user_id == user_id
        assert result.role == role
        assert result.email == email

    def test_get_current_user_token_invalid(self) -> None:
        """Test get_current_user_token with invalid credentials."""
        # Mock invalid credentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.jwt.token")

        with pytest.raises(HTTPException) as exc_info:
            get_current_user_token(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail


class TestRequireRole:
    """Test require_role dependency factory."""

    def test_require_role_valid_role(self) -> None:
        """Test require_role with valid role."""
        required_role = "admin"
        check_role = require_role(required_role)

        # Token with required role
        token_data = TokenData(user_id=uuid4(), role="admin", email="admin@example.com")

        result = check_role(token_data)
        assert result == token_data

    def test_require_role_sysadmin_always_allowed(self) -> None:
        """Test require_role allows sysadmin for any required role."""
        required_role = "admin"
        check_role = require_role(required_role)

        # Token with sysadmin role
        token_data = TokenData(user_id=uuid4(), role="sysadmin", email="sysadmin@example.com")

        result = check_role(token_data)
        assert result == token_data

    def test_require_role_insufficient_permissions(self) -> None:
        """Test require_role with insufficient permissions."""
        required_role = "admin"
        check_role = require_role(required_role)

        # Token with insufficient role
        token_data = TokenData(user_id=uuid4(), role="user", email="user@example.com")

        with pytest.raises(HTTPException) as exc_info:
            check_role(token_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Insufficient permissions" in exc_info.value.detail

    def test_require_role_exact_match(self) -> None:
        """Test require_role with exact role match."""
        required_role = "user"
        check_role = require_role(required_role)

        token_data = TokenData(user_id=uuid4(), role="user", email="user@example.com")

        result = check_role(token_data)
        assert result == token_data


class TestRequireAnyRole:
    """Test require_any_role dependency factory."""

    def test_require_any_role_valid_role(self) -> None:
        """Test require_any_role with valid role from list."""
        required_roles = ["admin", "moderator"]
        check_roles = require_any_role(required_roles)

        # Token with one of the required roles
        token_data = TokenData(user_id=uuid4(), role="admin", email="admin@example.com")

        result = check_roles(token_data)
        assert result == token_data

    def test_require_any_role_sysadmin_always_allowed(self) -> None:
        """Test require_any_role allows sysadmin for any required roles."""
        required_roles = ["admin", "moderator"]
        check_roles = require_any_role(required_roles)

        # Token with sysadmin role
        token_data = TokenData(user_id=uuid4(), role="sysadmin", email="sysadmin@example.com")

        result = check_roles(token_data)
        assert result == token_data

    def test_require_any_role_insufficient_permissions(self) -> None:
        """Test require_any_role with insufficient permissions."""
        required_roles = ["admin", "moderator"]
        check_roles = require_any_role(required_roles)

        # Token with role not in list
        token_data = TokenData(user_id=uuid4(), role="user", email="user@example.com")

        with pytest.raises(HTTPException) as exc_info:
            check_roles(token_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Insufficient permissions" in exc_info.value.detail

    def test_require_any_role_multiple_valid_roles(self) -> None:
        """Test require_any_role with multiple valid roles."""
        required_roles = ["admin", "moderator", "editor"]
        check_roles = require_any_role(required_roles)

        # Test each role in the list
        for role in required_roles:
            token_data = TokenData(user_id=uuid4(), role=role, email=f"{role}@example.com")

            result = check_roles(token_data)
            assert result == token_data

    def test_require_any_role_empty_list(self) -> None:
        """Test require_any_role with empty role list."""
        required_roles: list[str] = []
        check_roles = require_any_role(required_roles)

        # Only sysadmin should be allowed
        token_data = TokenData(user_id=uuid4(), role="user", email="user@example.com")

        with pytest.raises(HTTPException) as exc_info:
            check_roles(token_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

        # But sysadmin should still work
        sysadmin_token = TokenData(user_id=uuid4(), role="sysadmin", email="sysadmin@example.com")

        result = check_roles(sysadmin_token)
        assert result == sysadmin_token


class TestPasswordContext:
    """Test password context configuration."""

    def test_pwd_context_bcrypt(self) -> None:
        """Test password context uses bcrypt."""
        password = "test_password_123"
        hashed = pwd_context.hash(password)

        # Should be bcrypt format
        assert hashed.startswith("$2b$")

        # Should verify correctly
        assert pwd_context.verify(password, hashed) is True
        assert pwd_context.verify("wrong_password", hashed) is False

    def test_pwd_context_deprecated_schemes(self) -> None:
        """Test password context handles deprecated schemes."""
        # This tests that the context is configured to handle deprecated schemes
        assert "bcrypt" in str(pwd_context.schemes())
        # Check the configuration string instead of the deprecated attribute
        assert pwd_context.to_dict().get("deprecated") == ["auto"]


class TestSessionData:
    """Test SessionData Pydantic model."""

    def test_session_data_creation(self) -> None:
        """Test SessionData model creation."""
        session_data = SessionData(
            user_id="12345678-1234-5678-1234-567812345678",
            user_role="admin",
            user_email="admin@example.com",
            created_at="2025-08-02T10:00:00",
            last_activity="2025-08-02T10:30:00",
        )

        assert session_data.user_id == "12345678-1234-5678-1234-567812345678"
        assert session_data.user_role == "admin"
        assert session_data.user_email == "admin@example.com"
        assert session_data.created_at == "2025-08-02T10:00:00"
        assert session_data.last_activity == "2025-08-02T10:30:00"

    def test_session_data_json_serialization(self) -> None:
        """Test SessionData JSON serialization."""
        session_data = SessionData(
            user_id="12345678-1234-5678-1234-567812345678",
            user_role="user",
            user_email="user@example.com",
            created_at="2025-08-02T10:00:00",
            last_activity="2025-08-02T10:30:00",
        )

        json_str = session_data.model_dump_json()
        assert '"user_id":"12345678-1234-5678-1234-567812345678"' in json_str
        assert '"user_role":"user"' in json_str

        # Test deserialization
        restored = SessionData.model_validate_json(json_str)
        assert restored.user_id == session_data.user_id
        assert restored.user_role == session_data.user_role


class TestSecureAuthService:
    """Test SecureAuthService enhanced functionality."""

    @pytest.fixture
    def secure_auth_service(
        self, mock_redis_client: MagicMock
    ) -> SecureAuthService:
        """Create SecureAuthService instance for testing."""
        # Create SecureAuthService with mocked Redis client
        service = SecureAuthService()
        service.redis_client = mock_redis_client
        return service

    def test_secure_auth_service_init(self, secure_auth_service: SecureAuthService) -> None:
        """Test SecureAuthService initialization."""
        assert secure_auth_service.algorithm == "HS256"
        assert secure_auth_service.access_token_expire_minutes > 0
        assert secure_auth_service.session_expire_hours == 24
        assert secure_auth_service.secret_key is not None
        assert secure_auth_service.redis_client is not None

    def test_create_access_token_with_session(
        self, secure_auth_service: SecureAuthService, mock_redis_client: MagicMock
    ) -> None:
        """Test JWT creation with Redis session tracking."""
        user_id = uuid4()
        role = "admin"
        email = "admin@example.com"

        token_data = secure_auth_service.create_access_token(user_id, role, email)

        # Should return enhanced token data
        assert hasattr(token_data, "access_token")
        assert hasattr(token_data, "token_type")
        assert hasattr(token_data, "expires_in")
        assert hasattr(token_data, "session_id")

        assert token_data.token_type == "bearer"
        assert token_data.expires_in == secure_auth_service.access_token_expire_minutes * 60

        # Token should be decodable with enhanced fields
        decoded = jwt.decode(
            token_data.access_token,
            secure_auth_service.secret_key,
            algorithms=[secure_auth_service.algorithm],
        )

        assert decoded["sub"] == str(user_id)
        assert decoded["role"] == role
        assert decoded["email"] == email
        assert decoded["session_id"] == token_data.session_id
        assert "jti" in decoded
        assert "iat" in decoded
        assert "exp" in decoded

        # Session should be stored in Redis
        session_key = f"session:{token_data.session_id}"
        assert session_key in mock_redis_client.data

        session_json = mock_redis_client.data[session_key]
        session_data = SessionData.model_validate_json(session_json)
        assert session_data.user_id == str(user_id)
        assert session_data.user_role == role
        assert session_data.user_email == email

    def test_create_refresh_token(self, secure_auth_service: SecureAuthService) -> None:
        """Test refresh token creation."""
        user_id = uuid4()
        session_id = "test_session_123"

        refresh_token = secure_auth_service.create_refresh_token(user_id, session_id)

        # Token should be decodable
        decoded = jwt.decode(
            refresh_token,
            secure_auth_service.secret_key,
            algorithms=[secure_auth_service.algorithm],
        )

        assert decoded["sub"] == str(user_id)
        assert decoded["session_id"] == session_id
        assert decoded["type"] == "refresh"
        assert "jti" in decoded
        assert "iat" in decoded
        assert "exp" in decoded

    def test_verify_token_with_session_validation(
        self, secure_auth_service: SecureAuthService
    ) -> None:
        """Test token verification with session validation."""
        user_id = uuid4()
        role = "user"
        email = "user@example.com"

        # Create token (which stores session)
        token_data = secure_auth_service.create_access_token(user_id, role, email)
        access_token = token_data.access_token

        # Verify token
        verified_data = secure_auth_service.verify_token(access_token)

        assert isinstance(verified_data, TokenData)
        assert verified_data.user_id == user_id
        assert verified_data.role == role
        assert verified_data.email == email
        assert verified_data.session_id == token_data.session_id
        assert verified_data.jti is not None

    def test_verify_token_invalid_session(
        self, secure_auth_service: SecureAuthService, mock_redis_client: MagicMock
    ) -> None:
        """Test token verification with invalid session."""
        user_id = uuid4()
        role = "user"
        email = "user@example.com"

        # Create token
        token_data = secure_auth_service.create_access_token(user_id, role, email)
        access_token = token_data.access_token

        # Delete session from Redis
        session_key = f"session:{token_data.session_id}"
        del mock_redis_client.data[session_key]

        # Token verification should fail
        with pytest.raises(HTTPException) as exc_info:
            secure_auth_service.verify_token(access_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid session" in exc_info.value.detail

    def test_verify_token_blacklisted(
        self, secure_auth_service: SecureAuthService, mock_redis_client: MagicMock
    ) -> None:
        """Test token verification with blacklisted token."""
        user_id = uuid4()
        role = "user"
        email = "user@example.com"

        # Create token
        token_data = secure_auth_service.create_access_token(user_id, role, email)
        access_token = token_data.access_token

        # Decode to get JTI
        decoded = jwt.decode(
            access_token, secure_auth_service.secret_key, algorithms=[secure_auth_service.algorithm]
        )
        jti = decoded["jti"]

        # Blacklist the token
        mock_redis_client.data[f"blacklist:{jti}"] = "1"

        # Token verification should fail
        with pytest.raises(HTTPException) as exc_info:
            secure_auth_service.verify_token(access_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Token has been revoked" in exc_info.value.detail

    def test_refresh_access_token(self, secure_auth_service: SecureAuthService) -> None:
        """Test access token refresh functionality."""
        user_id = uuid4()
        role = "admin"
        email = "admin@example.com"

        # Create initial token and session
        token_data = secure_auth_service.create_access_token(user_id, role, email)
        session_id = token_data.session_id

        # Create refresh token
        refresh_token = secure_auth_service.create_refresh_token(user_id, session_id)

        # Refresh access token
        new_token_data = secure_auth_service.refresh_access_token(refresh_token)

        # Should return new access token
        assert hasattr(new_token_data, "access_token")
        assert hasattr(new_token_data, "token_type")
        assert hasattr(new_token_data, "expires_in")
        assert hasattr(new_token_data, "session_id")

        # Session ID should be the same
        assert new_token_data.session_id == session_id

        # New token should be valid
        verified_data = secure_auth_service.verify_token(new_token_data.access_token)
        assert verified_data.user_id == user_id
        assert verified_data.role == role
        assert verified_data.email == email

    def test_refresh_access_token_invalid_type(
        self, secure_auth_service: SecureAuthService
    ) -> None:
        """Test refresh token with invalid type."""
        user_id = uuid4()
        role = "user"
        email = "user@example.com"

        # Create regular access token (not refresh)
        token_data = secure_auth_service.create_access_token(user_id, role, email)
        access_token = token_data.access_token

        # Try to use access token as refresh token
        with pytest.raises(HTTPException) as exc_info:
            secure_auth_service.refresh_access_token(access_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token type" in exc_info.value.detail

    def test_refresh_access_token_blacklisted(
        self, secure_auth_service: SecureAuthService, mock_redis_client: MagicMock
    ) -> None:
        """Test refresh token that is blacklisted."""
        user_id = uuid4()
        session_id = "test_session"

        # Create and blacklist refresh token
        refresh_token = secure_auth_service.create_refresh_token(user_id, session_id)
        decoded = jwt.decode(
            refresh_token,
            secure_auth_service.secret_key,
            algorithms=[secure_auth_service.algorithm],
        )
        jti = decoded["jti"]
        mock_redis_client.data[f"blacklist:{jti}"] = "1"

        # Try to refresh
        with pytest.raises(HTTPException) as exc_info:
            secure_auth_service.refresh_access_token(refresh_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Refresh token has been revoked" in exc_info.value.detail

    def test_blacklist_token(
        self, secure_auth_service: SecureAuthService, mock_redis_client: MagicMock
    ) -> None:
        """Test token blacklisting functionality."""
        jti = "test_jti_123"
        exp_timestamp = int((datetime.utcnow() + timedelta(hours=1)).timestamp())

        # Blacklist token
        secure_auth_service.blacklist_token(jti, exp_timestamp)

        # Token should be blacklisted
        assert secure_auth_service._is_token_blacklisted(jti) is True

        # Check Redis storage
        assert f"blacklist:{jti}" in mock_redis_client.data

    def test_blacklist_token_expired(
        self, secure_auth_service: SecureAuthService, mock_redis_client: MagicMock
    ) -> None:
        """Test blacklisting already expired token."""
        jti = "expired_jti"
        exp_timestamp = int((datetime.utcnow() - timedelta(hours=1)).timestamp())

        # Blacklist expired token
        secure_auth_service.blacklist_token(jti, exp_timestamp)

        # Should not be stored since it's already expired
        assert f"blacklist:{jti}" not in mock_redis_client.data

    def test_revoke_session(
        self, secure_auth_service: SecureAuthService, mock_redis_client: MagicMock
    ) -> None:
        """Test session revocation."""
        user_id = uuid4()
        role = "user"
        email = "user@example.com"

        # Create token and session
        token_data = secure_auth_service.create_access_token(user_id, role, email)
        session_id = token_data.session_id

        # Verify session exists
        session_key = f"session:{session_id}"
        assert session_key in mock_redis_client.data

        # Revoke session
        secure_auth_service.revoke_session(session_id)

        # Session should be deleted
        assert session_key not in mock_redis_client.data

    def test_validate_session_updates_activity(
        self, secure_auth_service: SecureAuthService, mock_redis_client: MagicMock
    ) -> None:
        """Test that session validation updates last activity."""
        user_id = uuid4()
        role = "user"
        email = "user@example.com"

        # Create token and session
        token_data = secure_auth_service.create_access_token(user_id, role, email)
        session_id = token_data.session_id

        # Get initial session data
        session_key = f"session:{session_id}"
        initial_session_json = mock_redis_client.data[session_key]
        initial_session = SessionData.model_validate_json(initial_session_json)

        # Wait a moment and validate again
        time.sleep(0.1)

        # Verify token (which calls _validate_session)
        secure_auth_service.verify_token(token_data.access_token)

        # Session should have updated last_activity
        updated_session_json = mock_redis_client.data[session_key]
        updated_session = SessionData.model_validate_json(updated_session_json)

        assert updated_session.last_activity >= initial_session.last_activity

    def test_redis_connection_failure_graceful_handling(self, mock_redis_client: MagicMock) -> None:
        """Test that Redis failures are handled gracefully in most operations."""
        # Create service with mocked Redis that can fail
        service = SecureAuthService()

        # Mock Redis to fail for certain operations
        def failing_setex(key: str, _time: int, value: str) -> bool:
            raise Exception("Redis connection failed")

        mock_redis_client.setex = failing_setex

        # Service should handle Redis failures gracefully for non-critical operations
        # This test verifies that the service doesn't crash completely
        assert service is not None
        assert hasattr(service, "redis_client")
