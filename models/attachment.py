"""
PolicyHub Attachment Model

Represents a file attachment linked to a document.
"""

from dataclasses import dataclass
from sqlite3 import Row
from typing import Optional

from utils.files import format_file_size


@dataclass
class Attachment:
    """
    Represents a file attachment.

    Attributes:
        attachment_id: Unique identifier (UUID)
        doc_id: Foreign key to documents
        filename: Original filename
        file_path: Relative path in attachments folder
        file_size: Size in bytes
        version_label: Version this attachment represents
        is_current: Whether this is the current version
        uploaded_at: Upload timestamp (ISO 8601)
        uploaded_by: User ID who uploaded this file
        mime_type: MIME type of the file (optional)
    """

    attachment_id: str
    doc_id: str
    filename: str
    file_path: str
    file_size: int
    version_label: str
    is_current: bool
    uploaded_at: str
    uploaded_by: str
    mime_type: Optional[str] = None

    @property
    def size_display(self) -> str:
        """Get human-readable file size."""
        return format_file_size(self.file_size)

    @property
    def extension(self) -> str:
        """Get the file extension (lowercase)."""
        if "." in self.filename:
            return self.filename[self.filename.rfind("."):].lower()
        return ""

    @classmethod
    def from_row(cls, row: Row) -> "Attachment":
        """
        Create an Attachment from a SQLite row.

        Args:
            row: SQLite Row object with attachment data

        Returns:
            Attachment instance
        """
        return cls(
            attachment_id=row["attachment_id"],
            doc_id=row["doc_id"],
            filename=row["filename"],
            file_path=row["file_path"],
            file_size=row["file_size"],
            mime_type=row["mime_type"],
            version_label=row["version_label"],
            is_current=bool(row["is_current"]),
            uploaded_at=row["uploaded_at"],
            uploaded_by=row["uploaded_by"],
        )

    def to_dict(self) -> dict:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation of the attachment
        """
        return {
            "attachment_id": self.attachment_id,
            "doc_id": self.doc_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "version_label": self.version_label,
            "is_current": self.is_current,
            "uploaded_at": self.uploaded_at,
            "uploaded_by": self.uploaded_by,
        }


@dataclass
class AttachmentCreate:
    """Data required to create a new attachment record."""

    doc_id: str
    filename: str
    file_path: str
    file_size: int
    version_label: str
    is_current: bool = True
    mime_type: Optional[str] = None
