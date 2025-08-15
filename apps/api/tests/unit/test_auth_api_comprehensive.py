"""
Comprehensive Authentication API endpoint tests to improve coverage.
Following CLAUDE.md guidelines: Never mock internal business logic.
Mock only external dependencies (Redis, time, UUID generation, SMTP).
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.models.user import User, UserRole
from src.services.auth_service import auth_service


@pytest_asyncio.fixture
async def test_user(async_session):
    """Create a test user in the database."""
    # Mock only external UUID generation - APPROVED external dependency
    with patch(
        "uuid.uuid4", return_value=uuid.UUID("12345678-1234-5678-9012-123456789012")
    ):
        password_hash = auth_service.hash_password("TestPassword123!")

        user = User(
            id=uuid.UUID("12345678-1234-5678-9012-123456789012"),
            email="testuser@example.com",
            password_hash=password_hash,
            role=UserRole.USER,
            is_active=True,
            failed_login_attempts=0,
            locked_until=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        return user


@pytest_asyncio.fixture
async def locked_user(async_session):
    """Create a locked user in the database."""
    # Mock only external UUID generation - APPROVED external dependency
    with patch(
        "uuid.uuid4", return_value=uuid.UUID("87654321-4321-8765-2109-987654321098")
    ):
        password_hash = auth_service.hash_password("TestPassword123!")

        user = User(
            id=uuid.UUID("87654321-4321-8765-2109-987654321098"),
            email="lockeduser@example.com",
            password_hash=password_hash,
            role=UserRole.USER,
            is_active=True,
            failed_login_attempts=5,  # Max attempts reached
            locked_until=datetime.now(UTC).replace(hour=23, minute=59, second=59),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        return user


@pytest_asyncio.fixture
async def inactive_user(async_session):
    """Create an inactive user in the database."""
    # Mock only external UUID generation - APPROVED external dependency
    with patch(
        "uuid.uuid4", return_value=uuid.UUID("11111111-1111-1111-1111-111111111111")
    ):
        password_hash = auth_service.hash_password("TestPassword123!")

        user = User(
            id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            email="inactive@example.com",
            password_hash=password_hash,
            role=UserRole.USER,
            is_active=False,  # Inactive user
            failed_login_attempts=0,
            locked_until=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        return user


class TestAuthenticationEndpointCoverage:
    """Test suite to improve authentication endpoint coverage."""

    @pytest.mark.asyncio
    async def test_login_with_locked_account(self, app, locked_user):
        """Test login with locked account returns 423 status."""
        # Mock external Redis operations - APPROVED external dependency
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None
        with patch.object(auth_service, "_redis_client", mock_redis):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "lockeduser@example.com",
                        "password": "TestPassword123!",
                    },
                )

                assert response.status_code == 423
                data = response.json()
                assert "locked" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_with_inactive_user(self, app, inactive_user):
        """Test login with inactive user returns 401 status."""
        # Mock external Redis operations - APPROVED external dependency
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None
        with patch.object(auth_service, "_redis_client", mock_redis):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "inactive@example.com",
                        "password": "TestPassword123!",
                    },
                )

                assert response.status_code == 401
                data = response.json()
                assert "Invalid credentials" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_increments_failed_attempts(self, app, test_user):
        """Test login with wrong password increments failed attempts."""
        # Mock external Redis operations - APPROVED external dependency
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None
        with patch.object(auth_service, "_redis_client", mock_redis):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "testuser@example.com",
                        "password": "WrongPassword123!",
                    },
                )

                assert response.status_code == 401
                data = response.json()
                assert "Invalid credentials" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_with_exception_handling(self, app):
        """Test login exception handling for general errors."""
        # Mock external Redis operations to throw exception - APPROVED external dependency
        mock_redis = MagicMock()
        mock_redis.setex.side_effect = Exception("Redis connection failed")

        with patch.object(auth_service, "_redis_client", mock_redis):
            # Mock the database session to throw an exception
            with patch("src.api.v1.auth.get_user_by_email") as mock_get_user:
                mock_get_user.side_effect = Exception("Database error")

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.post(
                        "/api/v1/auth/login",
                        json={
                            "email": "test@example.com",
                            "password": "TestPassword123!",
                        },
                    )

                    assert response.status_code == 500
                    data = response.json()
                    assert "Login failed" in data["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token_with_exception_handling(self, app):
        """Test refresh token exception handling for general errors."""
        # Mock auth_service.refresh_access_token to throw exception
        with patch.object(auth_service, "refresh_access_token") as mock_refresh:
            mock_refresh.side_effect = Exception("Token refresh error")

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": "valid.token.here"},
                )

                assert response.status_code == 500
                data = response.json()
                assert "Token refresh failed" in data["detail"]

    @pytest.mark.asyncio
    async def test_logout_with_invalid_token_payload(self, app):
        """Test logout with token missing sub claim."""
        # Mock auth_service.verify_token to return payload without sub
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.return_value = {
                "role": "user",
                "exp": 9999999999,
            }  # Missing "sub"

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/v1/auth/logout",
                    headers={"Authorization": "Bearer invalid.token.payload"},
                )

                assert response.status_code == 401
                data = response.json()
                assert "Invalid token payload" in data["detail"]

    @pytest.mark.asyncio
    async def test_logout_with_exception_handling(self, app):
        """Test logout exception handling for general errors."""
        # Mock auth_service.verify_token to throw exception
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.side_effect = Exception("Token verification error")

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/v1/auth/logout",
                    headers={"Authorization": "Bearer some.token.here"},
                )

                assert response.status_code == 500
                data = response.json()
                assert "Logout failed" in data["detail"]

    @pytest.mark.asyncio
    async def test_logout_all_sessions_with_invalid_token_payload(self, app):
        """Test logout all sessions with token missing sub claim."""
        # Mock auth_service.verify_token to return payload without sub
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.return_value = {
                "role": "user",
                "exp": 9999999999,
            }  # Missing "sub"

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/v1/auth/logout-all",
                    headers={"Authorization": "Bearer invalid.token.payload"},
                )

                assert response.status_code == 401
                data = response.json()
                assert "Invalid token payload" in data["detail"]

    @pytest.mark.asyncio
    async def test_logout_all_sessions_with_exception_handling(self, app):
        """Test logout all sessions exception handling for general errors."""
        # Mock auth_service.verify_token to throw exception
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.side_effect = Exception("Token verification error")

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/v1/auth/logout-all",
                    headers={"Authorization": "Bearer some.token.here"},
                )

                assert response.status_code == 500
                data = response.json()
                assert "Logout from all sessions failed" in data["detail"]

    @pytest.mark.asyncio
    async def test_setup_2fa_with_invalid_token_payload(self, app):
        """Test setup 2FA with token missing sub claim."""
        # Mock auth_service.verify_token to return payload without sub
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.return_value = {
                "role": "user",
                "exp": 9999999999,
            }  # Missing "sub"

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(
                    "/api/v1/auth/setup-2fa",
                    headers={"Authorization": "Bearer invalid.token.payload"},
                )

                assert response.status_code == 401
                data = response.json()
                assert "Invalid token payload" in data["detail"]

    @pytest.mark.asyncio
    async def test_setup_2fa_user_not_found(self, app):
        """Test setup 2FA with non-existent user."""
        # Mock auth_service.verify_token to return valid payload for non-existent user
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "99999999-9999-9999-9999-999999999999",
                "role": "user",
                "exp": 9999999999,
            }

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(
                    "/api/v1/auth/setup-2fa",
                    headers={"Authorization": "Bearer valid.token.here"},
                )

                assert response.status_code == 404
                data = response.json()
                assert "User not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_setup_2fa_with_exception_handling(self, app):
        """Test setup 2FA exception handling for general errors."""
        # Mock auth_service.verify_token to throw exception
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.side_effect = Exception("Token verification error")

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(
                    "/api/v1/auth/setup-2fa",
                    headers={"Authorization": "Bearer some.token.here"},
                )

                assert response.status_code == 500
                data = response.json()
                assert "2FA setup failed" in data["detail"]

    @pytest.mark.asyncio
    async def test_enable_2fa_with_invalid_token_payload(self, app):
        """Test enable 2FA with token missing sub claim."""
        # Mock auth_service.verify_token to return payload without sub
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.return_value = {
                "role": "user",
                "exp": 9999999999,
            }  # Missing "sub"

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/v1/auth/enable-2fa",
                    headers={"Authorization": "Bearer invalid.token.payload"},
                    json={"totp_code": "123456"},
                )

                assert response.status_code == 401
                data = response.json()
                assert "Invalid token payload" in data["detail"]

    @pytest.mark.asyncio
    async def test_enable_2fa_user_not_found(self, app):
        """Test enable 2FA with non-existent user."""
        # Mock auth_service.verify_token to return valid payload for non-existent user
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "99999999-9999-9999-9999-999999999999",
                "role": "user",
                "exp": 9999999999,
            }

            # Mock Redis to return a secret (simulating setup was done)
            mock_redis = MagicMock()
            mock_redis.get.return_value = "JBSWY3DPEHPK3PXP"

            with patch.object(auth_service, "_redis_client", mock_redis):
                # Mock TOTP verification
                with patch("src.services.auth_service.pyotp.TOTP.verify") as mock_totp:
                    mock_totp.return_value = True

                    async with AsyncClient(
                        transport=ASGITransport(app=app), base_url="http://test"
                    ) as ac:
                        response = await ac.post(
                            "/api/v1/auth/enable-2fa",
                            headers={"Authorization": "Bearer valid.token.here"},
                            json={"totp_code": "123456"},
                        )

                        assert response.status_code == 404
                        data = response.json()
                        assert "User not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_enable_2fa_with_exception_handling(self, app):
        """Test enable 2FA exception handling for general errors."""
        # Mock auth_service.verify_token to throw exception
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.side_effect = Exception("Token verification error")

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/v1/auth/enable-2fa",
                    headers={"Authorization": "Bearer some.token.here"},
                    json={"totp_code": "123456"},
                )

                assert response.status_code == 500
                data = response.json()
                assert "Failed to enable 2FA" in data["detail"]

    @pytest.mark.asyncio
    async def test_disable_2fa_with_invalid_token_payload(self, app):
        """Test disable 2FA with token missing sub claim."""
        # Mock auth_service.verify_token to return payload without sub
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.return_value = {
                "role": "user",
                "exp": 9999999999,
            }  # Missing "sub"

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.delete(
                    "/api/v1/auth/disable-2fa",
                    headers={"Authorization": "Bearer invalid.token.payload"},
                )

                assert response.status_code == 401
                data = response.json()
                assert "Invalid token payload" in data["detail"]

    @pytest.mark.asyncio
    async def test_disable_2fa_user_not_found(self, app):
        """Test disable 2FA with non-existent user."""
        # Mock auth_service.verify_token to return valid payload for non-existent user
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "99999999-9999-9999-9999-999999999999",
                "role": "user",
                "exp": 9999999999,
            }

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.delete(
                    "/api/v1/auth/disable-2fa",
                    headers={"Authorization": "Bearer valid.token.here"},
                )

                assert response.status_code == 404
                data = response.json()
                assert "User not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_disable_2fa_with_exception_handling(self, app):
        """Test disable 2FA exception handling for general errors."""
        # Mock auth_service.verify_token to throw exception
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.side_effect = Exception("Token verification error")

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.delete(
                    "/api/v1/auth/disable-2fa",
                    headers={"Authorization": "Bearer some.token.here"},
                )

                assert response.status_code == 500
                data = response.json()
                assert "Failed to disable 2FA" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_with_invalid_token_payload(self, app):
        """Test get current user with token missing sub claim."""
        # Mock auth_service.verify_token to return payload without sub
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.return_value = {
                "role": "user",
                "exp": 9999999999,
            }  # Missing "sub"

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": "Bearer invalid.token.payload"},
                )

                assert response.status_code == 401
                data = response.json()
                assert "Invalid token payload" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, app):
        """Test get current user with non-existent user."""
        # Mock auth_service.verify_token to return valid payload for non-existent user
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "99999999-9999-9999-9999-999999999999",
                "role": "user",
                "exp": 9999999999,
            }

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": "Bearer valid.token.here"},
                )

                assert response.status_code == 404
                data = response.json()
                assert "User not found or inactive" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_with_exception_handling(self, app):
        """Test get current user exception handling for general errors."""
        # Mock auth_service.verify_token to throw exception
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.side_effect = Exception("Token verification error")

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": "Bearer some.token.here"},
                )

                assert response.status_code == 500
                data = response.json()
                assert "Failed to retrieve user information" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_with_expired_token_time_calculation(
        self, app, test_user
    ):
        """Test get current user with proper token expiration time calculation."""
        # Mock auth_service.verify_token to return token with past expiration
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": str(test_user.id),
                "role": test_user.role.value,
                "exp": datetime.now(UTC).timestamp() - 3600,  # Token expired 1 hour ago
            }

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": "Bearer expired.token.here"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["expires_in"] == 0  # Should be 0 for expired token
