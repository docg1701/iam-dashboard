"""Tests for Client schemas validation and functionality."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.schemas.clients import (
    ClientCreate,
    ClientList,
    ClientResponse,
    ClientSearchParams,
    ClientUpdate,
)


class TestClientSearchParams:
    """Test ClientSearchParams schema."""

    def test_client_search_params_empty(self):
        """Test ClientSearchParams with no filters."""
        search = ClientSearchParams()

        assert search.name is None
        assert search.ssn is None
        assert search.status is None
        assert search.created_after is None
        assert search.created_before is None

    def test_client_search_params_partial(self):
        """Test ClientSearchParams with some filters."""
        search = ClientSearchParams(
            name="John",
            status="active"
        )

        assert search.name == "John"
        assert search.status == "active"
        assert search.ssn is None
        assert search.created_after is None
        assert search.created_before is None

    def test_client_search_params_full(self):
        """Test ClientSearchParams with all filters."""
        created_after = date(2023, 1, 1)
        created_before = date(2023, 12, 31)

        search = ClientSearchParams(
            name="John Doe",
            ssn="123-45-6789",
            status="active",
            created_after=created_after,
            created_before=created_before
        )

        assert search.name == "John Doe"
        assert search.ssn == "123-45-6789"
        assert search.status == "active"
        assert search.created_after == created_after
        assert search.created_before == created_before

    def test_client_search_params_date_range(self):
        """Test ClientSearchParams with date range."""
        start_date = date(2023, 6, 1)
        end_date = date(2023, 6, 30)

        search = ClientSearchParams(
            created_after=start_date,
            created_before=end_date
        )

        assert search.created_after == start_date
        assert search.created_before == end_date


class TestClientCreate:
    """Test ClientCreate schema."""

    def test_client_create_minimal(self):
        """Test ClientCreate with minimal required fields."""
        client_create = ClientCreate(
            full_name="John Doe",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1)
        )

        assert client_create.full_name == "John Doe"
        assert client_create.ssn == "123-45-6789"
        assert client_create.birth_date == date(1990, 1, 1)
        assert client_create.notes is None

    def test_client_create_full(self):
        """Test ClientCreate with all fields."""
        birth_date = date(1985, 6, 15)
        notes = "Important client notes"

        client_create = ClientCreate(
            full_name="Jane Smith",
            ssn="987-65-4321",
            birth_date=birth_date,
            notes=notes
        )

        assert client_create.full_name == "Jane Smith"
        assert client_create.ssn == "987-65-4321"
        assert client_create.birth_date == birth_date
        assert client_create.notes == notes

    def test_client_create_ssn_validation_valid(self):
        """Test ClientCreate SSN validation with valid SSNs."""
        valid_ssns = [
            "123-45-6789",
            "987-65-4321",
            "555-12-3456",
            "000-00-0001",  # Edge case but format valid
        ]

        for ssn in valid_ssns:
            client = ClientCreate(
                full_name="Test Client",
                ssn=ssn,
                birth_date=date(1990, 1, 1)
            )
            assert client.ssn == ssn

    def test_client_create_ssn_validation_invalid(self):
        """Test ClientCreate SSN validation with invalid SSNs."""
        invalid_ssns = [
            "123456789",      # No dashes
            "123-456-789",    # Wrong dash placement
            "12-45-6789",     # Too short area
            "123-4-6789",     # Too short group
            "123-45-789",     # Too short serial
            "abc-de-fghi",    # Letters
            "123-45-67890",   # Too long serial
            "",               # Empty
            "123-45-XXXX",    # Letters in serial
        ]

        for ssn in invalid_ssns:
            with pytest.raises(ValidationError) as exc_info:
                ClientCreate(
                    full_name="Test Client",
                    ssn=ssn,
                    birth_date=date(1990, 1, 1)
                )
            assert "SSN must be in format XXX-XX-XXXX" in str(exc_info.value)

    def test_client_create_birth_date_validation_valid(self):
        """Test ClientCreate birth date validation with valid dates."""
        today = date.today()
        valid_dates = [
            date(1990, 1, 1),
            date(1950, 6, 15),
            today,                              # Today is valid
            today - timedelta(days=1),          # Yesterday is valid
            date(2000, 12, 31),
        ]

        for birth_date in valid_dates:
            client = ClientCreate(
                full_name="Test Client",
                ssn="123-45-6789",
                birth_date=birth_date
            )
            assert client.birth_date == birth_date

    def test_client_create_birth_date_validation_invalid(self):
        """Test ClientCreate birth date validation with future dates."""
        today = date.today()
        future_dates = [
            today + timedelta(days=1),    # Tomorrow
            today + timedelta(days=365),  # Next year
            date(2050, 1, 1),            # Far future
        ]

        for birth_date in future_dates:
            with pytest.raises(ValidationError) as exc_info:
                ClientCreate(
                    full_name="Test Client",
                    ssn="123-45-6789",
                    birth_date=birth_date
                )
            assert "Birth date cannot be in the future" in str(exc_info.value)

    def test_client_create_full_name_validation(self):
        """Test ClientCreate full name validation."""
        # Too short
        with pytest.raises(ValidationError) as exc_info:
            ClientCreate(
                full_name="A",  # Only 1 character
                ssn="123-45-6789",
                birth_date=date(1990, 1, 1)
            )
        assert "at least 2 characters" in str(exc_info.value)

        # Too long
        long_name = "A" * 256  # 256 characters
        with pytest.raises(ValidationError) as exc_info:
            ClientCreate(
                full_name=long_name,
                ssn="123-45-6789",
                birth_date=date(1990, 1, 1)
            )
        assert "at most 255 characters" in str(exc_info.value)

    def test_client_create_notes_validation(self):
        """Test ClientCreate notes validation."""
        # Valid notes
        valid_notes = [
            None,  # None is allowed
            "",    # Empty string is allowed
            "Short note",
            "A" * 1000,  # Exactly 1000 characters
        ]

        for notes in valid_notes:
            client = ClientCreate(
                full_name="Test Client",
                ssn="123-45-6789",
                birth_date=date(1990, 1, 1),
                notes=notes
            )
            assert client.notes == notes

        # Too long notes
        long_notes = "A" * 1001  # 1001 characters
        with pytest.raises(ValidationError) as exc_info:
            ClientCreate(
                full_name="Test Client",
                ssn="123-45-6789",
                birth_date=date(1990, 1, 1),
                notes=long_notes
            )
        assert "at most 1000 characters" in str(exc_info.value)


class TestClientUpdate:
    """Test ClientUpdate schema."""

    def test_client_update_empty(self):
        """Test ClientUpdate with no fields (all None)."""
        client_update = ClientUpdate()

        assert client_update.full_name is None
        assert client_update.ssn is None
        assert client_update.birth_date is None
        assert client_update.status is None
        assert client_update.notes is None

    def test_client_update_partial(self):
        """Test ClientUpdate with some fields."""
        client_update = ClientUpdate(
            full_name="Updated Name",
            status="inactive"
        )

        assert client_update.full_name == "Updated Name"
        assert client_update.status == "inactive"
        assert client_update.ssn is None
        assert client_update.birth_date is None
        assert client_update.notes is None

    def test_client_update_full(self):
        """Test ClientUpdate with all fields."""
        birth_date = date(1980, 3, 20)

        client_update = ClientUpdate(
            full_name="Fully Updated Name",
            ssn="555-12-3456",
            birth_date=birth_date,
            status="archived",
            notes="Updated notes"
        )

        assert client_update.full_name == "Fully Updated Name"
        assert client_update.ssn == "555-12-3456"
        assert client_update.birth_date == birth_date
        assert client_update.status == "archived"
        assert client_update.notes == "Updated notes"

    def test_client_update_ssn_validation_valid(self):
        """Test ClientUpdate SSN validation with valid SSNs and None."""
        valid_ssns = [
            None,             # None is allowed
            "123-45-6789",
            "987-65-4321",
            "555-12-3456",
        ]

        for ssn in valid_ssns:
            client_update = ClientUpdate(ssn=ssn)
            assert client_update.ssn == ssn

    def test_client_update_ssn_validation_invalid(self):
        """Test ClientUpdate SSN validation with invalid SSNs."""
        invalid_ssns = [
            "123456789",      # No dashes
            "123-456-789",    # Wrong format
            "abc-de-fghi",    # Letters
            "",               # Empty string
            "123-45-XXXX",    # Invalid characters
        ]

        for ssn in invalid_ssns:
            with pytest.raises(ValidationError) as exc_info:
                ClientUpdate(ssn=ssn)
            assert "SSN must be in format XXX-XX-XXXX" in str(exc_info.value)

    def test_client_update_birth_date_validation_valid(self):
        """Test ClientUpdate birth date validation with valid dates and None."""
        today = date.today()
        valid_dates = [
            None,                             # None is allowed
            date(1990, 1, 1),
            today,                            # Today is valid
            today - timedelta(days=1),        # Yesterday is valid
        ]

        for birth_date in valid_dates:
            client_update = ClientUpdate(birth_date=birth_date)
            assert client_update.birth_date == birth_date

    def test_client_update_birth_date_validation_invalid(self):
        """Test ClientUpdate birth date validation with future dates."""
        today = date.today()
        future_dates = [
            today + timedelta(days=1),    # Tomorrow
            today + timedelta(days=365),  # Next year
            date(2050, 1, 1),            # Far future
        ]

        for birth_date in future_dates:
            with pytest.raises(ValidationError) as exc_info:
                ClientUpdate(birth_date=birth_date)
            assert "Birth date cannot be in the future" in str(exc_info.value)


class TestClientResponse:
    """Test ClientResponse schema."""

    def test_client_response_creation(self):
        """Test ClientResponse schema creation."""
        client_id = uuid4()

        client_response = ClientResponse(
            client_id=client_id,
            full_name="John Doe",
            ssn="123-45-6789",  # Will be masked
            birth_date=date(1990, 1, 1),
            status="active",
            notes="Some notes",
            created_at="2023-01-01T00:00:00",
            updated_at="2023-01-01T00:00:00",
            created_by="admin"
        )

        assert client_response.client_id == client_id
        assert client_response.full_name == "John Doe"
        assert client_response.ssn == "***-**-6789"  # Masked
        assert client_response.birth_date == date(1990, 1, 1)
        assert client_response.status == "active"
        assert client_response.notes == "Some notes"
        assert client_response.created_at == "2023-01-01T00:00:00"
        assert client_response.updated_at == "2023-01-01T00:00:00"
        assert client_response.created_by == "admin"

    def test_client_response_ssn_masking_normal(self):
        """Test ClientResponse SSN masking with normal SSNs."""
        test_cases = [
            ("123-45-6789", "***-**-6789"),
            ("987-65-4321", "***-**-4321"),
            ("555-12-3456", "***-**-3456"),
            ("000-00-0001", "***-**-0001"),
        ]

        client_id = uuid4()
        for original_ssn, expected_masked in test_cases:
            client_response = ClientResponse(
                client_id=client_id,
                full_name="Test Client",
                ssn=original_ssn,
                birth_date=date(1990, 1, 1),
                status="active",
                created_at="2023-01-01T00:00:00",
                updated_at="2023-01-01T00:00:00",
                created_by="admin"
            )
            assert client_response.ssn == expected_masked

    def test_client_response_ssn_masking_edge_cases(self):
        """Test ClientResponse SSN masking with edge cases."""
        test_cases = [
            ("123", "***-**-****"),      # Too short, fallback
            ("12", "***-**-****"),       # Too short, fallback
            ("1", "***-**-****"),        # Too short, fallback
            ("", "***-**-****"),         # Empty, fallback
        ]

        client_id = uuid4()
        for original_ssn, expected_masked in test_cases:
            client_response = ClientResponse(
                client_id=client_id,
                full_name="Test Client",
                ssn=original_ssn,
                birth_date=date(1990, 1, 1),
                status="active",
                created_at="2023-01-01T00:00:00",
                updated_at="2023-01-01T00:00:00",
                created_by="admin"
            )
            assert client_response.ssn == expected_masked

    def test_client_response_minimal(self):
        """Test ClientResponse with minimal required fields."""
        client_id = uuid4()

        client_response = ClientResponse(
            client_id=client_id,
            full_name="Minimal Client",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            status="active",
            created_at="2023-01-01T00:00:00",
            updated_at="2023-01-01T00:00:00",
            created_by="admin"
        )

        assert client_response.client_id == client_id
        assert client_response.full_name == "Minimal Client"
        assert client_response.ssn == "***-**-6789"
        assert client_response.birth_date == date(1990, 1, 1)
        assert client_response.status == "active"
        assert client_response.notes is None  # Default
        assert client_response.created_at == "2023-01-01T00:00:00"
        assert client_response.updated_at == "2023-01-01T00:00:00"
        assert client_response.created_by == "admin"


class TestClientList:
    """Test ClientList schema."""

    def test_client_list_creation(self):
        """Test ClientList schema creation."""
        client_id = uuid4()

        client_list = ClientList(
            client_id=client_id,
            full_name="John Doe",
            ssn_masked="***-**-6789",
            status="active",
            created_at="2023-01-01T00:00:00"
        )

        assert client_list.client_id == client_id
        assert client_list.full_name == "John Doe"
        assert client_list.ssn_masked == "***-**-6789"
        assert client_list.status == "active"
        assert client_list.created_at == "2023-01-01T00:00:00"

    def test_client_list_multiple_clients(self):
        """Test ClientList with multiple different clients."""
        clients_data = [
            {
                "client_id": uuid4(),
                "full_name": "Alice Johnson",
                "ssn_masked": "***-**-1234",
                "status": "active",
                "created_at": "2023-01-01T00:00:00"
            },
            {
                "client_id": uuid4(),
                "full_name": "Bob Smith",
                "ssn_masked": "***-**-5678",
                "status": "inactive",
                "created_at": "2023-02-01T00:00:00"
            },
            {
                "client_id": uuid4(),
                "full_name": "Carol Wilson",
                "ssn_masked": "***-**-9012",
                "status": "archived",
                "created_at": "2023-03-01T00:00:00"
            }
        ]

        for client_data in clients_data:
            client_list = ClientList(**client_data)
            assert client_list.client_id == client_data["client_id"]
            assert client_list.full_name == client_data["full_name"]
            assert client_list.ssn_masked == client_data["ssn_masked"]
            assert client_list.status == client_data["status"]
            assert client_list.created_at == client_data["created_at"]

    def test_client_list_different_statuses(self):
        """Test ClientList with different status values."""
        statuses = ["active", "inactive", "archived", "pending"]
        client_id = uuid4()

        for status in statuses:
            client_list = ClientList(
                client_id=client_id,
                full_name="Test Client",
                ssn_masked="***-**-1234",
                status=status,
                created_at="2023-01-01T00:00:00"
            )
            assert client_list.status == status
