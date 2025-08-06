"""
Integration test specific configuration and fixtures.

Integration tests should use real database sessions, real services, and real permission logic.
Only mock external systems (APIs, SMTP, file systems) but test real internal integrations.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

# Import the main fixtures from parent conftest
from src.tests.conftest import (
    test_engine,
    test_session,
    test_user,
    test_sysadmin,
    test_regular_user,
    admin_auth_token,
    sysadmin_auth_token,
    user_auth_token,
    client,
)


@pytest.fixture(name="mock_external_apis", autouse=True)
def mock_external_apis():
    """Mock only external API calls for integration tests."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        # Mock external service responses
        mock_instance.get = AsyncMock()
        mock_instance.post = AsyncMock()
        yield mock_instance


@pytest.fixture(name="mock_smtp_only", autouse=True)
def mock_smtp_only():
    """Mock only SMTP operations for integration tests."""
    with patch("smtplib.SMTP") as mock_smtp_class:
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance
        mock_smtp_instance.send_message = MagicMock(return_value=True)
        yield mock_smtp_instance


@pytest.fixture(name="real_redis_or_mock")
def real_redis_or_mock():
    """
    Try to use real Redis for integration tests, fall back to mock if unavailable.
    Integration tests should ideally use real Redis when available.
    """
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        client.ping()
        yield client
    except (redis.ConnectionError, ImportError):
        # Fall back to mock if Redis is not available
        from src.tests.conftest import mock_redis_client
        yield mock_redis_client()