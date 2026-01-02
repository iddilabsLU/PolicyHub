"""
PolicyHub Document Model

Represents a policy, procedure, manual, or register in the system.
"""

from dataclasses import dataclass
from sqlite3 import Row
from typing import Optional

from app.constants import DocumentStatus, DocumentType, ReviewFrequency, ReviewStatus
from utils.dates import get_review_status


@dataclass
class Document:
    """
    Represents a document in the register.

    Attributes:
        doc_id: Unique identifier (UUID)
        doc_type: Type of document (POLICY, PROCEDURE, MANUAL, REGISTER)
        doc_ref: Unique reference code (e.g., POL-AML-001)
        title: Document title
        category: Category code (e.g., AML, GOV, OPS)
        owner: Responsible person/role
        status: Document status (DRAFT, ACTIVE, etc.)
        version: Version number (e.g., "2.1")
        effective_date: Date the document became effective (ISO 8601)
        last_review_date: Date of last review (ISO 8601)
        next_review_date: Date of next review (ISO 8601)
        review_frequency: How often to review (ANNUAL, QUARTERLY, etc.)
        created_at: Creation timestamp (ISO 8601)
        created_by: User ID who created this document
        updated_at: Last update timestamp (ISO 8601)
        updated_by: User ID who last updated this document
        description: Brief description (optional)
        approver: Final approver (optional)
        notes: Free text notes (optional)
    """

    doc_id: str
    doc_type: str
    doc_ref: str
    title: str
    category: str
    owner: str
    status: str
    version: str
    effective_date: str
    last_review_date: str
    next_review_date: str
    review_frequency: str
    created_at: str
    created_by: str
    updated_at: str
    updated_by: str
    description: Optional[str] = None
    approver: Optional[str] = None
    notes: Optional[str] = None

    @property
    def type_display(self) -> str:
        """Get the display name for the document type."""
        try:
            return DocumentType(self.doc_type).display_name
        except ValueError:
            return self.doc_type

    @property
    def status_display(self) -> str:
        """Get the display name for the document status."""
        try:
            return DocumentStatus(self.status).display_name
        except ValueError:
            return self.status

    @property
    def frequency_display(self) -> str:
        """Get the display name for the review frequency."""
        try:
            return ReviewFrequency(self.review_frequency).display_name
        except ValueError:
            return self.review_frequency

    @property
    def review_status(self) -> ReviewStatus:
        """Get the current review status based on next_review_date."""
        return get_review_status(self.next_review_date)

    @property
    def review_status_display(self) -> str:
        """Get the display name for the review status."""
        return self.review_status.display_name

    def is_active(self) -> bool:
        """Check if the document is active."""
        return self.status == DocumentStatus.ACTIVE.value

    def is_overdue(self) -> bool:
        """Check if the document is overdue for review."""
        return self.review_status == ReviewStatus.OVERDUE

    @classmethod
    def from_row(cls, row: Row) -> "Document":
        """
        Create a Document from a SQLite row.

        Args:
            row: SQLite Row object with document data

        Returns:
            Document instance
        """
        return cls(
            doc_id=row["doc_id"],
            doc_type=row["doc_type"],
            doc_ref=row["doc_ref"],
            title=row["title"],
            description=row["description"],
            category=row["category"],
            owner=row["owner"],
            approver=row["approver"],
            status=row["status"],
            version=row["version"],
            effective_date=row["effective_date"],
            last_review_date=row["last_review_date"],
            next_review_date=row["next_review_date"],
            review_frequency=row["review_frequency"],
            notes=row["notes"],
            created_at=row["created_at"],
            created_by=row["created_by"],
            updated_at=row["updated_at"],
            updated_by=row["updated_by"],
        )

    def to_dict(self) -> dict:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation of the document
        """
        return {
            "doc_id": self.doc_id,
            "doc_type": self.doc_type,
            "doc_ref": self.doc_ref,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "owner": self.owner,
            "approver": self.approver,
            "status": self.status,
            "version": self.version,
            "effective_date": self.effective_date,
            "last_review_date": self.last_review_date,
            "next_review_date": self.next_review_date,
            "review_frequency": self.review_frequency,
            "notes": self.notes,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "updated_at": self.updated_at,
            "updated_by": self.updated_by,
        }


@dataclass
class DocumentCreate:
    """Data required to create a new document."""

    doc_type: str
    doc_ref: str
    title: str
    category: str
    owner: str
    status: str
    version: str
    effective_date: str
    last_review_date: str
    next_review_date: str
    review_frequency: str
    description: Optional[str] = None
    approver: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class DocumentUpdate:
    """Data for updating an existing document."""

    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    owner: Optional[str] = None
    approver: Optional[str] = None
    status: Optional[str] = None
    version: Optional[str] = None
    effective_date: Optional[str] = None
    last_review_date: Optional[str] = None
    next_review_date: Optional[str] = None
    review_frequency: Optional[str] = None
    notes: Optional[str] = None
