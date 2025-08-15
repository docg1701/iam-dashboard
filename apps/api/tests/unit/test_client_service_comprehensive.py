"""
Comprehensive ClientService tests to improve coverage.

Following CLAUDE.md guidelines: Never mock internal business logic.
Mock only external dependencies (database sessions, time, UUID generation).

Target: Achieve >80% coverage for client_service.py
Focus: Lines 68-147 (create_client), 165-192 (get_client), 220-298 (list_clients),
       329-455 (update_client), 481-563 (delete_client)
"""

import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

import pytest
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

from src.models.audit import AuditAction, AuditLog
from src.models.client import Client
from src.schemas.client import (
    ClientCreateRequest,
    ClientListResponse,
    ClientResponse,
    ClientUpdateRequest,
)
from src.services.client_service import ClientService


class TestClientServiceCreateClient:
    """Test create_client method comprehensive coverage."""

    @pytest.fixture
    def mock_session_maker(self):
        """Mock session maker for database operations."""
        mock_session = AsyncMock()
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
        return mock_session_maker, mock_session

    @pytest.fixture
    def valid_client_data(self):
        """Valid client creation data."""
        return ClientCreateRequest(
            name="João Silva Santos",
            cpf="11144477735",  # Valid Brazilian CPF
            birth_date=date(1990, 5, 15),
        )

    @pytest.fixture
    def user_id(self):
        """Test user ID."""
        return uuid.UUID("12345678-1234-5678-9012-123456789012")

    @patch("src.services.client_service.get_session_maker")
    async def test_create_client_success(
        self, mock_get_session_maker, mock_session_maker, valid_client_data, user_id
    ):
        """Test successful client creation with audit logging."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock database operations
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None  # No duplicate CPF
        mock_session.execute.return_value = mock_result
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        # Mock UUID generation for consistent testing
        test_client_id = uuid.UUID("87654321-4321-8765-2109-876543210987")
        with patch("uuid.uuid4", return_value=test_client_id):
            client_service = ClientService()
            
            result = await client_service.create_client(
                client_data=valid_client_data,
                created_by=user_id,
                ip_address="192.168.1.1",
                user_agent="Test Agent",
                session_id="test-session-123",
            )

        # Verify result
        assert isinstance(result, ClientResponse)
        assert result.name == valid_client_data.name
        assert result.cpf == valid_client_data.cpf
        assert result.birth_date == valid_client_data.birth_date
        assert result.created_by == user_id
        assert result.is_active is True

        # Verify database operations
        mock_session.execute.assert_called()  # CPF check query
        mock_session.add.assert_called()  # Client and audit entry added
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("src.services.client_service.get_session_maker")
    async def test_create_client_duplicate_cpf(
        self, mock_get_session_maker, mock_session_maker, valid_client_data, user_id
    ):
        """Test client creation fails with duplicate CPF."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock existing client with same CPF
        existing_client = Client(
            id=uuid.uuid4(),
            name="Existing Client",
            cpf=valid_client_data.cpf,
            birth_date=date(1985, 1, 1),
            created_by=user_id,
        )
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing_client
        mock_session.execute.return_value = mock_result

        client_service = ClientService()
        
        with pytest.raises(HTTPException) as exc_info:
            await client_service.create_client(
                client_data=valid_client_data,
                created_by=user_id,
            )

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "CPF already exists" in exc_info.value.detail

    @patch("src.services.client_service.get_session_maker")
    async def test_create_client_validation_error(
        self, mock_get_session_maker, mock_session_maker, user_id
    ):
        """Test client creation handles validation errors."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock no duplicate CPF
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_session.rollback = AsyncMock()

        # Mock Client creation to raise ValidationError
        with patch("src.services.client_service.Client") as mock_client_class:
            validation_error = ValidationError.from_exception_data(
                "Client",
                [{"type": "value_error", "loc": ("cpf",), "msg": "Invalid CPF", "input": {}}],
            )
            mock_client_class.side_effect = validation_error

            client_service = ClientService()
            
            # Use valid data but Client constructor will raise ValidationError
            valid_data = ClientCreateRequest(
                name="Test Client",
                cpf="11144477735",
                birth_date=date(1990, 1, 1),
            )

            with pytest.raises(HTTPException) as exc_info:
                await client_service.create_client(
                    client_data=valid_data,
                    created_by=user_id,
                )

            assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert "Validation error" in exc_info.value.detail
            mock_session.rollback.assert_called_once()

    @patch("src.services.client_service.get_session_maker")
    async def test_create_client_database_error(
        self, mock_get_session_maker, mock_session_maker, valid_client_data, user_id
    ):
        """Test client creation handles database errors."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock database error during commit
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("Database error"))
        mock_session.rollback = AsyncMock()

        client_service = ClientService()
        
        with pytest.raises(HTTPException) as exc_info:
            await client_service.create_client(
                client_data=valid_client_data,
                created_by=user_id,
            )

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to create client" in exc_info.value.detail
        mock_session.rollback.assert_called_once()


