"""
PolicyHub Stat Card Component (PySide6)

A card displaying a statistic with value and label.
"""

from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

from app.theme import COLORS, SPACING, TYPOGRAPHY


class StatCard(QFrame):
    """
    A card displaying a statistic with value, label, and optional accent.

    Usage:
        card = StatCard(
            parent,
            value="42",
            label="Active Documents",
            accent_color=COLORS.SUCCESS,
        )

        # With click handler
        card = StatCard(
            parent,
            value="5",
            label="Overdue",
            accent_color=COLORS.DANGER,
            on_click=lambda: navigate_to_overdue(),
        )
    """

    clicked = Signal()

    def __init__(
        self,
        parent=None,
        value: str = "0",
        label: str = "",
        accent_color: Optional[str] = None,
        on_click: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the stat card.

        Args:
            parent: Parent widget
            value: The main value to display (e.g., "42")
            label: Description label (e.g., "Active Documents")
            accent_color: Color for the top accent border (defaults to primary)
            on_click: Optional callback when card is clicked
        """
        super().__init__(parent)

        self._on_click = on_click
        self._accent_color = accent_color or COLORS.PRIMARY
        self._default_border = COLORS.INPUT_BORDER

        # Fixed height
        self.setFixedHeight(60)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Build UI
        self._build_ui(value, label)

        # Apply base styling
        self._apply_styling()

        # Make clickable if handler provided
        if on_click:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.clicked.connect(on_click)

    def _build_ui(self, value: str, label: str) -> None:
        """Build the card UI with top accent border."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top accent border
        self.accent = QFrame()
        self.accent.setFixedHeight(3)
        self.accent.setStyleSheet(f"background-color: {self._accent_color};")
        main_layout.addWidget(self.accent)

        # Content container - horizontal layout
        content = QFrame()
        content.setStyleSheet("background: transparent;")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING - 4,
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING - 4
        )
        content_layout.setSpacing(10)

        # Value (number) on the left
        self.value_label = QLabel(value)
        self.value_label.setFont(TYPOGRAPHY.get_font(22, TYPOGRAPHY.WEIGHT_BOLD))
        self.value_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        content_layout.addWidget(self.value_label)

        # Label on the right
        self.label_widget = QLabel(label)
        self.label_widget.setFont(TYPOGRAPHY.body)
        self.label_widget.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        content_layout.addWidget(self.label_widget)

        # Stretch to push content to left
        content_layout.addStretch()

        main_layout.addWidget(content)

    def _apply_styling(self) -> None:
        """Apply card styling."""
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {COLORS.CARD};
                border: none;
                border-radius: {SPACING.CORNER_RADIUS_LARGE}px;
            }}
        """)

    def enterEvent(self, event) -> None:
        """Handle mouse enter (hover)."""
        if self._on_click:
            self.setStyleSheet(f"""
                StatCard {{
                    background-color: {COLORS.MUTED};
                    border: none;
                    border-radius: {SPACING.CORNER_RADIUS_LARGE}px;
                }}
            """)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Handle mouse leave."""
        self._apply_styling()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse click."""
        if event.button() == Qt.MouseButton.LeftButton and self._on_click:
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_value(self, value: str) -> None:
        """
        Update the displayed value.

        Args:
            value: New value to display
        """
        self.value_label.setText(value)

    def set_label(self, label: str) -> None:
        """
        Update the label text.

        Args:
            label: New label text
        """
        self.label_widget.setText(label)

    def set_accent_color(self, color: str) -> None:
        """
        Update the accent color.

        Args:
            color: New accent color
        """
        self._accent_color = color
        self.accent.setStyleSheet(f"background-color: {color};")
