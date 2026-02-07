"""
PolicyHub History Service

Handles audit trail logging for document changes.
"""

import logging
from typing import List, Optional

from app.constants import HistoryAction
from core.database import DatabaseManager
from core.session import SessionManager
from models.history import HistoryCreate, HistoryEntry
from utils.dates import get_now
from utils.files import generate_uuid

logger = logging.getLogger(__name__)


class HistoryService:
    """
    Service for managing document audit history.

    Records all changes to documents for compliance and auditing purposes.
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize the history service.

        Args:
            db: Database manager instance
        """
        self.db = db

    def log_action(
        self,
        doc_id: str,
        action: HistoryAction,
        field_changed: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        notes: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> HistoryEntry:
        """
        Log a history entry for a document action.

        Args:
            doc_id: Document ID
            action: Type of action performed
            field_changed: Name of the field that was changed (optional)
            old_value: Previous value (optional)
            new_value: New value (optional)
            notes: Additional notes (optional)
            user_id: User ID (defaults to current session user)

        Returns:
            Created HistoryEntry
        """
        history_id = generate_uuid()
        changed_at = get_now()

        # Get current user if not provided
        if user_id is None:
            session = SessionManager.get_instance()
            user_id = session.user_id if session.is_authenticated else None

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO document_history (
                    history_id, doc_id, action, field_changed,
                    old_value, new_value, changed_by, changed_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    history_id,
                    doc_id,
                    action.value if isinstance(action, HistoryAction) else action,
                    field_changed,
                    old_value,
                    new_value,
                    user_id,
                    changed_at,
                    notes,
                ),
            )

        logger.debug(f"History logged: {action} for document {doc_id}")

        return HistoryEntry(
            history_id=history_id,
            doc_id=doc_id,
            action=action.value if isinstance(action, HistoryAction) else action,
            field_changed=field_changed,
            old_value=old_value,
            new_value=new_value,
            changed_by=user_id,
            changed_at=changed_at,
            notes=notes,
        )

    def log_document_created(self, doc_id: str, notes: Optional[str] = None) -> HistoryEntry:
        """
        Log that a document was created.

        Args:
            doc_id: Document ID
            notes: Optional notes

        Returns:
            Created HistoryEntry
        """
        return self.log_action(
            doc_id=doc_id,
            action=HistoryAction.CREATED,
            notes=notes,
        )

    def log_field_change(
        self,
        doc_id: str,
        field_name: str,
        old_value: Optional[str],
        new_value: Optional[str],
    ) -> HistoryEntry:
        """
        Log a field value change.

        Args:
            doc_id: Document ID
            field_name: Name of the changed field
            old_value: Previous value
            new_value: New value

        Returns:
            Created HistoryEntry
        """
        return self.log_action(
            doc_id=doc_id,
            action=HistoryAction.UPDATED,
            field_changed=field_name,
            old_value=old_value,
            new_value=new_value,
        )

    def log_status_change(
        self,
        doc_id: str,
        old_status: str,
        new_status: str,
    ) -> HistoryEntry:
        """
        Log a status change.

        Args:
            doc_id: Document ID
            old_status: Previous status
            new_status: New status

        Returns:
            Created HistoryEntry
        """
        return self.log_action(
            doc_id=doc_id,
            action=HistoryAction.STATUS_CHANGED,
            field_changed="status",
            old_value=old_status,
            new_value=new_status,
        )

    def log_review(self, doc_id: str, notes: Optional[str] = None) -> HistoryEntry:
        """
        Log that a document was reviewed.

        Args:
            doc_id: Document ID
            notes: Review notes

        Returns:
            Created HistoryEntry
        """
        return self.log_action(
            doc_id=doc_id,
            action=HistoryAction.REVIEWED,
            notes=notes,
        )

    def log_attachment_added(
        self,
        doc_id: str,
        filename: str,
    ) -> HistoryEntry:
        """
        Log that an attachment was added.

        Args:
            doc_id: Document ID
            filename: Name of the added file

        Returns:
            Created HistoryEntry
        """
        return self.log_action(
            doc_id=doc_id,
            action=HistoryAction.ATTACHMENT_ADDED,
            new_value=filename,
        )

    def log_attachment_removed(
        self,
        doc_id: str,
        filename: str,
    ) -> HistoryEntry:
        """
        Log that an attachment was removed.

        Args:
            doc_id: Document ID
            filename: Name of the removed file

        Returns:
            Created HistoryEntry
        """
        return self.log_action(
            doc_id=doc_id,
            action=HistoryAction.ATTACHMENT_REMOVED,
            old_value=filename,
        )

    def log_link_added(
        self,
        doc_id: str,
        linked_doc_ref: str,
        link_type: str,
    ) -> HistoryEntry:
        """
        Log that a document link was added.

        Args:
            doc_id: Document ID
            linked_doc_ref: Reference of the linked document
            link_type: Type of link (IMPLEMENTS, REFERENCES, SUPERSEDES)

        Returns:
            Created HistoryEntry
        """
        return self.log_action(
            doc_id=doc_id,
            action=HistoryAction.LINK_ADDED,
            new_value=f"{link_type}: {linked_doc_ref}",
        )

    def log_link_removed(
        self,
        doc_id: str,
        linked_doc_ref: str,
        link_type: str,
    ) -> HistoryEntry:
        """
        Log that a document link was removed.

        Args:
            doc_id: Document ID
            linked_doc_ref: Reference of the unlinked document
            link_type: Type of link that was removed

        Returns:
            Created HistoryEntry
        """
        return self.log_action(
            doc_id=doc_id,
            action=HistoryAction.LINK_REMOVED,
            old_value=f"{link_type}: {linked_doc_ref}",
        )

    def get_document_history(
        self,
        doc_id: str,
        limit: int = 50,
    ) -> List[HistoryEntry]:
        """
        Get history entries for a document.

        Returns entries with username resolved from user ID.

        Args:
            doc_id: Document ID
            limit: Maximum number of entries to return

        Returns:
            List of HistoryEntry objects, most recent first
        """
        rows = self.db.fetch_all(
            """
            SELECT dh.*, u.username
            FROM document_history dh
            LEFT JOIN users u ON dh.changed_by = u.user_id
            WHERE dh.doc_id = ?
            ORDER BY dh.changed_at DESC
            LIMIT ?
            """,
            (doc_id, limit),
        )
        entries = []
        for row in rows:
            entry = HistoryEntry.from_row(row)
            # Replace user ID with username if available
            if row["username"]:
                entry.changed_by = row["username"]
            entries.append(entry)
        return entries

    def get_recent_activity(
        self,
        limit: int = 20,
    ) -> List[HistoryEntry]:
        """
        Get recent activity across all documents.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of HistoryEntry objects, most recent first
        """
        rows = self.db.fetch_all(
            """
            SELECT * FROM document_history
            ORDER BY changed_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [HistoryEntry.from_row(row) for row in rows]

    def get_activity_by_user(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[HistoryEntry]:
        """
        Get activity for a specific user.

        Args:
            user_id: User ID
            limit: Maximum number of entries to return

        Returns:
            List of HistoryEntry objects
        """
        rows = self.db.fetch_all(
            """
            SELECT * FROM document_history
            WHERE changed_by = ?
            ORDER BY changed_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        return [HistoryEntry.from_row(row) for row in rows]

    def get_activity_in_range(
        self,
        start_date: str,
        end_date: str,
    ) -> List[HistoryEntry]:
        """
        Get activity within a date range.

        Args:
            start_date: Start date (ISO 8601 format)
            end_date: End date (ISO 8601 format)

        Returns:
            List of HistoryEntry objects
        """
        rows = self.db.fetch_all(
            """
            SELECT * FROM document_history
            WHERE changed_at >= ? AND changed_at <= ?
            ORDER BY changed_at DESC
            """,
            (start_date, end_date),
        )
        return [HistoryEntry.from_row(row) for row in rows]
