"""
PolicyHub Backup Service

Handles backup creation and restoration for the application.
Includes database, attachments, and configuration.
"""

import json
import logging
import os
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from core.config import ConfigManager
from core.database import DatabaseManager
from core.permissions import Permission, require_permission
from core.session import SessionManager
from utils.dates import get_now
from utils.files import generate_uuid

logger = logging.getLogger(__name__)


@dataclass
class BackupInfo:
    """Information about a backup."""

    backup_id: str
    backup_path: str
    backup_type: str
    created_at: str
    created_by: str
    size_bytes: Optional[int]
    notes: Optional[str]

    @classmethod
    def from_row(cls, row) -> "BackupInfo":
        """Create BackupInfo from database row."""
        return cls(
            backup_id=row["backup_id"],
            backup_path=row["backup_path"],
            backup_type=row["backup_type"],
            created_at=row["created_at"],
            created_by=row["created_by"],
            size_bytes=row["size_bytes"],
            notes=row["notes"],
        )


class BackupService:
    """
    Service for creating and restoring backups.

    Backups include:
    - SQLite database file
    - All attachment files
    - Backup metadata (timestamp, version, user)
    """

    BACKUP_INFO_FILE = "backup_info.json"
    DATABASE_FILE = "policyhub.db"
    ATTACHMENTS_FOLDER = "attachments"

    def __init__(self, db: DatabaseManager):
        """
        Initialize the backup service.

        Args:
            db: Database manager instance
        """
        self.db = db
        self.config = ConfigManager.get_instance()

    @require_permission(Permission.CHANGE_SETTINGS)
    def create_backup(
        self,
        output_path: Path,
        notes: str = "",
    ) -> str:
        """
        Create a complete backup of the application data.

        Args:
            output_path: Path where backup ZIP will be saved
            notes: Optional notes about the backup

        Returns:
            Path to the created backup file

        Raises:
            ValueError: If paths are invalid
            IOError: If backup creation fails
        """
        session = SessionManager.get_instance()
        shared_folder = Path(self.config.get_shared_folder_path())
        db_path = shared_folder / "data" / self.DATABASE_FILE
        attachments_path = shared_folder / self.ATTACHMENTS_FOLDER

        # Ensure output path has .zip extension
        if not str(output_path).lower().endswith(".zip"):
            output_path = Path(str(output_path) + ".zip")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create backup info
        backup_id = generate_uuid()
        backup_info = {
            "backup_id": backup_id,
            "created_at": get_now(),
            "created_by": session.username,
            "created_by_id": session.user_id,
            "app_version": "1.0.0",
            "notes": notes,
        }

        try:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # Add backup info
                zf.writestr(
                    self.BACKUP_INFO_FILE,
                    json.dumps(backup_info, indent=2),
                )

                # Add database file
                if db_path.exists():
                    zf.write(db_path, self.DATABASE_FILE)
                    logger.info(f"Added database to backup: {db_path}")

                # Add attachments folder recursively
                if attachments_path.exists():
                    for root, dirs, files in os.walk(attachments_path):
                        for file in files:
                            file_path = Path(root) / file
                            arcname = str(
                                Path(self.ATTACHMENTS_FOLDER)
                                / file_path.relative_to(attachments_path)
                            )
                            zf.write(file_path, arcname)
                    logger.info(f"Added attachments to backup")

            # Get file size
            size_bytes = output_path.stat().st_size

            # Record backup in database
            self._record_backup(
                backup_id=backup_id,
                backup_path=str(output_path),
                backup_type="MANUAL",
                size_bytes=size_bytes,
                notes=notes,
            )

            logger.info(f"Backup created successfully: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            # Clean up partial backup
            if output_path.exists():
                output_path.unlink()
            raise IOError(f"Failed to create backup: {e}")

    def validate_backup(self, backup_path: Path) -> Tuple[bool, str, Optional[dict]]:
        """
        Validate a backup file.

        Args:
            backup_path: Path to the backup ZIP file

        Returns:
            Tuple of (is_valid, message, backup_info)
        """
        if not backup_path.exists():
            return False, "Backup file not found", None

        if not str(backup_path).lower().endswith(".zip"):
            return False, "Backup must be a ZIP file", None

        try:
            with zipfile.ZipFile(backup_path, "r") as zf:
                # Check for required files
                names = zf.namelist()

                if self.BACKUP_INFO_FILE not in names:
                    return False, "Invalid backup: missing backup info", None

                if self.DATABASE_FILE not in names:
                    return False, "Invalid backup: missing database", None

                # Read and validate backup info
                info_data = zf.read(self.BACKUP_INFO_FILE).decode("utf-8")
                backup_info = json.loads(info_data)

                if "created_at" not in backup_info:
                    return False, "Invalid backup: corrupt metadata", None

                return True, "Backup is valid", backup_info

        except zipfile.BadZipFile:
            return False, "Invalid or corrupt ZIP file", None
        except json.JSONDecodeError:
            return False, "Invalid backup: corrupt metadata", None
        except Exception as e:
            return False, f"Error validating backup: {e}", None

    @require_permission(Permission.CHANGE_SETTINGS)
    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore from a backup file.

        Creates a safety backup of current data before restoring.

        Args:
            backup_path: Path to the backup ZIP file

        Returns:
            True if restoration was successful

        Raises:
            ValueError: If backup is invalid
            IOError: If restoration fails
        """
        # Validate backup first
        is_valid, message, backup_info = self.validate_backup(backup_path)
        if not is_valid:
            raise ValueError(message)

        session = SessionManager.get_instance()
        shared_folder = Path(self.config.get_shared_folder_path())
        db_path = shared_folder / "data" / self.DATABASE_FILE
        attachments_path = shared_folder / self.ATTACHMENTS_FOLDER

        # Create safety backup first
        safety_backup_path = self._create_safety_backup(shared_folder)
        logger.info(f"Created safety backup: {safety_backup_path}")

        try:
            with zipfile.ZipFile(backup_path, "r") as zf:
                # Restore database
                db_data = zf.read(self.DATABASE_FILE)
                db_path.parent.mkdir(parents=True, exist_ok=True)
                db_path.write_bytes(db_data)
                logger.info("Database restored")

                # Clear and restore attachments
                if attachments_path.exists():
                    shutil.rmtree(attachments_path)
                attachments_path.mkdir(parents=True, exist_ok=True)

                # Extract attachments
                for name in zf.namelist():
                    if name.startswith(self.ATTACHMENTS_FOLDER + "/"):
                        zf.extract(name, shared_folder)

                logger.info("Attachments restored")

            logger.info(f"Backup restored successfully from: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            # Attempt to restore from safety backup
            try:
                self._restore_from_safety_backup(safety_backup_path, shared_folder)
                logger.info("Restored from safety backup after failure")
            except Exception as restore_error:
                logger.error(f"Failed to restore safety backup: {restore_error}")

            raise IOError(f"Failed to restore backup: {e}")

    def _create_safety_backup(self, shared_folder: Path) -> Path:
        """
        Create a temporary safety backup before restore.

        Args:
            shared_folder: Path to the shared folder

        Returns:
            Path to the safety backup
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safety_path = shared_folder / f"_safety_backup_{timestamp}.zip"

        db_path = shared_folder / "data" / self.DATABASE_FILE
        attachments_path = shared_folder / self.ATTACHMENTS_FOLDER

        with zipfile.ZipFile(safety_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add database
            if db_path.exists():
                zf.write(db_path, self.DATABASE_FILE)

            # Add attachments
            if attachments_path.exists():
                for root, dirs, files in os.walk(attachments_path):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = str(
                            Path(self.ATTACHMENTS_FOLDER)
                            / file_path.relative_to(attachments_path)
                        )
                        zf.write(file_path, arcname)

        return safety_path

    def _restore_from_safety_backup(
        self, safety_path: Path, shared_folder: Path
    ) -> None:
        """
        Restore from a safety backup.

        Args:
            safety_path: Path to the safety backup
            shared_folder: Path to the shared folder
        """
        db_path = shared_folder / "data" / self.DATABASE_FILE
        attachments_path = shared_folder / self.ATTACHMENTS_FOLDER

        with zipfile.ZipFile(safety_path, "r") as zf:
            # Restore database
            if self.DATABASE_FILE in zf.namelist():
                db_data = zf.read(self.DATABASE_FILE)
                db_path.write_bytes(db_data)

            # Restore attachments
            if attachments_path.exists():
                shutil.rmtree(attachments_path)
            attachments_path.mkdir(parents=True, exist_ok=True)

            for name in zf.namelist():
                if name.startswith(self.ATTACHMENTS_FOLDER + "/"):
                    zf.extract(name, shared_folder)

    def _record_backup(
        self,
        backup_id: str,
        backup_path: str,
        backup_type: str,
        size_bytes: int,
        notes: str,
    ) -> None:
        """
        Record backup in the database.

        Args:
            backup_id: Unique backup ID
            backup_path: Path to the backup file
            backup_type: Type of backup (MANUAL or SCHEDULED)
            size_bytes: Size of the backup file
            notes: Optional notes
        """
        session = SessionManager.get_instance()

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO backup_history (
                    backup_id, backup_path, backup_type,
                    created_at, created_by, size_bytes, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    backup_id,
                    backup_path,
                    backup_type,
                    get_now(),
                    session.user_id,
                    size_bytes,
                    notes or None,
                ),
            )

    def get_backup_history(self, limit: int = 50) -> List[BackupInfo]:
        """
        Get the backup history.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of BackupInfo objects
        """
        rows = self.db.fetch_all(
            """
            SELECT * FROM backup_history
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )

        return [BackupInfo.from_row(row) for row in rows]

    def delete_backup_record(self, backup_id: str) -> bool:
        """
        Delete a backup record from history.

        Does not delete the actual backup file.

        Args:
            backup_id: ID of the backup to remove

        Returns:
            True if record was deleted
        """
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM backup_history WHERE backup_id = ?",
                (backup_id,),
            )
            return cursor.rowcount > 0

    def format_backup_size(self, size_bytes: Optional[int]) -> str:
        """
        Format backup size for display.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
        if size_bytes is None:
            return "Unknown"

        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
