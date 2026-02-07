"""
PolicyHub Status Delegate (PySide6)

Custom cell rendering delegate for status columns in tables.
"""

from typing import Optional

from PySide6.QtCore import QModelIndex, QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
)

from app.constants import DocumentStatus, ReviewStatus
from app.theme import COLORS, TYPOGRAPHY


class StatusBadgeDelegate(QStyledItemDelegate):
    """
    Delegate that renders status values as colored pill badges.

    Usage:
        delegate = StatusBadgeDelegate(status_type="document")
        table_view.setItemDelegateForColumn(status_column, delegate)
    """

    def __init__(self, status_type: str = "document", parent: Optional[QWidget] = None):
        """
        Initialize the status badge delegate.

        Args:
            status_type: Type of status ("document" or "review")
            parent: Parent widget
        """
        super().__init__(parent)
        self._status_type = status_type

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        """Paint the status badge."""
        # Get the status text
        status_text = index.data(Qt.ItemDataRole.DisplayRole)
        if not status_text:
            return

        # Initialize painter
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Handle selection background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        # Get colors for this status
        bg_color, fg_color = self._get_status_colors(status_text)

        # Calculate badge dimensions
        font = TYPOGRAPHY.small
        painter.setFont(font)
        text_width = painter.fontMetrics().horizontalAdvance(status_text)
        badge_width = text_width + 16  # Padding
        badge_height = 20

        # Center the badge in the cell
        x = option.rect.x() + (option.rect.width() - badge_width) // 2
        y = option.rect.y() + (option.rect.height() - badge_height) // 2

        badge_rect = QRect(x, y, badge_width, badge_height)

        # Draw badge background
        painter.setBrush(QColor(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(badge_rect, 10, 10)

        # Draw text
        painter.setPen(QPen(QColor(fg_color)))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, status_text)

        painter.restore()

    def sizeHint(
        self, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QSize:
        """Return the preferred size for the cell."""
        return QSize(100, 32)

    def _get_status_colors(self, status_text: str) -> tuple[str, str]:
        """
        Get background and foreground colors for a status.

        Returns:
            Tuple of (background_color, foreground_color)
        """
        # Document statuses
        document_colors = {
            DocumentStatus.ACTIVE.display_name: (COLORS.SUCCESS_BG, COLORS.SUCCESS),
            DocumentStatus.DRAFT.display_name: (COLORS.MUTED, COLORS.TEXT_SECONDARY),
            DocumentStatus.UNDER_REVIEW.display_name: (COLORS.CAUTION_BG, COLORS.CAUTION),
            DocumentStatus.ARCHIVED.display_name: (COLORS.MUTED, COLORS.TEXT_MUTED),
        }

        # Review statuses
        review_colors = {
            ReviewStatus.OVERDUE.display_name: (COLORS.DANGER_BG, COLORS.DANGER),
            ReviewStatus.DUE_SOON.display_name: (COLORS.WARNING_BG, COLORS.WARNING),
            ReviewStatus.UPCOMING.display_name: (COLORS.CAUTION_BG, COLORS.CAUTION),
            ReviewStatus.ON_TRACK.display_name: (COLORS.SUCCESS_BG, COLORS.SUCCESS),
        }

        # Try document statuses first
        if status_text in document_colors:
            return document_colors[status_text]

        # Try review statuses
        if status_text in review_colors:
            return review_colors[status_text]

        # Default
        return (COLORS.MUTED, COLORS.TEXT_SECONDARY)


class ActiveStatusDelegate(QStyledItemDelegate):
    """
    Delegate that renders active/inactive status as colored badges.

    Usage:
        delegate = ActiveStatusDelegate()
        table_view.setItemDelegateForColumn(status_column, delegate)
    """

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        """Paint the active status badge."""
        # Get the status text
        status_text = index.data(Qt.ItemDataRole.DisplayRole)
        if not status_text:
            return

        # Initialize painter
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Handle selection background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        # Get colors based on active/inactive
        if status_text == "Active":
            bg_color = COLORS.SUCCESS_BG
            fg_color = COLORS.SUCCESS
        else:
            bg_color = COLORS.DANGER_BG
            fg_color = COLORS.DANGER

        # Calculate badge dimensions
        font = TYPOGRAPHY.small
        painter.setFont(font)
        text_width = painter.fontMetrics().horizontalAdvance(status_text)
        badge_width = text_width + 16
        badge_height = 20

        # Center the badge in the cell
        x = option.rect.x() + (option.rect.width() - badge_width) // 2
        y = option.rect.y() + (option.rect.height() - badge_height) // 2

        badge_rect = QRect(x, y, badge_width, badge_height)

        # Draw badge background
        painter.setBrush(QColor(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(badge_rect, 10, 10)

        # Draw text
        painter.setPen(QPen(QColor(fg_color)))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, status_text)

        painter.restore()

    def sizeHint(
        self, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QSize:
        """Return the preferred size for the cell."""
        return QSize(80, 32)


class RoleBadgeDelegate(QStyledItemDelegate):
    """
    Delegate that renders user roles as colored badges.

    Usage:
        delegate = RoleBadgeDelegate()
        table_view.setItemDelegateForColumn(role_column, delegate)
    """

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        """Paint the role badge."""
        # Get the role text
        role_text = index.data(Qt.ItemDataRole.DisplayRole)
        if not role_text:
            return

        # Initialize painter
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Handle selection background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        # Get colors based on role
        role_colors = {
            "Administrator": (COLORS.PRIMARY, COLORS.PRIMARY_FOREGROUND),
            "Editor": (COLORS.ACCENT_PROCEDURE, "#FFFFFF"),
            "Editor (Restricted)": (COLORS.CAUTION_BG, COLORS.CAUTION),
            "Viewer": (COLORS.MUTED, COLORS.TEXT_SECONDARY),
        }
        bg_color, fg_color = role_colors.get(role_text, (COLORS.MUTED, COLORS.TEXT_SECONDARY))

        # Calculate badge dimensions
        font = TYPOGRAPHY.small
        painter.setFont(font)
        text_width = painter.fontMetrics().horizontalAdvance(role_text)
        badge_width = text_width + 16
        badge_height = 20

        # Center the badge in the cell
        x = option.rect.x() + (option.rect.width() - badge_width) // 2
        y = option.rect.y() + (option.rect.height() - badge_height) // 2

        badge_rect = QRect(x, y, badge_width, badge_height)

        # Draw badge background
        painter.setBrush(QColor(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(badge_rect, 10, 10)

        # Draw text
        painter.setPen(QPen(QColor(fg_color)))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, role_text)

        painter.restore()

    def sizeHint(
        self, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QSize:
        """Return the preferred size for the cell."""
        return QSize(120, 32)
