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
from sqlmodel import Session

from src.core.exceptions import ConflictError, DatabaseError, NotFoundError, ValidationError
from src.models.client import Client
from src.models.user import User, UserRole
from src.schemas.clients import ClientCreate as ClientCreateSchema
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
        db_client = test_session.query(Client).filter(Client.client_id == result.client_id).first()
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
        self, mock_log_action, test_session: Session
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
        self, mock_log_action, test_session: Session
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
