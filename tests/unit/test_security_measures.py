"""Unit tests for security validation functions."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.utils.security_validators import (
    DocumentSecurityValidator,
    SecurityError,
    get_security_validator,
)


class TestDocumentSecurityValidator:
    """Unit tests for document security validation."""

    @pytest.fixture
    def validator(self):
        """Create security validator instance for testing."""
        return DocumentSecurityValidator()

    @pytest.fixture
    def valid_pdf_path(self, tmp_path):
        """Create a valid PDF file for testing."""
        pdf_path = tmp_path / "valid.pdf"
        # Write valid PDF header and some content
        with open(pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(b'%PDF content here...\n')
            f.write(b'A' * 1000)  # Some content to make it non-empty
        return pdf_path

    @pytest.fixture
    def invalid_pdf_path(self, tmp_path):
        """Create an invalid file for testing."""
        invalid_path = tmp_path / "invalid.pdf"
        with open(invalid_path, 'wb') as f:
            f.write(b'Not a PDF file')
        return invalid_path

    def test_validate_pdf_file_success(self, validator, valid_pdf_path):
        """Test successful PDF validation."""
        # Arrange
        with patch('app.utils.security_validators.fitz.open') as mock_fitz:
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 5
            mock_doc.needs_pass = False
            mock_fitz.return_value = mock_doc

            # Act
            result = validator.validate_pdf_file(valid_pdf_path)

            # Assert
            assert result["valid"] is True
            assert result["page_count"] == 5
            assert result["is_encrypted"] is False
            assert result["file_size"] > 0
            assert len(result["errors"]) == 0

    def test_validate_pdf_file_not_found(self, validator):
        """Test validation when file doesn't exist."""
        # Arrange
        nonexistent_path = Path("/nonexistent/file.pdf")

        # Act & Assert
        with pytest.raises(SecurityError, match="File does not exist"):
            validator.validate_pdf_file(nonexistent_path)

    def test_validate_pdf_file_empty(self, validator, tmp_path):
        """Test validation of empty file."""
        # Arrange
        empty_path = tmp_path / "empty.pdf"
        empty_path.touch()

        # Act & Assert
        with pytest.raises(SecurityError, match="File is empty"):
            validator.validate_pdf_file(empty_path)

    def test_validate_pdf_file_too_large(self, validator, tmp_path):
        """Test validation of file exceeding size limit."""
        # Arrange
        large_path = tmp_path / "large.pdf"
        with open(large_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            # Write more than 50MB
            f.write(b'A' * (51 * 1024 * 1024))

        # Act & Assert
        with pytest.raises(SecurityError, match="exceeds maximum allowed size"):
            validator.validate_pdf_file(large_path)

    def test_validate_pdf_file_invalid_header(self, validator, invalid_pdf_path):
        """Test validation of file with invalid PDF header."""
        # Act & Assert
        with pytest.raises(SecurityError, match="Invalid PDF header"):
            validator.validate_pdf_file(invalid_pdf_path)

    def test_validate_pdf_file_encrypted(self, validator, valid_pdf_path):
        """Test validation of encrypted PDF."""
        # Arrange
        with patch('app.utils.security_validators.fitz.open') as mock_fitz:
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 3
            mock_doc.needs_pass = True  # Encrypted
            mock_fitz.return_value = mock_doc

            # Act
            result = validator.validate_pdf_file(valid_pdf_path)

            # Assert
            assert result["valid"] is True
            assert result["is_encrypted"] is True
            assert "password protected" in result["warnings"][0]

    def test_sanitize_text_script_injection(self, validator):
        """Test sanitization of JavaScript injection patterns."""
        # Arrange
        malicious_text = "Normal text <script>alert('xss')</script> more text"

        # Act
        result = validator.sanitize_extracted_text(malicious_text)

        # Assert
        assert "<script>" not in result
        assert "alert" not in result
        assert "Normal text" in result
        assert "more text" in result

    def test_sanitize_text_sql_injection(self, validator):
        """Test sanitization of SQL injection patterns."""
        # Arrange
        malicious_text = "Text with ' OR '1'='1'; DROP TABLE users; -- comment"

        # Act
        result = validator.sanitize_extracted_text(malicious_text)

        # Assert
        assert "DROP TABLE" not in result
        assert "Text with" in result

    def test_sanitize_text_command_injection(self, validator):
        """Test sanitization of command injection patterns."""
        # Arrange
        malicious_text = "Text with $(rm -rf /) and `cat /etc/passwd` injection"

        # Act
        result = validator.sanitize_extracted_text(malicious_text)

        # Assert
        assert "$(" not in result
        assert "`cat" not in result
        assert "Text with" in result

    def test_sanitize_text_path_traversal(self, validator):
        """Test sanitization of path traversal patterns."""
        # Arrange
        malicious_text = "File path ../../../etc/passwd and ..\\windows\\system32"

        # Act
        result = validator.sanitize_extracted_text(malicious_text)

        # Assert
        assert "../" not in result
        assert "..\\" not in result
        assert "File path" in result

    def test_sanitize_text_empty_input(self, validator):
        """Test sanitization with empty input."""
        # Act
        result = validator.sanitize_extracted_text("")

        # Assert
        assert result == ""

    def test_sanitize_text_none_input(self, validator):
        """Test sanitization with None input."""
        # Act
        result = validator.sanitize_extracted_text(None)

        # Assert
        assert result is None

    def test_clean_text_null_bytes(self, validator):
        """Test cleaning of null bytes from text."""
        # Arrange
        text_with_nulls = "Text\x00with\x00null\x00bytes"

        # Act
        result = validator._clean_text(text_with_nulls)

        # Assert
        assert "\x00" not in result
        assert "Textwithnullbytes" in result

    def test_clean_text_line_endings(self, validator):
        """Test normalization of line endings."""
        # Arrange
        text_with_mixed_endings = "Line1\r\nLine2\rLine3\nLine4"

        # Act
        result = validator._clean_text(text_with_mixed_endings)

        # Assert
        assert "\r\n" not in result
        assert "\r" not in result
        lines = result.split("\n")
        assert len(lines) == 4

    def test_create_audit_log_entry(self, validator):
        """Test audit log entry creation."""
        # Arrange
        operation = "test_operation"
        document_id = "doc_123"
        details = {"key": "value"}

        # Act
        result = validator.create_audit_log_entry(operation, document_id, details)

        # Assert
        assert result["operation"] == operation
        assert result["document_id"] == document_id
        assert result["details"] == details
        assert "timestamp" in result
        assert "process_id" in result

    def test_secure_file_cleanup_success(self, validator, tmp_path):
        """Test secure file cleanup for existing files."""
        # Arrange
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("sensitive content")
        file_paths = [test_file]

        # Act
        result = validator.secure_file_cleanup(file_paths)

        # Assert
        assert result[str(test_file)] is True
        assert not test_file.exists()

    def test_secure_file_cleanup_nonexistent(self, validator):
        """Test secure file cleanup for non-existent files."""
        # Arrange
        nonexistent_file = Path("/nonexistent/file.txt")
        file_paths = [nonexistent_file]

        # Act
        result = validator.secure_file_cleanup(file_paths)

        # Assert
        assert result[str(nonexistent_file)] is True

    def test_secure_file_cleanup_error_handling(self, validator, tmp_path):
        """Test secure file cleanup error handling."""
        # Arrange
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("content")

        with patch('pathlib.Path.unlink', side_effect=PermissionError("Permission denied")):
            # Act
            result = validator.secure_file_cleanup([test_file])

            # Assert
            assert result[str(test_file)] is False

    def test_file_size_validation_bounds(self, validator):
        """Test file size validation at boundary conditions."""
        # Test at exactly the limit
        assert validator.max_file_size == 50 * 1024 * 1024  # 50MB

    def test_pdf_magic_bytes_validation(self, validator, tmp_path):
        """Test PDF magic bytes validation for different PDF versions."""
        # Test various PDF versions
        pdf_versions = [b'%PDF-1.0', b'%PDF-1.4', b'%PDF-1.7']

        for version in pdf_versions:
            pdf_path = tmp_path / f"test_{version.decode().replace('.', '_')}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(version)
                f.write(b'\ncontent')

            # Should not raise exception for valid headers
            with patch('app.utils.security_validators.fitz.open') as mock_fitz:
                mock_doc = MagicMock()
                mock_doc.__len__.return_value = 1
                mock_doc.needs_pass = False
                mock_fitz.return_value = mock_doc

                result = validator.validate_pdf_file(pdf_path)
                assert result["valid"] is True

    def test_injection_pattern_compilation(self):
        """Test that injection patterns are properly compiled."""
        from app.utils.security_validators import COMPILED_INJECTION_PATTERNS

        # Verify patterns are compiled
        assert len(COMPILED_INJECTION_PATTERNS) > 0

        # Test each pattern can be used
        test_text = "test string"
        for pattern in COMPILED_INJECTION_PATTERNS:
            matches = pattern.findall(test_text)
            assert isinstance(matches, list)

    def test_factory_function(self):
        """Test factory function returns DocumentSecurityValidator instance."""
        # Act
        result = get_security_validator()

        # Assert
        assert isinstance(result, DocumentSecurityValidator)

    @patch('app.utils.security_validators.logger')
    def test_audit_logging_integration(self, mock_logger, validator):
        """Test that audit entries are properly logged."""
        # Act
        validator.create_audit_log_entry("test", "doc_1", {"test": "data"})

        # Assert
        mock_logger.info.assert_called_once()

    def test_security_error_exception(self):
        """Test SecurityError exception can be raised and caught."""
        # Act & Assert
        with pytest.raises(SecurityError):
            raise SecurityError("Test security error")

    @patch('app.utils.security_validators.os.urandom')
    def test_secure_overwrite_before_deletion(self, mock_urandom, validator, tmp_path):
        """Test that files are securely overwritten before deletion."""
        # Arrange
        test_file = tmp_path / "sensitive.txt"
        test_content = "sensitive information"
        test_file.write_text(test_content)

        mock_urandom.return_value = b'random_data_for_overwrite'

        # Act
        validator.secure_file_cleanup([test_file])

        # Assert
        mock_urandom.assert_called_once_with(len(test_content.encode()))
        assert not test_file.exists()
