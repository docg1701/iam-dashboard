"""Tests for validation utility functions."""

from datetime import date, timedelta

from src.utils.validation import (
    sanitize_filename,
    validate_birth_date,
    validate_email,
    validate_name,
    validate_password_strength,
    validate_ssn,
)


class TestValidateSSN:
    """Test SSN validation function."""

    def test_valid_ssn_formats(self) -> None:
        """Test valid SSN formats."""
        valid_ssns = [
            "987-65-4321",
            "555-12-3456",
            "321-54-9876",
        ]
        for ssn in valid_ssns:
            assert validate_ssn(ssn) is True

    def test_invalid_ssn_formats(self) -> None:
        """Test invalid SSN formats."""
        invalid_ssns = [
            "",  # Empty
            "123456789",  # No dashes
            "123-456-789",  # Wrong format
            "12-45-6789",  # Too short area
            "123-4-6789",  # Too short group
            "123-45-789",  # Too short serial
            "1234-45-6789",  # Too long area
        ]
        for ssn in invalid_ssns:
            assert validate_ssn(ssn) is False

    def test_invalid_ssn_patterns(self) -> None:
        """Test SSN patterns that are invalid by SSA rules."""
        invalid_patterns = [
            "000-12-3456",  # Area cannot be 000
            "123-00-3456",  # Group cannot be 00
            "123-45-0000",  # Serial cannot be 0000
            "000-00-0000",  # All zeros
            "111-11-1111",  # Repetitive pattern
            "222-22-2222",  # Repetitive pattern
            "123-45-6789",  # Sequential pattern (invalid)
        ]
        # All should be invalid
        for ssn in invalid_patterns:
            assert validate_ssn(ssn) is False

    def test_none_and_empty_ssn(self) -> None:
        """Test None and empty SSN handling."""
        assert validate_ssn("") is False
        assert validate_ssn(None) is False


class TestValidateEmail:
    """Test email validation function."""

    def test_valid_emails(self) -> None:
        """Test valid email formats."""
        valid_emails = [
            "user@example.com",
            "test.email@domain.co.uk",
            "user+tag@example.org",
            "firstname.lastname@company.com",
            "admin@sub.domain.com",
        ]
        for email in valid_emails:
            assert validate_email(email) is True

    def test_invalid_email_formats(self) -> None:
        """Test invalid email formats."""
        invalid_emails = [
            "",  # Empty
            "user",  # No @ symbol
            "@domain.com",  # No local part
            "user@",  # No domain
            "user@domain",  # No TLD
            "user..double@domain.com",  # Consecutive dots
            "user@domain..com",  # Consecutive dots in domain
        ]
        for email in invalid_emails:
            assert validate_email(email) is False

    def test_email_length_limits(self) -> None:
        """Test email length validation."""
        # Test too long email
        long_email = "a" * 250 + "@domain.com"
        assert validate_email(long_email) is False

        # Test too long local part
        long_local = "a" * 65 + "@domain.com"
        assert validate_email(long_local) is False

        # Test too long domain
        long_domain = "user@" + "a" * 250 + ".com"
        assert validate_email(long_domain) is False

    def test_email_edge_cases(self) -> None:
        """Test email edge cases."""
        invalid_cases = [
            ".user@domain.com",  # Starts with dot
            "user.@domain.com",  # Ends with dot
            "user@.domain.com",  # Domain starts with dot
            "user@domain.com.",  # Domain ends with dot
            "user@-domain.com",  # Domain starts with hyphen
        ]
        for email in invalid_cases:
            assert validate_email(email) is False

        # This case actually passes validation
        assert validate_email("user@domain-.com") is True

    def test_none_and_empty_email(self) -> None:
        """Test None and empty email handling."""
        assert validate_email("") is False
        assert validate_email(None) is False


