"""Repository for audit log data access."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditAction, AuditLevel, AuditLog


class AuditLogRepository:
    """Repository for audit log operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the audit log repository."""
        self.session = session

    async def create(self, audit_log: AuditLog) -> AuditLog:
        """Create a new audit log entry."""
        self.session.add(audit_log)
        await self.session.commit()
        await self.session.refresh(audit_log)
        return audit_log

    async def get_logs_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        action_filter: AuditAction | None = None,
        level_filter: AuditLevel | None = None,
        user_filter: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        search_query: str | None = None,
    ) -> tuple[list[AuditLog], int]:
        """Get paginated audit logs with filtering."""
        query = select(AuditLog)

        # Apply filters
        conditions = []

        if action_filter:
            conditions.append(AuditLog.action == action_filter)

        if level_filter:
            conditions.append(AuditLog.level == level_filter)

        if user_filter:
            conditions.append(AuditLog.username.ilike(f"%{user_filter}%"))

        if date_from:
            conditions.append(AuditLog.created_at >= date_from)

        if date_to:
            conditions.append(AuditLog.created_at <= date_to)

        if search_query:
            conditions.append(
                AuditLog.message.ilike(f"%{search_query}%")
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_count = await self.session.scalar(count_query)

        # Apply pagination and ordering
        query = query.order_by(desc(AuditLog.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(query)
        logs = result.scalars().all()

        return list(logs), total_count or 0

    async def get_logs_for_export(
        self,
        action_filter: AuditAction | None = None,
        level_filter: AuditLevel | None = None,
        user_filter: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        search_query: str | None = None,
        limit: int = 10000,
    ) -> list[AuditLog]:
        """Get audit logs for export (without pagination)."""
        query = select(AuditLog)

        # Apply filters
        conditions = []

        if action_filter:
            conditions.append(AuditLog.action == action_filter)

        if level_filter:
            conditions.append(AuditLog.level == level_filter)

        if user_filter:
            conditions.append(AuditLog.username.ilike(f"%{user_filter}%"))

        if date_from:
            conditions.append(AuditLog.created_at >= date_from)

        if date_to:
            conditions.append(AuditLog.created_at <= date_to)

        if search_query:
            conditions.append(
                AuditLog.message.ilike(f"%{search_query}%")
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Order by timestamp and limit
        query = query.order_by(desc(AuditLog.created_at)).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_logs_by_user(
        self, user_id: UUID, limit: int = 100
    ) -> list[AuditLog]:
        """Get recent audit logs for a specific user."""
        query = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_logs_by_action(
        self, action: AuditAction, limit: int = 100
    ) -> list[AuditLog]:
        """Get recent audit logs for a specific action."""
        query = (
            select(AuditLog)
            .where(AuditLog.action == action)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_recent_critical_logs(self, limit: int = 50) -> list[AuditLog]:
        """Get recent critical and error level logs."""
        query = (
            select(AuditLog)
            .where(AuditLog.level.in_([AuditLevel.CRITICAL, AuditLevel.ERROR]))
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_logs_by_level(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict[str, int]:
        """Count logs by level within date range."""
        query = select(AuditLog.level, func.count(AuditLog.id))

        conditions = []
        if date_from:
            conditions.append(AuditLog.created_at >= date_from)
        if date_to:
            conditions.append(AuditLog.created_at <= date_to)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.group_by(AuditLog.level)

        result = await self.session.execute(query)
        counts = {level.value: count for level, count in result.all()}

        # Ensure all levels are represented
        for level in AuditLevel:
            if level.value not in counts:
                counts[level.value] = 0

        return counts

    async def count_logs_by_action(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 10,
    ) -> dict[str, int]:
        """Count logs by action within date range."""
        query = select(AuditLog.action, func.count(AuditLog.id))

        conditions = []
        if date_from:
            conditions.append(AuditLog.created_at >= date_from)
        if date_to:
            conditions.append(AuditLog.created_at <= date_to)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.group_by(AuditLog.action).order_by(
            desc(func.count(AuditLog.id))
        ).limit(limit)

        result = await self.session.execute(query)
        return {action.value: count for action, count in result.all()}

    async def cleanup_old_logs(self, older_than: datetime) -> int:
        """Remove audit logs older than specified date."""
        query = select(AuditLog).where(AuditLog.created_at < older_than)
        result = await self.session.execute(query)
        logs_to_delete = result.scalars().all()

        count = len(logs_to_delete)

        for log in logs_to_delete:
            await self.session.delete(log)

        await self.session.commit()
        return count

