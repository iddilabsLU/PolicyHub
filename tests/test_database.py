"""
PolicyHub Database Tests

Tests for the database manager and schema.
"""

from pathlib import Path

import pytest

from app.constants import DEFAULT_CATEGORIES, DEFAULT_SETTINGS
from core.database import DatabaseManager


class TestDatabaseManager:
    """Tests for DatabaseManager class."""

    def test_database_creation(self, temp_db_path: Path):
        """Test that database is created with schema."""
        # Ensure parent exists
        temp_db_path.parent.mkdir(parents=True, exist_ok=True)

        db = DatabaseManager(temp_db_path)
        assert not db.database_exists()

        db.initialize_schema()
        assert db.database_exists()

    def test_tables_created(self, db: DatabaseManager):
        """Test that all tables are created."""
        expected_tables = [
            "users",
            "documents",
            "attachments",
            "document_links",
            "document_history",
            "categories",
            "settings",
        ]

        for table in expected_tables:
            row = db.fetch_one(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            )
            assert row is not None, f"Table {table} should exist"

    def test_default_categories_seeded(self, db: DatabaseManager):
        """Test that default categories are seeded."""
        rows = db.fetch_all("SELECT * FROM categories ORDER BY sort_order")

        assert len(rows) == len(DEFAULT_CATEGORIES)

        for row, (code, name, sort_order) in zip(rows, DEFAULT_CATEGORIES):
            assert row["code"] == code
            assert row["name"] == name
            assert row["sort_order"] == sort_order
            assert row["is_active"] == 1

    def test_default_settings_seeded(self, db: DatabaseManager):
        """Test that default settings are seeded."""
        for key, expected_value in DEFAULT_SETTINGS.items():
            value = db.get_setting(key)
            if key == "master_password_hash":
                # Master password hash is a bcrypt hash, not the empty string from DEFAULT_SETTINGS
                assert value is not None, f"Setting {key} should be set"
                assert value.startswith("$2b$"), f"Setting {key} should be a bcrypt hash"
            else:
                assert value == expected_value, f"Setting {key} should be {expected_value}"

    def test_set_and_get_setting(self, db: DatabaseManager):
        """Test setting and getting a setting value."""
        db.set_setting("test_key", "test_value")
        assert db.get_setting("test_key") == "test_value"

        # Update the setting
        db.set_setting("test_key", "new_value")
        assert db.get_setting("test_key") == "new_value"

    def test_count_users_empty(self, db: DatabaseManager):
        """Test counting users when empty."""
        assert db.count_users() == 0
        assert not db.has_any_users()

    def test_connection_context_manager(self, db: DatabaseManager):
        """Test that connection context manager works."""
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

    def test_fetch_one_not_found(self, db: DatabaseManager):
        """Test fetch_one returns None for missing row."""
        result = db.fetch_one(
            "SELECT * FROM users WHERE username = ?",
            ("nonexistent",),
        )
        assert result is None

    def test_fetch_all_empty(self, db: DatabaseManager):
        """Test fetch_all returns empty list for no results."""
        results = db.fetch_all("SELECT * FROM users")
        assert results == []

    def test_database_info(self, db: DatabaseManager):
        """Test getting database info."""
        info = db.get_database_info()

        assert "path" in info
        assert info["exists"] is True
        assert info["size_bytes"] > 0
        assert info["users_count"] == 0
        assert info["documents_count"] == 0
        assert info["categories_count"] == len(DEFAULT_CATEGORIES)
