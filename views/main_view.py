"""
PolicyHub Main View

Main application view shown after successful login.
Contains the sidebar navigation and content area with view switching.
"""

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


class MainView(BaseView):
    """
    Main application view with sidebar navigation and content area.

    Manages switching between different content views:
    - Dashboard
    - Register
    - Document Detail
    - Reports (placeholder)
    - Settings (admin only, placeholder)
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
        # Configure grid
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
        self.dashboard_btn.pack(fill="x", pady=2)

        # Register button
        self.register_btn = self._create_nav_button(
            nav_frame, "  Register", "register"
        )
        self.register_btn.pack(fill="x", pady=2)

        # Reports button (placeholder)
        self.reports_btn = self._create_nav_button(
            nav_frame, "  Reports", "reports"
        )
        self.reports_btn.pack(fill="x", pady=2)

        # Settings button (admin only)
        if self.session.is_admin():
            self.settings_btn = self._create_nav_button(
                nav_frame, "  Settings", "settings"
            )
            self.settings_btn.pack(fill="x", pady=2)

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

    def _create_content_view(self, view_name: str) -> None:
        """Create a content view by name."""
        if view_name == "dashboard":
            from views.dashboard_view import DashboardView
            self.content_views[view_name] = DashboardView(self.content, self.app)

        elif view_name == "register":
            from views.register_view import RegisterView
            self.content_views[view_name] = RegisterView(self.content, self.app)

        elif view_name == "reports":
            # Placeholder
            self.content_views[view_name] = self._create_placeholder_view(
                "Reports",
                "Report generation will be available in a future update."
            )

        elif view_name == "settings":
            # Placeholder
            self.content_views[view_name] = self._create_placeholder_view(
                "Settings",
                "Settings management will be available in a future update."
            )

        elif view_name == "document_detail":
            # Document detail view is created dynamically with a document
            pass

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
