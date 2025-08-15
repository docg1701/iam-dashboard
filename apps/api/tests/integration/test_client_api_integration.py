"""
Client API integration tests with real database integration.

Following CLAUDE.md guidelines: Never mock internal business logic.
Mock only external dependencies (Redis, time, UUID generation, external APIs).
Tests full client management workflow with authentication and permissions.
"""

import uuid
from datetime import UTC, date, datetime
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlmodel import delete, select

from src.main import app
from src.models.client import Client
from src.models.permission import AgentName, UserAgentPermission
from src.models.user import User, UserRole
from src.services.auth_service import auth_service
from tests.factories.client_factory import ClientFactory


@pytest_asyncio.fixture
async def real_db_session(async_session):
    """
    Create a real database session for integration tests.
    Following CLAUDE.md: Use real database, never mock internal business logic.
    Uses the async_session fixture from conftest.py for proper async handling.
    """
    # Define test user IDs for cleanup
    test_user_with_perms_id = uuid.UUID("12345678-1234-5678-9012-123456789012")
    test_user_no_perms_id = uuid.UUID("87654321-4321-8765-4321-876543219876")
    
    # Clean up any existing test data
    await async_session.execute(delete(Client).where(Client.name.like("%Test%")))
    await async_session.execute(delete(User).where(User.email.like("%test%")))
    await async_session.execute(
        delete(UserAgentPermission).where(
            UserAgentPermission.user_id.in_([test_user_with_perms_id, test_user_no_perms_id])
        )
    )
    await async_session.commit()
    
    yield async_session
    
    # Clean up after test
    await async_session.execute(delete(Client).where(Client.name.like("%Test%")))
    await async_session.execute(delete(User).where(User.email.like("%test%")))
    await async_session.execute(
        delete(UserAgentPermission).where(
            UserAgentPermission.user_id.in_([test_user_with_perms_id, test_user_no_perms_id])
        )
    )
    await async_session.commit()


@pytest_asyncio.fixture
async def test_user_with_permissions(real_db_session):
    """Create test user with client_management permissions."""
    user_id = uuid.UUID("12345678-1234-5678-9012-123456789012")
    user_email = "testuser@example.com"
    password = "TestPassword123!"

    # Create test user
    password_hash = auth_service.hash_password(password)
    test_user = User(
        id=user_id,
        email=user_email,
        password_hash=password_hash,
        role=UserRole.USER,
        is_active=True,
        totp_secret=None,
        failed_login_attempts=0,
        locked_until=None,
        last_login_at=None,
    )

    real_db_session.add(test_user)

    # Create client_management permissions
    permission = UserAgentPermission(
        user_id=user_id,
        agent_name=AgentName.CLIENT_MANAGEMENT,
        can_create=True,
        can_read=True,
        can_update=True,
        can_delete=True,
        is_active=True,
        granted_by=user_id,  # User grants permission to themselves for testing
        valid_from=datetime.now(UTC).replace(tzinfo=None),
        valid_until=datetime(2030, 12, 31),
    )

    real_db_session.add(permission)
    await real_db_session.commit()
    await real_db_session.refresh(test_user)
    await real_db_session.refresh(permission)

    return {
        "user_id": str(user_id),
        "email": user_email,
        "password": password,
        "user": test_user,
        "permission": permission,
    }


@pytest_asyncio.fixture
async def test_user_no_permissions(real_db_session):
    """Create test user without client_management permissions."""
    user_id = uuid.UUID("87654321-4321-8765-4321-876543219876")
    user_email = "nopermuser@example.com"
    password = "TestPassword123!"

    # Create test user without permissions
    password_hash = auth_service.hash_password(password)
    test_user = User(
        id=user_id,
        email=user_email,
        password_hash=password_hash,
        role=UserRole.USER,
        is_active=True,
    )

    real_db_session.add(test_user)
    await real_db_session.commit()
    await real_db_session.refresh(test_user)

    return {
        "user_id": str(user_id),
        "email": user_email,
        "password": password,
        "user": test_user,
    }


@pytest_asyncio.fixture
async def mock_external_dependencies():
    """
    Mock only external dependencies as per CLAUDE.md guidelines.
    APPROVED: Redis, time, UUID generation (external boundaries).
    PROHIBITED: ClientService, database sessions, business logic.
    """
    with patch("redis.from_url") as mock_redis_factory:
        # Mock Redis (external dependency - APPROVED)
        mock_redis = MagicMock()
        mock_redis.setex.return_value = None
        mock_redis.delete.return_value = None
        mock_redis.exists.return_value = False
        mock_redis.smembers.return_value = set()
        mock_redis.get.return_value = None
        mock_redis_factory.return_value = mock_redis

        with patch("uuid.uuid4") as mock_uuid:
            # Mock UUID generation (external dependency - APPROVED)
            mock_uuid.return_value = uuid.UUID("87654321-4321-8765-2109-876543210987")

            with patch("src.services.auth_service.datetime") as mock_datetime:
                # Mock time for deterministic tests (external dependency - APPROVED)
                fixed_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
                mock_datetime.now.return_value = fixed_time
                mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

                yield {
                    "redis": mock_redis,
                    "uuid": mock_uuid,
                    "datetime": mock_datetime,
                    "fixed_time": fixed_time,
                }


