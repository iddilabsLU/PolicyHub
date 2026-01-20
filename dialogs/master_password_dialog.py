"""
PolicyHub Master Password Dialog

Dialog for changing the master password.
Requires verification of current master password before allowing change.
"""

import customtkinter as ctk

from app.theme import COLORS, SPACING, TYPOGRAPHY, configure_button_style, configure_input_style
from core.database import DatabaseManager
from dialogs.base_dialog import BaseDialog
from dialogs.confirm_dialog import InfoDialog
from services.auth_service import AuthService
from services.settings_service import SettingsService
from utils.validators import validate_password


class MasterPasswordDialog(BaseDialog):
    """
    Dialog for changing the master password.

    Requires the current master password to be entered for verification
    before allowing a new password to be set.

    Only accessible by admins (MANAGE_USERS permission required).
    """

    def __init__(self, parent, db: DatabaseManager):
        """
        Initialize the master password dialog.

        Args:
            parent: Parent window
            db: Database manager instance
        """
        self.db = db
        self.settings_service = SettingsService(db)

        super().__init__(
            parent,
            "Change Master Password",
            width=400,
            height=380,
            resizable=False,
        )
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        # Main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING)

        # Info text
        info_label = ctk.CTkLabel(
            container,
            text="The master password is a safety net for forgotten admin passwords. "
                 "Enter the current master password to verify your identity, then set a new one.",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
            wraplength=340,
            justify="left",
        )
        info_label.pack(anchor="w", pady=(0, 16))

        # Current password field
        self._create_label(container, "Current Master Password *")
        self.current_entry = ctk.CTkEntry(
            container,
            width=340,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
            show="*",
        )
        configure_input_style(self.current_entry)
        self.current_entry.pack(anchor="w", pady=(0, 16))

        # New password field
        self._create_label(container, "New Master Password *")
        self.new_entry = ctk.CTkEntry(
            container,
            width=340,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
            show="*",
        )
        configure_input_style(self.new_entry)
        self.new_entry.pack(anchor="w", pady=(0, 16))

        # Confirm password field
        self._create_label(container, "Confirm New Password *")
        self.confirm_entry = ctk.CTkEntry(
            container,
            width=340,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
            show="*",
        )
        configure_input_style(self.confirm_entry)
        self.confirm_entry.pack(anchor="w", pady=(0, 8))

        # Password hint
        hint_label = ctk.CTkLabel(
            container,
            text="Minimum 8 characters",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_MUTED,
        )
        hint_label.pack(anchor="w", pady=(0, 16))

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom")

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
        current = self.current_entry.get()
        new = self.new_entry.get()
        confirm = self.confirm_entry.get()

        # Validate current password is provided
        if not current:
            InfoDialog.show_error(self, "Error", "Please enter the current master password.")
            return

        # Verify current master password
        master_hash = self.settings_service.get_master_password_hash()
        if not master_hash:
            InfoDialog.show_error(
                self,
                "Error",
                "Master password not configured. Please contact your administrator.",
            )
            return

        if not AuthService.verify_password(current, master_hash):
            InfoDialog.show_error(self, "Error", "Current master password is incorrect.")
            return

        # Validate new password
        if not new:
            InfoDialog.show_error(self, "Error", "Please enter a new password.")
            return

        is_valid, error = validate_password(new)
        if not is_valid:
            InfoDialog.show_error(self, "Invalid Password", error)
            return

        # Confirm passwords match
        if new != confirm:
            InfoDialog.show_error(self, "Error", "New passwords do not match.")
            return

        # Check new password is different from current
        if AuthService.verify_password(new, master_hash):
            InfoDialog.show_error(
                self,
                "Error",
                "New password must be different from the current password.",
            )
            return

        try:
            # Set the new master password
            self.settings_service.set_master_password(new)
            InfoDialog.show_info(
                self,
                "Success",
                "Master password has been changed successfully.",
            )
            self.result = True
            self.destroy()

        except PermissionError:
            InfoDialog.show_error(
                self,
                "Permission Denied",
                "You do not have permission to change the master password.",
            )
        except ValueError as e:
            InfoDialog.show_error(self, "Error", str(e))
        except Exception as e:
            InfoDialog.show_error(self, "Error", f"Failed to change password: {str(e)}")