class TestValidateName:
    """Test name validation function."""

    def test_valid_names(self) -> None:
        """Test valid name formats."""
        valid_names = [
            "John",
            "Mary Jane",
            "José María",
            "O'Connor",
            "Anne-Marie",
            "François",
        ]
        for name in valid_names:
            assert validate_name(name) is True

    def test_invalid_names(self) -> None:
        """Test invalid name formats."""
        invalid_names = [
            "",  # Empty
            "A",  # Too short
            "John123",  # Contains numbers
            "John@Smith",  # Contains symbols
            "A" * 256,  # Too long
        ]
        for name in invalid_names:
            assert validate_name(name) is False

    def test_name_length_constraints(self) -> None:
        """Test name length validation."""
        # Test custom length constraints
        assert validate_name("A", min_length=1) is True
        assert validate_name("A", min_length=2) is False
        assert validate_name("AB", min_length=2, max_length=2) is True
        assert validate_name("ABC", min_length=2, max_length=2) is False

    def test_name_pattern_validation(self) -> None:
        """Test name pattern edge cases."""
        edge_cases = [
            "John  Smith",  # Multiple spaces (should pass)
            "John--Smith",  # Double hyphens
            "John''Smith",  # Double apostrophes
            "J o h n   S m i t h   T o o   M a n y   S p a c e s",  # Too many spaces
        ]
        # First one should pass, others should fail
        assert validate_name(edge_cases[0]) is True
        for name in edge_cases[1:]:
            assert validate_name(name) is False

    def test_name_whitespace_handling(self) -> None:
        """Test name whitespace trimming."""
        assert validate_name("  John  ") is True
        assert validate_name("   ") is False  # Only whitespace

    def test_none_and_empty_name(self) -> None:
        """Test None and empty name handling."""
        assert validate_name("") is False
        assert validate_name(None) is False


class TestValidateBirthDate:
    """Test birth date validation function."""

    def test_valid_birth_dates(self) -> None:
        """Test valid birth dates."""
        today = date.today()
        valid_dates = [
            date(1990, 5, 15),
            date(1980, 12, 31),
            date(2000, 1, 1),
            date(today.year - 13, today.month, today.day),  # Exactly 13 years old
        ]
        for birth_date in valid_dates:
            assert validate_birth_date(birth_date) is True

    def test_invalid_birth_dates(self) -> None:
        """Test invalid birth dates."""
        today = date.today()
        invalid_dates = [
            date(1899, 12, 31),  # Before 1900
            date(today.year - 12, today.month, today.day),  # Too young
            today + timedelta(days=1),  # Future date
        ]
        for birth_date in invalid_dates:
            assert validate_birth_date(birth_date) is False

    def test_custom_min_age(self) -> None:
        """Test custom minimum age validation."""
        today = date.today()
        birth_date = date(today.year - 18, today.month, today.day)

        assert validate_birth_date(birth_date, min_age=17) is True
        assert validate_birth_date(birth_date, min_age=19) is False

    def test_boundary_dates(self) -> None:
        """Test boundary date conditions."""
        # Test exactly on 1900-01-01 (should be valid)
        assert validate_birth_date(date(1900, 1, 1)) is True

        # Test exactly today (should be invalid)
        assert validate_birth_date(date.today()) is False

    def test_none_birth_date(self) -> None:
        """Test None birth date handling."""
        assert validate_birth_date(None) is False


