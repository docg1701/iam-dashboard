"""Service for audit log operations."""

import csv
import io
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from app.models.audit_log import AuditAction, AuditLevel, AuditLog
from app.repositories.audit_log_repository import AuditLogRepository


class AuditLogService:
    """Service for managing audit logs."""

    def __init__(self, audit_log_repository: AuditLogRepository) -> None:
        """Initialize the audit log service."""
        self.audit_log_repository = audit_log_repository

    async def log_action(
        self,
        action: AuditAction,
        message: str,
        user_id: UUID | None = None,
        username: str | None = None,
        level: AuditLevel = AuditLevel.INFO,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log an audit action."""
        log_entry = AuditLog(
            action=action,
            level=level,
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            message=message,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            action_timestamp=datetime.utcnow(),
        )

        return await self.audit_log_repository.create(log_entry)

    async def get_logs_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        action_filter: str | None = None,
        level_filter: str | None = None,
        user_filter: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        search_query: str | None = None,
    ) -> tuple[list[AuditLog], int, int]:
        """Get paginated audit logs with filtering."""
        # Convert string filters to enums
        action_enum = None
        if action_filter:
            try:
                action_enum = AuditAction(action_filter)
            except ValueError:
                pass

        level_enum = None
        if level_filter:
            try:
                level_enum = AuditLevel(level_filter)
            except ValueError:
                pass

        logs, total_count = await self.audit_log_repository.get_logs_paginated(
            page=page,
            page_size=page_size,
            action_filter=action_enum,
            level_filter=level_enum,
            user_filter=user_filter,
            date_from=date_from,
            date_to=date_to,
            search_query=search_query,
        )

        total_pages = (total_count + page_size - 1) // page_size

        return logs, total_count, total_pages

    async def export_logs_csv(
        self,
        action_filter: str | None = None,
        level_filter: str | None = None,
        user_filter: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        search_query: str | None = None,
        limit: int = 10000,
    ) -> str:
        """Export audit logs to CSV format."""
        # Convert string filters to enums
        action_enum = None
        if action_filter:
            try:
                action_enum = AuditAction(action_filter)
            except ValueError:
                pass

        level_enum = None
        if level_filter:
            try:
                level_enum = AuditLevel(level_filter)
            except ValueError:
                pass

        logs = await self.audit_log_repository.get_logs_for_export(
            action_filter=action_enum,
            level_filter=level_enum,
            user_filter=user_filter,
            date_from=date_from,
            date_to=date_to,
            search_query=search_query,
            limit=limit,
        )

        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Timestamp",
            "Action",
            "Level",
            "User",
            "Resource Type",
            "Resource ID",
            "Message",
            "IP Address",
            "User Agent",
            "Details"
        ])

        # Write data rows
        for log in logs:
            writer.writerow([
                log.created_at.isoformat(),
                log.action_display,
                log.level_display,
                log.username or "System",
                log.resource_type or "",
                log.resource_id or "",
                log.message,
                log.ip_address or "",
                log.user_agent or "",
                str(log.details) if log.details else ""
            ])

        return output.getvalue()

    async def get_logs_by_user(
        self, user_id: UUID, limit: int = 100
    ) -> list[AuditLog]:
        """Get recent audit logs for a specific user."""
        return await self.audit_log_repository.get_logs_by_user(user_id, limit)

    async def get_logs_by_action(
        self, action: AuditAction, limit: int = 100
    ) -> list[AuditLog]:
        """Get recent audit logs for a specific action."""
        return await self.audit_log_repository.get_logs_by_action(action, limit)

    async def get_recent_critical_logs(self, limit: int = 50) -> list[AuditLog]:
        """Get recent critical and error level logs."""
        return await self.audit_log_repository.get_recent_critical_logs(limit)

    async def get_audit_statistics(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict[str, Any]:
        """Get audit log statistics."""
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=30)
        if not date_to:
            date_to = datetime.utcnow()

        level_counts = await self.audit_log_repository.count_logs_by_level(
            date_from, date_to
        )
        action_counts = await self.audit_log_repository.count_logs_by_action(
            date_from, date_to
        )

        total_logs = sum(level_counts.values())

        return {
            "total_logs": total_logs,
            "date_range": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
            "level_counts": level_counts,
            "action_counts": action_counts,
            "critical_logs": level_counts.get("critical", 0),
            "error_logs": level_counts.get("error", 0),
            "warning_logs": level_counts.get("warning", 0),
            "info_logs": level_counts.get("info", 0),
        }

    async def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """Remove audit logs older than specified number of days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        return await self.audit_log_repository.cleanup_old_logs(cutoff_date)

    def get_available_actions(self) -> list[dict[str, str]]:
        """Get all available audit actions."""
        return [
            {"value": action.value, "label": action.value.replace("_", " ").title()}
            for action in AuditAction
        ]

    def get_available_levels(self) -> list[dict[str, str]]:
        """Get all available audit levels."""
        return [
            {"value": level.value, "label": level.value.title()}
            for level in AuditLevel
        ]

