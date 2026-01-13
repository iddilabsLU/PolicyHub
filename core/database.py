"""
PolicyHub Database Manager

Manages SQLite database connections with support for network shares.
Uses WAL mode and appropriate timeouts for concurrent multi-user access.
"""

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from app.constants import (
    DATABASE_BUSY_TIMEOUT,
    DATABASE_TIMEOUT,
    DEFAULT_CATEGORIES,
    DEFAULT_SETTINGS,
)

logger = logging.getLogger(__name__)


# SQL Schema Definitions
SCHEMA_SQL = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE,
    role TEXT NOT NULL CHECK (role IN ('ADMIN', 'EDITOR', 'VIEWER')),
    is_active INTEGER NOT NULL DEFAULT 1,
    force_password_change INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    created_by TEXT,
    last_login TEXT,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    doc_type TEXT NOT NULL CHECK (doc_type IN ('POLICY', 'PROCEDURE', 'MANUAL', 'HR_OTHERS')),
    doc_ref TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    owner TEXT NOT NULL,
    approver TEXT,
    status TEXT NOT NULL CHECK (status IN ('DRAFT', 'ACTIVE', 'UNDER_REVIEW', 'SUPERSEDED', 'ARCHIVED')),
    version TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    last_review_date TEXT NOT NULL,
    next_review_date TEXT NOT NULL,
    review_frequency TEXT NOT NULL CHECK (review_frequency IN ('ANNUAL', 'SEMI_ANNUAL', 'QUARTERLY', 'AD_HOC')),
    notes TEXT,
    mandatory_read_all INTEGER NOT NULL DEFAULT 0,
    applicable_entity TEXT,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    FOREIGN KEY (category) REFERENCES categories(code),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (updated_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_documents_doc_ref ON documents(doc_ref);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_next_review ON documents(next_review_date);
CREATE INDEX IF NOT EXISTS idx_documents_mandatory ON documents(mandatory_read_all);
CREATE INDEX IF NOT EXISTS idx_documents_entity ON documents(applicable_entity);

-- Attachments table
CREATE TABLE IF NOT EXISTS attachments (
    attachment_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type TEXT,
    version_label TEXT NOT NULL,
    is_current INTEGER NOT NULL DEFAULT 1,
    uploaded_at TEXT NOT NULL,
    uploaded_by TEXT NOT NULL,
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_attachments_doc_id ON attachments(doc_id);

-- Document Links table
CREATE TABLE IF NOT EXISTS document_links (
    link_id TEXT PRIMARY KEY,
    parent_doc_id TEXT NOT NULL,
    child_doc_id TEXT NOT NULL,
    link_type TEXT NOT NULL CHECK (link_type IN ('IMPLEMENTS', 'REFERENCES', 'SUPERSEDES')),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    UNIQUE (parent_doc_id, child_doc_id, link_type),
    FOREIGN KEY (parent_doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
    FOREIGN KEY (child_doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- Document History table
CREATE TABLE IF NOT EXISTS document_history (
    history_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('CREATED', 'UPDATED', 'STATUS_CHANGED', 'REVIEWED', 'ATTACHMENT_ADDED', 'ATTACHMENT_REMOVED', 'LINK_ADDED', 'LINK_REMOVED')),
    field_changed TEXT,
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_history_doc_id ON document_history(doc_id);

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 99
);

-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT,
    updated_by TEXT,
    FOREIGN KEY (updated_by) REFERENCES users(user_id)
);

-- Entities table (for applicable entity dropdown)
CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL COLLATE NOCASE,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
"""


class DatabaseManager:
    """
    Manages SQLite database connections.

    Designed for shared folder deployment with multiple concurrent users.
    Uses WAL mode and appropriate timeouts to handle network latency
    and concurrent access.
    """

    _instance: Optional["DatabaseManager"] = None

    def __init__(self, db_path: Path):
        """
        Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path

    @classmethod
    def get_instance(cls, db_path: Optional[Path] = None) -> "DatabaseManager":
        """
        Get the singleton DatabaseManager instance.

        Args:
            db_path: Path to the database (required on first call)

        Returns:
            DatabaseManager instance
        """
        if cls._instance is None:
            if db_path is None:
                raise ValueError("db_path required for first initialization")
            cls._instance = cls(db_path)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (mainly for testing)."""
        cls._instance = None

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a database connection with appropriate settings.

        Uses context manager pattern to ensure connections are properly closed.
        Configures:
        - 30 second timeout for busy database
        - WAL mode for better concurrent access
        - Row factory for dict-like access

        Yields:
            SQLite connection
        """
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=DATABASE_TIMEOUT,
            isolation_level=None,  # Autocommit mode
        )

        try:
            # Configure for network share access
            conn.execute(f"PRAGMA busy_timeout = {DATABASE_BUSY_TIMEOUT}")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA foreign_keys = ON")

            # Enable dict-like row access
            conn.row_factory = sqlite3.Row

            yield conn

        finally:
            conn.close()

    def database_exists(self) -> bool:
        """
        Check if the database file exists.

        Returns:
            True if the database file exists
        """
        return self.db_path.exists()

    def initialize_schema(self) -> None:
        """
        Create the database schema if it doesn't exist.

        Creates all tables, indexes, and seeds default data.
        Also runs migrations to update existing databases.
        """
        logger.info(f"Initializing database schema at: {self.db_path}")

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self.get_connection() as conn:
            # Create tables
            conn.executescript(SCHEMA_SQL)

            # Run migrations for existing databases
            self._run_migrations(conn)

            # Seed default categories
            self._seed_categories(conn)

            # Seed default settings
            self._seed_settings(conn)

        logger.info("Database schema initialized successfully")

    def _run_migrations(self, conn: sqlite3.Connection) -> None:
        """
        Run database migrations to update existing databases.

        Adds new columns and tables that may be missing from older databases.

        Args:
            conn: Database connection
        """
        # Check documents table columns
        cursor = conn.execute("PRAGMA table_info(documents)")
        columns = {row[1] for row in cursor.fetchall()}

        # Migration: Add mandatory_read_all column if missing
        if "mandatory_read_all" not in columns:
            logger.info("Migration: Adding mandatory_read_all column to documents")
            conn.execute(
                "ALTER TABLE documents ADD COLUMN mandatory_read_all INTEGER NOT NULL DEFAULT 0"
            )

        # Migration: Add applicable_entity column if missing
        if "applicable_entity" not in columns:
            logger.info("Migration: Adding applicable_entity column to documents")
            conn.execute(
                "ALTER TABLE documents ADD COLUMN applicable_entity TEXT"
            )

        # Migration: Create entities table if missing
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='entities'"
        )
        if cursor.fetchone() is None:
            logger.info("Migration: Creating entities table")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    entity_id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)")

        # Migration: Create new indexes if missing
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_mandatory ON documents(mandatory_read_all)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_entity ON documents(applicable_entity)")

        # Migration: Update REGISTER to HR_OTHERS for existing documents
        conn.execute("UPDATE documents SET doc_type = 'HR_OTHERS' WHERE doc_type = 'REGISTER'")

        # Check users table columns for user management migrations
        cursor = conn.execute("PRAGMA table_info(users)")
        user_columns = {row[1] for row in cursor.fetchall()}

        # Migration: Add force_password_change column if missing
        if "force_password_change" not in user_columns:
            logger.info("Migration: Adding force_password_change column to users")
            conn.execute(
                "ALTER TABLE users ADD COLUMN force_password_change INTEGER NOT NULL DEFAULT 0"
            )

        # Migration: Create email index if missing
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

    def _seed_categories(self, conn: sqlite3.Connection) -> None:
        """
        Insert default categories if they don't exist.

        Args:
            conn: Database connection
        """
        cursor = conn.execute("SELECT COUNT(*) FROM categories")
        count = cursor.fetchone()[0]

        if count == 0:
            logger.info("Seeding default categories")
            for code, name, sort_order in DEFAULT_CATEGORIES:
                conn.execute(
                    """
                    INSERT INTO categories (code, name, is_active, sort_order)
                    VALUES (?, ?, 1, ?)
                    """,
                    (code, name, sort_order),
                )

    def _seed_settings(self, conn: sqlite3.Connection) -> None:
        """
        Insert default settings if they don't exist.

        Args:
            conn: Database connection
        """
        cursor = conn.execute("SELECT COUNT(*) FROM settings")
        count = cursor.fetchone()[0]

        if count == 0:
            logger.info("Seeding default settings")
            for key, value in DEFAULT_SETTINGS.items():
                conn.execute(
                    """
                    INSERT INTO settings (key, value)
                    VALUES (?, ?)
                    """,
                    (key, value),
                )

    def execute(
        self,
        query: str,
        params: tuple = (),
    ) -> sqlite3.Cursor:
        """
        Execute a SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Cursor with results
        """
        with self.get_connection() as conn:
            return conn.execute(query, params)

    def execute_many(
        self,
        query: str,
        params_list: list[tuple],
    ) -> None:
        """
        Execute a SQL query with multiple parameter sets.

        Args:
            query: SQL query string
            params_list: List of parameter tuples
        """
        with self.get_connection() as conn:
            conn.executemany(query, params_list)

    def fetch_one(
        self,
        query: str,
        params: tuple = (),
    ) -> Optional[sqlite3.Row]:
        """
        Execute a query and fetch one result.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Single row or None
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()

    def fetch_all(
        self,
        query: str,
        params: tuple = (),
    ) -> list[sqlite3.Row]:
        """
        Execute a query and fetch all results.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of rows
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def get_setting(self, key: str) -> Optional[str]:
        """
        Get a setting value by key.

        Args:
            key: Setting key

        Returns:
            Setting value or None
        """
        row = self.fetch_one(
            "SELECT value FROM settings WHERE key = ?",
            (key,),
        )
        return row["value"] if row else None

    def set_setting(self, key: str, value: str, user_id: Optional[str] = None) -> None:
        """
        Set a setting value.

        Args:
            key: Setting key
            value: Setting value
            user_id: User who updated the setting
        """
        from utils.dates import get_now

        with self.get_connection() as conn:
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

    def count_users(self) -> int:
        """
        Count the number of users in the database.

        Returns:
            User count
        """
        row = self.fetch_one("SELECT COUNT(*) as count FROM users")
        return row["count"] if row else 0

    def has_any_users(self) -> bool:
        """
        Check if any users exist in the database.

        Returns:
            True if at least one user exists
        """
        return self.count_users() > 0

    def vacuum(self) -> None:
        """
        Optimize the database by running VACUUM.

        This rebuilds the database file to reclaim unused space.
        Should be run periodically or after many deletions.
        """
        with self.get_connection() as conn:
            conn.execute("VACUUM")
        logger.info("Database vacuumed")

    def get_database_info(self) -> dict:
        """
        Get information about the database.

        Returns:
            Dictionary with database statistics
        """
        info = {
            "path": str(self.db_path),
            "exists": self.database_exists(),
            "size_bytes": 0,
        }

        if self.database_exists():
            info["size_bytes"] = self.db_path.stat().st_size

            with self.get_connection() as conn:
                # Get table counts
                tables = ["users", "documents", "attachments", "document_links", "document_history", "categories"]
                for table in tables:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    info[f"{table}_count"] = cursor.fetchone()[0]

        return info
