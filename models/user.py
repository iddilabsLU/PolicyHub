"""
PolicyHub User Model

Represents a user in the system with role-based access control.
"""

from dataclasses import dataclass
from sqlite3 import Row
from typing import Optional

from app.constants import UserRole


@dataclass
class User:
    """
    Represents a user account.

    Attributes:
        user_id: Unique identifier (UUID)
        username: Login username (unique)
        password_hash: Bcrypt hashed password
        full_name: Display name
        email: Email address (optional)
        role: User role (ADMIN, EDITOR, VIEWER)
        is_active: Whether the account is active
        created_at: Account creation timestamp (ISO 8601)
        created_by: User ID who created this account (None for first admin)
        last_login: Last login timestamp (ISO 8601, optional)
    """

    user_id: str
    username: str
    password_hash: str
    full_name: str
    role: str
    is_active: bool
    created_at: str
    email: Optional[str] = None
    created_by: Optional[str] = None
    last_login: Optional[str] = None
    force_password_change: bool = False

    def can_edit(self) -> bool:
        """Check if user can edit documents (Admin or Editor)."""
        return self.role in (UserRole.ADMIN.value, UserRole.EDITOR.value)

    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN.value

    def is_editor(self) -> bool:
        """Check if user is an editor."""
        return self.role == UserRole.EDITOR.value

    def is_viewer(self) -> bool:
        """Check if user is a viewer."""
        return self.role == UserRole.VIEWER.value

    @property
    def role_display(self) -> str:
        """Get the display name for the user's role."""
        try:
            return UserRole(self.role).display_name
        except ValueError:
            return self.role

    @classmethod
    def from_row(cls, row: Row) -> "User":
        """
        Create a User from a SQLite row.

        Args:
            row: SQLite Row object with user data

        Returns:
            User instance
        """
        return cls(
            user_id=row["user_id"],
            username=row["username"],
            password_hash=row["password_hash"],
            full_name=row["full_name"],
            email=row["email"],
            role=row["role"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            created_by=row["created_by"],
            last_login=row["last_login"],
            force_password_change=bool(row["force_password_change"]) if "force_password_change" in row.keys() else False,
        )

    def to_dict(self) -> dict:
        """
        Convert to dictionary (excluding password_hash for safety).

        Returns:
            Dictionary representation of the user
        """
        return {
            "user_id": self.user_id,
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "last_login": self.last_login,
            "force_password_change": self.force_password_change,
        }


@dataclass
class UserCreate:
    """Data required to create a new user."""

    username: str
    password: str  # Plain text, will be hashed
    full_name: str
    role: str
    email: Optional[str] = None


@dataclass
class UserUpdate:
    """Data for updating an existing user."""

    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
