"""
Custom exception classes for the IAM Dashboard application.

All exceptions should inherit from the base DashboardException class
and provide meaningful error messages for debugging and user feedback.
"""

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError


class DashboardException(Exception):
    """Base exception class for IAM Dashboard application."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, object] | None = None,
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
    """Raised when a resource conflict occurs (e.g., duplicate CPF)."""

    pass


class DatabaseError(DashboardException):
    """Raised when database operations fail."""

    def __init__(
        self, message: str, original_error: SQLAlchemyError | None = None, **kwargs: object
    ) -> None:
        super().__init__(message)
        # Store any additional kwargs as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
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
    # Mapping of exception types to their HTTP status codes and details
    exception_mappings = {
        ValidationError: (400, True),  # (status_code, include_details)
        AuthenticationError: (401, False),
        AuthorizationError: (403, False),
        NotFoundError: (404, False),
        ConflictError: (409, True),
    }

    # Check if it's a specific exception type
    for exc_type, (status_code, include_details) in exception_mappings.items():
        if isinstance(exc, exc_type):
            detail: dict[str, object] = {"message": exc.message, "error_code": exc.error_code}
            if include_details:
                detail["details"] = exc.details
            return HTTPException(status_code=status_code, detail=detail)

    # Handle server error exceptions
    if isinstance(exc, DatabaseError | FileProcessingError | ExternalServiceError):
        return HTTPException(
            status_code=500,
            detail={"message": "Internal server error", "error_code": exc.error_code},
        )

    # Default fallback
    return HTTPException(
        status_code=500,
        detail={"message": "An unexpected error occurred", "error_code": "INTERNAL_ERROR"},
    )
