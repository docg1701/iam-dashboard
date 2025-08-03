"""Tests for Client model validation and functionality."""

from datetime import date, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from src.models.client import (
    Client,
    ClientBase,
    ClientCreate,
    ClientRead,
    ClientSearch,
    ClientStatus,
    ClientUpdate,
)


class TestClientStatus:
    """Test ClientStatus enumeration."""

    def test_client_status_values(self) -> None:
        """Test ClientStatus enum values."""
        assert ClientStatus.ACTIVE.value == "active"
        assert ClientStatus.INACTIVE.value == "inactive"
        assert ClientStatus.ARCHIVED.value == "archived"

    def test_client_status_iteration(self) -> None:
        """Test ClientStatus enum iteration."""
        statuses = list(ClientStatus)
        assert len(statuses) == 3
        assert ClientStatus.ACTIVE in statuses
        assert ClientStatus.INACTIVE in statuses
        assert ClientStatus.ARCHIVED in statuses


class TestClientBase:
    """Test ClientBase model functionality."""

    def test_client_base_creation_minimal(self) -> None:
        """Test ClientBase creation with minimal fields."""
        client_base = ClientBase(
            full_name="John Doe", ssn="123-45-6789", birth_date=date(1990, 1, 1)
        )

        assert client_base.full_name == "John Doe"
        assert client_base.ssn == "123-45-6789"
        assert client_base.birth_date == date(1990, 1, 1)
        assert client_base.status == ClientStatus.ACTIVE  # Default
        assert client_base.notes is None  # Default

    def test_client_base_creation_full(self) -> None:
        """Test ClientBase creation with all fields."""
        birth_date = date(1985, 6, 15)
        client_base = ClientBase(
            full_name="Jane Smith",
            ssn="987-65-4321",
            birth_date=birth_date,
            status=ClientStatus.INACTIVE,
            notes="Important client notes",
        )

        assert client_base.full_name == "Jane Smith"
        assert client_base.ssn == "987-65-4321"
        assert client_base.birth_date == birth_date
        assert client_base.status == ClientStatus.INACTIVE
        assert client_base.notes == "Important client notes"

    def test_client_base_full_name_validation_valid(self) -> None:
        """Test ClientBase full name validation with valid names."""
        valid_names = [
            "John Doe",
            "Mary Jane Smith",
            "José María García",
            "O'Connor",
            "Anne-Marie Dubois",
            "François",
            "Jean-Pierre van der Berg",
            "María José de la Cruz",
        ]

        for name in valid_names:
            client = ClientBase(full_name=name, ssn="123-45-6789", birth_date=date(1990, 1, 1))
            assert client.full_name == name

    def test_client_base_full_name_validation_trim_whitespace(self) -> None:
        """Test ClientBase full name validation trims whitespace."""
        client = ClientBase(
            full_name="  John Doe  ", ssn="123-45-6789", birth_date=date(1990, 1, 1)
        )
        assert client.full_name == "John Doe"  # Trimmed

    def test_client_base_full_name_validation_too_short(self) -> None:
        """Test ClientBase full name validation with too short name."""
        short_names = [
            "",
            " ",
            "A",
        ]

        for short_name in short_names:
            with pytest.raises(ValidationError) as exc_info:
                ClientBase(full_name=short_name, ssn="123-45-6789", birth_date=date(1990, 1, 1))
            # Pydantic will catch short strings before our custom validator
            assert "String should have at least 2 characters" in str(
                exc_info.value
            ) or "Full name must be at least 2 characters" in str(exc_info.value)

    def test_client_base_full_name_validation_invalid_characters(self) -> None:
        """Test ClientBase full name validation with invalid characters."""
        invalid_names = [
            "John123",  # Numbers
            "John@Doe",  # Special symbols
            "John.Doe",  # Periods
            "John_Doe",  # Underscores
            "John#Doe",  # Hash
            "John$Doe",  # Dollar sign
        ]

        for invalid_name in invalid_names:
            with pytest.raises(ValidationError) as exc_info:
                ClientBase(full_name=invalid_name, ssn="123-45-6789", birth_date=date(1990, 1, 1))
            assert "Full name can only contain letters, spaces, hyphens, and apostrophes" in str(
                exc_info.value
            )

    def test_client_base_ssn_validation_valid(self) -> None:
        """Test ClientBase SSN validation with valid SSNs."""
        valid_ssns = [
            "123-45-6789",
            "987-65-4321",
            "555-12-3456",
            "321-54-9876",
        ]

        for ssn in valid_ssns:
            client = ClientBase(full_name="John Doe", ssn=ssn, birth_date=date(1990, 1, 1))
            assert client.ssn == ssn

    def test_client_base_ssn_validation_format_errors(self) -> None:
        """Test ClientBase SSN validation with format errors."""
        invalid_formats = [
            "123456789",  # No dashes
            "123-456-789",  # Wrong dash placement
            "12-45-6789",  # Too short area
            "123-4-6789",  # Too short group
            "123-45-789",  # Too short serial
            "1234-45-6789",  # Too long area
            "123-456-6789",  # Too long group
            "123-45-67890",  # Too long serial
            "abc-de-fghi",  # Letters instead of numbers
        ]

        for invalid_ssn in invalid_formats:
            with pytest.raises(ValidationError) as exc_info:
                ClientBase(full_name="John Doe", ssn=invalid_ssn, birth_date=date(1990, 1, 1))
            assert "SSN must be in XXX-XX-XXXX format" in str(exc_info.value)

    def test_client_base_ssn_validation_invalid_patterns(self) -> None:
        """Test ClientBase SSN validation with invalid SSN patterns."""
        invalid_patterns = [
            ("000-12-3456", "SSN area number cannot be 000"),
            ("123-00-3456", "SSN group number cannot be 00"),
            ("123-45-0000", "SSN serial number cannot be 0000"),
        ]

        for invalid_ssn, expected_error in invalid_patterns:
            with pytest.raises(ValidationError) as exc_info:
                ClientBase(full_name="John Doe", ssn=invalid_ssn, birth_date=date(1990, 1, 1))
            assert expected_error in str(exc_info.value)

        # Test all zeros separately (format won't match regex)
        with pytest.raises(ValidationError) as exc_info:
            ClientBase(full_name="John Doe", ssn="000000000", birth_date=date(1990, 1, 1))
        assert "SSN must be in XXX-XX-XXXX format" in str(exc_info.value)

    def test_client_base_birth_date_validation_valid(self) -> None:
        """Test ClientBase birth date validation with valid dates."""
        today = date.today()
        valid_dates = [
            date(1990, 5, 15),
            date(1980, 12, 31),
            date(2000, 1, 1),
            date(today.year - 13, today.month, today.day),  # Exactly 13 years old
            date(1950, 6, 10),
            date(1900, 1, 1),  # Minimum allowed date
        ]

        for birth_date in valid_dates:
            client = ClientBase(full_name="John Doe", ssn="123-45-6789", birth_date=birth_date)
            assert client.birth_date == birth_date

    def test_client_base_birth_date_validation_too_old(self) -> None:
        """Test ClientBase birth date validation with too old date."""
        with pytest.raises(ValidationError) as exc_info:
            ClientBase(
                full_name="John Doe",
                ssn="123-45-6789",
                birth_date=date(1899, 12, 31),  # Before 1900
            )
        assert "Birth date cannot be before 1900-01-01" in str(exc_info.value)

    def test_client_base_birth_date_validation_too_young(self) -> None:
        """Test ClientBase birth date validation with too young date."""
        today = date.today()
        too_young_date = date(today.year - 12, today.month, today.day)  # Only 12 years old

        with pytest.raises(ValidationError) as exc_info:
            ClientBase(full_name="John Doe", ssn="123-45-6789", birth_date=too_young_date)
        assert "Client must be at least 13 years old" in str(exc_info.value)

    def test_client_base_notes_validation(self) -> None:
        """Test ClientBase notes field validation."""
        # Valid notes
        client = ClientBase(
            full_name="John Doe",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            notes="These are some notes about the client.",
        )
        assert client.notes == "These are some notes about the client."

        # None notes should work
        client_no_notes = ClientBase(
            full_name="John Doe", ssn="123-45-6789", birth_date=date(1990, 1, 1), notes=None
        )
        assert client_no_notes.notes is None

    def test_client_base_notes_max_length(self) -> None:
        """Test ClientBase notes maximum length validation."""
        # Create notes that exceed 1000 characters
        long_notes = "A" * 1001

        with pytest.raises(ValidationError) as exc_info:
            ClientBase(
                full_name="John Doe",
                ssn="123-45-6789",
                birth_date=date(1990, 1, 1),
                notes=long_notes,
            )
        # Check for either Pydantic v1 or v2 message format
        assert "ensure this value has at most 1000 characters" in str(
            exc_info.value
        ) or "String should have at most 1000 characters" in str(exc_info.value)

    def test_client_base_invalid_status(self) -> None:
        """Test ClientBase validation with invalid status."""
        with pytest.raises(ValidationError) as exc_info:
            ClientBase(
                full_name="John Doe",
                ssn="123-45-6789",
                birth_date=date(1990, 1, 1),
                status="invalid_status",
            )
        # Check for either Pydantic v1 or v2 message format
        assert "value is not a valid enumeration member" in str(
            exc_info.value
        ) or "Input should be" in str(exc_info.value)


