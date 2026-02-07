"""
PolicyHub Confirm Dialog (PySide6)

A simple confirmation dialog with Yes/No or custom buttons.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button
from ui.dialogs.base_dialog import BaseDialog


class ConfirmDialog(BaseDialog):
    """
    A confirmation dialog with customizable buttons.

    Usage:
        # Simple confirm
        if ConfirmDialog.ask(parent, "Confirm", "Are you sure?"):
            # User confirmed
            pass

        # Delete confirmation
        if ConfirmDialog.ask(
            parent,
            title="Delete Document",
            message="This will permanently delete the document.",
            confirm_text="Delete",
            confirm_style="danger",
        ):
            # Delete the document
            pass
    """

    def __init__(
        self,
        parent,
        title: str,
        message: str,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        confirm_style: str = "primary",
    ):
        """
        Initialize the confirm dialog.

        Args:
            parent: Parent window
            title: Dialog title
            message: Message to display
            confirm_text: Text for confirm button
            cancel_text: Text for cancel button
            confirm_style: Style for confirm button (primary, danger)
        """
        # Calculate height based on message length
        lines = len(message) // 45 + message.count('\n') + 1
        calculated_height = max(200, 120 + (lines * 22))

        super().__init__(parent, title, width=420, height=calculated_height)

        self._build_ui(message, confirm_text, cancel_text, confirm_style)

    def _build_ui(
        self,
        message: str,
        confirm_text: str,
        cancel_text: str,
        confirm_style: str,
    ) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 30, 20, 20)
        layout.setSpacing(0)

        # Message
        msg_label = QLabel(message)
        msg_label.setFont(TYPOGRAPHY.body)
        msg_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg_label)
        layout.addStretch()

        # Buttons frame
        btn_frame = QWidget()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)

        btn_layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setFixedSize(100, 36)
        cancel_btn.clicked.connect(self._on_cancel)
        style_button(cancel_btn, "secondary")
        btn_layout.addWidget(cancel_btn)

        # Confirm button
        confirm_btn = QPushButton(confirm_text)
        confirm_btn.setFixedSize(100, 36)
        confirm_btn.clicked.connect(self._on_confirm)
        style_button(confirm_btn, confirm_style)
        btn_layout.addWidget(confirm_btn)

        btn_layout.addStretch()

        layout.addWidget(btn_frame)

        # Focus confirm button
        confirm_btn.setFocus()

    def _on_confirm(self) -> None:
        """Handle confirm button click."""
        self.result = True
        self.accept()

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        self.result = False
        self.reject()

    @classmethod
    def ask(
        cls,
        parent,
        title: str,
        message: str,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        confirm_style: str = "primary",
    ) -> bool:
        """
        Show a confirmation dialog and return the result.

        Args:
            parent: Parent window
            title: Dialog title
            message: Message to display
            confirm_text: Text for confirm button
            cancel_text: Text for cancel button
            confirm_style: Style for confirm button

        Returns:
            True if confirmed, False if cancelled
        """
        dialog = cls(
            parent,
            title=title,
            message=message,
            confirm_text=confirm_text,
            cancel_text=cancel_text,
            confirm_style=confirm_style,
        )
        return dialog.show() or False

    @classmethod
    def ask_delete(
        cls,
        parent,
        item_name: str,
        item_type: str = "item",
    ) -> bool:
        """
        Show a delete confirmation dialog.

        Args:
            parent: Parent window
            item_name: Name of the item being deleted
            item_type: Type of item (e.g., "document", "user")

        Returns:
            True if delete confirmed
        """
        return cls.ask(
            parent,
            title=f"Delete {item_type.title()}",
            message=f"Are you sure you want to delete '{item_name}'?\n\nThis action cannot be undone.",
            confirm_text="Delete",
            confirm_style="danger",
        )


class InfoDialog(BaseDialog):
    """
    A simple information dialog with an OK button.

    Usage:
        InfoDialog.show_info(parent, "Success", "Operation completed.")
        InfoDialog.show_error(parent, "Error", "Something went wrong.")
    """

    def __init__(
        self,
        parent,
        title: str,
        message: str,
        button_text: str = "OK",
    ):
        """
        Initialize the info dialog.

        Args:
            parent: Parent window
            title: Dialog title
            message: Message to display
            button_text: Text for the button
        """
        # Calculate height based on message length
        lines = len(message) // 45 + message.count('\n') + 1
        calculated_height = max(180, 100 + (lines * 22))

        super().__init__(parent, title, width=420, height=calculated_height)

        self._build_ui(message, button_text)

    def _build_ui(self, message: str, button_text: str) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 30, 20, 20)
        layout.setSpacing(20)

        # Message
        msg_label = QLabel(message)
        msg_label.setFont(TYPOGRAPHY.body)
        msg_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg_label)
        layout.addStretch()

        # OK button
        ok_btn = QPushButton(button_text)
        ok_btn.setFixedSize(100, 36)
        ok_btn.clicked.connect(self._on_confirm)
        style_button(ok_btn, "primary")
        layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        ok_btn.setFocus()

    def _on_confirm(self) -> None:
        """Handle OK button click."""
        self.result = True
        self.accept()

    @classmethod
    def show_info(cls, parent, title: str, message: str) -> None:
        """
        Show an information dialog.

        Args:
            parent: Parent window
            title: Dialog title
            message: Message to display
        """
        dialog = cls(parent, title, message)
        dialog.show()

    @classmethod
    def show_error(cls, parent, title: str, message: str) -> None:
        """
        Show an error dialog.

        Args:
            parent: Parent window
            title: Dialog title
            message: Error message to display
        """
        dialog = cls(parent, f"Error: {title}", message)
        dialog.show()

    @classmethod
    def show_success(cls, parent, title: str, message: str) -> None:
        """
        Show a success dialog.

        Args:
            parent: Parent window
            title: Dialog title
            message: Success message to display
        """
        dialog = cls(parent, title, message)
        dialog.show()
