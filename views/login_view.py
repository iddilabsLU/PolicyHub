"""
PolicyHub Login View

User authentication screen.
"""

from typing import TYPE_CHECKING, Callable

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
from core.database import DatabaseManager
from services.auth_service import AuthService
from views.base_view import CenteredView

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class LoginView(CenteredView):
    """
    Login screen for user authentication.
    """

    def __init__(
        self,
        parent: ctk.CTkFrame,
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
        content = self.content_frame
        content.configure(width=400)

        # Header with logo area
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=(SPACING.CARD_PADDING, 0))

        # Logo placeholder (using text for now)
        logo_frame = ctk.CTkFrame(
            header_frame,
            fg_color=COLORS.PRIMARY,
            corner_radius=SPACING.CORNER_RADIUS_LARGE,
            width=60,
            height=60,
        )
        logo_frame.pack(pady=(0, 10))
        logo_frame.pack_propagate(False)

        logo_text = ctk.CTkLabel(
            logo_frame,
            text="PH",
            font=TYPOGRAPHY.get_font(24, "bold"),
            text_color=COLORS.PRIMARY_FOREGROUND,
        )
        logo_text.place(relx=0.5, rely=0.5, anchor="center")

        title_label = ctk.CTkLabel(
            header_frame,
            text=APP_NAME,
            font=TYPOGRAPHY.get_font(20, "bold"),
            text_color=COLORS.PRIMARY,
        )
        title_label.pack()

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Policy & Procedure Manager",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_SECONDARY,
        )
        subtitle_label.pack(pady=(5, 0))

        # Form
        form_frame = ctk.CTkFrame(content, fg_color="transparent")
        form_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=SPACING.SECTION_SPACING)

        # Username
        username_label = ctk.CTkLabel(
            form_frame,
            text="Username:",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        username_label.pack(anchor="w", pady=(0, 5))

        self.username_entry = ctk.CTkEntry(form_frame)
        configure_input_style(self.username_entry)
        self.username_entry.pack(fill="x", pady=(0, 15))

        # Password
        password_label = ctk.CTkLabel(
            form_frame,
            text="Password:",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        password_label.pack(anchor="w", pady=(0, 5))

        self.password_entry = ctk.CTkEntry(form_frame, show="*")
        configure_input_style(self.password_entry)
        self.password_entry.pack(fill="x", pady=(0, 15))
        self.password_entry.bind("<Return>", lambda e: self._on_login())

        # Remember username checkbox
        self.remember_var = ctk.BooleanVar(value=False)
        self.remember_check = ctk.CTkCheckBox(
            form_frame,
            text="Remember my username",
            variable=self.remember_var,
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
            fg_color=COLORS.PRIMARY,
            hover_color=COLORS.PRIMARY_HOVER,
            border_color=COLORS.INPUT_BORDER,
        )
        self.remember_check.pack(anchor="w")

        # Status/error label
        self.status_label = ctk.CTkLabel(
            content,
            text="",
            font=TYPOGRAPHY.small,
            text_color=COLORS.DANGER,
        )
        self.status_label.pack(padx=SPACING.CARD_PADDING, pady=(10, 0))

        # Login button
        self.login_button = ctk.CTkButton(
            content,
            text="Login",
            command=self._on_login,
            width=120,
        )
        configure_button_style(self.login_button, "primary")
        self.login_button.pack(pady=SPACING.SECTION_SPACING)

        # Divider
        divider = ctk.CTkFrame(content, fg_color=COLORS.BORDER, height=1)
        divider.pack(fill="x", padx=SPACING.CARD_PADDING)

        # Footer with connection info
        footer_frame = ctk.CTkFrame(content, fg_color="transparent")
        footer_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        # Get shared folder path
        config = self.config_manager.load()
        folder_path = config.shared_folder_path or "Not configured"

        # Truncate long paths
        if len(folder_path) > 35:
            folder_path = "..." + folder_path[-32:]

        connection_label = ctk.CTkLabel(
            footer_frame,
            text=f"Connected to: {folder_path}",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_MUTED,
        )
        connection_label.pack(side="left")

        change_button = ctk.CTkButton(
            footer_frame,
            text="Change...",
            command=self._on_change_folder,
            width=70,
            height=24,
            font=TYPOGRAPHY.small,
            fg_color="transparent",
            text_color=COLORS.PRIMARY,
            hover_color=COLORS.MUTED,
        )
        change_button.pack(side="right")

    def _load_remembered_username(self) -> None:
        """Load the remembered username from config."""
        config = self.config_manager.load()
        if config.remembered_username:
            self.username_entry.insert(0, config.remembered_username)
            self.remember_var.set(True)
            # Focus password field since username is pre-filled
            self.password_entry.focus()
        else:
            self.username_entry.focus()

    def _on_login(self) -> None:
        """Handle the Login button click."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username:
            self.status_label.configure(text="Please enter your username.")
            return

        if not password:
            self.status_label.configure(text="Please enter your password.")
            return

        # Attempt authentication
        session = self.auth_service.login(username, password)

        if session is None:
            self.status_label.configure(text="Invalid username or password.")
            self.password_entry.delete(0, "end")
            self.password_entry.focus()
            return

        # Handle "remember username"
        if self.remember_var.get():
            self.config_manager.update(remembered_username=username)
        else:
            self.config_manager.clear_remembered_username()

        self.status_label.configure(
            text="Login successful!",
            text_color=COLORS.SUCCESS,
        )

        # Call login callback
        self.on_login()

    def _on_change_folder(self) -> None:
        """Handle the Change folder link click."""
        self.on_change_folder()

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        # Clear password field
        self.password_entry.delete(0, "end")
        self.status_label.configure(text="")

        # Focus appropriate field
        if self.username_entry.get():
            self.password_entry.focus()
        else:
            self.username_entry.focus()

    def clear_form(self) -> None:
        """Clear the login form."""
        self.username_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.status_label.configure(text="")
        self.remember_var.set(False)
