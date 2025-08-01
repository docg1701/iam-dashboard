"""Agent execution tracking models."""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from .client import Client
    from .document import Document
    from .user import User


class AgentExecutionStatus(Enum):
    """Agent execution status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class AgentExecution(Base):
    """Agent execution tracking model."""

    __tablename__ = "agent_executions"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clients.id"), nullable=True
    )
    status: Mapped[AgentExecutionStatus] = mapped_column(
        String(50), nullable=False, default=AgentExecutionStatus.PENDING, index=True
    )
    input_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    output_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_duration: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="agent_executions")
    client: Mapped["Client | None"] = relationship("Client", back_populates="agent_executions")
    processed_documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="agent_execution"
    )

    def __repr__(self) -> str:
        """String representation of AgentExecution."""
        return f"<AgentExecution(execution_id={self.execution_id}, agent_id={self.agent_id}, status={self.status})>"
