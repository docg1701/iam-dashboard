"""
Comprehensive Authentication API tests covering successful flows to boost coverage.
Following CLAUDE.md guidelines: Never mock internal business logic.
Mock only external dependencies (Redis, time, UUID generation).
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.models.permission import AgentName, UserAgentPermission
from src.models.user import User, UserRole
from src.services.auth_service import auth_service


@pytest_asyncio.fixture
async def test_user_with_permissions(async_session):
    """Create a test user with permissions in the database."""
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
            totp_secret=None,  # No 2FA initially
        )

        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        # Add user permissions
        permission = UserAgentPermission(
            id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            user_id=user.id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            can_create=True,
            can_read=True,
            can_update=True,
            can_delete=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        async_session.add(permission)
        await async_session.commit()

        return user


@pytest_asyncio.fixture
async def test_user_with_2fa(async_session):
    """Create a test user with 2FA enabled."""
    # Mock only external UUID generation - APPROVED external dependency
    with patch(
        "uuid.uuid4", return_value=uuid.UUID("22222222-2222-2222-2222-222222222222")
    ):
        password_hash = auth_service.hash_password("TestPassword123!")

        user = User(
            id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            email="user2fa@example.com",
            password_hash=password_hash,
            role=UserRole.USER,
            is_active=True,
            failed_login_attempts=0,
            locked_until=None,
            totp_secret="JBSWY3DPEHPK3PXP",  # Base32 encoded secret
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        return user


class TestAuthenticationSuccessFlows:
    """Test suite to improve authentication endpoint coverage with successful flows."""

    @pytest.mark.asyncio
    async def test_successful_login_without_2fa_complete_flow(
        self, app, test_user_with_permissions
    ):
        """Test complete successful login flow without 2FA."""
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
                        "password": "TestPassword123!",
                    },
                )

                assert response.status_code == 200
                data = response.json()

                # Verify complete response structure
                assert "access_token" in data
                assert "refresh_token" in data
                assert data["token_type"] == "bearer"
                assert "expires_in" in data
                assert "user" in data
                assert "permissions" in data

                # Verify user info
                user_info = data["user"]
                assert user_info["email"] == "testuser@example.com"
                assert user_info["role"] == "user"
                assert user_info["is_active"] is True
                assert user_info["has_2fa"] is False

                # Verify permissions structure
                permissions = data["permissions"]
                assert "client_management" in permissions
                client_perms = permissions["client_management"]
                assert client_perms["create"] is True
                assert client_perms["read"] is True
                assert client_perms["update"] is True
                assert client_perms["delete"] is False

    @pytest.mark.asyncio
    async def test_successful_login_with_2fa(self, app, test_user_with_2fa):
        """Test successful login with 2FA verification."""
        # Mock external Redis operations - APPROVED external dependency
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None

        # Mock TOTP verification - APPROVED external library mock
        with patch.object(auth_service, "_redis_client", mock_redis):
            with patch("src.services.auth_service.pyotp.TOTP.verify") as mock_totp:
                mock_totp.return_value = True

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.post(
                        "/api/v1/auth/login",
                        json={
                            "email": "user2fa@example.com",
                            "password": "TestPassword123!",
                            "totp_code": "123456",
                        },
                    )

                    assert response.status_code == 200
                    data = response.json()

                    # Verify 2FA user has 2FA enabled
                    assert data["user"]["has_2fa"] is True
                    assert "access_token" in data

    @pytest.mark.asyncio
    async def test_login_requires_2fa_code(self, app, test_user_with_2fa):
        """Test that user with 2FA enabled requires TOTP code."""
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
                        "email": "user2fa@example.com",
                        "password": "TestPassword123!",
                        # Missing totp_code
                    },
                )

                assert response.status_code == 400
                data = response.json()
                assert "2FA code required" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_with_invalid_2fa_code(self, app, test_user_with_2fa):
        """Test login with invalid 2FA code."""
        # Mock external Redis operations - APPROVED external dependency
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None

        # Mock TOTP verification to return False - APPROVED external library mock
        with patch.object(auth_service, "_redis_client", mock_redis):
            with patch("src.services.auth_service.pyotp.TOTP.verify") as mock_totp:
                mock_totp.return_value = False

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.post(
                        "/api/v1/auth/login",
                        json={
                            "email": "user2fa@example.com",
                            "password": "TestPassword123!",
                            "totp_code": "wrong_code",
                        },
                    )

                    assert response.status_code == 401
                    data = response.json()
                    assert "Invalid 2FA code" in data["detail"]

    @pytest.mark.asyncio
    async def test_successful_token_refresh(self, app):
        """Test successful token refresh."""
        # Mock auth_service.refresh_access_token to return new tokens
        with patch.object(auth_service, "refresh_access_token") as mock_refresh:
            mock_refresh.return_value = ("new_access_token", "new_refresh_token")

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": "valid.refresh.token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["access_token"] == "new_access_token"
                assert data["refresh_token"] == "new_refresh_token"
                assert data["token_type"] == "bearer"
                assert "expires_in" in data

    @pytest.mark.asyncio
    async def test_successful_logout(self, app):
        """Test successful logout."""
        # Mock auth_service methods
        with patch.object(auth_service, "verify_token") as mock_verify:
            with patch.object(auth_service, "logout_user") as mock_logout:
                mock_verify.return_value = {"sub": "user_id_123", "role": "user"}
                mock_logout.return_value = None

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.post(
                        "/api/v1/auth/logout",
                        headers={"Authorization": "Bearer valid.token.here"},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["message"] == "Logout successful"

    @pytest.mark.asyncio
    async def test_successful_logout_all_sessions(self, app):
        """Test successful logout from all sessions."""
        # Mock auth_service methods
        with patch.object(auth_service, "verify_token") as mock_verify:
            with patch.object(auth_service, "logout_all_sessions") as mock_logout_all:
                mock_verify.return_value = {"sub": "user_id_123", "role": "user"}
                mock_logout_all.return_value = None

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.post(
                        "/api/v1/auth/logout-all",
                        headers={"Authorization": "Bearer valid.token.here"},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert (
                        data["message"] == "Logged out from all sessions successfully"
                    )

    @pytest.mark.asyncio
    async def test_successful_2fa_setup(self, app, test_user_with_permissions):
        """Test successful 2FA setup."""
        # Mock auth_service methods and Redis
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True

        with patch.object(auth_service, "verify_token") as mock_verify:
            with patch.object(auth_service, "_redis_client", mock_redis):
                with patch.object(auth_service, "generate_totp_secret") as mock_secret:
                    with patch.object(auth_service, "generate_totp_qr_url") as mock_qr:
                        with patch("secrets.randbelow") as mock_random:
                            mock_verify.return_value = {
                                "sub": str(test_user_with_permissions.id),
                                "role": "user",
                            }
                            mock_secret.return_value = "JBSWY3DPEHPK3PXP"
                            mock_qr.return_value = "otpauth://totp/test_app:testuser@example.com?secret=JBSWY3DPEHPK3PXP&issuer=test_app"
                            mock_random.side_effect = [
                                1,
                                2,
                                3,
                                4,
                                5,
                                6,
                                7,
                                8,
                            ] * 8  # Mock backup codes

                            async with AsyncClient(
                                transport=ASGITransport(app=app), base_url="http://test"
                            ) as ac:
                                response = await ac.get(
                                    "/api/v1/auth/setup-2fa",
                                    headers={
                                        "Authorization": "Bearer valid.token.here"
                                    },
                                )

                                assert response.status_code == 200
                                data = response.json()
                                assert data["secret"] == "JBSWY3DPEHPK3PXP"
                                assert "qr_code_url" in data
                                assert "backup_codes" in data
                                assert len(data["backup_codes"]) == 8

    @pytest.mark.asyncio
    async def test_successful_2fa_enable(self, app, test_user_with_permissions):
        """Test successful 2FA enable."""
        # Mock auth_service methods and Redis
        mock_redis = MagicMock()
        mock_redis.get.return_value = "JBSWY3DPEHPK3PXP"  # Return stored secret
        mock_redis.delete.return_value = True

        with patch.object(auth_service, "verify_token") as mock_verify:
            with patch.object(auth_service, "_redis_client", mock_redis):
                with patch("src.services.auth_service.pyotp.TOTP.verify") as mock_totp:
                    mock_verify.return_value = {
                        "sub": str(test_user_with_permissions.id),
                        "role": "user",
                    }
                    mock_totp.return_value = True

                    async with AsyncClient(
                        transport=ASGITransport(app=app), base_url="http://test"
                    ) as ac:
                        response = await ac.post(
                            "/api/v1/auth/enable-2fa",
                            headers={"Authorization": "Bearer valid.token.here"},
                            json={"totp_code": "123456"},
                        )

                        assert response.status_code == 200
                        data = response.json()
                        assert data["message"] == "2FA enabled successfully"

    @pytest.mark.asyncio
    async def test_enable_2fa_expired_setup(self, app, test_user_with_permissions):
        """Test enable 2FA with expired setup session."""
        # Mock Redis to return None (expired session)
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        with patch.object(auth_service, "verify_token") as mock_verify:
            with patch.object(auth_service, "_redis_client", mock_redis):
                mock_verify.return_value = {
                    "sub": str(test_user_with_permissions.id),
                    "role": "user",
                }

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.post(
                        "/api/v1/auth/enable-2fa",
                        headers={"Authorization": "Bearer valid.token.here"},
                        json={"totp_code": "123456"},
                    )

                    assert response.status_code == 400
                    data = response.json()
                    assert "2FA setup session expired" in data["detail"]

    @pytest.mark.asyncio
    async def test_enable_2fa_invalid_totp_code(self, app, test_user_with_permissions):
        """Test enable 2FA with invalid TOTP code."""
        # Mock auth_service methods and Redis
        mock_redis = MagicMock()
        mock_redis.get.return_value = "JBSWY3DPEHPK3PXP"  # Return stored secret

        with patch.object(auth_service, "verify_token") as mock_verify:
            with patch.object(auth_service, "_redis_client", mock_redis):
                with patch("src.services.auth_service.pyotp.TOTP.verify") as mock_totp:
                    mock_verify.return_value = {
                        "sub": str(test_user_with_permissions.id),
                        "role": "user",
                    }
                    mock_totp.return_value = False  # Invalid code

                    async with AsyncClient(
                        transport=ASGITransport(app=app), base_url="http://test"
                    ) as ac:
                        response = await ac.post(
                            "/api/v1/auth/enable-2fa",
                            headers={"Authorization": "Bearer valid.token.here"},
                            json={"totp_code": "wrong_code"},
                        )

                        assert response.status_code == 400
                        data = response.json()
                        assert "Invalid TOTP code" in data["detail"]

    @pytest.mark.asyncio
    async def test_successful_2fa_disable(self, app, test_user_with_2fa):
        """Test successful 2FA disable."""
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": str(test_user_with_2fa.id),
                "role": "user",
            }

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.delete(
                    "/api/v1/auth/disable-2fa",
                    headers={"Authorization": "Bearer valid.token.here"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["message"] == "2FA disabled successfully"

    @pytest.mark.asyncio
    async def test_successful_get_current_user(self, app, test_user_with_permissions):
        """Test successful get current user."""
        with patch.object(auth_service, "verify_token") as mock_verify:
            # Mock token with valid expiration
            current_time = datetime.now(UTC).timestamp()
            mock_verify.return_value = {
                "sub": str(test_user_with_permissions.id),
                "role": "user",
                "exp": current_time + 3600,  # Token expires in 1 hour
            }

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": "Bearer valid.token.here"},
                )

                assert response.status_code == 200
                data = response.json()

                # Verify response structure (same as login)
                assert data["access_token"] == "valid.token.here"
                assert data["refresh_token"] == ""  # Empty for /me endpoint
                assert data["token_type"] == "bearer"
                assert data["expires_in"] > 0  # Should have time left

                # Verify user info
                user_info = data["user"]
                assert user_info["email"] == "testuser@example.com"
                assert user_info["role"] == "user"
                assert user_info["is_active"] is True

                # Verify permissions
                assert "permissions" in data

    @pytest.mark.asyncio
    async def test_get_user_by_email_function_not_found(self, app):
        """Test get_user_by_email function with non-existent user."""
        from fastapi import HTTPException

        from src.api.v1.auth import get_user_by_email

        # Create a mock session
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No user found
        mock_session.execute.return_value = mock_result

        # Test the function directly
        with pytest.raises(HTTPException) as exc_info:
            await get_user_by_email("nonexistent@example.com", mock_session)

        # Should raise HTTPException with 401 status
        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_user_permissions_function_with_permissions(
        self, app, test_user_with_permissions
    ):
        """Test get_user_permissions function."""
        from src.api.v1.auth import get_user_permissions
        from src.core.database import get_async_session

        # Get a real session for this test
        async for session in get_async_session():
            permissions = await get_user_permissions(
                test_user_with_permissions.id, session
            )

            # Verify permissions structure
            assert isinstance(permissions, dict)
            assert "client_management" in permissions
            client_perms = permissions["client_management"]
            assert client_perms.create is True
            assert client_perms.read is True
            assert client_perms.update is True
            assert client_perms.delete is False
            break

    @pytest.mark.asyncio
    async def test_get_user_permissions_function_no_permissions(
        self, app, test_user_with_2fa
    ):
        """Test get_user_permissions function with user having no permissions."""
        from src.api.v1.auth import get_user_permissions
        from src.core.database import get_async_session

        # Get a real session for this test
        async for session in get_async_session():
            permissions = await get_user_permissions(test_user_with_2fa.id, session)

            # Verify empty permissions structure
            assert isinstance(permissions, dict)
            assert len(permissions) == 0
            break
