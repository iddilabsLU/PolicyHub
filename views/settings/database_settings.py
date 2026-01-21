"""
PolicyHub Database Settings View

Allows users to change database location or create a new database.
"""

import logging
from pathlib import Path
from tkinter import filedialog
from typing import TYPE_CHECKING

import customtkinter as ctk

from app.constants import APP_NAME, DATABASE_FILENAME
from app.theme import (
    COLORS,
    SPACING,
    TYPOGRAPHY,
    configure_button_style,
    configure_card_style,
)
from core.config import ConfigManager
from dialogs.confirm_dialog import ConfirmDialog, InfoDialog
from utils.files import ensure_shared_folder_structure, get_shared_folder_path
from views.base_view import BaseView

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

    def __init__(self, parent: ctk.CTkFrame, app: "PolicyHubApp"):
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
        # Scrollable container
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(
            fill="both", expand=True, padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING
        )

        # Current Database Card
        self._build_current_database_card(scroll)

        # Change Database Card
        self._build_change_database_card(scroll)

        # Create New Database Card
        self._build_create_database_card(scroll)

    def _build_current_database_card(self, parent: ctk.CTkFrame) -> None:
        """Build the current database information card."""
        card = ctk.CTkFrame(parent, fg_color=COLORS.CARD)
        configure_card_style(card, with_shadow=True)
        card.pack(fill="x", pady=(0, SPACING.SECTION_SPACING))

        # Title
        title = ctk.CTkLabel(
            card,
            text="Current Database",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title.pack(anchor="w", padx=SPACING.CARD_PADDING, pady=(SPACING.CARD_PADDING, 8))

        # Description
        desc = ctk.CTkLabel(
            card,
            text="The database you are currently connected to.",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        )
        desc.pack(anchor="w", padx=SPACING.CARD_PADDING, pady=(0, SPACING.CARD_PADDING))

        # Divider
        divider = ctk.CTkFrame(card, fg_color=COLORS.BORDER, height=1)
        divider.pack(fill="x", padx=SPACING.CARD_PADDING)

        # Database path display
        path_frame = ctk.CTkFrame(card, fg_color="transparent")
        path_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        path_label = ctk.CTkLabel(
            path_frame,
            text="Location:",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        path_label.pack(anchor="w")

        # Get current path
        current_path = get_shared_folder_path()
        path_text = str(current_path) if current_path else "Not configured"

        self.current_path_label = ctk.CTkLabel(
            path_frame,
            text=path_text,
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
            wraplength=500,
            justify="left",
        )
        self.current_path_label.pack(anchor="w", pady=(4, 0))

    def _build_change_database_card(self, parent: ctk.CTkFrame) -> None:
        """Build the change database card."""
        card = ctk.CTkFrame(parent, fg_color=COLORS.CARD)
        configure_card_style(card, with_shadow=True)
        card.pack(fill="x", pady=(0, SPACING.SECTION_SPACING))

        # Title
        title = ctk.CTkLabel(
            card,
            text="Change Database",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title.pack(anchor="w", padx=SPACING.CARD_PADDING, pady=(SPACING.CARD_PADDING, 8))

        # Description
        desc = ctk.CTkLabel(
            card,
            text=(
                "Connect to a different existing PolicyHub database. "
                "Use this option when you want to work with a database that has already been set up "
                "(for example, a shared database on your network or a local backup you want to restore)."
            ),
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
            wraplength=500,
            justify="left",
        )
        desc.pack(anchor="w", padx=SPACING.CARD_PADDING, pady=(0, SPACING.CARD_PADDING))

        # Divider
        divider = ctk.CTkFrame(card, fg_color=COLORS.BORDER, height=1)
        divider.pack(fill="x", padx=SPACING.CARD_PADDING)

        # Button
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        change_btn = ctk.CTkButton(
            btn_frame,
            text="Browse for Database...",
            command=self._on_change_database,
            width=180,
        )
        configure_button_style(change_btn, "secondary")
        change_btn.pack(anchor="w")

        # Help text
        help_text = ctk.CTkLabel(
            btn_frame,
            text="You will be logged out after changing the database.",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_MUTED,
        )
        help_text.pack(anchor="w", pady=(8, 0))

    def _build_create_database_card(self, parent: ctk.CTkFrame) -> None:
        """Build the create new database card."""
        card = ctk.CTkFrame(parent, fg_color=COLORS.CARD)
        configure_card_style(card, with_shadow=True)
        card.pack(fill="x", pady=(0, SPACING.SECTION_SPACING))

        # Title
        title = ctk.CTkLabel(
            card,
            text="Create New Database",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title.pack(anchor="w", padx=SPACING.CARD_PADDING, pady=(SPACING.CARD_PADDING, 8))

        # Description
        desc = ctk.CTkLabel(
            card,
            text=(
                "Start fresh with a new PolicyHub database at a location of your choice. "
                "Use this option if you want to create a completely separate database "
                "(for example, for a different organization or to work locally on your own)."
            ),
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
            wraplength=500,
            justify="left",
        )
        desc.pack(anchor="w", padx=SPACING.CARD_PADDING, pady=(0, SPACING.CARD_PADDING))

        # Divider
        divider = ctk.CTkFrame(card, fg_color=COLORS.BORDER, height=1)
        divider.pack(fill="x", padx=SPACING.CARD_PADDING)

        # Button
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        create_btn = ctk.CTkButton(
            btn_frame,
            text="Create New Database...",
            command=self._on_create_database,
            width=180,
        )
        configure_button_style(create_btn, "primary")
        create_btn.pack(anchor="w")

        # Help text
        help_text = ctk.CTkLabel(
            btn_frame,
            text="You will need to create a new admin account for the new database.",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_MUTED,
        )
        help_text.pack(anchor="w", pady=(8, 0))

    def _on_change_database(self) -> None:
        """Handle change database button click."""
        # Open folder browser
        folder_path = filedialog.askdirectory(
            title="Select PolicyHub Database Folder",
            parent=self.winfo_toplevel(),
        )

        if not folder_path:
            # User cancelled
            return

        # Check if this is the same as the current path
        current_path = get_shared_folder_path()
        if current_path and Path(folder_path).resolve() == Path(current_path).resolve():
            InfoDialog.show_info(
                self.winfo_toplevel(),
                "Same Database",
                "You are already connected to this database.",
            )
            return

        # Verify the folder contains a PolicyHub database
        db_file = Path(folder_path) / "data" / DATABASE_FILENAME
        if not db_file.exists():
            # Also check if database is directly in the folder (old structure)
            db_file_alt = Path(folder_path) / DATABASE_FILENAME
            if not db_file_alt.exists():
                InfoDialog.show_error(
                    self.winfo_toplevel(),
                    "Invalid Folder",
                    f"The selected folder does not contain a PolicyHub database.\n\n"
                    f"Expected to find: data/{DATABASE_FILENAME}",
                )
                return

        # Confirm the change
        confirmed = ConfirmDialog.ask(
            self.winfo_toplevel(),
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

        # Perform the database switch
        self._switch_database(folder_path, is_new=False)

    def _on_create_database(self) -> None:
        """Handle create new database button click."""
        # Open folder browser for saving
        folder_path = filedialog.askdirectory(
            title="Select Folder for New Database",
            parent=self.winfo_toplevel(),
        )

        if not folder_path:
            # User cancelled
            return

        folder = Path(folder_path)

        # Check if folder already contains a database
        db_file = folder / "data" / DATABASE_FILENAME
        if db_file.exists():
            InfoDialog.show_error(
                self.winfo_toplevel(),
                "Database Already Exists",
                "The selected folder already contains a PolicyHub database.\n\n"
                "Please choose a different folder or use 'Change Database' to connect to it.",
            )
            return

        # Validate the folder is writable
        is_valid, error = self.config_manager.validate_shared_folder(folder_path)
        if not is_valid:
            InfoDialog.show_error(
                self.winfo_toplevel(),
                "Invalid Folder",
                f"Cannot create database in this folder:\n\n{error}",
            )
            return

        # Confirm the creation
        confirmed = ConfirmDialog.ask(
            self.winfo_toplevel(),
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
                self.winfo_toplevel(),
                "Error",
                "Failed to create folder structure for the new database.",
            )
            return

        # Perform the database switch
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
        # This will handle schema initialization and show login/admin creation as needed
        self.app._connect_database(is_new_database=is_new)

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        # Update the current path display
        current_path = get_shared_folder_path()
        path_text = str(current_path) if current_path else "Not configured"
        self.current_path_label.configure(text=path_text)
