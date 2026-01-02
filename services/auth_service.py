"""
PolicyHub Authentication Service

Handles user authentication, password hashing, and session creation.
"""

import logging
from typing import Optional

import bcrypt

from app.constants import UserRole
from core.database import DatabaseManager
from core.session import SessionManager, UserSession
from models.user import User
from utils.dates import get_now
from utils.files import generate_uuid

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service for authentication operations.

    Handles:
    - Password hashing and verification
    - User authentication
    - First admin creation
    - Session management
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize the auth service.

        Args:
            db: Database manager instance
        """
        self.db = db
        self.session_manager = SessionManager.get_instance()

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Bcrypt hashed password
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            password: Plain text password to verify
            password_hash: Bcrypt hash to verify against

        Returns:
            True if password matches
        """
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8"),
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username and password.

        Args:
            username: Username to authenticate
            password: Password to verify

        Returns:
            User object if authentication succeeds, None otherwise
        """
        # Fetch user by username
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE username = ? AND is_active = 1",
            (username,),
        )

        if row is None:
            logger.warning(f"Authentication failed: user not found - {username}")
            return None

        user = User.from_row(row)

        # Verify password
        if not self.verify_password(password, user.password_hash):
            logger.warning(f"Authentication failed: wrong password - {username}")
            return None

        # Update last login
        self._update_last_login(user.user_id)

        logger.info(f"User authenticated successfully: {username}")
        return user

    def login(self, username: str, password: str) -> Optional[UserSession]:
        """
        Authenticate a user and create a session.

        Args:
            username: Username to authenticate
            password: Password to verify

        Returns:
            UserSession if login succeeds, None otherwise
        """
        user = self.authenticate(username, password)

        if user is None:
            return None

        # Create session
        session = self.session_manager.login(
            user_id=user.user_id,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
        )

        return session

    def logout(self) -> None:
        """Log out the current user."""
        self.session_manager.logout()
        logger.info("User logged out")

    def create_first_admin(
        self,
        username: str,
        password: str,
        full_name: str,
        email: Optional[str] = None,
    ) -> User:
        """
        Create the first admin user (during initial setup).

        Args:
            username: Admin username
            password: Admin password
            full_name: Admin's full name
            email: Admin's email (optional)

        Returns:
            Created User object

        Raises:
            RuntimeError: If users already exist
        """
        # Check no users exist
        if self.db.has_any_users():
            raise RuntimeError("Cannot create first admin: users already exist")

        user_id = generate_uuid()
        password_hash = self.hash_password(password)
        now = get_now()

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (
                    user_id, username, password_hash, full_name, email,
                    role, is_active, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, NULL)
                """,
                (
                    user_id,
                    username,
                    password_hash,
                    full_name,
                    email,
                    UserRole.ADMIN.value,
                    now,
                ),
            )

        logger.info(f"First admin created: {username}")

        # Fetch and return the created user
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        )
        return User.from_row(row)

    def _update_last_login(self, user_id: str) -> None:
        """
        Update the last login timestamp for a user.

        Args:
            user_id: User's ID
        """
        now = get_now()
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE users SET last_login = ? WHERE user_id = ?",
                (now, user_id),
            )

    def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> tuple[bool, str]:
        """
        Change a user's password.

        Args:
            user_id: User's ID
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            Tuple of (success, error_message)
        """
        # Fetch user
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        )

        if row is None:
            return False, "User not found"

        user = User.from_row(row)

        # Verify current password
        if not self.verify_password(current_password, user.password_hash):
            return False, "Current password is incorrect"

        # Update password
        new_hash = self.hash_password(new_password)
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE user_id = ?",
                (new_hash, user_id),
            )

        logger.info(f"Password changed for user: {user.username}")
        return True, ""

    def reset_password(self, user_id: str, new_password: str) -> bool:
        """
        Reset a user's password (admin function).

        Args:
            user_id: User's ID
            new_password: New password to set

        Returns:
            True if successful
        """
        new_hash = self.hash_password(new_password)
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE users SET password_hash = ? WHERE user_id = ?",
                (new_hash, user_id),
            )
            if cursor.rowcount > 0:
                logger.info(f"Password reset for user_id: {user_id}")
                return True
        return False

    @property
    def current_user(self) -> Optional[UserSession]:
        """Get the current logged-in user session."""
        return self.session_manager.current_user

    @property
    def is_authenticated(self) -> bool:
        """Check if a user is currently logged in."""
        return self.session_manager.is_authenticated
