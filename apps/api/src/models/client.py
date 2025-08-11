"""
Client model with CPF validation.
"""
from datetime import datetime, date
from typing import Optional
import uuid

from pydantic import field_validator
from sqlmodel import SQLModel, Field, Relationship


class Client(SQLModel, table=True):
    """
    Client model with CPF validation and audit fields.
    
    Includes comprehensive validation following Project Brief specifications
    with proper relationship to User model for audit tracking.
    """
    __tablename__ = "clients"
    
    # Primary key with UUID
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Client identification fields
    name: str = Field(min_length=2, max_length=100, index=True)
    cpf: str = Field(unique=True, index=True, description="CPF must be 11 digits without formatting")
    birth_date: date = Field(description="Client birth date")
    
    # Audit and relationship fields
    created_by: uuid.UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    # Relationships (will be implemented after User model is stable)
    
    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        """
        Validate CPF format and digits.
        
        CPF must be exactly 11 digits (no formatting characters).
        Full validation using cnpj-cpf-validator will be added in Task 6.
        """
        if not v:
            raise ValueError("CPF is required")
        
        # Remove any formatting characters
        cpf_digits = "".join(filter(str.isdigit, v))
        
        if len(cpf_digits) != 11:
            raise ValueError("CPF must contain exactly 11 digits")
        
        # Check for invalid sequences (all same digits)
        if cpf_digits == cpf_digits[0] * 11:
            raise ValueError("CPF cannot be all the same digits")
        
        return cpf_digits
    
    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, v: date) -> date:
        """
        Validate birth date is reasonable.
        
        Must be at least 16 years ago and not in the future.
        """
        if not v:
            raise ValueError("Birth date is required")
        
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        
        if v > today:
            raise ValueError("Birth date cannot be in the future")
        
        if age < 16:
            raise ValueError("Client must be at least 16 years old")
        
        if age > 120:
            raise ValueError("Birth date is unreasonably old")
        
        return v
    
    def __repr__(self) -> str:
        return f"Client(id={self.id}, name='{self.name}', cpf='{self.cpf[:3]}.***.{self.cpf[-2:]}')"