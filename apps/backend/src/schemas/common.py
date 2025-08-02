"""
Common Pydantic schemas used across the application.

This module contains base schemas and common response models
that are reused throughout the API.
"""

from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel):
    """Standard success response model."""
    success: bool = True
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Standard error response model."""
    success: bool = False
    message: str
    error_code: str | None = None
    details: dict[str, Any] | None = None


class PaginationInfo(BaseModel):
    """Pagination information model."""
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse[T](BaseModel):
    """Generic paginated response model."""
    success: bool = True
    data: list[T]
    pagination: PaginationInfo


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    version: str
    environment: str
    timestamp: str
    components: dict[str, str]
