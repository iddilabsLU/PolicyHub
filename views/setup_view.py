"""
PolicyHub Setup View

Initial setup wizard for selecting the shared folder path.
Shown when no config.json exists or when the shared path is invalid.
"""

import tkinter.filedialog as filedialog
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

import customtkinter as ctk

from app.constants import APP_NAME
from app.theme import (
    COLORS,
    SPACING,
    TYPOGRAPHY,
    configure_button_style,
    configure_input_style,
)
from core.config import ConfigManager
from utils.files import ensure_shared_folder_structure
from views.base_view import CenteredView

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class SetupView(CenteredView):
    """
    Setup wizard for first-time configuration.

    Allows the user to select a shared folder path for the application.
    """

    def __init__(
        self,
        parent: ctk.CTkFrame,
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
        # Content padding
        content = self.content_frame
        content.configure(width=500)

        # Header
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=(SPACING.CARD_PADDING, 0))

        # Logo/Title
        title_label = ctk.CTkLabel(
            header_frame,
            text=APP_NAME,
            font=TYPOGRAPHY.get_font(24, "bold"),
            text_color=COLORS.PRIMARY,
        )
        title_label.pack(pady=(0, 5))

        subtitle_text = "Create New Database" if self.create_new else "Connect to Database"
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text=subtitle_text,
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_SECONDARY,
        )
        subtitle_label.pack()

        # Divider
        divider = ctk.CTkFrame(content, fg_color=COLORS.BORDER, height=1)
        divider.pack(fill="x", padx=SPACING.CARD_PADDING, pady=SPACING.SECTION_SPACING)

        # Welcome message - different text based on context
        welcome_frame = ctk.CTkFrame(content, fg_color="transparent")
        welcome_frame.pack(fill="x", padx=SPACING.CARD_PADDING)

        if self.create_new:
            welcome_text = (
                "Let's create a new PolicyHub database.\n\n"
                "Choose a folder where the database will be stored. This can be:\n"
                "• A network folder (e.g., \\\\server\\PolicyHub) for team access\n"
                "• A local folder (e.g., C:\\PolicyHub) for personal use"
            )
        else:
            welcome_text = (
                "Let's connect PolicyHub to an existing database.\n\n"
                "Select the folder where your PolicyHub database is located. "
                "If you're unsure, ask your administrator for the correct path."
            )

        welcome_label = ctk.CTkLabel(
            welcome_frame,
            text=welcome_text,
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
            wraplength=450,
            justify="left",
        )
        welcome_label.pack(anchor="w")

        # Error message (if any)
        if error_message:
            error_frame = ctk.CTkFrame(
                content,
                fg_color=COLORS.DANGER_BG,
                corner_radius=SPACING.CORNER_RADIUS,
            )
            error_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=(SPACING.SECTION_SPACING, 0))

            error_label = ctk.CTkLabel(
                error_frame,
                text=error_message,
                font=TYPOGRAPHY.body,
                text_color=COLORS.DANGER,
                wraplength=430,
            )
            error_label.pack(padx=10, pady=10)

        # Path input section
        path_frame = ctk.CTkFrame(content, fg_color="transparent")
        path_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=SPACING.SECTION_SPACING)

        path_label_text = "Database Folder:" if self.create_new else "Database Location:"
        path_label = ctk.CTkLabel(
            path_frame,
            text=path_label_text,
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        path_label.pack(anchor="w", pady=(0, 5))

        # Path entry with browse button
        entry_frame = ctk.CTkFrame(path_frame, fg_color="transparent")
        entry_frame.pack(fill="x")
        entry_frame.grid_columnconfigure(0, weight=1)

        self.path_entry = ctk.CTkEntry(
            entry_frame,
            placeholder_text=r"\\server\PolicyHub or C:\PolicyHub",
            width=350,
        )
        configure_input_style(self.path_entry)
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.browse_button = ctk.CTkButton(
            entry_frame,
            text="Browse",
            width=80,
            command=self._browse_folder,
        )
        configure_button_style(self.browse_button, "secondary")
        self.browse_button.grid(row=0, column=1)

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

        help_label = ctk.CTkLabel(
            path_frame,
            text=help_text,
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
            justify="left",
        )
        help_label.pack(anchor="w", pady=(10, 0))

        # Status label (for validation messages)
        self.status_label = ctk.CTkLabel(
            content,
            text="",
            font=TYPOGRAPHY.small,
            text_color=COLORS.DANGER,
        )
        self.status_label.pack(padx=SPACING.CARD_PADDING)

        # Divider
        divider2 = ctk.CTkFrame(content, fg_color=COLORS.BORDER, height=1)
        divider2.pack(fill="x", padx=SPACING.CARD_PADDING, pady=SPACING.SECTION_SPACING)

        # Connect button
        button_frame = ctk.CTkFrame(content, fg_color="transparent")
        button_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=(0, SPACING.CARD_PADDING))

        button_text = "Create" if self.create_new else "Connect"
        self.connect_button = ctk.CTkButton(
            button_frame,
            text=button_text,
            command=self._on_connect,
            width=120,
        )
        configure_button_style(self.connect_button, "primary")
        self.connect_button.pack(side="right")

    def _browse_folder(self) -> None:
        """Open a folder browser dialog."""
        folder = filedialog.askdirectory(
            title="Select Shared Folder",
            mustexist=True,
        )
        if folder:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)
            self.status_label.configure(text="")

    def _on_connect(self) -> None:
        """Handle the Connect button click."""
        path = self.path_entry.get().strip()

        if not path:
            self.status_label.configure(
                text="Please enter a folder path.",
                text_color=COLORS.DANGER,
            )
            return

        # Validate the path
        is_valid, error = self.config_manager.validate_shared_folder(path)

        if not is_valid:
            self.status_label.configure(
                text=error,
                text_color=COLORS.DANGER,
            )
            return

        # Create folder structure
        if not ensure_shared_folder_structure(Path(path)):
            self.status_label.configure(
                text="Failed to create folder structure.",
                text_color=COLORS.DANGER,
            )
            return

        # Save configuration
        self.config_manager.update(shared_folder_path=path)

        self.status_label.configure(
            text="Connected successfully!",
            text_color=COLORS.SUCCESS,
        )

        # Call completion callback
        self.on_complete()

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        # Focus the path entry
        self.path_entry.focus()
