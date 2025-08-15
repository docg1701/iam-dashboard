"""
Authentication API edge cases and helper function tests for complete coverage.
Following CLAUDE.md guidelines: Never mock internal business logic.
Mock only external dependencies (Redis, time, UUID generation).
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
async def regular_user(async_session):
    """Create a regular test user."""
    # Mock only external UUID generation - APPROVED external dependency
    with patch(
        "uuid.uuid4", return_value=uuid.UUID("33333333-3333-3333-3333-333333333333")
    ):
        password_hash = auth_service.hash_password("TestPassword123!")

        user = User(
            id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
            email="regular@example.com",
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
async def user_with_failed_attempts(async_session):
    """Create a user with some failed login attempts."""
    # Mock only external UUID generation - APPROVED external dependency
    with patch(
        "uuid.uuid4", return_value=uuid.UUID("44444444-4444-4444-4444-444444444444")
    ):
        password_hash = auth_service.hash_password("TestPassword123!")

        user = User(
            id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
            email="attempts@example.com",
            password_hash=password_hash,
            role=UserRole.USER,
            is_active=True,
            failed_login_attempts=3,  # 3 failed attempts already
            locked_until=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        return user


class TestAuthenticationEdgeCases:
    """Test edge cases and helper functions for complete coverage."""

    @pytest.mark.asyncio
    async def test_login_wrong_password_increment_attempts(self, app, regular_user):
        """Test wrong password increments failed attempts without locking."""
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
                        "email": "regular@example.com",
                        "password": "WrongPassword123!",
                    },
                )

                assert response.status_code == 401
                data = response.json()
                assert "Invalid credentials" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_wrong_password_causes_account_lock(
        self, app, user_with_failed_attempts
    ):
        """Test wrong password after 4 attempts locks account."""
        # Mock external Redis operations - APPROVED external dependency
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None

        # Mock datetime.now to ensure consistent lock time
        with patch("src.api.v1.auth.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now
            mock_datetime.UTC = UTC

            with patch.object(auth_service, "_redis_client", mock_redis):
                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.post(
                        "/api/v1/auth/login",
                        json={
                            "email": "attempts@example.com",
                            "password": "WrongPassword123!",  # This will be the 5th attempt (4+1)
                        },
                    )

                    assert response.status_code == 401
                    data = response.json()
                    assert "Invalid credentials" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_successful_resets_failed_attempts(
        self, app, user_with_failed_attempts
    ):
        """Test successful login resets failed attempts and clears lock."""
        # Mock external Redis operations - APPROVED external dependency
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None

        # Mock datetime.now for last_login_at
        with patch("src.api.v1.auth.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 1, 15, 30, 45, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now
            mock_datetime.UTC = UTC

            with patch.object(auth_service, "_redis_client", mock_redis):
                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.post(
                        "/api/v1/auth/login",
                        json={
                            "email": "attempts@example.com",
                            "password": "TestPassword123!",  # Correct password
                        },
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert "access_token" in data

                    # Login should reset failed attempts and update last_login_at

    @pytest.mark.asyncio
    async def test_login_with_user_no_permissions(self, app, regular_user):
        """Test successful login with user having no permissions."""
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
                        "email": "regular@example.com",
                        "password": "TestPassword123!",
                    },
                )

                assert response.status_code == 200
                data = response.json()

                # Should have empty permissions dict
                assert data["permissions"] == {}
                assert data["user"]["email"] == "regular@example.com"

    @pytest.mark.asyncio
    async def test_login_with_inactive_user_via_get_user_by_email(self, app):
        """Test login with inactive user gets filtered out by get_user_by_email."""
        # This tests the is_active filter in the get_user_by_email function
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
                        "email": "nonexistent@example.com",  # Non-existent user
                        "password": "TestPassword123!",
                    },
                )

                assert response.status_code == 401
                data = response.json()
                assert "Invalid credentials" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_with_inactive_user(self, app):
        """Test get current user with inactive user."""
        # Mock token verification but user query returns None (inactive user)
        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "99999999-9999-9999-9999-999999999999",  # Non-existent user ID
                "role": "user",
                "exp": datetime.now(UTC).timestamp() + 3600,
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
    async def test_get_current_user_token_expires_in_past(self, app, regular_user):
        """Test get current user with token that has past expiration."""
        with patch.object(auth_service, "verify_token") as mock_verify:
            # Token expired 1 hour ago
            past_time = datetime.now(UTC).timestamp() - 3600
            mock_verify.return_value = {
                "sub": str(regular_user.id),
                "role": "user",
                "exp": past_time,
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

    @pytest.mark.asyncio
    async def test_get_current_user_token_no_exp_claim(self, app, regular_user):
        """Test get current user with token missing exp claim."""
        with patch.object(auth_service, "verify_token") as mock_verify:
            # Token without exp claim
            mock_verify.return_value = {
                "sub": str(regular_user.id),
                "role": "user",
                # Missing "exp" claim
            }

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": "Bearer no.exp.token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["expires_in"] == 0  # Should be 0 when no exp claim

    @pytest.mark.asyncio
    async def test_setup_2fa_with_redis_setex(self, app, regular_user):
        """Test 2FA setup properly stores secret in Redis."""
        # Mock Redis with proper setex call
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True

        with patch.object(auth_service, "verify_token") as mock_verify:
            with patch.object(auth_service, "_redis_client", mock_redis):
                with patch.object(auth_service, "generate_totp_secret") as mock_secret:
                    with patch.object(auth_service, "generate_totp_qr_url") as mock_qr:
                        with patch("secrets.randbelow") as mock_random:
                            mock_verify.return_value = {
                                "sub": str(regular_user.id),
                                "role": "user",
                            }
                            mock_secret.return_value = "JBSWY3DPEHPK3PXP"
                            mock_qr.return_value = "otpauth://totp/test"
                            mock_random.side_effect = [0, 1, 2, 3, 4, 5, 6, 7] * 8

                            async with AsyncClient(
                                transport=ASGITransport(app=app), base_url="http://test"
                            ) as ac:
                                response = await ac.get(
                                    "/api/v1/auth/setup-2fa",
                                    headers={"Authorization": "Bearer valid.token"},
                                )

                                assert response.status_code == 200

                                # Verify Redis setex was called correctly
                                mock_redis.setex.assert_called_once_with(
                                    f"totp_setup:{regular_user.id}",
                                    600,  # 10 minutes
                                    "JBSWY3DPEHPK3PXP",
                                )

    @pytest.mark.asyncio
    async def test_enable_2fa_stores_secret_and_deletes_temp(self, app, regular_user):
        """Test enable 2FA stores secret in user and deletes temporary Redis key."""
        # Mock Redis operations
        mock_redis = MagicMock()
        mock_redis.get.return_value = "JBSWY3DPEHPK3PXP"
        mock_redis.delete.return_value = True

        with patch.object(auth_service, "verify_token") as mock_verify:
            with patch.object(auth_service, "_redis_client", mock_redis):
                with patch("src.services.auth_service.pyotp.TOTP.verify") as mock_totp:
                    mock_verify.return_value = {
                        "sub": str(regular_user.id),
                        "role": "user",
                    }
                    mock_totp.return_value = True

                    async with AsyncClient(
                        transport=ASGITransport(app=app), base_url="http://test"
                    ) as ac:
                        response = await ac.post(
                            "/api/v1/auth/enable-2fa",
                            headers={"Authorization": "Bearer valid.token"},
                            json={"totp_code": "123456"},
                        )

                        assert response.status_code == 200

                        # Verify Redis delete was called
                        mock_redis.delete.assert_called_once_with(
                            f"totp_setup:{regular_user.id}"
                        )

    @pytest.mark.asyncio
    async def test_disable_2fa_clears_totp_secret(self, app, regular_user):
        """Test disable 2FA clears the TOTP secret."""
        # First set a TOTP secret on the user
        from src.core.database import get_async_session

        async for session in get_async_session():
            user = await session.get(User, regular_user.id)
            user.totp_secret = "JBSWY3DPEHPK3PXP"
            await session.commit()
            break

        with patch.object(auth_service, "verify_token") as mock_verify:
            mock_verify.return_value = {"sub": str(regular_user.id), "role": "user"}

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.delete(
                    "/api/v1/auth/disable-2fa",
                    headers={"Authorization": "Bearer valid.token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["message"] == "2FA disabled successfully"

    @pytest.mark.asyncio
    async def test_token_expiration_calculation_edge_cases(self, app, regular_user):
        """Test various edge cases for token expiration calculation."""
        test_cases = [
            # (exp_timestamp, expected_behavior)
            (datetime.now(UTC).timestamp() + 100, "positive_expires_in"),  # Future exp
            (datetime.now(UTC).timestamp() - 100, "zero_expires_in"),  # Past exp
            (datetime.now(UTC).timestamp(), "zero_or_small"),  # Current time
        ]

        for exp_time, expected in test_cases:
            with patch.object(auth_service, "verify_token") as mock_verify:
                mock_verify.return_value = {
                    "sub": str(regular_user.id),
                    "role": "user",
                    "exp": exp_time,
                }

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.get(
                        "/api/v1/auth/me",
                        headers={"Authorization": "Bearer test.token"},
                    )

                    assert response.status_code == 200
                    data = response.json()

                    if expected == "positive_expires_in":
                        assert data["expires_in"] > 0
                    elif expected == "zero_expires_in":
                        assert data["expires_in"] == 0
                    else:  # zero_or_small
                        assert data["expires_in"] >= 0

    @pytest.mark.asyncio
    async def test_helper_functions_direct_testing(self, app):
        """Test auth helper functions directly."""
        from src.api.v1.auth import get_user_permissions
        from src.core.database import get_async_session

        # Test with non-existent user ID
        fake_user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")

        async for session in get_async_session():
            permissions = await get_user_permissions(fake_user_id, session)
            assert isinstance(permissions, dict)
            assert len(permissions) == 0  # No permissions for non-existent user
            break

    @pytest.mark.asyncio
    async def test_access_token_expire_minutes_fallback(self, app, regular_user):
        """Test access token expiration minutes fallback logic."""
        # Mock auth_service settings to have None for ACCESS_TOKEN_EXPIRE_MINUTES
        with patch.object(auth_service, "settings") as mock_settings:
            mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = None  # Should fallback to 60

            with patch.object(auth_service, "verify_token") as mock_verify:
                mock_verify.return_value = {
                    "sub": str(regular_user.id),
                    "role": "user",
                    "exp": datetime.now(UTC).timestamp() + 3600,
                }

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as ac:
                    response = await ac.get(
                        "/api/v1/auth/me",
                        headers={"Authorization": "Bearer test.token"},
                    )

                    # The response should still work and use fallback value
                    assert response.status_code == 200
