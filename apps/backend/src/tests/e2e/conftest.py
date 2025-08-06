"""
End-to-end test specific configuration and fixtures.

E2E tests should use real authentication, real database operations, and complete workflows.
Only mock external services that are not part of the system under test.
"""

import pytest

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
    authenticated_sysadmin_headers,
    authenticated_admin_headers,
    auth_headers,
    user_auth_headers,
    client,
)


@pytest.fixture(name="e2e_client")
def e2e_client(client):
    """
    E2E client fixture that uses minimal mocking.
    Only the database session is overridden for test isolation.
    """
    return client


# E2E tests should use real implementations wherever possible
# No auto-mocking fixtures - only mock what's absolutely necessary