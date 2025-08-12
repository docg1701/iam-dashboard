"""
Audit log model for compliance tracking.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
import uuid

from sqlmodel import SQLModel, Field, Column, JSON
from pydantic import field_validator, ValidationError as PydanticValidationError


class AuditAction(str, Enum):
    """Audit action enumeration following architecture specifications."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    PERMISSION_CHANGE = "permission_change"
    
    def __str__(self) -> str:
        """Return the string value for proper test compatibility."""
        return self.value
    
    def __hash__(self) -> int:
        """Make enum hashable for SQLAlchemy compatibility."""
        return hash(self.value)


class AuditLog(SQLModel, table=True):
    """
    Audit log model for comprehensive compliance tracking.
    
    Tracks all state-changing operations with user, timestamp, and change details
    for complete audit trail and compliance requirements.
    """
    __tablename__ = "audit_logs"
    
    # Primary key with UUID
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Actor and action tracking
    actor_id: Optional[uuid.UUID] = Field(
        default=None, 
        foreign_key="users.id", 
        index=True,
        description="User who performed the action (null for system actions)"
    )
    action: AuditAction = Field(..., description="Action performed in the audit event")
    
    # Resource tracking for polymorphic references
    resource_type: str = Field(
        ..., 
        max_length=50, 
        index=True,
        description="Type of resource affected (e.g., 'user', 'client', 'permission')"
    )
    resource_id: Optional[uuid.UUID] = Field(
        default=None,
        index=True, 
        description="ID of the affected resource"
    )
    
    # Change tracking with JSON fields
    old_values: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Previous values before the change"
    )
    new_values: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="New values after the change"
    )
    
    # Security and session tracking
    ip_address: Optional[str] = Field(
        default=None,
        max_length=45,  # IPv6 max length
        index=True,
        description="IP address of the client"
    )
    user_agent: Optional[str] = Field(
        default=None,
        max_length=500,
        description="User agent string from the request"
    )
    session_id: Optional[str] = Field(
        default=None,
        max_length=128,
        index=True,
        description="Session identifier for tracking user sessions"
    )
    
    # Metadata and timing
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Human-readable description of the action"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        index=True,
        description="Timestamp when the action occurred"
    )
    
    # Additional context
    additional_data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional contextual data for the audit event"
    )
    
    def __init__(self, **data):
        """Initialize AuditLog with validation."""
        # Validate required fields
        if 'action' not in data or data['action'] is None:
            raise PydanticValidationError.from_exception_data(
                "AuditLog",
                [{"type": "missing", "loc": ("action",), "msg": "Field required"}]
            )
        if 'resource_type' not in data or data['resource_type'] is None:
            raise PydanticValidationError.from_exception_data(
                "AuditLog", 
                [{"type": "missing", "loc": ("resource_type",), "msg": "Field required"}]
            )
        super().__init__(**data)
    
    @classmethod
    def create_audit_entry(
        cls,
        action: AuditAction,
        resource_type: str,
        actor_id: Optional[uuid.UUID] = None,
        resource_id: Optional[uuid.UUID] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        description: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> "AuditLog":
        """
        Factory method to create audit log entries with consistent formatting.
        
        Args:
            action: The action being audited
            resource_type: Type of resource being affected
            actor_id: ID of user performing the action
            resource_id: ID of resource being affected
            old_values: Previous values (for update operations)
            new_values: New values (for create/update operations)
            ip_address: Client IP address
            user_agent: Client user agent string
            session_id: Session identifier
            description: Human-readable description
            additional_data: Any additional contextual data
            
        Returns:
            AuditLog instance ready to be saved
        """
        return cls(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            description=description,
            additional_data=additional_data,
        )
    
    def __repr__(self) -> str:
        return f"AuditLog(id={self.id}, action={self.action}, resource={self.resource_type}:{self.resource_id}, actor={self.actor_id})"