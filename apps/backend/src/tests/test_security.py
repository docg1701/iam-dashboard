"""Tests for security utilities and JWT handling."""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

from src.core.security import (
    AuthService,
    TokenData,
    auth_service,
    get_current_user_token,
    pwd_context,
    require_any_role,
    require_role,
)


class TestTokenData:
    """Test TokenData Pydantic model."""

    def test_token_data_creation(self):
        """Test TokenData model creation."""
        user_id = uuid4()
        token_data = TokenData(
            user_id=user_id,
            role="admin",
            email="admin@example.com"
        )

        assert token_data.user_id == user_id
        assert token_data.role == "admin"
        assert token_data.email == "admin@example.com"

    def test_token_data_validation(self):
        """Test TokenData model validation."""
        # Valid UUID string should work
        token_data = TokenData(
            user_id="12345678-1234-5678-1234-567812345678",
            role="user",
            email="user@example.com"
        )

        assert isinstance(token_data.user_id, UUID)
        assert str(token_data.user_id) == "12345678-1234-5678-1234-567812345678"

    def test_token_data_invalid_uuid(self):
        """Test TokenData with invalid UUID."""
        with pytest.raises(ValidationError, match="Input should be a valid UUID"):
            TokenData(
                user_id="invalid-uuid",
                role="user",
                email="user@example.com"
            )


