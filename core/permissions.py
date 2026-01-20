"""
PolicyHub Permission System

Defines the role-based access control (RBAC) system.
Based on PRD Section 4.2: Permission Matrix.
"""

from enum import Enum, auto
from functools import wraps
from typing import Callable, Set

from app.constants import UserRole
from core.session import SessionManager


class Permission(Enum):
    """
    Available permissions in the system.

    Permissions are grouped by functionality area.
    """

    # View permissions (all roles)
    VIEW_REGISTER = auto()
    VIEW_DOCUMENT = auto()
    DOWNLOAD_ATTACHMENT = auto()
    EXPORT_REGISTER = auto()
    GENERATE_REPORTS = auto()

    # Edit permissions (Admin, Editor)
    ADD_DOCUMENT = auto()
    EDIT_DOCUMENT = auto()
    UPLOAD_ATTACHMENT = auto()
    DELETE_ATTACHMENT = auto()
    MARK_REVIEWED = auto()
    MANAGE_LINKS = auto()

    # Admin-only permissions
    DELETE_DOCUMENT = auto()
    MANAGE_USERS = auto()
    CHANGE_SETTINGS = auto()
    MANAGE_CATEGORIES = auto()
    VIEW_AUDIT_LOG = auto()


# Permission matrix: maps roles to their permissions
ROLE_PERMISSIONS: dict[str, Set[Permission]] = {
    UserRole.ADMIN.value: {
        # All permissions
        Permission.VIEW_REGISTER,
        Permission.VIEW_DOCUMENT,
        Permission.DOWNLOAD_ATTACHMENT,
        Permission.EXPORT_REGISTER,
        Permission.GENERATE_REPORTS,
        Permission.ADD_DOCUMENT,
        Permission.EDIT_DOCUMENT,
        Permission.UPLOAD_ATTACHMENT,
        Permission.DELETE_ATTACHMENT,
        Permission.MARK_REVIEWED,
        Permission.MANAGE_LINKS,
        Permission.DELETE_DOCUMENT,
        Permission.MANAGE_USERS,
        Permission.CHANGE_SETTINGS,
        Permission.MANAGE_CATEGORIES,
        Permission.VIEW_AUDIT_LOG,
    },
    UserRole.EDITOR.value: {
        # View + Edit permissions
        Permission.VIEW_REGISTER,
        Permission.VIEW_DOCUMENT,
        Permission.DOWNLOAD_ATTACHMENT,
        Permission.EXPORT_REGISTER,
        Permission.GENERATE_REPORTS,
        Permission.ADD_DOCUMENT,
        Permission.EDIT_DOCUMENT,
        Permission.UPLOAD_ATTACHMENT,
        Permission.DELETE_ATTACHMENT,
        Permission.MARK_REVIEWED,
        Permission.MANAGE_LINKS,
    },
    UserRole.EDITOR_RESTRICTED.value: {
        # Same as Editor - restrictions enforced at document level
        Permission.VIEW_REGISTER,
        Permission.VIEW_DOCUMENT,
        Permission.DOWNLOAD_ATTACHMENT,
        Permission.EXPORT_REGISTER,
        Permission.GENERATE_REPORTS,
        Permission.ADD_DOCUMENT,
        Permission.EDIT_DOCUMENT,
        Permission.UPLOAD_ATTACHMENT,
        Permission.DELETE_ATTACHMENT,
        Permission.MARK_REVIEWED,
        Permission.MANAGE_LINKS,
    },
    UserRole.VIEWER.value: {
        # View-only permissions
        Permission.VIEW_REGISTER,
        Permission.VIEW_DOCUMENT,
        Permission.DOWNLOAD_ATTACHMENT,
        Permission.EXPORT_REGISTER,
        Permission.GENERATE_REPORTS,
    },
}


