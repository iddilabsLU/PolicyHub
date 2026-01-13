"""
PolicyHub Password Reset Dialog

Dialog for administrators to reset a user's password.
"""

import customtkinter as ctk

from app.theme import (
    COLORS,
    SPACING,
    TYPOGRAPHY,
    configure_button_style,
    configure_input_style,
)
from core.database import DatabaseManager
from dialogs.base_dialog import BaseDialog
from dialogs.confirm_dialog import InfoDialog
from models.user import User
from services.user_service import UserService
from utils.validators import validate_password


class PasswordResetDialog(BaseDialog):
    """
    Dialog for resetting a user's password.

    Admin-only operation that sets a new password without requiring the old one.
    """

    def __init__(
        self,
        parent,
        db: DatabaseManager,
        user: User,
    ):
        """
        Initialize the password reset dialog.

        Args:
            parent: Parent window
            db: Database manager
            user: User whose password to reset
        """
        self.db = db
        self.user_service = UserService(db)
        self.user = user

        super().__init__(parent, "Reset Password", width=400, height=300)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        # Form container
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING)

        # User info
        info_label = ctk.CTkLabel(
            form,
            text=f"Resetting password for: {self.user.full_name}",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        info_label.pack(anchor="w", pady=(0, 4))

        username_label = ctk.CTkLabel(
            form,
            text=f"Username: {self.user.username}",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        )
        username_label.pack(anchor="w", pady=(0, 16))

        # New Password field
        self._create_label(form, "New Password *")
        self.password_entry = ctk.CTkEntry(
            form,
            width=300,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
            show="*",
        )
        configure_input_style(self.password_entry)
        self.password_entry.pack(anchor="w", pady=(0, 12))

        # Confirm Password field
        self._create_label(form, "Confirm New Password *")
        self.confirm_entry = ctk.CTkEntry(
            form,
            width=300,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
            show="*",
        )
        configure_input_style(self.confirm_entry)
        self.confirm_entry.pack(anchor="w", pady=(0, 4))

        # Password hint
        hint = ctk.CTkLabel(
            form,
            text="Minimum 8 characters",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_MUTED,
        )
        hint.pack(anchor="w", pady=(0, 12))

        # Button frame
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING.WINDOW_PADDING, pady=(0, SPACING.WINDOW_PADDING))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self._on_cancel,
            width=100,
        )
        configure_button_style(cancel_btn, "secondary")
        cancel_btn.pack(side="right", padx=(8, 0))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Reset Password",
            command=self._on_save,
            width=140,
        )
        configure_button_style(save_btn, "primary")
        save_btn.pack(side="right")

    def _create_label(self, parent, text: str) -> None:
        """Create a field label."""
        label = ctk.CTkLabel(
            parent,
            text=text,
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        label.pack(anchor="w", pady=(0, 4))

    def _on_save(self) -> None:
        """Handle save button click."""
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()

        # Validate password
        is_valid, error = validate_password(password)
        if not is_valid:
            InfoDialog.show_error(self, "Invalid Password", error)
            return

        # Check passwords match
        if password != confirm:
            InfoDialog.show_error(self, "Password Mismatch", "Passwords do not match.")
            return

        try:
            self.user_service.reset_user_password(self.user.user_id, password)
            self.result = True
            InfoDialog.show_success(
                self,
                "Password Reset",
                f"Password has been reset for {self.user.username}.",
            )
            self.destroy()

        except PermissionError:
            InfoDialog.show_error(self, "Permission Denied", "You do not have permission to reset passwords.")
        except Exception as e:
            InfoDialog.show_error(self, "Error", str(e))
