"""
PolicyHub Config Tests

Tests for the configuration manager.
"""

import json
from pathlib import Path

import pytest

from core.config import ConfigManager, LocalConfig


class TestLocalConfig:
    """Tests for LocalConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LocalConfig()
        assert config.shared_folder_path is None
        assert config.remembered_username is None
        assert not config.is_configured()

    def test_is_configured(self):
        """Test is_configured with path set."""
        config = LocalConfig(shared_folder_path="/some/path")
        assert config.is_configured()

    def test_is_configured_empty_string(self):
        """Test is_configured with empty string."""
        config = LocalConfig(shared_folder_path="")
        assert not config.is_configured()

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = LocalConfig(
            shared_folder_path="/test/path",
            remembered_username="testuser",
        )
        data = config.to_dict()

        assert data["shared_folder_path"] == "/test/path"
        assert data["remembered_username"] == "testuser"

    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "shared_folder_path": "/test/path",
            "remembered_username": "testuser",
        }
        config = LocalConfig.from_dict(data)

        assert config.shared_folder_path == "/test/path"
        assert config.remembered_username == "testuser"

    def test_from_dict_missing_keys(self):
        """Test creating config from partial dictionary."""
        data = {"shared_folder_path": "/test/path"}
        config = LocalConfig.from_dict(data)

        assert config.shared_folder_path == "/test/path"
        assert config.remembered_username is None


class TestConfigManager:
    """Tests for ConfigManager class."""

    def test_singleton_pattern(self, temp_dir: Path, monkeypatch):
        """Test that ConfigManager is a singleton."""
        ConfigManager._instance = None

        def mock_get_local_app_folder():
            return temp_dir / "PolicyHub"

        monkeypatch.setattr(ConfigManager, "get_local_app_folder", staticmethod(mock_get_local_app_folder))

        manager1 = ConfigManager.get_instance()
        manager2 = ConfigManager.get_instance()

        assert manager1 is manager2

        # Cleanup
        ConfigManager._instance = None

    def test_load_default_config(self, temp_dir: Path, monkeypatch):
        """Test loading config when file doesn't exist."""
        ConfigManager._instance = None
        ConfigManager._config = None

        def mock_get_local_app_folder():
            return temp_dir / "PolicyHub"

        monkeypatch.setattr(ConfigManager, "get_local_app_folder", staticmethod(mock_get_local_app_folder))

        manager = ConfigManager()
        config = manager.load()

        assert config.shared_folder_path is None
        assert config.remembered_username is None

        # Cleanup
        ConfigManager._instance = None
        ConfigManager._config = None

    def test_save_and_load_config(self, temp_dir: Path, monkeypatch):
        """Test saving and loading config."""
        ConfigManager._instance = None
        ConfigManager._config = None

        def mock_get_local_app_folder():
            return temp_dir / "PolicyHub"

        monkeypatch.setattr(ConfigManager, "get_local_app_folder", staticmethod(mock_get_local_app_folder))

        manager = ConfigManager()

        # Save config
        config = LocalConfig(
            shared_folder_path="/test/path",
            remembered_username="testuser",
        )
        manager.save(config)

        # Clear cache and reload
        manager._config = None
        loaded = manager.load()

        assert loaded.shared_folder_path == "/test/path"
        assert loaded.remembered_username == "testuser"

        # Cleanup
        ConfigManager._instance = None
        ConfigManager._config = None

    def test_update_config(self, temp_dir: Path, monkeypatch):
        """Test updating specific config values."""
        ConfigManager._instance = None
        ConfigManager._config = None

        def mock_get_local_app_folder():
            return temp_dir / "PolicyHub"

        monkeypatch.setattr(ConfigManager, "get_local_app_folder", staticmethod(mock_get_local_app_folder))

        manager = ConfigManager()

        # Update shared folder path
        manager.update(shared_folder_path="/new/path")

        config = manager.load()
        assert config.shared_folder_path == "/new/path"

        # Update username without affecting path
        manager.update(remembered_username="newuser")

        config = manager.load()
        assert config.shared_folder_path == "/new/path"
        assert config.remembered_username == "newuser"

        # Cleanup
        ConfigManager._instance = None
        ConfigManager._config = None

    def test_validate_shared_folder_empty(self, temp_dir: Path, monkeypatch):
        """Test validating empty path."""
        ConfigManager._instance = None

        def mock_get_local_app_folder():
            return temp_dir / "PolicyHub"

        monkeypatch.setattr(ConfigManager, "get_local_app_folder", staticmethod(mock_get_local_app_folder))

        manager = ConfigManager()
        is_valid, error = manager.validate_shared_folder("")

        assert not is_valid
        assert "empty" in error.lower()

        # Cleanup
        ConfigManager._instance = None

    def test_validate_shared_folder_not_exists(self, temp_dir: Path, monkeypatch):
        """Test validating non-existent path."""
        ConfigManager._instance = None

        def mock_get_local_app_folder():
            return temp_dir / "PolicyHub"

        monkeypatch.setattr(ConfigManager, "get_local_app_folder", staticmethod(mock_get_local_app_folder))

        manager = ConfigManager()
        is_valid, error = manager.validate_shared_folder("/nonexistent/path")

        assert not is_valid
        assert "exist" in error.lower()

        # Cleanup
        ConfigManager._instance = None

    def test_validate_shared_folder_valid(self, temp_dir: Path, monkeypatch):
        """Test validating valid folder path."""
        ConfigManager._instance = None

        def mock_get_local_app_folder():
            return temp_dir / "PolicyHub"

        monkeypatch.setattr(ConfigManager, "get_local_app_folder", staticmethod(mock_get_local_app_folder))

        manager = ConfigManager()

        # Create a valid folder
        valid_folder = temp_dir / "shared"
        valid_folder.mkdir(parents=True)

        is_valid, error = manager.validate_shared_folder(str(valid_folder))

        assert is_valid
        assert error == ""

        # Cleanup
        ConfigManager._instance = None

    def test_clear_remembered_username(self, temp_dir: Path, monkeypatch):
        """Test clearing remembered username."""
        ConfigManager._instance = None
        ConfigManager._config = None

        def mock_get_local_app_folder():
            return temp_dir / "PolicyHub"

        monkeypatch.setattr(ConfigManager, "get_local_app_folder", staticmethod(mock_get_local_app_folder))

        manager = ConfigManager()

        # Set username first
        manager.update(remembered_username="testuser")
        assert manager.load().remembered_username == "testuser"

        # Clear it
        manager.clear_remembered_username()
        assert manager.load().remembered_username is None

        # Cleanup
        ConfigManager._instance = None
        ConfigManager._config = None