def has_permission(role: str, permission: Permission) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        role: User role (ADMIN, EDITOR, VIEWER)
        permission: Permission to check

    Returns:
        True if the role has the permission
    """
    role_perms = ROLE_PERMISSIONS.get(role, set())
    return permission in role_perms


def current_user_has_permission(permission: Permission) -> bool:
    """
    Check if the current logged-in user has a specific permission.

    Args:
        permission: Permission to check

    Returns:
        True if the current user has the permission, False if not logged in
    """
    session = SessionManager.get_instance()
    if not session.is_authenticated:
        return False

    return has_permission(session.role, permission)


def require_permission(permission: Permission) -> Callable:
    """
    Decorator to require a permission for a function.

    Usage:
        @require_permission(Permission.EDIT_DOCUMENT)
        def edit_document(doc_id: str, ...):
            ...

    Args:
        permission: Required permission

    Returns:
        Decorator function

    Raises:
        PermissionError: If the current user doesn't have the permission
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            session = SessionManager.get_instance()

            if not session.is_authenticated:
                raise PermissionError("Authentication required")

            if not has_permission(session.role, permission):
                raise PermissionError(
                    f"Permission denied: {permission.name} required"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_permissions_for_role(role: str) -> Set[Permission]:
    """
    Get all permissions for a role.

    Args:
        role: User role

    Returns:
        Set of permissions for the role
    """
    return ROLE_PERMISSIONS.get(role, set()).copy()


def get_missing_permissions(role: str, required: Set[Permission]) -> Set[Permission]:
    """
    Get permissions that a role is missing from a required set.

    Args:
        role: User role
        required: Set of required permissions

    Returns:
        Set of permissions the role doesn't have
    """
    role_perms = get_permissions_for_role(role)
    return required - role_perms


class PermissionChecker:
    """
    Helper class for checking multiple permissions.

    Usage:
        checker = PermissionChecker()
        if checker.can_edit():
            # Show edit button
        if checker.is_admin():
            # Show admin menu
    """

    def __init__(self):
        """Initialize the permission checker."""
        self._session = SessionManager.get_instance()

    @property
    def is_authenticated(self) -> bool:
        """Check if a user is logged in."""
        return self._session.is_authenticated

    @property
    def role(self) -> str | None:
        """Get the current user's role."""
        return self._session.role

    def has(self, permission: Permission) -> bool:
        """
        Check if the current user has a permission.

        Args:
            permission: Permission to check

        Returns:
            True if user has permission
        """
        if not self.is_authenticated:
            return False
        return has_permission(self.role, permission)

    def can_view(self) -> bool:
        """Check if user can view documents (all authenticated users)."""
        return self.has(Permission.VIEW_DOCUMENT)

    def can_edit(self) -> bool:
        """Check if user can edit documents (Admin, Editor)."""
        return self.has(Permission.EDIT_DOCUMENT)

    def can_delete(self) -> bool:
        """Check if user can delete documents (Admin only)."""
        return self.has(Permission.DELETE_DOCUMENT)

    def can_manage_users(self) -> bool:
        """Check if user can manage users (Admin only)."""
        return self.has(Permission.MANAGE_USERS)

    def can_change_settings(self) -> bool:
        """Check if user can change settings (Admin only)."""
        return self.has(Permission.CHANGE_SETTINGS)

    def can_view_audit_log(self) -> bool:
        """Check if user can view audit log (Admin only)."""
        return self.has(Permission.VIEW_AUDIT_LOG)

    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self._session.is_admin() if self.is_authenticated else False

    def is_editor(self) -> bool:
        """Check if user is an editor (full or restricted)."""
        if not self.is_authenticated:
            return False
        return self.role in (UserRole.EDITOR.value, UserRole.EDITOR_RESTRICTED.value)

    def is_editor_restricted(self) -> bool:
        """Check if user is a restricted editor."""
        if not self.is_authenticated:
            return False
        return self.role == UserRole.EDITOR_RESTRICTED.value

    def is_viewer(self) -> bool:
        """Check if user is a viewer."""
        if not self.is_authenticated:
            return False
        return self.role == UserRole.VIEWER.value
