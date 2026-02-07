"""
PolicyHub Change Password Dialog (PySide6)

Dialog for users to change their own password.
Available to all logged-in users.
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
from core.session import SessionManager
from services.auth_service import AuthService
from ui.dialogs.base_dialog import BaseDialog
from ui.dialogs.confirm_dialog import InfoDialog
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING
        )
        layout.setSpacing(0)

        # Info text
        info_label = QLabel("Enter your current password and choose a new password.")
        info_label.setFont(TYPOGRAPHY.body)
        info_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        layout.addSpacing(16)

        # Current Password field
        self._create_label(layout, "Current Password *")
        self.current_entry = QLineEdit()
        self.current_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        layout.addWidget(self.current_entry)
        layout.addSpacing(12)

        # New Password field
        self._create_label(layout, "New Password *")
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        layout.addWidget(self.password_entry)
        layout.addSpacing(12)

        # Confirm Password field
        self._create_label(layout, "Confirm New Password *")
        self.confirm_entry = QLineEdit()
        self.confirm_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        layout.addWidget(self.confirm_entry)
        layout.addSpacing(4)

        # Password hint
        hint = QLabel("Minimum 8 characters")
        hint.setFont(TYPOGRAPHY.small)
        hint.setStyleSheet(f"color: {COLORS.TEXT_MUTED};")
        layout.addWidget(hint)

        layout.addStretch()

        # Button frame
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

        # Focus first field
        self.current_entry.setFocus()

    def _create_label(self, layout: QVBoxLayout, text: str) -> None:
        """Create a field label."""
        label = QLabel(text)
        label.setFont(TYPOGRAPHY.body)
        label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        layout.addWidget(label)
        layout.addSpacing(4)

    def _on_save(self) -> None:
        """Handle save button click."""
        current_password = self.current_entry.text()
        new_password = self.password_entry.text()
        confirm_password = self.confirm_entry.text()

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
            self.accept()
        else:
            InfoDialog.show_error(self, "Error", error or "Failed to change password.")
