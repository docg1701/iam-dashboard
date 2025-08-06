"""
Performance test specific configuration and fixtures.

Performance tests should use real implementations to measure actual performance
but may use mocked external services to ensure consistent test conditions.
"""

import pytest
from unittest.mock import patch, MagicMock

# Import the main fixtures from parent conftest
from src.tests.conftest import (
    test_engine,
    test_session,
    test_user,
    test_sysadmin,
    test_regular_user,
    client,
)


@pytest.fixture(name="performance_session")
def performance_session(test_session):
    """Performance test session with optimized settings."""
    return test_session


@pytest.fixture(name="mock_slow_external_services", autouse=True)
def mock_slow_external_services():
    """Mock external services that might introduce timing variability."""
    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__.return_value = MagicMock()
        yield mock_smtp


@pytest.fixture(name="performance_markers")
def performance_markers():
    """Markers for performance test classification."""
    return {
        "benchmark": "Benchmark test for performance measurement",
        "load": "Load test for stress testing",
        "memory": "Memory usage test",
    }