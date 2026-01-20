"""
PolicyHub Attachment Service

Handles file attachment management for documents.
"""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from core.config import ConfigManager

from app.constants import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE_BYTES,
)
from core.database import DatabaseManager
from core.permissions import Permission, require_permission
from core.session import SessionManager
from models.attachment import Attachment, AttachmentCreate
from services.history_service import HistoryService
from utils.dates import get_now
from utils.files import (
    copy_file,
    delete_file,
    generate_attachment_path,
    generate_uuid,
    get_attachment_absolute_path,
    get_attachments_path,
    get_file_extension,
    get_file_size,
    is_valid_extension,
)
from utils.validators import validate_file_upload

logger = logging.getLogger(__name__)


class AttachmentService:
    """
    Service for managing document attachments.

    Handles file upload, storage, retrieval, and deletion with audit logging.
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize the attachment service.

        Args:
            db: Database manager instance
        """
        self.db = db
        self.history_service = HistoryService(db)

    def get_attachments_for_document(self, doc_id: str) -> List[Attachment]:
        """
        Get all attachments for a document.

        Args:
            doc_id: Document ID

        Returns:
            List of Attachment objects, most recent first
        """
        rows = self.db.fetch_all(
            """
            SELECT * FROM attachments
            WHERE doc_id = ?
            ORDER BY uploaded_at DESC
            """,
            (doc_id,),
        )
        return [Attachment.from_row(row) for row in rows]

    def get_current_attachment(self, doc_id: str) -> Optional[Attachment]:
        """
        Get the current (most recent) attachment for a document.

        Args:
            doc_id: Document ID

        Returns:
            Current Attachment or None
        """
        row = self.db.fetch_one(
            """
            SELECT * FROM attachments
            WHERE doc_id = ? AND is_current = 1
            ORDER BY uploaded_at DESC
            LIMIT 1
            """,
            (doc_id,),
        )
        return Attachment.from_row(row) if row else None

    def get_attachment_by_id(self, attachment_id: str) -> Optional[Attachment]:
        """
        Get an attachment by ID.

        Args:
            attachment_id: Attachment ID

        Returns:
            Attachment or None
        """
        row = self.db.fetch_one(
            """
            SELECT * FROM attachments
            WHERE attachment_id = ?
            """,
            (attachment_id,),
        )
        return Attachment.from_row(row) if row else None

    def validate_file(
        self,
        filename: str,
        file_size: int,
    ) -> tuple[bool, str]:
        """
        Validate a file for upload.

        Args:
            filename: Name of the file
            file_size: Size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        return validate_file_upload(filename, file_size)

    @require_permission(Permission.EDIT_DOCUMENT)
    def add_attachment(
        self,
        doc_id: str,
        doc_ref: str,
        source_path: Path,
        version_label: str,
        original_filename: Optional[str] = None,
    ) -> Attachment:
        """
        Add a new attachment to a document.

        Args:
            doc_id: Document ID
            doc_ref: Document reference code (for folder organization)
            source_path: Path to the source file to copy
            version_label: Version label for this attachment
            original_filename: Original filename (uses source_path.name if not provided)

        Returns:
            Created Attachment

        Raises:
            FileNotFoundError: If source file doesn't exist
            ValueError: If file is invalid (wrong type, too large, etc.)
            PermissionError: If user lacks permission
        """
        # Validate source file exists
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        filename = original_filename or source_path.name
        file_size = get_file_size(source_path)

        # Validate file
        is_valid, error = self.validate_file(filename, file_size)
        if not is_valid:
            raise ValueError(error)

        # Get mime type
        ext = get_file_extension(filename)
        mime_type = ALLOWED_MIME_TYPES.get(ext)

        # Generate relative path for storage
        relative_path = generate_attachment_path(doc_ref, filename, version_label)

        # Get absolute destination path
        dest_path = get_attachment_absolute_path(relative_path)
        if dest_path is None:
            raise ValueError("Attachments folder not configured")

        # Copy file to attachments folder
        if not copy_file(source_path, dest_path):
            raise ValueError("Failed to copy file to attachments folder")

        # Mark existing attachments as not current
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE attachments
                SET is_current = 0
                WHERE doc_id = ?
                """,
                (doc_id,),
            )

        # Get current user
        session = SessionManager.get_instance()
        user_id = session.user_id if session.is_authenticated else None

        # Create attachment record
        attachment_id = generate_uuid()
        uploaded_at = get_now()

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO attachments (
                    attachment_id, doc_id, filename, file_path, file_size,
                    mime_type, version_label, is_current, uploaded_at, uploaded_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attachment_id,
                    doc_id,
                    filename,
                    relative_path,
                    file_size,
                    mime_type,
                    version_label,
                    True,
                    uploaded_at,
                    user_id,
                ),
            )

        # Log history
        self.history_service.log_attachment_added(doc_id, filename)

        logger.info(f"Attachment added: {filename} for document {doc_id}")

        return Attachment(
            attachment_id=attachment_id,
            doc_id=doc_id,
            filename=filename,
            file_path=relative_path,
            file_size=file_size,
            mime_type=mime_type,
            version_label=version_label,
            is_current=True,
            uploaded_at=uploaded_at,
            uploaded_by=user_id,
        )

    def _get_deleted_folder(self, doc_ref: str) -> Path:
        """
        Get the _Deleted subfolder for a document.

        Args:
            doc_ref: Document reference code

        Returns:
            Path to the deleted folder for this document
        """
        config = ConfigManager.get_instance()
        shared_folder = config.get_shared_folder_path()
        if not shared_folder:
            raise ValueError("Shared folder not configured")
        return Path(shared_folder) / "_Deleted" / doc_ref

    def _get_unique_deleted_filename(self, folder: Path, filename: str) -> str:
        """
        Generate a unique filename for the deleted folder.

        Adds a timestamp to avoid conflicts with previously deleted files
        that had the same name.

        Args:
            folder: The deleted folder path
            filename: Original filename

        Returns:
            Unique filename with timestamp
        """
        base, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = f"{base}_deleted_{timestamp}{ext}"

        # Handle unlikely collision (same second)
        counter = 1
        while (folder / new_name).exists():
            new_name = f"{base}_deleted_{timestamp}_{counter}{ext}"
            counter += 1

        return new_name

    def _get_doc_ref_for_attachment(self, doc_id: str) -> Optional[str]:
        """
        Get the document reference code for an attachment's document.

        Args:
            doc_id: Document ID

        Returns:
            Document reference or None
        """
        row = self.db.fetch_one(
            "SELECT doc_ref FROM documents WHERE doc_id = ?",
            (doc_id,),
        )
        return row["doc_ref"] if row else None

    @require_permission(Permission.EDIT_DOCUMENT)
    def delete_attachment(self, attachment_id: str) -> bool:
        """
        Delete an attachment (soft delete - moves to _Deleted folder).

        The file is moved to a _Deleted/{doc_ref}/ folder rather than
        being permanently deleted, allowing for recovery if needed.

        Args:
            attachment_id: Attachment ID to delete

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If attachment not found
            PermissionError: If user lacks permission
        """
        attachment = self.get_attachment_by_id(attachment_id)
        if not attachment:
            raise ValueError(f"Attachment not found: {attachment_id}")

        # Get document reference for folder organization
        doc_ref = self._get_doc_ref_for_attachment(attachment.doc_id)
        if not doc_ref:
            doc_ref = "unknown"

        # Move file to _Deleted folder instead of deleting
        source_path = get_attachment_absolute_path(attachment.file_path)
        if source_path and source_path.exists():
            try:
                # Get the deleted folder for this document
                deleted_folder = self._get_deleted_folder(doc_ref)
                deleted_folder.mkdir(parents=True, exist_ok=True)

                # Generate unique filename
                dest_filename = self._get_unique_deleted_filename(
                    deleted_folder, attachment.filename
                )
                dest_path = deleted_folder / dest_filename

                # Move file
                shutil.move(str(source_path), str(dest_path))
                logger.info(f"Attachment moved to deleted folder: {dest_path}")

            except Exception as e:
                logger.error(f"Failed to move file to deleted folder: {e}")
                # Fall back to regular delete if move fails
                if not delete_file(source_path):
                    logger.warning(f"Failed to delete file: {source_path}")

        # Delete database record
        with self.db.get_connection() as conn:
            conn.execute(
                "DELETE FROM attachments WHERE attachment_id = ?",
                (attachment_id,),
            )

        # If this was the current attachment, make the most recent one current
        if attachment.is_current:
            with self.db.get_connection() as conn:
                conn.execute(
                    """
                    UPDATE attachments
                    SET is_current = 1
                    WHERE doc_id = ? AND attachment_id = (
                        SELECT attachment_id FROM attachments
                        WHERE doc_id = ?
                        ORDER BY uploaded_at DESC
                        LIMIT 1
                    )
                    """,
                    (attachment.doc_id, attachment.doc_id),
                )

        # Log history
        self.history_service.log_attachment_removed(attachment.doc_id, attachment.filename)

        logger.info(f"Attachment deleted: {attachment.filename}")
        return True

    def get_attachment_count(self, doc_id: str) -> int:
        """
        Get the number of attachments for a document.

        Args:
            doc_id: Document ID

        Returns:
            Number of attachments
        """
        row = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM attachments WHERE doc_id = ?",
            (doc_id,),
        )
        return row["count"] if row else 0

    def open_attachment(self, attachment_id: str) -> Optional[Path]:
        """
        Get the path to open an attachment.

        Args:
            attachment_id: Attachment ID

        Returns:
            Absolute path to the attachment file, or None if not found
        """
        attachment = self.get_attachment_by_id(attachment_id)
        if not attachment:
            return None

        return get_attachment_absolute_path(attachment.file_path)

    def get_total_attachment_size(self, doc_id: str) -> int:
        """
        Get the total size of all attachments for a document.

        Args:
            doc_id: Document ID

        Returns:
            Total size in bytes
        """
        row = self.db.fetch_one(
            "SELECT SUM(file_size) as total FROM attachments WHERE doc_id = ?",
            (doc_id,),
        )
        return row["total"] or 0 if row else 0