class TestClient:
    """Test Client database model."""

    def test_client_creation_minimal(self) -> None:
        """Test Client creation with minimal required fields."""
        created_by = uuid4()
        updated_by = uuid4()

        client = Client(
            full_name="John Doe",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            created_by=created_by,
            updated_by=updated_by,
        )

        assert client.full_name == "John Doe"
        assert client.ssn == "123-45-6789"
        assert client.birth_date == date(1990, 1, 1)
        assert client.created_by == created_by
        assert client.updated_by == updated_by
        assert client.status == ClientStatus.ACTIVE  # Default
        assert isinstance(client.client_id, UUID)
        assert isinstance(client.created_at, datetime)
        assert client.updated_at is None
        assert client.notes is None

    def test_client_creation_full(self) -> None:
        """Test Client creation with all fields."""
        client_id = uuid4()
        created_by = uuid4()
        updated_by = uuid4()
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()
        birth_date = date(1985, 6, 15)

        client = Client(
            client_id=client_id,
            full_name="Jane Smith",
            ssn="987-65-4321",
            birth_date=birth_date,
            status=ClientStatus.INACTIVE,
            notes="Important client",
            created_by=created_by,
            updated_by=updated_by,
            created_at=created_at,
            updated_at=updated_at,
        )

        assert client.client_id == client_id
        assert client.full_name == "Jane Smith"
        assert client.ssn == "987-65-4321"
        assert client.birth_date == birth_date
        assert client.status == ClientStatus.INACTIVE
        assert client.notes == "Important client"
        assert client.created_by == created_by
        assert client.updated_by == updated_by
        assert client.created_at == created_at
        assert client.updated_at == updated_at

    def test_client_tablename(self) -> None:
        """Test Client table name is correct."""
        assert Client.__tablename__ == "agent1_clients"


