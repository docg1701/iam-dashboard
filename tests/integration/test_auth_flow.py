"""Integration tests for authentication flows."""

import pytest
import pyotp
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.core.auth import AuthManager


class TestAuthFlow:
    """Integration tests for complete authentication flows."""
    
    @pytest.mark.asyncio
    async def test_complete_registration_flow(self, async_session: AsyncSession) -> None:
        """Test complete user registration flow."""
        # Initialize services
        user_repository = UserRepository(async_session)
        user_service = UserService(user_repository)
        
        # Registration data
        username = "integration_user"
        password = "integration_password123"
        role = UserRole.COMMON_USER
        
        # Step 1: Create user
        user = await user_service.create_user(
            username=username,
            password=password,
            role=role,
            enable_2fa=True
        )
        
        # Verify user was created correctly
        assert user.username == username
        assert user.role == role
        assert user.is_2fa_enabled is True
        assert user.totp_secret is not None
        assert user.is_active is True
        
        # Step 2: Verify user can be found in database
        found_user = await user_service.get_user_by_username(username)
        assert found_user is not None
        assert found_user.id == user.id
        
        # Step 3: Verify password authentication works
        authenticated_user = await user_service.authenticate_user(username, password)
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        
        # Step 4: Verify 2FA works
        totp = pyotp.TOTP(user.totp_secret)
        valid_code = totp.now()
        is_2fa_valid = await user_service.verify_totp_code(user, valid_code)
        assert is_2fa_valid is True
    
    @pytest.mark.asyncio
    async def test_complete_login_flow_with_2fa(self, async_session: AsyncSession) -> None:
        """Test complete login flow with 2FA."""
        # Initialize services
        user_repository = UserRepository(async_session)
        user_service = UserService(user_repository)
        
        # Create test user
        username = "login_test_user"
        password = "login_password123"
        
        user = await user_service.create_user(
            username=username,
            password=password,
            role=UserRole.COMMON_USER,
            enable_2fa=True
        )
        
        # Step 1: Authenticate with username/password
        authenticated_user = await user_service.authenticate_user(username, password)
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        
        # Step 2: Verify 2FA is required
        assert authenticated_user.is_2fa_enabled is True
        
        # Step 3: Generate and verify 2FA code
        totp = pyotp.TOTP(authenticated_user.totp_secret)
        valid_code = totp.now()
        is_2fa_valid = await user_service.verify_totp_code(authenticated_user, valid_code)
        assert is_2fa_valid is True
        
        # Step 4: Complete login (simulate session creation)
        token = AuthManager.create_access_token(str(user.id), user.username)
        assert token is not None
        
        # Step 5: Verify token is valid
        payload = AuthManager.verify_token(token)
        assert payload is not None
        assert payload["user_id"] == str(user.id)
        assert payload["username"] == user.username
    
    @pytest.mark.asyncio
    async def test_complete_login_flow_without_2fa(self, async_session: AsyncSession) -> None:
        """Test complete login flow without 2FA."""
        # Initialize services
        user_repository = UserRepository(async_session)
        user_service = UserService(user_repository)
        
        # Create test user without 2FA
        username = "login_no2fa_user"
        password = "login_password123"
        
        user = await user_service.create_user(
            username=username,
            password=password,
            role=UserRole.COMMON_USER,
            enable_2fa=False
        )
        
        # Step 1: Authenticate with username/password
        authenticated_user = await user_service.authenticate_user(username, password)
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        
        # Step 2: Verify 2FA is not required
        assert authenticated_user.is_2fa_enabled is False
        
        # Step 3: 2FA verification should pass automatically
        is_2fa_valid = await user_service.verify_totp_code(authenticated_user, "any_code")
        assert is_2fa_valid is True
        
        # Step 4: Complete login
        token = AuthManager.create_access_token(str(user.id), user.username)
        assert token is not None
        
        # Step 5: Verify token is valid
        payload = AuthManager.verify_token(token)
        assert payload is not None
        assert payload["user_id"] == str(user.id)
        assert payload["username"] == user.username
    
    @pytest.mark.asyncio
    async def test_2fa_enable_disable_flow(self, async_session: AsyncSession) -> None:
        """Test enabling and disabling 2FA."""
        # Initialize services
        user_repository = UserRepository(async_session)
        user_service = UserService(user_repository)
        
        # Create user without 2FA
        username = "2fa_toggle_user"
        password = "password123"
        
        user = await user_service.create_user(
            username=username,
            password=password,
            role=UserRole.COMMON_USER,
            enable_2fa=False
        )
        
        # Verify 2FA is initially disabled
        assert user.is_2fa_enabled is False
        assert user.totp_secret is None
        
        # Step 1: Enable 2FA
        secret = await user_service.enable_2fa(user)
        
        # Verify 2FA is now enabled
        assert user.is_2fa_enabled is True
        assert user.totp_secret == secret
        assert secret is not None
        
        # Step 2: Test 2FA works
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()
        is_valid = await user_service.verify_totp_code(user, valid_code)
        assert is_valid is True
        
        # Step 3: Disable 2FA
        await user_service.disable_2fa(user)
        
        # Verify 2FA is now disabled
        assert user.is_2fa_enabled is False
        assert user.totp_secret is None
        
        # Step 4: 2FA verification should pass automatically
        is_valid = await user_service.verify_totp_code(user, "any_code")
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_failed_login_attempts(self, async_session: AsyncSession) -> None:
        """Test various failed login scenarios."""
        # Initialize services
        user_repository = UserRepository(async_session)
        user_service = UserService(user_repository)
        
        # Create test user
        username = "fail_test_user"
        password = "correct_password123"
        
        user = await user_service.create_user(
            username=username,
            password=password,
            role=UserRole.COMMON_USER,
            enable_2fa=True
        )
        
        # Test 1: Wrong password
        authenticated_user = await user_service.authenticate_user(username, "wrong_password")
        assert authenticated_user is None
        
        # Test 2: Non-existent user
        authenticated_user = await user_service.authenticate_user("nonexistent", password)
        assert authenticated_user is None
        
        # Test 3: Correct credentials but wrong 2FA code
        authenticated_user = await user_service.authenticate_user(username, password)
        assert authenticated_user is not None
        
        is_2fa_valid = await user_service.verify_totp_code(authenticated_user, "000000")
        assert is_2fa_valid is False
        
        # Test 4: Correct credentials and correct 2FA code
        totp = pyotp.TOTP(authenticated_user.totp_secret)
        valid_code = totp.now()
        is_2fa_valid = await user_service.verify_totp_code(authenticated_user, valid_code)
        assert is_2fa_valid is True
    
    @pytest.mark.asyncio
    async def test_user_roles_and_permissions(self, async_session: AsyncSession) -> None:
        """Test user roles and permission properties."""
        # Initialize services
        user_repository = UserRepository(async_session)
        user_service = UserService(user_repository)
        
        # Test different user roles
        roles_to_test = [
            (UserRole.SYSADMIN, True, True),      # is_admin, is_sysadmin
            (UserRole.ADMIN_USER, True, False),   # is_admin, is_sysadmin
            (UserRole.COMMON_USER, False, False), # is_admin, is_sysadmin
        ]
        
        for role, expected_is_admin, expected_is_sysadmin in roles_to_test:
            user = await user_service.create_user(
                username=f"user_{role.value}",
                password="password123",
                role=role,
                enable_2fa=False
            )
            
            assert user.role == role
            assert user.is_admin == expected_is_admin
            assert user.is_sysadmin == expected_is_sysadmin