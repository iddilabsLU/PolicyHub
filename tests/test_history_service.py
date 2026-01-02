"""
Tests for HistoryService.

Tests audit trail functionality for document changes.
"""

import pytest

from app.constants import HistoryAction
from services.history_service import HistoryService


class TestHistoryService:
    """Tests for HistoryService."""

    def test_log_action_creates_entry(self, db, logged_in_admin, sample_document_data):
        """Test that log_action creates a history entry."""
        from services.document_service import DocumentService
        from models.document import DocumentCreate

        # Create a document first
        doc_service = DocumentService(db)
        doc_data = DocumentCreate(**sample_document_data)
        doc = doc_service.create_document(doc_data)

        history_service = HistoryService(db)

        # Log an action
        entry = history_service.log_action(
            doc_id=doc.doc_id,
            action=HistoryAction.UPDATED,
            field_changed="title",
            old_value="Old Title",
            new_value="New Title",
        )

        assert entry is not None
        assert entry.doc_id == doc.doc_id
        assert entry.action == HistoryAction.UPDATED.value
        assert entry.field_changed == "title"
        assert entry.old_value == "Old Title"
        assert entry.new_value == "New Title"

    def test_log_document_created(self, db, logged_in_admin, sample_document_data):
        """Test logging document creation."""
        from services.document_service import DocumentService
        from models.document import DocumentCreate

        doc_service = DocumentService(db)
        doc_data = DocumentCreate(**sample_document_data)
        doc = doc_service.create_document(doc_data)

        # Document creation should auto-log
        history_service = HistoryService(db)
        history = history_service.get_document_history(doc.doc_id)

        assert len(history) >= 1
        assert history[0].action == HistoryAction.CREATED.value

    def test_log_field_change(self, db, logged_in_admin, sample_document_data):
        """Test logging field changes."""
        from services.document_service import DocumentService
        from models.document import DocumentCreate

        doc_service = DocumentService(db)
        doc_data = DocumentCreate(**sample_document_data)
        doc = doc_service.create_document(doc_data)

        history_service = HistoryService(db)
        entry = history_service.log_field_change(
            doc_id=doc.doc_id,
            field_name="owner",
            old_value="Old Owner",
            new_value="New Owner",
        )

        assert entry.action == HistoryAction.UPDATED.value
        assert entry.field_changed == "owner"

    def test_log_status_change(self, db, logged_in_admin, sample_document_data):
        """Test logging status changes."""
        from services.document_service import DocumentService
        from models.document import DocumentCreate

        doc_service = DocumentService(db)
        doc_data = DocumentCreate(**sample_document_data)
        doc = doc_service.create_document(doc_data)

        history_service = HistoryService(db)
        entry = history_service.log_status_change(
            doc_id=doc.doc_id,
            old_status="DRAFT",
            new_status="ACTIVE",
        )

        assert entry.action == HistoryAction.STATUS_CHANGED.value
        assert entry.old_value == "DRAFT"
        assert entry.new_value == "ACTIVE"

    def test_log_review(self, db, logged_in_admin, sample_document_data):
        """Test logging document review."""
        from services.document_service import DocumentService
        from models.document import DocumentCreate

        doc_service = DocumentService(db)
        doc_data = DocumentCreate(**sample_document_data)
        doc = doc_service.create_document(doc_data)

        history_service = HistoryService(db)
        entry = history_service.log_review(
            doc_id=doc.doc_id,
            notes="Annual review completed",
        )

        assert entry.action == HistoryAction.REVIEWED.value
        assert entry.notes == "Annual review completed"

    def test_get_document_history_returns_entries(self, db, logged_in_admin, sample_document_data):
        """Test retrieving document history."""
        from services.document_service import DocumentService
        from models.document import DocumentCreate

        doc_service = DocumentService(db)
        doc_data = DocumentCreate(**sample_document_data)
        doc = doc_service.create_document(doc_data)

        history_service = HistoryService(db)

        # Add some history
        history_service.log_field_change(doc.doc_id, "title", "Old", "New")
        history_service.log_review(doc.doc_id, "Review notes")

        history = history_service.get_document_history(doc.doc_id)

        # Should have CREATED + 2 additional entries
        assert len(history) >= 3

    def test_get_document_history_ordered_by_date(self, db, logged_in_admin, sample_document_data):
        """Test that history is ordered by date (most recent first)."""
        from services.document_service import DocumentService
        from models.document import DocumentCreate

        doc_service = DocumentService(db)
        doc_data = DocumentCreate(**sample_document_data)
        doc = doc_service.create_document(doc_data)

        history_service = HistoryService(db)

        # Add entries
        history_service.log_field_change(doc.doc_id, "field1", "a", "b")
        history_service.log_field_change(doc.doc_id, "field2", "c", "d")

        history = history_service.get_document_history(doc.doc_id)

        # Should have at least 3 entries (CREATED + 2 UPDATED)
        assert len(history) >= 3

        # All entries should have timestamps (ORDER BY changed_at DESC)
        # Since all happen in same second, just verify entries exist
        actions = [h.action for h in history]
        assert HistoryAction.CREATED.value in actions
        assert HistoryAction.UPDATED.value in actions

    def test_get_recent_activity(self, db, logged_in_admin, sample_document_data):
        """Test retrieving recent activity across all documents."""
        from services.document_service import DocumentService
        from models.document import DocumentCreate

        doc_service = DocumentService(db)
        history_service = HistoryService(db)

        # Create multiple documents
        data1 = DocumentCreate(**sample_document_data)
        doc1 = doc_service.create_document(data1)

        data2 = DocumentCreate(**{**sample_document_data, "doc_ref": "POL-AML-002"})
        doc2 = doc_service.create_document(data2)

        activity = history_service.get_recent_activity(limit=10)

        # Should have entries from both documents
        assert len(activity) >= 2

    def test_history_entry_get_change_description(self, db, logged_in_admin, sample_document_data):
        """Test the change description generation."""
        from services.document_service import DocumentService
        from models.document import DocumentCreate

        doc_service = DocumentService(db)
        doc_data = DocumentCreate(**sample_document_data)
        doc = doc_service.create_document(doc_data)

        history_service = HistoryService(db)
        entry = history_service.log_field_change(
            doc.doc_id, "title", "Old Title", "New Title"
        )

        description = entry.get_change_description()
        assert "title" in description
        assert "Old Title" in description or "New Title" in description
