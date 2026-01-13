"""
PolicyHub Force Password Change View

Displayed when a user must change their password on first login
or after an admin password reset.
"""

from typing import TYPE_CHECKING, Callable

import customtkinter as ctk

from app.constants import MIN_PASSWORD_LENGTH
from app.theme import (
    COLORS,
    SPACING,
    TYPOGRAPHY,
    configure_button_style,
    configure_input_style,
)
from core.database import DatabaseManager
from core.session import SessionManager
from services.auth_service import AuthService
from views.base_view import CenteredView

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class ForcePasswordChangeView(CenteredView):
    """
    Force password change screen.

    Displayed after login when the user's force_password_change flag is set.
    User must set a new password before proceeding to the main application.
    """

    def __init__(
        self,
        parent: ctk.CTkFrame,
        app: "PolicyHubApp",
        db: DatabaseManager,
        on_password_changed: Callable[[], None],
    ):
        """
        Initialize the force password change view.

        Args:
            parent: Parent widget
            app: Main application instance
            db: Database manager
            on_password_changed: Callback when password is successfully changed
        """
        super().__init__(parent, app, max_width=420)
        self.db = db
        self.auth_service = AuthService(db)
        self.session_manager = SessionManager.get_instance()
        self.on_password_changed = on_password_changed

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the password change UI."""
        content = self.content_frame
        content.configure(width=420)

        # Header
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=(SPACING.CARD_PADDING, 0))

        # Icon (lock symbol)
        icon_frame = ctk.CTkFrame(
            header_frame,
            fg_color=COLORS.WARNING,
            corner_radius=SPACING.CORNER_RADIUS_LARGE,
            width=50,
            height=50,
        )
        icon_frame.pack(pady=(0, 10))
        icon_frame.pack_propagate(False)

        icon_text = ctk.CTkLabel(
            icon_frame,
            text="!",
            font=TYPOGRAPHY.get_font(24, "bold"),
            text_color=COLORS.CARD,
        )
        icon_text.place(relx=0.5, rely=0.5, anchor="center")

        title_label = ctk.CTkLabel(
            header_frame,
            text="Password Change Required",
            font=TYPOGRAPHY.get_font(18, "bold"),
            text_color=COLORS.TEXT_PRIMARY,
        )
        title_label.pack()

        # Get current user's name
        user_name = self.session_manager.full_name or self.session_manager.username or "User"

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text=f"Welcome, {user_name}!\nPlease set a new password to continue.",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_SECONDARY,
            justify="center",
        )
        subtitle_label.pack(pady=(10, 0))

        # Form
        form_frame = ctk.CTkFrame(content, fg_color="transparent")
        form_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=SPACING.SECTION_SPACING)

        # New Password
        new_password_label = ctk.CTkLabel(
            form_frame,
            text="New Password:",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        new_password_label.pack(anchor="w", pady=(0, 5))

        self.new_password_entry = ctk.CTkEntry(form_frame, show="*")
        configure_input_style(self.new_password_entry)
        self.new_password_entry.pack(fill="x", pady=(0, 15))

        # Confirm Password
        confirm_password_label = ctk.CTkLabel(
            form_frame,
            text="Confirm New Password:",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        confirm_password_label.pack(anchor="w", pady=(0, 5))

        self.confirm_password_entry = ctk.CTkEntry(form_frame, show="*")
        configure_input_style(self.confirm_password_entry)
        self.confirm_password_entry.pack(fill="x", pady=(0, 10))
        self.confirm_password_entry.bind("<Return>", lambda e: self._on_change_password())

        # Password requirements hint
        hint_label = ctk.CTkLabel(
            form_frame,
            text=f"Password must be at least {MIN_PASSWORD_LENGTH} characters.",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_MUTED,
        )
        hint_label.pack(anchor="w")

        # Status/error label
        self.status_label = ctk.CTkLabel(
            content,
            text="",
            font=TYPOGRAPHY.small,
            text_color=COLORS.DANGER,
            wraplength=350,
        )
        self.status_label.pack(padx=SPACING.CARD_PADDING, pady=(5, 0))

        # Change Password button
        self.change_button = ctk.CTkButton(
            content,
            text="Change Password",
            command=self._on_change_password,
            width=150,
        )
        configure_button_style(self.change_button, "primary")
        self.change_button.pack(pady=SPACING.SECTION_SPACING)

    def _on_change_password(self) -> None:
        """Handle the Change Password button click."""
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        # Validate new password
        if not new_password:
            self.status_label.configure(
                text="Please enter a new password.",
                text_color=COLORS.DANGER,
            )
            return

        if len(new_password) < MIN_PASSWORD_LENGTH:
            self.status_label.configure(
                text=f"Password must be at least {MIN_PASSWORD_LENGTH} characters.",
                text_color=COLORS.DANGER,
            )
            return

        # Validate confirmation
        if not confirm_password:
            self.status_label.configure(
                text="Please confirm your new password.",
                text_color=COLORS.DANGER,
            )
            return

        if new_password != confirm_password:
            self.status_label.configure(
                text="Passwords do not match.",
                text_color=COLORS.DANGER,
            )
            self.confirm_password_entry.delete(0, "end")
            self.confirm_password_entry.focus()
            return

        # Get current user ID
        user_id = self.session_manager.user_id
        if not user_id:
            self.status_label.configure(
                text="Session error. Please log in again.",
                text_color=COLORS.DANGER,
            )
            return

        # Change the password
        success, error = self.auth_service.set_new_password(user_id, new_password)

        if success:
            self.status_label.configure(
                text="Password changed successfully!",
                text_color=COLORS.SUCCESS,
            )
            # Proceed to main view after a short delay
            self.after(500, self.on_password_changed)
        else:
            self.status_label.configure(
                text=error or "Failed to change password. Please try again.",
                text_color=COLORS.DANGER,
            )

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        # Clear fields and focus
        self.new_password_entry.delete(0, "end")
        self.confirm_password_entry.delete(0, "end")
        self.status_label.configure(text="")
        self.new_password_entry.focus()
