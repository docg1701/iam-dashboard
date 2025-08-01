"""Audit log model for tracking administrative actions."""

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID

from .base import TimestampedModel


class AuditAction(enum.Enum):
    """Audit action enumeration."""

    # User management actions
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_2FA_RESET = "user_2fa_reset"
    USER_ROLE_CHANGED = "user_role_changed"

    # Agent management actions
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_RESTARTED = "agent_restarted"
    AGENT_CONFIG_UPDATED = "agent_config_updated"
    AGENT_CONFIG_ROLLBACK = "agent_config_rollback"

    # System actions
    SYSTEM_HEALTH_CHECK = "system_health_check"
    SYSTEM_METRICS_ACCESSED = "system_metrics_accessed"
    SYSTEM_RESTART_ALL_AGENTS = "system_restart_all_agents"

    # Authentication actions
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    SESSION_EXPIRED = "session_expired"

    # Data export actions
    AUDIT_LOGS_EXPORTED = "audit_logs_exported"
    USERS_LIST_ACCESSED = "users_list_accessed"

    # Document actions
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_PROCESSED = "document_processed"
    DOCUMENT_DELETED = "document_deleted"


class AuditLevel(enum.Enum):
    """Audit level enumeration."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog(TimestampedModel):
    """Audit log model for tracking administrative and user actions."""

    __tablename__ = "audit_logs"

    # Action details
    action = Column(
        Enum(AuditAction, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    level = Column(
        Enum(AuditLevel, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AuditLevel.INFO,
        index=True
    )

    # User information
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    username = Column(String(255), nullable=True, index=True)

    # Action context
    resource_type = Column(String(100), nullable=True, index=True)  # e.g., "user", "agent", "document"
    resource_id = Column(String(255), nullable=True, index=True)

    # Details
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)  # Additional structured data

    # Request context
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)

    # Timestamp override for specific actions
    action_timestamp = Column(DateTime, nullable=True, index=True)

    def __repr__(self) -> str:
        """String representation of AuditLog."""
        return (
            f"<AuditLog(id={self.id}, action='{self.action.value}', "
            f"user='{self.username}', timestamp='{self.created_at}')>"
        )

    @property
    def action_display(self) -> str:
        """Human-readable action name."""
        action_names = {
            AuditAction.USER_CREATED: "User Created",
            AuditAction.USER_UPDATED: "User Updated",
            AuditAction.USER_DELETED: "User Deleted",
            AuditAction.USER_2FA_RESET: "User 2FA Reset",
            AuditAction.USER_ROLE_CHANGED: "User Role Changed",
            AuditAction.AGENT_STARTED: "Agent Started",
            AuditAction.AGENT_STOPPED: "Agent Stopped",
            AuditAction.AGENT_RESTARTED: "Agent Restarted",
            AuditAction.AGENT_CONFIG_UPDATED: "Agent Config Updated",
            AuditAction.AGENT_CONFIG_ROLLBACK: "Agent Config Rollback",
            AuditAction.SYSTEM_HEALTH_CHECK: "System Health Check",
            AuditAction.SYSTEM_METRICS_ACCESSED: "System Metrics Accessed",
            AuditAction.SYSTEM_RESTART_ALL_AGENTS: "System Restart All Agents",
            AuditAction.LOGIN_SUCCESS: "Login Success",
            AuditAction.LOGIN_FAILED: "Login Failed",
            AuditAction.LOGOUT: "Logout",
            AuditAction.SESSION_EXPIRED: "Session Expired",
            AuditAction.AUDIT_LOGS_EXPORTED: "Audit Logs Exported",
            AuditAction.USERS_LIST_ACCESSED: "Users List Accessed",
            AuditAction.DOCUMENT_UPLOADED: "Document Uploaded",
            AuditAction.DOCUMENT_PROCESSED: "Document Processed",
            AuditAction.DOCUMENT_DELETED: "Document Deleted",
        }
        return action_names.get(self.action, self.action.value.replace("_", " ").title())

    @property
    def level_display(self) -> str:
        """Human-readable level name."""
        return self.level.value.title()

    @property
    def level_color(self) -> str:
        """Color for the level display."""
        colors = {
            AuditLevel.INFO: "blue",
            AuditLevel.WARNING: "orange",
            AuditLevel.ERROR: "red",
            AuditLevel.CRITICAL: "red"
        }
        return colors.get(self.level, "grey")

    @classmethod
    async def log_action(
        cls,
        session: Any,  # AsyncSession
        action: AuditAction,
        message: str,
        user_id: str | None = None,
        username: str | None = None,
        level: AuditLevel = AuditLevel.INFO,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        action_timestamp: datetime | None = None,
    ) -> "AuditLog":
        """Create and save an audit log entry."""
        log_entry = cls(
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
            action_timestamp=action_timestamp or datetime.utcnow(),
        )

        session.add(log_entry)
        await session.commit()
        await session.refresh(log_entry)

        return log_entry

