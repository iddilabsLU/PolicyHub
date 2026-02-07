"""
PolicyHub Base Dialog (PySide6)

Base class for modal dialog windows.
"""

from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QDialog, QVBoxLayout, QWidget

from app.theme import COLORS


class BaseDialog(QDialog):
    """
    Base class for modal dialogs.

    Features:
    - Modal behavior (blocks parent window)
    - Centered positioning on parent
    - Consistent styling
    - Close on Escape key
    - Result storage

    Usage:
        class MyDialog(BaseDialog):
            def __init__(self, parent, **kwargs):
                super().__init__(parent, "My Dialog", width=400, height=300)
                self._build_ui()

            def _build_ui(self):
                layout = QVBoxLayout(self)
                # Build your UI here

            def _on_confirm(self):
                self.result = {"data": "value"}
                super()._on_confirm()

        # Show dialog and get result
        dialog = MyDialog(parent)
        result = dialog.show()
        if result is not None:
            # User confirmed
            pass
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        title: str,
        width: int = 500,
        height: int = 400,
        resizable: bool = False,
    ):
        """
        Initialize the base dialog.

        Args:
            parent: Parent window
            title: Dialog title
            width: Dialog width in pixels
            height: Dialog height in pixels
            resizable: Whether the dialog can be resized
        """
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setModal(True)

        # Get screen dimensions and cap dialog size at 90% of screen
        if parent:
            screen = parent.screen()
        else:
            from PySide6.QtWidgets import QApplication
            screen = QApplication.primaryScreen()

        screen_geometry = screen.availableGeometry()
        max_width = int(screen_geometry.width() * 0.9)
        max_height = int(screen_geometry.height() * 0.85)

        # Ensure dialog fits on screen
        final_width = min(width, max_width)
        final_height = min(height, max_height)

        self.resize(final_width, final_height)

        if not resizable:
            self.setFixedSize(final_width, final_height)

        # Set window flags for proper modal behavior
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        # Apply styling
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS.BACKGROUND}; }}")

        # Center on parent
        self._center_on_parent(parent, final_width, final_height)

        # Result storage
        self.result: Optional[Any] = None
        self._cancelled = False

    def _center_on_parent(
        self, parent: Optional[QWidget], width: int, height: int
    ) -> None:
        """
        Center the dialog on the parent window.

        Args:
            parent: Parent window
            width: Dialog width
            height: Dialog height
        """
        if parent:
            parent_geometry = parent.geometry()
            x = parent_geometry.x() + (parent_geometry.width() - width) // 2
            y = parent_geometry.y() + (parent_geometry.height() - height) // 2

            # Ensure dialog is on screen
            screen = parent.screen()
            screen_geometry = screen.availableGeometry()
            x = max(screen_geometry.x(), min(x, screen_geometry.right() - width))
            y = max(screen_geometry.y(), min(y, screen_geometry.bottom() - height))

            self.move(x, y)
        else:
            # Center on primary screen
            from PySide6.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - width) // 2
            y = (screen_geometry.height() - height) // 2
            self.move(x, y)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape:
            self._on_cancel()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        """Handle window close button."""
        if not self._cancelled and self.result is None:
            self._cancelled = True
        super().closeEvent(event)

    def _on_cancel(self) -> None:
        """Handle cancel/close action."""
        self._cancelled = True
        self.result = None
        self.reject()

    def _on_confirm(self) -> None:
        """
        Handle confirm action.

        Override this method to set self.result before calling super()._on_confirm().
        """
        self.accept()

    def show(self) -> Optional[Any]:
        """
        Show the dialog and wait for it to close.

        Returns:
            The dialog result, or None if cancelled
        """
        self.exec()
        return self.result

    @property
    def was_cancelled(self) -> bool:
        """Check if the dialog was cancelled."""
        return self._cancelled
