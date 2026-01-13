"""
PolicyHub Session Manager

Manages the current user session for the application.
Uses singleton pattern to provide global access to session state.
"""

from dataclasses import dataclass
from typing import Optional

from app.constants import UserRole


@dataclass
class UserSession:
    """
    Represents the current logged-in user's session.

    This is a lightweight object that holds essential user info
    for the current session. It does not contain sensitive data
    like password hashes.
    """

    user_id: str
    username: str
    full_name: str
    role: str
    force_password_change: bool = False

    def can_edit(self) -> bool:
        """
        Check if the user can edit documents.

        Returns:
            True if user is ADMIN or EDITOR
        """
        return self.role in (UserRole.ADMIN.value, UserRole.EDITOR.value)

    def is_admin(self) -> bool:
        """
        Check if the user is an administrator.

        Returns:
            True if user is ADMIN
        """
        return self.role == UserRole.ADMIN.value

    def is_editor(self) -> bool:
        """
        Check if the user is an editor.

        Returns:
            True if user is EDITOR
        """
        return self.role == UserRole.EDITOR.value

    def is_viewer(self) -> bool:
        """
        Check if the user is a viewer.

        Returns:
            True if user is VIEWER
        """
        return self.role == UserRole.VIEWER.value

    @property
    def role_display(self) -> str:
        """Get the display name for the user's role."""
        try:
            return UserRole(self.role).display_name
        except ValueError:
            return self.role


class SessionManager:
    """
    Manages the current user session.

    Uses singleton pattern to provide global access to the session.
    Only one user can be logged in at a time per application instance.
    """

    _instance: Optional["SessionManager"] = None
    _session: Optional[UserSession] = None

    def __new__(cls) -> "SessionManager":
        """Singleton pattern - only one SessionManager instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "SessionManager":
        """
        Get the singleton SessionManager instance.

        Returns:
            SessionManager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (mainly for testing)."""
        cls._instance = None
        cls._session = None

    def login(
        self,
        user_id: str,
        username: str,
        full_name: str,
        role: str,
        force_password_change: bool = False,
    ) -> UserSession:
        """
        Create a new session for a user.

        Args:
            user_id: User's unique ID
            username: User's username
            full_name: User's display name
            role: User's role (ADMIN, EDITOR, VIEWER)
            force_password_change: Whether user must change password

        Returns:
            The created UserSession
        """
        self._session = UserSession(
            user_id=user_id,
            username=username,
            full_name=full_name,
            role=role,
            force_password_change=force_password_change,
        )
        return self._session

    def logout(self) -> None:
        """Clear the current session."""
        self._session = None

    @property
    def current_user(self) -> Optional[UserSession]:
        """
        Get the current logged-in user.

        Returns:
            UserSession if logged in, None otherwise
        """
        return self._session

    @property
    def is_authenticated(self) -> bool:
        """
        Check if a user is currently logged in.

        Returns:
            True if a session exists
        """
        return self._session is not None

    @property
    def user_id(self) -> Optional[str]:
        """
        Get the current user's ID.

        Returns:
            User ID if logged in, None otherwise
        """
        return self._session.user_id if self._session else None

    @property
    def username(self) -> Optional[str]:
        """
        Get the current user's username.

        Returns:
            Username if logged in, None otherwise
        """
        return self._session.username if self._session else None

    @property
    def full_name(self) -> Optional[str]:
        """
        Get the current user's full name.

        Returns:
            Full name if logged in, None otherwise
        """
        return self._session.full_name if self._session else None

    @property
    def role(self) -> Optional[str]:
        """
        Get the current user's role.

        Returns:
            Role if logged in, None otherwise
        """
        return self._session.role if self._session else None

    def can_edit(self) -> bool:
        """
        Check if the current user can edit documents.

        Returns:
            True if user is ADMIN or EDITOR, False otherwise
        """
        if self._session is None:
            return False
        return self._session.can_edit()

    def is_admin(self) -> bool:
        """
        Check if the current user is an administrator.

        Returns:
            True if user is ADMIN, False otherwise
        """
        if self._session is None:
            return False
        return self._session.is_admin()

    def require_authenticated(self) -> UserSession:
        """
        Get the current session, raising an error if not authenticated.

        Returns:
            Current UserSession

        Raises:
            RuntimeError: If no user is logged in
        """
        if self._session is None:
            raise RuntimeError("No user is logged in")
        return self._session

    def require_admin(self) -> UserSession:
        """
        Get the current session, raising an error if not an admin.

        Returns:
            Current UserSession

        Raises:
            RuntimeError: If no user is logged in or user is not admin
        """
        session = self.require_authenticated()
        if not session.is_admin():
            raise RuntimeError("Admin access required")
        return session

    def require_editor(self) -> UserSession:
        """
        Get the current session, raising an error if user cannot edit.

        Returns:
            Current UserSession

        Raises:
            RuntimeError: If no user is logged in or user cannot edit
        """
        session = self.require_authenticated()
        if not session.can_edit():
            raise RuntimeError("Editor access required")
        return session
