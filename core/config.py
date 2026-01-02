"""
PolicyHub Local Configuration Manager

Manages the local config.json file stored in %APPDATA%\\Local\\PolicyHub\\.
This file stores user-specific settings like the shared folder path and
remembered username.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from app.constants import LOCAL_APP_FOLDER, LOCAL_CONFIG_FILE, LOCAL_LOGS_FOLDER

logger = logging.getLogger(__name__)


@dataclass
class LocalConfig:
    """
    Local configuration stored on each user's machine.

    Attributes:
        shared_folder_path: Path to the shared network folder (e.g., \\\\server\\PolicyHub)
        remembered_username: Username to pre-fill on login screen (if "remember me" checked)
    """

    shared_folder_path: Optional[str] = None
    remembered_username: Optional[str] = None

    def is_configured(self) -> bool:
        """Check if the shared folder path has been set."""
        return self.shared_folder_path is not None and len(self.shared_folder_path) > 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LocalConfig":
        """Create a LocalConfig from a dictionary."""
        return cls(
            shared_folder_path=data.get("shared_folder_path"),
            remembered_username=data.get("remembered_username"),
        )


class ConfigManager:
    """
    Manages the local configuration file.

    The configuration is stored in:
    - Windows: %LOCALAPPDATA%\\PolicyHub\\config.json
    - Example: C:\\Users\\John\\AppData\\Local\\PolicyHub\\config.json
    """

    _instance: Optional["ConfigManager"] = None
    _config: Optional[LocalConfig] = None

    def __new__(cls) -> "ConfigManager":
        """Singleton pattern - only one ConfigManager instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ConfigManager":
        """Get the singleton ConfigManager instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def get_local_app_folder() -> Path:
        """
        Get the local app data folder path.

        Returns:
            Path to %LOCALAPPDATA%\\PolicyHub
        """
        # On Windows, this resolves to C:\Users\<user>\AppData\Local
        local_app_data = Path.home() / "AppData" / "Local"
        return local_app_data / LOCAL_APP_FOLDER

    @staticmethod
    def get_config_path() -> Path:
        """
        Get the path to the config.json file.

        Returns:
            Path to config.json
        """
        return ConfigManager.get_local_app_folder() / LOCAL_CONFIG_FILE

    @staticmethod
    def get_logs_folder() -> Path:
        """
        Get the path to the logs folder.

        Returns:
            Path to the logs folder
        """
        return ConfigManager.get_local_app_folder() / LOCAL_LOGS_FOLDER

    def ensure_local_folders(self) -> None:
        """
        Ensure the local app folder and subfolders exist.

        Creates:
        - %LOCALAPPDATA%\\PolicyHub\\
        - %LOCALAPPDATA%\\PolicyHub\\logs\\
        """
        app_folder = self.get_local_app_folder()
        logs_folder = self.get_logs_folder()

        try:
            app_folder.mkdir(parents=True, exist_ok=True)
            logs_folder.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Local folders ensured at: {app_folder}")
        except OSError as e:
            logger.error(f"Failed to create local folders: {e}")
            raise

    def load(self) -> LocalConfig:
        """
        Load the configuration from disk.

        Returns:
            LocalConfig instance (creates default if file doesn't exist)
        """
        if self._config is not None:
            return self._config

        config_path = self.get_config_path()

        if not config_path.exists():
            logger.info("No config file found, using defaults")
            self._config = LocalConfig()
            return self._config

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._config = LocalConfig.from_dict(data)
                logger.info(f"Config loaded from: {config_path}")
                return self._config
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid config file, using defaults: {e}")
            self._config = LocalConfig()
            return self._config
        except OSError as e:
            logger.error(f"Failed to read config file: {e}")
            self._config = LocalConfig()
            return self._config

    def save(self, config: LocalConfig) -> None:
        """
        Save the configuration to disk.

        Args:
            config: LocalConfig instance to save
        """
        self.ensure_local_folders()
        config_path = self.get_config_path()

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, indent=2)
            self._config = config
            logger.info(f"Config saved to: {config_path}")
        except OSError as e:
            logger.error(f"Failed to save config file: {e}")
            raise

    def update(self, **kwargs) -> LocalConfig:
        """
        Update specific configuration values and save.

        Args:
            **kwargs: Fields to update (shared_folder_path, remembered_username)

        Returns:
            Updated LocalConfig instance
        """
        config = self.load()

        if "shared_folder_path" in kwargs:
            config.shared_folder_path = kwargs["shared_folder_path"]
        if "remembered_username" in kwargs:
            config.remembered_username = kwargs["remembered_username"]

        self.save(config)
        return config

    def clear_remembered_username(self) -> None:
        """Clear the remembered username."""
        self.update(remembered_username=None)

    def get_shared_folder_path(self) -> Optional[Path]:
        """
        Get the shared folder path as a Path object.

        Returns:
            Path to the shared folder, or None if not configured
        """
        config = self.load()
        if config.shared_folder_path:
            return Path(config.shared_folder_path)
        return None

    def validate_shared_folder(self, path: str) -> tuple[bool, str]:
        """
        Validate that a path is suitable for use as the shared folder.

        Args:
            path: Path to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not path:
            return False, "Path cannot be empty"

        try:
            folder = Path(path)

            if not folder.exists():
                return False, "Folder does not exist"

            if not folder.is_dir():
                return False, "Path is not a directory"

            # Try to write a test file to check permissions
            test_file = folder / ".policyhub_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except OSError:
                return False, "No write permission to folder"

            return True, ""

        except Exception as e:
            return False, f"Invalid path: {str(e)}"

    def reset(self) -> None:
        """Reset to default configuration (clears all saved settings)."""
        self._config = LocalConfig()
        config_path = self.get_config_path()
        if config_path.exists():
            try:
                config_path.unlink()
                logger.info("Config file deleted")
            except OSError as e:
                logger.error(f"Failed to delete config file: {e}")
