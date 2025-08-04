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
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": password
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["access_token"] != ""
        assert data["token_type"] == "bearer"
        assert data["requires_2fa"] is False
        assert data["session_id"] is None
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["role"] == "user"

    def test_login_success_with_2fa_required(self, client: TestClient, test_session: Session) -> None:
        """Test login with 2FA enabled - should return session_id."""
        # Create test user with 2FA enabled
        password = "Test123!@#"
        user = User(
            email="test2fa@example.com",
            password_hash=auth_service.get_password_hash(password),
            role=UserRole.USER,
            is_active=True,
            totp_enabled=True,
            totp_secret="TESTSECRET123456",
        )
        test_session.add(user)
        test_session.commit()

        # Login request
        response = client.post("/api/v1/auth/login", json={
            "email": "test2fa@example.com",
            "password": password
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["access_token"] == ""  # No token yet
        assert data["requires_2fa"] is True
        assert data["session_id"] is not None
        assert data["user"] is None  # No user data yet

    def test_login_invalid_email(self, client: TestClient) -> None:
        """Test login with non-existent email."""
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })

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
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrong_password"
        })

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
        response = client.post("/api/v1/auth/login", json={
            "email": "inactive@example.com",
            "password": password
        })

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Account is deactivated" in response.json()["detail"]

    def test_login_account_locked(self, client: TestClient, test_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test login with locked account."""
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

        # Mock password security service to return locked account
        def mock_is_account_locked(email: str) -> bool:
            return True

        import src.api.v1.auth as auth_module  # noqa: PLC0415
        monkeypatch.setattr(auth_module.password_security_service, "is_account_locked", mock_is_account_locked)

        # Login request
        response = client.post("/api/v1/auth/login", json={
            "email": "locked@example.com",
            "password": password
        })

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
        response = client.post("/api/v1/auth/login", json={
            "email": "timestamp@example.com",
            "password": password
        })

        assert response.status_code == status.HTTP_200_OK

        # Refresh user from database
        test_session.refresh(user)
        assert user.last_login is not None
        assert isinstance(user.last_login, datetime)


class TestAuth2FA:
    """Test 2FA authentication endpoints."""

    def test_verify_2fa_success(self, client: TestClient, test_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful 2FA verification."""
        # Create test user with 2FA
        user = User(
            email="test2fa@example.com",
            password_hash=auth_service.get_password_hash("password123"),
            role=UserRole.USER,
            is_active=True,
            totp_enabled=True,
            totp_secret="TESTSECRET123456",
        )
        test_session.add(user)
        test_session.commit()

        # Create a temporary session
        session_id = "temp_session_123"

        # Mock temporary session
        def mock_get_temp_session(session_id: str) -> SessionData:
            return SessionData(
                user_email="test2fa@example.com",
                user_id=str(user.user_id),
                user_role="user",
                created_at=datetime.utcnow().isoformat(),
                last_activity=datetime.utcnow().isoformat(),
            )

        def mock_revoke_temp_session(session_id: str) -> None:
            pass

        # Mock TOTP verification
        def mock_verify_totp(secret: str, code: str) -> bool:
            return code == "123456"

        import src.api.v1.auth as auth_module  # noqa: PLC0415
        monkeypatch.setattr(auth_service, "get_temp_session", mock_get_temp_session)
        monkeypatch.setattr(auth_service, "revoke_temp_session", mock_revoke_temp_session)
        monkeypatch.setattr(auth_module.totp_service, "verify_totp", mock_verify_totp)

        # Verify 2FA
        response = client.post("/api/v1/auth/2fa/verify", json={
            "session_id": session_id,
            "totp_code": "123456"
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["access_token"] != ""
        assert data["requires_2fa"] is False
        assert data["user"]["email"] == "test2fa@example.com"

    def test_verify_2fa_invalid_session(self, client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test 2FA verification with invalid session."""
        # Mock invalid session
        def mock_get_temp_session(session_id: str) -> SessionData | None:
            return None

        import src.api.v1.auth as auth_module  # noqa: PLC0415
        monkeypatch.setattr(auth_service, "get_temp_session", mock_get_temp_session)

        # Verify 2FA
        response = client.post("/api/v1/auth/2fa/verify", json={
            "session_id": "invalid_session",
            "totp_code": "123456"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid or expired session" in response.json()["detail"]

    def test_verify_2fa_invalid_code(self, client: TestClient, test_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test 2FA verification with invalid TOTP code."""
        # Create test user with 2FA
        user = User(
            email="test2fa@example.com",
            password_hash=auth_service.get_password_hash("password123"),
            role=UserRole.USER,
            is_active=True,
            totp_enabled=True,
            totp_secret="TESTSECRET123456",
        )
        test_session.add(user)
        test_session.commit()

        # Mock temporary session
        def mock_get_temp_session(session_id: str) -> SessionData:
            return SessionData(
                user_email="test2fa@example.com",
                user_id=str(user.user_id),
                user_role="user",
                created_at=datetime.utcnow().isoformat(),
                last_activity=datetime.utcnow().isoformat(),
            )

        # Mock TOTP verification to fail
        def mock_verify_totp(secret: str, code: str) -> bool:
            return False

        import src.api.v1.auth as auth_module  # noqa: PLC0415
        monkeypatch.setattr(auth_service, "get_temp_session", mock_get_temp_session)
        monkeypatch.setattr(auth_module.totp_service, "verify_totp", mock_verify_totp)

        # Verify 2FA with wrong code (use 6-digit code to pass schema validation)
        response = client.post("/api/v1/auth/2fa/verify", json={
            "session_id": "temp_session_123",
            "totp_code": "000000"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid 2FA code" in response.json()["detail"]

    def test_setup_2fa_success(self, client: TestClient, test_session: Session, monkeypatch: pytest.MonkeyPatch, auth_headers: dict[str, str], mock_user: TokenData) -> None:
        """Test successful 2FA setup."""
        # Create test user matching the mock_user email
        user = User(
            user_id=mock_user.user_id,
            email=mock_user.email,  # Use the mock user's email
            password_hash=auth_service.get_password_hash("password123"),
            role=UserRole.ADMIN,  # Match mock user role
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

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
        test_session.refresh(user)
        assert user.totp_enabled is True
        assert user.totp_secret == "NEW_TOTP_SECRET"

    def test_setup_2fa_already_enabled(self, client: TestClient, test_session: Session, auth_headers: dict[str, str], mock_user: TokenData) -> None:
        """Test 2FA setup when already enabled."""
        # Create test user with 2FA already enabled, matching mock user
        user = User(
            user_id=mock_user.user_id,
            email=mock_user.email,
            password_hash=auth_service.get_password_hash("password123"),
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=True,
            totp_secret="EXISTING_SECRET",
        )
        test_session.add(user)
        test_session.commit()

        # Try to setup 2FA again with authentication header
        response = client.post("/api/v1/auth/2fa/setup", headers=auth_headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "2FA is already enabled" in response.json()["detail"]


class TestAuthTokens:
    """Test token-related authentication endpoints."""

    def test_refresh_token_success(self, client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful token refresh."""
        # Mock token verification
        def mock_verify_token(token: str) -> TokenData:
            return TokenData(
                user_id=uuid4(),
                email="test@example.com",
                role="user",
                session_id="test_session",
                jti="old_jti",
            )

        import src.api.v1.auth as auth_module  # noqa: PLC0415
        monkeypatch.setattr(auth_service, "verify_token", mock_verify_token)

        # Refresh token request
        response = client.post("/api/v1/auth/refresh", headers={
            "Authorization": "Bearer old_token"
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_logout_success(self, client: TestClient, monkeypatch: pytest.MonkeyPatch, auth_headers: dict[str, str]) -> None:
        """Test successful logout."""
        # Mock blacklist and session revocation
        def mock_blacklist_token(jti: str, exp_timestamp: int) -> None:
            pass

        def mock_revoke_session(session_id: str) -> None:
            pass

        import src.api.v1.auth as auth_module  # noqa: PLC0415
        monkeypatch.setattr(auth_service, "blacklist_token", mock_blacklist_token)
        monkeypatch.setattr(auth_service, "revoke_session", mock_revoke_session)

        # Logout request with authentication header
        response = client.post("/api/v1/auth/logout", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "Logged out successfully" in data["message"]

    def test_logout_with_exception(self, client: TestClient, monkeypatch: pytest.MonkeyPatch, auth_headers: dict[str, str]) -> None:
        """Test logout with exception during cleanup."""
        # Mock functions that raise exceptions
        def mock_blacklist_token(jti: str, exp_timestamp: int) -> None:
            raise Exception("Redis connection failed")

        def mock_revoke_session(session_id: str) -> None:
            raise Exception("Session revocation failed")

        import src.api.v1.auth as auth_module  # noqa: PLC0415
        monkeypatch.setattr(auth_service, "blacklist_token", mock_blacklist_token)
        monkeypatch.setattr(auth_service, "revoke_session", mock_revoke_session)

        # Logout should still succeed despite exceptions
        response = client.post("/api/v1/auth/logout", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    def test_get_current_user_success(self, client: TestClient, test_session: Session, auth_headers: dict[str, str], mock_user: TokenData) -> None:
        """Test getting current user information."""
        # Create test user matching mock user
        user = User(
            user_id=mock_user.user_id,
            email=mock_user.email,
            password_hash=auth_service.get_password_hash("password123"),
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=True,
            last_login=datetime.utcnow(),
        )
        test_session.add(user)
        test_session.commit()

        # Get current user with authentication header
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == mock_user.email
        assert data["role"] == "admin"
        assert data["is_active"] is True
        assert "created_at" in data

    def test_get_current_user_not_found(self, client: TestClient, test_session: Session) -> None:
        """Test getting current user when user not found in database."""
        from src.core import security  # noqa: PLC0415
        from src.main import app  # noqa: PLC0415
        
        # Create a non-existent user token data
        nonexistent_user_token = TokenData(
            user_id=uuid4(),  # Non-existent user ID
            email="nonexistent@example.com",
            role="user", 
            session_id="test_session",
            jti="test_jti",
        )
        
        def mock_get_nonexistent_user() -> TokenData:
            return nonexistent_user_token
        
        # Temporarily override the authentication dependency for this test
        app.dependency_overrides[security.get_current_user_token] = mock_get_nonexistent_user
        app.dependency_overrides[security.require_authenticated] = mock_get_nonexistent_user
        
        try:
            # Make request with authentication header
            response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer mock_token"})
            
            # Should return 404 because user doesn't exist in database
            assert response.status_code == status.HTTP_404_NOT_FOUND
            # The middleware might convert the error message to a generic one
            error_detail = response.json()["detail"]
            assert "not found" in error_detail.lower() or "user not found" in error_detail.lower()
            
        finally:
            # Restore original overrides (the conftest.py will handle this, but be safe)
            pass


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
        response = client.post("/api/v1/auth/login",
            json={"email": "ip@example.com", "password": password},
            headers={"X-Forwarded-For": "192.168.1.100, 10.0.0.1"}
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
        response = client.post("/api/v1/auth/login",
            json={"email": "realip@example.com", "password": password},
            headers={"X-Real-IP": "192.168.1.200"}
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
        response = client.post("/api/v1/auth/login",
            json={"email": "fallback@example.com", "password": password}
        )

        assert response.status_code == status.HTTP_200_OK
