"""
Unit test specific configuration and fixtures.

Unit tests should mock all external dependencies (Redis, SMTP, file I/O, time, random)
but test real business logic and internal service behavior.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
from uuid import UUID, uuid4

# Import the main fixtures from parent conftest
from src.tests.conftest import (
    mock_redis_client,
    mock_email_service,
    mock_time,
    mock_uuid,
    mock_audit_logger,
    test_engine,
    test_session,
)


@pytest.fixture(name="mock_external_http", autouse=True)
def mock_external_http():
    """Mock external HTTP calls for unit tests."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.get = AsyncMock()
        mock_instance.post = AsyncMock()
        mock_instance.put = AsyncMock()
        mock_instance.delete = AsyncMock()
        yield mock_instance


@pytest.fixture(name="mock_file_operations", autouse=True)
def mock_file_operations():
    """Mock file system operations for unit tests."""
    with patch("builtins.open") as mock_open, \
         patch("os.path.exists") as mock_exists, \
         patch("os.makedirs") as mock_makedirs:
        
        mock_exists.return_value = True
        yield {
            "open": mock_open,
            "exists": mock_exists,
            "makedirs": mock_makedirs,
        }


@pytest.fixture(name="mock_smtp", autouse=True)
def mock_smtp():
    """Mock SMTP operations for unit tests."""
    with patch("smtplib.SMTP") as mock_smtp_class:
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance
        yield mock_smtp_instance