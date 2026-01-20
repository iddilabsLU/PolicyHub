"""
PolicyHub Settings Service

Handles CRUD operations for application settings stored as key-value pairs.
"""

import logging
from typing import Dict, Optional

from core.database import DatabaseManager
from core.permissions import Permission, require_permission
from core.session import SessionManager
from utils.dates import get_now

logger = logging.getLogger(__name__)


class SettingsService:
    """
    Service for managing application settings.

    Settings are stored in the `settings` table as key-value pairs.
    Provides typed getters for common settings.
    """

    # Setting key constants
    COMPANY_NAME = "company_name"
    WARNING_THRESHOLD = "warning_threshold_days"
    UPCOMING_THRESHOLD = "upcoming_threshold_days"
    DATE_FORMAT = "date_format"
    DEFAULT_REVIEW_FREQUENCY = "default_review_frequency"
    REQUIRE_LOGIN = "require_login"
    MASTER_PASSWORD_HASH = "master_password_hash"

    # Default values
    DEFAULTS = {
        COMPANY_NAME: "",
        WARNING_THRESHOLD: "30",
        UPCOMING_THRESHOLD: "90",
        DATE_FORMAT: "DD/MM/YYYY",
        DEFAULT_REVIEW_FREQUENCY: "ANNUAL",
    }

    def __init__(self, db: DatabaseManager):
        """
        Initialize the settings service.

        Args:
            db: Database manager instance
        """
        self.db = db
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        """Ensure default settings exist in the database."""
        existing = self.get_all_settings()
        for key, default_value in self.DEFAULTS.items():
            if key not in existing:
                self._insert_setting(key, default_value)

    def _insert_setting(self, key: str, value: str) -> None:
        """Insert a setting without permission check (for defaults)."""
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
                """,
                (key, value, get_now()),
            )

    def get_setting(self, key: str) -> Optional[str]:
        """
        Get a setting value by key.

        Args:
            key: Setting key

        Returns:
            Setting value or None if not found
        """
        row = self.db.fetch_one(
            "SELECT value FROM settings WHERE key = ?",
            (key,),
        )
        if row:
            return row["value"]
        return self.DEFAULTS.get(key)

    def get_all_settings(self) -> Dict[str, str]:
        """
        Get all settings as a dictionary.

        Returns:
            Dictionary mapping keys to values
        """
        rows = self.db.fetch_all("SELECT key, value FROM settings")
        return {row["key"]: row["value"] for row in rows}

    @require_permission(Permission.CHANGE_SETTINGS)
    def set_setting(self, key: str, value: str) -> None:
        """
        Set a setting value.

        Args:
            key: Setting key
            value: Setting value

        Raises:
            PermissionError: If user lacks permission
        """
        session = SessionManager.get_instance()
        user_id = session.current_user.user_id if session.current_user else None

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO settings (key, value, updated_at, updated_by)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at,
                    updated_by = excluded.updated_by
                """,
                (key, value, get_now(), user_id),
            )

        logger.info(f"Setting updated: {key}")

    @require_permission(Permission.CHANGE_SETTINGS)
    def update_settings(self, settings: Dict[str, str]) -> None:
        """
        Update multiple settings at once.

        Args:
            settings: Dictionary of key-value pairs to update

        Raises:
            PermissionError: If user lacks permission
        """
        session = SessionManager.get_instance()
        user_id = session.current_user.user_id if session.current_user else None
        now = get_now()

        with self.db.get_connection() as conn:
            for key, value in settings.items():
                conn.execute(
                    """
                    INSERT INTO settings (key, value, updated_at, updated_by)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        updated_at = excluded.updated_at,
                        updated_by = excluded.updated_by
                    """,
                    (key, value, now, user_id),
                )

        logger.info(f"Settings updated: {list(settings.keys())}")

    # Typed getters for common settings

    def get_company_name(self) -> str:
        """
        Get the company name setting.

        Returns:
            Company name or empty string if not set
        """
        return self.get_setting(self.COMPANY_NAME) or ""

    def get_warning_threshold_days(self) -> int:
        """
        Get the warning threshold in days.

        Documents due within this many days are marked as "Due Soon".

        Returns:
            Number of days (default: 30)
        """
        value = self.get_setting(self.WARNING_THRESHOLD)
        try:
            return int(value) if value else 30
        except ValueError:
            return 30

    def get_upcoming_threshold_days(self) -> int:
        """
        Get the upcoming threshold in days.

        Documents due within this many days are marked as "Upcoming".

        Returns:
            Number of days (default: 90)
        """
        value = self.get_setting(self.UPCOMING_THRESHOLD)
        try:
            return int(value) if value else 90
        except ValueError:
            return 90

    def get_date_format(self) -> str:
        """
        Get the date display format.

        Returns:
            Date format string (default: DD/MM/YYYY)
        """
        return self.get_setting(self.DATE_FORMAT) or "DD/MM/YYYY"

    def get_default_review_frequency(self) -> str:
        """
        Get the default review frequency for new documents.

        Returns:
            Review frequency code (default: ANNUAL)
        """
        return self.get_setting(self.DEFAULT_REVIEW_FREQUENCY) or "ANNUAL"

    # Authentication settings

    def get_require_login(self) -> bool:
        """
        Get whether login is required to use the application.

        Returns:
            True if login is required, False otherwise (default: False for new DBs)
        """
        value = self.get_setting(self.REQUIRE_LOGIN)
        return value.lower() == "true" if value else False

    @require_permission(Permission.CHANGE_SETTINGS)
    def set_require_login(self, require: bool) -> None:
        """
        Set whether login is required to use the application.

        Args:
            require: True to require login, False to allow auto-login

        Raises:
            PermissionError: If user lacks CHANGE_SETTINGS permission
        """
        self.set_setting(self.REQUIRE_LOGIN, "true" if require else "false")
        logger.info(f"Require login setting changed to: {require}")

    def set_require_login_direct(self, require: bool) -> None:
        """
        Set require_login without permission check.

        Used during initial setup when no user is logged in yet.

        Args:
            require: True to require login, False to allow auto-login
        """
        self._insert_setting(self.REQUIRE_LOGIN, "true" if require else "false")
        logger.info(f"Require login setting set to: {require} (direct)")

    def get_master_password_hash(self) -> Optional[str]:
        """
        Get the master password hash.

        Returns:
            bcrypt hash of the master password, or None if not set
        """
        return self.get_setting(self.MASTER_PASSWORD_HASH)

    @require_permission(Permission.MANAGE_USERS)
    def set_master_password(self, new_password: str) -> None:
        """
        Set a new master password.

        Args:
            new_password: The new master password (will be hashed)

        Raises:
            PermissionError: If user lacks MANAGE_USERS permission
            ValueError: If password doesn't meet requirements
        """
        from services.auth_service import AuthService
        from utils.validators import validate_password

        # Validate password strength
        is_valid, error = validate_password(new_password)
        if not is_valid:
            raise ValueError(error)

        # Hash and store
        hashed = AuthService.hash_password(new_password)
        self.set_setting(self.MASTER_PASSWORD_HASH, hashed)
        logger.info("Master password changed")
