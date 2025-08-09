"""
Tests for validation utilities to improve coverage.
"""

from datetime import date

from src.utils.validation import (
    sanitize_filename,
    validate_birth_date,
    validate_cpf,
    validate_email,
    validate_name,
    validate_password_strength,
)


class TestValidationUtilities:
    """Test all validation utility functions."""

    def test_validate_cpf_valid(self) -> None:
        """Test CPF validation with valid CPFs."""
        valid_cpfs = [
            "123.456.789-09",  # Valid CPF with correct check digits
            "987.654.321-00",  # Valid CPF with correct check digits
            "12345678909",  # Valid without formatting
        ]

        for cpf in valid_cpfs:
            assert validate_cpf(cpf) is True

    def test_validate_cpf_invalid(self) -> None:
        """Test CPF validation with invalid CPFs."""
        invalid_cpfs = [
            "000.000.000-00",  # All zeros
            "111.111.111-11",  # All same digits
            "123.456.789-10",  # Invalid check digits
            "123.456.789",  # Wrong format (missing check digits)
            "12345678",  # Too short
            "abc.def.ghi-jk",  # Non-numeric
            "",  # Empty string
            None,  # None input
            "123.456.789-09-extra",  # Too long
        ]

        for cpf in invalid_cpfs:
            assert validate_cpf(cpf) is False

    def test_validate_email_valid(self) -> None:
        """Test email validation with valid emails."""
        valid_emails = [
            "user@example.com",
            "test.email@domain.co.uk",
            "user+tag@example.org",
            "123@numbers.com",
        ]

        for email in valid_emails:
            assert validate_email(email) is True

    def test_validate_email_invalid(self) -> None:
        """Test email validation with invalid emails."""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@domain",
            "user@@domain.com",
            "",
            None,
            "user@domain..com",
        ]

        for email in invalid_emails:
            assert validate_email(email) is False

    def test_validate_name_valid(self) -> None:
        """Test name validation with valid names."""
        valid_names = [
            "John Doe",
            "Jane Smith-Johnson",
            "José García",
            "Mary O'Connor",
        ]

        for name in valid_names:
            assert validate_name(name) is True

    def test_validate_name_invalid(self) -> None:
        """Test name validation with invalid names."""
        invalid_names = [
            "",  # Empty
            None,  # None
            "A",  # Too short
            "X" * 256,  # Too long
            "123",  # Numbers only
            "John@Doe",  # Invalid characters
        ]

        for name in invalid_names:
            assert validate_name(name) is False

    def test_validate_birth_date_valid(self) -> None:
        """Test birth date validation with valid dates."""
        today = date.today()
        valid_dates = [
            date(1990, 5, 15),
            date(2000, 12, 25),
            date(today.year - 18, today.month, today.day),  # Exactly 18 years old today
        ]

        for birth_date in valid_dates:
            assert validate_birth_date(birth_date) is True

    def test_validate_birth_date_invalid(self) -> None:
        """Test birth date validation with invalid dates."""
        today = date.today()
        invalid_dates = [
            None,  # None input
            date(today.year - 12, today.month, today.day),  # Under min_age (13)
            date(today.year + 1, today.month, today.day),  # Future date
            date(1899, 12, 31),  # Too old (before 1900)
        ]

        for birth_date in invalid_dates:
            assert validate_birth_date(birth_date) is False

    def test_validate_password_strength_valid(self) -> None:
        """Test password strength validation with valid passwords."""
        valid_passwords = [
            "MySecure#P4ssw0rd",  # Changed to avoid common patterns
            "ComplexP@ssw0rd",
            "SecureTest9183#",  # Non-sequential numbers to avoid weak patterns
        ]

        for password in valid_passwords:
            is_valid, messages = validate_password_strength(password)
            assert is_valid is True
            assert len(messages) == 0

    def test_validate_password_strength_invalid(self) -> None:
        """Test password strength validation with invalid passwords."""
        invalid_passwords = [
            "short",  # Too short
            "password",  # Common weak password
            "12345678",  # Numbers only
            "ALLCAPS",  # All uppercase
            "",  # Empty
            None,  # None input
            "nouppercaseornumbers",  # No uppercase or numbers
        ]

        for password in invalid_passwords:
            is_valid, messages = validate_password_strength(password)
            assert is_valid is False
            assert len(messages) > 0

    def test_sanitize_filename_valid(self) -> None:
        """Test filename sanitization."""
        test_cases = [
            ("document.pdf", "document.pdf"),
            ("my document.pdf", "my_document.pdf"),
            ("file<>:|?*.txt", "file.txt"),
            ("", "untitled"),
            (None, "untitled"),
            ("file/name\\test.doc", "file_name_test.doc"),
        ]

        for input_filename, expected in test_cases:
            result = sanitize_filename(input_filename)
            assert result == expected

    def test_validate_name_with_custom_lengths(self) -> None:
        """Test name validation with custom min/max lengths."""
        # Custom minimum length
        assert validate_name("Jo", min_length=2) is True
        assert validate_name("J", min_length=2) is False

        # Custom maximum length
        assert validate_name("Short", max_length=10) is True
        assert validate_name("VeryLongName", max_length=5) is False

    def test_validate_birth_date_with_custom_min_age(self) -> None:
        """Test birth date validation with custom minimum age."""
        today = date.today()

        # 21 years old (valid for min_age=21)
        birth_date_21 = date(today.year - 21, today.month, today.day)
        assert validate_birth_date(birth_date_21, min_age=21) is True

        # 20 years old (invalid for min_age=21)
        birth_date_20 = date(today.year - 20, today.month, today.day)
        assert validate_birth_date(birth_date_20, min_age=21) is False
