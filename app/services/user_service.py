"""User service for business logic operations."""

import uuid

import pyotp
from passlib.context import CryptContext

from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository


class UserService:
    """Service class for user-related business logic."""

    def __init__(self, user_repository: UserRepository) -> None:
        """Initialize the service with a user repository."""
        self.user_repository = user_repository
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def create_user(
        self,
        username: str,
        password: str,
        role: UserRole = UserRole.COMMON_USER,
        enable_2fa: bool = True,
    ) -> User:
        """Create a new user with hashed password and optional 2FA setup."""
        # Validate username
        if await self.user_repository.is_username_taken(username):
            raise ValueError(f"Username '{username}' is already taken")

        # Hash password
        hashed_password = self.pwd_context.hash(password)

        # Generate TOTP secret if 2FA is enabled
        totp_secret = self._generate_totp_secret() if enable_2fa else None

        # Create user
        user = await self.user_repository.create(
            username=username,
            hashed_password=hashed_password,
            role=role,
            totp_secret=totp_secret,
        )

        return user

    async def authenticate_user(self, username: str, password: str) -> User | None:
        """Authenticate a user with username and password."""
        user = await self.user_repository.get_by_username(username)

        if not user or not user.is_active:
            return None

        if not self.pwd_context.verify(password, user.hashed_password):
            return None

        return user

    async def verify_totp_code(self, user: User, totp_code: str) -> bool:
        """Verify a TOTP code for 2FA authentication."""
        if not user.is_2fa_enabled or not user.totp_secret:
            return True  # 2FA not enabled

        totp = pyotp.TOTP(str(user.totp_secret))
        return totp.verify(totp_code, valid_window=1)  # Allow 1 window tolerance

    def get_totp_provisioning_uri(self, user: User) -> str | None:
        """Get the TOTP provisioning URI for QR code generation."""
        if not user.totp_secret:
            return None

        totp = pyotp.TOTP(str(user.totp_secret))
        return totp.provisioning_uri(
            name=str(user.username), issuer_name="IAM Dashboard"
        )

    async def enable_2fa(self, user: User) -> str:
        """Enable 2FA for a user and return the secret."""
        if not user.totp_secret:
            user.totp_secret = self._generate_totp_secret()  # type: ignore[assignment]

        user.is_2fa_enabled = True  # type: ignore[assignment]
        await self.user_repository.update(user)

        return str(user.totp_secret)

    async def disable_2fa(self, user: User) -> None:
        """Disable 2FA for a user."""
        user.is_2fa_enabled = False  # type: ignore[assignment]
        user.totp_secret = None  # type: ignore[assignment]
        await self.user_repository.update(user)

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get a user by ID."""
        return await self.user_repository.get_by_id(user_id)

    async def get_user_by_username(self, username: str) -> User | None:
        """Get a user by username."""
        return await self.user_repository.get_by_username(username)

    async def get_all_users(self) -> list[User]:
        """Get all users in the system."""
        return await self.user_repository.get_all()

    async def update_user(
        self,
        user_id: uuid.UUID,
        username: str | None = None,
        role: UserRole | None = None,
        is_active: bool | None = None,
        new_password: str | None = None,
    ) -> User | None:
        """Update an existing user."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None

        # Update fields if provided
        if username is not None:
            # Check if username is taken by another user
            existing_user = await self.user_repository.get_by_username(username)
            if existing_user and existing_user.id != user.id:
                raise ValueError(f"Username '{username}' is already taken")
            user.username = username  # type: ignore[assignment]

        if role is not None:
            user.role = role  # type: ignore[assignment]

        if is_active is not None:
            user.is_active = is_active  # type: ignore[assignment]

        if new_password is not None:
            user.hashed_password = self.pwd_context.hash(new_password)  # type: ignore[assignment]

        return await self.user_repository.update(user)

    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """Delete a user by ID. Returns True if user was deleted, False if not found."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return False

        await self.user_repository.delete(user)
        return True

    async def reset_2fa(self, user_id: uuid.UUID) -> bool:
        """Reset 2FA for a user by ID. Returns True if successful, False if user not found."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return False

        user.is_2fa_enabled = False  # type: ignore[assignment]
        user.totp_secret = None  # type: ignore[assignment]
        await self.user_repository.update(user)
        return True

    def _generate_totp_secret(self) -> str:
        """Generate a random TOTP secret."""
        return pyotp.random_base32()
