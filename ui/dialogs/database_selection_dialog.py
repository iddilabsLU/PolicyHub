"""
PolicyHub Database Selection Dialog (PySide6)

Dialog for choosing between creating a new database or connecting to an existing one.
Shown on first run when no database is configured.
"""

from pathlib import Path
from typing import Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.constants import DATABASE_FILENAME
from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button
from ui.dialogs.base_dialog import BaseDialog


# Result constants
RESULT_CREATE_NEW = "CREATE_NEW"
RESULT_CONNECT = "CONNECT"
RESULT_CANCELLED = "CANCELLED"


class DatabaseSelectionDialog(BaseDialog):
    """
    Dialog for selecting database mode on first run.

    Shows two card options:
    - Create New Database: Start fresh with the setup wizard
    - Connect to Existing: Browse for an existing database folder

    Result:
    - (RESULT_CREATE_NEW, None) - User chose to create new database
    - (RESULT_CONNECT, folder_path) - User chose to connect to existing
    - (RESULT_CANCELLED, None) - User cancelled the dialog
    """

    def __init__(self, parent):
        """
        Initialize the database selection dialog.

        Args:
            parent: Parent window
        """
        super().__init__(
            parent,
            "Welcome to PolicyHub",
            width=520,
            height=520,
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

        # Welcome header
        header = QLabel("Welcome to PolicyHub")
        header.setFont(TYPOGRAPHY.window_title)
        header.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        layout.addSpacing(8)

        # Subtitle
        subtitle = QLabel("PolicyHub stores documents in a shared database.\nChoose how you want to proceed:")
        subtitle.setFont(TYPOGRAPHY.body)
        subtitle.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        layout.addSpacing(24)

        # Create New Database card
        self._create_option_card(
            layout,
            title="Create New Database",
            description=(
                "Start fresh with a new database. Choose this if you're setting up PolicyHub "
                "for the first time in your organization, or if you want to create a separate "
                "database for personal use."
            ),
            button_text="Create New",
            on_click=self._on_create_new,
            icon_text="+"
        )

        layout.addSpacing(12)

        # Connect to Existing card
        self._create_option_card(
            layout,
            title="Connect to Existing Database",
            description=(
                "Connect to a database that has already been set up. Choose this if your team "
                "already has a PolicyHub database on a shared network folder, or if you want to "
                "connect to a backup you've restored."
            ),
            button_text="Browse...",
            on_click=self._on_connect_existing,
            icon_text="..."
        )

        layout.addStretch()

    def _create_option_card(
        self,
        parent_layout: QVBoxLayout,
        title: str,
        description: str,
        button_text: str,
        on_click,
        icon_text: str,
    ) -> None:
        """Create an option card with title, description, and button."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.CARD};
                border-radius: 8px;
                border: none;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(8)

        # Header row with icon and title
        header_row = QWidget()
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        # Icon circle
        icon_frame = QFrame()
        icon_frame.setFixedSize(32, 32)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.PRIMARY};
                border-radius: 16px;
            }}
        """)
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        icon_label = QLabel(icon_text)
        icon_label.setFont(TYPOGRAPHY.body)
        icon_label.setStyleSheet(f"color: #FFFFFF; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(icon_label)

        header_layout.addWidget(icon_frame)

        # Title
        title_label = QLabel(title)
        title_label.setFont(TYPOGRAPHY.section_heading)
        title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        card_layout.addWidget(header_row)

        # Description
        desc_label = QLabel(description)
        desc_label.setFont(TYPOGRAPHY.small)
        desc_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        desc_label.setWordWrap(True)
        card_layout.addWidget(desc_label)

        # Button
        btn = QPushButton(button_text)
        btn.setFixedWidth(120)
        btn.clicked.connect(on_click)
        style_button(btn, "primary")
        card_layout.addWidget(btn)

        parent_layout.addWidget(card)

    def _on_create_new(self) -> None:
        """Handle Create New Database button click."""
        self.result = (RESULT_CREATE_NEW, None)
        self.accept()

    def _on_connect_existing(self) -> None:
        """Handle Connect to Existing button click."""
        # Open folder browser
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select PolicyHub Database Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if not folder_path:
            # User cancelled folder selection
            return

        # Verify the folder contains a PolicyHub database
        # Check both in data/ subfolder and directly in folder (for compatibility)
        db_path = Path(folder_path) / "data" / DATABASE_FILENAME
        db_path_alt = Path(folder_path) / DATABASE_FILENAME

        if not db_path.exists() and not db_path_alt.exists():
            from ui.dialogs.confirm_dialog import InfoDialog
            InfoDialog.show_error(
                self,
                "No Database Found",
                f"The selected folder does not contain a PolicyHub database.\n\n"
                f"Make sure you select the main PolicyHub folder that contains "
                f"the 'data' subfolder with the database file.\n\n"
                f"If you want to create a new database, click 'Create New' instead."
            )
            return

        self.result = (RESULT_CONNECT, folder_path)
        self.accept()

    def _on_cancel(self) -> None:
        """Handle cancel/close action."""
        self.result = (RESULT_CANCELLED, None)
        self.reject()

    def show(self) -> Tuple[str, Optional[str]]:
        """
        Show the dialog and wait for result.

        Returns:
            Tuple of (result_type, folder_path or None)
        """
        self.exec()
        return self.result if self.result else (RESULT_CANCELLED, None)
