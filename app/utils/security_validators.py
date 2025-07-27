"""Security validation functions for document processing."""

import logging
import os
import re
from datetime import UTC
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# Maximum file size: 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes

# PDF magic bytes for validation
PDF_MAGIC_BYTES = [
    b'%PDF-1.0',
    b'%PDF-1.1',
    b'%PDF-1.2',
    b'%PDF-1.3',
    b'%PDF-1.4',
    b'%PDF-1.5',
    b'%PDF-1.6',
    b'%PDF-1.7',
]

# Patterns that could indicate injection attempts
INJECTION_PATTERNS = [
    # JavaScript injection
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    r'vbscript:',

    # SQL injection patterns
    r"(?:'[^']*'[;])|(?:--)|(?:\/\*)|(?:\*\/)",
    r'union.*select.*from',
    r'drop\s+table',
    r'delete\s+from',
    r'insert\s+into',

    # XSS patterns
    r'<iframe[^>]*>.*?</iframe>',
    r'<object[^>]*>.*?</object>',
    r'<embed[^>]*>.*?</embed>',
    r'onload\s*=',
    r'onerror\s*=',
    r'onclick\s*=',

    # Command injection
    r'[;&|`$]',
    r'\$\(',
    r'`[^`]*`',

    # Path traversal
    r'\.\./',
    r'\.\.\\',
]

# Compile patterns for performance
COMPILED_INJECTION_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in INJECTION_PATTERNS]


class DocumentSecurityValidator:
    """Handles security validation for document processing."""

    def __init__(self):
        """Initialize the security validator."""
        self.max_file_size = MAX_FILE_SIZE

    def validate_pdf_file(self, file_path: Path) -> dict[str, Any]:
        """
        Comprehensive security validation for PDF files.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dict with validation results

        Raises:
            SecurityError: If validation fails
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "file_size": 0,
            "is_encrypted": False,
            "page_count": 0
        }

        try:
            # Check 1: File exists and is readable
            if not file_path.exists():
                raise SecurityError(f"File does not exist: {file_path}")

            if not file_path.is_file():
                raise SecurityError(f"Path is not a file: {file_path}")

            # Check 2: File size validation
            file_size = file_path.stat().st_size
            validation_results["file_size"] = file_size

            if file_size > self.max_file_size:
                raise SecurityError(f"File size {file_size} exceeds maximum allowed size {self.max_file_size}")

            if file_size == 0:
                raise SecurityError("File is empty")

            # Check 3: PDF header validation
            with open(file_path, 'rb') as f:
                header = f.read(10)

            if not any(header.startswith(magic) for magic in PDF_MAGIC_BYTES):
                raise SecurityError("Invalid PDF header - file may be corrupted or not a valid PDF")

            # Check 4: PDF structure validation using PyMuPDF
            try:
                pdf_document = fitz.open(file_path)
                validation_results["page_count"] = len(pdf_document)
                validation_results["is_encrypted"] = pdf_document.needs_pass

                # Check for password protection
                if pdf_document.needs_pass:
                    validation_results["warnings"].append("Document is password protected")

                # Basic structure validation
                if len(pdf_document) == 0:
                    validation_results["warnings"].append("Document has no pages")

                pdf_document.close()

            except Exception as pdf_error:
                raise SecurityError(f"PDF structure validation failed: {str(pdf_error)}") from pdf_error

            logger.info(f"PDF validation successful for {file_path.name}: {validation_results}")
            return validation_results

        except SecurityError:
            validation_results["valid"] = False
            raise
        except Exception as e:
            validation_results["valid"] = False
            raise SecurityError(f"Unexpected error during validation: {str(e)}") from e

    def sanitize_extracted_text(self, text: str) -> str:
        """
        Sanitize extracted text to remove potential injection patterns.

        Args:
            text: Raw extracted text

        Returns:
            Sanitized text
        """
        if not text:
            return text

        original_length = len(text)
        sanitized = text
        removed_patterns = []

        # Remove potential injection patterns
        for pattern in COMPILED_INJECTION_PATTERNS:
            matches = pattern.findall(sanitized)
            if matches:
                removed_patterns.extend(matches)
                sanitized = pattern.sub('', sanitized)

        # Log any sanitization actions
        if removed_patterns:
            logger.warning(f"Removed {len(removed_patterns)} potential injection patterns from text")
            logger.debug(f"Removed patterns: {removed_patterns[:5]}...")  # Log first 5 for debugging

        # Additional cleanup
        sanitized = self._clean_text(sanitized)

        final_length = len(sanitized)
        if final_length != original_length:
            logger.info(f"Text sanitized: {original_length} -> {final_length} characters")

        return sanitized

    def _clean_text(self, text: str) -> str:
        """
        Additional text cleaning for safety.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Remove null bytes
        text = text.replace('\x00', '')

        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove excessive whitespace but preserve paragraph structure
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Clean each line but preserve intentional spacing
            cleaned_line = ' '.join(line.split())
            cleaned_lines.append(cleaned_line)

        return '\n'.join(cleaned_lines)

    def create_audit_log_entry(self, operation: str, document_id: str, details: dict[str, Any]) -> dict[str, Any]:
        """
        Create an audit log entry for document processing operations.

        Args:
            operation: Type of operation (e.g., 'upload', 'process', 'delete')
            document_id: Document identifier
            details: Additional operation details

        Returns:
            Audit log entry
        """
        audit_entry = {
            "timestamp": self._get_utc_timestamp(),
            "operation": operation,
            "document_id": document_id,
            "details": details,
            "process_id": os.getpid(),
        }

        # Log the audit entry
        logger.info(f"AUDIT: {operation} - Document {document_id}", extra=audit_entry)

        return audit_entry

    def secure_file_cleanup(self, file_paths: list[Path]) -> dict[str, bool]:
        """
        Securely delete temporary files after processing.

        Args:
            file_paths: List of file paths to delete

        Returns:
            Dict mapping file path to deletion success
        """
        cleanup_results = {}

        for file_path in file_paths:
            try:
                if file_path.exists():
                    # Overwrite file content before deletion for security
                    if file_path.is_file():
                        file_size = file_path.stat().st_size
                        with open(file_path, 'wb') as f:
                            f.write(os.urandom(file_size))
                        file_path.unlink()

                    cleanup_results[str(file_path)] = True
                    logger.debug(f"Securely deleted file: {file_path}")
                else:
                    cleanup_results[str(file_path)] = True  # Already doesn't exist

            except Exception as e:
                cleanup_results[str(file_path)] = False
                logger.error(f"Failed to securely delete {file_path}: {str(e)}")

        return cleanup_results

    def _get_utc_timestamp(self) -> str:
        """Get current UTC timestamp in ISO format."""
        from datetime import datetime
        return datetime.now(UTC).isoformat()


class SecurityError(Exception):
    """Custom exception for security validation failures."""
    pass


def get_security_validator() -> DocumentSecurityValidator:
    """Factory function to get DocumentSecurityValidator instance."""
    return DocumentSecurityValidator()
