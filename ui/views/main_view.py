"""
PolicyHub Main View (PySide6)

Main application view shown after successful login.
Contains the sidebar navigation and content area with view switching.
"""

import logging
from typing import TYPE_CHECKING, Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStackedWidget,
)

from app.constants import APP_NAME
from app.theme import COLORS, SPACING, TYPOGRAPHY
from core.session import SessionManager
from models.document import Document
from ui.views.base_view import BaseView

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

    def __init__(self, parent: QWidget, app: "PolicyHubApp"):
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
        self._nav_buttons: Dict[str, QPushButton] = {}

        self._build_ui()

        # Show dashboard by default
        QTimer.singleShot(100, lambda: self._switch_content_view("dashboard"))

    def _build_ui(self) -> None:
        """Build the main view UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self._build_sidebar(layout)

        # Main content area
        self.content = QStackedWidget()
        self.content.setStyleSheet(f"background-color: {COLORS.BACKGROUND};")
        layout.addWidget(self.content, 1)

    def _build_sidebar(self, parent_layout: QHBoxLayout) -> None:
        """Build the sidebar navigation."""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(SPACING.SIDEBAR_WIDTH)
        self.sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.PRIMARY};
                border: none;
            }}
        """)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Sidebar header
        header_widget = QWidget()
        header_widget.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 20, 15, 10)

        app_title = QLabel(APP_NAME)
        app_title.setFont(TYPOGRAPHY.get_font(18, TYPOGRAPHY.WEIGHT_BOLD))
        app_title.setStyleSheet(f"color: {COLORS.PRIMARY_FOREGROUND}; background: transparent;")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(app_title)

        sidebar_layout.addWidget(header_widget)

        # Divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {COLORS.PRIMARY_HOVER};")
        sidebar_layout.addWidget(divider)

        # Navigation buttons
        nav_widget = QWidget()
        nav_widget.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(10, 10, 10, 10)
        nav_layout.setSpacing(4)

        # Dashboard button
        self._nav_buttons["dashboard"] = self._create_nav_button("  Dashboard", "dashboard")
        nav_layout.addWidget(self._nav_buttons["dashboard"])

        # Register button
        self._nav_buttons["register"] = self._create_nav_button("  Register", "register")
        nav_layout.addWidget(self._nav_buttons["register"])

        # Reports button
        self._nav_buttons["reports"] = self._create_nav_button("  Reports", "reports")
        nav_layout.addWidget(self._nav_buttons["reports"])

        # Settings button (admin only)
        if self.session.is_admin():
            self._nav_buttons["settings"] = self._create_nav_button("  Settings", "settings")
            nav_layout.addWidget(self._nav_buttons["settings"])

        # IddiLabs button
        self._nav_buttons["iddilabs"] = self._create_nav_button("  IddiLabs", "iddilabs")
        nav_layout.addWidget(self._nav_buttons["iddilabs"])

        nav_layout.addStretch()
        sidebar_layout.addWidget(nav_widget, 1)

        # User info and logout at bottom
        user_widget = QFrame()
        user_widget.setStyleSheet("background: transparent;")
        user_layout = QVBoxLayout(user_widget)
        user_layout.setContentsMargins(15, 0, 15, 20)

        # Divider
        divider2 = QFrame()
        divider2.setFixedHeight(1)
        divider2.setStyleSheet(f"background-color: {COLORS.PRIMARY_HOVER};")
        user_layout.addWidget(divider2)

        # User name and role
        user = self.session.current_user
        if user:
            name_label = QLabel(user.full_name)
            name_label.setFont(TYPOGRAPHY.body)
            name_label.setStyleSheet(f"color: {COLORS.PRIMARY_FOREGROUND}; background: transparent;")
            name_label.setContentsMargins(0, 15, 0, 0)
            user_layout.addWidget(name_label)

            role_label = QLabel(user.role_display)
            role_label.setFont(TYPOGRAPHY.small)
            role_label.setStyleSheet(f"color: {COLORS.SECONDARY}; background: transparent;")
            role_label.setContentsMargins(0, 2, 0, 10)
            user_layout.addWidget(role_label)

        # Change Password button
        change_password_btn = QPushButton("Change Password")
        change_password_btn.setFixedHeight(32)
        change_password_btn.setFont(TYPOGRAPHY.small)
        change_password_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        change_password_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS.PRIMARY_FOREGROUND};
                border: 1px solid {COLORS.PRIMARY_FOREGROUND};
                border-radius: 4px;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_HOVER};
            }}
        """)
        change_password_btn.clicked.connect(self._on_change_password)
        user_layout.addWidget(change_password_btn)

        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setFixedHeight(32)
        logout_btn.setFont(TYPOGRAPHY.small)
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.SECONDARY};
                color: {COLORS.PRIMARY};
                border: none;
                border-radius: 4px;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.SECONDARY_HOVER};
            }}
        """)
        logout_btn.clicked.connect(self._on_logout)
        user_layout.addWidget(logout_btn)

        sidebar_layout.addWidget(user_widget)
        parent_layout.addWidget(self.sidebar)

    def _create_nav_button(self, text: str, view_name: str) -> QPushButton:
        """Create a navigation button."""
        btn = QPushButton(text)
        btn.setFixedHeight(40)
        btn.setFont(TYPOGRAPHY.body)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS.PRIMARY_FOREGROUND};
                border: none;
                border-radius: 4px;
                padding: 0 15px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_HOVER};
            }}
        """)
        btn.clicked.connect(lambda: self._switch_content_view(view_name))
        return btn

    def _update_nav_button_states(self) -> None:
        """Update navigation button visual states."""
        for name, btn in self._nav_buttons.items():
            if name == self._current_view_name:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS.PRIMARY_HOVER};
                        color: {COLORS.PRIMARY_FOREGROUND};
                        border: none;
                        border-radius: 4px;
                        padding: 0 15px;
                        text-align: left;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS.PRIMARY_HOVER};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {COLORS.PRIMARY_FOREGROUND};
                        border: none;
                        border-radius: 4px;
                        padding: 0 15px;
                        text-align: left;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS.PRIMARY_HOVER};
                    }}
                """)

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

            # Create view if needed
            if view_name not in self.content_views:
                self._create_content_view(view_name)

            # Show new view
            if view_name in self.content_views:
                view = self.content_views[view_name]

                # Ensure view is in stack
                if self.content.indexOf(view) == -1:
                    self.content.addWidget(view)

                self.content.setCurrentWidget(view)

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
                from ui.views.dashboard_view import DashboardView
                logger.info("Creating DashboardView...")
                self.content_views[view_name] = DashboardView(self.content, self.app)
                logger.info("DashboardView created successfully")

            elif view_name == "register":
                from ui.views.register_view import RegisterView
                logger.info("Creating RegisterView...")
                self.content_views[view_name] = RegisterView(self.content, self.app)
                logger.info("RegisterView created successfully")

            elif view_name == "reports":
                from ui.views.reports_view import ReportsView
                logger.info("Creating ReportsView...")
                self.content_views[view_name] = ReportsView(self.content, self.app)
                logger.info("ReportsView created successfully")

            elif view_name == "settings":
                from ui.views.settings_view import SettingsView
                logger.info("Creating SettingsView...")
                self.content_views[view_name] = SettingsView(self.content, self.app)
                logger.info("SettingsView created successfully")

            elif view_name == "iddilabs":
                from ui.views.iddilabs_view import IddiLabsView
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

    def _create_error_view(self, view_name: str, error_message: str) -> BaseView:
        """Create an error view when a view fails to load."""
        view = BaseView(self.content, self.app)
        layout = QVBoxLayout(view)
        layout.setContentsMargins(SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING)

        # Header
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"background-color: {COLORS.DANGER_BG}; border-radius: {SPACING.CORNER_RADIUS}px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.CARD_PADDING, 0, SPACING.CARD_PADDING, 0)

        title_label = QLabel(f"Error Loading {view_name.title()}")
        title_label.setFont(TYPOGRAPHY.window_title)
        title_label.setStyleSheet(f"color: {COLORS.DANGER}; background: transparent;")
        header_layout.addWidget(title_label)

        layout.addWidget(header)

        # Content
        content = QFrame()
        content.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.CARD};
                border-radius: {SPACING.CORNER_RADIUS_LARGE}px;
            }}
        """)
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        error_label = QLabel(f"Error: {error_message}\n\nCheck the log file for details.")
        error_label.setFont(TYPOGRAPHY.body)
        error_label.setStyleSheet(f"color: {COLORS.DANGER}; background: transparent;")
        error_label.setWordWrap(True)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(error_label)

        layout.addWidget(content, 1)

        return view

    def _show_error_view(self, error_message: str) -> None:
        """Show an error message in the content area."""
        # Create error widget
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)
        error_layout.setContentsMargins(SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING)

        error_frame = QFrame()
        error_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.DANGER_BG};
                border-radius: {SPACING.CORNER_RADIUS_LARGE}px;
            }}
        """)
        frame_layout = QVBoxLayout(error_frame)
        frame_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        error_label = QLabel(f"Error: {error_message}\n\nCheck the log file for details.")
        error_label.setFont(TYPOGRAPHY.body)
        error_label.setStyleSheet(f"color: {COLORS.DANGER}; background: transparent;")
        error_label.setWordWrap(True)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(error_label)

        error_layout.addWidget(error_frame, 1)

        # Add to stack and show
        self.content.addWidget(error_widget)
        self.content.setCurrentWidget(error_widget)

    def _show_document_detail(self, document: Document) -> None:
        """
        Show the document detail view.

        Args:
            document: Document to display
        """
        from ui.views.document_detail_view import DocumentDetailView

        self._current_document = document

        # Remove existing detail view if any
        if "document_detail" in self.content_views:
            old_view = self.content_views["document_detail"]
            self.content.removeWidget(old_view)
            old_view.deleteLater()
            del self.content_views["document_detail"]

        # Create new detail view
        detail_view = DocumentDetailView(
            self.content,
            self.app,
            document=document,
            on_back=lambda: self._switch_content_view("register"),
        )
        self.content_views["document_detail"] = detail_view

        self._switch_content_view("document_detail")

    def _on_change_password(self) -> None:
        """Handle change password button click."""
        from ui.dialogs.change_password_dialog import ChangePasswordDialog

        dialog = ChangePasswordDialog(self.window(), self.app.db)
        dialog.exec()

    def _on_logout(self) -> None:
        """Handle logout button click."""
        # Clean up content views
        for view_name, view in list(self.content_views.items()):
            self.content.removeWidget(view)
            view.deleteLater()
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
