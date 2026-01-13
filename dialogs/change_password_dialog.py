"""
PolicyHub Change Password Dialog

Dialog for users to change their own password.
Available to all logged-in users.
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
from core.session import SessionManager
from dialogs.base_dialog import BaseDialog
from dialogs.confirm_dialog import InfoDialog
from services.auth_service import AuthService
from utils.validators import validate_password


class ChangePasswordDialog(BaseDialog):
    """
    Dialog for users to change their own password.

    Requires the current password for verification before allowing change.
    """

    def __init__(
        self,
        parent,
        db: DatabaseManager,
    ):
        """
        Initialize the change password dialog.

        Args:
            parent: Parent window
            db: Database manager
        """
        self.db = db
        self.auth_service = AuthService(db)
        self.session_manager = SessionManager.get_instance()

        super().__init__(parent, "Change Password", width=400, height=350)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        # Form container
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING)

        # Info text
        info_label = ctk.CTkLabel(
            form,
            text="Enter your current password and choose a new password.",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_SECONDARY,
            wraplength=350,
        )
        info_label.pack(anchor="w", pady=(0, 16))

        # Current Password field
        self._create_label(form, "Current Password *")
        self.current_entry = ctk.CTkEntry(
            form,
            width=300,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
            show="*",
        )
        configure_input_style(self.current_entry)
        self.current_entry.pack(anchor="w", pady=(0, 12))

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
            text="Change Password",
            command=self._on_save,
            width=140,
        )
        configure_button_style(save_btn, "primary")
        save_btn.pack(side="right")

        # Focus first field
        self.current_entry.focus()

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
        current_password = self.current_entry.get()
        new_password = self.password_entry.get()
        confirm_password = self.confirm_entry.get()

        # Validate current password is provided
        if not current_password:
            InfoDialog.show_error(self, "Required Field", "Please enter your current password.")
            return

        # Validate new password
        is_valid, error = validate_password(new_password)
        if not is_valid:
            InfoDialog.show_error(self, "Invalid Password", error)
            return

        # Check passwords match
        if new_password != confirm_password:
            InfoDialog.show_error(self, "Password Mismatch", "New passwords do not match.")
            return

        # Check new password is different from current
        if current_password == new_password:
            InfoDialog.show_error(self, "Same Password", "New password must be different from current password.")
            return

        # Get current user ID
        user_id = self.session_manager.user_id
        if not user_id:
            InfoDialog.show_error(self, "Session Error", "No user logged in.")
            return

        # Attempt to change password
        success, error = self.auth_service.change_password(
            user_id=user_id,
            current_password=current_password,
            new_password=new_password,
        )

        if success:
            self.result = True
            InfoDialog.show_success(
                self,
                "Password Changed",
                "Your password has been changed successfully.",
            )
            self.destroy()
        else:
            InfoDialog.show_error(self, "Error", error or "Failed to change password.")
