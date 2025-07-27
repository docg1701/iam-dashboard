"""Client model for storing law office client information."""

from typing import TYPE_CHECKING

from sqlalchemy import Column, Date, String
from sqlalchemy.orm import relationship

from .base import TimestampedModel

if TYPE_CHECKING:
    pass


class Client(TimestampedModel):
    """Client model for storing law office client information."""

    __tablename__ = "clients"

    name = Column(String(255), nullable=False)
    cpf = Column(String(11), unique=True, nullable=False)
    birth_date = Column(Date, nullable=False)

    # Relationships
    documents = relationship(
        "Document", back_populates="client", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of Client."""
        return f"<Client(id={self.id}, name='{self.name}', cpf='{self.cpf}')>"

    @property
    def formatted_cpf(self) -> str:
        """Format CPF for display (XXX.XXX.XXX-XX)."""
        if len(self.cpf) != 11:
            return self.cpf
        return f"{self.cpf[:3]}.{self.cpf[3:6]}.{self.cpf[6:9]}-{self.cpf[9:]}"
