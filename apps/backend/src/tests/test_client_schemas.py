"""Tests for Client schemas validation and functionality."""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.schemas.clients import (
    ClientCreate,
    ClientListItem,
    ClientResponse,
    ClientSearchParams,
    ClientStatus,
    ClientUpdate,
)


class TestClientSearchParams:
    """Test ClientSearchParams schema."""

    def test_client_search_params_empty(self) -> None:
        """Test ClientSearchParams with no filters."""
        search = ClientSearchParams()

        assert search.full_name is None
        assert search.ssn is None
        assert search.status is None
        assert search.created_after is None
        assert search.created_before is None

    def test_client_search_params_partial(self) -> None:
        """Test ClientSearchParams with some filters."""

        search = ClientSearchParams(full_name="John", status=ClientStatus.ACTIVE)

        assert search.full_name == "John"
        assert search.status == ClientStatus.ACTIVE
        assert search.ssn is None
        assert search.created_after is None
        assert search.created_before is None

    def test_client_search_params_full(self) -> None:
        """Test ClientSearchParams with all filters."""

        created_after = date(2023, 1, 1)
        created_before = date(2023, 12, 31)

        search = ClientSearchParams(
            full_name="John Doe",
            ssn="123-45-6789",
            status=ClientStatus.ACTIVE,
            created_after=created_after,
            created_before=created_before,
        )

        assert search.full_name == "John Doe"
        assert search.ssn == "123-45-6789"
        assert search.status == ClientStatus.ACTIVE
        assert search.created_after == created_after
        assert search.created_before == created_before

    def test_client_search_params_date_range(self) -> None:
        """Test ClientSearchParams with date range."""
        start_date = date(2023, 6, 1)
        end_date = date(2023, 6, 30)

        search = ClientSearchParams(created_after=start_date, created_before=end_date)

        assert search.created_after == start_date
        assert search.created_before == end_date


