"""
PolicyHub Settings View (PySide6)

Main settings container with tab navigation for General, Users, and Categories.
"""

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

from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button, style_card
from core.session import SessionManager
from ui.views.base_view import BaseView

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class SettingsView(BaseView):
    """
    Settings view container with tab navigation.

    Provides access to:
    - General settings (company name, thresholds)
    - User management
    - Category management
    - Backup & Restore
    - Database settings

    Admin-only access is enforced.
    """

    def __init__(self, parent: QWidget, app: "PolicyHubApp"):
        """
        Initialize the settings view.

        Args:
            parent: Parent widget
            app: Main application instance
        """
        super().__init__(parent, app)
        self._tabs: Dict[str, BaseView] = {}
        self._current_tab: Optional[str] = None
        self._tab_buttons: Dict[str, QPushButton] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the settings view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
        )
        layout.setSpacing(0)

        # Check admin permission
        session = SessionManager.get_instance()
        if not session.is_admin():
            self._build_no_permission_view(layout)
            return

        # Header with title
        header = QFrame()
        header.setFixedHeight(60)
        style_card(header, with_shadow=True)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
        )

        title = QLabel("Settings")
        title.setFont(TYPOGRAPHY.window_title)
        title.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(header)
        layout.addSpacing(SPACING.WINDOW_PADDING)

        # Tab bar
        tab_bar = QFrame()
        tab_bar.setStyleSheet("background: transparent;")
        tab_layout = QHBoxLayout(tab_bar)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(4)

        # Create tab buttons with icons
        tab_config = [
            ("general", "⚙️ General"),
            ("users", "👥 Users"),
            ("categories", "📁 Categories"),
            ("backup", "💾 Backup & Restore"),
            ("database", "🗄️ Database"),
        ]

        for tab_id, tab_label in tab_config:
            btn = QPushButton(tab_label)
            btn.setFixedHeight(44)
            btn.setMinimumWidth(120)
            btn.setFont(TYPOGRAPHY.body)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, t=tab_id: self._switch_tab(t))
            self._style_tab_button(btn, active=False)
            tab_layout.addWidget(btn)
            self._tab_buttons[tab_id] = btn

        tab_layout.addStretch()
        layout.addWidget(tab_bar)
        layout.addSpacing(10)

        # Content area using QStackedWidget
        self._content_stack = QStackedWidget()
        self._content_stack.setStyleSheet("background: transparent;")
        layout.addWidget(self._content_stack, 1)

        # Show default tab after a short delay
        QTimer.singleShot(100, lambda: self._switch_tab("general"))

    def _build_no_permission_view(self, layout: QVBoxLayout) -> None:
        """Build view for non-admin users."""
        container = QFrame()
        style_card(container)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        msg = QLabel(
            "You do not have permission to access settings.\n\nPlease contact an administrator."
        )
        msg.setFont(TYPOGRAPHY.body)
        msg.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(msg, 1, Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(container, 1)

    def _style_tab_button(self, btn: QPushButton, active: bool) -> None:
        """Style a tab button based on active state."""
        if active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS.PRIMARY};
                    color: {COLORS.PRIMARY_FOREGROUND};
                    border: none;
                    border-radius: {SPACING.CORNER_RADIUS}px;
                    padding: 0 16px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS.PRIMARY_HOVER};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS.TEXT_SECONDARY};
                    border: none;
                    border-radius: {SPACING.CORNER_RADIUS}px;
                    padding: 0 16px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS.MUTED};
                }}
            """)

    def _switch_tab(self, tab_id: str) -> None:
        """
        Switch to a different tab.

        Args:
            tab_id: ID of the tab to switch to (general, users, categories, backup, database)
        """
        # Hide current tab
        if self._current_tab and self._current_tab in self._tabs:
            self._tabs[self._current_tab].on_hide()

        # Update button states
        for btn_id, btn in self._tab_buttons.items():
            self._style_tab_button(btn, active=(btn_id == tab_id))

        # Create tab view if needed
        if tab_id not in self._tabs:
            self._create_tab_view(tab_id)

        # Show new tab
        if tab_id in self._tabs:
            view = self._tabs[tab_id]
            self._content_stack.setCurrentWidget(view)
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
                from ui.views.settings.general_settings import GeneralSettingsView
                view = GeneralSettingsView(self, self.app)

            elif tab_id == "users":
                from ui.views.settings.users_settings import UsersSettingsView
                view = UsersSettingsView(self, self.app)

            elif tab_id == "categories":
                from ui.views.settings.categories_settings import CategoriesSettingsView
                view = CategoriesSettingsView(self, self.app)

            elif tab_id == "backup":
                from ui.views.settings.backup_settings import BackupSettingsView
                view = BackupSettingsView(self, self.app)

            elif tab_id == "database":
                from ui.views.settings.database_settings import DatabaseSettingsView
                view = DatabaseSettingsView(self, self.app)

            else:
                raise ValueError(f"Unknown tab: {tab_id}")

            self._tabs[tab_id] = view
            self._content_stack.addWidget(view)

        except Exception as e:
            # Create error view
            error_view = BaseView(self, self.app)
            error_layout = QVBoxLayout(error_view)
            error_label = QLabel(f"Error loading {tab_id} settings: {str(e)}")
            error_label.setFont(TYPOGRAPHY.body)
            error_label.setStyleSheet(f"color: {COLORS.DANGER}; background: transparent;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_layout.addWidget(error_label, 1, Qt.AlignmentFlag.AlignCenter)
            self._tabs[tab_id] = error_view
            self._content_stack.addWidget(error_view)

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
