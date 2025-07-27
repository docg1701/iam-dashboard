"""Unit tests for UserService."""

import pytest
import pyotp
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


class TestUserService:
    """Test cases for UserService."""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service: UserService) -> None:
        """Test successful user creation."""
        username = "newuser"
        password = "password123"
        role = UserRole.COMMON_USER
        
        user = await user_service.create_user(
            username=username,
            password=password,
            role=role,
            enable_2fa=True
        )
        
        assert user.username == username
        assert user.role == role
        assert user.is_2fa_enabled is True
        assert user.totp_secret is not None
        assert user.is_active is True
        # Password should be hashed
        assert user.hashed_password != password
    
    @pytest.mark.asyncio
    async def test_create_user_without_2fa(self, user_service: UserService) -> None:
        """Test user creation without 2FA."""
        username = "user_no2fa"
        password = "password123"
        
        user = await user_service.create_user(
            username=username,
            password=password,
            role=UserRole.COMMON_USER,
            enable_2fa=False
        )
        
        assert user.username == username
        assert user.is_2fa_enabled is False
        assert user.totp_secret is None
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, user_service: UserService) -> None:
        """Test user creation with duplicate username."""
        username = "duplicate"
        password = "password123"
        
        # Create first user
        await user_service.create_user(username, password)
        
        # Try to create second user with same username
        with pytest.raises(ValueError, match="Username 'duplicate' is already taken"):
            await user_service.create_user(username, password)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, user_service: UserService, test_user: User) -> None:
        """Test successful user authentication."""
        authenticated_user = await user_service.authenticate_user("testuser", "testpassword123")
        
        assert authenticated_user is not None
        assert authenticated_user.id == test_user.id
        assert authenticated_user.username == test_user.username
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, user_service: UserService, test_user: User) -> None:
        """Test authentication with wrong password."""
        authenticated_user = await user_service.authenticate_user("testuser", "wrongpassword")
        
        assert authenticated_user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent(self, user_service: UserService) -> None:
        """Test authentication with nonexistent user."""
        authenticated_user = await user_service.authenticate_user("nonexistent", "password")
        
        assert authenticated_user is None
    
    @pytest.mark.asyncio
    async def test_verify_totp_code_success(self, user_service: UserService, test_user: User) -> None:
        """Test successful TOTP code verification."""
        # Generate valid TOTP code
        totp = pyotp.TOTP(test_user.totp_secret)
        valid_code = totp.now()
        
        is_valid = await user_service.verify_totp_code(test_user, valid_code)
        
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_verify_totp_code_invalid(self, user_service: UserService, test_user: User) -> None:
        """Test TOTP code verification with invalid code."""
        is_valid = await user_service.verify_totp_code(test_user, "000000")
        
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_verify_totp_code_no_2fa(self, user_service: UserService, test_user_no_2fa: User) -> None:
        """Test TOTP code verification for user without 2FA."""
        is_valid = await user_service.verify_totp_code(test_user_no_2fa, "123456")
        
        # Should return True when 2FA is not enabled
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_get_totp_provisioning_uri(self, user_service: UserService, test_user: User) -> None:
        """Test getting TOTP provisioning URI."""
        uri = user_service.get_totp_provisioning_uri(test_user)
        
        assert uri is not None
        assert "otpauth://totp/" in uri
        assert test_user.username in uri
        assert "IAM%20Dashboard" in uri or "IAM Dashboard" in uri
    
    @pytest.mark.asyncio
    async def test_get_totp_provisioning_uri_no_secret(self, user_service: UserService, test_user_no_2fa: User) -> None:
        """Test getting TOTP provisioning URI for user without secret."""
        uri = user_service.get_totp_provisioning_uri(test_user_no_2fa)
        
        assert uri is None
    
    @pytest.mark.asyncio
    async def test_enable_2fa(self, user_service: UserService, test_user_no_2fa: User) -> None:
        """Test enabling 2FA for a user."""
        secret = await user_service.enable_2fa(test_user_no_2fa)
        
        assert secret is not None
        assert len(secret) == 32  # Base32 secret length
        assert test_user_no_2fa.is_2fa_enabled is True
        assert test_user_no_2fa.totp_secret == secret
    
    @pytest.mark.asyncio
    async def test_disable_2fa(self, user_service: UserService, test_user: User) -> None:
        """Test disabling 2FA for a user."""
        await user_service.disable_2fa(test_user)
        
        assert test_user.is_2fa_enabled is False
        assert test_user.totp_secret is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, user_service: UserService, test_user: User) -> None:
        """Test getting user by ID."""
        found_user = await user_service.get_user_by_id(test_user.id)
        
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.username == test_user.username
    
    @pytest.mark.asyncio
    async def test_get_user_by_username(self, user_service: UserService, test_user: User) -> None:
        """Test getting user by username."""
        found_user = await user_service.get_user_by_username(test_user.username)
        
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.username == test_user.username