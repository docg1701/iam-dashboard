"""
Custom exception classes for the IAM Dashboard application.

All exceptions should inherit from the base DashboardException class
and provide meaningful error messages for debugging and user feedback.
"""

from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError


class DashboardException(Exception):
    """Base exception class for IAM Dashboard application."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(DashboardException):
    """Raised when input validation fails."""

    pass


class AuthenticationError(DashboardException):
    """Raised when authentication fails."""

    pass


class AuthorizationError(DashboardException):
    """Raised when user lacks required permissions."""

    pass


class NotFoundError(DashboardException):
    """Raised when a requested resource is not found."""

    pass


class ConflictError(DashboardException):
    """Raised when a resource conflict occurs (e.g., duplicate SSN)."""

    pass


class DatabaseError(DashboardException):
    """Raised when database operations fail."""

    def __init__(self, message: str, original_error: SQLAlchemyError | None = None, **kwargs: Any):
        super().__init__(message, **kwargs)
        self.original_error = original_error


class FileProcessingError(DashboardException):
    """Raised when file processing operations fail."""

    pass


class ExternalServiceError(DashboardException):
    """Raised when external service calls fail."""

    pass


# HTTP Exception Mappers
def dashboard_exception_to_http(exc: DashboardException) -> HTTPException:
    """
    Convert DashboardException to FastAPI HTTPException.

    Args:
        exc: The DashboardException to convert

    Returns:
        HTTPException: Corresponding HTTP exception
    """
    if isinstance(exc, ValidationError):
        return HTTPException(
            status_code=400,
            detail={"message": exc.message, "error_code": exc.error_code, "details": exc.details},
        )

    elif isinstance(exc, AuthenticationError):
        return HTTPException(
            status_code=401, detail={"message": exc.message, "error_code": exc.error_code}
        )

    elif isinstance(exc, AuthorizationError):
        return HTTPException(
            status_code=403, detail={"message": exc.message, "error_code": exc.error_code}
        )

    elif isinstance(exc, NotFoundError):
        return HTTPException(
            status_code=404, detail={"message": exc.message, "error_code": exc.error_code}
        )

    elif isinstance(exc, ConflictError):
        return HTTPException(
            status_code=409,
            detail={"message": exc.message, "error_code": exc.error_code, "details": exc.details},
        )

    elif isinstance(exc, DatabaseError | FileProcessingError | ExternalServiceError):
        return HTTPException(
            status_code=500,
            detail={"message": "Internal server error", "error_code": exc.error_code},
        )

    else:
        return HTTPException(
            status_code=500,
            detail={"message": "An unexpected error occurred", "error_code": "INTERNAL_ERROR"},
        )