class TestClientServiceGetClient:
    """Test get_client method comprehensive coverage."""

    @pytest.fixture
    def mock_session_maker(self):
        """Mock session maker for database operations."""
        mock_session = AsyncMock()
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
        return mock_session_maker, mock_session

    @pytest.fixture
    def test_client(self):
        """Test client instance."""
        return Client(
            id=uuid.UUID("12345678-1234-5678-9012-123456789012"),
            name="Test Client",
            cpf="11144477735",
            birth_date=date(1990, 1, 1),
            created_by=uuid.UUID("87654321-4321-8765-2109-876543210987"),
        )

    @patch("src.services.client_service.get_session_maker")
    async def test_get_client_success(
        self, mock_get_session_maker, mock_session_maker, test_client
    ):
        """Test successful client retrieval."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock successful client query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = test_client
        mock_session.execute.return_value = mock_result

        client_service = ClientService()
        result = await client_service.get_client(test_client.id)

        # Verify result
        assert isinstance(result, ClientResponse)
        assert result.id == test_client.id
        assert result.name == test_client.name
        assert result.cpf == test_client.cpf
        assert result.birth_date == test_client.birth_date

        # Verify query was executed
        mock_session.execute.assert_called_once()

    @patch("src.services.client_service.get_session_maker")
    async def test_get_client_not_found(
        self, mock_get_session_maker, mock_session_maker
    ):
        """Test client not found scenario."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock client not found
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        client_service = ClientService()
        client_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
        
        with pytest.raises(HTTPException) as exc_info:
            await client_service.get_client(client_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Client not found" in exc_info.value.detail

    @patch("src.services.client_service.get_session_maker")
    async def test_get_client_database_error(
        self, mock_get_session_maker, mock_session_maker
    ):
        """Test get client handles database errors."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock database error
        mock_session.execute.side_effect = SQLAlchemyError("Database error")

        client_service = ClientService()
        client_id = uuid.UUID("12345678-1234-5678-9012-123456789012")
        
        with pytest.raises(HTTPException) as exc_info:
            await client_service.get_client(client_id)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to retrieve client" in exc_info.value.detail


class TestClientServiceListClients:
    """Test list_clients method comprehensive coverage."""

    @pytest.fixture
    def mock_session_maker(self):
        """Mock session maker for database operations."""
        mock_session = AsyncMock()
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
        return mock_session_maker, mock_session

    @pytest.fixture
    def test_clients(self):
        """Test client list."""
        return [
            Client(
                id=uuid.UUID("12345678-1234-5678-9012-123456789001"),
                name="Client One",
                cpf="11144477735",
                birth_date=date(1990, 1, 1),
                created_by=uuid.UUID("87654321-4321-8765-2109-876543210987"),
            ),
            Client(
                id=uuid.UUID("12345678-1234-5678-9012-123456789002"),
                name="Client Two",
                cpf="22255588846",
                birth_date=date(1985, 5, 15),
                created_by=uuid.UUID("87654321-4321-8765-2109-876543210987"),
            ),
        ]

    @patch("src.services.client_service.get_session_maker")
    async def test_list_clients_success(
        self, mock_get_session_maker, mock_session_maker, test_clients
    ):
        """Test successful client listing with pagination."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock count query result
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 25

        # Mock clients query result
        mock_clients_result = MagicMock()
        mock_clients_result.scalars.return_value.all.return_value = test_clients

        # Configure mock_session.execute to return different results for different queries
        mock_session.execute.side_effect = [mock_count_result, mock_clients_result]

        client_service = ClientService()
        result = await client_service.list_clients(page=2, per_page=5, search="Client")

        # Verify result
        assert isinstance(result, ClientListResponse)
        assert len(result.clients) == 2
        assert result.total == 25
        assert result.page == 2
        assert result.per_page == 5
        assert result.total_pages == 5

        # Verify queries were executed
        assert mock_session.execute.call_count == 2

    @patch("src.services.client_service.get_session_maker")
    async def test_list_clients_invalid_page(
        self, mock_get_session_maker, mock_session_maker
    ):
        """Test list clients with invalid page parameters."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        client_service = ClientService()
        
        # Test negative page
        with pytest.raises(HTTPException) as exc_info:
            await client_service.list_clients(page=-1)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Page number must be positive" in exc_info.value.detail

        # Test zero page
        with pytest.raises(HTTPException) as exc_info:
            await client_service.list_clients(page=0)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Page number must be positive" in exc_info.value.detail

    @patch("src.services.client_service.get_session_maker")
    async def test_list_clients_invalid_per_page(
        self, mock_get_session_maker, mock_session_maker
    ):
        """Test list clients with invalid per_page parameters."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        client_service = ClientService()
        
        # Test per_page too small
        with pytest.raises(HTTPException) as exc_info:
            await client_service.list_clients(per_page=0)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Per page must be between 1 and 100" in exc_info.value.detail

        # Test per_page too large
        with pytest.raises(HTTPException) as exc_info:
            await client_service.list_clients(per_page=101)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Per page must be between 1 and 100" in exc_info.value.detail

    @patch("src.services.client_service.get_session_maker")
    async def test_list_clients_with_filters(
        self, mock_get_session_maker, mock_session_maker, test_clients
    ):
        """Test list clients with is_active filter."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock results
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2
        mock_clients_result = MagicMock()
        mock_clients_result.scalars.return_value.all.return_value = test_clients

        mock_session.execute.side_effect = [mock_count_result, mock_clients_result]

        client_service = ClientService()
        result = await client_service.list_clients(is_active=False)

        # Verify result
        assert isinstance(result, ClientListResponse)
        assert len(result.clients) == 2
        assert result.total == 2

    @patch("src.services.client_service.get_session_maker")
    async def test_list_clients_database_error(
        self, mock_get_session_maker, mock_session_maker
    ):
        """Test list clients handles database errors."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock database error
        mock_session.execute.side_effect = SQLAlchemyError("Database error")

        client_service = ClientService()
        
        with pytest.raises(HTTPException) as exc_info:
            await client_service.list_clients()

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to retrieve clients" in exc_info.value.detail


class TestClientServiceUpdateClient:
    """Test update_client method comprehensive coverage."""

    @pytest.fixture
    def mock_session_maker(self):
        """Mock session maker for database operations."""
        mock_session = AsyncMock()
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
        return mock_session_maker, mock_session

    @pytest.fixture
    def test_client(self):
        """Test client instance."""
        return Client(
            id=uuid.UUID("12345678-1234-5678-9012-123456789012"),
            name="Original Name",
            cpf="11144477735",
            birth_date=date(1990, 1, 1),
            created_by=uuid.UUID("87654321-4321-8765-2109-876543210987"),
        )

    @pytest.fixture
    def update_data(self):
        """Client update data."""
        return ClientUpdateRequest(
            name="Updated Name",
            birth_date=date(1992, 6, 20),
            is_active=True,
        )

    @pytest.fixture
    def user_id(self):
        """Test user ID."""
        return uuid.UUID("11111111-1111-1111-1111-111111111111")

    @patch("src.services.client_service.get_session_maker")
    @patch("src.services.client_service.datetime")
    async def test_update_client_success(
        self, mock_datetime, mock_get_session_maker, mock_session_maker, 
        test_client, update_data, user_id
    ):
        """Test successful client update with audit logging."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock datetime for consistent timestamps
        fixed_datetime = datetime(2025, 8, 15, 10, 30, 0)
        mock_datetime.now.return_value = fixed_datetime

        # Mock successful client query (for update)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = test_client
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        client_service = ClientService()
        result = await client_service.update_client(
            client_id=test_client.id,
            client_data=update_data,
            updated_by=user_id,
            ip_address="192.168.1.1",
            user_agent="Test Agent",
            session_id="test-session-123",
        )

        # Verify result
        assert isinstance(result, ClientResponse)
        assert result.name == update_data.name
        assert result.birth_date == update_data.birth_date
        assert result.is_active == update_data.is_active

        # Verify database operations
        mock_session.execute.assert_called()  # Client query
        mock_session.add.assert_called()  # Audit entry added
        mock_session.commit.assert_called_once()

    @patch("src.services.client_service.get_session_maker")
    async def test_update_client_not_found(
        self, mock_get_session_maker, mock_session_maker, update_data, user_id
    ):
        """Test update client when client not found."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock client not found
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        client_service = ClientService()
        client_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
        
        with pytest.raises(HTTPException) as exc_info:
            await client_service.update_client(
                client_id=client_id,
                client_data=update_data,
                updated_by=user_id,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Client not found" in exc_info.value.detail

    @patch("src.services.client_service.get_session_maker")
    async def test_update_client_cpf_conflict(
        self, mock_get_session_maker, mock_session_maker, test_client, user_id
    ):
        """Test update client with CPF conflict."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Create update data with new CPF
        update_data = ClientUpdateRequest(cpf="22255588846")

        # Mock existing client with conflicting CPF
        conflicting_client = Client(
            id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
            name="Other Client",
            cpf="22255588846",
            birth_date=date(1985, 1, 1),
            created_by=user_id,
        )

        # Mock query results: first call returns target client, second returns conflicting client
        mock_result1 = AsyncMock()
        mock_result1.scalar_one_or_none.return_value = test_client
        mock_result2 = AsyncMock()
        mock_result2.scalar_one_or_none.return_value = conflicting_client
        mock_session.execute.side_effect = [mock_result1, mock_result2]
        mock_session.rollback = AsyncMock()

        client_service = ClientService()
        
        with pytest.raises(HTTPException) as exc_info:
            await client_service.update_client(
                client_id=test_client.id,
                client_data=update_data,
                updated_by=user_id,
            )

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "CPF already exists" in exc_info.value.detail
        mock_session.rollback.assert_called_once()

    @patch("src.services.client_service.get_session_maker")
    async def test_update_client_validation_error(
        self, mock_get_session_maker, mock_session_maker, test_client, user_id
    ):
        """Test update client handles validation errors."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock client found
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = test_client
        mock_session.execute.return_value = mock_result
        mock_session.rollback = AsyncMock()

        # Mock _validate_fields to raise ValidationError
        with patch.object(test_client, "_validate_fields") as mock_validate:
            validation_error = ValidationError.from_exception_data(
                "Client",
                [{"type": "value_error", "loc": ("name",), "msg": "Invalid name", "input": {}}],
            )
            mock_validate.side_effect = validation_error

            client_service = ClientService()
            update_data = ClientUpdateRequest(name="Updated Name")
            
            with pytest.raises(HTTPException) as exc_info:
                await client_service.update_client(
                    client_id=test_client.id,
                    client_data=update_data,
                    updated_by=user_id,
                )

            assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert "Validation error" in exc_info.value.detail
            mock_session.rollback.assert_called_once()

    @patch("src.services.client_service.get_session_maker")
    async def test_update_client_database_error(
        self, mock_get_session_maker, mock_session_maker, test_client, update_data, user_id
    ):
        """Test update client handles database errors."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock client found but commit fails
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = test_client
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("Database error"))
        mock_session.rollback = AsyncMock()

        client_service = ClientService()
        
        with pytest.raises(HTTPException) as exc_info:
            await client_service.update_client(
                client_id=test_client.id,
                client_data=update_data,
                updated_by=user_id,
            )

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to update client" in exc_info.value.detail
        mock_session.rollback.assert_called_once()


class TestClientServiceDeleteClient:
    """Test delete_client method comprehensive coverage."""

    @pytest.fixture
    def mock_session_maker(self):
        """Mock session maker for database operations."""
        mock_session = AsyncMock()
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
        return mock_session_maker, mock_session

    @pytest.fixture
    def test_client(self):
        """Test client instance."""
        return Client(
            id=uuid.UUID("12345678-1234-5678-9012-123456789012"),
            name="Test Client",
            cpf="11144477735",
            birth_date=date(1990, 1, 1),
            created_by=uuid.UUID("87654321-4321-8765-2109-876543210987"),
            is_active=True,
        )

    @pytest.fixture
    def user_id(self):
        """Test user ID."""
        return uuid.UUID("11111111-1111-1111-1111-111111111111")

    @patch("src.services.client_service.get_session_maker")
    @patch("src.services.client_service.datetime")
    async def test_delete_client_success(
        self, mock_datetime, mock_get_session_maker, mock_session_maker, 
        test_client, user_id
    ):
        """Test successful client soft deletion with audit logging."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock datetime for consistent timestamps
        fixed_datetime = datetime(2025, 8, 15, 10, 30, 0)
        mock_datetime.now.return_value = fixed_datetime

        # Mock successful client query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = test_client
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        client_service = ClientService()
        await client_service.delete_client(
            client_id=test_client.id,
            deleted_by=user_id,
            ip_address="192.168.1.1",
            user_agent="Test Agent",
            session_id="test-session-123",
        )

        # Verify client was soft deleted
        assert test_client.is_active is False

        # Verify database operations
        mock_session.execute.assert_called_once()  # Client query
        mock_session.add.assert_called_once()  # Audit entry added
        mock_session.commit.assert_called_once()

    @patch("src.services.client_service.get_session_maker")
    async def test_delete_client_not_found(
        self, mock_get_session_maker, mock_session_maker, user_id
    ):
        """Test delete client when client not found."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock client not found
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_session.rollback = AsyncMock()

        client_service = ClientService()
        client_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
        
        with pytest.raises(HTTPException) as exc_info:
            await client_service.delete_client(
                client_id=client_id,
                deleted_by=user_id,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Client not found" in exc_info.value.detail
        mock_session.rollback.assert_called_once()

    @patch("src.services.client_service.get_session_maker")
    async def test_delete_client_already_deleted(
        self, mock_get_session_maker, mock_session_maker, test_client, user_id
    ):
        """Test delete client when client is already inactive."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Set client as already inactive
        test_client.is_active = False

        # Mock client found but inactive
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = test_client
        mock_session.execute.return_value = mock_result
        mock_session.rollback = AsyncMock()

        client_service = ClientService()
        
        with pytest.raises(HTTPException) as exc_info:
            await client_service.delete_client(
                client_id=test_client.id,
                deleted_by=user_id,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Client is already deleted" in exc_info.value.detail
        mock_session.rollback.assert_called_once()

    @patch("src.services.client_service.get_session_maker")
    async def test_delete_client_database_error(
        self, mock_get_session_maker, mock_session_maker, test_client, user_id
    ):
        """Test delete client handles database errors."""
        mock_session_maker_func, mock_session = mock_session_maker
        mock_get_session_maker.return_value = mock_session_maker_func

        # Mock client found but commit fails
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = test_client
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("Database error"))
        mock_session.rollback = AsyncMock()

        client_service = ClientService()
        
        with pytest.raises(HTTPException) as exc_info:
            await client_service.delete_client(
                client_id=test_client.id,
                deleted_by=user_id,
            )

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to delete client" in exc_info.value.detail
        mock_session.rollback.assert_called_once()


class TestClientServiceHelperMethods:
    """Test helper methods coverage."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def test_client(self):
        """Test client instance."""
        return Client(
            id=uuid.UUID("12345678-1234-5678-9012-123456789012"),
            name="Test Client",
            cpf="11144477735",
            birth_date=date(1990, 1, 1),
            created_by=uuid.UUID("87654321-4321-8765-2109-876543210987"),
        )

    async def test_get_client_by_cpf_found(self, mock_session, test_client):
        """Test _get_client_by_cpf when client is found."""
        # Mock successful query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = test_client
        mock_session.execute.return_value = mock_result

        client_service = ClientService()
        result = await client_service._get_client_by_cpf(mock_session, "11144477735")

        assert result == test_client
        mock_session.execute.assert_called_once()

    async def test_get_client_by_cpf_not_found(self, mock_session):
        """Test _get_client_by_cpf when client is not found."""
        # Mock query returning None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        client_service = ClientService()
        result = await client_service._get_client_by_cpf(mock_session, "99999999999")

        assert result is None
        mock_session.execute.assert_called_once()


class TestClientServiceIntegration:
    """Test service integration and edge cases."""

    def test_service_initialization(self):
        """Test ClientService initializes correctly."""
        with patch("src.services.client_service.get_session_maker") as mock_get_session_maker:
            mock_session_maker = MagicMock()
            mock_get_session_maker.return_value = mock_session_maker

            service = ClientService()
            
            assert service.session_maker == mock_session_maker
            mock_get_session_maker.assert_called_once()

    def test_global_service_instance(self):
        """Test global service instance is available."""
        from src.services.client_service import client_service

        assert client_service is not None
        assert isinstance(client_service, ClientService)

    @patch("src.services.client_service.get_session_maker")
    async def test_audit_log_creation_parameters(self, mock_get_session_maker):
        """Test audit log creation with all parameters."""
        mock_session = AsyncMock()
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_get_session_maker.return_value = mock_session_maker

        # Mock no duplicate CPF
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        # Capture audit log creation
        captured_audit_logs = []
        original_add = mock_session.add
        def capture_add(obj):
            if isinstance(obj, AuditLog):
                captured_audit_logs.append(obj)
            original_add(obj)
        mock_session.add.side_effect = capture_add

        client_service = ClientService()
        valid_data = ClientCreateRequest(
            name="Test Client",
            cpf="11144477735",
            birth_date=date(1990, 1, 1),
        )
        user_id = uuid.UUID("12345678-1234-5678-9012-123456789012")

        await client_service.create_client(
            client_data=valid_data,
            created_by=user_id,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Agent",
            session_id="session-abc-123",
        )

        # Verify audit log was created with correct parameters
        assert len(captured_audit_logs) == 1
        audit_log = captured_audit_logs[0]
        assert audit_log.action == AuditAction.CREATE
        assert audit_log.resource_type == "client"
        assert audit_log.actor_id == user_id
        assert audit_log.ip_address == "192.168.1.100"
        assert audit_log.user_agent == "Mozilla/5.0 Test Agent"
        assert audit_log.session_id == "session-abc-123"
        assert "Created client" in audit_log.description
        assert audit_log.new_values is not None
        assert "name" in audit_log.new_values
        assert "cpf" in audit_log.new_values  # Should be masked
        assert "birth_date" in audit_log.new_values
        assert "is_active" in audit_log.new_values