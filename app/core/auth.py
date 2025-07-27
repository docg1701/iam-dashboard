"""Authentication and session management utilities."""

import os
from datetime import datetime, timedelta

from jose import JWTError, jwt
from nicegui import app

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


class AuthManager:
    """Authentication and session management."""

    @staticmethod
    def create_access_token(user_id: str, username: str) -> str:
        """Create a JWT access token."""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": user_id,
            "username": username,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> dict | None:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            username = payload.get("username")

            if user_id is None or username is None:
                return None

            return {"user_id": user_id, "username": username}
        except JWTError:
            return None

    @staticmethod
    def login_user(
        user_id: str,
        username: str,
        role: str = None,
        is_active: bool = True,
        is_2fa_enabled: bool = False,
    ) -> str:
        """Login a user and store session data."""
        # Create JWT token
        token = AuthManager.create_access_token(str(user_id), username)

        # Store in NiceGUI session
        app.storage.user.update(
            {
                "authenticated": True,
                "user_id": str(user_id),
                "username": username,
                "token": token,
                "role": role,
                "is_active": is_active,
                "is_2fa_enabled": is_2fa_enabled,
                "login_time": datetime.utcnow().isoformat(),
            }
        )

        return token

    @staticmethod
    def logout_user() -> None:
        """Logout the current user."""
        app.storage.user.clear()

    @staticmethod
    def get_current_user() -> dict | None:
        """Get the current authenticated user from session."""
        if not app.storage.user.get("authenticated"):
            return None

        token = app.storage.user.get("token")
        if not token:
            return None

        # Verify token is still valid
        payload = AuthManager.verify_token(token)
        if not payload:
            # Token invalid, clear session
            AuthManager.logout_user()
            return None

        # Return basic session data (can be enhanced to fetch full user data if needed)
        return {
            "user_id": app.storage.user.get("user_id"),
            "username": app.storage.user.get("username"),
            "login_time": app.storage.user.get("login_time"),
            "role": app.storage.user.get("role", "Não disponível"),
            "is_active": app.storage.user.get("is_active", True),
            "is_2fa_enabled": app.storage.user.get("is_2fa_enabled", False),
        }

    @staticmethod
    def is_authenticated() -> bool:
        """Check if current user is authenticated."""
        return AuthManager.get_current_user() is not None

    @staticmethod
    def require_auth():
        """Decorator/middleware to require authentication."""
        if not AuthManager.is_authenticated():
            from nicegui import ui

            ui.navigate.to("/login")
            return False
        return True
