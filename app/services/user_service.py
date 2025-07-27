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

        totp = pyotp.TOTP(user.totp_secret)
        return totp.verify(totp_code, valid_window=1)  # Allow 1 window tolerance

    def get_totp_provisioning_uri(self, user: User) -> str | None:
        """Get the TOTP provisioning URI for QR code generation."""
        if not user.totp_secret:
            return None

        totp = pyotp.TOTP(user.totp_secret)
        return totp.provisioning_uri(name=user.username, issuer_name="IAM Dashboard")

    async def enable_2fa(self, user: User) -> str:
        """Enable 2FA for a user and return the secret."""
        if not user.totp_secret:
            user.totp_secret = self._generate_totp_secret()

        user.is_2fa_enabled = True
        await self.user_repository.update(user)

        return user.totp_secret

    async def disable_2fa(self, user: User) -> None:
        """Disable 2FA for a user."""
        user.is_2fa_enabled = False
        user.totp_secret = None
        await self.user_repository.update(user)

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get a user by ID."""
        return await self.user_repository.get_by_id(user_id)

    async def get_user_by_username(self, username: str) -> User | None:
        """Get a user by username."""
        return await self.user_repository.get_by_username(username)

    def _generate_totp_secret(self) -> str:
        """Generate a random TOTP secret."""
        return pyotp.random_base32()
