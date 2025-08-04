"""
Additional tests for ClientService update and delete operations.

This module provides comprehensive test coverage for the update and delete
functionality in the ClientService class.
"""

from datetime import date, datetime
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi import Request
from sqlmodel import Session

from src.core.exceptions import ConflictError, NotFoundError
from src.models.client import Client, ClientStatus, ClientUpdate
from src.models.user import User, UserRole
from src.services.client_service import ClientService


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
            status=ClientStatus.ACTIVE,
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
        update_data = ClientUpdate(full_name="Updated Name", notes="Updated notes")

        # Update client
        result = await service.update_client(client_id, update_data, user.user_id, mock_request)

        # Verify result
        assert result.full_name == "Updated Name"
        assert result.notes == "Updated notes"
        assert result.ssn == "123-45-6789"  # Unchanged
        assert result.birth_date == date(1990, 1, 1)  # Unchanged
        assert result.updated_by == user.user_id
        assert result.updated_at is not None

        # Verify in database
        db_client = test_session.query(Client).filter(Client.client_id == client_id).first()
        assert db_client.full_name == "Updated Name"
        assert db_client.notes == "Updated notes"

    @pytest.mark.asyncio
    async def test_update_client_not_found(self, test_session: Session) -> None:
        """Test update client with non-existent ID raises NotFoundError."""
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

        # Try to update non-existent client
        non_existent_id = uuid4()
        update_data = ClientUpdate(full_name="New Name")

        with pytest.raises(NotFoundError) as exc_info:
            await service.update_client(non_existent_id, update_data, user.user_id, mock_request)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_client_ssn_conflict(self, test_session: Session) -> None:
        """Test update client with duplicate SSN raises ConflictError."""
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
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )

        client2_id = uuid4()
        client2 = Client(
            client_id=client2_id,
            full_name="Client 2",
            ssn="987-65-4321",
            birth_date=date(1985, 6, 15),
            status=ClientStatus.ACTIVE,
            created_by=user.user_id,
            updated_by=user.user_id,
            created_at=datetime.utcnow(),
        )

        test_session.add(client1)
        test_session.add(client2)
        test_session.commit()

        # Create client service
        service = ClientService(test_session)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        # Try to update client2 with client1's SSN
        update_data = ClientUpdate(ssn="123-45-6789")

        with pytest.raises(ConflictError) as exc_info:
            await service.update_client(client2_id, update_data, user.user_id, mock_request)

        assert "already exists" in str(exc_info.value).lower()

    @patch("src.services.client_service.log_database_action")
    @pytest.mark.asyncio
    async def test_update_client_audit_logging(
        self, mock_log_action, test_session: Session
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
            full_name="Test Client",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
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


class TestClientServiceDelete:
    """Test ClientService.delete_client method."""

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
        client_id = uuid4()
        test_client = Client(
            client_id=client_id,
            full_name="Test Client",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
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

        # Verify client is archived (soft deleted)
        db_client = test_session.query(Client).filter(Client.client_id == client_id).first()
        assert db_client is not None
        assert db_client.status == ClientStatus.ARCHIVED
        assert db_client.updated_by == user.user_id
        assert db_client.updated_at is not None

    @pytest.mark.asyncio
    async def test_delete_client_not_found(self, test_session: Session) -> None:
        """Test delete client with non-existent ID raises NotFoundError."""
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
        self, mock_log_action, test_session: Session
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
            status=ClientStatus.ACTIVE,
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
