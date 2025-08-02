"""
TOTP (Time-based One-Time Password) service for 2FA implementation.

This module provides TOTP secret generation, QR code creation, and validation
functionality for two-factor authentication.
"""

import base64
import io
import secrets

import pyotp
import qrcode
from pydantic import BaseModel

from .config import settings


class TOTPSetupData(BaseModel):
    """TOTP setup data structure."""

    secret: str
    qr_code_url: str
    backup_codes: list[str]


class TOTPService:
    """Service for TOTP-based two-factor authentication."""

    def __init__(self):
        self.issuer_name = settings.PROJECT_NAME

    def generate_secret(self) -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()

    def generate_backup_codes(self, count: int = 8) -> list[str]:
        """Generate backup codes for 2FA recovery."""
        backup_codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = secrets.token_hex(4).upper()
            backup_codes.append(f"{code[:4]}-{code[4:]}")
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
        img.save(buffer, format="PNG")
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
        self, backup_codes: list[str], provided_code: str
    ) -> tuple[bool, list[str]]:
        """
        Verify a backup code and return updated backup codes list.

        Returns:
            tuple: (is_valid, updated_backup_codes)
        """
        if not backup_codes or not provided_code:
            return False, backup_codes

        # Normalize the provided code
        normalized_code = provided_code.upper().replace("-", "").replace(" ", "")

        for i, backup_code in enumerate(backup_codes):
            normalized_backup = backup_code.replace("-", "")
            if normalized_backup == normalized_code:
                # Remove the used backup code
                updated_codes = backup_codes[:i] + backup_codes[i + 1 :]
                return True, updated_codes

        return False, backup_codes

    def is_totp_enabled(self, totp_secret: str | None) -> bool:
        """Check if TOTP is enabled for a user."""
        return totp_secret is not None and len(totp_secret) > 0


# Global TOTP service instance
totp_service = TOTPService()
