"""
PolicyHub Link Service

Handles document linking functionality.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from app.constants import LinkType
from core.database import DatabaseManager
from core.permissions import Permission, require_permission
from core.session import SessionManager
from models.link import DocumentLink, DocumentLinkCreate
from services.history_service import HistoryService
from utils.dates import get_now
from utils.files import generate_uuid

logger = logging.getLogger(__name__)


@dataclass
class LinkedDocument:
    """A document link with document info for display."""

    link: DocumentLink
    doc_ref: str
    title: str
    status: str
    is_parent: bool  # Whether the linked doc is the parent in the relationship


class LinkService:
    """
    Service for managing document links.

    Handles creation, retrieval, and deletion of links between documents
    with audit logging.
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize the link service.

        Args:
            db: Database manager instance
        """
        self.db = db
        self.history_service = HistoryService(db)

    def get_links_for_document(self, doc_id: str) -> List[LinkedDocument]:
        """
        Get all links for a document (both as parent and child).

        Args:
            doc_id: Document ID

        Returns:
            List of LinkedDocument objects with document info
        """
        # Get links where this document is the parent
        parent_links = self.db.fetch_all(
            """
            SELECT dl.*, d.doc_ref, d.title, d.status
            FROM document_links dl
            JOIN documents d ON dl.child_doc_id = d.doc_id
            WHERE dl.parent_doc_id = ?
            ORDER BY dl.created_at DESC
            """,
            (doc_id,),
        )

        # Get links where this document is the child
        child_links = self.db.fetch_all(
            """
            SELECT dl.*, d.doc_ref, d.title, d.status
            FROM document_links dl
            JOIN documents d ON dl.parent_doc_id = d.doc_id
            WHERE dl.child_doc_id = ?
            ORDER BY dl.created_at DESC
            """,
            (doc_id,),
        )

        result = []

        # Process parent links (this doc is parent, linked doc is child)
        for row in parent_links:
            result.append(LinkedDocument(
                link=DocumentLink.from_row(row),
                doc_ref=row["doc_ref"],
                title=row["title"],
                status=row["status"],
                is_parent=True,  # This document is the parent
            ))

        # Process child links (this doc is child, linked doc is parent)
        for row in child_links:
            result.append(LinkedDocument(
                link=DocumentLink.from_row(row),
                doc_ref=row["doc_ref"],
                title=row["title"],
                status=row["status"],
                is_parent=False,  # This document is the child
            ))

        return result

    def get_link_by_id(self, link_id: str) -> Optional[DocumentLink]:
        """
        Get a link by ID.

        Args:
            link_id: Link ID

        Returns:
            DocumentLink or None
        """
        row = self.db.fetch_one(
            "SELECT * FROM document_links WHERE link_id = ?",
            (link_id,),
        )
        return DocumentLink.from_row(row) if row else None

    def link_exists(
        self,
        parent_doc_id: str,
        child_doc_id: str,
        link_type: Optional[str] = None,
    ) -> bool:
        """
        Check if a link already exists between two documents.

        Args:
            parent_doc_id: Parent document ID
            child_doc_id: Child document ID
            link_type: Optional link type to check for specific type

        Returns:
            True if link exists
        """
        if link_type:
            row = self.db.fetch_one(
                """
                SELECT 1 FROM document_links
                WHERE parent_doc_id = ? AND child_doc_id = ? AND link_type = ?
                """,
                (parent_doc_id, child_doc_id, link_type),
            )
        else:
            row = self.db.fetch_one(
                """
                SELECT 1 FROM document_links
                WHERE parent_doc_id = ? AND child_doc_id = ?
                """,
                (parent_doc_id, child_doc_id),
            )
        return row is not None

    def get_document_ref(self, doc_id: str) -> Optional[str]:
        """
        Get a document reference by ID.

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
    def create_link(
        self,
        parent_doc_id: str,
        child_doc_id: str,
        link_type: str,
    ) -> DocumentLink:
        """
        Create a link between two documents.

        Args:
            parent_doc_id: Parent document ID (e.g., Policy)
            child_doc_id: Child document ID (e.g., Procedure that implements it)
            link_type: Type of relationship

        Returns:
            Created DocumentLink

        Raises:
            ValueError: If documents don't exist or link already exists
            PermissionError: If user lacks permission
        """
        # Validate link type
        try:
            LinkType(link_type)
        except ValueError:
            raise ValueError(f"Invalid link type: {link_type}")

        # Check documents exist
        parent_ref = self.get_document_ref(parent_doc_id)
        child_ref = self.get_document_ref(child_doc_id)

        if not parent_ref:
            raise ValueError("Parent document not found")
        if not child_ref:
            raise ValueError("Child document not found")

        # Check for self-link
        if parent_doc_id == child_doc_id:
            raise ValueError("Cannot link a document to itself")

        # Check if link already exists
        if self.link_exists(parent_doc_id, child_doc_id, link_type):
            raise ValueError(f"Link of type '{link_type}' already exists between these documents")

        # Get current user
        session = SessionManager.get_instance()
        user_id = session.user_id if session.is_authenticated else None

        # Create link
        link_id = generate_uuid()
        created_at = get_now()

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO document_links (
                    link_id, parent_doc_id, child_doc_id, link_type, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (link_id, parent_doc_id, child_doc_id, link_type, created_at, user_id),
            )

        # Log history for both documents
        self.history_service.log_link_added(parent_doc_id, child_ref, link_type)
        self.history_service.log_link_added(child_doc_id, parent_ref, link_type)

        logger.info(f"Link created: {parent_ref} -> {child_ref} ({link_type})")

        return DocumentLink(
            link_id=link_id,
            parent_doc_id=parent_doc_id,
            child_doc_id=child_doc_id,
            link_type=link_type,
            created_at=created_at,
            created_by=user_id,
        )

    @require_permission(Permission.EDIT_DOCUMENT)
    def delete_link(self, link_id: str) -> bool:
        """
        Delete a document link.

        Args:
            link_id: Link ID to delete

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If link not found
            PermissionError: If user lacks permission
        """
        link = self.get_link_by_id(link_id)
        if not link:
            raise ValueError(f"Link not found: {link_id}")

        # Get document refs for history
        parent_ref = self.get_document_ref(link.parent_doc_id)
        child_ref = self.get_document_ref(link.child_doc_id)

        # Delete link
        with self.db.get_connection() as conn:
            conn.execute(
                "DELETE FROM document_links WHERE link_id = ?",
                (link_id,),
            )

        # Log history for both documents
        if parent_ref and child_ref:
            self.history_service.log_link_removed(link.parent_doc_id, child_ref, link.link_type)
            self.history_service.log_link_removed(link.child_doc_id, parent_ref, link.link_type)

        logger.info(f"Link deleted: {parent_ref} -> {child_ref}")
        return True

    def get_link_count(self, doc_id: str) -> int:
        """
        Get the number of links for a document.

        Args:
            doc_id: Document ID

        Returns:
            Number of links (both as parent and child)
        """
        row = self.db.fetch_one(
            """
            SELECT COUNT(*) as count FROM document_links
            WHERE parent_doc_id = ? OR child_doc_id = ?
            """,
            (doc_id, doc_id),
        )
        return row["count"] if row else 0

    def get_available_documents_for_linking(
        self,
        exclude_doc_id: str,
        search_term: Optional[str] = None,
    ) -> List[dict]:
        """
        Get documents available for linking (excluding already linked and self).

        Args:
            exclude_doc_id: Document ID to exclude (the current document)
            search_term: Optional search term to filter results

        Returns:
            List of document dicts with doc_id, doc_ref, title, doc_type, status
        """
        # Get existing linked document IDs
        existing_links = self.db.fetch_all(
            """
            SELECT child_doc_id as linked_id FROM document_links WHERE parent_doc_id = ?
            UNION
            SELECT parent_doc_id as linked_id FROM document_links WHERE child_doc_id = ?
            """,
            (exclude_doc_id, exclude_doc_id),
        )
        linked_ids = {row["linked_id"] for row in existing_links}
        linked_ids.add(exclude_doc_id)

        # Build query
        if search_term:
            rows = self.db.fetch_all(
                """
                SELECT doc_id, doc_ref, title, doc_type, status
                FROM documents
                WHERE (doc_ref LIKE ? OR title LIKE ?)
                AND status != 'ARCHIVED'
                ORDER BY doc_ref
                LIMIT 50
                """,
                (f"%{search_term}%", f"%{search_term}%"),
            )
        else:
            rows = self.db.fetch_all(
                """
                SELECT doc_id, doc_ref, title, doc_type, status
                FROM documents
                WHERE status != 'ARCHIVED'
                ORDER BY doc_ref
                LIMIT 50
                """,
            )

        # Filter out already linked documents
        return [
            dict(row)
            for row in rows
            if row["doc_id"] not in linked_ids
        ]
