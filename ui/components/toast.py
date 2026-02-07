"""
Toast Notification Component

Brief auto-dismissing notifications positioned at bottom-right.
"""

from typing import Optional

from PySide6.QtCore import QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from app.theme import COLORS, SPACING, TYPOGRAPHY


class Toast(QFrame):
    """
    A toast notification component that auto-dismisses.

    Usage:
        Toast.show_success(parent, "Document saved successfully!")
        Toast.show_error(parent, "Failed to save document.")
        Toast.show_info(parent, "3 documents selected.")
    """

    # Toast variants with their colors
    VARIANTS = {
        "success": {
            "bg": "#DCFCE7",
            "text": "#15803D",
            "icon": "✓",
        },
        "error": {
            "bg": "#FEE2E2",
            "text": "#B91C1C",
            "icon": "✕",
        },
        "info": {
            "bg": "#E0F2FE",
            "text": "#0369A1",
            "icon": "ℹ",
        },
        "warning": {
            "bg": "#FEF3C7",
            "text": "#B45309",
            "icon": "⚠",
        },
    }

    # Active toasts tracking for stacking
    _active_toasts: list["Toast"] = []

    def __init__(
        self,
        parent: QWidget,
        message: str,
        variant: str = "info",
        duration: int = 3000,
    ):
        """
        Initialize a toast notification.

        Args:
            parent: Parent widget (used for positioning)
            message: Message to display
            variant: 'success', 'error', 'info', or 'warning'
            duration: Auto-dismiss time in milliseconds
        """
        # Get the top-level window for proper positioning
        top_level = parent
        while top_level.parent():
            top_level = top_level.parent()

        super().__init__(top_level)

        self._message = message
        self._variant = variant
        self._duration = duration
        self._top_level = top_level

        self.setProperty("toast", True)
        self.setProperty("toastVariant", variant)
        self._build_ui()
        self._setup_animation()

    def _build_ui(self) -> None:
        """Build the toast UI."""
        colors = self.VARIANTS.get(self._variant, self.VARIANTS["info"])

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['bg']};
                border-radius: 8px;
                border: 1px solid {colors['text']}20;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Icon
        icon_label = QLabel(colors["icon"])
        icon_label.setStyleSheet(f"""
            color: {colors['text']};
            font-size: 16px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(icon_label)

        # Message
        message_label = QLabel(self._message)
        message_label.setFont(TYPOGRAPHY.body)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            color: {colors['text']};
            background: transparent;
        """)
        layout.addWidget(message_label, 1)

        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {colors['text']};
                border: none;
                font-size: 18px;
                font-weight: bold;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: {colors['text']}20;
                border-radius: 10px;
            }}
        """)
        close_btn.clicked.connect(self._dismiss)
        layout.addWidget(close_btn)

        # Set size
        self.setMinimumWidth(300)
        self.setMaximumWidth(450)
        self.adjustSize()

    def _setup_animation(self) -> None:
        """Setup fade animation."""
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(0)

    def _position_toast(self) -> None:
        """Position the toast at bottom-right of parent."""
        if not self._top_level:
            return

        parent_rect = self._top_level.rect()
        margin = 20

        # Calculate vertical position based on active toasts
        y_offset = margin
        for toast in Toast._active_toasts:
            if toast is not self and toast.isVisible():
                y_offset += toast.height() + 10

        x = parent_rect.width() - self.width() - margin
        y = parent_rect.height() - self.height() - y_offset

        self.move(x, y)

    def show(self) -> None:
        """Show the toast with fade-in animation."""
        Toast._active_toasts.append(self)
        self._position_toast()
        super().show()
        self.raise_()

        # Fade in
        self._fade_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_animation.setDuration(200)
        self._fade_animation.setStartValue(0)
        self._fade_animation.setEndValue(1)
        self._fade_animation.start()

        # Auto dismiss timer
        QTimer.singleShot(self._duration, self._dismiss)

    def _dismiss(self) -> None:
        """Dismiss the toast with fade-out animation."""
        if self in Toast._active_toasts:
            Toast._active_toasts.remove(self)

        # Fade out
        self._fade_out = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_out.setDuration(200)
        self._fade_out.setStartValue(1)
        self._fade_out.setEndValue(0)
        self._fade_out.finished.connect(self._on_fade_out_finished)
        self._fade_out.start()

    def _on_fade_out_finished(self) -> None:
        """Clean up after fade out."""
        self.hide()
        self.deleteLater()
        # Reposition remaining toasts
        for toast in Toast._active_toasts:
            toast._position_toast()

    @staticmethod
    def show_success(
        parent: QWidget,
        message: str,
        duration: int = 3000,
    ) -> "Toast":
        """
        Show a success toast notification.

        Args:
            parent: Parent widget
            message: Success message
            duration: Auto-dismiss time in ms

        Returns:
            The Toast instance
        """
        toast = Toast(parent, message, "success", duration)
        toast.show()
        return toast

    @staticmethod
    def show_error(
        parent: QWidget,
        message: str,
        duration: int = 4000,
    ) -> "Toast":
        """
        Show an error toast notification.

        Args:
            parent: Parent widget
            message: Error message
            duration: Auto-dismiss time in ms

        Returns:
            The Toast instance
        """
        toast = Toast(parent, message, "error", duration)
        toast.show()
        return toast

    @staticmethod
    def show_info(
        parent: QWidget,
        message: str,
        duration: int = 3000,
    ) -> "Toast":
        """
        Show an info toast notification.

        Args:
            parent: Parent widget
            message: Info message
            duration: Auto-dismiss time in ms

        Returns:
            The Toast instance
        """
        toast = Toast(parent, message, "info", duration)
        toast.show()
        return toast

    @staticmethod
    def show_warning(
        parent: QWidget,
        message: str,
        duration: int = 3500,
    ) -> "Toast":
        """
        Show a warning toast notification.

        Args:
            parent: Parent widget
            message: Warning message
            duration: Auto-dismiss time in ms

        Returns:
            The Toast instance
        """
        toast = Toast(parent, message, "warning", duration)
        toast.show()
        return toast