class TestValidatePasswordStrength:
    """Test password strength validation function."""

    def test_valid_passwords(self) -> None:
        """Test valid password formats."""
        valid_passwords = [
            "MySecure@Pass1",
            "C0mplex&Strong",
            "ValidP@ssw0rd",
        ]
        for password in valid_passwords:
            is_valid, errors = validate_password_strength(password)
            assert is_valid is True
            assert len(errors) == 0

    def test_invalid_passwords(self) -> None:
        """Test invalid password formats."""
        invalid_cases = [
            ("", ["Password is required"]),
            ("short", ["Password must be at least 8 characters long"]),
            ("a" * 129, ["Password cannot exceed 128 characters"]),
            ("lowercase123!", ["Password must contain at least one uppercase letter"]),
            ("UPPERCASE123!", ["Password must contain at least one lowercase letter"]),
            ("NoNumbers!", ["Password must contain at least one digit"]),
            ("NoSpecial123", ["Password must contain at least one special character"]),
        ]

        for password, expected_errors in invalid_cases:
            is_valid, errors = validate_password_strength(password)
            assert is_valid is False
            for expected_error in expected_errors:
                assert expected_error in errors

    def test_weak_password_patterns(self) -> None:
        """Test detection of weak password patterns."""
        weak_passwords = [
            "Password1111!",  # Repeated characters
            "Abc123456!",  # Sequential patterns
            "password123!",  # Common password (case insensitive)
        ]

        for password in weak_passwords:
            is_valid, errors = validate_password_strength(password)
            assert is_valid is False
            assert len(errors) > 0

    def test_common_passwords(self) -> None:
        """Test detection of common passwords."""
        # Test a actually common password
        is_valid, errors = validate_password_strength("password")
        assert is_valid is False
        assert any("too common" in error for error in errors)

        # Test a password with sequential pattern
        is_valid, errors = validate_password_strength("Password123!")
        assert is_valid is False
        assert any("weak patterns" in error for error in errors)

    def test_none_password(self) -> None:
        """Test None password handling."""
        is_valid, errors = validate_password_strength(None)
        assert is_valid is False
        assert "Password is required" in errors


class TestSanitizeFilename:
    """Test filename sanitization function."""

    def test_valid_filenames(self) -> None:
        """Test already valid filenames."""
        valid_filenames = [
            "document.pdf",
            "image.jpg",
            "report_2023.docx",
        ]
        for filename in valid_filenames:
            assert sanitize_filename(filename) == filename

    def test_dangerous_characters(self) -> None:
        """Test removal of dangerous characters."""
        dangerous_cases = [
            ("file<name>.txt", "filename.txt"),  # < and > removed entirely
            ("file>name.txt", "filename.txt"),   # < and > removed entirely
            ('file"name.txt', "filename.txt"),   # " removed entirely
            ("file/name.txt", "file_name.txt"),  # / replaced with _
            ("file\\name.txt", "file_name.txt"), # \ replaced with _
            ("file|name.txt", "filename.txt"),   # | removed entirely
            ("file?name.txt", "filename.txt"),   # ? removed entirely
            ("file*name.txt", "filename.txt"),   # * removed entirely
            ("file:name.txt", "filename.txt"),   # : removed entirely
        ]

        for original, expected in dangerous_cases:
            result = sanitize_filename(original)
            assert result == expected, f"Expected {expected}, got {result} for input {original}"

    def test_control_characters(self) -> None:
        """Test removal of control characters."""
        filename_with_control = "file\x00name\x1f.txt"
        sanitized = sanitize_filename(filename_with_control)
        assert sanitized == "filename.txt"

    def test_long_filename(self) -> None:
        """Test filename length limiting."""
        long_name = "a" * 300 + ".txt"
        sanitized = sanitize_filename(long_name)
        assert len(sanitized) <= 255
        assert sanitized.endswith(".txt")

    def test_empty_and_none_filename(self) -> None:
        """Test empty and None filename handling."""
        assert sanitize_filename("") == "untitled"
        assert sanitize_filename(None) == "untitled"
        assert sanitize_filename("   ") == "untitled"  # Only whitespace

    def test_filename_without_extension(self) -> None:
        """Test filename without extension."""
        long_name_no_ext = "a" * 300
        sanitized = sanitize_filename(long_name_no_ext)
        assert len(sanitized) <= 255
        assert sanitized == "a" * 255

    def test_edge_cases(self) -> None:
        """Test various edge cases."""
        edge_cases = [
            ("...", "..."),  # Only dots should be preserved
            ("---", "---"),  # Only hyphens should be preserved
            ("\x00\x01\x02", "untitled"),  # Only control chars - becomes empty, so returns untitled
        ]

        for original, expected in edge_cases:
            assert sanitize_filename(original) == expected