class TestAuthService:
    """Test AuthService functionality."""

    @pytest.fixture
    def auth_service_instance(self):
        """Create AuthService instance for testing."""
        return AuthService()

    def test_auth_service_init(self, auth_service_instance):
        """Test AuthService initialization."""
        assert auth_service_instance.algorithm == "HS256"
        assert auth_service_instance.access_token_expire_minutes > 0
        assert auth_service_instance.secret_key is not None

    def test_password_hashing(self, auth_service_instance):
        """Test password hashing functionality."""
        password = "test_password_123!"
        hashed = auth_service_instance.get_password_hash(password)

        # Hash should be different from original password
        assert hashed != password

        # Hash should be bcrypt format
        assert hashed.startswith("$2b$")

        # Should verify correctly
        assert auth_service_instance.verify_password(password, hashed) is True

    def test_password_verification_wrong_password(self, auth_service_instance):
        """Test password verification with wrong password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = auth_service_instance.get_password_hash(password)

        assert auth_service_instance.verify_password(wrong_password, hashed) is False

    def test_create_access_token(self, auth_service_instance):
        """Test JWT token creation."""
        user_id = uuid4()
        role = "admin"
        email = "admin@example.com"

        token_data = auth_service_instance.create_access_token(user_id, role, email)

        # Should return dict with required fields
        assert "access_token" in token_data
        assert "token_type" in token_data
        assert "expires_in" in token_data

        assert token_data["token_type"] == "bearer"
        assert token_data["expires_in"] == auth_service_instance.access_token_expire_minutes * 60

        # Token should be decodable
        decoded = jwt.decode(
            token_data["access_token"],
            auth_service_instance.secret_key,
            algorithms=[auth_service_instance.algorithm]
        )

        assert decoded["sub"] == str(user_id)
        assert decoded["role"] == role
        assert decoded["email"] == email
        assert "iat" in decoded
        assert "exp" in decoded

    def test_verify_token_valid(self, auth_service_instance):
        """Test JWT token verification with valid token."""
        user_id = uuid4()
        role = "user"
        email = "user@example.com"

        # Create token
        token_data = auth_service_instance.create_access_token(user_id, role, email)
        access_token = token_data["access_token"]

        # Verify token
        verified_data = auth_service_instance.verify_token(access_token)

        assert isinstance(verified_data, TokenData)
        assert verified_data.user_id == user_id
        assert verified_data.role == role
        assert verified_data.email == email

    def test_verify_token_expired(self, auth_service_instance):
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
            payload,
            auth_service_instance.secret_key,
            algorithm=auth_service_instance.algorithm
        )

        with pytest.raises(HTTPException) as exc_info:
            auth_service_instance.verify_token(expired_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in exc_info.value.detail.lower()

    def test_verify_token_invalid_signature(self, auth_service_instance):
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

    def test_verify_token_malformed(self, auth_service_instance):
        """Test JWT token verification with malformed token."""
        malformed_token = "not.a.valid.jwt.token"

        with pytest.raises(HTTPException) as exc_info:
            auth_service_instance.verify_token(malformed_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail

    def test_verify_token_missing_fields(self, auth_service_instance):
        """Test JWT token verification with missing required fields."""
        # Token missing required fields
        payload = {
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1),
        }

        incomplete_token = jwt.encode(
            payload,
            auth_service_instance.secret_key,
            algorithm=auth_service_instance.algorithm
        )

        with pytest.raises(HTTPException) as exc_info:
            auth_service_instance.verify_token(incomplete_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail

    def test_verify_token_invalid_uuid(self, auth_service_instance):
        """Test JWT token verification with invalid UUID in sub field."""
        payload = {
            "sub": "invalid-uuid-string",
            "role": "user",
            "email": "user@example.com",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1),
        }

        invalid_uuid_token = jwt.encode(
            payload,
            auth_service_instance.secret_key,
            algorithm=auth_service_instance.algorithm
        )

        with pytest.raises(HTTPException) as exc_info:
            auth_service_instance.verify_token(invalid_uuid_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail


class TestGlobalAuthService:
    """Test global auth service instance."""

    def test_global_auth_service_exists(self):
        """Test that global auth service instance exists."""
        assert auth_service is not None
        assert isinstance(auth_service, AuthService)

    def test_global_auth_service_functionality(self):
        """Test global auth service functionality."""
        password = "test_password"
        hashed = auth_service.get_password_hash(password)
        assert auth_service.verify_password(password, hashed) is True


class TestGetCurrentUserToken:
    """Test get_current_user_token dependency."""

    def test_get_current_user_token_valid(self):
        """Test get_current_user_token with valid credentials."""
        user_id = uuid4()
        role = "admin"
        email = "admin@example.com"

        # Create valid token
        token_data = auth_service.create_access_token(user_id, role, email)
        access_token = token_data["access_token"]

        # Mock credentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=access_token
        )

        # Test function
        result = get_current_user_token(credentials)

        assert isinstance(result, TokenData)
        assert result.user_id == user_id
        assert result.role == role
        assert result.email == email

    def test_get_current_user_token_invalid(self):
        """Test get_current_user_token with invalid credentials."""
        # Mock invalid credentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.jwt.token"
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user_token(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail


class TestRequireRole:
    """Test require_role dependency factory."""

    def test_require_role_valid_role(self):
        """Test require_role with valid role."""
        required_role = "admin"
        check_role = require_role(required_role)

        # Token with required role
        token_data = TokenData(
            user_id=uuid4(),
            role="admin",
            email="admin@example.com"
        )

        result = check_role(token_data)
        assert result == token_data

    def test_require_role_sysadmin_always_allowed(self):
        """Test require_role allows sysadmin for any required role."""
        required_role = "admin"
        check_role = require_role(required_role)

        # Token with sysadmin role
        token_data = TokenData(
            user_id=uuid4(),
            role="sysadmin",
            email="sysadmin@example.com"
        )

        result = check_role(token_data)
        assert result == token_data

    def test_require_role_insufficient_permissions(self):
        """Test require_role with insufficient permissions."""
        required_role = "admin"
        check_role = require_role(required_role)

        # Token with insufficient role
        token_data = TokenData(
            user_id=uuid4(),
            role="user",
            email="user@example.com"
        )

        with pytest.raises(HTTPException) as exc_info:
            check_role(token_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Insufficient permissions" in exc_info.value.detail

    def test_require_role_exact_match(self):
        """Test require_role with exact role match."""
        required_role = "user"
        check_role = require_role(required_role)

        token_data = TokenData(
            user_id=uuid4(),
            role="user",
            email="user@example.com"
        )

        result = check_role(token_data)
        assert result == token_data


class TestRequireAnyRole:
    """Test require_any_role dependency factory."""

    def test_require_any_role_valid_role(self):
        """Test require_any_role with valid role from list."""
        required_roles = ["admin", "moderator"]
        check_roles = require_any_role(required_roles)

        # Token with one of the required roles
        token_data = TokenData(
            user_id=uuid4(),
            role="admin",
            email="admin@example.com"
        )

        result = check_roles(token_data)
        assert result == token_data

    def test_require_any_role_sysadmin_always_allowed(self):
        """Test require_any_role allows sysadmin for any required roles."""
        required_roles = ["admin", "moderator"]
        check_roles = require_any_role(required_roles)

        # Token with sysadmin role
        token_data = TokenData(
            user_id=uuid4(),
            role="sysadmin",
            email="sysadmin@example.com"
        )

        result = check_roles(token_data)
        assert result == token_data

    def test_require_any_role_insufficient_permissions(self):
        """Test require_any_role with insufficient permissions."""
        required_roles = ["admin", "moderator"]
        check_roles = require_any_role(required_roles)

        # Token with role not in list
        token_data = TokenData(
            user_id=uuid4(),
            role="user",
            email="user@example.com"
        )

        with pytest.raises(HTTPException) as exc_info:
            check_roles(token_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Insufficient permissions" in exc_info.value.detail

    def test_require_any_role_multiple_valid_roles(self):
        """Test require_any_role with multiple valid roles."""
        required_roles = ["admin", "moderator", "editor"]
        check_roles = require_any_role(required_roles)

        # Test each role in the list
        for role in required_roles:
            token_data = TokenData(
                user_id=uuid4(),
                role=role,
                email=f"{role}@example.com"
            )

            result = check_roles(token_data)
            assert result == token_data

    def test_require_any_role_empty_list(self):
        """Test require_any_role with empty role list."""
        required_roles = []
        check_roles = require_any_role(required_roles)

        # Only sysadmin should be allowed
        token_data = TokenData(
            user_id=uuid4(),
            role="user",
            email="user@example.com"
        )

        with pytest.raises(HTTPException) as exc_info:
            check_roles(token_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

        # But sysadmin should still work
        sysadmin_token = TokenData(
            user_id=uuid4(),
            role="sysadmin",
            email="sysadmin@example.com"
        )

        result = check_roles(sysadmin_token)
        assert result == sysadmin_token


class TestPasswordContext:
    """Test password context configuration."""

    def test_pwd_context_bcrypt(self):
        """Test password context uses bcrypt."""
        password = "test_password_123"
        hashed = pwd_context.hash(password)

        # Should be bcrypt format
        assert hashed.startswith("$2b$")

        # Should verify correctly
        assert pwd_context.verify(password, hashed) is True
        assert pwd_context.verify("wrong_password", hashed) is False

    def test_pwd_context_deprecated_schemes(self):
        """Test password context handles deprecated schemes."""
        # This tests that the context is configured to handle deprecated schemes
        assert "bcrypt" in str(pwd_context.schemes())
        # Check the configuration string instead of the deprecated attribute
        assert pwd_context.to_dict().get("deprecated") == ["auto"]
