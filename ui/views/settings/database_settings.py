"""
PolicyHub Database Settings View (PySide6)

Allows users to change database location or create a new database.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QFileDialog,
)

from app.constants import APP_NAME, DATABASE_FILENAME
from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button, style_card
from core.config import ConfigManager
from ui.components.section_card import SectionCard
from ui.dialogs.confirm_dialog import ConfirmDialog, InfoDialog
from ui.views.base_view import BaseView
from utils.files import ensure_shared_folder_structure, get_shared_folder_path

if TYPE_CHECKING:
    from app.application import PolicyHubApp

logger = logging.getLogger(__name__)


class DatabaseSettingsView(BaseView):
    """
    Database management settings view.

    Allows users to:
    - View current database location
    - Change to a different existing database
    - Create a new database at a new location
    """

    def __init__(self, parent: QWidget, app: "PolicyHubApp"):
        """
        Initialize the database settings view.

        Args:
            parent: Parent widget
            app: Main application instance
        """
        super().__init__(parent, app)
        self.config_manager = ConfigManager.get_instance()
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the database settings UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
        )
        layout.setSpacing(0)

        # Scrollable container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(SPACING.SECTION_SPACING)

        # Current Database Card
        self._build_current_database_card(scroll_layout)

        # Change Database Card
        self._build_change_database_card(scroll_layout)

        # Create New Database Card
        self._build_create_database_card(scroll_layout)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def _build_current_database_card(self, parent_layout: QVBoxLayout) -> None:
        """Build the current database information card."""
        card = SectionCard(
            self,
            title="🗄️ Current Database",
            description="The database you are currently connected to"
        )

        # Content container
        content = QWidget()
        content.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        # Path display
        path_label = QLabel("Location:")
        path_label.setFont(TYPOGRAPHY.body)
        path_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        content_layout.addWidget(path_label)

        current_path = get_shared_folder_path()
        path_text = str(current_path) if current_path else "Not configured"

        self.current_path_label = QLabel(path_text)
        self.current_path_label.setFont(TYPOGRAPHY.small)
        self.current_path_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        self.current_path_label.setWordWrap(True)
        content_layout.addWidget(self.current_path_label)

        # File size and last modified
        self.db_info_label = QLabel("")
        self.db_info_label.setFont(TYPOGRAPHY.small)
        self.db_info_label.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; background: transparent;")
        content_layout.addWidget(self.db_info_label)

        card.add_content(content)
        parent_layout.addWidget(card)

    def _get_database_info(self) -> str:
        """Get database file size and last modified info."""
        current_path = get_shared_folder_path()
        if not current_path:
            return ""

        db_file = Path(current_path) / "data" / DATABASE_FILENAME
        if not db_file.exists():
            db_file = Path(current_path) / DATABASE_FILENAME

        if not db_file.exists():
            return ""

        try:
            import os
            from datetime import datetime

            stat = db_file.stat()
            size_bytes = stat.st_size
            modified_time = datetime.fromtimestamp(stat.st_mtime)

            # Format size
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

            # Format time
            time_str = modified_time.strftime("%Y-%m-%d %H:%M")

            return f"Size: {size_str}  •  Last modified: {time_str}"
        except Exception:
            return ""

    def _build_change_database_card(self, parent_layout: QVBoxLayout) -> None:
        """Build the change database card."""
        card = SectionCard(
            self,
            title="Change Database",
            description="Connect to a different existing PolicyHub database (shared or local backup)"
        )

        # Content container
        content = QWidget()
        content.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        # Button
        change_btn = QPushButton("Browse for Database...")
        change_btn.setFixedSize(170, 32)
        style_button(change_btn, "secondary")
        change_btn.clicked.connect(self._on_change_database)
        content_layout.addWidget(change_btn, 0, Qt.AlignmentFlag.AlignLeft)

        # Help text
        help_text = QLabel("You will be logged out after changing the database.")
        help_text.setFont(TYPOGRAPHY.small)
        help_text.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; background: transparent;")
        content_layout.addWidget(help_text)

        card.add_content(content)
        parent_layout.addWidget(card)

    def _build_create_database_card(self, parent_layout: QVBoxLayout) -> None:
        """Build the create new database card."""
        card = SectionCard(
            self,
            title="Create New Database",
            description="Start fresh with a new database at a location of your choice"
        )

        # Content container
        content = QWidget()
        content.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        # Button
        create_btn = QPushButton("Create New Database...")
        create_btn.setFixedSize(170, 32)
        style_button(create_btn, "primary")
        create_btn.clicked.connect(self._on_create_database)
        content_layout.addWidget(create_btn, 0, Qt.AlignmentFlag.AlignLeft)

        # Help text
        help_text = QLabel("You will need to create a new admin account for the new database.")
        help_text.setFont(TYPOGRAPHY.small)
        help_text.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; background: transparent;")
        content_layout.addWidget(help_text)

        card.add_content(content)
        parent_layout.addWidget(card)

    def _on_change_database(self) -> None:
        """Handle change database button click."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select PolicyHub Database Folder",
        )

        if not folder_path:
            return

        # Check if this is the same as the current path
        current_path = get_shared_folder_path()
        if current_path and Path(folder_path).resolve() == Path(current_path).resolve():
            InfoDialog.show_info(
                self.window(),
                "Same Database",
                "You are already connected to this database.",
            )
            return

        # Verify the folder contains a PolicyHub database
        db_file = Path(folder_path) / "data" / DATABASE_FILENAME
        if not db_file.exists():
            db_file_alt = Path(folder_path) / DATABASE_FILENAME
            if not db_file_alt.exists():
                InfoDialog.show_error(
                    self.window(),
                    "Invalid Folder",
                    f"The selected folder does not contain a PolicyHub database.\n\n"
                    f"Expected to find: data/{DATABASE_FILENAME}",
                )
                return

        # Confirm the change
        confirmed = ConfirmDialog.ask(
            self.window(),
            title="Change Database?",
            message=f"You are about to switch to a different database:\n\n{folder_path}\n\n"
            "You will be logged out and need to log in again with credentials "
            "from the selected database.\n\n"
            "Do you want to continue?",
            confirm_text="Yes, Change",
            cancel_text="Cancel",
        )

        if not confirmed:
            return

        self._switch_database(folder_path, is_new=False)

    def _on_create_database(self) -> None:
        """Handle create new database button click."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder for New Database",
        )

        if not folder_path:
            return

        folder = Path(folder_path)

        # Check if folder already contains a database
        db_file = folder / "data" / DATABASE_FILENAME
        if db_file.exists():
            InfoDialog.show_error(
                self.window(),
                "Database Already Exists",
                "The selected folder already contains a PolicyHub database.\n\n"
                "Please choose a different folder or use 'Change Database' to connect to it.",
            )
            return

        # Validate the folder is writable
        is_valid, error = self.config_manager.validate_shared_folder(folder_path)
        if not is_valid:
            InfoDialog.show_error(
                self.window(),
                "Invalid Folder",
                f"Cannot create database in this folder:\n\n{error}",
            )
            return

        # Confirm the creation
        confirmed = ConfirmDialog.ask(
            self.window(),
            title="Create New Database?",
            message=f"You are about to create a new database at:\n\n{folder_path}\n\n"
            "You will be logged out and need to create a new admin account "
            "for the new database.\n\n"
            "Do you want to continue?",
            confirm_text="Yes, Create",
            cancel_text="Cancel",
        )

        if not confirmed:
            return

        # Create folder structure
        if not ensure_shared_folder_structure(folder):
            InfoDialog.show_error(
                self.window(),
                "Error",
                "Failed to create folder structure for the new database.",
            )
            return

        self._switch_database(folder_path, is_new=True)

    def _switch_database(self, folder_path: str, is_new: bool) -> None:
        """
        Switch to a different database.

        Args:
            folder_path: Path to the new database folder
            is_new: True if creating a new database
        """
        from core.database import DatabaseManager
        from core.session import SessionManager

        logger.info(f"Switching database to: {folder_path} (new={is_new})")

        # Update the config with the new path
        self.config_manager.update(shared_folder_path=folder_path)

        # Logout the current user
        session = SessionManager.get_instance()
        session.logout()

        # Reset the database manager singleton
        DatabaseManager.reset_instance()

        # Reconnect through the application
        self.app._connect_database(is_new_database=is_new)

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        # Update the current path display
        current_path = get_shared_folder_path()
        path_text = str(current_path) if current_path else "Not configured"
        self.current_path_label.setText(path_text)

        # Update database info
        db_info = self._get_database_info()
        self.db_info_label.setText(db_info)
