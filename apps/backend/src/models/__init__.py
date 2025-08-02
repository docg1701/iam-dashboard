"""Database models for the IAM Dashboard application.

This module contains all SQLModel database models following the multi-agent
architecture where each agent has its own tables but can read from others.
"""

from .audit import AuditLog
from .base import BaseModel
from .client import Client, ClientCreate, ClientSearch, ClientUpdate
from .user import User, UserCreate, UserUpdate

__all__ = [
    "BaseModel",
    "User",
    "UserCreate",
    "UserUpdate",
    "Client",
    "ClientCreate",
    "ClientUpdate",
    "ClientSearch",
    "AuditLog",
]
