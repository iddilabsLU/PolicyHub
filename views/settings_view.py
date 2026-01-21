"""
PolicyHub Settings View

Main settings container with tab navigation for General, Users, and Categories.
"""

from typing import TYPE_CHECKING, Dict, Optional

import customtkinter as ctk

from app.theme import (
    COLORS,
    SPACING,
    TYPOGRAPHY,
    configure_card_style,
)
from core.session import SessionManager
from views.base_view import BaseView

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class SettingsView(BaseView):
    """
    Settings view container with tab navigation.

    Provides access to:
    - General settings (company name, thresholds)
    - User management
    - Category management

    Admin-only access is enforced.
    """

    def __init__(self, parent: ctk.CTkFrame, app: "PolicyHubApp"):
        """
        Initialize the settings view.

        Args:
            parent: Parent widget
            app: Main application instance
        """
        super().__init__(parent, app)
        self._tabs: Dict[str, BaseView] = {}
        self._current_tab: Optional[str] = None
        self._tab_buttons: Dict[str, ctk.CTkButton] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the settings view UI."""
        # Check admin permission
        session = SessionManager.get_instance()
        if not session.is_admin():
            self._build_no_permission_view()
            return

        # Header with title
        header = ctk.CTkFrame(self, fg_color=COLORS.CARD, height=60)
        configure_card_style(header, with_shadow=True)
        header.pack(fill="x", padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING)
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="Settings",
            font=TYPOGRAPHY.window_title,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title.pack(side="left", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        # Tab bar
        tab_bar = ctk.CTkFrame(self, fg_color="transparent")
        tab_bar.pack(fill="x", padx=SPACING.WINDOW_PADDING, pady=(0, 10))

        # Create tab buttons
        tab_config = [
            ("general", "General"),
            ("users", "Users"),
            ("categories", "Categories"),
            ("backup", "Backup & Restore"),
            ("database", "Database"),
        ]

        for tab_id, tab_label in tab_config:
            btn = ctk.CTkButton(
                tab_bar,
                text=tab_label,
                command=lambda t=tab_id: self._switch_tab(t),
                fg_color="transparent",
                hover_color=COLORS.MUTED,
                text_color=COLORS.TEXT_SECONDARY,
                font=TYPOGRAPHY.body,
                height=36,
                width=100,
                corner_radius=SPACING.CORNER_RADIUS,
            )
            btn.pack(side="left", padx=(0, 4))
            self._tab_buttons[tab_id] = btn

        # Content area
        self._content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._content_frame.pack(fill="both", expand=True)

        # Show default tab
        self.after(100, lambda: self._switch_tab("general"))

    def _build_no_permission_view(self) -> None:
        """Build view for non-admin users."""
        container = ctk.CTkFrame(self, fg_color=COLORS.CARD)
        configure_card_style(container)
        container.pack(
            fill="both",
            expand=True,
            padx=SPACING.WINDOW_PADDING,
            pady=SPACING.WINDOW_PADDING,
        )

        msg = ctk.CTkLabel(
            container,
            text="You do not have permission to access settings.\n\nPlease contact an administrator.",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_SECONDARY,
        )
        msg.place(relx=0.5, rely=0.5, anchor="center")

    def _switch_tab(self, tab_id: str) -> None:
        """
        Switch to a different tab.

        Args:
            tab_id: ID of the tab to switch to (general, users, categories)
        """
        # Hide current tab
        if self._current_tab and self._current_tab in self._tabs:
            current_view = self._tabs[self._current_tab]
            current_view.on_hide()
            current_view.pack_forget()

        # Update button states
        for btn_id, btn in self._tab_buttons.items():
            if btn_id == tab_id:
                btn.configure(
                    fg_color=COLORS.PRIMARY,
                    text_color=COLORS.PRIMARY_FOREGROUND,
                    hover_color=COLORS.PRIMARY_HOVER,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS.TEXT_SECONDARY,
                    hover_color=COLORS.MUTED,
                )

        # Create tab view if needed
        if tab_id not in self._tabs:
            self._create_tab_view(tab_id)

        # Show new tab
        if tab_id in self._tabs:
            view = self._tabs[tab_id]
            view.pack(in_=self._content_frame, fill="both", expand=True)
            view.on_show()
            self._current_tab = tab_id

    def _create_tab_view(self, tab_id: str) -> None:
        """
        Create a tab view by ID.

        Args:
            tab_id: ID of the tab to create
        """
        try:
            if tab_id == "general":
                from views.settings.general_settings import GeneralSettingsView
                self._tabs[tab_id] = GeneralSettingsView(self._content_frame, self.app)

            elif tab_id == "users":
                from views.settings.users_settings import UsersSettingsView
                self._tabs[tab_id] = UsersSettingsView(self._content_frame, self.app)

            elif tab_id == "categories":
                from views.settings.categories_settings import CategoriesSettingsView
                self._tabs[tab_id] = CategoriesSettingsView(self._content_frame, self.app)

            elif tab_id == "backup":
                from views.settings.backup_settings import BackupSettingsView
                self._tabs[tab_id] = BackupSettingsView(self._content_frame, self.app)

            elif tab_id == "database":
                from views.settings.database_settings import DatabaseSettingsView
                self._tabs[tab_id] = DatabaseSettingsView(self._content_frame, self.app)

        except Exception as e:
            # Create error view
            error_view = BaseView(self._content_frame, self.app)
            error_label = ctk.CTkLabel(
                error_view,
                text=f"Error loading {tab_id} settings: {str(e)}",
                font=TYPOGRAPHY.body,
                text_color=COLORS.DANGER,
            )
            error_label.place(relx=0.5, rely=0.5, anchor="center")
            self._tabs[tab_id] = error_view

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        # Refresh current tab
        if self._current_tab and self._current_tab in self._tabs:
            self._tabs[self._current_tab].on_show()

    def on_hide(self) -> None:
        """Called when the view is hidden."""
        super().on_hide()
        # Hide current tab
        if self._current_tab and self._current_tab in self._tabs:
            self._tabs[self._current_tab].on_hide()
