"""
Comprehensive tests for ClientService business logic.

This module tests the ClientService class which handles business logic
for client operations including validation, audit logging, and error handling.
"""

from datetime import date, datetime
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi import Request
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from src.core.exceptions import ConflictError, DatabaseError, NotFoundError, ValidationError
from src.models.client import Client, ClientStatus
from src.models.user import User, UserRole
from src.schemas.clients import ClientCreate as ClientCreateSchema
from src.schemas.clients import ClientSearchParams, ClientUpdate
from src.services.client_service import ClientService


class TestClientServiceCreate:
    """Test ClientService.create_client method."""

    @pytest.mark.asyncio
    async def test_create_client_success(self, test_session: Session) -> None:
        """Test successful client creation."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Client data
        client_data = ClientCreateSchema(
            full_name="Test Client",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            notes="Test notes",
        )

        # Create client
        result = await service.create_client(client_data, user.user_id, mock_request)

        # Verify result
        assert result.full_name == client_data.full_name
        assert result.ssn == client_data.ssn
        assert result.birth_date == client_data.birth_date
        assert result.notes == client_data.notes
        assert result.status == "active"
        assert result.created_by == user.user_id
        assert result.updated_by == user.user_id
        assert result.created_at is not None
        # updated_at is None for new records, only set during updates

        # Verify in database

        db_client = test_session.exec(
            select(Client).where(Client.client_id == result.client_id)
        ).first()
        assert db_client is not None
        assert db_client.full_name == client_data.full_name

    @pytest.mark.asyncio
    async def test_create_client_duplicate_ssn(self, test_session: Session) -> None:
        """Test client creation with duplicate SSN raises ConflictError."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Create first client
        existing_client = Client(
            client_id=uuid4(),
            full_name="Existing Client",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            status="active",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(existing_client)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Try to create client with same SSN
        client_data = ClientCreateSchema(
            full_name="New Client",
            ssn="123-45-6789",  # Same SSN
            birth_date=date(1985, 6, 15),
        )

        # Should raise ConflictError
        with pytest.raises(ConflictError) as exc_info:
            await service.create_client(client_data, user.user_id, mock_request)

        assert "already exists" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_client_minimal_data(self, test_session: Session) -> None:
        """Test client creation with minimal required data."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Client data with no notes
        client_data = ClientCreateSchema(
            full_name="Minimal Client", ssn="987-65-4321", birth_date=date(1995, 8, 12)
        )

        # Create client
        result = await service.create_client(client_data, user.user_id, mock_request)

        # Verify result
        assert result.full_name == client_data.full_name
        assert result.ssn == client_data.ssn
        assert result.birth_date == client_data.birth_date
        assert result.notes is None
        assert result.status == "active"

    @patch("src.services.client_service.log_database_action")
    @pytest.mark.asyncio
    async def test_create_client_audit_logging(
        self, mock_log_action: Mock, test_session: Session
    ) -> None:
        """Test that audit logging is called during client creation."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Client data
        client_data = ClientCreateSchema(
            full_name="Audit Test Client", ssn="555-66-7777", birth_date=date(1992, 4, 8)
        )

        # Create client
        result = await service.create_client(client_data, user.user_id, mock_request)

        # Verify audit logging was called
        mock_log_action.assert_called_once()
        call_args = mock_log_action.call_args

        # Verify audit log parameters
        assert call_args[1]["table_name"] == "clients"
        assert call_args[1]["record_id"] == str(result.client_id)
        assert call_args[1]["action"] == "CREATE"
        assert call_args[1]["user_id"] == user.user_id

    @pytest.mark.asyncio
    async def test_create_client_database_error_handling(self, test_session: Session) -> None:
        """Test handling of database errors during client creation."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Client data
        client_data = ClientCreateSchema(
            full_name="Error Test Client", ssn="888-99-1111", birth_date=date(1990, 1, 1)
        )

        # Mock session to raise SQLAlchemy database error

        with (
            patch.object(test_session, "commit", side_effect=SQLAlchemyError("Database error")),
            pytest.raises(DatabaseError),
        ):
            await service.create_client(client_data, user.user_id, mock_request)


class TestClientServiceGetById:
    """Test ClientService.get_client_by_id method."""

    @pytest.mark.asyncio
    async def test_get_client_by_id_success(self, test_session: Session) -> None:
        """Test successful client retrieval by ID."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)

        # Create test client
        client_id = uuid4()
        test_client = Client(
            client_id=client_id,
            full_name="Test Client",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            status="active",
            notes="Test notes",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(test_client)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Get client by ID
        result = await service.get_client_by_id(client_id, user.user_id, mock_request)

        # Verify result (ClientRead object)
        assert result.client_id == client_id
        assert result.full_name == test_client.full_name
        assert result.ssn == test_client.ssn
        assert result.birth_date == test_client.birth_date
        assert result.notes == test_client.notes

    @pytest.mark.asyncio
    async def test_get_client_by_id_not_found(self, test_session: Session) -> None:
        """Test client retrieval with non-existent ID raises NotFoundError."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Try to get non-existent client
        non_existent_id = uuid4()

        with pytest.raises(NotFoundError) as exc_info:
            await service.get_client_by_id(non_existent_id, user.user_id, mock_request)

        assert "not found" in str(exc_info.value).lower()

    @patch("src.services.client_service.log_database_action")
    @pytest.mark.asyncio
    async def test_get_client_by_id_audit_logging(
        self, mock_log_action: Mock, test_session: Session
    ) -> None:
        """Test that audit logging is called during client retrieval."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)

        # Create test client
        client_id = uuid4()
        test_client = Client(
            client_id=client_id,
            full_name="Audit Test Client",
            ssn="999-88-7777",
            birth_date=date(1985, 12, 25),
            status="active",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(test_client)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Get client by ID
        await service.get_client_by_id(client_id, user.user_id, mock_request)

        # Verify audit logging was called
        mock_log_action.assert_called_once()
        call_args = mock_log_action.call_args

        # Verify audit log parameters
        assert call_args[1]["table_name"] == "clients"
        assert call_args[1]["record_id"] == str(client_id)
        assert call_args[1]["action"] == "VIEW"
        assert call_args[1]["user_id"] == user.user_id


class TestClientServiceValidation:
    """Test ClientService validation logic."""

    @pytest.mark.asyncio
    async def test_ssn_uniqueness_check(self, test_session: Session) -> None:
        """Test SSN uniqueness validation through service."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Create first client
        client_data1 = ClientCreateSchema(
            full_name="First Client", ssn="111-22-3333", birth_date=date(1990, 1, 1)
        )

        await service.create_client(client_data1, user.user_id, mock_request)

        # Try to create second client with same SSN - should fail
        client_data2 = ClientCreateSchema(
            full_name="Second Client",
            ssn="111-22-3333",  # Same SSN
            birth_date=date(1985, 6, 15),
        )

        with pytest.raises(ConflictError):
            await service.create_client(client_data2, user.user_id, mock_request)


class TestClientServiceErrorHandling:
    """Test error handling in ClientService."""

    @pytest.mark.asyncio
    async def test_validation_error_handling(self, test_session: Session) -> None:
        """Test handling of validation errors in service layer."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Valid client data
        client_data = ClientCreateSchema(
            full_name="Test Client", ssn="123-45-6789", birth_date=date(1990, 1, 1)
        )

        # Mock session to raise Pydantic validation error during commit/refresh

        with (
            patch.object(
                test_session,
                "refresh",
                side_effect=PydanticValidationError.from_exception_data("test", []),
            ),
            pytest.raises(ValidationError),
        ):
            await service.create_client(client_data, user.user_id, mock_request)

    @pytest.mark.asyncio
    async def test_session_rollback_on_error(self, test_session: Session) -> None:
        """Test that database session is properly rolled back on errors."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Get initial client count
        initial_count = test_session.query(Client).count()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Client data
        client_data = ClientCreateSchema(
            full_name="Rollback Test Client", ssn="123-45-6789", birth_date=date(1990, 1, 1)
        )

        # Mock session commit to raise SQLAlchemy error

        with (
            patch.object(test_session, "commit", side_effect=SQLAlchemyError("Database error")),
            pytest.raises(DatabaseError),
        ):
            await service.create_client(client_data, user.user_id, mock_request)

        # Verify no client was actually created
        final_count = test_session.query(Client).count()
        assert final_count == initial_count


class TestClientServiceUpdate:
    """Test ClientService.update_client method."""

    @pytest.mark.asyncio
    async def test_update_client_success(self, test_session: Session) -> None:
        """Test successful client update."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)

        # Create test client
        client_id = uuid4()
        test_client = Client(
            client_id=client_id,
            full_name="Original Name",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            status="active",
            notes="Original notes",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )
        test_session.add(test_client)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Update data

        update_data = ClientUpdate(
            full_name="Updated Name",
            notes="Updated notes",
        )

        # Update client
        result = await service.update_client(client_id, update_data, user.user_id, mock_request)

        # Verify result
        assert result.full_name == "Updated Name"
        assert result.notes == "Updated notes"
        assert result.ssn == "123-45-6789"  # Unchanged
        assert result.updated_by == user.user_id
        assert result.updated_at is not None

    @pytest.mark.asyncio
    async def test_update_client_not_found(self, test_session: Session) -> None:
        """Test client update with non-existent ID raises NotFoundError."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Update data

        update_data = ClientUpdate(full_name="Updated Name")

        # Try to update non-existent client
        non_existent_id = uuid4()

        with pytest.raises(NotFoundError) as exc_info:
            await service.update_client(non_existent_id, update_data, user.user_id, mock_request)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_client_ssn_duplicate(self, test_session: Session) -> None:
        """Test client update with duplicate SSN raises ConflictError."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)

        # Create two test clients
        client1_id = uuid4()
        client1 = Client(
            client_id=client1_id,
            full_name="Client 1",
            ssn="111-11-1111",
            birth_date=date(1990, 1, 1),
            status="active",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )

        client2_id = uuid4()
        client2 = Client(
            client_id=client2_id,
            full_name="Client 2",
            ssn="222-22-2222",
            birth_date=date(1991, 2, 2),
            status="active",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )

        test_session.add_all([client1, client2])
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Try to update client2's SSN to match client1's SSN

        update_data = ClientUpdate(ssn="111-11-1111")

        with pytest.raises(ConflictError) as exc_info:
            await service.update_client(client2_id, update_data, user.user_id, mock_request)

        assert "already exists" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_client_partial_fields(self, test_session: Session) -> None:
        """Test client update with partial field updates."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)

        # Create test client
        client_id = uuid4()
        original_birth_date = date(1990, 1, 1)
        test_client = Client(
            client_id=client_id,
            full_name="Original Name",
            ssn="123-45-6789",
            birth_date=original_birth_date,
            status="active",
            notes="Original notes",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )
        test_session.add(test_client)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Update only birth_date

        update_data = ClientUpdate(birth_date=date(1985, 6, 15))

        result = await service.update_client(client_id, update_data, user.user_id, mock_request)

        # Verify only birth_date changed, other fields unchanged
        assert result.full_name == "Original Name"  # Unchanged
        assert result.ssn == "123-45-6789"  # Unchanged
        assert result.notes == "Original notes"  # Unchanged
        assert result.birth_date == date(1985, 6, 15)  # Changed

    @patch("src.services.client_service.log_database_action")
    @pytest.mark.asyncio
    async def test_update_client_audit_logging(
        self, mock_log_action: Mock, test_session: Session
    ) -> None:
        """Test that audit logging is called during client update."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)

        # Create test client
        client_id = uuid4()
        test_client = Client(
            client_id=client_id,
            full_name="Original Name",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            status="active",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )
        test_session.add(test_client)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Update data

        update_data = ClientUpdate(full_name="Updated Name")

        # Update client
        await service.update_client(client_id, update_data, user.user_id, mock_request)

        # Verify audit logging was called
        mock_log_action.assert_called_once()
        call_args = mock_log_action.call_args

        # Verify audit log parameters
        assert call_args[1]["table_name"] == "clients"
        assert call_args[1]["record_id"] == str(client_id)
        assert call_args[1]["action"] == "UPDATE"
        assert call_args[1]["user_id"] == user.user_id
        assert call_args[1]["old_data"] is not None
        assert call_args[1]["new_data"] is not None


class TestClientServiceDelete:
    """Test ClientService.delete_client method."""

    @pytest.mark.asyncio
    async def test_delete_client_success(self, test_session: Session) -> None:
        """Test successful client soft deletion."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)

        # Create test client
        client_id = uuid4()
        test_client = Client(
            client_id=client_id,
            full_name="Test Client",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            status="active",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )
        test_session.add(test_client)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Delete client
        result = await service.delete_client(client_id, user.user_id, mock_request)

        # Verify result
        assert result is True

        # Verify client is soft-deleted (archived)

        db_client = test_session.exec(select(Client).where(Client.client_id == client_id)).first()
        assert db_client is not None
        assert db_client.status == "archived"
        assert db_client.updated_by == user.user_id
        assert db_client.updated_at is not None

    @pytest.mark.asyncio
    async def test_delete_client_not_found(self, test_session: Session) -> None:
        """Test client deletion with non-existent ID raises NotFoundError."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Try to delete non-existent client
        non_existent_id = uuid4()

        with pytest.raises(NotFoundError) as exc_info:
            await service.delete_client(non_existent_id, user.user_id, mock_request)

        assert "not found" in str(exc_info.value).lower()

    @patch("src.services.client_service.log_database_action")
    @pytest.mark.asyncio
    async def test_delete_client_audit_logging(
        self, mock_log_action: Mock, test_session: Session
    ) -> None:
        """Test that audit logging is called during client deletion."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)

        # Create test client
        client_id = uuid4()
        test_client = Client(
            client_id=client_id,
            full_name="Test Client",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            status="active",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )
        test_session.add(test_client)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Delete client
        await service.delete_client(client_id, user.user_id, mock_request)

        # Verify audit logging was called
        mock_log_action.assert_called_once()
        call_args = mock_log_action.call_args

        # Verify audit log parameters
        assert call_args[1]["table_name"] == "clients"
        assert call_args[1]["record_id"] == str(client_id)
        assert call_args[1]["action"] == "DELETE"
        assert call_args[1]["user_id"] == user.user_id
        assert call_args[1]["old_data"] is not None
        assert call_args[1]["new_data"] is not None


class TestClientServiceList:
    """Test ClientService.list_clients method."""

    @pytest.mark.asyncio
    async def test_list_clients_success(self, test_session: Session) -> None:
        """Test successful client listing with pagination."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)

        # Create test clients
        clients = []
        for i in range(5):
            client = Client(
                client_id=uuid4(),
                full_name=f"Test Client {i + 1}",
                ssn=f"12{i}-45-678{i}",
                birth_date=date(1990, 1, i + 1),
                status="active",
                created_by=user.user_id,
                updated_by=user.user_id,
                created_at=datetime.utcnow(),
            )
            clients.append(client)
            test_session.add(client)

        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Search parameters

        search_params = ClientSearchParams()

        # List clients with pagination
        result_clients, pagination_info = await service.list_clients(
            search_params, page=1, per_page=3, user_id=user.user_id, request=mock_request
        )

        # Verify results
        assert len(result_clients) == 3  # First page with 3 items
        assert pagination_info["page"] == 1
        assert pagination_info["per_page"] == 3
        assert pagination_info["total"] == 5
        assert pagination_info["total_pages"] == 2
        assert pagination_info["has_next"] is True
        assert pagination_info["has_prev"] is False

    @pytest.mark.asyncio
    async def test_list_clients_with_name_filter(self, test_session: Session) -> None:
        """Test client listing with name filter."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)

        # Create test clients with different names
        client1 = Client(
            client_id=uuid4(),
            full_name="John Doe",
            ssn="111-11-1111",
            birth_date=date(1990, 1, 1),
            status="active",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )

        client2 = Client(
            client_id=uuid4(),
            full_name="Jane Smith",
            ssn="222-22-2222",
            birth_date=date(1991, 2, 2),
            status="active",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )

        client3 = Client(
            client_id=uuid4(),
            full_name="John Johnson",
            ssn="333-33-3333",
            birth_date=date(1992, 3, 3),
            status="active",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )

        test_session.add_all([client1, client2, client3])
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Search for clients with "John" in name

        search_params = ClientSearchParams(full_name="john")

        result_clients, pagination_info = await service.list_clients(
            search_params, page=1, per_page=10, user_id=user.user_id, request=mock_request
        )

        # Verify results - should find 2 clients with "John" in name
        assert len(result_clients) == 2
        assert pagination_info["total"] == 2
        client_names = [client.full_name for client in result_clients]
        assert "John Doe" in client_names
        assert "John Johnson" in client_names
        assert "Jane Smith" not in client_names

    @pytest.mark.asyncio
    async def test_list_clients_with_status_filter(self, test_session: Session) -> None:
        """Test client listing with status filter."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)

        # Create test clients with different statuses

        active_client = Client(
            client_id=uuid4(),
            full_name="Active Client",
            ssn="111-11-1111",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )

        inactive_client = Client(
            client_id=uuid4(),
            full_name="Inactive Client",
            ssn="222-22-2222",
            birth_date=date(1991, 2, 2),
            status=ClientStatus.INACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )

        test_session.add_all([active_client, inactive_client])
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Search for active clients only

        search_params = ClientSearchParams(status=ClientStatus.ACTIVE)

        result_clients, pagination_info = await service.list_clients(
            search_params, page=1, per_page=10, user_id=user.user_id, request=mock_request
        )

        # Verify results - should find only active client
        assert len(result_clients) == 1
        assert pagination_info["total"] == 1
        assert result_clients[0].full_name == "Active Client"
        assert result_clients[0].status == ClientStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_list_clients_empty_results(self, test_session: Session) -> None:
        """Test client listing with no matching results."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Search parameters

        search_params = ClientSearchParams()

        # List clients (no clients exist)
        result_clients, pagination_info = await service.list_clients(
            search_params, page=1, per_page=10, user_id=user.user_id, request=mock_request
        )

        # Verify empty results
        assert len(result_clients) == 0
        assert pagination_info["total"] == 0
        assert pagination_info["total_pages"] == 0
        assert pagination_info["has_next"] is False
        assert pagination_info["has_prev"] is False

    @patch("src.services.client_service.log_database_action")
    @pytest.mark.asyncio
    async def test_list_clients_audit_logging(
        self, mock_log_action: Mock, test_session: Session
    ) -> None:
        """Test that audit logging is called during client listing."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Search parameters

        search_params = ClientSearchParams()

        # List clients
        await service.list_clients(
            search_params, page=1, per_page=10, user_id=user.user_id, request=mock_request
        )

        # Verify audit logging was called
        mock_log_action.assert_called_once()
        call_args = mock_log_action.call_args

        # Verify audit log parameters
        assert call_args[1]["table_name"] == "clients"
        assert call_args[1]["record_id"] == "list_operation"
        assert call_args[1]["action"] == "VIEW"
        assert call_args[1]["user_id"] == user.user_id


class TestClientServiceSSNValidation:
    """Test ClientService SSN validation edge cases."""

    @pytest.mark.asyncio
    async def test_check_ssn_uniqueness_direct(self, test_session: Session) -> None:
        """Test _check_ssn_uniqueness method directly."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)

        # Create existing client
        existing_client = Client(
            client_id=uuid4(),
            full_name="Existing Client",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            status="active",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )
        test_session.add(existing_client)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Test SSN uniqueness check for duplicate SSN
        with pytest.raises(ConflictError) as exc_info:
            await service._check_ssn_uniqueness("123-45-6789")

        assert "already exists" in str(exc_info.value).lower()
        assert exc_info.value.error_code == "SSN_DUPLICATE"

    @pytest.mark.asyncio
    async def test_check_ssn_uniqueness_with_exclusion(self, test_session: Session) -> None:
        """Test _check_ssn_uniqueness method with client exclusion for updates."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)

        # Create existing client
        client_id = uuid4()
        existing_client = Client(
            client_id=client_id,
            full_name="Existing Client",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            status="active",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )
        test_session.add(existing_client)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Test SSN uniqueness check excluding the same client (should pass)
        try:
            await service._check_ssn_uniqueness("123-45-6789", exclude_client_id=client_id)
        except ConflictError:
            pytest.fail("SSN uniqueness check should pass when excluding the same client")

    @pytest.mark.asyncio
    async def test_check_ssn_uniqueness_unique_ssn(self, test_session: Session) -> None:
        """Test _check_ssn_uniqueness method with unique SSN."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Test SSN uniqueness check for unique SSN (should pass)
        try:
            await service._check_ssn_uniqueness("999-99-9999")
        except ConflictError:
            pytest.fail("SSN uniqueness check should pass for unique SSN")


class TestClientServiceErrorHandlingExtended:
    """Test additional error handling scenarios in ClientService."""

    @pytest.mark.asyncio
    async def test_update_client_database_error(self, test_session: Session) -> None:
        """Test handling of database errors during client update."""
        # Create test user and client
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)

        client_id = uuid4()
        test_client = Client(
            client_id=client_id,
            full_name="Test Client",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            status="active",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )
        test_session.add(test_client)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Update data

        update_data = ClientUpdate(full_name="Updated Name")

        # Mock session to raise SQLAlchemy error
        with (
            patch.object(test_session, "commit", side_effect=SQLAlchemyError("Database error")),
            pytest.raises(DatabaseError),
        ):
            await service.update_client(client_id, update_data, user.user_id, mock_request)

    @pytest.mark.asyncio
    async def test_delete_client_database_error(self, test_session: Session) -> None:
        """Test handling of database errors during client deletion."""
        # Create test user and client
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)

        client_id = uuid4()
        test_client = Client(
            client_id=client_id,
            full_name="Test Client",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            status="active",
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )
        test_session.add(test_client)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Mock session to raise SQLAlchemy error
        with (
            patch.object(test_session, "commit", side_effect=SQLAlchemyError("Database error")),
            pytest.raises(DatabaseError),
        ):
            await service.delete_client(client_id, user.user_id, mock_request)

    @pytest.mark.asyncio
    async def test_list_clients_database_error(self, test_session: Session) -> None:
        """Test handling of database errors during client listing."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Search parameters

        search_params = ClientSearchParams()

        # Mock session to raise SQLAlchemy error
        with (
            patch.object(test_session, "exec", side_effect=SQLAlchemyError("Database error")),
            pytest.raises(DatabaseError),
        ):
            await service.list_clients(
                search_params, page=1, per_page=10, user_id=user.user_id, request=mock_request
            )

    @pytest.mark.asyncio
    async def test_get_client_by_id_database_error(self, test_session: Session) -> None:
        """Test handling of database errors during client retrieval."""
        # Create test user
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.ADMIN,
            is_active=True,
            totp_enabled=False,
        )
        test_session.add(user)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Mock session to raise SQLAlchemy error
        client_id = uuid4()
        with (
            patch.object(test_session, "exec", side_effect=SQLAlchemyError("Database error")),
            pytest.raises(DatabaseError),
        ):
            await service.get_client_by_id(client_id, user.user_id, mock_request)
