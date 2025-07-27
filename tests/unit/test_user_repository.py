"""Unit tests for UserRepository."""

import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository


class TestUserRepository:
    """Test cases for UserRepository."""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_repository: UserRepository) -> None:
        """Test successful user creation."""
        username = "testuser"
        hashed_password = "hashed_password_123"
        role = UserRole.COMMON_USER
        
        user = await user_repository.create(
            username=username,
            hashed_password=hashed_password,
            role=role
        )
        
        assert user.id is not None
        assert user.username == username
        assert user.hashed_password == hashed_password
        assert user.role == role
        assert user.is_active is True
        assert user.is_2fa_enabled is False
        assert user.totp_secret is None
    
    @pytest.mark.asyncio
    async def test_create_user_with_2fa(self, user_repository: UserRepository) -> None:
        """Test user creation with 2FA."""
        username = "testuser2fa"
        hashed_password = "hashed_password_123"
        role = UserRole.COMMON_USER
        totp_secret = "JBSWY3DPEHPK3PXP"
        
        user = await user_repository.create(
            username=username,
            hashed_password=hashed_password,
            role=role,
            totp_secret=totp_secret
        )
        
        assert user.totp_secret == totp_secret
        assert user.is_2fa_enabled is True
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, user_repository: UserRepository) -> None:
        """Test user creation with duplicate username."""
        username = "duplicate"
        hashed_password = "hashed_password_123"
        role = UserRole.COMMON_USER
        
        # Create first user
        await user_repository.create(username, hashed_password, role)
        
        # Try to create second user with same username
        with pytest.raises(ValueError, match="Username 'duplicate' already exists"):
            await user_repository.create(username, hashed_password, role)
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, user_repository: UserRepository) -> None:
        """Test getting user by ID."""
        # Create a user first
        created_user = await user_repository.create(
            "testuser", "hashed_password", UserRole.COMMON_USER
        )
        
        # Get the user by ID
        found_user = await user_repository.get_by_id(created_user.id)
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.username == created_user.username
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, user_repository: UserRepository) -> None:
        """Test getting user by nonexistent ID."""
        random_id = uuid.uuid4()
        found_user = await user_repository.get_by_id(random_id)
        
        assert found_user is None
    
    @pytest.mark.asyncio
    async def test_get_by_username_success(self, user_repository: UserRepository) -> None:
        """Test getting user by username."""
        username = "testuser"
        
        # Create a user first
        created_user = await user_repository.create(
            username, "hashed_password", UserRole.COMMON_USER
        )
        
        # Get the user by username
        found_user = await user_repository.get_by_username(username)
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.username == username
    
    @pytest.mark.asyncio
    async def test_get_by_username_not_found(self, user_repository: UserRepository) -> None:
        """Test getting user by nonexistent username."""
        found_user = await user_repository.get_by_username("nonexistent")
        
        assert found_user is None
    
    @pytest.mark.asyncio
    async def test_update_user(self, user_repository: UserRepository) -> None:
        """Test updating user."""
        # Create a user first
        user = await user_repository.create(
            "testuser", "hashed_password", UserRole.COMMON_USER
        )
        
        # Update user fields
        user.totp_secret = "JBSWY3DPEHPK3PXP"
        user.is_2fa_enabled = True
        
        # Update in repository
        updated_user = await user_repository.update(user)
        
        assert updated_user.totp_secret == "JBSWY3DPEHPK3PXP"
        assert updated_user.is_2fa_enabled is True
    
    @pytest.mark.asyncio
    async def test_is_username_taken_true(self, user_repository: UserRepository) -> None:
        """Test checking if username is taken (true case)."""
        username = "testuser"
        
        # Create a user first
        await user_repository.create(username, "hashed_password", UserRole.COMMON_USER)
        
        # Check if username is taken
        is_taken = await user_repository.is_username_taken(username)
        
        assert is_taken is True
    
    @pytest.mark.asyncio
    async def test_is_username_taken_false(self, user_repository: UserRepository) -> None:
        """Test checking if username is taken (false case)."""
        is_taken = await user_repository.is_username_taken("nonexistent")
        
        assert is_taken is False
    
    @pytest.mark.asyncio
    async def test_delete_user(self, user_repository: UserRepository) -> None:
        """Test deleting user."""
        # Create a user first
        user = await user_repository.create(
            "testuser", "hashed_password", UserRole.COMMON_USER
        )
        
        # Delete the user
        await user_repository.delete(user)
        
        # Try to find the user (should not exist)
        found_user = await user_repository.get_by_id(user.id)
        assert found_user is None