@pytest_asyncio.fixture
async def client():
    """HTTP client for API testing."""
    from httpx import ASGITransport

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def authenticated_headers(
    client: AsyncClient, test_user_with_permissions, mock_external_dependencies
):
    """Get authentication headers for test user with permissions."""
    # Login to get access token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user_with_permissions["email"],
            "password": test_user_with_permissions["password"],
        },
    )

    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def unauthenticated_headers(
    client: AsyncClient, test_user_no_permissions, mock_external_dependencies
):
    """Get authentication headers for test user without permissions."""
    # Login to get access token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user_no_permissions["email"],
            "password": test_user_no_permissions["password"],
        },
    )

    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    return {"Authorization": f"Bearer {access_token}"}


class TestClientAPIIntegration:
    """
    Full client API integration tests using real database.
    Tests actual business logic without mocking internal services.
    """

    async def test_create_client_success_with_real_database(
        self,
        client: AsyncClient,
        real_db_session,
        test_user_with_permissions,
        authenticated_headers,
        mock_external_dependencies,
    ):
        """
        Test complete client creation flow with real database integration.
        Following CLAUDE.md: Use real ClientService, real database, mock only external deps.
        """
        # Test client data
        client_data = {
            "name": "Test Integration Client",
            "cpf": "11144477735",
            "birth_date": "1990-05-15",
        }

        # Test successful client creation using real authentication logic
        response = await client.post(
            "/api/v1/clients",
            json=client_data,
            headers=authenticated_headers,
        )

        assert response.status_code == 201
        response_data = response.json()

        # Verify complete response structure
        assert "id" in response_data
        assert response_data["name"] == client_data["name"]
        assert response_data["cpf"] == client_data["cpf"]
        assert response_data["birth_date"] == client_data["birth_date"]
        assert response_data["is_active"] is True
        assert "created_at" in response_data
        assert "updated_at" in response_data
        assert response_data["created_by"] == test_user_with_permissions["user_id"]

        # Verify client was actually saved in database
        client_id = uuid.UUID(response_data["id"])
        statement = select(Client).where(Client.id == client_id)
        result = await real_db_session.execute(statement)
        saved_client = result.scalar_one_or_none()

        assert saved_client is not None
        assert saved_client.name == client_data["name"]
        assert saved_client.cpf == client_data["cpf"]
        assert saved_client.is_active is True

    async def test_create_client_duplicate_cpf_real_flow(
        self,
        client: AsyncClient,
        real_db_session,
        test_user_with_permissions,
        authenticated_headers,
        mock_external_dependencies,
    ):
        """Test client creation with duplicate CPF using real database validation."""
        # Create first client directly in database
        existing_client = ClientFactory.create_client(
            name="Existing Client",
            cpf="11144477735",
            created_by=uuid.UUID(test_user_with_permissions["user_id"]),
        )
        real_db_session.add(existing_client)
        await real_db_session.commit()

        # Try to create second client with same CPF via API
        client_data = {
            "name": "Duplicate CPF Client",
            "cpf": "11144477735",  # Same CPF as existing client
            "birth_date": "1985-01-01",
        }

        response = await client.post(
            "/api/v1/clients",
            json=client_data,
            headers=authenticated_headers,
        )

        assert response.status_code == 409
        assert "CPF already exists" in response.json()["detail"]

    async def test_get_client_success_real_database(
        self,
        client: AsyncClient,
        real_db_session,
        test_user_with_permissions,
        authenticated_headers,
        mock_external_dependencies,
    ):
        """Test client retrieval with real database lookup."""
        # Create client directly in database
        test_client = ClientFactory.create_client(
            name="Test Retrieval Client",
            created_by=uuid.UUID(test_user_with_permissions["user_id"]),
        )
        real_db_session.add(test_client)
        await real_db_session.commit()
        await real_db_session.refresh(test_client)

        # Test client retrieval via API
        response = await client.get(
            f"/api/v1/clients/{test_client.id}",
            headers=authenticated_headers,
        )

        assert response.status_code == 200
        response_data = response.json()

        # Verify client information from real database lookup
        assert response_data["id"] == str(test_client.id)
        assert response_data["name"] == test_client.name
        assert response_data["cpf"] == test_client.cpf
        assert response_data["birth_date"] == test_client.birth_date.isoformat()
        assert response_data["is_active"] is True

    async def test_get_client_not_found_real_database(
        self,
        client: AsyncClient,
        authenticated_headers,
        mock_external_dependencies,
    ):
        """Test client retrieval for non-existent client."""
        non_existent_id = uuid.uuid4()

        response = await client.get(
            f"/api/v1/clients/{non_existent_id}",
            headers=authenticated_headers,
        )

        assert response.status_code == 404
        assert "Client not found" in response.json()["detail"]

    async def test_list_clients_success_real_database(
        self,
        client: AsyncClient,
        real_db_session,
        test_user_with_permissions,
        authenticated_headers,
        mock_external_dependencies,
    ):
        """Test client listing with real database and pagination."""
        # Create multiple clients in database
        clients_data = []
        for i in range(5):
            test_client = ClientFactory.create_client(
                name=f"Test List Client {i + 1}",
                created_by=uuid.UUID(test_user_with_permissions["user_id"]),
            )
            real_db_session.add(test_client)
            clients_data.append(test_client)

        await real_db_session.commit()

        # Test client listing via API
        response = await client.get(
            "/api/v1/clients?page=1&per_page=10",
            headers=authenticated_headers,
        )

        assert response.status_code == 200
        response_data = response.json()

        # Verify pagination structure and data
        assert "clients" in response_data
        assert "total" in response_data
        assert "page" in response_data
        assert "per_page" in response_data
        assert "total_pages" in response_data

        assert response_data["total"] >= 5  # At least our test clients
        assert response_data["page"] == 1
        assert response_data["per_page"] == 10
        assert len(response_data["clients"]) >= 5

        # Verify client structure
        for client_data in response_data["clients"]:
            assert "id" in client_data
            assert "name" in client_data
            assert "cpf" in client_data
            assert "birth_date" in client_data
            assert "is_active" in client_data

    async def test_list_clients_with_search_real_database(
        self,
        client: AsyncClient,
        real_db_session,
        test_user_with_permissions,
        authenticated_headers,
        mock_external_dependencies,
    ):
        """Test client listing with search functionality."""
        # Create clients with specific names
        searchable_client = ClientFactory.create_client(
            name="João Silva Santos",
            created_by=uuid.UUID(test_user_with_permissions["user_id"]),
        )
        non_matching_client = ClientFactory.create_client(
            name="Maria Oliveira Costa",
            created_by=uuid.UUID(test_user_with_permissions["user_id"]),
        )

        real_db_session.add(searchable_client)
        real_db_session.add(non_matching_client)
        await real_db_session.commit()

        # Test search functionality
        response = await client.get(
            "/api/v1/clients?search=João&page=1&per_page=10",
            headers=authenticated_headers,
        )

        assert response.status_code == 200
        response_data = response.json()

        # Should find the searchable client
        matching_names = [client["name"] for client in response_data["clients"]]
        assert any("João" in name for name in matching_names)

    async def test_update_client_success_real_database(
        self,
        client: AsyncClient,
        real_db_session,
        test_user_with_permissions,
        authenticated_headers,
        mock_external_dependencies,
    ):
        """Test client update with real database persistence."""
        # Create client in database
        test_client = ClientFactory.create_client(
            name="Original Name",
            created_by=uuid.UUID(test_user_with_permissions["user_id"]),
        )
        real_db_session.add(test_client)
        await real_db_session.commit()
        await real_db_session.refresh(test_client)

        original_id = test_client.id
        original_cpf = test_client.cpf

        # Update client via API
        update_data = {
            "name": "Updated Name",
            "birth_date": "1992-06-20",
        }

        response = await client.put(
            f"/api/v1/clients/{original_id}",
            json=update_data,
            headers=authenticated_headers,
        )

        assert response.status_code == 200
        response_data = response.json()

        # Verify response data
        assert response_data["id"] == str(original_id)
        assert response_data["name"] == "Updated Name"
        assert response_data["cpf"] == original_cpf  # Should remain unchanged
        assert response_data["birth_date"] == "1992-06-20"

        # Verify changes persisted in database
        await real_db_session.refresh(test_client)
        assert test_client.name == "Updated Name"
        assert test_client.birth_date == date(1992, 6, 20)

    async def test_delete_client_success_real_database(
        self,
        client: AsyncClient,
        real_db_session,
        test_user_with_permissions,
        authenticated_headers,
        mock_external_dependencies,
    ):
        """Test client soft deletion with real database persistence."""
        # Create client in database
        test_client = ClientFactory.create_client(
            name="To Be Deleted",
            created_by=uuid.UUID(test_user_with_permissions["user_id"]),
        )
        real_db_session.add(test_client)
        await real_db_session.commit()
        await real_db_session.refresh(test_client)

        original_id = test_client.id

        # Delete client via API
        response = await client.delete(
            f"/api/v1/clients/{original_id}",
            headers=authenticated_headers,
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify client was soft deleted in database
        await real_db_session.refresh(test_client)
        assert test_client.is_active is False

        # Verify client no longer appears in active listings
        list_response = await client.get(
            "/api/v1/clients",
            headers=authenticated_headers,
        )

        active_client_ids = [client["id"] for client in list_response.json()["clients"]]
        assert str(original_id) not in active_client_ids


class TestClientAPIPermissions:
    """Test client API permission validation."""

    async def test_create_client_without_permission(
        self,
        client: AsyncClient,
        test_user_no_permissions,
        unauthenticated_headers,
        mock_external_dependencies,
    ):
        """Test client creation without proper permissions."""
        client_data = {
            "name": "Unauthorized Client",
            "cpf": "11144477735",
            "birth_date": "1990-05-15",
        }

        response = await client.post(
            "/api/v1/clients",
            json=client_data,
            headers=unauthenticated_headers,
        )

        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]

    async def test_get_client_without_permission(
        self,
        client: AsyncClient,
        unauthenticated_headers,
        mock_external_dependencies,
    ):
        """Test client retrieval without proper permissions."""
        test_id = uuid.uuid4()

        response = await client.get(
            f"/api/v1/clients/{test_id}",
            headers=unauthenticated_headers,
        )

        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]

    async def test_list_clients_without_permission(
        self,
        client: AsyncClient,
        unauthenticated_headers,
        mock_external_dependencies,
    ):
        """Test client listing without proper permissions."""
        response = await client.get(
            "/api/v1/clients",
            headers=unauthenticated_headers,
        )

        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]

    async def test_update_client_without_permission(
        self,
        client: AsyncClient,
        unauthenticated_headers,
        mock_external_dependencies,
    ):
        """Test client update without proper permissions."""
        test_id = uuid.uuid4()
        update_data = {"name": "Unauthorized Update"}

        response = await client.put(
            f"/api/v1/clients/{test_id}",
            json=update_data,
            headers=unauthenticated_headers,
        )

        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]

    async def test_delete_client_without_permission(
        self,
        client: AsyncClient,
        unauthenticated_headers,
        mock_external_dependencies,
    ):
        """Test client deletion without proper permissions."""
        test_id = uuid.uuid4()

        response = await client.delete(
            f"/api/v1/clients/{test_id}",
            headers=unauthenticated_headers,
        )

        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]

    async def test_unauthenticated_access(
        self,
        client: AsyncClient,
        mock_external_dependencies,
    ):
        """Test API access without authentication token."""
        # Test without any authorization header
        response = await client.get("/api/v1/clients")

        assert response.status_code in [401, 403]  # Both unauthorized statuses are valid
        assert (
            "Not authenticated" in response.json()["detail"]
            or "Authorization header missing" in response.json()["detail"]
            or "Permission denied" in response.json()["detail"]
        )


