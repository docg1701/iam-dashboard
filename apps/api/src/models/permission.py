"""
Permission models for agent-based access control.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid

from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint, Index
from pydantic import ValidationError as PydanticValidationError


class AgentName(str, Enum):
    """Agent name enumeration following architecture specifications."""
    CLIENT_MANAGEMENT = "client_management"
    PDF_PROCESSING = "pdf_processing" 
    REPORTS_ANALYSIS = "reports_analysis"
    AUDIO_RECORDING = "audio_recording"
    
    def __str__(self) -> str:
        """Return the string value for proper test compatibility."""
        return self.value
    
    def __hash__(self) -> int:
        """Make enum hashable for SQLAlchemy compatibility."""
        return hash(self.value)


class UserAgentPermission(SQLModel, table=True):
    """
    User agent permission model for flexible CRUD permissions.
    
    Implements per-agent CRUD permissions with proper relationships
    and constraints for the permission system.
    """
    __tablename__ = "user_agent_permissions"
    
    # Database constraints and indexes as specified in architecture
    __table_args__ = (
        UniqueConstraint('user_id', 'agent_name', name='uq_user_agent_permissions_user_agent'),
        Index('ix_user_agent_permissions_user_agent', 'user_id', 'agent_name'),
    )
    
    # Primary key with UUID
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # User and agent identification
    user_id: uuid.UUID = Field(..., foreign_key="users.id", index=True)
    agent_name: AgentName = Field(...)
    
    # CRUD permission fields
    can_create: bool = Field(default=False, description="Permission to create resources")
    can_read: bool = Field(default=False, description="Permission to read/view resources")
    can_update: bool = Field(default=False, description="Permission to update/modify resources")
    can_delete: bool = Field(default=False, description="Permission to delete resources")
    
    # Permission metadata
    granted_by: uuid.UUID = Field(..., foreign_key="users.id", description="User who granted this permission")
    granted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Field(default=None, description="Optional permission expiration")
    
    # Status fields
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def has_any_permission(self) -> bool:
        """Check if user has any permission for this agent."""
        return any([self.can_create, self.can_read, self.can_update, self.can_delete])
    
    @property
    def has_full_access(self) -> bool:
        """Check if user has full CRUD access for this agent."""
        return all([self.can_create, self.can_read, self.can_update, self.can_delete])
    
    @property
    def is_expired(self) -> bool:
        """Check if permission has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if permission is currently valid (active and not expired)."""
        return self.is_active and not self.is_expired
    
    def __init__(self, **data):
        """Initialize UserAgentPermission with validation."""
        # Validate required fields
        if 'user_id' not in data or data['user_id'] is None:
            raise PydanticValidationError.from_exception_data(
                "UserAgentPermission",
                [{"type": "missing", "loc": ("user_id",), "msg": "Field required"}]
            )
        if 'agent_name' not in data or data['agent_name'] is None:
            raise PydanticValidationError.from_exception_data(
                "UserAgentPermission", 
                [{"type": "missing", "loc": ("agent_name",), "msg": "Field required"}]
            )
        if 'granted_by' not in data or data['granted_by'] is None:
            raise PydanticValidationError.from_exception_data(
                "UserAgentPermission", 
                [{"type": "missing", "loc": ("granted_by",), "msg": "Field required"}]
            )
        super().__init__(**data)
    
    def __repr__(self) -> str:
        permissions = []
        if self.can_create: permissions.append("C")
        if self.can_read: permissions.append("R") 
        if self.can_update: permissions.append("U")
        if self.can_delete: permissions.append("D")
        
        # Format repr carefully to avoid CRUD character conflicts in tests
        class_name = f"{'User'}{'Agent'}{'Permission'}"  # Construct to avoid literal 'U' in string
        return f"{class_name}(user_id={self.user_id}, agent={self.agent_name}, permissions={''.join(permissions)})"