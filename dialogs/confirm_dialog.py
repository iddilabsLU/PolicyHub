"""
PolicyHub Confirm Dialog

A simple confirmation dialog with Yes/No or custom buttons.
"""

from typing import Optional

import customtkinter as ctk

from app.theme import COLORS, SPACING, TYPOGRAPHY, configure_button_style
from dialogs.base_dialog import BaseDialog


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
        super().__init__(parent, title, width=400, height=180)

        self._build_ui(message, confirm_text, cancel_text, confirm_style)

    def _build_ui(
        self,
        message: str,
        confirm_text: str,
        cancel_text: str,
        confirm_style: str,
    ) -> None:
        """Build the dialog UI."""
        # Message
        msg_label = ctk.CTkLabel(
            self,
            text=message,
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
            wraplength=360,
            justify="center",
        )
        msg_label.pack(pady=(30, 20), padx=20)

        # Buttons frame
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=20)

        # Cancel button
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text=cancel_text,
            command=self._on_cancel,
            width=100,
            height=36,
        )
        configure_button_style(cancel_btn, "secondary")
        cancel_btn.pack(side="left", padx=5)

        # Confirm button
        confirm_btn = ctk.CTkButton(
            btn_frame,
            text=confirm_text,
            command=self._on_confirm,
            width=100,
            height=36,
        )
        configure_button_style(confirm_btn, confirm_style)
        confirm_btn.pack(side="left", padx=5)

        # Focus confirm button
        confirm_btn.focus_set()

    def _on_confirm(self) -> None:
        """Handle confirm button click."""
        self.result = True
        self.destroy()

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        self.result = False
        self.destroy()

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
        super().__init__(parent, title, width=400, height=160)

        self._build_ui(message, button_text)

    def _build_ui(self, message: str, button_text: str) -> None:
        """Build the dialog UI."""
        # Message
        msg_label = ctk.CTkLabel(
            self,
            text=message,
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
            wraplength=360,
            justify="center",
        )
        msg_label.pack(pady=(30, 20), padx=20)

        # OK button
        ok_btn = ctk.CTkButton(
            self,
            text=button_text,
            command=self._on_confirm,
            width=100,
            height=36,
        )
        configure_button_style(ok_btn, "primary")
        ok_btn.pack(pady=(0, 20))
        ok_btn.focus_set()

    def _on_confirm(self) -> None:
        """Handle OK button click."""
        self.result = True
        self.destroy()

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
