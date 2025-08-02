"""
Authentication and JWT handling for IAM Dashboard.

This module provides JWT token creation, validation, and security utilities.
All authentication logic is centralized here for consistency.
"""

from datetime import datetime, timedelta
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel

from .config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer scheme for JWT tokens
security = HTTPBearer()


class TokenData(BaseModel):
    """Token payload data structure."""

    user_id: UUID
    role: str
    email: str


class AuthService:
    """Authentication service for JWT token management."""

    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a plain password."""
        return pwd_context.hash(password)

    def create_access_token(self, user_id: UUID, user_role: str, user_email: str) -> dict:
        """Create secure JWT token with user data."""
        payload = {
            "sub": str(user_id),
            "role": user_role,
            "email": user_email,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
        }

        access_token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
        }

    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = UUID(payload["sub"])
            role = payload["role"]
            email = payload["email"]
            return TokenData(user_id=user_id, role=role, email=email)
        except jwt.ExpiredSignatureError as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from err
        except (
            jwt.InvalidSignatureError,
            jwt.DecodeError,
            jwt.InvalidTokenError,
            KeyError,
            ValueError,
        ) as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from err


# Global auth service instance
auth_service = AuthService()


def get_current_user_token(credentials: HTTPAuthorizationCredentials) -> TokenData:
    """
    Dependency to get current user from JWT token.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        TokenData: Decoded token data

    Raises:
        HTTPException: If token is invalid
    """
    return auth_service.verify_token(credentials.credentials)


def require_role(required_role: str):
    """
    Dependency factory for role-based access control.

    Args:
        required_role: Required user role

    Returns:
        Dependency function that checks user role
    """

    def check_role(token_data: TokenData) -> TokenData:
        if token_data.role not in (required_role, "sysadmin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return token_data

    return check_role


def require_any_role(required_roles: list[str]):
    """
    Dependency factory for multi-role access control.

    Args:
        required_roles: List of acceptable user roles

    Returns:
        Dependency function that checks user role
    """

    def check_roles(token_data: TokenData) -> TokenData:
        if token_data.role not in required_roles and token_data.role != "sysadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return token_data

    return check_roles
