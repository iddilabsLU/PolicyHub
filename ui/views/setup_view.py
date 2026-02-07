"""
PolicyHub Setup View (PySide6)

Initial setup wizard for selecting the shared folder path.
Shown when no config.json exists or when the shared path is invalid.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
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
from core.config import ConfigManager
from ui.views.base_view import CenteredView
from utils.files import ensure_shared_folder_structure

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class SetupView(CenteredView):
    """
    Setup wizard for first-time configuration.

    Allows the user to select a shared folder path for the application.
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        app: "PolicyHubApp",
        on_complete: Callable[[], None],
        error_message: Optional[str] = None,
        create_new: bool = False,
    ):
        """
        Initialize the setup view.

        Args:
            parent: Parent widget
            app: Main application instance
            on_complete: Callback when setup is complete
            error_message: Optional error message to display
            create_new: True if creating a new database (affects default settings)
        """
        super().__init__(parent, app, max_width=500)
        self.on_complete = on_complete
        self.config_manager = ConfigManager.get_instance()
        self.create_new = create_new

        self._build_ui(error_message)

    def _build_ui(self, error_message: Optional[str] = None) -> None:
        """Build the setup UI."""
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

        subtitle_text = "Create New Database" if self.create_new else "Connect to Database"
        subtitle_label = QLabel(subtitle_text)
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

        # Welcome message - different text based on context
        if self.create_new:
            welcome_text = (
                "Let's create a new PolicyHub database.\n\n"
                "Choose a folder where the database will be stored. This can be:\n"
                "- A network folder (e.g., \\\\server\\PolicyHub) for team access\n"
                "- A local folder (e.g., C:\\PolicyHub) for personal use"
            )
        else:
            welcome_text = (
                "Let's connect PolicyHub to an existing database.\n\n"
                "Select the folder where your PolicyHub database is located. "
                "If you're unsure, ask your administrator for the correct path."
            )

        welcome_label = QLabel(welcome_text)
        welcome_label.setFont(TYPOGRAPHY.body)
        welcome_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        welcome_label.setWordWrap(True)
        layout.addWidget(welcome_label)

        # Error message (if any)
        if error_message:
            error_frame = QFrame()
            error_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS.DANGER_BG};
                    border-radius: {SPACING.CORNER_RADIUS}px;
                }}
            """)
            error_layout = QVBoxLayout(error_frame)
            error_layout.setContentsMargins(10, 10, 10, 10)

            error_label = QLabel(error_message)
            error_label.setFont(TYPOGRAPHY.body)
            error_label.setStyleSheet(f"color: {COLORS.DANGER}; background: transparent;")
            error_label.setWordWrap(True)
            error_layout.addWidget(error_label)

            layout.addSpacing(SPACING.SECTION_SPACING)
            layout.addWidget(error_frame)

        # Path input section
        layout.addSpacing(SPACING.SECTION_SPACING)

        path_label_text = "Database Folder:" if self.create_new else "Database Location:"
        path_label = QLabel(path_label_text)
        path_label.setFont(TYPOGRAPHY.body)
        path_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        layout.addWidget(path_label)
        layout.addSpacing(5)

        # Path entry with browse button
        entry_frame = QWidget()
        entry_layout = QHBoxLayout(entry_frame)
        entry_layout.setContentsMargins(0, 0, 0, 0)
        entry_layout.setSpacing(10)

        self.path_entry = QLineEdit()
        self.path_entry.setPlaceholderText(r"\\server\PolicyHub or C:\PolicyHub")
        self.path_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        entry_layout.addWidget(self.path_entry)

        self.browse_button = QPushButton("Browse")
        self.browse_button.setFixedWidth(80)
        self.browse_button.clicked.connect(self._browse_folder)
        style_button(self.browse_button, "secondary")
        entry_layout.addWidget(self.browse_button)

        layout.addWidget(entry_frame)

        # Help text - different based on context
        if self.create_new:
            help_text = (
                "The folder must already exist and you must have write permission.\n"
                "PolicyHub will create subfolders for data, attachments, and exports."
            )
        else:
            help_text = (
                "Select the main PolicyHub folder that contains the 'data' subfolder.\n"
                "Ask your administrator if you don't know the path."
            )

        help_label = QLabel(help_text)
        help_label.setFont(TYPOGRAPHY.small)
        help_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        layout.addSpacing(10)
        layout.addWidget(help_label)

        # Status label (for validation messages)
        self.status_label = QLabel("")
        self.status_label.setFont(TYPOGRAPHY.small)
        self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
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

        # Connect button
        button_frame = QWidget()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()

        button_text = "Create" if self.create_new else "Connect"
        self.connect_button = QPushButton(button_text)
        self.connect_button.setFixedWidth(120)
        self.connect_button.clicked.connect(self._on_connect)
        style_button(self.connect_button, "primary")
        button_layout.addWidget(self.connect_button)

        layout.addWidget(button_frame)

    def _browse_folder(self) -> None:
        """Open a folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Shared Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.path_entry.setText(folder)
            self.status_label.setText("")

    def _on_connect(self) -> None:
        """Handle the Connect button click."""
        path = self.path_entry.text().strip()

        if not path:
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
            self.status_label.setText("Please enter a folder path.")
            return

        # Validate the path
        is_valid, error = self.config_manager.validate_shared_folder(path)

        if not is_valid:
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
            self.status_label.setText(error)
            return

        # Create folder structure
        if not ensure_shared_folder_structure(Path(path)):
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER};")
            self.status_label.setText("Failed to create folder structure.")
            return

        # Save configuration
        self.config_manager.update(shared_folder_path=path)

        self.status_label.setStyleSheet(f"color: {COLORS.SUCCESS};")
        self.status_label.setText("Connected successfully!")

        # Call completion callback
        self.on_complete()

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        # Focus the path entry
        self.path_entry.setFocus()
