"""Validation utility functions."""

import re
from datetime import date


def validate_cpf(cpf: str | None) -> bool:
    """Validate Brazilian CPF (Cadastro de Pessoa Física) format and check digit.

    Args:
        cpf: CPF string to validate (accepts formats: XXX.XXX.XXX-XX or XXXXXXXXXXX)

    Returns:
        True if CPF is valid, False otherwise
    """
    if not cpf:
        return False

    # First check format - must be exactly XXX.XXX.XXX-XX or 11 digits
    formatted_pattern = re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf)
    unformatted_pattern = re.match(r"^\d{11}$", cpf)

    if not (formatted_pattern or unformatted_pattern):
        return False

    try:
        from cnpj_cpf_validator import CPF

        return CPF.is_valid(cpf)
    except ImportError:
        # Fallback validation if library is not available
        return _validate_cpf_fallback(cpf)


def _validate_cpf_fallback(cpf: str) -> bool:
    """Fallback CPF validation implementation.

    Args:
        cpf: CPF string to validate

    Returns:
        True if CPF is valid, False otherwise
    """
    # Remove formatting
    cpf_digits = re.sub(r"\D", "", cpf)

    # Must have exactly 11 digits
    if len(cpf_digits) != 11:
        return False

    # Check for repeated digits (111.111.111-11, etc.)
    if cpf_digits == cpf_digits[0] * 11:
        return False

    # Calculate first check digit
    sum1 = sum(int(cpf_digits[i]) * (10 - i) for i in range(9))
    remainder1 = sum1 % 11
    check_digit1 = 0 if remainder1 < 2 else 11 - remainder1

    if int(cpf_digits[9]) != check_digit1:
        return False

    # Calculate second check digit
    sum2 = sum(int(cpf_digits[i]) * (11 - i) for i in range(10))
    remainder2 = sum2 % 11
    check_digit2 = 0 if remainder2 < 2 else 11 - remainder2

    return int(cpf_digits[10]) == check_digit2


def validate_email(email: str | None) -> bool:
    """Validate email address format.

    Args:
        email: Email string to validate

    Returns:
        True if email is valid, False otherwise
    """
    # Initial validation
    if not email:
        return False

    # Basic email regex pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return False

    # Split email into parts for detailed validation
    parts = email.split("@")
    if len(parts) != 2:
        return False

    local, domain = parts

    # Compile all validation conditions
    invalid_conditions = [
        len(email) > 255,
        ".." in email,
        not local or len(local) > 64,
        local.startswith(".") or local.endswith("."),
        not domain or len(domain) > 255,
        domain.startswith(".") or domain.endswith("."),
        domain.startswith("-") or domain.endswith("-"),
    ]

    return not any(invalid_conditions)


def validate_name(name: str | None, min_length: int = 2, max_length: int = 255) -> bool:
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


def validate_birth_date(birth_date: date | None, min_age: int = 13) -> bool:
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

    # Check minimum date (after year 1900)
    min_date = date(1900, 1, 1)
    if birth_date < min_date:
        return False

    # Check maximum date (must be at least min_age years old)
    max_date = date(today.year - min_age, today.month, today.day)
    if birth_date > max_date:
        return False

    # Check not in future
    return not birth_date > today


def validate_password_strength(password: str | None) -> tuple[bool, list[str]]:
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
        r"(012|123|234|345|456|567|678|789|890)",  # Sequential numbers (3+ chars)
        r"(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)",  # Sequential letters (3+ chars)
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


def sanitize_filename(filename: str | None) -> str:
    """Sanitize filename for safe storage.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem
    """
    if not filename:
        return "untitled"

    # Remove control characters first
    filename = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", filename)

    # Replace spaces and path separators with underscores, remove other dangerous characters
    filename = re.sub(
        r"[\s/\\]", "_", filename
    )  # Replace spaces, forward/back slashes with underscores
    filename = re.sub(r'[<>:"|?*]', "", filename)  # Remove other dangerous characters entirely

    # Clean up multiple consecutive underscores
    filename = re.sub(r"_+", "_", filename)

    # Remove leading/trailing underscores
    filename = filename.strip("_")

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        max_name_len = 255 - len(ext) - 1 if ext else 255
        filename = name[:max_name_len] + ("." + ext if ext else "")

    # Ensure it's not empty after sanitization
    if not filename.strip():
        return "untitled"

    return filename.strip()
