"""
PolicyHub Login View (PySide6)

User authentication screen.
"""

from typing import TYPE_CHECKING, Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.constants import APP_NAME
from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button
from core.config import ConfigManager
from core.database import DatabaseManager
from services.auth_service import AuthService
from ui.dialogs.forgot_password_dialog import ForgotPasswordDialog
from ui.views.base_view import CenteredView

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class LoginView(CenteredView):
    """
    Login screen for user authentication.
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        app: "PolicyHubApp",
        db: DatabaseManager,
        on_login: Callable[[], None],
        on_change_folder: Callable[[], None],
    ):
        """
        Initialize the login view.

        Args:
            parent: Parent widget
            app: Main application instance
            db: Database manager
            on_login: Callback when login succeeds
            on_change_folder: Callback to change shared folder
        """
        super().__init__(parent, app, max_width=400)
        self.db = db
        self.auth_service = AuthService(db)
        self.config_manager = ConfigManager.get_instance()
        self.on_login = on_login
        self.on_change_folder = on_change_folder

        self._build_ui()
        self._load_remembered_username()

    def _build_ui(self) -> None:
        """Build the login UI."""
        # Override the content_frame style to remove border, use subtle shadow
        self.content_frame.setStyleSheet(f"""
            QFrame#contentCard {{
                background-color: {COLORS.CARD};
                border-radius: {SPACING.CORNER_RADIUS_LARGE}px;
                border: none;
            }}
        """)

        # Content layout
        layout = QVBoxLayout(self.content_frame)
        layout.setContentsMargins(32, 32, 32, 24)
        layout.setSpacing(0)

        # Header with logo area
        header_frame = QWidget()
        header_frame.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo
        logo_frame = QFrame()
        logo_frame.setFixedSize(64, 64)
        logo_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.PRIMARY};
                border-radius: 12px;
                border: none;
            }}
        """)
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(0, 0, 0, 0)

        logo_text = QLabel("PH")
        logo_text.setFont(TYPOGRAPHY.get_font(26, TYPOGRAPHY.WEIGHT_BOLD))
        logo_text.setStyleSheet(f"color: {COLORS.PRIMARY_FOREGROUND}; background: transparent;")
        logo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_text)

        header_layout.addWidget(logo_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        header_layout.addSpacing(12)

        # App title
        title_label = QLabel(APP_NAME)
        title_label.setFont(TYPOGRAPHY.get_font(22, TYPOGRAPHY.WEIGHT_BOLD))
        title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Policy & Procedure Manager")
        subtitle_label.setFont(TYPOGRAPHY.body)
        subtitle_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)

        layout.addWidget(header_frame)
        layout.addSpacing(28)

        # Form
        form_frame = QWidget()
        form_frame.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(0)

        # Modern input style without heavy borders
        input_style = f"""
            QLineEdit {{
                background-color: {COLORS.MUTED};
                border: none;
                border-radius: 8px;
                padding: 0 14px;
                font-size: 14px;
                color: {COLORS.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                background-color: {COLORS.CARD};
                border: 2px solid {COLORS.PRIMARY};
            }}
            QLineEdit::placeholder {{
                color: {COLORS.TEXT_MUTED};
            }}
        """

        # Username
        username_label = QLabel("Username")
        username_label.setFont(TYPOGRAPHY.get_font(13, TYPOGRAPHY.WEIGHT_MEDIUM))
        username_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        form_layout.addWidget(username_label)
        form_layout.addSpacing(6)

        self.username_entry = QLineEdit()
        self.username_entry.setFixedHeight(44)
        self.username_entry.setPlaceholderText("Enter your username")
        self.username_entry.setStyleSheet(input_style)
        form_layout.addWidget(self.username_entry)
        form_layout.addSpacing(16)

        # Password
        password_label = QLabel("Password")
        password_label.setFont(TYPOGRAPHY.get_font(13, TYPOGRAPHY.WEIGHT_MEDIUM))
        password_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        form_layout.addWidget(password_label)
        form_layout.addSpacing(6)

        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_entry.setFixedHeight(44)
        self.password_entry.setPlaceholderText("Enter your password")
        self.password_entry.setStyleSheet(input_style)
        self.password_entry.returnPressed.connect(self._on_login)
        form_layout.addWidget(self.password_entry)
        form_layout.addSpacing(16)

        # Options row
        options_layout = QHBoxLayout()
        options_layout.setContentsMargins(0, 0, 0, 0)

        # Remember username checkbox
        self.remember_check = QCheckBox("Remember me")
        self.remember_check.setFont(TYPOGRAPHY.small)
        self.remember_check.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS.TEXT_SECONDARY};
                background: transparent;
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid {COLORS.INPUT_BORDER};
                background-color: {COLORS.CARD};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS.PRIMARY};
                border-color: {COLORS.PRIMARY};
            }}
        """)
        options_layout.addWidget(self.remember_check)

        options_layout.addStretch()

        # Forgot password link
        forgot_button = QPushButton("Forgot password?")
        forgot_button.setFont(TYPOGRAPHY.small)
        forgot_button.setCursor(Qt.CursorShape.PointingHandCursor)
        forgot_button.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS.PRIMARY};
                background: transparent;
                border: none;
                padding: 0;
            }}
            QPushButton:hover {{
                color: {COLORS.PRIMARY_HOVER};
            }}
        """)
        forgot_button.clicked.connect(self._on_forgot_password)
        options_layout.addWidget(forgot_button)

        form_layout.addLayout(options_layout)

        layout.addWidget(form_frame)

        # Status/error label
        self.status_label = QLabel("")
        self.status_label.setFont(TYPOGRAPHY.small)
        self.status_label.setStyleSheet(f"color: {COLORS.DANGER}; background: transparent;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(16)
        layout.addWidget(self.status_label)

        # Login button - full width
        self.login_button = QPushButton("Sign In")
        self.login_button.setFixedHeight(44)
        self.login_button.setFont(TYPOGRAPHY.get_font(14, TYPOGRAPHY.WEIGHT_MEDIUM))
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.clicked.connect(self._on_login)
        self.login_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.PRIMARY};
                color: {COLORS.PRIMARY_FOREGROUND};
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.PRIMARY};
            }}
        """)
        layout.addSpacing(8)
        layout.addWidget(self.login_button)

        # Footer with connection info
        layout.addSpacing(24)

        footer_frame = QWidget()
        footer_frame.setStyleSheet("background: transparent;")
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(0, 0, 0, 0)

        # Get shared folder path
        config = self.config_manager.load()
        folder_path = config.shared_folder_path or "Not configured"

        # Truncate long paths
        if len(folder_path) > 30:
            folder_path = "..." + folder_path[-27:]

        connection_label = QLabel(f"Database: {folder_path}")
        connection_label.setFont(TYPOGRAPHY.small)
        connection_label.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; background: transparent;")
        footer_layout.addWidget(connection_label)

        footer_layout.addStretch()

        change_button = QPushButton("Change")
        change_button.setFont(TYPOGRAPHY.small)
        change_button.setCursor(Qt.CursorShape.PointingHandCursor)
        change_button.clicked.connect(self._on_change_folder)
        change_button.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS.PRIMARY};
                background: transparent;
                border: none;
                padding: 0;
            }}
            QPushButton:hover {{
                color: {COLORS.PRIMARY_HOVER};
            }}
        """)
        footer_layout.addWidget(change_button)

        layout.addWidget(footer_frame)

    def _load_remembered_username(self) -> None:
        """Load the remembered username from config."""
        config = self.config_manager.load()
        if config.remembered_username:
            self.username_entry.setText(config.remembered_username)
            self.remember_check.setChecked(True)
            # Focus password field since username is pre-filled
            self.password_entry.setFocus()
        else:
            self.username_entry.setFocus()

    def _on_login(self) -> None:
        """Handle the Login button click."""
        username = self.username_entry.text().strip()
        password = self.password_entry.text()

        if not username:
            self.status_label.setText("Please enter your username.")
            return

        if not password:
            self.status_label.setText("Please enter your password.")
            return

        # Attempt authentication
        session = self.auth_service.login(username, password)

        if session is None:
            self.status_label.setText("Invalid username or password.")
            self.password_entry.clear()
            self.password_entry.setFocus()
            return

        # Handle "remember username"
        if self.remember_check.isChecked():
            self.config_manager.update(remembered_username=username)
        else:
            self.config_manager.clear_remembered_username()

        self.status_label.setStyleSheet(f"color: {COLORS.SUCCESS};")
        self.status_label.setText("Login successful!")

        # Call login callback
        self.on_login()

    def _on_change_folder(self) -> None:
        """Handle the Change folder link click."""
        self.on_change_folder()

    def _on_forgot_password(self) -> None:
        """Handle the Forgot password link click."""
        dialog = ForgotPasswordDialog(self.window(), self.db)
        result = dialog.show()

        if result:
            # Password was reset successfully
            self.status_label.setStyleSheet(f"color: {COLORS.SUCCESS};")
            self.status_label.setText("Password reset. Please log in with your new password.")

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        # Clear password field
        self.password_entry.clear()
        self.status_label.setText("")
        self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")

        # Focus appropriate field
        if self.username_entry.text():
            self.password_entry.setFocus()
        else:
            self.username_entry.setFocus()

    def clear_form(self) -> None:
        """Clear the login form."""
        self.username_entry.clear()
        self.password_entry.clear()
        self.status_label.setText("")
        self.remember_check.setChecked(False)
