"""Tests for TOTP service functionality."""

import re

import pyotp
import pytest

from src.core.totp import TOTPService, TOTPSetupData, totp_service


class TestTOTPService:
    """Test TOTP service functionality."""

    @pytest.fixture
    def totp_service_instance(self):
        """Create TOTP service instance for testing."""
        return TOTPService()

    def test_totp_service_init(self, totp_service_instance):
        """Test TOTP service initialization."""
        assert totp_service_instance.issuer_name is not None
        assert isinstance(totp_service_instance.issuer_name, str)

    def test_generate_secret(self, totp_service_instance):
        """Test TOTP secret generation."""
        secret = totp_service_instance.generate_secret()

        # Should be 32-character base32 string
        assert len(secret) == 32
        assert re.match(r"^[A-Z2-7]{32}$", secret)

        # Should generate different secrets each time
        secret2 = totp_service_instance.generate_secret()
        assert secret != secret2

    def test_generate_backup_codes(self, totp_service_instance):
        """Test backup codes generation."""
        codes = totp_service_instance.generate_backup_codes()

        # Should generate 8 codes by default
        assert len(codes) == 8

        # Each code should be in format XXXX-XXXX
        for code in codes:
            assert re.match(r"^[A-F0-9]{4}-[A-F0-9]{4}$", code)

        # All codes should be unique
        assert len(set(codes)) == len(codes)

    def test_generate_backup_codes_custom_count(self, totp_service_instance):
        """Test backup codes generation with custom count."""
        codes = totp_service_instance.generate_backup_codes(count=5)
        assert len(codes) == 5

    def test_generate_qr_code(self, totp_service_instance):
        """Test QR code generation."""
        user_email = "test@example.com"
        secret = "JBSWY3DPEHPK3PXP"  # Known test secret

        qr_code_url = totp_service_instance.generate_qr_code(user_email, secret)

        # Should be a data URL
        assert qr_code_url.startswith("data:image/png;base64,")

        # Should contain base64 encoded data
        base64_data = qr_code_url.split(",")[1]
        assert len(base64_data) > 100  # QR code should be substantial

    def test_setup_totp(self, totp_service_instance):
        """Test complete TOTP setup."""
        user_email = "test@example.com"

        setup_data = totp_service_instance.setup_totp(user_email)

        assert isinstance(setup_data, TOTPSetupData)
        assert len(setup_data.secret) == 32
        assert re.match(r"^[A-Z2-7]{32}$", setup_data.secret)
        assert setup_data.qr_code_url.startswith("data:image/png;base64,")
        assert len(setup_data.backup_codes) == 8

    def test_verify_totp_valid(self, totp_service_instance):
        """Test TOTP verification with valid token."""
        secret = "JBSWY3DPEHPK3PXP"  # Known test secret

        # Generate a valid token
        totp = pyotp.TOTP(secret)
        valid_token = totp.now()

        # Should verify successfully
        assert totp_service_instance.verify_totp(secret, valid_token) is True

    def test_verify_totp_invalid(self, totp_service_instance):
        """Test TOTP verification with invalid token."""
        secret = "JBSWY3DPEHPK3PXP"
        invalid_token = "000000"

        # Should fail verification
        assert totp_service_instance.verify_totp(secret, invalid_token) is False

    def test_verify_totp_empty_inputs(self, totp_service_instance):
        """Test TOTP verification with empty inputs."""
        assert totp_service_instance.verify_totp("", "123456") is False
        assert totp_service_instance.verify_totp("JBSWY3DPEHPK3PXP", "") is False
        assert totp_service_instance.verify_totp("", "") is False

    def test_verify_totp_exception_handling(self, totp_service_instance):
        """Test TOTP verification exception handling."""
        # Invalid secret format should return False
        assert totp_service_instance.verify_totp("invalid_secret", "123456") is False

    def test_verify_backup_code_valid(self, totp_service_instance):
        """Test backup code verification with valid code."""
        backup_codes = ["1234-5678", "ABCD-EFGH", "9999-0000"]
        provided_code = "1234-5678"

        is_valid, updated_codes = totp_service_instance.verify_backup_code(
            backup_codes, provided_code
        )

        assert is_valid is True
        assert len(updated_codes) == 2
        assert "1234-5678" not in updated_codes
        assert "ABCD-EFGH" in updated_codes
        assert "9999-0000" in updated_codes

    def test_verify_backup_code_case_insensitive(self, totp_service_instance):
        """Test backup code verification is case insensitive."""
        backup_codes = ["ABCD-EFGH"]
        provided_code = "abcd-efgh"

        is_valid, updated_codes = totp_service_instance.verify_backup_code(
            backup_codes, provided_code
        )

        assert is_valid is True
        assert len(updated_codes) == 0

    def test_verify_backup_code_format_flexible(self, totp_service_instance):
        """Test backup code verification handles different formats."""
        backup_codes = ["1234-5678"]

        # Test without dash
        is_valid, _ = totp_service_instance.verify_backup_code(backup_codes, "12345678")
        assert is_valid is True

        # Test with spaces
        backup_codes = ["ABCD-EFGH"]
        is_valid, _ = totp_service_instance.verify_backup_code(backup_codes, "ABCD EFGH")
        assert is_valid is True

    def test_verify_backup_code_invalid(self, totp_service_instance):
        """Test backup code verification with invalid code."""
        backup_codes = ["1234-5678", "ABCD-EFGH"]
        provided_code = "9999-9999"

        is_valid, updated_codes = totp_service_instance.verify_backup_code(
            backup_codes, provided_code
        )

        assert is_valid is False
        assert updated_codes == backup_codes  # Should remain unchanged

    def test_verify_backup_code_empty_inputs(self, totp_service_instance):
        """Test backup code verification with empty inputs."""
        backup_codes = ["1234-5678"]

        is_valid, updated_codes = totp_service_instance.verify_backup_code([], "1234-5678")
        assert is_valid is False
        assert updated_codes == []

        is_valid, updated_codes = totp_service_instance.verify_backup_code(backup_codes, "")
        assert is_valid is False
        assert updated_codes == backup_codes

    def test_is_totp_enabled_true(self, totp_service_instance):
        """Test TOTP enabled check with valid secret."""
        assert totp_service_instance.is_totp_enabled("JBSWY3DPEHPK3PXP") is True

    def test_is_totp_enabled_false(self, totp_service_instance):
        """Test TOTP enabled check with invalid/empty secret."""
        assert totp_service_instance.is_totp_enabled(None) is False
        assert totp_service_instance.is_totp_enabled("") is False

    def test_global_totp_service_exists(self):
        """Test that global TOTP service instance exists."""
        assert totp_service is not None
        assert isinstance(totp_service, TOTPService)

    def test_totp_service_time_window(self, totp_service_instance):
        """Test TOTP verification with time window."""
        secret = "JBSWY3DPEHPK3PXP"

        # Mock time to test previous/next window
        import time

        current_time = int(time.time())

        # Test current window
        totp = pyotp.TOTP(secret)
        current_token = totp.at(current_time)
        assert totp_service_instance.verify_totp(secret, current_token) is True

        # Test previous window (should work with valid_window=1)
        previous_token = totp.at(current_time - 30)
        assert totp_service_instance.verify_totp(secret, previous_token) is True

        # Test next window (should work with valid_window=1)
        next_token = totp.at(current_time + 30)
        assert totp_service_instance.verify_totp(secret, next_token) is True


class TestTOTPSetupData:
    """Test TOTPSetupData model."""

    def test_totp_setup_data_creation(self):
        """Test TOTPSetupData model creation."""
        setup_data = TOTPSetupData(
            secret="JBSWY3DPEHPK3PXP",
            qr_code_url="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA",
            backup_codes=["1234-5678", "ABCD-EFGH"],
        )

        assert setup_data.secret == "JBSWY3DPEHPK3PXP"
        assert setup_data.qr_code_url == "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA"
        assert len(setup_data.backup_codes) == 2
        assert "1234-5678" in setup_data.backup_codes

    def test_totp_setup_data_json_serialization(self):
        """Test TOTPSetupData JSON serialization."""
        setup_data = TOTPSetupData(
            secret="JBSWY3DPEHPK3PXP",
            qr_code_url="data:image/png;base64,test",
            backup_codes=["1234-5678"],
        )

        json_str = setup_data.model_dump_json()
        assert '"secret":"JBSWY3DPEHPK3PXP"' in json_str
        assert '"backup_codes":["1234-5678"]' in json_str

        # Test deserialization
        restored = TOTPSetupData.model_validate_json(json_str)
        assert restored.secret == setup_data.secret
        assert restored.backup_codes == setup_data.backup_codes
