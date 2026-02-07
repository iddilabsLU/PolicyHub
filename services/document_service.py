"""
PolicyHub Document Service

Handles CRUD operations for documents with automatic audit logging.
"""

import logging
import re
from typing import Dict, List, Optional

from app.constants import (
    DocumentStatus,
    DocumentType,
    HistoryAction,
    ReviewFrequency,
    ReviewStatus,
    UserRole,
)
from core.database import DatabaseManager
from core.permissions import Permission, require_permission
from core.session import SessionManager
from models.document import Document, DocumentCreate, DocumentUpdate
from services.history_service import HistoryService
from utils.dates import calculate_next_review, get_now, get_review_status, get_today
from utils.files import generate_uuid

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Service for managing documents.

    Handles all document CRUD operations with automatic audit trail logging.
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize the document service.

        Args:
            db: Database manager instance
        """
        self.db = db
        self.history_service = HistoryService(db)
        # Lazy import to avoid circular dependency
        self._user_service = None

    def _get_user_service(self):
        """Get the user service (lazy load to avoid circular import)."""
        if self._user_service is None:
            from services.user_service import UserService
            self._user_service = UserService(self.db)
        return self._user_service

    def _check_restricted_editor_access(
        self,
        category: str,
        applicable_entity: Optional[str],
    ) -> None:
        """
        Check if a restricted editor has access to a document.

        Raises PermissionError if the user is a restricted editor
        and doesn't have access to the document's category or entities.

        Args:
            category: Document's category code
            applicable_entity: Document's semicolon-separated entities (or None)

        Raises:
            PermissionError: If access is denied
        """
        session = SessionManager.get_instance()

        # Only check for EDITOR_RESTRICTED role
        if session.role != UserRole.EDITOR_RESTRICTED.value:
            return

        user_service = self._get_user_service()
        has_access = user_service.check_document_access(
            session.user_id,
            category,
            applicable_entity,
        )

        if not has_access:
            raise PermissionError(
                "Access denied: This document is outside your allowed categories and entities"
            )

    # ============================================================
    # Query Methods
    # ============================================================

    def get_all_documents(
        self,
        status: Optional[str] = None,
        doc_type: Optional[str] = None,
        category: Optional[str] = None,
        review_status: Optional[str] = None,
        search_term: Optional[str] = None,
        mandatory_read_all: Optional[bool] = None,
        applicable_entity: Optional[str] = None,
        order_by: str = "doc_ref",
        order_dir: str = "ASC",
        bypass_restrictions: bool = False,
    ) -> List[Document]:
        """
        Get documents with optional filtering and sorting.

        Args:
            status: Filter by document status (ACTIVE, DRAFT, etc.)
            doc_type: Filter by document type (POLICY, PROCEDURE, etc.)
            category: Filter by category code
            review_status: Filter by review status (OVERDUE, DUE_SOON, etc.)
            search_term: Search in title, doc_ref, and description
            mandatory_read_all: Filter by mandatory read status (True/False)
            applicable_entity: Filter by applicable entity name
            order_by: Column to sort by
            order_dir: Sort direction (ASC or DESC)
            bypass_restrictions: If True, skip user restriction filtering (for admin stats)

        Returns:
            List of Document objects
        """
        query = "SELECT * FROM documents WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if doc_type:
            query += " AND doc_type = ?"
            params.append(doc_type)

        if category:
            query += " AND category = ?"
            params.append(category)

        if mandatory_read_all is not None:
            query += " AND mandatory_read_all = ?"
            params.append(1 if mandatory_read_all else 0)

        if applicable_entity:
            # Use LIKE to match semicolon-separated entities
            query += " AND (applicable_entity = ? OR applicable_entity LIKE ? OR applicable_entity LIKE ? OR applicable_entity LIKE ?)"
            params.append(applicable_entity)  # Exact match
            params.append(f"{applicable_entity};%")  # At start
            params.append(f"%;{applicable_entity}")  # At end
            params.append(f"%;{applicable_entity};%")  # In middle

        if search_term:
            query += " AND (title LIKE ? OR doc_ref LIKE ? OR description LIKE ?)"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern, search_pattern])

        # Validate order_by to prevent SQL injection
        valid_columns = [
            "doc_ref", "title", "doc_type", "category", "status",
            "version", "next_review_date", "effective_date", "owner"
        ]
        if order_by not in valid_columns:
            order_by = "doc_ref"

        order_dir = "DESC" if order_dir.upper() == "DESC" else "ASC"
        query += f" ORDER BY {order_by} {order_dir}"

        rows = self.db.fetch_all(query, tuple(params))
        documents = [Document.from_row(row) for row in rows]

        # Apply review_status filter in Python (it's a calculated field)
        if review_status:
            documents = [
                doc for doc in documents
                if doc.review_status.value == review_status
            ]

        # Apply user restrictions for EDITOR_RESTRICTED role
        if not bypass_restrictions:
            documents = self._apply_user_restrictions(documents)

        return documents

    def _apply_user_restrictions(self, documents: List[Document]) -> List[Document]:
        """
        Filter documents based on the current user's restrictions.

        For EDITOR_RESTRICTED users, only return documents that match
        their allowed categories OR entities.

        Args:
            documents: List of documents to filter

        Returns:
            Filtered list of documents (or original list if user has no restrictions)
        """
        session = SessionManager.get_instance()

        # Only filter for EDITOR_RESTRICTED role
        if session.role != UserRole.EDITOR_RESTRICTED.value:
            return documents

        # Get user's restrictions
        user_service = self._get_user_service()
        restrictions = user_service.get_user_restrictions(session.user_id)

        # If no restrictions defined, return empty (safety: restricted user with no restrictions sees nothing)
        if not restrictions["categories"] and not restrictions["entities"]:
            return []

        # Filter documents that match allowed categories OR entities
        filtered = []
        for doc in documents:
            # Check category match
            if doc.category in restrictions["categories"]:
                filtered.append(doc)
                continue

            # Check entity match (semicolon-separated entities)
            if doc.applicable_entity and restrictions["entities"]:
                doc_entities = [e.strip() for e in doc.applicable_entity.split(";") if e.strip()]
                for entity in doc_entities:
                    if entity in restrictions["entities"]:
                        filtered.append(doc)
                        break

        return filtered

    def get_document_by_id(self, doc_id: str) -> Optional[Document]:
        """
        Get a document by its ID.

        Args:
            doc_id: Document's unique ID

        Returns:
            Document object or None if not found
        """
        row = self.db.fetch_one(
            "SELECT * FROM documents WHERE doc_id = ?",
            (doc_id,),
        )
        return Document.from_row(row) if row else None

    def get_document_by_ref(self, doc_ref: str) -> Optional[Document]:
        """
        Get a document by its reference code.

        Args:
            doc_ref: Document reference (e.g., POL-AML-001)

        Returns:
            Document object or None if not found
        """
        row = self.db.fetch_one(
            "SELECT * FROM documents WHERE doc_ref = ?",
            (doc_ref,),
        )
        return Document.from_row(row) if row else None

    def doc_ref_exists(self, doc_ref: str, exclude_id: Optional[str] = None) -> bool:
        """
        Check if a document reference already exists.

        Args:
            doc_ref: Document reference to check
            exclude_id: Document ID to exclude from check (for updates)

        Returns:
            True if reference exists
        """
        if exclude_id:
            row = self.db.fetch_one(
                "SELECT 1 FROM documents WHERE doc_ref = ? AND doc_id != ?",
                (doc_ref, exclude_id),
            )
        else:
            row = self.db.fetch_one(
                "SELECT 1 FROM documents WHERE doc_ref = ?",
                (doc_ref,),
            )
        return row is not None

    # ============================================================
    # Statistics Methods
    # ============================================================

    def get_total_document_count(self, bypass_restrictions: bool = False) -> int:
        """
        Get total number of documents.

        Args:
            bypass_restrictions: If True, count all documents regardless of user role

        Returns:
            Total document count
        """
        if bypass_restrictions:
            row = self.db.fetch_one("SELECT COUNT(*) as count FROM documents")
            return row["count"] if row else 0

        # Use get_all_documents to respect user restrictions
        documents = self.get_all_documents()
        return len(documents)

    def get_document_counts_by_status(self, bypass_restrictions: bool = False) -> Dict[str, int]:
        """
        Count documents grouped by status.

        Args:
            bypass_restrictions: If True, count all documents regardless of user role

        Returns:
            Dictionary mapping status to count
        """
        if bypass_restrictions:
            rows = self.db.fetch_all(
                """
                SELECT status, COUNT(*) as count
                FROM documents
                GROUP BY status
                """
            )
            return {row["status"]: row["count"] for row in rows}

        # Use get_all_documents to respect user restrictions
        documents = self.get_all_documents()
        counts: Dict[str, int] = {}
        for doc in documents:
            counts[doc.status] = counts.get(doc.status, 0) + 1
        return counts

    def get_document_counts_by_type(self, bypass_restrictions: bool = False) -> Dict[str, int]:
        """
        Count documents grouped by type.

        Args:
            bypass_restrictions: If True, count all documents regardless of user role

        Returns:
            Dictionary mapping type to count
        """
        if bypass_restrictions:
            rows = self.db.fetch_all(
                """
                SELECT doc_type, COUNT(*) as count
                FROM documents
                GROUP BY doc_type
                """
            )
            return {row["doc_type"]: row["count"] for row in rows}

        # Use get_all_documents to respect user restrictions
        documents = self.get_all_documents()
        counts: Dict[str, int] = {}
        for doc in documents:
            counts[doc.doc_type] = counts.get(doc.doc_type, 0) + 1
        return counts

    def get_review_status_counts(self) -> Dict[str, int]:
        """
        Count documents by review status.

        Note: Review status is calculated, not stored, so we fetch
        all documents and count in Python.
        Archived documents are excluded as they are no longer actively managed.

        Returns:
            Dictionary mapping review status to count
        """
        documents = self.get_all_documents()
        counts = {status.value: 0 for status in ReviewStatus}

        for doc in documents:
            if doc.status == DocumentStatus.ARCHIVED.value:
                continue
            status = doc.review_status.value
            counts[status] = counts.get(status, 0) + 1

        return counts

    def get_documents_requiring_attention(self, limit: int = 10) -> List[Document]:
        """
        Get documents that are overdue or due soon.

        Archived documents are excluded as they are no longer actively managed.

        Args:
            limit: Maximum number of documents to return

        Returns:
            List of Document objects sorted by urgency
        """
        # Get all documents and filter by review status
        documents = self.get_all_documents(order_by="next_review_date", order_dir="ASC")

        attention_docs = [
            doc for doc in documents
            if doc.review_status in (ReviewStatus.OVERDUE, ReviewStatus.DUE_SOON)
            and doc.status != DocumentStatus.ARCHIVED.value
        ]

        # Sort by review status (OVERDUE first) then by date
        attention_docs.sort(
            key=lambda d: (
                0 if d.review_status == ReviewStatus.OVERDUE else 1,
                d.next_review_date or "",
            )
        )

        return attention_docs[:limit]

    def get_overdue_documents(self, bypass_restrictions: bool = False) -> List[Document]:
        """
        Get all overdue documents.

        Args:
            bypass_restrictions: If True, return all overdue docs regardless of user role

        Returns:
            List of overdue Document objects
        """
        today = get_today()
        rows = self.db.fetch_all(
            """
            SELECT * FROM documents
            WHERE next_review_date < ?
            AND status = ?
            ORDER BY next_review_date ASC
            """,
            (today, DocumentStatus.ACTIVE.value),
        )
        documents = [Document.from_row(row) for row in rows]

        # Apply user restrictions for EDITOR_RESTRICTED role
        if not bypass_restrictions:
            documents = self._apply_user_restrictions(documents)

        return documents

    # ============================================================
    # CRUD Methods
    # ============================================================

    @require_permission(Permission.ADD_DOCUMENT)
    def create_document(self, data: DocumentCreate) -> Document:
        """
        Create a new document.

        Args:
            data: Document creation data

        Returns:
            Created Document object

        Raises:
            ValueError: If doc_ref already exists
            PermissionError: If user lacks permission or restricted access
        """
        # Check restricted editor access
        self._check_restricted_editor_access(data.category, data.applicable_entity)

        # Validate doc_ref uniqueness
        if self.doc_ref_exists(data.doc_ref):
            raise ValueError(f"Document reference '{data.doc_ref}' already exists")

        doc_id = generate_uuid()
        now = get_now()
        session = SessionManager.get_instance()
        user_id = session.user_id

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO documents (
                    doc_id, doc_type, doc_ref, title, description,
                    category, owner, approver, status, version,
                    effective_date, last_review_date, next_review_date,
                    review_frequency, notes, mandatory_read_all, applicable_entity,
                    created_at, created_by, updated_at, updated_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    data.doc_type,
                    data.doc_ref,
                    data.title,
                    data.description,
                    data.category,
                    data.owner,
                    data.approver,
                    data.status,
                    data.version,
                    data.effective_date,
                    data.last_review_date,
                    data.next_review_date,
                    data.review_frequency,
                    data.notes,
                    1 if data.mandatory_read_all else 0,
                    data.applicable_entity,
                    now,
                    user_id,
                    now,
                    user_id,
                ),
            )

        # Log to history
        self.history_service.log_document_created(doc_id)

        logger.info(f"Document created: {data.doc_ref}")
        return self.get_document_by_id(doc_id)

    @require_permission(Permission.EDIT_DOCUMENT)
    def update_document(self, doc_id: str, data: DocumentUpdate) -> Optional[Document]:
        """
        Update a document.

        Each changed field is logged to the history.

        Args:
            doc_id: Document ID
            data: Update data

        Returns:
            Updated Document object or None if not found

        Raises:
            PermissionError: If user lacks permission or restricted access
        """
        document = self.get_document_by_id(doc_id)
        if document is None:
            return None

        # Check restricted editor access (use current or new category/entity)
        check_category = data.category if data.category else document.category
        check_entity = data.applicable_entity if data.applicable_entity is not None else document.applicable_entity
        self._check_restricted_editor_access(check_category, check_entity)

        now = get_now()
        session = SessionManager.get_instance()
        user_id = session.user_id

        updates = []
        params = []
        changes = []

        # Check each field for changes
        field_mapping = [
            ("title", data.title, document.title),
            ("description", data.description, document.description),
            ("category", data.category, document.category),
            ("owner", data.owner, document.owner),
            ("approver", data.approver, document.approver),
            ("status", data.status, document.status),
            ("version", data.version, document.version),
            ("effective_date", data.effective_date, document.effective_date),
            ("last_review_date", data.last_review_date, document.last_review_date),
            ("next_review_date", data.next_review_date, document.next_review_date),
            ("review_frequency", data.review_frequency, document.review_frequency),
            ("notes", data.notes, document.notes),
            ("applicable_entity", data.applicable_entity, document.applicable_entity),
        ]

        # Handle mandatory_read_all separately (boolean field)
        if data.mandatory_read_all is not None and data.mandatory_read_all != document.mandatory_read_all:
            updates.append("mandatory_read_all = ?")
            params.append(1 if data.mandatory_read_all else 0)
            changes.append(("mandatory_read_all", str(document.mandatory_read_all), str(data.mandatory_read_all)))

        for field_name, new_value, old_value in field_mapping:
            if new_value is not None and new_value != old_value:
                updates.append(f"{field_name} = ?")
                params.append(new_value)
                changes.append((field_name, old_value, new_value))

        if not updates:
            return document  # Nothing to update

        # Add updated_at and updated_by
        updates.extend(["updated_at = ?", "updated_by = ?"])
        params.extend([now, user_id])
        params.append(doc_id)

        query = f"UPDATE documents SET {', '.join(updates)} WHERE doc_id = ?"

        with self.db.get_connection() as conn:
            conn.execute(query, tuple(params))

        # Log each change to history
        for field_name, old_value, new_value in changes:
            if field_name == "status":
                self.history_service.log_status_change(
                    doc_id,
                    old_value or "",
                    new_value or "",
                )
            else:
                self.history_service.log_field_change(
                    doc_id,
                    field_name,
                    old_value,
                    new_value,
                )

        logger.info(f"Document updated: {document.doc_ref}")
        return self.get_document_by_id(doc_id)

    @require_permission(Permission.DELETE_DOCUMENT)
    def delete_document(self, doc_id: str) -> bool:
        """
        Permanently delete a document.

        This also deletes all associated attachments, links, and history.

        Args:
            doc_id: Document ID

        Returns:
            True if successful

        Raises:
            PermissionError: If user lacks permission (admin only)
        """
        document = self.get_document_by_id(doc_id)
        if document is None:
            return False

        with self.db.get_connection() as conn:
            # Attachments, links, and history are deleted via CASCADE
            conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))

        logger.info(f"Document deleted: {document.doc_ref}")
        return True

    @require_permission(Permission.MARK_REVIEWED)
    def mark_as_reviewed(
        self,
        doc_id: str,
        review_notes: Optional[str] = None,
        new_version: Optional[str] = None,
    ) -> Optional[Document]:
        """
        Mark a document as reviewed.

        Updates last_review_date to today and recalculates next_review_date.

        Args:
            doc_id: Document ID
            review_notes: Optional notes about the review
            new_version: Optional new version number

        Returns:
            Updated Document object or None if not found

        Raises:
            PermissionError: If user lacks permission or restricted access
        """
        document = self.get_document_by_id(doc_id)
        if document is None:
            return None

        # Check restricted editor access
        self._check_restricted_editor_access(document.category, document.applicable_entity)

        today = get_today()
        now = get_now()
        session = SessionManager.get_instance()
        user_id = session.user_id

        # Calculate next review date
        next_review = calculate_next_review(today, document.review_frequency)
        if next_review is None:
            # For AD_HOC, keep the existing date or set to one year from now
            next_review = document.next_review_date

        updates = [
            "last_review_date = ?",
            "next_review_date = ?",
            "updated_at = ?",
            "updated_by = ?",
        ]
        params = [today, next_review, now, user_id]

        if new_version:
            updates.append("version = ?")
            params.append(new_version)

        params.append(doc_id)
        query = f"UPDATE documents SET {', '.join(updates)} WHERE doc_id = ?"

        with self.db.get_connection() as conn:
            conn.execute(query, tuple(params))

        # Log to history
        self.history_service.log_review(doc_id, review_notes)

        if new_version and new_version != document.version:
            self.history_service.log_field_change(
                doc_id, "version", document.version, new_version
            )

        logger.info(f"Document reviewed: {document.doc_ref}")
        return self.get_document_by_id(doc_id)

    # ============================================================
    # Reference Code Generation
    # ============================================================

    def generate_next_ref(self, doc_type: str, category: str) -> str:
        """
        Generate the next sequential reference code.

        Format: {TYPE_PREFIX}-{CATEGORY}-{NUMBER}
        Example: POL-AML-001, PROC-AML-002

        Args:
            doc_type: Document type (POLICY, PROCEDURE, etc.)
            category: Category code (AML, GOV, etc.)

        Returns:
            Next available reference code
        """
        # Get type prefix
        try:
            type_enum = DocumentType(doc_type)
            prefix = type_enum.code_prefix
        except ValueError:
            prefix = doc_type[:3].upper()

        # Find existing refs with this prefix and category
        pattern = f"{prefix}-{category}-%"
        rows = self.db.fetch_all(
            "SELECT doc_ref FROM documents WHERE doc_ref LIKE ? ORDER BY doc_ref DESC",
            (pattern,),
        )

        if not rows:
            return f"{prefix}-{category}-001"

        # Extract the highest number
        max_num = 0
        number_pattern = re.compile(rf"^{prefix}-{category}-(\d+)$")

        for row in rows:
            match = number_pattern.match(row["doc_ref"])
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num

        next_num = max_num + 1
        return f"{prefix}-{category}-{next_num:03d}"

    def suggest_ref(self, doc_type: str, category: str) -> str:
        """
        Suggest a reference code for a new document.

        This is an alias for generate_next_ref for clarity.

        Args:
            doc_type: Document type
            category: Category code

        Returns:
            Suggested reference code
        """
        return self.generate_next_ref(doc_type, category)

    # ============================================================
    # Sample Data Seeding
    # ============================================================

    def seed_sample_documents(self) -> int:
        """
        Seed sample documents for testing purposes.

        Creates 5 dummy policies with various statuses and categories.
        Only runs if no documents exist in the database.

        Returns:
            Number of documents created
        """
        # Check if documents already exist
        if self.get_total_document_count() > 0:
            logger.info("Documents already exist, skipping sample data seeding")
            return 0

        session = SessionManager.get_instance()
        if not session.is_authenticated:
            logger.warning("Cannot seed sample documents: no user logged in")
            return 0

        user_id = session.current_user.user_id
        now = get_now()
        today = get_today()

        # Sample documents data
        sample_documents = [
            {
                "doc_type": "POLICY",
                "doc_ref": "POL-AML-001",
                "title": "Anti-Money Laundering Policy",
                "description": "This policy outlines the company's approach to preventing money laundering and terrorist financing activities.",
                "category": "AML",
                "owner": "Compliance Officer",
                "approver": "Board of Directors",
                "status": "ACTIVE",
                "version": "2.1",
                "effective_date": "2024-01-15",
                "last_review_date": "2024-01-15",
                "next_review_date": "2025-01-15",
                "review_frequency": "ANNUAL",
                "notes": "Updated to comply with latest CSSF regulations.",
            },
            {
                "doc_type": "POLICY",
                "doc_ref": "POL-GOV-001",
                "title": "Corporate Governance Framework",
                "description": "Establishes the governance structure and decision-making processes for the organization.",
                "category": "GOV",
                "owner": "CEO",
                "approver": "Board of Directors",
                "status": "ACTIVE",
                "version": "1.0",
                "effective_date": "2023-06-01",
                "last_review_date": "2023-06-01",
                "next_review_date": "2024-06-01",
                "review_frequency": "ANNUAL",
                "notes": "Initial version approved by the Board.",
            },
            {
                "doc_type": "PROCEDURE",
                "doc_ref": "PROC-IT-001",
                "title": "Information Security Incident Response",
                "description": "Step-by-step procedures for identifying, containing, and responding to security incidents.",
                "category": "IT",
                "owner": "IT Manager",
                "approver": "CTO",
                "status": "UNDER_REVIEW",
                "version": "3.0",
                "effective_date": "2023-03-20",
                "last_review_date": "2023-03-20",
                "next_review_date": "2024-03-20",
                "review_frequency": "ANNUAL",
                "notes": "Under review for alignment with ISO 27001.",
            },
            {
                "doc_type": "POLICY",
                "doc_ref": "POL-DP-001",
                "title": "Data Protection & Privacy Policy",
                "description": "Defines how personal data is collected, processed, stored, and protected in compliance with GDPR.",
                "category": "DP",
                "owner": "Data Protection Officer",
                "approver": "Legal Counsel",
                "status": "ACTIVE",
                "version": "2.0",
                "effective_date": "2024-05-25",
                "last_review_date": "2024-05-25",
                "next_review_date": "2024-11-25",
                "review_frequency": "SEMI_ANNUAL",
                "notes": "Updated with new data retention schedules.",
            },
            {
                "doc_type": "MANUAL",
                "doc_ref": "MAN-HR-001",
                "title": "Employee Handbook",
                "description": "Comprehensive guide covering employment policies, benefits, and workplace expectations.",
                "category": "HR",
                "owner": "HR Director",
                "approver": "CEO",
                "status": "DRAFT",
                "version": "1.0",
                "effective_date": "2025-01-01",
                "last_review_date": "2024-12-01",
                "next_review_date": "2026-01-01",
                "review_frequency": "ANNUAL",
                "notes": "Draft pending final review.",
            },
        ]

        created_count = 0

        for doc_data in sample_documents:
            doc_id = generate_uuid()

            with self.db.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO documents (
                        doc_id, doc_type, doc_ref, title, description, category,
                        owner, approver, status, version, effective_date,
                        last_review_date, next_review_date, review_frequency,
                        notes, mandatory_read_all, applicable_entity,
                        created_at, created_by, updated_at, updated_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        doc_id,
                        doc_data["doc_type"],
                        doc_data["doc_ref"],
                        doc_data["title"],
                        doc_data["description"],
                        doc_data["category"],
                        doc_data["owner"],
                        doc_data["approver"],
                        doc_data["status"],
                        doc_data["version"],
                        doc_data["effective_date"],
                        doc_data["last_review_date"],
                        doc_data["next_review_date"],
                        doc_data["review_frequency"],
                        doc_data["notes"],
                        0,  # mandatory_read_all
                        None,  # applicable_entity
                        now,
                        user_id,
                        now,
                        user_id,
                    ),
                )

            # Log creation to history
            self.history_service.log_document_created(doc_id)
            created_count += 1
            logger.info(f"Sample document created: {doc_data['doc_ref']}")

        logger.info(f"Seeded {created_count} sample documents")
        return created_count
