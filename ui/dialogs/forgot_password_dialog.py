"""
PolicyHub Forgot Password Dialog (PySide6)

Dialog for users to reset their password using the master password.
Accessible from the login screen without being logged in.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button
from core.database import DatabaseManager
from services.auth_service import AuthService
from services.settings_service import SettingsService
from ui.dialogs.base_dialog import BaseDialog
from ui.dialogs.confirm_dialog import InfoDialog
from utils.validators import validate_password


class ForgotPasswordDialog(BaseDialog):
    """
    Dialog for resetting a forgotten password using the master password.

    This allows users who have forgotten their password to reset it
    by verifying with the master password.
    """

    def __init__(self, parent: Optional[QWidget], db: DatabaseManager):
        """
        Initialize the forgot password dialog.

        Args:
            parent: Parent window
            db: Database manager instance
        """
        self.db = db
        self.auth_service = AuthService(db)
        self.settings_service = SettingsService(db)

        super().__init__(
            parent,
            "Reset Forgotten Password",
            width=420,
            height=420,
            resizable=False,
        )
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
        )
        layout.setSpacing(0)

        # Info text
        info_label = QLabel(
            "Enter your username and the master password to reset your password. "
            "Contact your administrator if you don't know the master password."
        )
        info_label.setFont(TYPOGRAPHY.small)
        info_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        layout.addSpacing(16)

        # Username field
        self._add_field_label(layout, "Username *")
        self.username_entry = QLineEdit()
        self.username_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        layout.addWidget(self.username_entry)
        layout.addSpacing(12)

        # Master password field
        self._add_field_label(layout, "Master Password *")
        self.master_entry = QLineEdit()
        self.master_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.master_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        layout.addWidget(self.master_entry)
        layout.addSpacing(12)

        # New password field
        self._add_field_label(layout, "New Password *")
        self.new_entry = QLineEdit()
        self.new_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        layout.addWidget(self.new_entry)
        layout.addSpacing(12)

        # Confirm password field
        self._add_field_label(layout, "Confirm New Password *")
        self.confirm_entry = QLineEdit()
        self.confirm_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        layout.addWidget(self.confirm_entry)
        layout.addSpacing(4)

        # Password hint
        hint_label = QLabel("Minimum 8 characters")
        hint_label.setFont(TYPOGRAPHY.small)
        hint_label.setStyleSheet(f"color: {COLORS.TEXT_MUTED};")
        layout.addWidget(hint_label)

        layout.addStretch()

        # Buttons
        btn_frame = QWidget()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 36)
        cancel_btn.clicked.connect(self._on_cancel)
        style_button(cancel_btn, "secondary")
        btn_layout.addWidget(cancel_btn)

        reset_btn = QPushButton("Reset Password")
        reset_btn.setFixedSize(140, 36)
        reset_btn.clicked.connect(self._on_reset)
        style_button(reset_btn, "primary")
        btn_layout.addWidget(reset_btn)

        layout.addWidget(btn_frame)

        # Focus username entry
        self.username_entry.setFocus()

    def _add_field_label(self, layout: QVBoxLayout, text: str) -> None:
        """Add a field label to the layout."""
        label = QLabel(text)
        label.setFont(TYPOGRAPHY.body)
        label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        layout.addWidget(label)
        layout.addSpacing(4)

    def _on_reset(self) -> None:
        """Handle reset button click."""
        username = self.username_entry.text().strip()
        master_password = self.master_entry.text()
        new_password = self.new_entry.text()
        confirm_password = self.confirm_entry.text()

        # Validate username
        if not username:
            InfoDialog.show_error(self, "Validation", "Please enter your username.")
            return

        # Find the user
        user_row = self.db.fetch_one(
            "SELECT * FROM users WHERE LOWER(username) = LOWER(?) AND is_active = 1",
            (username,),
        )
        if not user_row:
            InfoDialog.show_error(
                self, "User Not Found", "User not found or account is inactive."
            )
            return

        # Validate master password
        if not master_password:
            InfoDialog.show_error(
                self, "Validation", "Please enter the master password."
            )
            return

        # Verify master password
        master_hash = self.settings_service.get_master_password_hash()
        if not master_hash:
            InfoDialog.show_error(
                self,
                "Not Configured",
                "Master password is not configured. Please contact your administrator.",
            )
            return

        if not AuthService.verify_password(master_password, master_hash):
            InfoDialog.show_error(
                self, "Invalid Password", "Master password is incorrect."
            )
            return

        # Validate new password
        if not new_password:
            InfoDialog.show_error(self, "Validation", "Please enter a new password.")
            return

        is_valid, error = validate_password(new_password)
        if not is_valid:
            InfoDialog.show_error(self, "Invalid Password", error)
            return

        # Confirm passwords match
        if new_password != confirm_password:
            InfoDialog.show_error(
                self, "Password Mismatch", "New passwords do not match."
            )
            return

        # Reset the password
        try:
            user_id = user_row["user_id"]
            success = self.auth_service.reset_password(
                user_id, new_password, force_change=False
            )

            if success:
                InfoDialog.show_success(
                    self,
                    "Password Reset",
                    "Your password has been reset successfully. "
                    "You can now log in with your new password.",
                )
                self.result = True
                self.accept()
            else:
                InfoDialog.show_error(
                    self, "Failed", "Failed to reset password. Please try again."
                )

        except Exception as e:
            InfoDialog.show_error(
                self, "Error", f"Failed to reset password: {str(e)}"
            )
