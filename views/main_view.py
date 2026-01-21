"""
PolicyHub Main View

Main application view shown after successful login.
Contains the sidebar navigation and content area with view switching.
"""

import logging
from typing import TYPE_CHECKING, Dict, Optional

import customtkinter as ctk

from app.constants import APP_NAME
from app.theme import (
    COLORS,
    SPACING,
    TYPOGRAPHY,
)
from core.session import SessionManager
from models.document import Document
from views.base_view import BaseView

if TYPE_CHECKING:
    from app.application import PolicyHubApp

logger = logging.getLogger(__name__)


class MainView(BaseView):
    """
    Main application view with sidebar navigation and content area.

    Manages switching between different content views:
    - Dashboard
    - Register
    - Document Detail
    - Reports
    - Settings (admin only)
    """

    def __init__(self, parent: ctk.CTkFrame, app: "PolicyHubApp"):
        """
        Initialize the main view.

        Args:
            parent: Parent widget
            app: Main application instance
        """
        super().__init__(parent, app)
        self.session = SessionManager.get_instance()
        self.content_views: Dict[str, BaseView] = {}
        self._current_view_name: Optional[str] = None
        self._current_document: Optional[Document] = None

        self._build_ui()

        # Show dashboard by default
        self.after(100, lambda: self._switch_content_view("dashboard"))

    def _build_ui(self) -> None:
        """Build the main view UI."""
        # Configure grid with proper column weights
        self.grid_columnconfigure(0, weight=0, minsize=SPACING.SIDEBAR_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self._build_sidebar()

        # Main content area
        self.content = ctk.CTkFrame(
            self,
            fg_color=COLORS.BACKGROUND,
            corner_radius=0,
        )
        self.content.grid(row=0, column=1, sticky="nsew")

    def _build_sidebar(self) -> None:
        """Build the sidebar navigation."""
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=COLORS.PRIMARY,
            corner_radius=0,
            width=SPACING.SIDEBAR_WIDTH,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Sidebar header
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=20)

        app_title = ctk.CTkLabel(
            header_frame,
            text=APP_NAME,
            font=TYPOGRAPHY.get_font(18, "bold"),
            text_color=COLORS.PRIMARY_FOREGROUND,
        )
        app_title.pack()

        # Divider
        divider = ctk.CTkFrame(
            self.sidebar,
            fg_color=COLORS.PRIMARY_HOVER,
            height=1,
        )
        divider.pack(fill="x", padx=15, pady=10)

        # Navigation buttons
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=10, pady=10)

        # Dashboard button
        self.dashboard_btn = self._create_nav_button(
            nav_frame, "  Dashboard", "dashboard"
        )
        self.dashboard_btn.pack(fill="x", pady=4)

        # Register button
        self.register_btn = self._create_nav_button(
            nav_frame, "  Register", "register"
        )
        self.register_btn.pack(fill="x", pady=4)

        # Reports button (placeholder)
        self.reports_btn = self._create_nav_button(
            nav_frame, "  Reports", "reports"
        )
        self.reports_btn.pack(fill="x", pady=4)

        # Settings button (admin only)
        if self.session.is_admin():
            self.settings_btn = self._create_nav_button(
                nav_frame, "  Settings", "settings"
            )
            self.settings_btn.pack(fill="x", pady=4)

        # IddiLabs button
        self.iddilabs_btn = self._create_nav_button(
            nav_frame, "  IddiLabs", "iddilabs"
        )
        self.iddilabs_btn.pack(fill="x", pady=4)

        # User info and logout at bottom
        user_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        user_frame.pack(side="bottom", fill="x", padx=15, pady=20)

        # Divider
        divider2 = ctk.CTkFrame(
            user_frame,
            fg_color=COLORS.PRIMARY_HOVER,
            height=1,
        )
        divider2.pack(fill="x", pady=(0, 15))

        # User name and role
        user = self.session.current_user
        if user:
            name_label = ctk.CTkLabel(
                user_frame,
                text=user.full_name,
                font=TYPOGRAPHY.body,
                text_color=COLORS.PRIMARY_FOREGROUND,
            )
            name_label.pack(anchor="w")

            role_label = ctk.CTkLabel(
                user_frame,
                text=user.role_display,
                font=TYPOGRAPHY.small,
                text_color=COLORS.SECONDARY,
            )
            role_label.pack(anchor="w", pady=(2, 10))

        # Change Password button
        self.change_password_btn = ctk.CTkButton(
            user_frame,
            text="Change Password",
            command=self._on_change_password,
            fg_color="transparent",
            hover_color=COLORS.PRIMARY_HOVER,
            text_color=COLORS.PRIMARY_FOREGROUND,
            height=32,
            font=TYPOGRAPHY.small,
            border_width=1,
            border_color=COLORS.PRIMARY_FOREGROUND,
        )
        self.change_password_btn.pack(fill="x", pady=(0, 8))

        # Logout button
        self.logout_btn = ctk.CTkButton(
            user_frame,
            text="Logout",
            command=self._on_logout,
            fg_color=COLORS.SECONDARY,
            hover_color=COLORS.SECONDARY_HOVER,
            text_color=COLORS.PRIMARY,
            height=32,
            font=TYPOGRAPHY.small,
        )
        self.logout_btn.pack(fill="x")

    def _create_nav_button(self, parent, text: str, view_name: str) -> ctk.CTkButton:
        """Create a navigation button."""
        btn = ctk.CTkButton(
            parent,
            text=text,
            anchor="w",
            fg_color="transparent",
            hover_color=COLORS.PRIMARY_HOVER,
            text_color=COLORS.PRIMARY_FOREGROUND,
            height=40,
            font=TYPOGRAPHY.body,
            command=lambda: self._switch_content_view(view_name),
        )
        return btn

    def _update_nav_button_states(self) -> None:
        """Update navigation button visual states."""
        buttons = {
            "dashboard": self.dashboard_btn,
            "register": self.register_btn,
            "reports": self.reports_btn,
            "iddilabs": self.iddilabs_btn,
        }

        if hasattr(self, "settings_btn"):
            buttons["settings"] = self.settings_btn

        for name, btn in buttons.items():
            if name == self._current_view_name:
                btn.configure(fg_color=COLORS.PRIMARY_HOVER)
            else:
                btn.configure(fg_color="transparent")

    def _switch_content_view(
        self,
        view_name: str,
        filter_type: Optional[str] = None,
        review_status: Optional[str] = None,
    ) -> None:
        """
        Switch the content area to a different view.

        Args:
            view_name: Name of the view to switch to
            filter_type: Optional filter to apply (for register)
            review_status: Optional review status filter (for register)
        """
        try:
            # Hide current view
            if self._current_view_name and self._current_view_name in self.content_views:
                current = self.content_views[self._current_view_name]
                current.on_hide()
                current.pack_forget()

            # Create view if needed
            if view_name not in self.content_views:
                self._create_content_view(view_name)

            # Show new view
            if view_name in self.content_views:
                view = self.content_views[view_name]
                view.pack(in_=self.content, fill="both", expand=True)

                # Apply filters if provided (for register view)
                if view_name == "register" and hasattr(view, "apply_filter"):
                    if filter_type or review_status:
                        view.apply_filter(filter_type=filter_type, review_status=review_status)

                view.on_show()
                self._current_view_name = view_name
                self._update_nav_button_states()
        except Exception as e:
            logger.exception(f"Error switching to view '{view_name}': {e}")
            self._show_error_view(f"Failed to load {view_name} view: {str(e)}")

    def _create_content_view(self, view_name: str) -> None:
        """Create a content view by name."""
        try:
            if view_name == "dashboard":
                from views.dashboard_view import DashboardView
                logger.info("Creating DashboardView...")
                self.content_views[view_name] = DashboardView(self.content, self.app)
                logger.info("DashboardView created successfully")

            elif view_name == "register":
                from views.register_view import RegisterView
                logger.info("Creating RegisterView...")
                self.content_views[view_name] = RegisterView(self.content, self.app)
                logger.info("RegisterView created successfully")

            elif view_name == "reports":
                from views.reports_view import ReportsView
                logger.info("Creating ReportsView...")
                self.content_views[view_name] = ReportsView(self.content, self.app)
                logger.info("ReportsView created successfully")

            elif view_name == "settings":
                from views.settings_view import SettingsView
                logger.info("Creating SettingsView...")
                self.content_views[view_name] = SettingsView(self.content, self.app)
                logger.info("SettingsView created successfully")

            elif view_name == "iddilabs":
                from views.iddilabs_view import IddiLabsView
                logger.info("Creating IddiLabsView...")
                self.content_views[view_name] = IddiLabsView(self.content, self.app)
                logger.info("IddiLabsView created successfully")

            elif view_name == "document_detail":
                # Document detail view is created dynamically with a document
                pass
        except Exception as e:
            logger.exception(f"Error creating view '{view_name}': {e}")
            # Create an error view instead
            self.content_views[view_name] = self._create_error_view(
                view_name,
                f"Failed to initialize: {str(e)}"
            )

    def _create_placeholder_view(self, title: str, message: str) -> BaseView:
        """Create a placeholder view for unimplemented features."""
        view = BaseView(self.content, self.app)

        # Header
        header = ctk.CTkFrame(view, fg_color=COLORS.CARD, height=60)
        header.pack(fill="x", padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING)
        header.pack_propagate(False)

        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=TYPOGRAPHY.window_title,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title_label.pack(side="left", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        # Content
        content = ctk.CTkFrame(
            view,
            fg_color=COLORS.CARD,
            corner_radius=SPACING.CORNER_RADIUS_LARGE,
        )
        content.pack(
            fill="both",
            expand=True,
            padx=SPACING.WINDOW_PADDING,
            pady=(0, SPACING.WINDOW_PADDING),
        )

        msg_label = ctk.CTkLabel(
            content,
            text=message,
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_SECONDARY,
        )
        msg_label.place(relx=0.5, rely=0.5, anchor="center")

        return view

    def _create_error_view(self, view_name: str, error_message: str) -> BaseView:
        """Create an error view when a view fails to load."""
        view = BaseView(self.content, self.app)

        # Header
        header = ctk.CTkFrame(view, fg_color=COLORS.DANGER_BG, height=60)
        header.pack(fill="x", padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING)
        header.pack_propagate(False)

        title_label = ctk.CTkLabel(
            header,
            text=f"Error Loading {view_name.title()}",
            font=TYPOGRAPHY.window_title,
            text_color=COLORS.DANGER,
        )
        title_label.pack(side="left", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        # Content
        content = ctk.CTkFrame(
            view,
            fg_color=COLORS.CARD,
            corner_radius=SPACING.CORNER_RADIUS_LARGE,
        )
        content.pack(
            fill="both",
            expand=True,
            padx=SPACING.WINDOW_PADDING,
            pady=(0, SPACING.WINDOW_PADDING),
        )

        error_label = ctk.CTkLabel(
            content,
            text=f"Error: {error_message}\n\nCheck the log file for more details.",
            font=TYPOGRAPHY.body,
            text_color=COLORS.DANGER,
            wraplength=500,
        )
        error_label.place(relx=0.5, rely=0.5, anchor="center")

        return view

    def _show_error_view(self, error_message: str) -> None:
        """Show an error message in the content area."""
        # Clear existing views
        for widget in self.content.winfo_children():
            widget.destroy()

        # Create error display
        error_frame = ctk.CTkFrame(
            self.content,
            fg_color=COLORS.DANGER_BG,
            corner_radius=SPACING.CORNER_RADIUS_LARGE,
        )
        error_frame.pack(
            fill="both",
            expand=True,
            padx=SPACING.WINDOW_PADDING,
            pady=SPACING.WINDOW_PADDING,
        )

        error_label = ctk.CTkLabel(
            error_frame,
            text=f"Error: {error_message}\n\nCheck the log file for more details.",
            font=TYPOGRAPHY.body,
            text_color=COLORS.DANGER,
            wraplength=500,
        )
        error_label.place(relx=0.5, rely=0.5, anchor="center")

    def _show_document_detail(self, document: Document) -> None:
        """
        Show the document detail view.

        Args:
            document: Document to display
        """
        from views.document_detail_view import DocumentDetailView

        self._current_document = document

        # Remove existing detail view if any
        if "document_detail" in self.content_views:
            self.content_views["document_detail"].destroy()
            del self.content_views["document_detail"]

        # Create new detail view
        self.content_views["document_detail"] = DocumentDetailView(
            self.content,
            self.app,
            document=document,
            on_back=lambda: self._switch_content_view("register"),
        )

        self._switch_content_view("document_detail")

    def _on_change_password(self) -> None:
        """Handle change password button click."""
        from dialogs.change_password_dialog import ChangePasswordDialog

        dialog = ChangePasswordDialog(self.winfo_toplevel(), self.app.db)
        dialog.show()

    def _on_logout(self) -> None:
        """Handle logout button click."""
        # Clean up content views
        for view in self.content_views.values():
            view.destroy()
        self.content_views.clear()

        self.app.logout()

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        # Refresh current view if any
        if self._current_view_name and self._current_view_name in self.content_views:
            self.content_views[self._current_view_name].on_show()

    def on_hide(self) -> None:
        """Called when the view is hidden."""
        super().on_hide()
        # Hide current content view
        if self._current_view_name and self._current_view_name in self.content_views:
            self.content_views[self._current_view_name].on_hide()
