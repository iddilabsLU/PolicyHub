"""
PolicyHub Force Password Change View (PySide6)

Displayed when a user must change their password on first login
or after an admin password reset.
"""

from typing import TYPE_CHECKING, Callable, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.constants import MIN_PASSWORD_LENGTH
from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button
from core.database import DatabaseManager
from core.session import SessionManager
from services.auth_service import AuthService
from ui.views.base_view import CenteredView

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class ForcePasswordChangeView(CenteredView):
    """
    Force password change screen.

    Displayed after login when the user's force_password_change flag is set.
    User must set a new password before proceeding to the main application.
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        app: "PolicyHubApp",
        db: DatabaseManager,
        on_password_changed: Callable[[], None],
    ):
        """
        Initialize the force password change view.

        Args:
            parent: Parent widget
            app: Main application instance
            db: Database manager
            on_password_changed: Callback when password is successfully changed
        """
        super().__init__(parent, app, max_width=420)
        self.db = db
        self.auth_service = AuthService(db)
        self.session_manager = SessionManager.get_instance()
        self.on_password_changed = on_password_changed

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the password change UI."""
        # Content layout
        layout = QVBoxLayout(self.content_frame)
        layout.setContentsMargins(
            SPACING.CARD_PADDING, SPACING.CARD_PADDING,
            SPACING.CARD_PADDING, SPACING.CARD_PADDING
        )
        layout.setSpacing(0)

        # Header
        header_frame = QWidget()
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon (lock symbol)
        icon_frame = QFrame()
        icon_frame.setFixedSize(50, 50)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.WARNING};
                border-radius: {SPACING.CORNER_RADIUS_LARGE}px;
            }}
        """)
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        icon_text = QLabel("!")
        icon_text.setFont(TYPOGRAPHY.get_font(24, TYPOGRAPHY.WEIGHT_BOLD))
        icon_text.setStyleSheet(f"color: {COLORS.CARD}; background: transparent;")
        icon_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(icon_text)

        header_layout.addWidget(icon_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        header_layout.addSpacing(10)

        title_label = QLabel("Password Change Required")
        title_label.setFont(TYPOGRAPHY.get_font(18, TYPOGRAPHY.WEIGHT_BOLD))
        title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        # Get current user's name
        user_name = self.session_manager.full_name or self.session_manager.username or "User"

        subtitle_label = QLabel(f"Welcome, {user_name}!\nPlease set a new password to continue.")
        subtitle_label.setFont(TYPOGRAPHY.body)
        subtitle_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addSpacing(10)
        header_layout.addWidget(subtitle_label)

        layout.addWidget(header_frame)
        layout.addSpacing(SPACING.SECTION_SPACING)

        # Form
        form_frame = QWidget()
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(0)

        # New Password
        new_password_label = QLabel("New Password:")
        new_password_label.setFont(TYPOGRAPHY.body)
        new_password_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        form_layout.addWidget(new_password_label)
        form_layout.addSpacing(5)

        self.new_password_entry = QLineEdit()
        self.new_password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        form_layout.addWidget(self.new_password_entry)
        form_layout.addSpacing(15)

        # Confirm Password
        confirm_password_label = QLabel("Confirm New Password:")
        confirm_password_label.setFont(TYPOGRAPHY.body)
        confirm_password_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        form_layout.addWidget(confirm_password_label)
        form_layout.addSpacing(5)

        self.confirm_password_entry = QLineEdit()
        self.confirm_password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        self.confirm_password_entry.returnPressed.connect(self._on_change_password)
        form_layout.addWidget(self.confirm_password_entry)
        form_layout.addSpacing(10)

        # Password requirements hint
        hint_label = QLabel(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
        hint_label.setFont(TYPOGRAPHY.small)
        hint_label.setStyleSheet(f"color: {COLORS.TEXT_MUTED};")
        form_layout.addWidget(hint_label)

        layout.addWidget(form_frame)

        # Status/error label
        self.status_label = QLabel("")
        self.status_label.setFont(TYPOGRAPHY.small)
        self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(5)
        layout.addWidget(self.status_label)

        # Change Password button
        self.change_button = QPushButton("Change Password")
        self.change_button.setFixedWidth(150)
        self.change_button.clicked.connect(self._on_change_password)
        style_button(self.change_button, "primary")
        layout.addSpacing(SPACING.SECTION_SPACING)
        layout.addWidget(self.change_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def _on_change_password(self) -> None:
        """Handle the Change Password button click."""
        new_password = self.new_password_entry.text()
        confirm_password = self.confirm_password_entry.text()

        # Validate new password
        if not new_password:
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
            self.status_label.setText("Please enter a new password.")
            return

        if len(new_password) < MIN_PASSWORD_LENGTH:
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
            self.status_label.setText(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
            return

        # Validate confirmation
        if not confirm_password:
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
            self.status_label.setText("Please confirm your new password.")
            return

        if new_password != confirm_password:
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
            self.status_label.setText("Passwords do not match.")
            self.confirm_password_entry.clear()
            self.confirm_password_entry.setFocus()
            return

        # Get current user ID
        user_id = self.session_manager.user_id
        if not user_id:
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
            self.status_label.setText("Session error. Please log in again.")
            return

        # Change the password
        success, error = self.auth_service.set_new_password(user_id, new_password)

        if success:
            self.status_label.setStyleSheet(f"color: {COLORS.SUCCESS};")
            self.status_label.setText("Password changed successfully!")
            # Proceed to main view after a short delay
            QTimer.singleShot(500, self.on_password_changed)
        else:
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
            self.status_label.setText(error or "Failed to change password. Please try again.")

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        # Clear fields and focus
        self.new_password_entry.clear()
        self.confirm_password_entry.clear()
        self.status_label.setText("")
        self.new_password_entry.setFocus()
