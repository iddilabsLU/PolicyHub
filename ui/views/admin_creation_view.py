"""
PolicyHub Admin Creation View (PySide6)

First-time admin account creation screen.
Shown when the database exists but has no users.
"""

from typing import TYPE_CHECKING, Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.constants import APP_NAME
from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button
from core.database import DatabaseManager
from services.auth_service import AuthService
from ui.views.base_view import CenteredView
from utils.validators import (
    validate_email,
    validate_full_name,
    validate_password,
    validate_passwords_match,
    validate_username,
)

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class AdminCreationView(CenteredView):
    """
    Admin account creation screen for first-time setup.

    Creates the first admin user who will manage the system.
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        app: "PolicyHubApp",
        db: DatabaseManager,
        on_complete: Callable[[], None],
    ):
        """
        Initialize the admin creation view.

        Args:
            parent: Parent widget
            app: Main application instance
            db: Database manager
            on_complete: Callback when admin is created
        """
        super().__init__(parent, app, max_width=500)
        self.db = db
        self.auth_service = AuthService(db)
        self.on_complete = on_complete

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the admin creation UI."""
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

        title_label = QLabel(APP_NAME)
        title_label.setFont(TYPOGRAPHY.get_font(24, TYPOGRAPHY.WEIGHT_BOLD))
        title_label.setStyleSheet(f"color: {COLORS.PRIMARY};")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        header_layout.addSpacing(5)

        subtitle_label = QLabel("Create Administrator Account")
        subtitle_label.setFont(TYPOGRAPHY.section_heading)
        subtitle_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)

        layout.addWidget(header_frame)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"background-color: {COLORS.BORDER};")
        divider.setFixedHeight(1)
        layout.addSpacing(SPACING.SECTION_SPACING)
        layout.addWidget(divider)
        layout.addSpacing(SPACING.SECTION_SPACING)

        # Info message
        info_label = QLabel("You're the first user. Create an admin account to get started.")
        info_label.setFont(TYPOGRAPHY.body)
        info_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        layout.addSpacing(SPACING.SECTION_SPACING)

        # Form
        form_frame = QWidget()
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setVerticalSpacing(5)
        form_layout.setHorizontalSpacing(0)

        row = 0

        # Username
        username_label = QLabel("Username:")
        username_label.setFont(TYPOGRAPHY.body)
        username_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        form_layout.addWidget(username_label, row, 0)
        row += 1

        self.username_entry = QLineEdit()
        self.username_entry.setPlaceholderText("admin")
        self.username_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        form_layout.addWidget(self.username_entry, row, 0)
        row += 1
        form_layout.setRowMinimumHeight(row, 15)
        row += 1

        # Full Name
        fullname_label = QLabel("Full Name:")
        fullname_label.setFont(TYPOGRAPHY.body)
        fullname_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        form_layout.addWidget(fullname_label, row, 0)
        row += 1

        self.fullname_entry = QLineEdit()
        self.fullname_entry.setPlaceholderText("John Smith")
        self.fullname_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        form_layout.addWidget(self.fullname_entry, row, 0)
        row += 1
        form_layout.setRowMinimumHeight(row, 15)
        row += 1

        # Email (required)
        email_label = QLabel("Email *")
        email_label.setFont(TYPOGRAPHY.body)
        email_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        form_layout.addWidget(email_label, row, 0)
        row += 1

        self.email_entry = QLineEdit()
        self.email_entry.setPlaceholderText("j.smith@company.lu")
        self.email_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        form_layout.addWidget(self.email_entry, row, 0)
        row += 1
        form_layout.setRowMinimumHeight(row, 15)
        row += 1

        # Password
        password_label = QLabel("Password:")
        password_label.setFont(TYPOGRAPHY.body)
        password_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        form_layout.addWidget(password_label, row, 0)
        row += 1

        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        form_layout.addWidget(self.password_entry, row, 0)
        row += 1
        form_layout.setRowMinimumHeight(row, 15)
        row += 1

        # Confirm Password
        confirm_label = QLabel("Confirm Password:")
        confirm_label.setFont(TYPOGRAPHY.body)
        confirm_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        form_layout.addWidget(confirm_label, row, 0)
        row += 1

        self.confirm_entry = QLineEdit()
        self.confirm_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        form_layout.addWidget(self.confirm_entry, row, 0)
        row += 1

        # Password hint
        hint_label = QLabel("Minimum 8 characters")
        hint_label.setFont(TYPOGRAPHY.small)
        hint_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        form_layout.addWidget(hint_label, row, 0)

        layout.addWidget(form_frame)

        # Status/error label
        self.status_label = QLabel("")
        self.status_label.setFont(TYPOGRAPHY.small)
        self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(self.status_label)

        # Divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.Shape.HLine)
        divider2.setStyleSheet(f"background-color: {COLORS.BORDER};")
        divider2.setFixedHeight(1)
        layout.addSpacing(SPACING.SECTION_SPACING)
        layout.addWidget(divider2)
        layout.addSpacing(SPACING.SECTION_SPACING)

        # Create button
        button_frame = QWidget()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()

        self.create_button = QPushButton("Create & Login")
        self.create_button.setFixedWidth(140)
        self.create_button.clicked.connect(self._on_create)
        style_button(self.create_button, "primary")
        button_layout.addWidget(self.create_button)

        layout.addWidget(button_frame)

    def _on_create(self) -> None:
        """Handle the Create button click."""
        username = self.username_entry.text().strip()
        full_name = self.fullname_entry.text().strip()
        email = self.email_entry.text().strip()
        password = self.password_entry.text()
        confirm = self.confirm_entry.text()

        # Validate username
        valid, error = validate_username(username)
        if not valid:
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
            self.status_label.setText(error)
            return

        # Validate full name
        valid, error = validate_full_name(full_name)
        if not valid:
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
            self.status_label.setText(error)
            return

        # Validate email (required)
        if not email:
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
            self.status_label.setText("Email is required.")
            return

        valid, error = validate_email(email)
        if not valid:
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
            self.status_label.setText(error)
            return

        # Validate password
        valid, error = validate_password(password)
        if not valid:
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
            self.status_label.setText(error)
            return

        # Validate passwords match
        valid, error = validate_passwords_match(password, confirm)
        if not valid:
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
            self.status_label.setText(error)
            return

        try:
            # Create the admin user
            user = self.auth_service.create_first_admin(
                username=username,
                password=password,
                full_name=full_name,
                email=email,
            )

            # Set require_login to false for new databases (bypass permission check)
            from services.settings_service import SettingsService
            settings_service = SettingsService(self.db)
            settings_service.set_require_login_direct(False)

            # Auto-login
            self.auth_service.login(username, password)

            # Seed sample documents for testing
            from services.document_service import DocumentService
            doc_service = DocumentService(self.db)
            doc_service.seed_sample_documents()

            self.status_label.setStyleSheet(f"color: {COLORS.SUCCESS};")
            self.status_label.setText("Account created successfully!")

            # Call completion callback
            self.on_complete()

        except Exception as e:
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
            self.status_label.setText(f"Error: {str(e)}")

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        self.username_entry.setFocus()
