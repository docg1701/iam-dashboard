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
    async def test_create_client_integrity_error_non_ssn(self, test_session: Session) -> None:
        """Test create_client with IntegrityError not related to SSN."""
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
            full_name="Test Client", ssn="123-45-6789", birth_date=date(1990, 1, 1)
        )

        # Mock IntegrityError without "ssn" in the message
        with patch.object(
            test_session,
            "commit",
            side_effect=IntegrityError(
                "other constraint", {}, SQLAlchemyError("other constraint violation")
            ),
        ):
            with pytest.raises(DatabaseError) as exc_info:
                await service.create_client(client_data, user.user_id, mock_request)

            assert exc_info.value.error_code == "CONSTRAINT_VIOLATION"
            assert "constraint" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_create_client_pydantic_validation_error(self, test_session: Session) -> None:
        """Test create_client with PydanticValidationError."""

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
            full_name="Test Client", ssn="123-45-6789", birth_date=date(1990, 1, 1)
        )

        # Mock PydanticValidationError during session operations
        with patch.object(
            test_session, "add", side_effect=PydanticValidationError("Mock validation error", [])
        ):
            with pytest.raises(ValidationError) as exc_info:
                await service.create_client(client_data, user.user_id, mock_request)

            assert exc_info.value.error_code == "VALIDATION_ERROR"
            assert "validation failed" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_create_client_general_sqlalchemy_error(self, test_session: Session) -> None:
        """Test create_client with general SQLAlchemyError."""
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
            full_name="Test Client", ssn="123-45-6789", birth_date=date(1990, 1, 1)
        )

        # Mock SQLAlchemyError during session operations
        with patch.object(test_session, "commit", side_effect=SQLAlchemyError("Database error")):
            with pytest.raises(DatabaseError) as exc_info:
                await service.create_client(client_data, user.user_id, mock_request)

            assert exc_info.value.error_code == "DATABASE_ERROR"
            assert "Database operation failed" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_get_client_by_id_sqlalchemy_error(self, test_session: Session) -> None:
        """Test get_client_by_id with SQLAlchemyError."""
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

        client_id = uuid4()

        # Mock SQLAlchemyError during database query
        with patch.object(
            test_session, "exec", side_effect=SQLAlchemyError("Database query error")
        ):
            with pytest.raises(DatabaseError) as exc_info:
                await service.get_client_by_id(client_id, user.user_id, mock_request)

            assert exc_info.value.error_code == "DATABASE_ERROR"
            assert "Database operation failed during client retrieval" in exc_info.value.message


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
            ssn="123-45-6789",
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
        assert result.ssn == "123-45-6789"  # Unchanged
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
    async def test_update_client_ssn_change_success(self, test_session: Session) -> None:
        """Test update_client with SSN change to unique value."""
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
            ssn="123-45-6789",
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

        # Update SSN to new unique value
        update_data = ClientUpdate(ssn="987-65-4321")

        result = await service.update_client(
            client.client_id, update_data, user.user_id, mock_request
        )

        assert result.ssn == "987-65-4321"

    @pytest.mark.asyncio
    async def test_update_client_ssn_conflict(self, test_session: Session) -> None:
        """Test update_client with SSN conflict."""
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
            ssn="123-45-6789",
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
            ssn="987-65-4321",
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

        # Try to update client2's SSN to client1's SSN
        update_data = ClientUpdate(ssn="123-45-6789")

        with pytest.raises(ConflictError) as exc_info:
            await service.update_client(client2.client_id, update_data, user.user_id, mock_request)

        assert "already exists" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_client_integrity_error_ssn(self, test_session: Session) -> None:
        """Test update_client with IntegrityError related to SSN."""
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
            ssn="123-45-6789",
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

        update_data = ClientUpdate(ssn="987-65-4321")

        # Mock IntegrityError with "ssn" in the message
        orig_exception = SQLAlchemyError("ssn constraint violation")
        mock_error = IntegrityError("ssn constraint", {}, orig_exception)
        mock_error.orig = orig_exception
        with patch.object(test_session, "commit", side_effect=mock_error):
            with pytest.raises(ConflictError) as exc_info:
                await service.update_client(
                    client.client_id, update_data, user.user_id, mock_request
                )

            assert exc_info.value.error_code == "SSN_DUPLICATE"

    @pytest.mark.asyncio
    async def test_update_client_integrity_error_non_ssn(self, test_session: Session) -> None:
        """Test update_client with IntegrityError not related to SSN."""
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
            ssn="123-45-6789",
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

        # Mock IntegrityError without "ssn" in the message
        with patch.object(
            test_session,
            "commit",
            side_effect=IntegrityError(
                "other constraint", {}, SQLAlchemyError("other constraint violation")
            ),
        ):
            with pytest.raises(DatabaseError) as exc_info:
                await service.update_client(
                    client.client_id, update_data, user.user_id, mock_request
                )

            assert exc_info.value.error_code == "CONSTRAINT_VIOLATION"

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
            ssn="123-45-6789",
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

        # Mock PydanticValidationError during update
        with patch.object(
            ClientUpdate,
            "model_dump",
            side_effect=PydanticValidationError("Mock validation error", []),
        ):
            with pytest.raises(ValidationError) as exc_info:
                await service.update_client(
                    client.client_id, update_data, user.user_id, mock_request
                )

            assert exc_info.value.error_code == "VALIDATION_ERROR"

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
            ssn="123-45-6789",
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

        # Mock SQLAlchemyError during update
        with patch.object(test_session, "commit", side_effect=SQLAlchemyError("Database error")):
            with pytest.raises(DatabaseError) as exc_info:
                await service.update_client(
                    client.client_id, update_data, user.user_id, mock_request
                )

            assert exc_info.value.error_code == "DATABASE_ERROR"


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
            ssn="123-45-6789",
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
            ssn="123-45-6789",
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

        # Mock SQLAlchemyError during deletion
        with patch.object(test_session, "commit", side_effect=SQLAlchemyError("Database error")):
            with pytest.raises(DatabaseError) as exc_info:
                await service.delete_client(client.client_id, user.user_id, mock_request)

            assert exc_info.value.error_code == "DATABASE_ERROR"
            assert "Database operation failed during client deletion" in exc_info.value.message