class TestClientCreate:
    """Test ClientCreate schema."""

    def test_client_create_minimal(self) -> None:
        """Test ClientCreate with minimal required fields."""
        client_create = ClientCreate(
            full_name="John Doe", ssn="123-45-6789", birth_date=date(1990, 1, 1)
        )

        assert client_create.full_name == "John Doe"
        assert client_create.ssn == "123-45-6789"
        assert client_create.birth_date == date(1990, 1, 1)
        assert client_create.notes is None

    def test_client_create_full(self) -> None:
        """Test ClientCreate with all fields."""
        birth_date = date(1985, 6, 15)
        notes = "Important client notes"

        client_create = ClientCreate(
            full_name="Jane Smith", ssn="987-65-4321", birth_date=birth_date, notes=notes
        )

        assert client_create.full_name == "Jane Smith"
        assert client_create.ssn == "987-65-4321"
        assert client_create.birth_date == birth_date
        assert client_create.notes == notes

    def test_client_create_ssn_validation_valid(self) -> None:
        """Test ClientCreate SSN validation with valid SSNs."""
        valid_ssns = [
            "123-45-6789",
            "987-65-4321",
            "555-12-3456",
            "111-11-1111",  # Valid format
        ]

        for ssn in valid_ssns:
            client = ClientCreate(full_name="Test Client", ssn=ssn, birth_date=date(1990, 1, 1))
            assert client.ssn == ssn

    def test_client_create_ssn_validation_invalid(self) -> None:
        """Test ClientCreate SSN validation with invalid SSNs."""
        invalid_ssns = [
            "123456789",  # No dashes
            "123-456-789",  # Wrong dash placement
            "12-45-6789",  # Too short area
            "123-4-6789",  # Too short group
            "123-45-789",  # Too short serial
            "abc-de-fghi",  # Letters
            "123-45-67890",  # Too long serial
            "",  # Empty
            "123-45-XXXX",  # Letters in serial
        ]

        for ssn in invalid_ssns:
            with pytest.raises(ValidationError) as exc_info:
                ClientCreate(full_name="Test Client", ssn=ssn, birth_date=date(1990, 1, 1))
            error_msg = str(exc_info.value)
            # Accept either custom validation message or Pydantic regex mismatch
            assert (
                "SSN must be in XXX-XX-XXXX format" in error_msg
                or "String should match pattern" in error_msg
                or "area number cannot be 000" in error_msg
                or "group number cannot be 00" in error_msg
                or "serial number cannot be 0000" in error_msg
            )

    def test_client_create_birth_date_validation_valid(self) -> None:
        """Test ClientCreate birth date validation with valid dates."""
        today = date.today()
        valid_dates = [
            date(1990, 1, 1),
            date(1950, 6, 15),
            date(today.year - 13, today.month, today.day),  # Exactly 13 years old
            date(today.year - 20, today.month, today.day),  # 20 years old
            date(2000, 12, 31),  # If it's after 2013
        ]

        for birth_date in valid_dates:
            # Only test dates that should actually be valid (at least 13 years old)
            if birth_date <= date(today.year - 13, today.month, today.day):
                client = ClientCreate(
                    full_name="Test Client", ssn="123-45-6789", birth_date=birth_date
                )
                assert client.birth_date == birth_date

    def test_client_create_birth_date_validation_invalid(self) -> None:
        """Test ClientCreate birth date validation with invalid dates."""
        today = date.today()
        invalid_dates = [
            today + timedelta(days=1),  # Tomorrow (too young)
            today + timedelta(days=365),  # Next year (too young)
            date(today.year - 12, today.month, today.day),  # Only 12 years old
            date(1899, 1, 1),  # Too old (before 1900)
        ]

        for birth_date in invalid_dates:
            with pytest.raises(ValidationError) as exc_info:
                ClientCreate(full_name="Test Client", ssn="123-45-6789", birth_date=birth_date)
            error_message = str(exc_info.value)
            assert (
                "Client must be at least 13 years old" in error_message
                or "Birth date cannot be before 1900-01-01" in error_message
            )

    def test_client_create_full_name_validation(self) -> None:
        """Test ClientCreate full name validation."""
        # Too short
        with pytest.raises(ValidationError) as exc_info:
            ClientCreate(
                full_name="A",  # Only 1 character
                ssn="123-45-6789",
                birth_date=date(1990, 1, 1),
            )
        assert "at least 2 characters" in str(exc_info.value)

        # Too long
        long_name = "A" * 256  # 256 characters
        with pytest.raises(ValidationError) as exc_info:
            ClientCreate(full_name=long_name, ssn="123-45-6789", birth_date=date(1990, 1, 1))
        assert "at most 255 characters" in str(exc_info.value)

    def test_client_create_notes_validation(self) -> None:
        """Test ClientCreate notes validation."""
        # Valid notes
        valid_notes = [
            None,  # None is allowed
            "",  # Empty string is allowed
            "Short note",
            "A" * 1000,  # Exactly 1000 characters
        ]

        for notes in valid_notes:
            client = ClientCreate(
                full_name="Test Client", ssn="123-45-6789", birth_date=date(1990, 1, 1), notes=notes
            )
            assert client.notes == notes

        # Too long notes
        long_notes = "A" * 1001  # 1001 characters
        with pytest.raises(ValidationError) as exc_info:
            ClientCreate(
                full_name="Test Client",
                ssn="123-45-6789",
                birth_date=date(1990, 1, 1),
                notes=long_notes,
            )
        assert "at most 1000 characters" in str(exc_info.value)

    def test_client_create_ssn_edge_cases(self) -> None:
        """Test ClientCreate SSN validation edge cases to improve coverage."""
        # Test all invalid SSN patterns that trigger specific validation errors
        invalid_ssn_cases = [
            ("000-12-3456", "area number cannot be 000"),
            ("123-00-4567", "group number cannot be 00"),
            ("123-45-0000", "serial number cannot be 0000"),
            ("000-00-0000", "SSN cannot be all zeros"),
        ]

        for ssn, expected_error in invalid_ssn_cases:
            with pytest.raises(ValidationError) as exc_info:
                ClientCreate(full_name="Test Client", ssn=ssn, birth_date=date(1990, 1, 1))
            error_msg = str(exc_info.value)
            assert expected_error in error_msg

    def test_client_create_name_validation_edge_cases(self) -> None:
        """Test ClientCreate name validation edge cases to improve coverage."""
        # Test name trimming
        client = ClientCreate(
            full_name="  John Doe  ",  # Name with spaces
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
        )
        assert client.full_name == "John Doe"  # Should be trimmed

        # Test invalid characters
        invalid_names = [
            "John123",  # Numbers
            "John@Doe",  # Special characters
            "John_Doe",  # Underscore
            "John.Doe",  # Period
        ]

        for invalid_name in invalid_names:
            with pytest.raises(ValidationError) as exc_info:
                ClientCreate(
                    full_name=invalid_name,
                    ssn="123-45-6789",
                    birth_date=date(1990, 1, 1),
                )
            error_msg = str(exc_info.value)
            assert "can only contain letters, spaces, hyphens, and apostrophes" in error_msg

        # Test valid special characters
        valid_names = [
            "Jean-Pierre",  # Hyphen
            "O'Connor",  # Apostrophe
            "José María",  # Accented characters
            "Anne-Marie O'Connor",  # Multiple special chars
        ]

        for valid_name in valid_names:
            client = ClientCreate(
                full_name=valid_name,
                ssn="123-45-6789",
                birth_date=date(1990, 1, 1),
            )
            assert client.full_name == valid_name

    def test_client_create_birth_date_edge_cases(self) -> None:
        """Test ClientCreate birth date validation edge cases."""
        today = date.today()

        # Test exact boundary - 13 years old today
        exactly_13_years = date(today.year - 13, today.month, today.day)
        client = ClientCreate(
            full_name="Boundary Test",
            ssn="123-45-6789",
            birth_date=exactly_13_years,
        )
        assert client.birth_date == exactly_13_years

        # Test minimum date boundary
        min_date = date(1900, 1, 1)
        client = ClientCreate(
            full_name="Old Test",
            ssn="123-45-6789",
            birth_date=min_date,
        )
        assert client.birth_date == min_date


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
        client_update = ClientUpdate(full_name="Updated Name", status="inactive")

        assert client_update.full_name == "Updated Name"
        assert client_update.status == "inactive"
        assert client_update.ssn is None
        assert client_update.birth_date is None
        assert client_update.notes is None

    def test_client_update_full(self) -> None:
        """Test ClientUpdate with all fields."""
        birth_date = date(1980, 3, 20)

        client_update = ClientUpdate(
            full_name="Fully Updated Name",
            ssn="555-12-3456",
            birth_date=birth_date,
            status="archived",
            notes="Updated notes",
        )

        assert client_update.full_name == "Fully Updated Name"
        assert client_update.ssn == "555-12-3456"
        assert client_update.birth_date == birth_date
        assert client_update.status == "archived"
        assert client_update.notes == "Updated notes"

    def test_client_update_ssn_validation_valid(self) -> None:
        """Test ClientUpdate SSN validation with valid SSNs and None."""
        valid_ssns = [
            None,  # None is allowed
            "123-45-6789",
            "987-65-4321",
            "555-12-3456",
        ]

        for ssn in valid_ssns:
            client_update = ClientUpdate(ssn=ssn)
            assert client_update.ssn == ssn

    def test_client_update_ssn_validation_invalid(self) -> None:
        """Test ClientUpdate SSN validation with invalid SSNs."""
        invalid_ssns = [
            "123456789",  # No dashes
            "123-456-789",  # Wrong format
            "abc-de-fghi",  # Letters
            "",  # Empty string
            "123-45-XXXX",  # Invalid characters
        ]

        for ssn in invalid_ssns:
            with pytest.raises(ValidationError) as exc_info:
                ClientUpdate(ssn=ssn)
            error_msg = str(exc_info.value)
            # Accept either custom validation message or Pydantic regex mismatch
            assert (
                "SSN must be in XXX-XX-XXXX format" in error_msg
                or "String should match pattern" in error_msg
                or "area number cannot be 000" in error_msg
                or "group number cannot be 00" in error_msg
                or "serial number cannot be 0000" in error_msg
            )

    def test_client_update_birth_date_validation_valid(self) -> None:
        """Test ClientUpdate birth date validation with valid dates and None."""
        today = date.today()
        valid_dates = [
            None,  # None is allowed
            date(1990, 1, 1),
            date(today.year - 13, today.month, today.day),  # Exactly 13 years old
            date(today.year - 20, today.month, today.day),  # 20 years old
        ]

        for birth_date in valid_dates:
            # Only test dates that should actually be valid
            if birth_date is None or birth_date <= date(today.year - 13, today.month, today.day):
                client_update = ClientUpdate(birth_date=birth_date)
                assert client_update.birth_date == birth_date

    def test_client_update_birth_date_validation_invalid(self) -> None:
        """Test ClientUpdate birth date validation with invalid dates."""
        today = date.today()
        invalid_dates = [
            today + timedelta(days=1),  # Tomorrow (too young)
            date(today.year - 12, today.month, today.day),  # Only 12 years old
            date(1899, 1, 1),  # Too old (before 1900)
        ]

        for birth_date in invalid_dates:
            with pytest.raises(ValidationError) as exc_info:
                ClientUpdate(birth_date=birth_date)
            error_message = str(exc_info.value)
            assert (
                "Client must be at least 13 years old" in error_message
                or "Birth date cannot be before 1900-01-01" in error_message
            )

    def test_client_update_ssn_edge_cases(self) -> None:
        """Test ClientUpdate SSN validation edge cases to improve coverage."""
        # Test all invalid SSN patterns that trigger specific validation errors
        invalid_ssn_cases = [
            ("000-12-3456", "area number cannot be 000"),
            ("123-00-4567", "group number cannot be 00"),
            ("123-45-0000", "serial number cannot be 0000"),
            ("000-00-0000", "SSN cannot be all zeros"),
        ]

        for ssn, expected_error in invalid_ssn_cases:
            with pytest.raises(ValidationError) as exc_info:
                ClientUpdate(ssn=ssn)
            error_msg = str(exc_info.value)
            assert expected_error in error_msg

    def test_client_update_name_validation_edge_cases(self) -> None:
        """Test ClientUpdate name validation edge cases to improve coverage."""
        # Test name trimming
        client_update = ClientUpdate(full_name="  Updated Name  ")
        assert client_update.full_name == "Updated Name"  # Should be trimmed

        # Test invalid characters
        invalid_names = [
            "John123",  # Numbers
            "John@Doe",  # Special characters
            "John_Doe",  # Underscore
            "John.Doe",  # Period
        ]

        for invalid_name in invalid_names:
            with pytest.raises(ValidationError) as exc_info:
                ClientUpdate(full_name=invalid_name)
            error_msg = str(exc_info.value)
            assert "can only contain letters, spaces, hyphens, and apostrophes" in error_msg

        # Test valid special characters
        valid_names = [
            "Jean-Pierre",  # Hyphen
            "O'Connor",  # Apostrophe
            "José María",  # Accented characters
            "Anne-Marie O'Connor",  # Multiple special chars
        ]

        for valid_name in valid_names:
            client_update = ClientUpdate(full_name=valid_name)
            assert client_update.full_name == valid_name

    def test_client_update_birth_date_edge_cases(self) -> None:
        """Test ClientUpdate birth date validation edge cases."""
        today = date.today()

        # Test exact boundary - 13 years old today
        exactly_13_years = date(today.year - 13, today.month, today.day)
        client_update = ClientUpdate(birth_date=exactly_13_years)
        assert client_update.birth_date == exactly_13_years

        # Test minimum date boundary
        min_date = date(1900, 1, 1)
        client_update = ClientUpdate(birth_date=min_date)
        assert client_update.birth_date == min_date

    def test_client_create_name_after_trim_too_short(self) -> None:
        """Test ClientCreate name validation when string becomes too short after trimming."""
        # Test when trimmed name becomes too short
        with pytest.raises(ValidationError) as exc_info:
            ClientCreate(
                full_name="  A  ",  # Only 1 character after trimming
                ssn="123-45-6789",
                birth_date=date(1990, 1, 1),
            )
        assert "at least 2 characters after trimming" in str(exc_info.value)

    def test_client_update_name_after_trim_too_short(self) -> None:
        """Test ClientUpdate name validation when string becomes too short after trimming."""
        # Test when trimmed name becomes too short
        with pytest.raises(ValidationError) as exc_info:
            ClientUpdate(full_name="  A  ")  # Only 1 character after trimming
        assert "at least 2 characters after trimming" in str(exc_info.value)

    def test_client_create_ssn_invalid_format_edge_case(self) -> None:
        """Test ClientCreate SSN validation with format edge case."""
        # Test format that doesn't match regex before other validations
        with pytest.raises(ValidationError) as exc_info:
            ClientCreate(
                full_name="Test Client",
                ssn="12-345-6789",  # Wrong format - should trigger regex error
                birth_date=date(1990, 1, 1),
            )
        error_msg = str(exc_info.value)
        assert (
            "SSN must be in XXX-XX-XXXX format" in error_msg
            or "String should match pattern" in error_msg
        )

    def test_client_update_ssn_invalid_format_edge_case(self) -> None:
        """Test ClientUpdate SSN validation with format edge case."""
        # Test format that doesn't match regex before other validations
        with pytest.raises(ValidationError) as exc_info:
            ClientUpdate(ssn="12-345-6789")  # Wrong format - should trigger regex error
        error_msg = str(exc_info.value)
        assert (
            "SSN must be in XXX-XX-XXXX format" in error_msg
            or "String should match pattern" in error_msg
        )


