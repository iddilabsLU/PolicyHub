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
        self._parent = parent
        super().__init__(
            parent,
            "Welcome to PolicyHub",
            width=520,
            height=100,  # Initial height, will auto-adjust
            resizable=False,
        )
        self._build_ui()
        self._auto_resize()

    def _auto_resize(self) -> None:
        """Auto-resize dialog to fit content."""
        self.update_idletasks()

        # Get required height based on content
        req_height = self.winfo_reqheight()
        req_width = 520  # Keep width fixed

        # Add some padding
        final_height = max(req_height + 20, 400)

        # Cap at screen size
        screen_height = self.winfo_screenheight()
        final_height = min(final_height, int(screen_height * 0.85))

        # Re-center on parent
        self._parent.update_idletasks()
        px = self._parent.winfo_rootx()
        py = self._parent.winfo_rooty()
        pw = self._parent.winfo_width()
        ph = self._parent.winfo_height()

        x = px + (pw - req_width) // 2
        y = py + (ph - final_height) // 2

        # Ensure on screen
        screen_width = self._parent.winfo_screenwidth()
        x = max(0, min(x, screen_width - req_width))
        y = max(0, min(y, screen_height - final_height))

        self.geometry(f"{req_width}x{final_height}+{x}+{y}")

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        # Main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING)

        # Welcome header
        header = ctk.CTkLabel(
            container,
            text="Welcome to PolicyHub",
            font=TYPOGRAPHY.window_title,
            text_color=COLORS.TEXT_PRIMARY,
        )
        header.pack(pady=(0, 8))

        # Subtitle
        subtitle = ctk.CTkLabel(
            container,
            text="PolicyHub stores documents in a shared database.\nChoose how you want to proceed:",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_SECONDARY,
            justify="center",
        )
        subtitle.pack(pady=(0, 24))

        # Cards container
        cards_frame = ctk.CTkFrame(container, fg_color="transparent")
        cards_frame.pack(fill="both", expand=True)

        # Create New Database card
        self._create_option_card(
            cards_frame,
            title="Create New Database",
            description=(
                "Start fresh with a new database. Choose this if you're setting up PolicyHub "
                "for the first time in your organization, or if you want to create a separate "
                "database for personal use."
            ),
            button_text="Create New",
            command=self._on_create_new,
            icon_text="+"
        )

        # Connect to Existing card
        self._create_option_card(
            cards_frame,
            title="Connect to Existing Database",
            description=(
                "Connect to a database that has already been set up. Choose this if your team "
                "already has a PolicyHub database on a shared network folder, or if you want to "
                "connect to a backup you've restored."
            ),
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
        # Check both in data/ subfolder and directly in folder (for compatibility)
        db_path = Path(folder_path) / "data" / DATABASE_FILENAME
        db_path_alt = Path(folder_path) / DATABASE_FILENAME

        if not db_path.exists() and not db_path_alt.exists():
            from dialogs.confirm_dialog import InfoDialog
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
