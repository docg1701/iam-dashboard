"""User repository for database operations."""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User, UserRole


class UserRepository:
    """Repository for User model database operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        self.session = session

    async def create(
        self,
        username: str,
        hashed_password: str,
        role: UserRole,
        totp_secret: str | None = None,
    ) -> User:
        """Create a new user in the database."""
        user = User(
            username=username,
            hashed_password=hashed_password,
            role=role,
            totp_secret=totp_secret,
            is_2fa_enabled=bool(totp_secret),
        )

        self.session.add(user)
        try:
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except IntegrityError as e:
            await self.session.rollback()
            raise ValueError(f"Username '{username}' already exists") from e

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get a user by ID."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Get a user by username."""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def update(self, user: User) -> User:
        """Update an existing user."""
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Delete a user from the database."""
        await self.session.delete(user)
        await self.session.commit()

    async def get_all(self) -> list[User]:
        """Get all users."""
        result = await self.session.execute(select(User))
        return list(result.scalars().all())

    async def is_username_taken(self, username: str) -> bool:
        """Check if a username is already taken."""
        user = await self.get_by_username(username)
        return user is not None
