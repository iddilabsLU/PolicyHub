"""
PolicyHub Document Link Model

Represents a relationship between two documents.
"""

from dataclasses import dataclass
from sqlite3 import Row

from app.constants import LinkType


@dataclass
class DocumentLink:
    """
    Represents a link between two documents.

    Attributes:
        link_id: Unique identifier (UUID)
        parent_doc_id: Foreign key to the parent document (e.g., Policy)
        child_doc_id: Foreign key to the child document (e.g., Procedure)
        link_type: Type of relationship (IMPLEMENTS, REFERENCES, SUPERSEDES)
        created_at: Creation timestamp (ISO 8601)
        created_by: User ID who created this link
    """

    link_id: str
    parent_doc_id: str
    child_doc_id: str
    link_type: str
    created_at: str
    created_by: str

    @property
    def link_type_display(self) -> str:
        """Get the display name for the link type."""
        try:
            return LinkType(self.link_type).display_name
        except ValueError:
            return self.link_type

    def get_relationship_text(self, is_parent: bool = True) -> str:
        """
        Get human-readable relationship text.

        Args:
            is_parent: True if viewing from parent's perspective

        Returns:
            Relationship description
        """
        if self.link_type == LinkType.IMPLEMENTS.value:
            return "Implements" if not is_parent else "Implemented by"
        elif self.link_type == LinkType.REFERENCES.value:
            return "References" if is_parent else "Referenced by"
        elif self.link_type == LinkType.SUPERSEDES.value:
            return "Supersedes" if is_parent else "Superseded by"
        return self.link_type

    @classmethod
    def from_row(cls, row: Row) -> "DocumentLink":
        """
        Create a DocumentLink from a SQLite row.

        Args:
            row: SQLite Row object with link data

        Returns:
            DocumentLink instance
        """
        return cls(
            link_id=row["link_id"],
            parent_doc_id=row["parent_doc_id"],
            child_doc_id=row["child_doc_id"],
            link_type=row["link_type"],
            created_at=row["created_at"],
            created_by=row["created_by"],
        )

    def to_dict(self) -> dict:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation of the link
        """
        return {
            "link_id": self.link_id,
            "parent_doc_id": self.parent_doc_id,
            "child_doc_id": self.child_doc_id,
            "link_type": self.link_type,
            "created_at": self.created_at,
            "created_by": self.created_by,
        }


@dataclass
class DocumentLinkCreate:
    """Data required to create a new document link."""

    parent_doc_id: str
    child_doc_id: str
    link_type: str
