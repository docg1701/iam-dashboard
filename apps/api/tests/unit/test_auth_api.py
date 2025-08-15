"""
Enhanced Authentication API endpoint tests with database integration.
Following CLAUDE.md guidelines: Never mock internal business logic.
Mock only external dependencies (Redis, time, UUID generation, SMTP).
"""

import uuid
from datetime import UTC, datetime, timezone
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.models.user import User, UserRole
from src.services.auth_service import auth_service


@pytest_asyncio.fixture
async def test_db_session(async_session):
    """
    Create a test database session with isolated transaction.
    Following CLAUDE.md: Use real database for integration tests.
    """
    # Use the properly configured async session from conftest
    yield async_session


@pytest_asyncio.fixture
async def test_user(test_db_session):
    """
    Create a test user in the database.
    Following CLAUDE.md: Real database entities, not mocks.
    """
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
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        return user


@pytest_asyncio.fixture
async def test_user_with_2fa(test_db_session):
    """
    Create a test user with 2FA enabled.
    Following CLAUDE.md: Real database entities, not mocks.
    """
    # Mock only external UUID generation - APPROVED external dependency
    with patch(
        "uuid.uuid4", return_value=uuid.UUID("87654321-4321-8765-2109-987654321098")
    ):
        password_hash = auth_service.hash_password("TestPassword123!")
        totp_secret = auth_service.generate_totp_secret()

        user = User(
            id=uuid.UUID("87654321-4321-8765-2109-987654321098"),
            email="testuser2fa@example.com",
            password_hash=password_hash,
            role=UserRole.ADMIN,
            is_active=True,
            totp_secret=totp_secret,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        return user


class TestAuthenticationAPI:
    """Test suite for authentication API endpoints with real database integration."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test API health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "v1"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, app):
        """Test login with invalid credentials."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as ac:
            response = await ac.post(
                "/api/v1/auth/login",
                json={"email": "invalid@example.com", "password": "wrongpassword"},
            )
            assert response.status_code == 401
            data = response.json()
            assert "Invalid credentials" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_valid_credentials_without_2fa_integration(
        self, app, test_user
    ):
        """
        Database-backed integration test for login with valid credentials and no 2FA.

        Following CLAUDE.md guidelines: Never mock internal business logic.
        Tests actual authentication flow with real database user.
        Mock only external dependencies (Redis sessions, time).
        """
        # Mock external Redis operations - APPROVED external dependency
        from unittest.mock import MagicMock

        from src.services.auth_service import auth_service

        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None
        with patch.object(auth_service, "_redis_client", mock_redis):
            # Mock time for consistent token expiration - APPROVED external dependency
            with patch("src.services.auth_service.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(
                    2025, 1, 1, 12, 0, 0, tzinfo=UTC
                )
                mock_datetime.timezone = timezone

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.post(
                        "/api/v1/auth/login",
                        json={
                            "email": "testuser@example.com",
                            "password": "TestPassword123!",
                        },
                    )

                    assert response.status_code == 200
                    data = response.json()

                    # Verify response structure
                    assert "access_token" in data
                    assert "refresh_token" in data
                    assert "user" in data

                    # Verify user data
                    user_data = data["user"]
                    assert user_data["email"] == "testuser@example.com"
                    assert user_data["role"] == "user"
                    assert user_data["is_active"] is True
                    assert user_data["has_2fa"] is False
                    assert "id" in user_data

                    # Verify tokens are valid JWT format
                    access_token = data["access_token"]
                    refresh_token = data["refresh_token"]

                    assert len(access_token.split(".")) == 3  # JWT format
                    assert len(refresh_token.split(".")) == 3  # JWT format

                    # Verify Redis session creation was attempted
                    mock_redis.setex.assert_called()

    @pytest.mark.asyncio
    async def test_login_with_2fa_missing_code_integration(
        self, app, test_user_with_2fa
    ):
        """
        Database-backed integration test for login with 2FA enabled but missing TOTP code.

        Following CLAUDE.md guidelines: Test actual behavior, not mocked responses.
        Tests real authentication flow with database user having 2FA enabled.
        """
        # Mock external Redis operations - APPROVED external dependency
        from unittest.mock import MagicMock

        from src.services.auth_service import auth_service

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
                        "email": "testuser2fa@example.com",
                        "password": "TestPassword123!",
                        # No totp_code provided
                    },
                )

                assert response.status_code == 400
                data = response.json()
                assert "2FA" in data["detail"] or "TOTP" in data["detail"]

                # Should not create session for incomplete 2FA
                mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_login_with_2fa_invalid_code_integration(
        self, app, test_user_with_2fa
    ):
        """
        Database-backed integration test for login with 2FA enabled and invalid TOTP code.

        Following CLAUDE.md guidelines: Test actual behavior, not mocked responses.
        Tests real authentication flow with invalid TOTP verification.
        """
        # Mock external TOTP verification - APPROVED external dependency
        with patch("src.services.auth_service.pyotp.TOTP.verify") as mock_verify:
            mock_verify.return_value = False  # Invalid TOTP code

            # Mock external Redis operations - APPROVED external dependency
            from unittest.mock import MagicMock

            from src.services.auth_service import auth_service

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
                            "email": "testuser2fa@example.com",
                            "password": "TestPassword123!",
                            "totp_code": "123456",  # Invalid code
                        },
                    )

                    assert response.status_code == 401
                    data = response.json()
                    assert "Invalid" in data["detail"] and (
                        "2FA" in data["detail"] or "TOTP" in data["detail"]
                    )

                    # Verify TOTP verification was called with correct parameters
                    mock_verify.assert_called_once_with("123456", valid_window=1)

                    # Should not create session for failed 2FA
                    mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_login_with_2fa_valid_code_integration(self, app, test_user_with_2fa):
        """
        Database-backed integration test for successful login with valid 2FA code.

        Following CLAUDE.md guidelines: Test actual behavior with real database.
        Tests complete authentication flow including 2FA verification.
        """
        # Mock external TOTP verification - APPROVED external dependency
        with patch("src.services.auth_service.pyotp.TOTP.verify") as mock_verify:
            mock_verify.return_value = True  # Valid TOTP code

            # Mock external Redis operations - APPROVED external dependency
            from unittest.mock import MagicMock

            from src.services.auth_service import auth_service

            mock_redis = MagicMock()
            mock_redis.setex.return_value = True
            mock_redis.get.return_value = None
            with patch.object(auth_service, "_redis_client", mock_redis):
                # Mock time for consistent token expiration - APPROVED external dependency
                with patch("src.services.auth_service.datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime(
                        2025, 1, 1, 12, 0, 0, tzinfo=UTC
                    )
                    mock_datetime.timezone = timezone

                    async with AsyncClient(
                        transport=ASGITransport(app=app), base_url="http://test"
                    ) as ac:
                        response = await ac.post(
                            "/api/v1/auth/login",
                            json={
                                "email": "testuser2fa@example.com",
                                "password": "TestPassword123!",
                                "totp_code": "123456",  # Valid code (mocked)
                            },
                        )

                        assert response.status_code == 200
                        data = response.json()

                        # Verify response structure
                        assert "access_token" in data
                        assert "refresh_token" in data
                        assert "user" in data

                        # Verify user data for 2FA user
                        user_data = data["user"]
                        assert user_data["email"] == "testuser2fa@example.com"
                        assert user_data["role"] == "admin"
                        assert user_data["is_active"] is True
                        assert user_data["has_2fa"] is True
                        assert "id" in user_data

                        # Verify TOTP verification was called
                        mock_verify.assert_called_once_with("123456", valid_window=1)

                        # Verify Redis session creation was attempted
                        mock_redis.setex.assert_called()

    @pytest.mark.asyncio
    async def test_logout_without_token(self, app):
        """Test logout without authentication token."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as ac:
            response = await ac.post("/api/v1/auth/logout")
            assert response.status_code == 403  # Forbidden due to missing auth header

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, app):
        """Test token refresh with invalid refresh token."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as ac:
            response = await ac.post(
                "/api/v1/auth/refresh", json={"refresh_token": "invalid_token"}
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_setup_2fa_without_auth(self, app):
        """Test 2FA setup without authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as ac:
            response = await ac.get("/api/v1/auth/setup-2fa")
            assert response.status_code == 403  # Forbidden due to missing auth header

    @pytest.mark.asyncio
    async def test_enable_2fa_without_auth(self, app):
        """Test 2FA enable without authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as ac:
            response = await ac.post(
                "/api/v1/auth/enable-2fa", json={"totp_code": "123456"}
            )
            assert response.status_code == 403  # Forbidden due to missing auth header

    @pytest.mark.asyncio
    async def test_disable_2fa_without_auth(self, app):
        """Test 2FA disable without authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as ac:
            response = await ac.delete("/api/v1/auth/disable-2fa")
            assert response.status_code == 403  # Forbidden due to missing auth header

    @pytest.mark.asyncio
    async def test_logout_with_valid_token_integration(self, app, test_user):
        """
        Test successful logout with valid authentication token.
        Following CLAUDE.md guidelines: Test actual authentication flow.
        """
        # Mock external Redis operations - APPROVED external dependency
        from unittest.mock import MagicMock

        from src.services.auth_service import auth_service

        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None
        with patch.object(auth_service, "_redis_client", mock_redis):
            mock_redis.delete.return_value = True

            # Mock time for consistent token expiration - APPROVED external dependency
            with patch("src.services.auth_service.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(
                    2025, 1, 1, 12, 0, 0, tzinfo=UTC
                )
                mock_datetime.timezone = timezone

                # First, create a valid access token
                access_token = auth_service.create_access_token(
                    user_id=str(test_user.id), user_role=test_user.role.value
                )

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.post(
                        "/api/v1/auth/logout",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["message"] == "Logout successful"

    @pytest.mark.asyncio
    async def test_logout_all_sessions_integration(self, app, test_user):
        """
        Test logout from all sessions with valid authentication token.
        Following CLAUDE.md guidelines: Test actual authentication flow.
        """
        # Mock external Redis operations - APPROVED external dependency
        from unittest.mock import MagicMock

        from src.services.auth_service import auth_service

        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None
        mock_redis.delete.return_value = True
        mock_redis.scan_iter.return_value = [
            f"session:{test_user.id}:token1",
            f"session:{test_user.id}:token2",
        ]
        with patch.object(auth_service, "_redis_client", mock_redis):
            # Mock time for consistent token expiration - APPROVED external dependency
            with patch("src.services.auth_service.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(
                    2025, 1, 1, 12, 0, 0, tzinfo=UTC
                )
                mock_datetime.timezone = timezone

                # Create a valid access token
                access_token = auth_service.create_access_token(
                    user_id=str(test_user.id), user_role=test_user.role.value
                )

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.post(
                        "/api/v1/auth/logout-all",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert (
                        data["message"] == "Logged out from all sessions successfully"
                    )

    @pytest.mark.asyncio
    async def test_refresh_token_valid_integration(self, app, test_user):
        """
        Test token refresh with valid refresh token.
        Following CLAUDE.md guidelines: Test actual authentication flow.
        """
        # Mock external Redis operations - APPROVED external dependency
        from unittest.mock import MagicMock

        from src.services.auth_service import auth_service

        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None
        with patch.object(auth_service, "_redis_client", mock_redis):
            mock_redis.delete.return_value = True

            # Mock time for consistent token expiration - APPROVED external dependency
            with patch("src.services.auth_service.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(
                    2025, 1, 1, 12, 0, 0, tzinfo=UTC
                )
                mock_datetime.timezone = timezone

                # Create a valid refresh token
                refresh_token = auth_service.create_refresh_token(
                    user_id=str(test_user.id)
                )

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.post(
                        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert "access_token" in data
                    assert "refresh_token" in data
                    assert data["token_type"] == "bearer"
                    assert "expires_in" in data

    @pytest.mark.asyncio
    async def test_setup_2fa_with_valid_token_integration(self, app, test_user):
        """
        Test 2FA setup with valid authentication token.
        Following CLAUDE.md guidelines: Test actual authentication flow.
        """
        # Mock external Redis operations - APPROVED external dependency
        from unittest.mock import MagicMock

        from src.services.auth_service import auth_service

        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None
        with patch.object(auth_service, "_redis_client", mock_redis):
            # Mock time for consistent token expiration - APPROVED external dependency
            with patch("src.services.auth_service.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(
                    2025, 1, 1, 12, 0, 0, tzinfo=UTC
                )
                mock_datetime.timezone = timezone

                # Create a valid access token
                access_token = auth_service.create_access_token(
                    user_id=str(test_user.id), user_role=test_user.role.value
                )

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.get(
                        "/api/v1/auth/setup-2fa",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert "secret" in data
                    assert "qr_code_url" in data
                    assert "backup_codes" in data
                    assert len(data["backup_codes"]) == 8
                    assert len(data["secret"]) == 32

    @pytest.mark.asyncio
    async def test_enable_2fa_with_valid_code_integration(self, app, test_user):
        """
        Test 2FA enable with valid TOTP code after setup.
        Following CLAUDE.md guidelines: Test actual authentication flow.
        """
        # Mock external TOTP verification - APPROVED external dependency
        with patch("src.services.auth_service.pyotp.TOTP.verify") as mock_verify:
            mock_verify.return_value = True

            # Mock external Redis operations - APPROVED external dependency
            from unittest.mock import MagicMock

            from src.services.auth_service import auth_service

            mock_redis = MagicMock()
            mock_redis.setex.return_value = True
            mock_redis.get.return_value = "JBSWY3DPEHPK3PXP"  # Mock secret from setup
            mock_redis.delete.return_value = True
            with patch.object(auth_service, "_redis_client", mock_redis):
                # Mock time for consistent token expiration - APPROVED external dependency
                with patch("src.services.auth_service.datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime(
                        2025, 1, 1, 12, 0, 0, tzinfo=UTC
                    )
                    mock_datetime.timezone = timezone

                    # Create a valid access token
                    access_token = auth_service.create_access_token(
                        user_id=str(test_user.id), user_role=test_user.role.value
                    )

                    async with AsyncClient(
                        transport=ASGITransport(app=app), base_url="http://test"
                    ) as ac:
                        response = await ac.post(
                            "/api/v1/auth/enable-2fa",
                            headers={"Authorization": f"Bearer {access_token}"},
                            json={"totp_code": "123456"},
                        )

                        assert response.status_code == 200
                        data = response.json()
                        assert data["message"] == "2FA enabled successfully"

                        # Verify TOTP verification was called
                        mock_verify.assert_called_once_with("123456", valid_window=1)

    @pytest.mark.asyncio
    async def test_disable_2fa_integration(self, app, test_user_with_2fa):
        """
        Test 2FA disable for user with 2FA enabled.
        Following CLAUDE.md guidelines: Test actual authentication flow.
        """
        # Mock external Redis operations - APPROVED external dependency
        from unittest.mock import MagicMock

        from src.services.auth_service import auth_service

        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None
        with patch.object(auth_service, "_redis_client", mock_redis):
            # Mock time for consistent token expiration - APPROVED external dependency
            with patch("src.services.auth_service.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(
                    2025, 1, 1, 12, 0, 0, tzinfo=UTC
                )
                mock_datetime.timezone = timezone

                # Create a valid access token
                access_token = auth_service.create_access_token(
                    user_id=str(test_user_with_2fa.id),
                    user_role=test_user_with_2fa.role.value,
                )

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.delete(
                        "/api/v1/auth/disable-2fa",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["message"] == "2FA disabled successfully"

    @pytest.mark.asyncio
    async def test_get_current_user_integration(self, app, test_user):
        """
        Test get current user information with valid token.
        Following CLAUDE.md guidelines: Test actual authentication flow.
        """
        # Mock external Redis operations - APPROVED external dependency
        from unittest.mock import MagicMock

        from src.services.auth_service import auth_service

        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None
        with patch.object(auth_service, "_redis_client", mock_redis):
            # Mock time for consistent token expiration - APPROVED external dependency
            with patch("src.services.auth_service.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(
                    2025, 1, 1, 12, 0, 0, tzinfo=UTC
                )
                mock_datetime.timezone = timezone

                # Create a valid access token
                access_token = auth_service.create_access_token(
                    user_id=str(test_user.id), user_role=test_user.role.value
                )

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.get(
                        "/api/v1/auth/me",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )

                    assert response.status_code == 200
                    data = response.json()

                    # Verify response structure
                    assert "access_token" in data
                    assert "user" in data
                    assert "permissions" in data

                    # Verify user data
                    user_data = data["user"]
                    assert user_data["email"] == test_user.email
                    assert user_data["role"] == test_user.role.value
                    assert user_data["is_active"] is True
                    assert "id" in user_data

    @pytest.mark.asyncio
    async def test_enable_2fa_invalid_code_integration(self, app, test_user):
        """
        Test 2FA enable with invalid TOTP code.
        Following CLAUDE.md guidelines: Test actual authentication flow.
        """
        # Mock external TOTP verification - APPROVED external dependency
        with patch("src.services.auth_service.pyotp.TOTP.verify") as mock_verify:
            mock_verify.return_value = False  # Invalid code

            # Mock external Redis operations - APPROVED external dependency
            from unittest.mock import MagicMock

            from src.services.auth_service import auth_service

            mock_redis = MagicMock()
            mock_redis.setex.return_value = True
            mock_redis.get.return_value = "JBSWY3DPEHPK3PXP"  # Mock secret from setup
            with patch.object(auth_service, "_redis_client", mock_redis):
                # Mock time for consistent token expiration - APPROVED external dependency
                with patch("src.services.auth_service.datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime(
                        2025, 1, 1, 12, 0, 0, tzinfo=UTC
                    )
                    mock_datetime.timezone = timezone

                    # Create a valid access token
                    access_token = auth_service.create_access_token(
                        user_id=str(test_user.id), user_role=test_user.role.value
                    )

                    async with AsyncClient(
                        transport=ASGITransport(app=app), base_url="http://test"
                    ) as ac:
                        response = await ac.post(
                            "/api/v1/auth/enable-2fa",
                            headers={"Authorization": f"Bearer {access_token}"},
                            json={"totp_code": "invalid"},
                        )

                        assert response.status_code == 400
                        data = response.json()
                        assert "Invalid TOTP code" in data["detail"]

    @pytest.mark.asyncio
    async def test_enable_2fa_expired_setup_integration(self, app, test_user):
        """
        Test 2FA enable with expired setup session.
        Following CLAUDE.md guidelines: Test actual authentication flow.
        """
        # Mock external Redis operations - APPROVED external dependency
        from unittest.mock import MagicMock

        from src.services.auth_service import auth_service

        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None
        with patch.object(
            auth_service, "_redis_client", mock_redis
        ):  # No secret found (expired)
            # Mock time for consistent token expiration - APPROVED external dependency
            with patch("src.services.auth_service.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(
                    2025, 1, 1, 12, 0, 0, tzinfo=UTC
                )
                mock_datetime.timezone = timezone

                # Create a valid access token
                access_token = auth_service.create_access_token(
                    user_id=str(test_user.id), user_role=test_user.role.value
                )

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.post(
                        "/api/v1/auth/enable-2fa",
                        headers={"Authorization": f"Bearer {access_token}"},
                        json={"totp_code": "123456"},
                    )

                    assert response.status_code == 400
                    data = response.json()
                    assert "2FA setup session expired" in data["detail"]


class TestAuthenticationService:
    """Test suite for authentication service functions."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        from src.services.auth_service import auth_service

        password = "SecurePassword123!"
        hashed = auth_service.hash_password(password)

        # Hash should be different from original password
        assert hashed != password
        # Should verify correctly
        assert auth_service.verify_password(password, hashed) is True
        # Wrong password should not verify
        assert auth_service.verify_password("WrongPassword", hashed) is False

    def test_totp_secret_generation(self):
        """Test TOTP secret generation."""
        from src.services.auth_service import auth_service

        secret = auth_service.generate_totp_secret()

        # Secret should be a string
        assert isinstance(secret, str)
        # Secret should be base32 encoded (32 characters)
        assert len(secret) == 32
        # Should be different each time
        secret2 = auth_service.generate_totp_secret()
        assert secret != secret2

    def test_totp_qr_url_generation(self):
        """Test TOTP QR URL generation."""
        from src.services.auth_service import auth_service

        email = "test@example.com"
        secret = "JBSWY3DPEHPK3PXP"

        qr_url = auth_service.generate_totp_qr_url(email, secret)

        # URL should contain the expected components
        assert "otpauth://totp/" in qr_url
        assert secret in qr_url
        assert "IAM%20Dashboard" in qr_url  # URL-encoded space
        # Email is URL encoded as %40 instead of @
        assert "test%40example.com" in qr_url

    @patch(
        "src.services.auth_service.pyotp.TOTP.verify"
    )  # OK: Mocking external library
    def test_totp_verification_with_external_mock(self, mock_verify):
        """
        Test TOTP verification - APPROVED mock of external library.

        This mock is APPROVED per CLAUDE.md as it mocks external dependency (pyotp),
        not internal business logic.
        """
        from src.services.auth_service import auth_service

        secret = "JBSWY3DPEHPK3PXP"
        code = "123456"

        # Test valid code - mocking external library behavior
        mock_verify.return_value = True
        assert auth_service.verify_totp(secret, code) is True

        # Test invalid code - mocking external library behavior
        mock_verify.return_value = False
        assert auth_service.verify_totp(secret, "654321") is False

        # Test business logic validation (empty inputs)
        assert auth_service.verify_totp("", code) is False
        assert auth_service.verify_totp(secret, "") is False
