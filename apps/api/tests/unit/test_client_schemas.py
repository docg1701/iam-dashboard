"""
Test cases for client schemas validation.

Tests all client-related Pydantic schemas to ensure proper validation
and serialization behavior.
"""

import uuid
from datetime import date, datetime

import pytest
from pydantic import ValidationError

from src.schemas.client import (
    ClientCreateRequest,
    ClientListResponse,
    ClientResponse,
    ClientUpdateRequest,
)


class TestClientCreateRequest:
    """Test cases for ClientCreateRequest schema."""

    def test_valid_client_creation(self):
        """Test valid client creation request."""
        request = ClientCreateRequest(
            name="João Silva Santos",
            cpf="11144477735",  # Valid CPF
            birth_date="1990-05-15",
        )

        assert request.name == "João Silva Santos"
        assert request.cpf == "11144477735"
        assert request.birth_date == date(1990, 5, 15)

    def test_name_validation(self):
        """Test name field validation."""
        # Test minimum length
        with pytest.raises(ValidationError) as exc_info:
            ClientCreateRequest(
                name="A",  # Too short
                cpf="11144477735",
                birth_date="1990-05-15",
            )
        assert "at least 2 characters" in str(exc_info.value)

        # Test maximum length
        with pytest.raises(ValidationError) as exc_info:
            ClientCreateRequest(
                name="A" * 101,  # Too long
                cpf="11144477735",
                birth_date="1990-05-15",
            )
        assert "at most 100 characters" in str(exc_info.value)

        # Test empty name
        with pytest.raises(ValidationError) as exc_info:
            ClientCreateRequest(name="", cpf="11144477735", birth_date="1990-05-15")
        assert "Name is required" in str(exc_info.value)

    def test_cpf_validation(self):
        """Test CPF field validation."""
        # Test invalid CPF (all same digits)
        with pytest.raises(ValidationError) as exc_info:
            ClientCreateRequest(
                name="Test User", cpf="11111111111", birth_date="1990-05-15"
            )
        assert "cannot be all the same digits" in str(exc_info.value)

        # Test wrong length
        with pytest.raises(ValidationError) as exc_info:
            ClientCreateRequest(
                name="Test User",
                cpf="123456789",  # Too short
                birth_date="1990-05-15",
            )
        assert "exactly 11 digits" in str(exc_info.value)

        # Test CPF with formatting (should be cleaned)
        request = ClientCreateRequest(
            name="Test User",
            cpf="111.444.777-35",  # With formatting
            birth_date="1990-05-15",
        )
        assert request.cpf == "11144477735"

    def test_birth_date_validation(self):
        """Test birth date field validation."""
        # Test future date
        with pytest.raises(ValidationError) as exc_info:
            ClientCreateRequest(
                name="Test User", cpf="11144477735", birth_date="2030-01-01"
            )
        assert "cannot be in the future" in str(exc_info.value)

        # Test minimum age (16 years)
        recent_date = date.today().replace(year=date.today().year - 15)
        with pytest.raises(ValidationError) as exc_info:
            ClientCreateRequest(
                name="Test User", cpf="11144477735", birth_date=recent_date.isoformat()
            )
        assert "at least 16 years old" in str(exc_info.value)


class TestClientUpdateRequest:
    """Test cases for ClientUpdateRequest schema."""

    def test_partial_update(self):
        """Test partial update with some fields."""
        request = ClientUpdateRequest(name="Updated Name", is_active=False)

        assert request.name == "Updated Name"
        assert request.cpf is None
        assert request.birth_date is None
        assert request.is_active is False

    def test_all_fields_none(self):
        """Test request with all fields as None."""
        request = ClientUpdateRequest()

        assert request.name is None
        assert request.cpf is None
        assert request.birth_date is None
        assert request.is_active is None

    def test_name_validation_when_provided(self):
        """Test name validation when field is provided."""
        with pytest.raises(ValidationError) as exc_info:
            ClientUpdateRequest(name="A")  # Too short
        assert "at least 2 characters" in str(exc_info.value)

    def test_cpf_validation_when_provided(self):
        """Test CPF validation when field is provided."""
        with pytest.raises(ValidationError) as exc_info:
            ClientUpdateRequest(cpf="11111111111")  # Invalid CPF
        assert "cannot be all the same digits" in str(exc_info.value)


class TestClientResponse:
    """Test cases for ClientResponse schema."""

    def test_valid_response(self):
        """Test valid client response."""
        client_id = uuid.uuid4()
        created_by_id = uuid.uuid4()
        now = datetime.now()

        response = ClientResponse(
            id=client_id,
            name="João Silva Santos",
            cpf="11144477735",
            birth_date=date(1990, 5, 15),
            created_by=created_by_id,
            created_at=now,
            updated_at=now,
            is_active=True,
        )

        assert response.id == client_id
        assert response.name == "João Silva Santos"
        assert response.cpf == "11144477735"
        assert response.birth_date == date(1990, 5, 15)
        assert response.created_by == created_by_id
        assert response.created_at == now
        assert response.updated_at == now
        assert response.is_active is True

    def test_from_attributes_config(self):
        """Test that response can be created from model attributes."""
        # This would typically be used with SQLModel instances
        # We simulate the behavior by using a dict
        data = {
            "id": uuid.uuid4(),
            "name": "Test Client",
            "cpf": "11144477735",
            "birth_date": date(1990, 1, 1),
            "created_by": uuid.uuid4(),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "is_active": True,
        }

        response = ClientResponse(**data)
        assert response.name == "Test Client"


class TestClientListResponse:
    """Test cases for ClientListResponse schema."""

    def test_valid_list_response(self):
        """Test valid client list response."""
        client_response = ClientResponse(
            id=uuid.uuid4(),
            name="Test Client",
            cpf="11144477735",
            birth_date=date(1990, 1, 1),
            created_by=uuid.uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True,
        )

        list_response = ClientListResponse(
            clients=[client_response], total=1, page=1, per_page=10, total_pages=1
        )

        assert len(list_response.clients) == 1
        assert list_response.total == 1
        assert list_response.page == 1
        assert list_response.per_page == 10
        assert list_response.total_pages == 1

    def test_empty_list_response(self):
        """Test empty client list response."""
        list_response = ClientListResponse(
            clients=[], total=0, page=1, per_page=10, total_pages=0
        )

        assert len(list_response.clients) == 0
        assert list_response.total == 0
