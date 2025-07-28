#!/usr/bin/env python3
"""Script to disable 2FA for a user."""

import asyncio

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.core.database import get_async_db
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


async def disable_2fa_for_user(username: str):
    """Disable 2FA for a specific user."""
    async for db_session in get_async_db():
        user_repository = UserRepository(db_session)
        user_service = UserService(user_repository)

        # Get user by username
        user = await user_repository.get_by_username(username)

        if not user:
            print(f"User '{username}' not found")
            return False

        if not user.is_2fa_enabled:
            print(f"User '{username}' already has 2FA disabled")
            return True

        # Disable 2FA
        await user_service.disable_2fa(user)
        print(f"2FA disabled for user '{username}'")
        return True


async def main():
    """Main function."""
    username = "testuser_qa"
    print(f"Disabling 2FA for user: {username}")

    success = await disable_2fa_for_user(username)
    if success:
        print("✅ 2FA disabled successfully")
    else:
        print("❌ Failed to disable 2FA")


if __name__ == "__main__":
    asyncio.run(main())