class TestClientResponse:
    """Test ClientResponse schema."""

    def test_client_response_creation(self) -> None:
        """Test ClientResponse schema creation."""

        client_id = uuid4()
        created_by = uuid4()
        updated_by = uuid4()
        created_at = datetime(2023, 1, 1)
        updated_at = datetime(2023, 1, 1)

        client_response = ClientResponse(
            client_id=client_id,
            full_name="John Doe",
            ssn="123-45-6789",  # Will be masked
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            notes="Some notes",
            created_at=created_at,
            updated_at=updated_at,
            created_by=created_by,
            updated_by=updated_by,
        )

        assert client_response.client_id == client_id
        assert client_response.full_name == "John Doe"
        assert client_response.ssn == "***-**-6789"  # Masked
        assert client_response.birth_date == date(1990, 1, 1)
        assert client_response.status == ClientStatus.ACTIVE
        assert client_response.notes == "Some notes"
        assert client_response.created_at == created_at
        assert client_response.updated_at == updated_at
        assert client_response.created_by == created_by
        assert client_response.updated_by == updated_by

    def test_client_response_ssn_masking_normal(self) -> None:
        """Test ClientResponse SSN masking with normal SSNs."""

        test_cases = [
            ("123-45-6789", "***-**-6789"),
            ("987-65-4321", "***-**-4321"),
            ("555-12-3456", "***-**-3456"),
            ("000-00-0001", "***-**-0001"),
        ]

        client_id = uuid4()
        created_by = uuid4()
        updated_by = uuid4()
        created_at = datetime(2023, 1, 1)
        updated_at = datetime(2023, 1, 1)

        for original_ssn, expected_masked in test_cases:
            client_response = ClientResponse(
                client_id=client_id,
                full_name="Test Client",
                ssn=original_ssn,
                birth_date=date(1990, 1, 1),
                status=ClientStatus.ACTIVE,
                notes=None,
                created_at=created_at,
                updated_at=updated_at,
                created_by=created_by,
                updated_by=updated_by,
            )
            assert client_response.ssn == expected_masked

    def test_client_response_ssn_masking_edge_cases(self) -> None:
        """Test ClientResponse SSN masking with edge cases."""

        test_cases = [
            ("123", "***-**-****"),  # Too short, fallback
            ("12", "***-**-****"),  # Too short, fallback
            ("1", "***-**-****"),  # Too short, fallback
            ("", "***-**-****"),  # Empty, fallback
        ]

        client_id = uuid4()
        created_by = uuid4()
        updated_by = uuid4()
        created_at = datetime(2023, 1, 1)
        updated_at = datetime(2023, 1, 1)

        for original_ssn, expected_masked in test_cases:
            client_response = ClientResponse(
                client_id=client_id,
                full_name="Test Client",
                ssn=original_ssn,
                birth_date=date(1990, 1, 1),
                status=ClientStatus.ACTIVE,
                notes=None,
                created_at=created_at,
                updated_at=updated_at,
                created_by=created_by,
                updated_by=updated_by,
            )
            assert client_response.ssn == expected_masked

    def test_client_response_minimal(self) -> None:
        """Test ClientResponse with minimal required fields."""

        client_id = uuid4()
        created_by = uuid4()
        updated_by = uuid4()
        created_at = datetime(2023, 1, 1)
        updated_at = datetime(2023, 1, 1)

        client_response = ClientResponse(
            client_id=client_id,
            full_name="Minimal Client",
            ssn="123-45-6789",
            birth_date=date(1990, 1, 1),
            status=ClientStatus.ACTIVE,
            notes=None,
            created_at=created_at,
            updated_at=updated_at,
            created_by=created_by,
            updated_by=updated_by,
        )

        assert client_response.client_id == client_id
        assert client_response.full_name == "Minimal Client"
        assert client_response.ssn == "***-**-6789"
        assert client_response.birth_date == date(1990, 1, 1)
        assert client_response.status == ClientStatus.ACTIVE
        assert client_response.notes is None  # Default
        assert client_response.created_at == created_at
        assert client_response.updated_at == updated_at
        assert client_response.created_by == created_by
        assert client_response.updated_by == updated_by


