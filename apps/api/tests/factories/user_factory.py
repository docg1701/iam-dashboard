"""
User factory for generating test user data.

Provides realistic test data generation for User models with different roles
and authentication scenarios.
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from src.models.user import User, UserRole
from .base_factory import BaseFactory


class UserFactory(BaseFactory):
    """Factory for creating User test instances."""
    
    @classmethod
    def create_user(
        self,
        email: Optional[str] = None,
        password: str = "testpass123",
        role: Optional[UserRole] = None,
        is_active: bool = True,
        totp_secret: Optional[str] = None,
        last_login_at: Optional[datetime] = None,
        failed_login_attempts: int = 0,
        locked_until: Optional[datetime] = None,
        **kwargs
    ) -> User:
        """
        Create a User instance with realistic test data.
        
        Args:
            email: User email (auto-generated if None)
            password: Plain password to hash (default: testpass123)
            role: User role (random if None)
            is_active: Account active status
            totp_secret: TOTP secret for 2FA
            last_login_at: Last login timestamp
            failed_login_attempts: Failed login count
            locked_until: Account lock expiration
            **kwargs: Additional fields to override
            
        Returns:
            User instance with test data
        """
        # Generate email if not provided
        if email is None:
            email = self.generate_email()
        
        # Generate random role if not provided
        if role is None:
            role = self.pick_random(list(UserRole))
        
        # Hash the password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Create base user data
        user_data = {
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "is_active": is_active,
            "totp_secret": totp_secret,
            "last_login_at": last_login_at,
            "failed_login_attempts": failed_login_attempts,
            "locked_until": locked_until,
            **kwargs
        }
        
        return User(**user_data)
    
    @classmethod
    def create_sysadmin(self, email: Optional[str] = None, **kwargs) -> User:
        """Create a sysadmin user."""
        return self.create_user(
            email=email or "sysadmin@example.com",
            role=UserRole.SYSADMIN,
            **kwargs
        )
    
    @classmethod 
    def create_admin(self, email: Optional[str] = None, **kwargs) -> User:
        """Create an admin user."""
        return self.create_user(
            email=email or "admin@example.com",
            role=UserRole.ADMIN,
            **kwargs
        )
    
    @classmethod
    def create_regular_user(self, email: Optional[str] = None, **kwargs) -> User:
        """Create a regular user."""
        return self.create_user(
            email=email or self.generate_email(),
            role=UserRole.USER,
            **kwargs
        )
    
    @classmethod
    def create_user_with_2fa(self, email: Optional[str] = None, **kwargs) -> User:
        """Create a user with 2FA enabled."""
        totp_secret = secrets.token_hex(16)
        return self.create_user(
            email=email,
            totp_secret=totp_secret,
            **kwargs
        )
    
    @classmethod
    def create_locked_user(
        self,
        email: Optional[str] = None,
        lock_duration_hours: int = 24,
        **kwargs
    ) -> User:
        """Create a locked user account."""
        locked_until = datetime.utcnow() + timedelta(hours=lock_duration_hours)
        return self.create_user(
            email=email,
            failed_login_attempts=5,
            locked_until=locked_until,
            is_active=False,
            **kwargs
        )
    
    @classmethod
    def create_inactive_user(self, email: Optional[str] = None, **kwargs) -> User:
        """Create an inactive user account."""
        return self.create_user(
            email=email,
            is_active=False,
            **kwargs
        )
    
    @classmethod
    def create_user_with_login_history(
        self,
        email: Optional[str] = None,
        days_since_login: int = 1,
        **kwargs
    ) -> User:
        """Create a user with recent login history."""
        last_login = datetime.utcnow() - timedelta(days=days_since_login)
        return self.create_user(
            email=email,
            last_login_at=last_login,
            **kwargs
        )
    
    @classmethod
    def create_multiple_users(
        self,
        count: int,
        role_distribution: Optional[dict] = None,
        **kwargs
    ) -> list[User]:
        """
        Create multiple users with specified role distribution.
        
        Args:
            count: Number of users to create
            role_distribution: Dict mapping UserRole to percentage (0-1)
            **kwargs: Additional arguments for user creation
            
        Returns:
            List of User instances
        """
        if role_distribution is None:
            role_distribution = {
                UserRole.SYSADMIN: 0.1,
                UserRole.ADMIN: 0.2,
                UserRole.USER: 0.7,
            }
        
        users = []
        for i in range(count):
            # Determine role based on distribution
            if i < count * role_distribution.get(UserRole.SYSADMIN, 0):
                role = UserRole.SYSADMIN
            elif i < count * (role_distribution.get(UserRole.SYSADMIN, 0) + 
                            role_distribution.get(UserRole.ADMIN, 0)):
                role = UserRole.ADMIN
            else:
                role = UserRole.USER
            
            user = self.create_user(
                role=role,
                email=self.generate_email(domain="testdomain.com"),
                **kwargs
            )
            users.append(user)
        
        return users
    
    @classmethod
    def get_default_password_hash(cls, password: str = "testpass123") -> str:
        """Get the default password hash for testing."""
        return hashlib.sha256(password.encode()).hexdigest()