"""
PolicyHub User Table Model (PySide6)

QAbstractTableModel implementation for the users management table.
"""

from typing import Any, List, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QBrush, QColor

from app.theme import COLORS
from models.user import User
from utils.dates import format_datetime


class UserTableModel(QAbstractTableModel):
    """
    Table model for displaying users in a QTableView.

    Columns:
    - Username
    - Full Name
    - Email
    - Role
    - Status
    - Last Login
    """

    COLUMNS = [
        ("username", "Username"),
        ("full_name", "Full Name"),
        ("email", "Email"),
        ("role", "Role"),
        ("is_active", "Status"),
        ("last_login", "Last Login"),
    ]

    def __init__(self, parent=None):
        """Initialize the user table model."""
        super().__init__(parent)
        self._users: List[User] = []

    def set_users(self, users: List[User]) -> None:
        """
        Set the users to display.

        Args:
            users: List of User objects.
        """
        self.beginResetModel()
        self._users = users
        self.endResetModel()

    def get_user(self, row: int) -> Optional[User]:
        """
        Get a user by row index.

        Args:
            row: Row index.

        Returns:
            User at the row, or None if invalid.
        """
        if 0 <= row < len(self._users):
            return self._users[row]
        return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user by their ID.

        Args:
            user_id: User ID.

        Returns:
            User with the ID, or None if not found.
        """
        for user in self._users:
            if user.user_id == user_id:
                return user
        return None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows."""
        if parent.isValid():
            return 0
        return len(self._users)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns."""
        if parent.isValid():
            return 0
        return len(self.COLUMNS)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        """Return header data for the table."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self.COLUMNS):
                return self.COLUMNS[section][1]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return data for a cell."""
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row < 0 or row >= len(self._users):
            return None

        user = self._users[row]
        col_key = self.COLUMNS[col][0]

        if role == Qt.ItemDataRole.DisplayRole:
            return self._get_display_value(user, col_key)

        elif role == Qt.ItemDataRole.ForegroundRole:
            return self._get_cell_foreground(user, col_key)

        elif role == Qt.ItemDataRole.UserRole:
            # Return the user object
            return user

        return None

    def _get_display_value(self, user: User, col_key: str) -> str:
        """Get the display value for a column."""
        if col_key == "username":
            return user.username
        elif col_key == "full_name":
            return user.full_name
        elif col_key == "email":
            return user.email or ""
        elif col_key == "role":
            return user.role_display
        elif col_key == "is_active":
            return "Active" if user.is_active else "Inactive"
        elif col_key == "last_login":
            return format_datetime(user.last_login) if user.last_login else "Never"
        return ""

    def _get_cell_foreground(self, user: User, col_key: str) -> Optional[QBrush]:
        """Get the foreground color for a cell."""
        if col_key == "is_active":
            if user.is_active:
                return QBrush(QColor(COLORS.SUCCESS))
            else:
                return QBrush(QColor(COLORS.DANGER))

        elif col_key == "role":
            if user.role == "ADMIN":
                return QBrush(QColor(COLORS.PRIMARY))
            elif user.role == "EDITOR":
                return QBrush(QColor(COLORS.ACCENT_PROCEDURE))
            elif user.role == "EDITOR_RESTRICTED":
                return QBrush(QColor(COLORS.CAUTION))

        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        """Sort the table by a column."""
        if column < 0 or column >= len(self.COLUMNS):
            return

        col_key = self.COLUMNS[column][0]
        reverse = order == Qt.SortOrder.DescendingOrder

        self.beginResetModel()

        def get_sort_key(user: User) -> Any:
            if col_key == "username":
                return user.username.lower()
            elif col_key == "full_name":
                return user.full_name.lower()
            elif col_key == "email":
                return (user.email or "").lower()
            elif col_key == "role":
                # Sort by role hierarchy: ADMIN first
                role_order = {"ADMIN": 0, "EDITOR": 1, "EDITOR_RESTRICTED": 2, "VIEWER": 3}
                return role_order.get(user.role, 4)
            elif col_key == "is_active":
                return 0 if user.is_active else 1
            elif col_key == "last_login":
                return user.last_login or ""
            return ""

        self._users.sort(key=get_sort_key, reverse=reverse)
        self.endResetModel()
