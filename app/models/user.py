"""User model for authentication and authorization."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Enum, String
from sqlalchemy.orm import Mapped, relationship

from .base import TimestampedModel

if TYPE_CHECKING:
    from .agent import AgentExecution


class UserRole(enum.Enum):
    """User role enumeration."""

    SYSADMIN = "sysadmin"
    ADMIN_USER = "admin_user"
    COMMON_USER = "common_user"


class User(TimestampedModel):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    username = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role: Column[UserRole] = Column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]), nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)

    # 2FA fields
    totp_secret = Column(String(32), nullable=True)
    is_2fa_enabled = Column(Boolean, default=False, nullable=False)

    # Relationships
    agent_executions: Mapped[list["AgentExecution"]] = relationship("AgentExecution", back_populates="user")
    questionnaire_drafts = relationship("QuestionnaireDraft", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return bool(self.role in (UserRole.SYSADMIN, UserRole.ADMIN_USER))

    @property
    def is_sysadmin(self) -> bool:
        """Check if user is a system administrator."""
        return bool(self.role == UserRole.SYSADMIN)
