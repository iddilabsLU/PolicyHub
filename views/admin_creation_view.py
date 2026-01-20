"""
PolicyHub Admin Creation View

First-time admin account creation screen.
Shown when the database exists but has no users.
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
from core.database import DatabaseManager
from services.auth_service import AuthService
from utils.validators import (
    validate_email,
    validate_full_name,
    validate_password,
    validate_passwords_match,
    validate_username,
)
from views.base_view import CenteredView

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class AdminCreationView(CenteredView):
    """
    Admin account creation screen for first-time setup.

    Creates the first admin user who will manage the system.
    """

    def __init__(
        self,
        parent: ctk.CTkFrame,
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
        content = self.content_frame
        content.configure(width=500)

        # Header
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=(SPACING.CARD_PADDING, 0))

        title_label = ctk.CTkLabel(
            header_frame,
            text=APP_NAME,
            font=TYPOGRAPHY.get_font(24, "bold"),
            text_color=COLORS.PRIMARY,
        )
        title_label.pack(pady=(0, 5))

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Create Administrator Account",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_SECONDARY,
        )
        subtitle_label.pack()

        # Divider
        divider = ctk.CTkFrame(content, fg_color=COLORS.BORDER, height=1)
        divider.pack(fill="x", padx=SPACING.CARD_PADDING, pady=SPACING.SECTION_SPACING)

        # Info message
        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(fill="x", padx=SPACING.CARD_PADDING)

        info_label = ctk.CTkLabel(
            info_frame,
            text="You're the first user. Create an admin account to get started.",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
            wraplength=450,
        )
        info_label.pack(anchor="w")

        # Form
        form_frame = ctk.CTkFrame(content, fg_color="transparent")
        form_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=SPACING.SECTION_SPACING)

        # Username
        self._create_field(form_frame, "Username:", 0)
        self.username_entry = ctk.CTkEntry(form_frame, placeholder_text="admin")
        configure_input_style(self.username_entry)
        self.username_entry.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        # Full Name
        self._create_field(form_frame, "Full Name:", 2)
        self.fullname_entry = ctk.CTkEntry(form_frame, placeholder_text="John Smith")
        configure_input_style(self.fullname_entry)
        self.fullname_entry.grid(row=3, column=0, sticky="ew", pady=(0, 15))

        # Email (required)
        self._create_field(form_frame, "Email *", 4)
        self.email_entry = ctk.CTkEntry(form_frame, placeholder_text="j.smith@company.lu")
        configure_input_style(self.email_entry)
        self.email_entry.grid(row=5, column=0, sticky="ew", pady=(0, 15))

        # Password
        self._create_field(form_frame, "Password:", 6)
        self.password_entry = ctk.CTkEntry(form_frame, placeholder_text="", show="*")
        configure_input_style(self.password_entry)
        self.password_entry.grid(row=7, column=0, sticky="ew", pady=(0, 15))

        # Confirm Password
        self._create_field(form_frame, "Confirm Password:", 8)
        self.confirm_entry = ctk.CTkEntry(form_frame, placeholder_text="", show="*")
        configure_input_style(self.confirm_entry)
        self.confirm_entry.grid(row=9, column=0, sticky="ew", pady=(0, 5))

        # Password hint
        hint_label = ctk.CTkLabel(
            form_frame,
            text="Minimum 8 characters",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        )
        hint_label.grid(row=10, column=0, sticky="w")

        form_frame.grid_columnconfigure(0, weight=1)

        # Status/error label
        self.status_label = ctk.CTkLabel(
            content,
            text="",
            font=TYPOGRAPHY.small,
            text_color=COLORS.DANGER,
            wraplength=450,
        )
        self.status_label.pack(padx=SPACING.CARD_PADDING, pady=(10, 0))

        # Divider
        divider2 = ctk.CTkFrame(content, fg_color=COLORS.BORDER, height=1)
        divider2.pack(fill="x", padx=SPACING.CARD_PADDING, pady=SPACING.SECTION_SPACING)

        # Create button
        button_frame = ctk.CTkFrame(content, fg_color="transparent")
        button_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=(0, SPACING.CARD_PADDING))

        self.create_button = ctk.CTkButton(
            button_frame,
            text="Create & Login",
            command=self._on_create,
            width=140,
        )
        configure_button_style(self.create_button, "primary")
        self.create_button.pack(side="right")

    def _create_field(self, parent: ctk.CTkFrame, label: str, row: int) -> None:
        """Create a form field label."""
        label_widget = ctk.CTkLabel(
            parent,
            text=label,
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        label_widget.grid(row=row, column=0, sticky="w", pady=(0, 5))

    def _on_create(self) -> None:
        """Handle the Create button click."""
        username = self.username_entry.get().strip()
        full_name = self.fullname_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()

        # Validate username
        valid, error = validate_username(username)
        if not valid:
            self.status_label.configure(text=error, text_color=COLORS.DANGER)
            return

        # Validate full name
        valid, error = validate_full_name(full_name)
        if not valid:
            self.status_label.configure(text=error, text_color=COLORS.DANGER)
            return

        # Validate email (required)
        if not email:
            self.status_label.configure(text="Email is required.", text_color=COLORS.DANGER)
            return

        valid, error = validate_email(email)
        if not valid:
            self.status_label.configure(text=error, text_color=COLORS.DANGER)
            return

        # Validate password
        valid, error = validate_password(password)
        if not valid:
            self.status_label.configure(text=error, text_color=COLORS.DANGER)
            return

        # Validate passwords match
        valid, error = validate_passwords_match(password, confirm)
        if not valid:
            self.status_label.configure(text=error, text_color=COLORS.DANGER)
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
            # This is a new database, so login should not be required by default
            from services.settings_service import SettingsService
            settings_service = SettingsService(self.db)
            settings_service.set_require_login_direct(False)

            # Auto-login
            self.auth_service.login(username, password)

            # Seed sample documents for testing
            from services.document_service import DocumentService
            doc_service = DocumentService(self.db)
            doc_service.seed_sample_documents()

            self.status_label.configure(
                text="Account created successfully!",
                text_color=COLORS.SUCCESS,
            )

            # Call completion callback
            self.on_complete()

        except Exception as e:
            self.status_label.configure(
                text=f"Error: {str(e)}",
                text_color=COLORS.DANGER,
            )

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        self.username_entry.focus()
