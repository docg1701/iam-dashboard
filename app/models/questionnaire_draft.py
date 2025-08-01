"""Questionnaire draft model for storing generated legal questionnaires."""

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import TimestampedModel

if TYPE_CHECKING:
    pass


class QuestionnaireDraft(TimestampedModel):
    """Model for storing generated legal questionnaire drafts."""

    __tablename__ = "questionnaire_drafts"

    # Foreign key to client with CASCADE delete
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)

    # Foreign key to user (required by story) with CASCADE delete
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Template type and status (required by story)
    template_type = Column(String(100), nullable=False, default="standard", server_default="'standard'")
    status = Column(String(50), nullable=False, default="draft", server_default="'draft'")

    # Questionnaire content
    content = Column(Text, nullable=False)

    # Case-related fields (copied from form data)
    profession = Column(String(100), nullable=False)
    disease = Column(String(200), nullable=False)
    incident_date = Column(String(10), nullable=False)  # Format: dd/mm/yyyy
    medical_date = Column(String(10), nullable=False)  # Format: dd/mm/yyyy

    # Metadata about generation process
    metadata_ = Column(
        JSONB, name="metadata"
    )  # Avoid conflict with SQLAlchemy metadata

    # Relationships
    client = relationship("Client", back_populates="questionnaire_drafts")
    user = relationship("User", back_populates="questionnaire_drafts")

    def __repr__(self) -> str:
        """String representation of QuestionnaireDraft."""
        return f"<QuestionnaireDraft(id={self.id}, client_id={self.client_id}, profession='{self.profession}')>"

    @property
    def content_preview(self) -> str:
        """Get preview of questionnaire content (first 100 characters)."""
        if not self.content:
            return ""
        return self.content[:100] + "..." if len(self.content) > 100 else self.content

    @property
    def word_count(self) -> int:
        """Get approximate word count of questionnaire content."""
        if not self.content:
            return 0
        return len(self.content.split())

    @property
    def character_count(self) -> int:
        """Get character count of questionnaire content."""
        return len(self.content) if self.content else 0


# Define indexes for performance
Index('idx_questionnaire_drafts_client_id', QuestionnaireDraft.client_id)
Index('idx_questionnaire_drafts_user_id', QuestionnaireDraft.user_id)
Index('idx_questionnaire_drafts_status', QuestionnaireDraft.status)
Index('idx_questionnaire_drafts_template_type', QuestionnaireDraft.template_type)