class TestClientServiceSSNUniqueness:
    """Test ClientService SSN uniqueness checking."""

    @pytest.mark.asyncio
    async def test_check_ssn_uniqueness_with_exclusion(self, test_session: Session) -> None:
        """Test _check_ssn_uniqueness with client ID exclusion."""
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
            ssn="123-45-6789",
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
        await service._check_ssn_uniqueness("123-45-6789", exclude_client_id=client.client_id)

        # Check uniqueness without exclusion - should fail
        with pytest.raises(ConflictError):
            await service._check_ssn_uniqueness("123-45-6789")

    @pytest.mark.asyncio
    async def test_check_ssn_uniqueness_unique_ssn(self, test_session: Session) -> None:
        """Test _check_ssn_uniqueness with truly unique SSN."""
        service = ClientService(test_session)

        # Check uniqueness of non-existent SSN - should pass
        await service._check_ssn_uniqueness("999-99-9999")

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
            ssn="123-45-6789",
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
    async def test_update_client_same_ssn_no_change(self, test_session: Session) -> None:
        """Test update_client when updating SSN to the same value."""
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
            ssn="123-45-6789",
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

        # Update SSN to the same value
        update_data = ClientUpdate(ssn="123-45-6789")

        result = await service.update_client(
            client.client_id, update_data, user.user_id, mock_request
        )

        # Should succeed without checking uniqueness
        assert result.ssn == "123-45-6789"

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
            ssn="123-45-6789",
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
            ssn="987-65-4321",
            birth_date=date(1985, 6, 15),
            status=ClientStatus.INACTIVE,
            notes="Updated notes",
        )

        result = await service.update_client(
            client.client_id, update_data, user.user_id, mock_request
        )

        # Verify all fields were updated
        assert result.full_name == "Updated Name"
        assert result.ssn == "987-65-4321"
        assert result.birth_date == date(1985, 6, 15)
        assert result.status == ClientStatus.INACTIVE
        assert result.notes == "Updated notes"
        assert result.updated_by == user.user_id
