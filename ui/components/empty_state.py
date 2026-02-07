"""
EmptyState Component

Displays a friendly message when tables/lists are empty.
"""

from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button


class EmptyState(QFrame):
    """
    A component that displays a friendly message when tables/lists are empty.

    Usage:
        empty = EmptyState(
            parent=self,
            icon="🔍",
            title="No documents found",
            message="Try adjusting your filters or add a new document.",
            action_text="Add Document",
            action_callback=self._on_add_document
        )
    """

    # Common icons for empty states
    ICON_SEARCH = "🔍"
    ICON_DOCUMENT = "📄"
    ICON_USER = "👤"
    ICON_FILTER = "⚙"
    ICON_FOLDER = "📁"
    ICON_DATABASE = "🗄️"

    def __init__(
        self,
        parent=None,
        icon: str = "📄",
        title: str = "No items found",
        message: str = "",
        action_text: Optional[str] = None,
        action_callback: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the EmptyState component.

        Args:
            parent: Parent widget
            icon: Unicode emoji icon to display
            title: Main title text
            message: Secondary description text
            action_text: Optional button text for action
            action_callback: Optional callback for action button
        """
        super().__init__(parent)

        self._icon = icon
        self._title = title
        self._message = message
        self._action_text = action_text
        self._action_callback = action_callback

        self.setProperty("emptyState", True)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the component UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING.CARD_PADDING * 2,
            SPACING.CARD_PADDING * 3,
            SPACING.CARD_PADDING * 2,
            SPACING.CARD_PADDING * 3,
        )
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        self.icon_label = QLabel(self._icon)
        self.icon_label.setProperty("emptyStateIcon", True)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet(f"""
            font-size: 48px;
            color: {COLORS.TEXT_MUTED};
            background: transparent;
        """)
        layout.addWidget(self.icon_label)

        # Title
        self.title_label = QLabel(self._title)
        self.title_label.setFont(TYPOGRAPHY.section_heading)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(f"""
            color: {COLORS.TEXT_PRIMARY};
            background: transparent;
        """)
        layout.addWidget(self.title_label)

        # Message
        if self._message:
            self.message_label = QLabel(self._message)
            self.message_label.setFont(TYPOGRAPHY.body)
            self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.message_label.setWordWrap(True)
            self.message_label.setMaximumWidth(400)
            self.message_label.setStyleSheet(f"""
                color: {COLORS.TEXT_SECONDARY};
                background: transparent;
            """)
            layout.addWidget(self.message_label)

        # Action button (optional)
        if self._action_text and self._action_callback:
            layout.addSpacing(8)

            btn_container = QFrame()
            btn_container.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.action_btn = QPushButton(self._action_text)
            self.action_btn.setFixedHeight(SPACING.BUTTON_HEIGHT)
            self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            style_button(self.action_btn, "primary")
            self.action_btn.clicked.connect(self._action_callback)
            btn_layout.addWidget(self.action_btn)

            layout.addWidget(btn_container)

    def set_icon(self, icon: str) -> None:
        """Update the icon."""
        self._icon = icon
        self.icon_label.setText(icon)

    def set_title(self, title: str) -> None:
        """Update the title."""
        self._title = title
        self.title_label.setText(title)

    def set_message(self, message: str) -> None:
        """Update the message."""
        self._message = message
        if hasattr(self, "message_label"):
            self.message_label.setText(message)
