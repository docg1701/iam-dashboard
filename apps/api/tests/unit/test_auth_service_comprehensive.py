"""
Comprehensive Authentication Service tests to improve coverage.
Following CLAUDE.md guidelines: Never mock internal business logic.
Mock only external dependencies (Redis, time, UUID generation, database connections).
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from jose import jwt

from src.services.auth_service import AuthService, auth_service


class TestAuthServiceCoverage:
    """Test suite to improve auth service coverage."""

    def test_redis_client_property_lazy_initialization(self):
        """Test Redis client lazy initialization."""
        # Create new auth service instance to test lazy loading
        auth_svc = AuthService()
        assert auth_svc._redis_client is None

        # Mock redis.from_url to avoid actual Redis connection
        with patch("src.services.auth_service.redis.from_url") as mock_redis_from_url:
            mock_redis_instance = MagicMock()
            mock_redis_from_url.return_value = mock_redis_instance

            # Access redis_client property to trigger lazy initialization
            redis_client = auth_svc.redis_client

            # Verify Redis client was initialized correctly
            assert redis_client == mock_redis_instance
            assert auth_svc._redis_client == mock_redis_instance
            mock_redis_from_url.assert_called_once_with(
                auth_svc.settings.REDIS_URL,
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True,
            )

    def test_create_access_token_with_custom_expiration(self):
        """Test access token creation with custom expiration delta."""
        # Mock external Redis operations - APPROVED external dependency
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True

        with patch.object(auth_service, "_redis_client", mock_redis):
            # Mock time for consistent token - APPROVED external dependency
            with patch("src.services.auth_service.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(
                    2025, 1, 1, 12, 0, 0, tzinfo=UTC
                )
                mock_datetime.timezone = datetime.timezone

                # Create token with custom expiration
                custom_delta = timedelta(minutes=30)
                token = auth_service.create_access_token(
                    user_id="test-user-id",
                    user_role="admin",
                    expires_delta=custom_delta,
                )

                # Verify token is created
                assert isinstance(token, str)
                assert len(token.split(".")) == 3  # JWT format

                # Decode and verify custom expiration
                payload = jwt.decode(
                    token,
                    auth_service.settings.SECRET_KEY,
                    algorithms=[auth_service.settings.ALGORITHM],
                )

                expected_exp = mock_datetime.now.return_value + custom_delta
                assert payload["exp"] == expected_exp
                assert payload["sub"] == "test-user-id"
                assert payload["role"] == "admin"
                assert payload["type"] == "access"

                # Verify session storage was called
                mock_redis.setex.assert_called()

    def test_create_refresh_token_with_custom_expiration(self):
        """Test refresh token creation with custom expiration delta."""
        # Mock external Redis operations - APPROVED external dependency
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True

        with patch.object(auth_service, "_redis_client", mock_redis):
            # Mock time for consistent token - APPROVED external dependency
            with patch("src.services.auth_service.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(
                    2025, 1, 1, 12, 0, 0, tzinfo=UTC
                )
                mock_datetime.timezone = datetime.timezone

                # Mock UUID generation - APPROVED external dependency
                with patch("src.services.auth_service.uuid.uuid4") as mock_uuid:
                    mock_uuid.return_value = uuid.UUID(
                        "12345678-1234-5678-9012-123456789012"
                    )

                    # Create token with custom expiration
                    custom_delta = timedelta(days=7)
                    token = auth_service.create_refresh_token(
                        user_id="test-user-id", expires_delta=custom_delta
                    )

                    # Verify token is created
                    assert isinstance(token, str)
                    assert len(token.split(".")) == 3  # JWT format

                    # Decode and verify custom expiration
                    payload = jwt.decode(
                        token,
                        auth_service.settings.SECRET_KEY,
                        algorithms=[auth_service.settings.ALGORITHM],
                    )

                    expected_exp = mock_datetime.now.return_value + custom_delta
                    assert payload["exp"] == expected_exp
                    assert payload["sub"] == "test-user-id"
                    assert payload["type"] == "refresh"
                    assert payload["jti"] == str(mock_uuid.return_value)

                    # Verify Redis storage was called with correct TTL
                    expected_ttl = int(
                        expected_exp.timestamp()
                        - mock_datetime.now.return_value.timestamp()
                    )
                    mock_redis.setex.assert_called_with(
                        f"refresh_token:{mock_uuid.return_value}",
                        expected_ttl,
                        "test-user-id",
                    )

    def test_verify_token_with_missing_user_id(self):
        """Test token verification with missing sub claim."""
        # Create token without sub claim
        payload = {
            "role": "user",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
            "type": "access",
        }

        token = jwt.encode(
            payload,
            auth_service.settings.SECRET_KEY,
            algorithm=auth_service.settings.ALGORITHM,
        )

        # Mock Redis to not find blacklisted token
        mock_redis = MagicMock()
        mock_redis.exists.return_value = False

        with patch.object(auth_service, "_redis_client", mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                auth_service.verify_token(token)

            assert exc_info.value.status_code == 401
            assert "Token validation failed" in str(exc_info.value.detail)

    def test_verify_token_with_blacklisted_token(self):
        """Test token verification with blacklisted token."""
        # Create valid token
        payload = {
            "sub": "test-user-id",
            "role": "user",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
            "type": "access",
        }

        token = jwt.encode(
            payload,
            auth_service.settings.SECRET_KEY,
            algorithm=auth_service.settings.ALGORITHM,
        )

        # Mock Redis to find blacklisted token
        mock_redis = MagicMock()
        mock_redis.exists.return_value = True  # Token is blacklisted

        with patch.object(auth_service, "_redis_client", mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                auth_service.verify_token(token)

            assert exc_info.value.status_code == 401
            assert "Token has been revoked" in str(exc_info.value.detail)

    def test_verify_token_with_jwt_error(self):
        """Test token verification with invalid JWT."""
        # Mock Redis
        mock_redis = MagicMock()
        mock_redis.exists.return_value = False

        with patch.object(auth_service, "_redis_client", mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                auth_service.verify_token("invalid.jwt.token")

            assert exc_info.value.status_code == 401
            assert "Token validation failed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_access_token_with_invalid_type(self):
        """Test refresh token with wrong token type."""
        # Create access token instead of refresh token
        payload = {
            "sub": "test-user-id",
            "role": "user",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
            "type": "access",  # Wrong type
            "jti": str(uuid.uuid4()),
        }

        token = jwt.encode(
            payload,
            auth_service.settings.SECRET_KEY,
            algorithm=auth_service.settings.ALGORITHM,
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.refresh_access_token(token)

        assert exc_info.value.status_code == 401
        assert "Invalid token type" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_access_token_with_missing_claims(self):
        """Test refresh token with missing required claims."""
        # Create token missing jti claim
        payload = {
            "sub": "test-user-id",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
            "type": "refresh",
            # Missing jti
        }

        token = jwt.encode(
            payload,
            auth_service.settings.SECRET_KEY,
            algorithm=auth_service.settings.ALGORITHM,
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.refresh_access_token(token)

        assert exc_info.value.status_code == 401
        assert "Invalid refresh token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_access_token_with_invalid_jti(self):
        """Test refresh token with JTI not found in Redis."""
        # Create valid refresh token
        jti = str(uuid.uuid4())
        payload = {
            "sub": "test-user-id",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
            "type": "refresh",
            "jti": jti,
        }

        token = jwt.encode(
            payload,
            auth_service.settings.SECRET_KEY,
            algorithm=auth_service.settings.ALGORITHM,
        )

        # Mock Redis to not find JTI
        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # JTI not found

        with patch.object(auth_service, "_redis_client", mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.refresh_access_token(token)

            assert exc_info.value.status_code == 401
            assert "Refresh token not found or invalid" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_access_token_with_mismatched_user_id(self):
        """Test refresh token with mismatched user ID in Redis."""
        # Create valid refresh token
        jti = str(uuid.uuid4())
        payload = {
            "sub": "test-user-id",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
            "type": "refresh",
            "jti": jti,
        }

        token = jwt.encode(
            payload,
            auth_service.settings.SECRET_KEY,
            algorithm=auth_service.settings.ALGORITHM,
        )

        # Mock Redis to return different user ID
        mock_redis = MagicMock()
        mock_redis.get.return_value = "different-user-id"

        with patch.object(auth_service, "_redis_client", mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.refresh_access_token(token)

            assert exc_info.value.status_code == 401
            assert "Refresh token not found or invalid" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_access_token_with_jwt_error(self):
        """Test refresh token with invalid JWT format."""
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.refresh_access_token("invalid.jwt.token")

        assert exc_info.value.status_code == 401
        assert "Invalid refresh token" in str(exc_info.value.detail)

    def test_blacklist_token_with_valid_token(self):
        """Test blacklisting a valid token."""
        # Create valid token
        exp_time = datetime.now(UTC) + timedelta(hours=1)
        payload = {
            "sub": "test-user-id",
            "role": "user",
            "exp": exp_time,
            "iat": datetime.now(UTC),
            "type": "access",
        }

        token = jwt.encode(
            payload,
            auth_service.settings.SECRET_KEY,
            algorithm=auth_service.settings.ALGORITHM,
        )

        # Mock Redis and time
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True

        with patch.object(auth_service, "_redis_client", mock_redis):
            with patch("src.services.auth_service.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(
                    2025, 1, 1, 12, 0, 0, tzinfo=UTC
                )

                auth_service.blacklist_token(token)

                # Verify token was blacklisted with correct TTL
                expected_ttl = int(
                    exp_time.timestamp() - mock_datetime.now.return_value.timestamp()
                )
                mock_redis.setex.assert_called_with(
                    f"blacklisted_token:{token}", expected_ttl, "blacklisted"
                )

    def test_blacklist_token_with_expired_token(self):
        """Test blacklisting an already expired token."""
        # Create expired token
        exp_time = datetime.now(UTC) - timedelta(hours=1)  # Already expired
        payload = {
            "sub": "test-user-id",
            "role": "user",
            "exp": exp_time,
            "iat": datetime.now(UTC) - timedelta(hours=2),
            "type": "access",
        }

        token = jwt.encode(
            payload,
            auth_service.settings.SECRET_KEY,
            algorithm=auth_service.settings.ALGORITHM,
        )

        # Mock Redis and time
        mock_redis = MagicMock()

        with patch.object(auth_service, "_redis_client", mock_redis):
            with patch("src.services.auth_service.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(
                    2025, 1, 1, 12, 0, 0, tzinfo=UTC
                )

                auth_service.blacklist_token(token)

                # Verify setex was not called for expired token
                mock_redis.setex.assert_not_called()

    def test_blacklist_token_with_invalid_jwt(self):
        """Test blacklisting an invalid JWT token."""
        # Mock Redis
        mock_redis = MagicMock()

        with patch.object(auth_service, "_redis_client", mock_redis):
            # Should not raise exception for invalid token
            auth_service.blacklist_token("invalid.jwt.token")

            # Verify setex was not called
            mock_redis.setex.assert_not_called()

    def test_store_user_session_with_session_limit(self):
        """Test session storage with concurrent session limit enforcement."""
        user_id = "test-user-id"
        token = "new.jwt.token"
        expire_time = datetime.now(UTC) + timedelta(hours=1)

        # Mock Redis with 5 existing sessions (at limit)
        mock_redis = MagicMock()
        existing_sessions = [f"session{i}.token" for i in range(5)]
        mock_redis.smembers.return_value = existing_sessions
        mock_redis.srem.return_value = True
        mock_redis.sadd.return_value = True
        mock_redis.setex.return_value = True
        mock_redis.expire.return_value = True

        with patch.object(auth_service, "_redis_client", mock_redis):
            with patch("src.services.auth_service.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(
                    2025, 1, 1, 12, 0, 0, tzinfo=UTC
                )

                auth_service._store_user_session(user_id, token, expire_time)

                # Verify oldest session was removed
                mock_redis.srem.assert_called_with(
                    f"user_session:{user_id}", existing_sessions[0]
                )

                # Verify oldest token was blacklisted
                mock_redis.setex.assert_any_call(
                    f"blacklisted_token:{existing_sessions[0]}",
                    3600,  # 1 hour TTL
                    "session_limit_exceeded",
                )

                # Verify new session was added
                mock_redis.sadd.assert_called_with(f"user_session:{user_id}", token)

                # Verify session set expiration was updated
                expected_ttl = int(
                    expire_time.timestamp() - mock_datetime.now.return_value.timestamp()
                )
                mock_redis.expire.assert_called_with(
                    f"user_session:{user_id}", expected_ttl
                )

    def test_store_user_session_under_limit(self):
        """Test session storage when under concurrent session limit."""
        user_id = "test-user-id"
        token = "new.jwt.token"
        expire_time = datetime.now(UTC) + timedelta(hours=1)

        # Mock Redis with 3 existing sessions (under limit)
        mock_redis = MagicMock()
        existing_sessions = [f"session{i}.token" for i in range(3)]
        mock_redis.smembers.return_value = existing_sessions
        mock_redis.sadd.return_value = True
        mock_redis.expire.return_value = True

        with patch.object(auth_service, "_redis_client", mock_redis):
            with patch("src.services.auth_service.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(
                    2025, 1, 1, 12, 0, 0, tzinfo=UTC
                )

                auth_service._store_user_session(user_id, token, expire_time)

                # Verify no sessions were removed
                mock_redis.srem.assert_not_called()

                # Verify no tokens were blacklisted
                mock_redis.setex.assert_not_called()

                # Verify new session was added
                mock_redis.sadd.assert_called_with(f"user_session:{user_id}", token)

                # Verify session set expiration was updated
                expected_ttl = int(
                    expire_time.timestamp() - mock_datetime.now.return_value.timestamp()
                )
                mock_redis.expire.assert_called_with(
                    f"user_session:{user_id}", expected_ttl
                )

    def test_logout_user(self):
        """Test user logout functionality."""
        user_id = "test-user-id"
        token = "user.jwt.token"

        # Mock Redis
        mock_redis = MagicMock()
        mock_redis.srem.return_value = True

        with patch.object(auth_service, "_redis_client", mock_redis):
            # Mock the blacklist_token method
            with patch.object(auth_service, "blacklist_token") as mock_blacklist:
                auth_service.logout_user(token, user_id)

                # Verify token was blacklisted
                mock_blacklist.assert_called_once_with(token)

                # Verify session was removed
                mock_redis.srem.assert_called_once_with(
                    f"user_session:{user_id}", token
                )

    def test_logout_all_sessions(self):
        """Test logout from all sessions functionality."""
        user_id = "test-user-id"

        # Mock Redis with multiple sessions
        mock_redis = MagicMock()
        existing_sessions = [
            "session1.token",
            "session2.token",
            b"session3.token",
        ]  # Mix of str and bytes
        mock_redis.smembers.return_value = existing_sessions
        mock_redis.delete.return_value = True

        with patch.object(auth_service, "_redis_client", mock_redis):
            # Mock the blacklist_token method
            with patch.object(auth_service, "blacklist_token") as mock_blacklist:
                auth_service.logout_all_sessions(user_id)

                # Verify all sessions were blacklisted
                assert mock_blacklist.call_count == 3
                mock_blacklist.assert_any_call("session1.token")
                mock_blacklist.assert_any_call("session2.token")
                mock_blacklist.assert_any_call(
                    "session3.token"
                )  # bytes converted to str

                # Verify session set was deleted
                mock_redis.delete.assert_called_once_with(f"user_session:{user_id}")

    @pytest.mark.asyncio
    async def test_get_user_role_from_db_success(self):
        """Test successful user role lookup from database."""
        user_id = "12345678-1234-5678-9012-123456789012"

        # Mock the database session and query result
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_user = MagicMock()
        mock_user.role.value = "admin"
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        # Mock session maker
        mock_session_maker = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session

        with patch(
            "src.services.auth_service.get_session_maker"
        ) as mock_get_session_maker:
            mock_get_session_maker.return_value = mock_session_maker

            role = await auth_service._get_user_role_from_db(user_id)

            assert role == "admin"
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_role_from_db_user_not_found(self):
        """Test user role lookup when user not found."""
        user_id = "12345678-1234-5678-9012-123456789012"

        # Mock the database session and query result
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # User not found
        mock_session.execute.return_value = mock_result

        # Mock session maker
        mock_session_maker = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session

        with patch(
            "src.services.auth_service.get_session_maker"
        ) as mock_get_session_maker:
            mock_get_session_maker.return_value = mock_session_maker

            with pytest.raises(HTTPException) as exc_info:
                await auth_service._get_user_role_from_db(user_id)

            assert exc_info.value.status_code == 401
            assert "User not found or inactive" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_user_role_from_db_invalid_uuid(self):
        """Test user role lookup with invalid UUID format."""
        user_id = "invalid-uuid-format"

        with pytest.raises(HTTPException) as exc_info:
            await auth_service._get_user_role_from_db(user_id)

        assert exc_info.value.status_code == 401
        assert "Invalid user ID" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_user_role_from_db_database_error(self):
        """Test user role lookup with database error."""
        user_id = "12345678-1234-5678-9012-123456789012"

        # Mock session maker to raise exception
        with patch(
            "src.services.auth_service.get_session_maker"
        ) as mock_get_session_maker:
            mock_get_session_maker.side_effect = Exception("Database connection error")

            with pytest.raises(HTTPException) as exc_info:
                await auth_service._get_user_role_from_db(user_id)

            assert exc_info.value.status_code == 500
            assert "Failed to retrieve user information" in str(exc_info.value.detail)
