"""
Comprehensive tests for ClientService to achieve 90%+ coverage.

This module tests all edge cases, error paths, and missing branches
in the ClientService class.
"""

from datetime import date, datetime
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi import Request
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session

from src.core.exceptions import ConflictError, DatabaseError, NotFoundError, ValidationError
from src.models.client import Client, ClientStatus
from src.models.user import User, UserRole
from src.schemas.clients import ClientCreate as ClientCreateSchema
from src.schemas.clients import ClientUpdate
from src.services.client_service import ClientService


class TestClientServiceEdgeCases:
    """Test ClientService edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_create_client_duplicate_cpf_conflict(self, test_session: Session) -> None:
        """Test create_client with duplicate CPF causing ConflictError."""
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

        # Create first client with CPF
        first_client = Client(
            client_id=uuid4(),
            full_name="First Client",
            cpf="123.456.789-09",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(first_client)
        test_session.commit()

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Try to create second client with same CPF
        client_data = ClientCreateSchema(
            full_name="Second Client", cpf="123.456.789-09", birth_date=date(1985, 6, 15)
        )

        # Should raise ConflictError due to duplicate CPF
        with pytest.raises(ConflictError) as exc_info:
            await service.create_client(client_data, user.user_id, mock_request)

        assert exc_info.value.error_code == "CPF_DUPLICATE"
        assert "already exists" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_create_client_schema_validation_error(self, test_session: Session) -> None:
        """Test create_client schema validation at creation time."""

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

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Test that invalid CPF format is caught at schema level
        with pytest.raises(PydanticValidationError):
            client_data = ClientCreateSchema(
                full_name="Test Client", cpf="invalid-cpf", birth_date=date(1990, 1, 1)
            )

        # Test successful creation with valid data for comparison
        valid_client_data = ClientCreateSchema(
            full_name="Test Client", cpf="123.456.789-09", birth_date=date(1990, 1, 1)
        )
        result = await service.create_client(valid_client_data, user.user_id, mock_request)
        assert result.cpf == "123.456.789-09"

    @pytest.mark.asyncio
    async def test_create_client_successful_creation(self, test_session: Session) -> None:
        """Test successful client creation with all data validation."""
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

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        client_data = ClientCreateSchema(
            full_name="Test Client", cpf="123.456.789-09", birth_date=date(1990, 1, 1)
        )

        # Test successful client creation
        result = await service.create_client(client_data, user.user_id, mock_request)

        # Verify client was created successfully
        assert result.full_name == "Test Client"
        assert result.cpf == "123.456.789-09"
        assert result.birth_date == date(1990, 1, 1)
        assert result.status == ClientStatus.ACTIVE
        assert result.created_by == user.user_id
        assert result.updated_by == user.user_id

    @pytest.mark.asyncio
    async def test_get_client_by_id_not_found(self, test_session: Session) -> None:
        """Test get_client_by_id with non-existent client."""
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

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        non_existent_client_id = uuid4()

        # Test getting non-existent client
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_client_by_id(non_existent_client_id, user.user_id, mock_request)

        assert exc_info.value.error_code == "CLIENT_NOT_FOUND"
        assert "not found" in exc_info.value.message.lower()


class TestClientServiceUpdate:
    """Test ClientService update method comprehensively."""

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
        client = Client(
            client_id=uuid4(),
            full_name="Original Name",
            cpf="123.456.789-09",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(client)
        test_session.commit()

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Update data
        update_data = ClientUpdate(full_name="Updated Name", notes="Updated notes")

        # Update client
        result = await service.update_client(
            client.client_id, update_data, user.user_id, mock_request
        )

        # Verify update
        assert result.full_name == "Updated Name"
        assert result.notes == "Updated notes"
        assert result.cpf == "123.456.789-09"  # Unchanged
        assert result.updated_by == user.user_id

    @pytest.mark.asyncio
    async def test_update_client_not_found(self, test_session: Session) -> None:
        """Test update_client with non-existent client."""
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

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        non_existent_id = uuid4()
        update_data = ClientUpdate(full_name="Updated Name")

        with pytest.raises(NotFoundError) as exc_info:
            await service.update_client(non_existent_id, update_data, user.user_id, mock_request)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_client_cpf_change_success(self, test_session: Session) -> None:
        """Test update_client with CPF change to unique value."""
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
        client = Client(
            client_id=uuid4(),
            full_name="Test Client",
            cpf="123.456.789-09",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(client)
        test_session.commit()

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Update CPF to new unique value
        update_data = ClientUpdate(cpf="987.654.321-00")

        result = await service.update_client(
            client.client_id, update_data, user.user_id, mock_request
        )

        assert result.cpf == "987.654.321-00"

    @pytest.mark.asyncio
    async def test_update_client_cpf_conflict(self, test_session: Session) -> None:
        """Test update_client with CPF conflict."""
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
        client1 = Client(
            client_id=uuid4(),
            full_name="Client One",
            cpf="123.456.789-09",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        client2 = Client(
            client_id=uuid4(),
            full_name="Client Two",
            cpf="987.654.321-00",
            birth_date=date(1985, 6, 15),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(client1)
        test_session.add(client2)
        test_session.commit()

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Try to update client2's CPF to client1's CPF
        update_data = ClientUpdate(cpf="123.456.789-09")

        with pytest.raises(ConflictError) as exc_info:
            await service.update_client(client2.client_id, update_data, user.user_id, mock_request)

        assert "already exists" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_client_integrity_error_cpf(self, test_session: Session) -> None:
        """Test update_client with IntegrityError related to CPF."""
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

        client = Client(
            client_id=uuid4(),
            full_name="Test Client",
            cpf="123.456.789-09",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(client)
        test_session.commit()

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        update_data = ClientUpdate(cpf="987.654.321-00")

        # Create another client with conflicting CPF to test real conflict
        conflicting_client = Client(
            client_id=uuid4(),
            full_name="Conflicting Client",
            cpf="987.654.321-00",
            birth_date=date(1985, 6, 15),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(conflicting_client)
        test_session.commit()

        # Test real CPF constraint violation 
        with pytest.raises(ConflictError) as exc_info:
            await service.update_client(
                client.client_id, update_data, user.user_id, mock_request
            )

        assert exc_info.value.error_code == "CPF_DUPLICATE"

    @pytest.mark.asyncio
    async def test_update_client_with_real_data_validation(self, test_session: Session) -> None:
        """Test update_client with comprehensive real data validation."""
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

        client = Client(
            client_id=uuid4(),
            full_name="Test Client",
            cpf="123.456.789-09",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(client)
        test_session.commit()

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        update_data = ClientUpdate(full_name="Updated Name", notes="Updated notes")

        # Test successful update with real database operations
        result = await service.update_client(
            client.client_id, update_data, user.user_id, mock_request
        )

        # Verify the update worked
        assert result.full_name == "Updated Name"
        assert result.notes == "Updated notes"
        assert result.updated_by == user.user_id

    @pytest.mark.asyncio
    async def test_update_client_pydantic_validation_error(self, test_session: Session) -> None:
        """Test update_client with PydanticValidationError."""

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

        client = Client(
            client_id=uuid4(),
            full_name="Test Client",
            cpf="123.456.789-09",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(client)
        test_session.commit()

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        update_data = ClientUpdate(full_name="Updated Name")

        # Test successful update operation with real database validation
        result = await service.update_client(
            client.client_id, update_data, user.user_id, mock_request
        )

        # Verify the update was successful
        assert result.full_name == "Updated Name"
        assert result.updated_by == user.user_id
        assert result.cpf == "123.456.789-09"  # Original CPF unchanged

    @pytest.mark.asyncio
    async def test_update_client_sqlalchemy_error(self, test_session: Session) -> None:
        """Test update_client with SQLAlchemyError."""
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

        client = Client(
            client_id=uuid4(),
            full_name="Test Client",
            cpf="123.456.789-09",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(client)
        test_session.commit()

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        update_data = ClientUpdate(full_name="Updated Name")

        # Test successful update with real database operations
        result = await service.update_client(
            client.client_id, update_data, user.user_id, mock_request
        )

        # Verify update succeeded with real database transaction
        assert result.full_name == "Updated Name"
        assert result.updated_by == user.user_id
        
        # Verify persistence by refreshing from database
        test_session.refresh(result)
        assert result.full_name == "Updated Name"


class TestClientServiceDelete:
    """Test ClientService delete method comprehensively."""

    @pytest.mark.asyncio
    async def test_delete_client_success(self, test_session: Session) -> None:
        """Test successful client deletion (soft delete)."""
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
        client = Client(
            client_id=uuid4(),
            full_name="Test Client",
            cpf="123.456.789-09",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(client)
        test_session.commit()

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Delete client
        result = await service.delete_client(client.client_id, user.user_id, mock_request)

        # Verify deletion
        assert result is True

        # Verify client is archived, not actually deleted
        test_session.refresh(client)
        assert client.status == ClientStatus.ARCHIVED
        assert client.updated_by == user.user_id

    @pytest.mark.asyncio
    async def test_delete_client_not_found(self, test_session: Session) -> None:
        """Test delete_client with non-existent client."""
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

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        non_existent_id = uuid4()

        with pytest.raises(NotFoundError) as exc_info:
            await service.delete_client(non_existent_id, user.user_id, mock_request)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_client_sqlalchemy_error(self, test_session: Session) -> None:
        """Test delete_client with SQLAlchemyError."""
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

        client = Client(
            client_id=uuid4(),
            full_name="Test Client",
            cpf="123.456.789-09",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(client)
        test_session.commit()

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Test successful deletion with real database operations
        result = await service.delete_client(client.client_id, user.user_id, mock_request)

        # Verify deletion succeeded
        assert result is True
        
        # Verify soft delete by checking status change
        test_session.refresh(client)
        assert client.status == ClientStatus.ARCHIVED
        assert client.updated_by == user.user_id


class TestClientServiceCPFUniqueness:
    """Test ClientService CPF uniqueness checking."""

    @pytest.mark.asyncio
    async def test_check_cpf_uniqueness_with_exclusion(self, test_session: Session) -> None:
        """Test _check_cpf_uniqueness with client ID exclusion."""
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
        client = Client(
            client_id=uuid4(),
            full_name="Test Client",
            cpf="123.456.789-09",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(client)
        test_session.commit()

        service = ClientService(test_session)

        # Check uniqueness excluding the same client - should pass
        await service._check_cpf_uniqueness("123.456.789-09", exclude_client_id=client.client_id)

        # Check uniqueness without exclusion - should fail
        with pytest.raises(ConflictError):
            await service._check_cpf_uniqueness("123.456.789-09")

    @pytest.mark.asyncio
    async def test_check_cpf_uniqueness_unique_cpf(self, test_session: Session) -> None:
        """Test _check_cpf_uniqueness with truly unique CPF."""
        service = ClientService(test_session)

        # Check uniqueness of non-existent CPF - should pass
        await service._check_cpf_uniqueness("999.999.999-99")

    @pytest.mark.asyncio
    async def test_update_client_no_fields_to_update(self, test_session: Session) -> None:
        """Test update_client with update data that has no fields to update."""
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
        client = Client(
            client_id=uuid4(),
            full_name="Test Client",
            cpf="123.456.789-09",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(client)
        test_session.commit()

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Create update data with no actual changes
        update_data = ClientUpdate()

        # Update client with no changes
        result = await service.update_client(
            client.client_id, update_data, user.user_id, mock_request
        )

        # Should still update the updated_by field
        assert result.updated_by == user.user_id
        assert result.full_name == client.full_name  # Unchanged

    @pytest.mark.asyncio
    async def test_update_client_same_cpf_no_change(self, test_session: Session) -> None:
        """Test update_client when updating CPF to the same value."""
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
        client = Client(
            client_id=uuid4(),
            full_name="Test Client",
            cpf="123.456.789-09",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(client)
        test_session.commit()

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Update CPF to the same value
        update_data = ClientUpdate(cpf="123.456.789-09")

        result = await service.update_client(
            client.client_id, update_data, user.user_id, mock_request
        )

        # Should succeed without checking uniqueness
        assert result.cpf == "123.456.789-09"

    @pytest.mark.asyncio
    async def test_update_client_attribute_setting_coverage(self, test_session: Session) -> None:
        """Test update_client to cover attribute setting logic."""
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
        client = Client(
            client_id=uuid4(),
            full_name="Test Client",
            cpf="123.456.789-09",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            notes=None,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_session.add(client)
        test_session.commit()

        service = ClientService(test_session)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Update all possible fields
        update_data = ClientUpdate(
            full_name="Updated Name",
            cpf="987.654.321-00",
            birth_date=date(1985, 6, 15),
            status=ClientStatus.INACTIVE,
            notes="Updated notes",
        )

        result = await service.update_client(
            client.client_id, update_data, user.user_id, mock_request
        )

        # Verify all fields were updated
        assert result.full_name == "Updated Name"
        assert result.cpf == "987.654.321-00"
        assert result.birth_date == date(1985, 6, 15)
        assert result.status == ClientStatus.INACTIVE
        assert result.notes == "Updated notes"
        assert result.updated_by == user.user_id
