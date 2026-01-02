"""
PolicyHub User Service

Handles CRUD operations for user accounts.
"""

import logging
from typing import List, Optional

from app.constants import UserRole
from core.database import DatabaseManager
from core.permissions import Permission, require_permission
from core.session import SessionManager
from models.user import User, UserCreate, UserUpdate
from services.auth_service import AuthService
from utils.dates import get_now
from utils.files import generate_uuid

logger = logging.getLogger(__name__)


class UserService:
    """
    Service for user management operations.

    All mutating operations require appropriate permissions.
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize the user service.

        Args:
            db: Database manager instance
        """
        self.db = db
        self.auth_service = AuthService(db)

    def get_all_users(self, include_inactive: bool = False) -> List[User]:
        """
        Get all users.

        Args:
            include_inactive: Whether to include inactive users

        Returns:
            List of User objects
        """
        if include_inactive:
            query = "SELECT * FROM users ORDER BY username"
            rows = self.db.fetch_all(query)
        else:
            query = "SELECT * FROM users WHERE is_active = 1 ORDER BY username"
            rows = self.db.fetch_all(query)

        return [User.from_row(row) for row in rows]

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: User's unique ID

        Returns:
            User object or None if not found
        """
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        )
        return User.from_row(row) if row else None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.

        Args:
            username: Username to search for

        Returns:
            User object or None if not found
        """
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        )
        return User.from_row(row) if row else None

    def username_exists(self, username: str, exclude_user_id: Optional[str] = None) -> bool:
        """
        Check if a username is already taken.

        Args:
            username: Username to check
            exclude_user_id: User ID to exclude from check (for updates)

        Returns:
            True if username exists
        """
        if exclude_user_id:
            row = self.db.fetch_one(
                "SELECT 1 FROM users WHERE username = ? AND user_id != ?",
                (username, exclude_user_id),
            )
        else:
            row = self.db.fetch_one(
                "SELECT 1 FROM users WHERE username = ?",
                (username,),
            )
        return row is not None

    @require_permission(Permission.MANAGE_USERS)
    def create_user(self, data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            data: User creation data

        Returns:
            Created User object

        Raises:
            ValueError: If username already exists
            PermissionError: If current user lacks permission
        """
        # Check username availability
        if self.username_exists(data.username):
            raise ValueError(f"Username '{data.username}' is already taken")

        user_id = generate_uuid()
        password_hash = self.auth_service.hash_password(data.password)
        now = get_now()
        created_by = SessionManager.get_instance().user_id

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (
                    user_id, username, password_hash, full_name, email,
                    role, is_active, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    user_id,
                    data.username,
                    password_hash,
                    data.full_name,
                    data.email,
                    data.role,
                    now,
                    created_by,
                ),
            )

        logger.info(f"User created: {data.username} by {created_by}")

        return self.get_user_by_id(user_id)

    @require_permission(Permission.MANAGE_USERS)
    def update_user(self, user_id: str, data: UserUpdate) -> Optional[User]:
        """
        Update a user's information.

        Args:
            user_id: User's ID
            data: Update data

        Returns:
            Updated User object or None if not found

        Raises:
            PermissionError: If current user lacks permission
        """
        user = self.get_user_by_id(user_id)
        if user is None:
            return None

        # Build update query
        updates = []
        params = []

        if data.full_name is not None:
            updates.append("full_name = ?")
            params.append(data.full_name)

        if data.email is not None:
            updates.append("email = ?")
            params.append(data.email)

        if data.role is not None:
            # Prevent removing the last admin
            if user.role == UserRole.ADMIN.value and data.role != UserRole.ADMIN.value:
                if self.count_admins() <= 1:
                    raise ValueError("Cannot change role: this is the last admin")
            updates.append("role = ?")
            params.append(data.role)

        if data.is_active is not None:
            # Prevent deactivating the last admin
            if user.role == UserRole.ADMIN.value and not data.is_active:
                if self.count_active_admins() <= 1:
                    raise ValueError("Cannot deactivate: this is the last active admin")
            updates.append("is_active = ?")
            params.append(1 if data.is_active else 0)

        if not updates:
            return user  # Nothing to update

        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"

        with self.db.get_connection() as conn:
            conn.execute(query, tuple(params))

        logger.info(f"User updated: {user.username}")
        return self.get_user_by_id(user_id)

    @require_permission(Permission.MANAGE_USERS)
    def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user account.

        Args:
            user_id: User's ID

        Returns:
            True if successful

        Raises:
            ValueError: If trying to deactivate the last admin
            PermissionError: If current user lacks permission
        """
        user = self.get_user_by_id(user_id)
        if user is None:
            return False

        # Prevent deactivating the last admin
        if user.role == UserRole.ADMIN.value:
            if self.count_active_admins() <= 1:
                raise ValueError("Cannot deactivate: this is the last active admin")

        # Prevent self-deactivation
        current_user_id = SessionManager.get_instance().user_id
        if user_id == current_user_id:
            raise ValueError("Cannot deactivate your own account")

        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE users SET is_active = 0 WHERE user_id = ?",
                (user_id,),
            )

        logger.info(f"User deactivated: {user.username}")
        return True

    @require_permission(Permission.MANAGE_USERS)
    def activate_user(self, user_id: str) -> bool:
        """
        Activate a user account.

        Args:
            user_id: User's ID

        Returns:
            True if successful

        Raises:
            PermissionError: If current user lacks permission
        """
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE users SET is_active = 1 WHERE user_id = ?",
                (user_id,),
            )
            if cursor.rowcount > 0:
                logger.info(f"User activated: {user_id}")
                return True
        return False

    @require_permission(Permission.MANAGE_USERS)
    def reset_user_password(self, user_id: str, new_password: str) -> bool:
        """
        Reset a user's password (admin function).

        Args:
            user_id: User's ID
            new_password: New password to set

        Returns:
            True if successful

        Raises:
            PermissionError: If current user lacks permission
        """
        return self.auth_service.reset_password(user_id, new_password)

    def count_users(self) -> int:
        """
        Count all users.

        Returns:
            Total user count
        """
        return self.db.count_users()

    def count_admins(self) -> int:
        """
        Count all admin users.

        Returns:
            Admin count
        """
        row = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM users WHERE role = ?",
            (UserRole.ADMIN.value,),
        )
        return row["count"] if row else 0

    def count_active_admins(self) -> int:
        """
        Count active admin users.

        Returns:
            Active admin count
        """
        row = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM users WHERE role = ? AND is_active = 1",
            (UserRole.ADMIN.value,),
        )
        return row["count"] if row else 0

    def get_users_by_role(self, role: str) -> List[User]:
        """
        Get all users with a specific role.

        Args:
            role: Role to filter by

        Returns:
            List of User objects
        """
        rows = self.db.fetch_all(
            "SELECT * FROM users WHERE role = ? AND is_active = 1 ORDER BY username",
            (role,),
        )
        return [User.from_row(row) for row in rows]
