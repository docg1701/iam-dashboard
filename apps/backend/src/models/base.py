"""Base model for all database entities."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class BaseModel(SQLModel):
    """Base model with common fields for all database entities."""

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique identifier for the record",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the record was created",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Timestamp when the record was last updated",
    )

    class Config:
        """SQLModel configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None,
        }
