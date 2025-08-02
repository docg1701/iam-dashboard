"""Audit logging utility functions."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlmodel import Session

from src.models.audit import AuditAction, AuditLog, AuditLogCreate


def extract_request_info(request: Request) -> tuple[str, str]:
    """Extract IP address and user agent from request."""
    # Get real IP address, considering proxy headers
    ip_address = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP", "").strip()
        or request.client.host
        if request.client
        else "unknown"
    )

    user_agent = request.headers.get("User-Agent", "unknown")[:500]

    return ip_address, user_agent


async def create_audit_log(
    session: Session,
    table_name: str,
    record_id: str,
    action: AuditAction,
    user_id: UUID,
    request: Request,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
) -> AuditLog:
    """Create an audit log entry for a database action.

    Args:
        session: Database session
        table_name: Name of the table being modified
        record_id: ID of the record being modified
        action: Type of action (CREATE, UPDATE, DELETE, VIEW)
        user_id: ID of the user performing the action
        request: FastAPI request object for extracting IP and user agent
        old_values: Previous values (for UPDATE/DELETE actions)
        new_values: New values (for CREATE/UPDATE actions)

    Returns:
        Created AuditLog instance
    """
    ip_address, user_agent = extract_request_info(request)

    audit_data = AuditLogCreate(
        table_name=table_name,
        record_id=record_id,
        action=action,
        old_values=old_values,
        new_values=new_values,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    audit_log = AuditLog(**audit_data.dict())
    session.add(audit_log)
    session.commit()
    session.refresh(audit_log)

    return audit_log


def log_database_action(
    session: Session,
    action: AuditAction,
    table_name: str,
    record_id: str,
    user_id: UUID,
    request: Request,
    old_data: dict[str, Any] | None = None,
    new_data: dict[str, Any] | None = None,
) -> None:
    """Convenience function to log database actions.

    This function automatically handles the audit logging for CRUD operations.
    Use this in your service layer after performing database operations.

    Args:
        session: Database session
        action: Action type (CREATE, UPDATE, DELETE, VIEW)
        table_name: Table that was modified
        record_id: ID of the record
        user_id: User who performed the action
        request: FastAPI request for IP/user agent extraction
        old_data: Previous data state (for UPDATE/DELETE)
        new_data: New data state (for CREATE/UPDATE)
    """
    try:
        create_audit_log(
            session=session,
            table_name=table_name,
            record_id=record_id,
            action=action,
            user_id=user_id,
            request=request,
            old_values=old_data,
            new_values=new_data,
        )
    except Exception as e:
        # Log the error but don't fail the main operation
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create audit log for {action} on {table_name}:{record_id}: {e}")


def prepare_audit_data(model_instance: Any) -> dict[str, Any]:
    """Prepare model data for audit logging.

    Converts a SQLModel instance to a dictionary suitable for audit logging,
    excluding sensitive fields and handling special types.

    Args:
        model_instance: SQLModel instance to convert

    Returns:
        Dictionary of model data safe for audit logging
    """
    if not model_instance:
        return {}

    # Get model data as dict
    data = model_instance.dict() if hasattr(model_instance, "dict") else {}

    # Remove sensitive fields that shouldn't be logged
    sensitive_fields = {"password", "password_hash", "totp_secret", "access_token", "refresh_token"}

    for field in sensitive_fields:
        if field in data:
            data[field] = "[REDACTED]"

    # Convert datetime objects to ISO strings for JSON serialization
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = value.isoformat()
        elif isinstance(value, UUID):
            data[key] = str(value)

    return data