class TestClientListItem:
    """Test ClientListItem schema."""

    def test_client_list_item_creation(self) -> None:
        """Test ClientListItem schema creation."""

        client_id = uuid4()
        created_at = datetime(2023, 1, 1)

        client_list = ClientListItem(
            client_id=client_id,
            full_name="John Doe",
            ssn_masked="***-**-6789",
            status=ClientStatus.ACTIVE,
            created_at=created_at,
        )

        assert client_list.client_id == client_id
        assert client_list.full_name == "John Doe"
        assert client_list.ssn_masked == "***-**-6789"
        assert client_list.status == ClientStatus.ACTIVE
        assert client_list.created_at == created_at

    def test_client_list_item_multiple_clients(self) -> None:
        """Test ClientListItem with multiple different clients."""

        clients_data = [
            {
                "client_id": uuid4(),
                "full_name": "Alice Johnson",
                "ssn_masked": "***-**-1234",
                "status": ClientStatus.ACTIVE,
                "created_at": datetime(2023, 1, 1),
            },
            {
                "client_id": uuid4(),
                "full_name": "Bob Smith",
                "ssn_masked": "***-**-5678",
                "status": ClientStatus.INACTIVE,
                "created_at": datetime(2023, 2, 1),
            },
            {
                "client_id": uuid4(),
                "full_name": "Carol Wilson",
                "ssn_masked": "***-**-9012",
                "status": ClientStatus.ARCHIVED,
                "created_at": datetime(2023, 3, 1),
            },
        ]

        for client_data in clients_data:
            client_list = ClientListItem(**client_data)
            assert client_list.client_id == client_data["client_id"]
            assert client_list.full_name == client_data["full_name"]
            assert client_list.ssn_masked == client_data["ssn_masked"]
            assert client_list.status == client_data["status"]
            assert client_list.created_at == client_data["created_at"]

    def test_client_list_item_different_statuses(self) -> None:
        """Test ClientListItem with different status values."""

        statuses = [ClientStatus.ACTIVE, ClientStatus.INACTIVE, ClientStatus.ARCHIVED]
        client_id = uuid4()
        created_at = datetime(2023, 1, 1)

        for status in statuses:
            client_list = ClientListItem(
                client_id=client_id,
                full_name="Test Client",
                ssn_masked="***-**-1234",
                status=status,
                created_at=created_at,
            )
            assert client_list.status == status
