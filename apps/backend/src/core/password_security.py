"""
Password security enhancements for authentication system.

This module provides password reset, password history, and account lockout
functionality to enhance the security of the authentication system.
"""

import contextlib
import secrets
from datetime import datetime, timedelta
from typing import TypedDict
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel

from .security import auth_service


class PasswordResetToken(BaseModel):
    """Password reset token data structure."""

    user_id: str
    email: str
    expires_at: str
    token_type: str = "password_reset"


class LoginAttempt(BaseModel):
    """Login attempt tracking data."""

    email: str
    ip_address: str
    attempted_at: str
    success: bool


class LockoutInfo(TypedDict):
    """Account lockout information structure."""
    
    locked: bool
    unlock_in_minutes: int
    failed_attempts: int


class PasswordSecurityService:
    """Service for password security enhancements."""

    def __init__(self) -> None:
        self.redis_client = auth_service.redis_client
        self.reset_token_expire_hours = 1  # Password reset tokens expire in 1 hour
        self.max_failed_attempts = 5  # Lock account after 5 failed attempts
        self.lockout_duration_minutes = 15  # Lock account for 15 minutes
        self.password_history_count = 5  # Remember last 5 passwords

    def generate_reset_token(self, user_id: UUID, user_email: str) -> str:
        """Generate a secure password reset token."""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=self.reset_token_expire_hours)

        # Store reset token data in Redis
        reset_data = PasswordResetToken(
            user_id=str(user_id), email=user_email, expires_at=expires_at.isoformat()
        )

        try:
            self.redis_client.setex(
                f"password_reset:{token}",
                timedelta(hours=self.reset_token_expire_hours),
                reset_data.model_dump_json(),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to generate reset token",
            ) from e

        return token

    def verify_reset_token(self, token: str) -> PasswordResetToken | None:
        """Verify and retrieve password reset token data."""
        try:
            token_json = self.redis_client.get(f"password_reset:{token}")
            if token_json:
                token_data = PasswordResetToken.model_validate_json(token_json)
                # Check if token is expired
                expires_at = datetime.fromisoformat(token_data.expires_at)
                if datetime.utcnow() < expires_at:
                    return token_data
        except Exception:
            pass
        return None

    def revoke_reset_token(self, token: str) -> None:
        """Revoke a password reset token after use."""
        with contextlib.suppress(Exception):
            self.redis_client.delete(f"password_reset:{token}")

    def record_login_attempt(self, email: str, ip_address: str, success: bool) -> None:
        """Record a login attempt for tracking failed attempts."""
        attempt = LoginAttempt(
            email=email,
            ip_address=ip_address,
            attempted_at=datetime.utcnow().isoformat(),
            success=success,
        )

        try:
            # Store in Redis with expiration based on lockout duration
            expiry = timedelta(minutes=self.lockout_duration_minutes + 5)
            self.redis_client.lpush(f"login_attempts:{email}", attempt.model_dump_json())
            self.redis_client.expire(f"login_attempts:{email}", expiry)

            # Limit the list to recent attempts only
            self.redis_client.ltrim(f"login_attempts:{email}", 0, 19)  # Keep last 20 attempts

        except Exception:
            # If Redis is unavailable, don't fail the login process
            pass

    def is_account_locked(self, email: str) -> bool:
        """Check if an account is locked due to failed login attempts."""
        try:
            attempts_json = self.redis_client.lrange(f"login_attempts:{email}", 0, -1)

            if not attempts_json:
                return False

            recent_failed_attempts = []
            cutoff_time = datetime.utcnow() - timedelta(minutes=self.lockout_duration_minutes)

            for attempt_json in attempts_json:
                try:
                    attempt = LoginAttempt.model_validate_json(attempt_json)
                    attempt_time = datetime.fromisoformat(attempt.attempted_at)

                    # Only consider recent attempts
                    if attempt_time > cutoff_time:
                        if not attempt.success:
                            recent_failed_attempts.append(attempt)
                        else:
                            # If there's a successful login, break the chain of failed attempts
                            break
                except Exception:
                    continue

            return len(recent_failed_attempts) >= self.max_failed_attempts

        except Exception:
            # If Redis is unavailable, don't lock accounts
            return False

    def clear_failed_attempts(self, email: str) -> None:
        """Clear failed login attempts for an account after successful login."""
        with contextlib.suppress(Exception):
            self.redis_client.delete(f"login_attempts:{email}")

    def store_password_hash(self, user_id: UUID, password_hash: str) -> None:
        """Store a password hash in the user's password history."""
        try:
            history_key = f"password_history:{user_id}"

            # Add new hash to the front of the list
            self.redis_client.lpush(history_key, password_hash)

            # Keep only the last N passwords
            self.redis_client.ltrim(history_key, 0, self.password_history_count - 1)

            # Set expiration (keep password history for 90 days)
            self.redis_client.expire(history_key, timedelta(days=90))

        except Exception:
            # If Redis is unavailable, don't fail password changes
            pass

    def is_password_reused(self, user_id: UUID, new_password: str) -> bool:
        """Check if a password has been used recently."""
        try:
            history_key = f"password_history:{user_id}"
            password_hashes = self.redis_client.lrange(history_key, 0, -1)

            for stored_hash in password_hashes:
                if auth_service.verify_password(new_password, stored_hash):
                    return True

            return False

        except Exception:
            # If Redis is unavailable, allow password change
            return False

    def get_lockout_info(self, email: str) -> LockoutInfo | None:
        """Get information about account lockout status."""
        if not self.is_account_locked(email):
            return None

        try:
            attempts_json = self.redis_client.lrange(f"login_attempts:{email}", 0, 4)

            if attempts_json:
                # Get the time of the most recent failed attempt
                latest_attempt = LoginAttempt.model_validate_json(attempts_json[0])
                latest_time = datetime.fromisoformat(latest_attempt.attempted_at)
                unlock_time = latest_time + timedelta(minutes=self.lockout_duration_minutes)

                remaining_minutes = max(
                    0, int((unlock_time - datetime.utcnow()).total_seconds() / 60)
                )

                return {
                    "locked": True,
                    "unlock_in_minutes": remaining_minutes,
                    "failed_attempts": len(attempts_json),
                }
        except Exception:
            pass

        return {
            "locked": True,
            "unlock_in_minutes": self.lockout_duration_minutes,
            "failed_attempts": self.max_failed_attempts,
        }


# Global password security service instance
password_security_service = PasswordSecurityService()