class TestClientCreate:
    """Test ClientCreate schema."""

    def test_client_create_minimal(self) -> None:
        """Test ClientCreate with minimal valid data."""
        client_create = ClientCreate(
            full_name="John Doe", ssn="123-45-6789", birth_date=date(1990, 1, 1)
        )

        assert client_create.full_name == "John Doe"
        assert client_create.ssn == "123-45-6789"
        assert client_create.birth_date == date(1990, 1, 1)
        assert client_create.status == ClientStatus.ACTIVE  # Default
        assert client_create.notes is None  # Default

    def test_client_create_full(self) -> None:
        """Test ClientCreate with all fields."""
        birth_date = date(1985, 6, 15)
        client_create = ClientCreate(
            full_name="Jane Smith",
            ssn="987-65-4321",
            birth_date=birth_date,
            status=ClientStatus.ARCHIVED,
            notes="Test notes",
        )

        assert client_create.full_name == "Jane Smith"
        assert client_create.ssn == "987-65-4321"
        assert client_create.birth_date == birth_date
        assert client_create.status == ClientStatus.ARCHIVED
        assert client_create.notes == "Test notes"

    def test_client_create_inherits_validation(self) -> None:
        """Test ClientCreate inherits validation from ClientBase."""
        # Should fail with invalid SSN
        with pytest.raises(ValidationError):
            ClientCreate(full_name="John Doe", ssn="invalid-ssn", birth_date=date(1990, 1, 1))


class TestClientUpdate:
    """Test ClientUpdate schema."""

    def test_client_update_empty(self) -> None:
        """Test ClientUpdate with no fields (all None)."""
        client_update = ClientUpdate()

        assert client_update.full_name is None
        assert client_update.ssn is None
        assert client_update.birth_date is None
        assert client_update.status is None
        assert client_update.notes is None

    def test_client_update_partial(self) -> None:
        """Test ClientUpdate with some fields."""
        client_update = ClientUpdate(full_name="New Name", status=ClientStatus.INACTIVE)

        assert client_update.full_name == "New Name"
        assert client_update.status == ClientStatus.INACTIVE
        assert client_update.ssn is None
        assert client_update.birth_date is None
        assert client_update.notes is None

    def test_client_update_full(self) -> None:
        """Test ClientUpdate with all fields."""
        birth_date = date(1980, 3, 20)
        client_update = ClientUpdate(
            full_name="Updated Name",
            ssn="555-12-3456",
            birth_date=birth_date,
            status=ClientStatus.ARCHIVED,
            notes="Updated notes",
        )

        assert client_update.full_name == "Updated Name"
        assert client_update.ssn == "555-12-3456"
        assert client_update.birth_date == birth_date
        assert client_update.status == ClientStatus.ARCHIVED
        assert client_update.notes == "Updated notes"

    def test_client_update_validation_reuse(self) -> None:
        """Test ClientUpdate uses Pydantic built-in validators."""
        # Should fail with invalid full name (min_length constraint works)
        with pytest.raises(ValidationError) as exc_info:
            ClientUpdate(full_name="A")  # Too short
        assert "String should have at least 2 characters" in str(exc_info.value)

        # Should fail with invalid SSN (regex constraint works)
        with pytest.raises(ValidationError) as exc_info:
            ClientUpdate(ssn="invalid")
        assert "String should match pattern" in str(exc_info.value)

        # Birth date validation from custom validators doesn't work with SQLModel
        # But this should still be accepted (no built-in constraint for 1900 limit)
        client_update = ClientUpdate(birth_date=date(1899, 1, 1))
        assert client_update.birth_date == date(1899, 1, 1)


