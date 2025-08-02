"""Validation utility functions."""

import re
from datetime import date


def validate_ssn(ssn: str) -> bool:
    """Validate Social Security Number format and basic rules.

    Args:
        ssn: SSN string to validate

    Returns:
        True if SSN is valid, False otherwise
    """
    if not ssn:
        return False

    # Check format: XXX-XX-XXXX
    if not re.match(r"^\d{3}-\d{2}-\d{4}$", ssn):
        return False

    # Extract digits for validation
    digits = ssn.replace("-", "")

    # Check for invalid SSN patterns
    if digits == "000000000":
        return False
    if digits[:3] == "000":  # Area number cannot be 000
        return False
    if digits[3:5] == "00":  # Group number cannot be 00
        return False
    if digits[5:] == "0000":  # Serial number cannot be 0000
        return False

    # Check for other invalid patterns
    invalid_patterns = [
        "123456789",
        "111111111",
        "222222222",
        "333333333",
        "444444444",
        "555555555",
        "666666666",
        "777777777",
        "888888888",
        "999999999",
    ]
    return digits not in invalid_patterns


def validate_email(email: str) -> bool:
    """Validate email address format.

    Args:
        email: Email string to validate

    Returns:
        True if email is valid, False otherwise
    """
    if not email:
        return False

    # Basic email regex pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(pattern, email):
        return False

    # Additional checks
    if len(email) > 255:
        return False

    # Check for consecutive dots
    if ".." in email:
        return False

    # Check for valid domain
    parts = email.split("@")
    if len(parts) != 2:
        return False

    local, domain = parts

    # Local part checks
    if not local or len(local) > 64:
        return False
    if local.startswith(".") or local.endswith("."):
        return False

    # Domain part checks
    if not domain or len(domain) > 255:
        return False
    if domain.startswith(".") or domain.endswith("."):
        return False
    return not (domain.startswith("-") or domain.endswith("-"))


def validate_name(name: str, min_length: int = 2, max_length: int = 255) -> bool:
    """Validate person name format.

    Args:
        name: Name string to validate
        min_length: Minimum name length
        max_length: Maximum name length

    Returns:
        True if name is valid, False otherwise
    """
    if not name:
        return False

    # Trim and check length
    name = name.strip()
    if len(name) < min_length or len(name) > max_length:
        return False

    # Check for valid characters (letters, spaces, hyphens, apostrophes)
    pattern = r"^[a-zA-ZÀ-ÿ\s\-']+$"
    if not re.match(pattern, name):
        return False

    # Check for reasonable patterns
    if name.count(" ") > 10:  # Too many spaces
        return False

    return not ("--" in name or "''" in name)  # Consecutive special chars


def validate_birth_date(birth_date: date, min_age: int = 13) -> bool:
    """Validate birth date is within reasonable range.

    Args:
        birth_date: Date of birth to validate
        min_age: Minimum age required

    Returns:
        True if birth date is valid, False otherwise
    """
    if not birth_date:
        return False

    today = date.today()

    # Check minimum date (year 1900)
    min_date = date(1900, 1, 1)
    if birth_date < min_date:
        return False

    # Check maximum date (must be at least min_age years old)
    max_date = date(today.year - min_age, today.month, today.day)
    if birth_date > max_date:
        return False

    # Check not in future
    return not birth_date > today


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """Validate password strength and return specific error messages.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    if not password:
        errors.append("Password is required")
        return False, errors

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if len(password) > 128:
        errors.append("Password cannot exceed 128 characters")

    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")

    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")

    # Check for common weak patterns
    weak_patterns = [
        r"(.)\1{3,}",  # Same character repeated 4+ times
        r"(012|123|234|345|456|567|678|789|890)",  # Sequential numbers
        r"(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)",  # Sequential letters
    ]

    for pattern in weak_patterns:
        if re.search(pattern, password.lower()):
            errors.append("Password contains common weak patterns")
            break

    # Check against common passwords (simplified list)
    common_passwords = {
        "password",
        "12345678",
        "qwerty",
        "abc123",
        "password123",
        "admin",
        "letmein",
        "welcome",
        "monkey",
        "1234567890",
    }

    if password.lower() in common_passwords:
        errors.append("Password is too common")

    return len(errors) == 0, errors


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem
    """
    if not filename:
        return "unnamed_file"

    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove control characters
    filename = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", filename)

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        max_name_len = 255 - len(ext) - 1 if ext else 255
        filename = name[:max_name_len] + ("." + ext if ext else "")

    # Ensure it's not empty after sanitization
    if not filename.strip():
        return "unnamed_file"

    return filename.strip()