class TestClientAPIErrorScenarios:
    """Test client API error handling scenarios."""

    async def test_create_client_invalid_data(
        self,
        client: AsyncClient,
        authenticated_headers,
        mock_external_dependencies,
    ):
        """Test client creation with invalid data."""
        # Invalid CPF
        invalid_data = {
            "name": "Test Client",
            "cpf": "invalid-cpf",
            "birth_date": "1990-05-15",
        }

        response = await client.post(
            "/api/v1/clients",
            json=invalid_data,
            headers=authenticated_headers,
        )

        assert response.status_code == 422  # Validation error
        assert "validation" in response.json()["detail"].lower()

    async def test_update_client_invalid_uuid(
        self,
        client: AsyncClient,
        authenticated_headers,
        mock_external_dependencies,
    ):
        """Test client update with invalid UUID."""
        update_data = {"name": "Updated Name"}

        response = await client.put(
            "/api/v1/clients/invalid-uuid",
            json=update_data,
            headers=authenticated_headers,
        )

        assert response.status_code == 422  # Validation error

    async def test_client_api_malformed_request(
        self,
        client: AsyncClient,
        authenticated_headers,
        mock_external_dependencies,
    ):
        """Test API with malformed JSON request."""
        # Send malformed JSON
        response = await client.post(
            "/api/v1/clients",
            content="invalid json",  # Use content instead of json to send raw text
            headers={**authenticated_headers, "Content-Type": "application/json"},
        )

        assert response.status_code == 422  # Unprocessable Entity for malformed JSON