class TestClientSearch:
    """Test ClientSearch schema."""

    def test_client_search_empty(self) -> None:
        """Test ClientSearch with no filters."""
        client_search = ClientSearch()

        assert client_search.full_name is None
        assert client_search.ssn is None
        assert client_search.status is None
        assert client_search.created_after is None
        assert client_search.created_before is None

    def test_client_search_partial(self) -> None:
        """Test ClientSearch with some filters."""
        client_search = ClientSearch(full_name="John", status=ClientStatus.ACTIVE)

        assert client_search.full_name == "John"
        assert client_search.status == ClientStatus.ACTIVE
        assert client_search.ssn is None
        assert client_search.created_after is None
        assert client_search.created_before is None

    def test_client_search_full(self) -> None:
        """Test ClientSearch with all filters."""
        created_after = date(2023, 1, 1)
        created_before = date(2023, 12, 31)

        client_search = ClientSearch(
            full_name="John Doe",
            ssn="123-45-6789",
            status=ClientStatus.ACTIVE,
            created_after=created_after,
            created_before=created_before,
        )

        assert client_search.full_name == "John Doe"
        assert client_search.ssn == "123-45-6789"
        assert client_search.status == ClientStatus.ACTIVE
        assert client_search.created_after == created_after
        assert client_search.created_before == created_before

    def test_client_search_date_range(self) -> None:
        """Test ClientSearch with date range filters."""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 6, 30)

        client_search = ClientSearch(created_after=start_date, created_before=end_date)

        assert client_search.created_after == start_date
        assert client_search.created_before == end_date


class TestClientRead:
    """Test ClientRead schema."""

    def test_client_read_creation(self) -> None:
        """Test ClientRead schema creation."""
        client_id = uuid4()
        created_by = uuid4()
        updated_by = uuid4()
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()
        birth_date = date(1990, 1, 1)

        client_read = ClientRead(
            client_id=client_id,
            full_name="John Doe",
            ssn="123-45-6789",
            birth_date=birth_date,
            status=ClientStatus.ACTIVE,
            notes="Client notes",
            created_by=created_by,
            updated_by=updated_by,
            created_at=created_at,
            updated_at=updated_at,
        )

        assert client_read.client_id == client_id
        assert client_read.full_name == "John Doe"
        assert client_read.ssn == "123-45-6789"
        assert client_read.birth_date == birth_date
        assert client_read.status == ClientStatus.ACTIVE
        assert client_read.notes == "Client notes"
        assert client_read.created_by == created_by
        assert client_read.updated_by == updated_by
        assert client_read.created_at == created_at
        assert client_read.updated_at == updated_at

    def test_client_read_minimal(self) -> None:
        """Test ClientRead with minimal required fields."""
        client_id = uuid4()
        created_by = uuid4()
        updated_by = uuid4()
        created_at = datetime.utcnow()

        client_read = ClientRead(
            client_id=client_id,
            full_name="John Doe",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            created_by=created_by,
            updated_by=updated_by,
            created_at=created_at,
            updated_at=None,  # Explicitly provide None
        )

        assert client_read.client_id == client_id
        assert client_read.full_name == "John Doe"
        assert client_read.ssn == "123-45-6789"
        assert client_read.created_by == created_by
        assert client_read.updated_by == updated_by
        assert client_read.created_at == created_at
        assert client_read.status == ClientStatus.ACTIVE  # Default
        assert client_read.notes is None  # Default
        assert client_read.updated_at is None  # Explicit None

    def test_client_read_config(self) -> None:
        """Test ClientRead configuration."""
        assert ClientRead.Config.from_attributes is True
