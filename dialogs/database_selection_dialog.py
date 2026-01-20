"""
PolicyHub Database Selection Dialog

Dialog for choosing between creating a new database or connecting to an existing one.
Shown on first run when no database is configured.
"""

from pathlib import Path
from tkinter import filedialog
from typing import Optional, Tuple

import customtkinter as ctk

from app.constants import DATABASE_FILENAME
from app.theme import COLORS, SPACING, TYPOGRAPHY, configure_button_style
from dialogs.base_dialog import BaseDialog


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
            width=500,
            height=400,
            resizable=False,
        )
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        # Main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING)

        # Welcome header
        header = ctk.CTkLabel(
            container,
            text="Welcome to PolicyHub",
            font=TYPOGRAPHY.page_title,
            text_color=COLORS.TEXT_PRIMARY,
        )
        header.pack(pady=(0, 8))

        # Subtitle
        subtitle = ctk.CTkLabel(
            container,
            text="How would you like to get started?",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_SECONDARY,
        )
        subtitle.pack(pady=(0, 24))

        # Cards container
        cards_frame = ctk.CTkFrame(container, fg_color="transparent")
        cards_frame.pack(fill="both", expand=True)

        # Create New Database card
        self._create_option_card(
            cards_frame,
            title="Create New Database",
            description="Start fresh with a new PolicyHub database. You'll set up the storage location and create an admin account.",
            button_text="Create New",
            command=self._on_create_new,
            icon_text="+"
        )

        # Connect to Existing card
        self._create_option_card(
            cards_frame,
            title="Connect to Existing",
            description="Connect to an existing PolicyHub database folder. Choose this if you've already set up PolicyHub before.",
            button_text="Browse...",
            command=self._on_connect_existing,
            icon_text="..."
        )

    def _create_option_card(
        self,
        parent,
        title: str,
        description: str,
        button_text: str,
        command,
        icon_text: str,
    ) -> None:
        """Create an option card with title, description, and button."""
        card = ctk.CTkFrame(parent, fg_color=COLORS.CARD, corner_radius=8)
        card.pack(fill="x", pady=(0, 12))

        # Card content
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=16, pady=16)

        # Header row with icon and title
        header_row = ctk.CTkFrame(content, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 8))

        # Icon circle
        icon_frame = ctk.CTkFrame(
            header_row,
            width=32,
            height=32,
            fg_color=COLORS.PRIMARY,
            corner_radius=16,
        )
        icon_frame.pack(side="left", padx=(0, 12))
        icon_frame.pack_propagate(False)

        icon_label = ctk.CTkLabel(
            icon_frame,
            text=icon_text,
            font=TYPOGRAPHY.body,
            text_color="#FFFFFF",
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        title_label = ctk.CTkLabel(
            header_row,
            text=title,
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title_label.pack(side="left")

        # Description
        desc_label = ctk.CTkLabel(
            content,
            text=description,
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
            wraplength=400,
            justify="left",
        )
        desc_label.pack(anchor="w", pady=(0, 12))

        # Button
        btn = ctk.CTkButton(
            content,
            text=button_text,
            command=command,
            width=120,
        )
        configure_button_style(btn, "primary")
        btn.pack(anchor="w")

    def _on_create_new(self) -> None:
        """Handle Create New Database button click."""
        self.result = (RESULT_CREATE_NEW, None)
        self.destroy()

    def _on_connect_existing(self) -> None:
        """Handle Connect to Existing button click."""
        # Open folder browser
        folder_path = filedialog.askdirectory(
            title="Select PolicyHub Database Folder",
            parent=self,
        )

        if not folder_path:
            # User cancelled folder selection
            return

        # Verify the folder contains a PolicyHub database
        db_path = Path(folder_path) / DATABASE_FILENAME
        if not db_path.exists():
            from dialogs.confirm_dialog import InfoDialog
            InfoDialog.show_error(
                self,
                "Invalid Folder",
                f"The selected folder does not contain a PolicyHub database.\n\n"
                f"Expected to find: {DATABASE_FILENAME}"
            )
            return

        self.result = (RESULT_CONNECT, folder_path)
        self.destroy()

    def _on_cancel(self) -> None:
        """Handle cancel/close action."""
        self.result = (RESULT_CANCELLED, None)
        self.destroy()

    def show(self) -> Tuple[str, Optional[str]]:
        """
        Show the dialog and wait for result.

        Returns:
            Tuple of (result_type, folder_path or None)
        """
        self.wait_window()
        return self.result if self.result else (RESULT_CANCELLED, None)
