"""
TOTP (Time-based One-Time Password) service for 2FA implementation.

This module provides TOTP secret generation, QR code creation, and validation
functionality for two-factor authentication with enhanced backup code security.
"""

import base64
import io
import logging
import secrets

import pyotp
import qrcode
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)


class TOTPSetupData(BaseModel):
    """TOTP setup data structure."""

    secret: str
    qr_code_url: str
    backup_codes: list[str]


class BackupCodeSecurityError(Exception):
    """Exception for backup code security violations."""

    pass


class TOTPService:
    """Service for TOTP-based two-factor authentication."""

    def __init__(self) -> None:
        self.issuer_name = settings.PROJECT_NAME

    def generate_secret(self) -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()

    def generate_backup_codes(self, count: int = 8, strength: str = "high") -> list[str]:
        """
        Generate cryptographically secure backup codes for 2FA recovery.

        Args:
            count: Number of backup codes to generate (default 8)
            strength: Security strength - 'high' or 'standard'

        Returns:
            List of formatted backup codes

        Raises:
            ValueError: If count is invalid
        """
        if count < 1 or count > 20:
            raise ValueError("Backup code count must be between 1 and 20")

        backup_codes = []
        used_codes = set()  # Prevent duplicates

        code_length = 12 if strength == "high" else 8
        max_attempts = count * 10  # Prevent infinite loops
        attempts = 0

        while len(backup_codes) < count and attempts < max_attempts:
            attempts += 1

            if strength == "high":
                # Generate 12-character codes with mixed case and numbers
                code = secrets.token_urlsafe(9)[:code_length].upper()
                # Ensure no ambiguous characters (0, O, I, L, 1)
                code = (
                    code.replace("0", "2")
                    .replace("O", "3")
                    .replace("I", "4")
                    .replace("L", "5")
                    .replace("1", "6")
                )
            else:
                # Standard 8-character hex codes
                code = secrets.token_hex(4).upper()

            # Format with dashes for readability
            if code_length == 12:
                formatted_code = f"{code[:4]}-{code[4:8]}-{code[8:]}"
            else:
                formatted_code = f"{code[:4]}-{code[4:]}"

            # Ensure uniqueness
            if formatted_code not in used_codes:
                used_codes.add(formatted_code)
                backup_codes.append(formatted_code)

        if len(backup_codes) < count:
            raise BackupCodeSecurityError("Failed to generate unique backup codes")

        logger.info(f"Generated {count} backup codes with {strength} strength")
        return backup_codes

    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """Generate QR code URL for TOTP setup."""
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=user_email, issuer_name=self.issuer_name)

        # Generate QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64 data URL
        buffer = io.BytesIO()
        img.save(buffer, "PNG")
        img_data = buffer.getvalue()
        img_base64 = base64.b64encode(img_data).decode()

        return f"data:image/png;base64,{img_base64}"

    def setup_totp(self, user_email: str) -> TOTPSetupData:
        """Setup TOTP for a user and return setup data."""
        secret = self.generate_secret()
        qr_code_url = self.generate_qr_code(user_email, secret)
        backup_codes = self.generate_backup_codes()

        return TOTPSetupData(secret=secret, qr_code_url=qr_code_url, backup_codes=backup_codes)

    def verify_totp(self, secret: str, token: str) -> bool:
        """Verify a TOTP token against the secret."""
        if not secret or not token:
            return False

        try:
            totp = pyotp.TOTP(secret)
            # Allow some time window for clock drift
            return totp.verify(token, valid_window=1)
        except Exception:
            return False

    def verify_backup_code(
        self,
        backup_codes: list[str],
        provided_code: str,
        user_id: str | None = None,
        rate_limit_check: bool = True,
    ) -> tuple[bool, list[str], str | None]:
        """
        Verify a backup code with enhanced security checks.

        Args:
            backup_codes: List of available backup codes
            provided_code: User-provided backup code
            user_id: User ID for rate limiting (optional)
            rate_limit_check: Whether to enforce rate limiting

        Returns:
            tuple: (is_valid, updated_backup_codes, error_message)

        Raises:
            BackupCodeSecurityError: If security violation is detected
        """
        if not backup_codes or not provided_code:
            return False, backup_codes, "Invalid backup code format"

        # Security check: minimum code length
        if len(provided_code.replace("-", "").replace(" ", "")) < 6:
            logger.warning(f"Backup code too short for user {user_id}")
            return False, backup_codes, "Backup code too short"

        # Security check: maximum code length (prevent buffer overflow attempts)
        if len(provided_code) > 20:
            logger.warning(f"Backup code too long for user {user_id}")
            return False, backup_codes, "Backup code too long"

        # Normalize the provided code (case insensitive, remove separators)
        normalized_code = provided_code.upper().replace("-", "").replace(" ", "").strip()

        # Security check: ensure only alphanumeric characters
        if not normalized_code.replace("-", "").isalnum():
            logger.warning(f"Invalid characters in backup code for user {user_id}")
            return False, backup_codes, "Invalid backup code format"

        # Check for common weak backup codes
        weak_codes = {
            "12345678",
            "ABCDEFGH",
            "00000000",
            "11111111",
            "PASSWORD",
            "BACKUP12",
            "CODE1234",
            "TEST1234",
            "ADMIN123",
            "USER1234",
        }

        if normalized_code in weak_codes:
            logger.warning(f"Weak backup code attempt for user {user_id}")
            return False, backup_codes, "Invalid backup code"

        # Search for matching backup code
        for i, backup_code in enumerate(backup_codes):
            # Normalize stored backup code
            normalized_backup = backup_code.upper().replace("-", "").replace(" ", "").strip()

            # Constant-time comparison to prevent timing attacks
            if self._secure_compare(normalized_backup, normalized_code):
                # Remove the used backup code (single use only)
                updated_codes = backup_codes[:i] + backup_codes[i + 1 :]

                logger.info(f"Backup code used successfully for user {user_id}")
                return True, updated_codes, None

        logger.warning(f"Invalid backup code attempt for user {user_id}")
        return False, backup_codes, "Invalid backup code"

    def _secure_compare(self, a: str, b: str) -> bool:
        """
        Constant-time string comparison to prevent timing attacks.

        Args:
            a: First string
            b: Second string

        Returns:
            bool: True if strings match
        """
        if len(a) != len(b):
            return False

        result = 0
        for x, y in zip(a, b, strict=False):
            result |= ord(x) ^ ord(y)

        return result == 0

    def validate_backup_codes_security(self, backup_codes: list[str]) -> tuple[bool, list[str]]:
        """
        Validate backup codes for security requirements.

        Args:
            backup_codes: List of backup codes to validate

        Returns:
            tuple: (are_valid, validation_errors)
        """
        errors = []

        if not backup_codes:
            errors.append("No backup codes provided")
            return False, errors

        if len(backup_codes) < 3:
            errors.append("Minimum 3 backup codes required")

        if len(backup_codes) > 20:
            errors.append("Maximum 20 backup codes allowed")

        # Check for duplicates
        normalized_codes = [code.upper().replace("-", "").replace(" ", "") for code in backup_codes]
        if len(normalized_codes) != len(set(normalized_codes)):
            errors.append("Duplicate backup codes found")

        # Check individual code security
        weak_patterns = ["1234", "ABCD", "0000", "1111", "PASSWORD", "ADMIN", "TEST"]

        for i, code in enumerate(backup_codes):
            normalized = code.upper().replace("-", "").replace(" ", "")

            # Length check
            if len(normalized) < 6:
                errors.append(f"Code {i + 1}: Too short (minimum 6 characters)")

            if len(normalized) > 16:
                errors.append(f"Code {i + 1}: Too long (maximum 16 characters)")

            # Character validation
            if not normalized.isalnum():
                errors.append(f"Code {i + 1}: Contains invalid characters")

            # Weak pattern check
            for pattern in weak_patterns:
                if pattern in normalized:
                    errors.append(f"Code {i + 1}: Contains weak pattern")
                    break

        return len(errors) == 0, errors

    def is_totp_enabled(self, totp_secret: str | None) -> bool:
        """Check if TOTP is enabled for a user."""
        return totp_secret is not None and len(totp_secret) > 0


# Global TOTP service instance
totp_service = TOTPService()
