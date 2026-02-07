"""
PolicyHub Password Reset Dialog (PySide6)

Dialog for administrators to reset a user's password.
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
from models.user import User
from services.user_service import UserService
from ui.dialogs.base_dialog import BaseDialog
from ui.dialogs.confirm_dialog import InfoDialog
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING
        )
        layout.setSpacing(0)

        # User info
        info_label = QLabel(f"Resetting password for: {self.user.full_name}")
        info_label.setFont(TYPOGRAPHY.body)
        info_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        layout.addWidget(info_label)
        layout.addSpacing(4)

        username_label = QLabel(f"Username: {self.user.username}")
        username_label.setFont(TYPOGRAPHY.small)
        username_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        layout.addWidget(username_label)
        layout.addSpacing(16)

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

        save_btn = QPushButton("Reset Password")
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
        password = self.password_entry.text()
        confirm = self.confirm_entry.text()

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
            self.accept()

        except PermissionError:
            InfoDialog.show_error(self, "Permission Denied", "You do not have permission to reset passwords.")
        except Exception as e:
            InfoDialog.show_error(self, "Error", str(e))
