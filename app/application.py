"""
PolicyHub Main Application

The main application class that orchestrates the startup flow
and manages view switching.
"""

import logging
from pathlib import Path
from typing import Optional

import customtkinter as ctk

from app.constants import APP_NAME, APP_VERSION
from app.theme import COLORS, WINDOW_SIZE
from core.config import ConfigManager
from core.database import DatabaseManager
from core.session import SessionManager
from utils.files import get_database_path

logger = logging.getLogger(__name__)


class PolicyHubApp(ctk.CTk):
    """
    Main PolicyHub application.

    Manages the application lifecycle:
    1. Load local config
    2. Show setup wizard if needed
    3. Connect to database
    4. Show admin creation if first run
    5. Show login screen
    6. Show main application after login
    """

    def __init__(self):
        """Initialize the PolicyHub application."""
        super().__init__()

        # Configure window
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_SIZE.DEFAULT_WIDTH}x{WINDOW_SIZE.DEFAULT_HEIGHT}")
        self.minsize(WINDOW_SIZE.MIN_WIDTH, WINDOW_SIZE.MIN_HEIGHT)
        self.configure(fg_color=COLORS.BACKGROUND)

        # Center window on screen
        self._center_window()

        # Initialize managers
        self.config_manager = ConfigManager.get_instance()
        self.session_manager = SessionManager.get_instance()
        self.db: Optional[DatabaseManager] = None

        # View container
        self.container = ctk.CTkFrame(self, fg_color=COLORS.BACKGROUND)
        self.container.pack(fill="both", expand=True)

        # Current view
        self.current_view: Optional[ctk.CTkFrame] = None

        # Ensure local folders exist
        self.config_manager.ensure_local_folders()

        # Start the application flow
        self._start_application_flow()

    def _center_window(self) -> None:
        """Center the window on the screen."""
        self.update_idletasks()
        width = WINDOW_SIZE.DEFAULT_WIDTH
        height = WINDOW_SIZE.DEFAULT_HEIGHT
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _start_application_flow(self) -> None:
        """Start the application flow based on current state."""
        config = self.config_manager.load()

        # Check if shared folder is configured
        if not config.is_configured():
            logger.info("No shared folder configured, showing setup wizard")
            self._show_setup_view()
            return

        # Validate the shared folder path
        is_valid, error = self.config_manager.validate_shared_folder(
            config.shared_folder_path
        )

        if not is_valid:
            logger.warning(f"Shared folder invalid: {error}")
            self._show_setup_view(error_message=f"Previous folder unavailable: {error}")
            return

        # Connect to database
        self._connect_database()

    def _connect_database(self) -> None:
        """Connect to the database and continue the flow."""
        db_path = get_database_path()

        if db_path is None:
            logger.error("Database path not available")
            self._show_setup_view(error_message="Could not determine database path")
            return

        self.db = DatabaseManager(db_path)

        # Check if database exists and has users
        if not self.db.database_exists():
            logger.info("Database does not exist, initializing schema")
            self.db.initialize_schema()
            self._show_admin_creation_view()
        elif not self.db.has_any_users():
            logger.info("Database exists but has no users")
            self._show_admin_creation_view()
        else:
            logger.info("Database ready, showing login")
            self._show_login_view()

    def _show_setup_view(self, error_message: Optional[str] = None) -> None:
        """Show the setup wizard view."""
        from views.setup_view import SetupView

        self._clear_container()

        view = SetupView(
            parent=self.container,
            app=self,
            on_complete=self._on_setup_complete,
            error_message=error_message,
        )
        view.pack(fill="both", expand=True)
        self.current_view = view
        view.on_show()

    def _show_admin_creation_view(self) -> None:
        """Show the admin creation view."""
        from views.admin_creation_view import AdminCreationView

        self._clear_container()

        view = AdminCreationView(
            parent=self.container,
            app=self,
            db=self.db,
            on_complete=self._on_admin_created,
        )
        view.pack(fill="both", expand=True)
        self.current_view = view
        view.on_show()

    def _show_login_view(self) -> None:
        """Show the login view."""
        from views.login_view import LoginView

        self._clear_container()

        view = LoginView(
            parent=self.container,
            app=self,
            db=self.db,
            on_login=self._on_login_success,
            on_change_folder=self._on_change_folder,
        )
        view.pack(fill="both", expand=True)
        self.current_view = view
        view.on_show()

    def _show_main_view(self) -> None:
        """Show the main application view."""
        from views.main_view import MainView

        self._clear_container()

        view = MainView(
            parent=self.container,
            app=self,
        )
        view.pack(fill="both", expand=True)
        self.current_view = view
        view.on_show()

        # Update window title with user info
        user = self.session_manager.current_user
        if user:
            self.title(f"{APP_NAME} - {user.full_name} ({user.role_display})")

    def _clear_container(self) -> None:
        """Clear the current view from the container."""
        if self.current_view:
            self.current_view.on_hide()
            self.current_view.destroy()
            self.current_view = None

    def _on_setup_complete(self) -> None:
        """Called when setup wizard completes."""
        logger.info("Setup complete, connecting to database")
        self._connect_database()

    def _on_admin_created(self) -> None:
        """Called when admin account is created."""
        logger.info("Admin created, showing main view")
        self._show_main_view()

    def _on_login_success(self) -> None:
        """Called when login succeeds."""
        logger.info("Login successful, showing main view")
        self._show_main_view()

    def _on_change_folder(self) -> None:
        """Called when user wants to change the shared folder."""
        logger.info("User requested folder change")
        self._show_setup_view()

    def logout(self) -> None:
        """Log out the current user."""
        logger.info("User logging out")
        self.session_manager.logout()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self._show_login_view()

    def run(self) -> None:
        """Run the application main loop."""
        logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
        self.mainloop()
