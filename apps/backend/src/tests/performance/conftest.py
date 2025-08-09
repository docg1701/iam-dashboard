"""
Performance test specific configuration and fixtures.

Performance tests should use real implementations to measure actual performance
but may use mocked external services to ensure consistent test conditions.
"""

from unittest.mock import MagicMock, patch

import pytest

# Import the main fixtures from parent conftest


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


@pytest.fixture
def mock_redis() -> MagicMock:
    """Create a fast mock Redis client for performance testing."""
    from unittest.mock import AsyncMock

    redis_mock = MagicMock()
    redis_mock.get = AsyncMock(return_value=None)  # Default to cache miss
    redis_mock.setex = AsyncMock()
    redis_mock.delete = AsyncMock()
    redis_mock.keys = AsyncMock(return_value=[])
    redis_mock.close = AsyncMock()
    return redis_mock


@pytest.fixture
def fast_permission_service(test_session, mock_redis):
    """Create PermissionService optimized for performance testing."""
    from src.services.permission_service import PermissionService

    service = PermissionService(session=test_session)
    service.redis_client = mock_redis
    service._is_testing = False  # Enable Redis operations for performance testing
    return service


@pytest.fixture
async def authenticated_user(test_session):
    """Create an authenticated test user."""
    from src.models.user import UserRole
    from src.tests.factories import create_test_user

    user = create_test_user(
        email="performance.authenticated@example.com", role=UserRole.ADMIN, is_active=True
    )
    test_session.add(user)
    test_session.commit()
    return user


@pytest.fixture
def authenticated_headers(authenticated_user):
    """Create authentication headers for API testing."""
    # Mock JWT token for performance testing
    mock_token = "mock.jwt.token.for.performance.testing"
    return {"Authorization": f"Bearer {mock_token}", "Content-Type": "application/json"}


@pytest.fixture
def performance_metrics_collector():
    """Performance metrics collection fixture."""
    import time
    from typing import Any

    class PerformanceMetricsCollector:
        def __init__(self):
            self.metrics = {}
            self.test_results = []

        def record_metric(self, test_name: str, metric_name: str, value: float, unit: str):
            """Record a performance metric."""
            if test_name not in self.metrics:
                self.metrics[test_name] = {}
            self.metrics[test_name][metric_name] = {"value": value, "unit": unit}

        def record_test_result(
            self, test_name: str, passed: bool, duration_s: float, details: dict[str, Any]
        ):
            """Record a test result."""
            self.test_results.append(
                {
                    "test_name": test_name,
                    "passed": passed,
                    "duration_s": duration_s,
                    "details": details,
                    "timestamp": time.time(),
                }
            )

        def get_summary_report(self) -> dict[str, Any]:
            """Generate summary performance report."""
            passed_tests = [r for r in self.test_results if r["passed"]]
            failed_tests = [r for r in self.test_results if not r["passed"]]

            return {
                "total_tests": len(self.test_results),
                "passed_tests": len(passed_tests),
                "failed_tests": len(failed_tests),
                "success_rate": len(passed_tests) / len(self.test_results)
                if self.test_results
                else 0,
                "total_duration_s": sum(r["duration_s"] for r in self.test_results),
                "avg_test_duration_s": sum(r["duration_s"] for r in self.test_results)
                / len(self.test_results)
                if self.test_results
                else 0,
                "metrics": self.metrics,
                "failed_test_details": list(failed_tests),
            }

    return PerformanceMetricsCollector()
