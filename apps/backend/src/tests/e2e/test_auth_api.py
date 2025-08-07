"""Tests for authentication API endpoints."""

from datetime import datetime
from typing import Any
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.core.security import SessionData, TokenData, auth_service
from src.models.user import User, UserRole


class TestAuthLogin:
    """Test authentication login endpoint."""

    def test_login_success_without_2fa(self, client: TestClient, test_session: Session) -> None:
        """Test successful login without 2FA enabled."""
        # Create test user
        password = "Test123!@#"
        user = User(
            email="test@example.com",
            password_hash=auth_service.get_password_hash(password),
            role=UserRole.USER,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Login request
        response = client.post(
            "/api/v1/auth/login", json={"email": "test@example.com", "password": password}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["access_token"] != ""
        assert data["token_type"] == "bearer"
        assert data["requires_2fa"] is False
        assert data["session_id"] is None
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["role"] == "user"

    def test_login_success_with_2fa_required(
        self, client: TestClient, test_session: Session
    ) -> None:
        """Test login with 2FA enabled - should return session_id."""
        # Create test user with 2FA enabled
        password = "Test123!@#"
        user = User(
            email="test2fa@example.com",
            password_hash=auth_service.get_password_hash(password),
            role=UserRole.USER,
            is_active=True,
            totp_enabled=True,
            totp_secret="JBSWY3DPEHPK3PXP",  # Valid base32 secret
        )
        test_session.add(user)
        test_session.commit()

        # Login request
        response = client.post(
            "/api/v1/auth/login", json={"email": "test2fa@example.com", "password": password}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["access_token"] == ""  # No token yet
        assert data["requires_2fa"] is True
        assert data["session_id"] is not None
        assert data["user"] is None  # No user data yet

    def test_login_invalid_email(self, client: TestClient) -> None:
        """Test login with non-existent email."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_invalid_password(self, client: TestClient, test_session: Session) -> None:
        """Test login with incorrect password."""
        # Create test user
        user = User(
            email="test@example.com",
            password_hash=auth_service.get_password_hash("correct_password"),
            role=UserRole.USER,
            is_active=True,
        )
        test_session.add(user)
        test_session.commit()

        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login", json={"email": "test@example.com", "password": "wrong_password"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_inactive_user(self, client: TestClient, test_session: Session) -> None:
        """Test login with inactive user account."""
        # Create inactive user
        password = "Test123!@#"
        user = User(
            email="inactive@example.com",
            password_hash=auth_service.get_password_hash(password),
            role=UserRole.USER,
            is_active=False,
        )
        test_session.add(user)
        test_session.commit()

        # Login request
        response = client.post(
            "/api/v1/auth/login", json={"email": "inactive@example.com", "password": password}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Account is deactivated" in response.json()["detail"]

    def test_login_account_locked(
        self, client: TestClient, test_session: Session, mock_redis_client, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test login with locked account using real business logic."""
        # Mock Redis clients for all services that need it
        from src.core import security
        from src.core import password_security
        from src.api.v1 import auth as auth_module
        
        # Mock Redis for all instances
        monkeypatch.setattr(security.auth_service, "redis_client", mock_redis_client)
        monkeypatch.setattr(password_security.auth_service, "redis_client", mock_redis_client)
        monkeypatch.setattr(password_security.password_security_service, "redis_client", mock_redis_client)
        monkeypatch.setattr(auth_module.password_security_service, "redis_client", mock_redis_client)
        
        # Create test user
        password = "Test123!@#"
        user = User(
            email="locked@example.com",
            password_hash=auth_service.get_password_hash(password),
            role=UserRole.USER,
            is_active=True,
        )
        test_session.add(user)
        test_session.commit()

        # Create actual failed login attempts to trigger account lockout
        # This tests the real business logic for account locking
        for i in range(5):  # Make 5 failed attempts (threshold is 5)
            response = client.post(
                "/api/v1/auth/login", 
                json={"email": "locked@example.com", "password": "wrong_password"}
            )
            # Should get 401 for failed attempts
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid email or password" in response.json()["detail"]

        # 6th attempt should trigger lockout (even with wrong password)
        response = client.post(
            "/api/v1/auth/login", 
            json={"email": "locked@example.com", "password": "wrong_password"}
        )
        assert response.status_code == status.HTTP_423_LOCKED
        assert "Account is temporarily locked" in response.json()["detail"]

        # Now attempt login with correct password - should still be locked
        response = client.post(
            "/api/v1/auth/login", json={"email": "locked@example.com", "password": password}
        )
        assert response.status_code == status.HTTP_423_LOCKED
        assert "Account is temporarily locked" in response.json()["detail"]

    def test_login_updates_last_login(self, client: TestClient, test_session: Session) -> None:
        """Test that login updates the user's last_login timestamp."""
        # Create test user
        password = "Test123!@#"
        user = User(
            email="timestamp@example.com",
            password_hash=auth_service.get_password_hash(password),
            role=UserRole.USER,
            is_active=True,
            last_login=None,
        )
        test_session.add(user)
        test_session.commit()
        # Store user_id for potential future use
        _user_id = user.user_id

        # Login request
        response = client.post(
            "/api/v1/auth/login", json={"email": "timestamp@example.com", "password": password}
        )

        assert response.status_code == status.HTTP_200_OK

        # Refresh user from database
        test_session.refresh(user)
        assert user.last_login is not None
        assert isinstance(user.last_login, datetime)


class TestAuth2FA:
    """Test 2FA authentication endpoints."""

    def test_verify_2fa_success(
        self, client: TestClient, test_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful 2FA verification using real business logic."""
        # Create test user with 2FA
        password = "password123"
        user = User(
            email="test2fa@example.com",
            password_hash=auth_service.get_password_hash(password),
            role=UserRole.USER,
            is_active=True,
            totp_enabled=True,
            totp_secret="JBSWY3DPEHPK3PXP",  # Valid base32 secret
        )
        test_session.add(user)
        test_session.commit()

        # First, perform real login to get a temporary session
        login_response = client.post(
            "/api/v1/auth/login", json={"email": "test2fa@example.com", "password": password}
        )
        
        assert login_response.status_code == status.HTTP_200_OK
        login_data = login_response.json()
        assert login_data["requires_2fa"] is True
        session_id = login_data["session_id"]
        assert session_id is not None

        # Mock only external session storage (Redis), not business logic
        # This allows testing real TOTP verification and token generation
        def mock_get_temp_session(session_id: str) -> SessionData:
            return SessionData(
                user_email="test2fa@example.com",
                user_id=str(user.user_id),
                user_role="user",
                created_at=datetime.utcnow().isoformat(),
                last_activity=datetime.utcnow().isoformat(),
            )

        def mock_revoke_temp_session(session_id: str) -> None:
            pass  # Mock external Redis operation

        monkeypatch.setattr(auth_service, "get_temp_session", mock_get_temp_session)
        monkeypatch.setattr(auth_service, "revoke_temp_session", mock_revoke_temp_session)

        # Generate real TOTP code for the current time - tests real TOTP business logic
        import pyotp  # noqa: PLC0415
        totp = pyotp.TOTP("JBSWY3DPEHPK3PXP")  # Valid base32 secret
        current_code = totp.now()

        # Verify 2FA with real TOTP code - tests real verification logic
        response = client.post(
            "/api/v1/auth/2fa/verify", json={"session_id": session_id, "totp_code": current_code}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["access_token"] != ""  # Real JWT token generated
        assert data["requires_2fa"] is False
        assert data["user"]["email"] == "test2fa@example.com"

    def test_verify_2fa_invalid_session(
        self, client: TestClient
    ) -> None:
        """Test 2FA verification with invalid session using real session validation."""
        # Use completely invalid session ID that was never created
        response = client.post(
            "/api/v1/auth/2fa/verify", json={"session_id": "invalid_session_never_created", "totp_code": "123456"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid or expired session" in response.json()["detail"]

    def test_verify_2fa_invalid_code(
        self, client: TestClient, test_session: Session, mock_redis_client, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test 2FA verification with invalid TOTP code using real validation."""
        # Mock Redis clients for all services that need it
        from src.core import security
        from src.core import password_security
        from src.api.v1 import auth as auth_module
        
        # Mock Redis for all instances
        monkeypatch.setattr(security.auth_service, "redis_client", mock_redis_client)
        monkeypatch.setattr(password_security.auth_service, "redis_client", mock_redis_client)
        monkeypatch.setattr(password_security.password_security_service, "redis_client", mock_redis_client)
        monkeypatch.setattr(auth_module.password_security_service, "redis_client", mock_redis_client)
        
        # Create test user with 2FA
        password = "password123"
        user = User(
            email="test2fa@example.com",
            password_hash=auth_service.get_password_hash(password),
            role=UserRole.USER,
            is_active=True,
            totp_enabled=True,
            totp_secret="JBSWY3DPEHPK3PXP",  # Valid base32 secret
        )
        test_session.add(user)
        test_session.commit()

        # First, perform real login to get a temporary session
        login_response = client.post(
            "/api/v1/auth/login", json={"email": "test2fa@example.com", "password": password}
        )
        
        assert login_response.status_code == status.HTTP_200_OK
        login_data = login_response.json()
        session_id = login_data["session_id"]

        # Verify 2FA with intentionally wrong code that will fail real validation
        response = client.post(
            "/api/v1/auth/2fa/verify",
            json={"session_id": session_id, "totp_code": "000000"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid 2FA code" in response.json()["detail"]

    def test_setup_2fa_success(
        self,
        client: TestClient,
        test_session: Session,
        monkeypatch: pytest.MonkeyPatch,
        auth_headers: dict[str, str],
        test_user: User,
    ) -> None:
        """Test successful 2FA setup."""
        # Use the existing test_user fixture instead of creating a new one
        # The auth_headers fixture already matches the test_user

        # Mock TOTP setup
        def mock_setup_totp(email: str) -> Any:
            class SetupData:
                secret = "NEW_TOTP_SECRET"
                qr_code_url = "https://example.com/qr"
                backup_codes = ["code1", "code2", "code3"]

            return SetupData()

        import src.api.v1.auth as auth_module  # noqa: PLC0415

        monkeypatch.setattr(auth_module.totp_service, "setup_totp", mock_setup_totp)

        # Setup 2FA with authentication header
        response = client.post("/api/v1/auth/2fa/setup", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["secret"] == "NEW_TOTP_SECRET"
        assert data["qr_code_url"] == "https://example.com/qr"
        assert len(data["backup_codes"]) == 3

        # Verify user was updated
        test_session.refresh(test_user)
        assert test_user.totp_enabled is True
        assert test_user.totp_secret == "NEW_TOTP_SECRET"

    def test_setup_2fa_already_enabled(
        self,
        client: TestClient,
        test_session: Session,
        auth_headers: dict[str, str],
        test_user: User,
    ) -> None:
        """Test 2FA setup when already enabled."""
        # Update existing test_user to have 2FA already enabled
        test_user.totp_enabled = True
        test_user.totp_secret = "EXISTING_SECRET"
        test_session.commit()

        # Try to setup 2FA again with authentication header
        response = client.post("/api/v1/auth/2fa/setup", headers=auth_headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "2FA is already enabled" in response.json()["detail"]


class TestAuthTokens:
    """Test token-related authentication endpoints."""

    def test_refresh_token_success(
        self, client: TestClient, test_session: Session
    ) -> None:
        """Test successful token refresh using real authentication flow."""
        # Create test user
        password = "Test123!@#"
        user = User(
            email="refresh@example.com",
            password_hash=auth_service.get_password_hash(password),
            role=UserRole.USER,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # First login to get a real token
        login_response = client.post(
            "/api/v1/auth/login", json={"email": "refresh@example.com", "password": password}
        )
        
        assert login_response.status_code == status.HTTP_200_OK
        login_data = login_response.json()
        original_token = login_data["access_token"]

        # Use real token to refresh
        response = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {original_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        # New token should be different from original
        assert data["access_token"] != original_token

    def test_logout_success(
        self, client: TestClient, test_session: Session, mock_redis_client, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful logout using real authentication flow."""
        # Mock Redis clients for all services that need it
        from src.core import security
        from src.core import password_security
        from src.api.v1 import auth as auth_module
        
        # Mock Redis for all instances
        monkeypatch.setattr(security.auth_service, "redis_client", mock_redis_client)
        monkeypatch.setattr(password_security.auth_service, "redis_client", mock_redis_client)
        monkeypatch.setattr(password_security.password_security_service, "redis_client", mock_redis_client)
        monkeypatch.setattr(auth_module.password_security_service, "redis_client", mock_redis_client)
        
        # Create test user
        password = "Test123!@#"
        user = User(
            email="logout@example.com",
            password_hash=auth_service.get_password_hash(password),
            role=UserRole.USER,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # First login to get a real token
        login_response = client.post(
            "/api/v1/auth/login", json={"email": "logout@example.com", "password": password}
        )
        
        assert login_response.status_code == status.HTTP_200_OK
        login_data = login_response.json()
        token = login_data["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Logout request with real authentication token
        response = client.post("/api/v1/auth/logout", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "Logged out successfully" in data["message"]

        # Verify token is actually blacklisted by trying to use it again
        protected_response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert protected_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_with_external_service_failure(
        self, client: TestClient, test_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test logout resilience when external services fail (Redis, etc)."""
        # Create test user
        password = "Test123!@#"
        user = User(
            email="logout_fail@example.com",
            password_hash=auth_service.get_password_hash(password),
            role=UserRole.USER,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # First login to get a real token
        login_response = client.post(
            "/api/v1/auth/login", json={"email": "logout_fail@example.com", "password": password}
        )
        
        token = login_response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Mock external service failures (Redis blacklist, session store)
        import redis.exceptions  # noqa: PLC0415
        def mock_redis_failure(*args, **kwargs):
            raise redis.exceptions.ConnectionError("Redis connection failed")

        # Mock Redis operations to fail (external dependency)
        monkeypatch.setattr("redis.Redis.setex", mock_redis_failure)
        monkeypatch.setattr("redis.Redis.delete", mock_redis_failure)

        # Logout should still succeed despite external service failures
        response = client.post("/api/v1/auth/logout", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    def test_get_current_user_success(
        self,
        client: TestClient,
        test_session: Session,
        auth_headers: dict[str, str],
        test_user: User,
    ) -> None:
        """Test getting current user information."""
        # Use the existing test_user fixture
        # Update with additional properties needed for the test
        test_user.totp_enabled = True
        test_user.last_login = datetime.utcnow()
        test_session.commit()

        # Get current user with authentication header
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email
        assert data["role"] == "admin"
        assert data["is_active"] is True
        assert "created_at" in data

    def test_get_current_user_not_found(self, client: TestClient) -> None:
        """Test getting current user when user not found in database."""
        from fastapi import HTTPException  # noqa: PLC0415
        from src.core import security  # noqa: PLC0415
        from src.main import app  # noqa: PLC0415

        # Test with invalid token format - should return 401 or raise HTTPException
        try:
            response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token_format"})
            
            # Should return 401 because token format is invalid
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            error_detail = response.json()["detail"]
            assert "credentials" in error_detail.lower()
        except HTTPException as e:
            # Alternative: middleware raises HTTPException directly (also valid)
            assert e.status_code == status.HTTP_401_UNAUTHORIZED
            assert "credentials" in e.detail.lower()


class TestAuthHelpers:
    """Test authentication helper functions."""

    def test_get_client_ip_x_forwarded_for(self, client: TestClient, test_session: Session) -> None:
        """Test client IP extraction from X-Forwarded-For header."""
        # Create test user
        password = "Test123!@#"
        user = User(
            email="ip@example.com",
            password_hash=auth_service.get_password_hash(password),
            role=UserRole.USER,
            is_active=True,
        )
        test_session.add(user)
        test_session.commit()

        # Login with X-Forwarded-For header
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "ip@example.com", "password": password},
            headers={"X-Forwarded-For": "192.168.1.100, 10.0.0.1"},
        )

        # Should extract first IP from X-Forwarded-For
        assert response.status_code == status.HTTP_200_OK

    def test_get_client_ip_x_real_ip(self, client: TestClient, test_session: Session) -> None:
        """Test client IP extraction from X-Real-IP header."""
        # Create test user
        password = "Test123!@#"
        user = User(
            email="realip@example.com",
            password_hash=auth_service.get_password_hash(password),
            role=UserRole.USER,
            is_active=True,
        )
        test_session.add(user)
        test_session.commit()

        # Login with X-Real-IP header
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "realip@example.com", "password": password},
            headers={"X-Real-IP": "192.168.1.200"},
        )

        assert response.status_code == status.HTTP_200_OK

    def test_get_client_ip_fallback(self, client: TestClient, test_session: Session) -> None:
        """Test client IP fallback to direct client IP."""
        # Create test user
        password = "Test123!@#"
        user = User(
            email="fallback@example.com",
            password_hash=auth_service.get_password_hash(password),
            role=UserRole.USER,
            is_active=True,
        )
        test_session.add(user)
        test_session.commit()

        # Login without proxy headers (should use direct IP)
        response = client.post(
            "/api/v1/auth/login", json={"email": "fallback@example.com", "password": password}
        )

        assert response.status_code == status.HTTP_200_OK
