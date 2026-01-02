"""
PolicyHub History Model

Represents an audit trail entry for document changes.
"""

from dataclasses import dataclass
from sqlite3 import Row
from typing import Optional

from app.constants import HistoryAction


@dataclass
class HistoryEntry:
    """
    Represents an audit trail entry.

    Attributes:
        history_id: Unique identifier (UUID)
        doc_id: Foreign key to documents
        action: Type of action performed
        changed_by: User ID who made the change
        changed_at: Timestamp of the change (ISO 8601)
        field_changed: Name of the field that was changed (optional)
        old_value: Previous value (optional)
        new_value: New value (optional)
        notes: Additional notes about the change (optional)
    """

    history_id: str
    doc_id: str
    action: str
    changed_by: str
    changed_at: str
    field_changed: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    notes: Optional[str] = None

    @property
    def action_display(self) -> str:
        """Get the display name for the action."""
        try:
            action_enum = HistoryAction(self.action)
            names = {
                HistoryAction.CREATED: "Created",
                HistoryAction.UPDATED: "Updated",
                HistoryAction.STATUS_CHANGED: "Status Changed",
                HistoryAction.REVIEWED: "Reviewed",
                HistoryAction.ATTACHMENT_ADDED: "Attachment Added",
                HistoryAction.ATTACHMENT_REMOVED: "Attachment Removed",
            }
            return names.get(action_enum, self.action)
        except ValueError:
            return self.action

    def get_change_description(self) -> str:
        """
        Get a human-readable description of the change.

        Returns:
            Description string
        """
        if self.action == HistoryAction.CREATED.value:
            return "Document created"

        if self.action == HistoryAction.REVIEWED.value:
            return self.notes or "Document reviewed"

        if self.action == HistoryAction.ATTACHMENT_ADDED.value:
            return f"Attachment added: {self.new_value or 'file'}"

        if self.action == HistoryAction.ATTACHMENT_REMOVED.value:
            return f"Attachment removed: {self.old_value or 'file'}"

        if self.field_changed:
            if self.old_value and self.new_value:
                return f"{self.field_changed}: {self.old_value} → {self.new_value}"
            elif self.new_value:
                return f"{self.field_changed} set to: {self.new_value}"
            else:
                return f"{self.field_changed} changed"

        return self.notes or self.action_display

    @classmethod
    def from_row(cls, row: Row) -> "HistoryEntry":
        """
        Create a HistoryEntry from a SQLite row.

        Args:
            row: SQLite Row object with history data

        Returns:
            HistoryEntry instance
        """
        return cls(
            history_id=row["history_id"],
            doc_id=row["doc_id"],
            action=row["action"],
            field_changed=row["field_changed"],
            old_value=row["old_value"],
            new_value=row["new_value"],
            changed_by=row["changed_by"],
            changed_at=row["changed_at"],
            notes=row["notes"],
        )

    def to_dict(self) -> dict:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation of the history entry
        """
        return {
            "history_id": self.history_id,
            "doc_id": self.doc_id,
            "action": self.action,
            "field_changed": self.field_changed,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changed_by": self.changed_by,
            "changed_at": self.changed_at,
            "notes": self.notes,
        }


@dataclass
class HistoryCreate:
    """Data required to create a new history entry."""

    doc_id: str
    action: str
    changed_by: str
    field_changed: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    notes: Optional[str] = None
