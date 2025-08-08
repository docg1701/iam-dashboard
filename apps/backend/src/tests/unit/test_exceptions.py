"""
Tests for exceptions module.

This module tests custom exception classes and HTTP exception mapping.
"""

from typing import cast

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DashboardException,
    DatabaseError,
    ExternalServiceError,
    FileProcessingError,
    NotFoundError,
    ValidationError,
    dashboard_exception_to_http,
)


def test_dashboard_exception_creation() -> None:
    """Test basic DashboardException creation."""
    exc = DashboardException("Test message", "TEST_CODE", {"key": "value"})

    assert exc.message == "Test message"
    assert exc.error_code == "TEST_CODE"
    assert exc.details == {"key": "value"}
    assert str(exc) == "Test message"


def test_dashboard_exception_defaults() -> None:
    """Test DashboardException with default values."""
    exc = DashboardException("Test message")

    assert exc.message == "Test message"
    assert exc.error_code is None
    assert exc.details == {}


def test_validation_error() -> None:
    """Test ValidationError creation."""
    exc = ValidationError("Validation failed", "VALIDATION_ERROR")

    assert isinstance(exc, DashboardException)
    assert exc.message == "Validation failed"
    assert exc.error_code == "VALIDATION_ERROR"


def test_authentication_error() -> None:
    """Test AuthenticationError creation."""
    exc = AuthenticationError("Auth failed")

    assert isinstance(exc, DashboardException)
    assert exc.message == "Auth failed"


def test_authorization_error() -> None:
    """Test AuthorizationError creation."""
    exc = AuthorizationError("Access denied")

    assert isinstance(exc, DashboardException)
    assert exc.message == "Access denied"


def test_not_found_error() -> None:
    """Test NotFoundError creation."""
    exc = NotFoundError("Resource not found")

    assert isinstance(exc, DashboardException)
    assert exc.message == "Resource not found"


def test_conflict_error() -> None:
    """Test ConflictError creation."""
    exc = ConflictError("Resource conflict", "CONFLICT", {"field": "value"})

    assert isinstance(exc, DashboardException)
    assert exc.message == "Resource conflict"
    assert exc.error_code == "CONFLICT"
    assert exc.details == {"field": "value"}


def test_database_error() -> None:
    """Test DatabaseError creation."""
    original_error = SQLAlchemyError("SQL error")
    exc = DatabaseError("Database failed", original_error, error_code="DB_ERROR")

    assert isinstance(exc, DashboardException)
    assert exc.message == "Database failed"
    assert exc.original_error == original_error
    assert exc.error_code == "DB_ERROR"


def test_database_error_without_original() -> None:
    """Test DatabaseError without original error."""
    exc = DatabaseError("Database failed")

    assert isinstance(exc, DashboardException)
    assert exc.message == "Database failed"
    assert exc.original_error is None


def test_file_processing_error() -> None:
    """Test FileProcessingError creation."""
    exc = FileProcessingError("File processing failed")

    assert isinstance(exc, DashboardException)
    assert exc.message == "File processing failed"


def test_external_service_error() -> None:
    """Test ExternalServiceError creation."""
    exc = ExternalServiceError("Service unavailable")

    assert isinstance(exc, DashboardException)
    assert exc.message == "Service unavailable"


def test_dashboard_exception_to_http_validation_error() -> None:
    """Test ValidationError to HTTP mapping."""
    exc = ValidationError("Invalid input", "VALIDATION_001", {"field": "email"})
    http_exc = dashboard_exception_to_http(exc)

    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == 400
    detail = cast("dict[str, object]", http_exc.detail)
    assert isinstance(detail, dict)
    assert detail["message"] == "Invalid input"
    assert detail["error_code"] == "VALIDATION_001"
    assert detail["details"] == {"field": "email"}


def test_dashboard_exception_to_http_authentication_error() -> None:
    """Test AuthenticationError to HTTP mapping."""
    exc = AuthenticationError("Invalid credentials", "AUTH_001")
    http_exc = dashboard_exception_to_http(exc)

    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == 401
    detail = cast("dict[str, object]", http_exc.detail)
    assert isinstance(detail, dict)
    assert detail["message"] == "Invalid credentials"
    assert detail["error_code"] == "AUTH_001"


def test_dashboard_exception_to_http_authorization_error() -> None:
    """Test AuthorizationError to HTTP mapping."""
    exc = AuthorizationError("Access denied", "AUTHZ_001")
    http_exc = dashboard_exception_to_http(exc)

    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == 403
    detail = cast("dict[str, object]", http_exc.detail)
    assert isinstance(detail, dict)
    assert detail["message"] == "Access denied"
    assert detail["error_code"] == "AUTHZ_001"


def test_dashboard_exception_to_http_not_found_error() -> None:
    """Test NotFoundError to HTTP mapping."""
    exc = NotFoundError("Resource not found", "NOT_FOUND_001")
    http_exc = dashboard_exception_to_http(exc)

    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == 404
    detail = cast("dict[str, object]", http_exc.detail)
    assert isinstance(detail, dict)
    assert detail["message"] == "Resource not found"
    assert detail["error_code"] == "NOT_FOUND_001"


def test_dashboard_exception_to_http_conflict_error() -> None:
    """Test ConflictError to HTTP mapping."""
    exc = ConflictError("Resource conflict", "CONFLICT_001", {"field": "cpf"})
    http_exc = dashboard_exception_to_http(exc)

    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == 409
    detail = cast("dict[str, object]", http_exc.detail)
    assert isinstance(detail, dict)
    assert detail["message"] == "Resource conflict"
    assert detail["error_code"] == "CONFLICT_001"
    assert detail["details"] == {"field": "cpf"}


def test_dashboard_exception_to_http_database_error() -> None:
    """Test DatabaseError to HTTP mapping."""
    exc = DatabaseError("Database failed", error_code="DB_001")
    http_exc = dashboard_exception_to_http(exc)

    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == 500
    detail = cast("dict[str, object]", http_exc.detail)
    assert isinstance(detail, dict)
    assert detail["message"] == "Internal server error"
    assert detail["error_code"] == "DB_001"


def test_dashboard_exception_to_http_file_processing_error() -> None:
    """Test FileProcessingError to HTTP mapping."""
    exc = FileProcessingError("File failed", error_code="FILE_001")
    http_exc = dashboard_exception_to_http(exc)

    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == 500
    detail = cast("dict[str, object]", http_exc.detail)
    assert isinstance(detail, dict)
    assert detail["message"] == "Internal server error"
    assert detail["error_code"] == "FILE_001"


def test_dashboard_exception_to_http_external_service_error() -> None:
    """Test ExternalServiceError to HTTP mapping."""
    exc = ExternalServiceError("Service failed", error_code="EXT_001")
    http_exc = dashboard_exception_to_http(exc)

    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == 500
    detail = cast("dict[str, object]", http_exc.detail)
    assert isinstance(detail, dict)
    assert detail["message"] == "Internal server error"
    assert detail["error_code"] == "EXT_001"


def test_dashboard_exception_to_http_unknown_error() -> None:
    """Test unknown exception to HTTP mapping."""
    exc = DashboardException("Unknown error")
    http_exc = dashboard_exception_to_http(exc)

    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == 500
    detail = cast("dict[str, object]", http_exc.detail)
    assert isinstance(detail, dict)
    assert detail["message"] == "An unexpected error occurred"
    assert detail["error_code"] == "INTERNAL_ERROR"
