"""
PolicyHub Test Configuration

Pytest fixtures for testing PolicyHub components.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from app.constants import DEFAULT_CATEGORIES, DEFAULT_SETTINGS
from core.config import ConfigManager, LocalConfig
from core.database import DatabaseManager
from core.session import SessionManager


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_db_path(temp_dir: Path) -> Path:
    """Get a temporary database path."""
    return temp_dir / "data" / "policyhub.db"


@pytest.fixture
def db(temp_db_path: Path) -> Generator[DatabaseManager, None, None]:
    """Create a temporary database for testing."""
    # Ensure parent directory exists
    temp_db_path.parent.mkdir(parents=True, exist_ok=True)

    # Reset the singleton
    DatabaseManager.reset_instance()

    # Create database manager
    db_manager = DatabaseManager(temp_db_path)
    db_manager.initialize_schema()

    yield db_manager

    # Cleanup
    DatabaseManager.reset_instance()


@pytest.fixture
def session_manager() -> Generator[SessionManager, None, None]:
    """Get a fresh session manager."""
    SessionManager.reset_instance()
    manager = SessionManager.get_instance()
    yield manager
    SessionManager.reset_instance()


@pytest.fixture
def config_manager(temp_dir: Path, monkeypatch) -> Generator[ConfigManager, None, None]:
    """Create a temporary config manager."""
    # Patch the home directory to use temp dir
    def mock_get_local_app_folder():
        return temp_dir / "PolicyHub"

    ConfigManager._instance = None
    ConfigManager._config = None

    manager = ConfigManager.get_instance()
    monkeypatch.setattr(ConfigManager, "get_local_app_folder", staticmethod(mock_get_local_app_folder))

    yield manager

    # Cleanup
    ConfigManager._instance = None
    ConfigManager._config = None


@pytest.fixture
def test_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User",
        "email": "test@example.com",
    }


@pytest.fixture
def admin_user_data() -> dict:
    """Sample admin user data for testing."""
    return {
        "username": "admin",
        "password": "adminpassword123",
        "full_name": "Admin User",
        "email": "admin@example.com",
    }


@pytest.fixture
def sample_document_data() -> dict:
    """Sample document data for testing."""
    return {
        "doc_type": "POLICY",
        "doc_ref": "POL-AML-001",
        "title": "Anti-Money Laundering Policy",
        "category": "AML",
        "owner": "Compliance Officer",
        "status": "ACTIVE",
        "version": "1.0",
        "effective_date": "2024-01-15",
        "last_review_date": "2024-01-15",
        "next_review_date": "2025-01-15",
        "review_frequency": "ANNUAL",
        "description": "Policy for AML compliance",
        "approver": "CEO",
        "notes": "Initial version",
    }


@pytest.fixture
def logged_in_admin(db, admin_user_data, session_manager):
    """Create and login an admin user for testing."""
    from services.auth_service import AuthService

    auth = AuthService(db)
    user = auth.create_first_admin(
        username=admin_user_data["username"],
        password=admin_user_data["password"],
        full_name=admin_user_data["full_name"],
        email=admin_user_data["email"],
    )

    auth.login(admin_user_data["username"], admin_user_data["password"])

    return user
