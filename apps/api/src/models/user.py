"""
User model with authentication support.
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import EmailStr
from sqlmodel import SQLModel, Field


class UserRole(str, Enum):
    """User role enumeration following data model specifications."""
    SYSADMIN = "sysadmin"
    ADMIN = "admin" 
    USER = "user"


class User(SQLModel, table=True):
    """User model with authentication support and role-based access control."""
    __tablename__ = "users"
    
    # Primary key with UUID
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Authentication fields
    email: EmailStr = Field(unique=True, index=True)
    password_hash: str
    
    # Role-based access control
    role: UserRole = Field(default=UserRole.USER)
    
    # 2FA support - TOTP secret is optional
    totp_secret: Optional[str] = Field(default=None)
    
    # Status and audit fields
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Additional metadata for security
    last_login_at: Optional[datetime] = Field(default=None)
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None)
    
    def __repr__(self) -> str:
        return f"User(id={self.id}, email='{self.email}', role='{self.role}')"