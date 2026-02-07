"""
PolicyHub Master Password Dialog (PySide6)

Dialog for changing the master password.
Requires verification of current master password before allowing change.
"""

from typing import Optional

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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING
        )
        layout.setSpacing(0)

        # Info text
        info_label = QLabel(
            "The master password is a safety net for forgotten admin passwords. "
            "Enter the current master password to verify your identity, then set a new one."
        )
        info_label.setFont(TYPOGRAPHY.small)
        info_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        layout.addSpacing(16)

        # Current password field
        self._create_label(layout, "Current Master Password *")
        self.current_entry = QLineEdit()
        self.current_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        layout.addWidget(self.current_entry)
        layout.addSpacing(16)

        # New password field
        self._create_label(layout, "New Master Password *")
        self.new_entry = QLineEdit()
        self.new_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        layout.addWidget(self.new_entry)
        layout.addSpacing(16)

        # Confirm password field
        self._create_label(layout, "Confirm New Password *")
        self.confirm_entry = QLineEdit()
        self.confirm_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        layout.addWidget(self.confirm_entry)
        layout.addSpacing(8)

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

        save_btn = QPushButton("Change Password")
        save_btn.setFixedWidth(140)
        save_btn.clicked.connect(self._on_save)
        style_button(save_btn, "primary")
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self._on_cancel)
        style_button(cancel_btn, "secondary")
        btn_layout.addWidget(cancel_btn)

        layout.addWidget(btn_frame)

    def _create_label(self, layout: QVBoxLayout, text: str) -> None:
        """Create a field label."""
        label = QLabel(text)
        label.setFont(TYPOGRAPHY.body)
        label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        layout.addWidget(label)
        layout.addSpacing(4)

    def _on_save(self) -> None:
        """Handle save button click."""
        current = self.current_entry.text()
        new = self.new_entry.text()
        confirm = self.confirm_entry.text()

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
            self.accept()

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
