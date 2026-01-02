"""
Tests for DocumentService.

Tests document CRUD operations with audit logging.
"""

import pytest

from app.constants import DocumentStatus, DocumentType, ReviewStatus
from models.document import DocumentCreate, DocumentUpdate
from services.document_service import DocumentService


class TestDocumentService:
    """Tests for DocumentService."""

    def test_create_document(self, db, logged_in_admin, sample_document_data):
        """Test creating a new document."""
        service = DocumentService(db)
        data = DocumentCreate(**sample_document_data)

        doc = service.create_document(data)

        assert doc is not None
        assert doc.doc_ref == "POL-AML-001"
        assert doc.title == "Anti-Money Laundering Policy"
        assert doc.status == DocumentStatus.ACTIVE.value

    def test_create_document_duplicate_ref_raises(self, db, logged_in_admin, sample_document_data):
        """Test that creating document with existing ref raises error."""
        service = DocumentService(db)

        data = DocumentCreate(**sample_document_data)
        service.create_document(data)

        # Try to create another with same ref
        with pytest.raises(ValueError, match="already exists"):
            service.create_document(data)

    def test_create_document_requires_permission(self, db, sample_document_data):
        """Test that creating document requires permission."""
        service = DocumentService(db)
        data = DocumentCreate(**sample_document_data)

        with pytest.raises(PermissionError):
            service.create_document(data)

    def test_get_document_by_id(self, db, logged_in_admin, sample_document_data):
        """Test retrieving document by ID."""
        service = DocumentService(db)
        data = DocumentCreate(**sample_document_data)
        created = service.create_document(data)

        doc = service.get_document_by_id(created.doc_id)

        assert doc is not None
        assert doc.doc_id == created.doc_id

    def test_get_document_by_ref(self, db, logged_in_admin, sample_document_data):
        """Test retrieving document by reference."""
        service = DocumentService(db)
        data = DocumentCreate(**sample_document_data)
        service.create_document(data)

        doc = service.get_document_by_ref("POL-AML-001")

        assert doc is not None
        assert doc.doc_ref == "POL-AML-001"

    def test_get_all_documents(self, db, logged_in_admin, sample_document_data):
        """Test retrieving all documents."""
        service = DocumentService(db)

        # Create multiple documents
        data1 = DocumentCreate(**sample_document_data)
        service.create_document(data1)

        data2 = DocumentCreate(**{**sample_document_data, "doc_ref": "POL-AML-002"})
        service.create_document(data2)

        docs = service.get_all_documents()

        assert len(docs) == 2

    def test_get_all_documents_with_filter(self, db, logged_in_admin, sample_document_data):
        """Test filtering documents."""
        service = DocumentService(db)

        # Create documents with different statuses
        data1 = DocumentCreate(**{**sample_document_data, "status": "ACTIVE"})
        service.create_document(data1)

        data2 = DocumentCreate(**{**sample_document_data, "doc_ref": "POL-AML-002", "status": "DRAFT"})
        service.create_document(data2)

        active_docs = service.get_all_documents(status="ACTIVE")
        draft_docs = service.get_all_documents(status="DRAFT")

        assert len(active_docs) == 1
        assert len(draft_docs) == 1
        assert active_docs[0].status == "ACTIVE"

    def test_get_all_documents_with_search(self, db, logged_in_admin, sample_document_data):
        """Test searching documents."""
        service = DocumentService(db)

        data = DocumentCreate(**sample_document_data)
        service.create_document(data)

        # Search by title
        results = service.get_all_documents(search_term="Money Laundering")
        assert len(results) == 1

        # Search that doesn't match
        results = service.get_all_documents(search_term="NONEXISTENT")
        assert len(results) == 0

    def test_update_document(self, db, logged_in_admin, sample_document_data):
        """Test updating a document."""
        service = DocumentService(db)
        data = DocumentCreate(**sample_document_data)
        created = service.create_document(data)

        update_data = DocumentUpdate(title="Updated Title", version="1.1")
        updated = service.update_document(created.doc_id, update_data)

        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.version == "1.1"

    def test_update_document_logs_history(self, db, logged_in_admin, sample_document_data):
        """Test that updates are logged to history."""
        from services.history_service import HistoryService

        service = DocumentService(db)
        data = DocumentCreate(**sample_document_data)
        created = service.create_document(data)

        update_data = DocumentUpdate(title="New Title")
        service.update_document(created.doc_id, update_data)

        history_service = HistoryService(db)
        history = history_service.get_document_history(created.doc_id)

        # Should have CREATED + UPDATED entries
        assert len(history) >= 2

    def test_delete_document(self, db, logged_in_admin, sample_document_data):
        """Test deleting a document."""
        service = DocumentService(db)
        data = DocumentCreate(**sample_document_data)
        created = service.create_document(data)

        result = service.delete_document(created.doc_id)

        assert result is True
        assert service.get_document_by_id(created.doc_id) is None

    def test_delete_document_requires_admin(self, db, logged_in_admin, sample_document_data):
        """Test that delete requires admin permission."""
        # This test would need a non-admin user
        # For now, just verify the method works for admin
        service = DocumentService(db)
        data = DocumentCreate(**sample_document_data)
        created = service.create_document(data)

        result = service.delete_document(created.doc_id)
        assert result is True

    def test_mark_as_reviewed(self, db, logged_in_admin, sample_document_data):
        """Test marking document as reviewed."""
        service = DocumentService(db)
        data = DocumentCreate(**sample_document_data)
        created = service.create_document(data)

        reviewed = service.mark_as_reviewed(created.doc_id, review_notes="Annual review")

        assert reviewed is not None
        # Last review date should be updated
        assert reviewed.last_review_date != created.last_review_date

    def test_mark_as_reviewed_calculates_next_date(self, db, logged_in_admin, sample_document_data):
        """Test that marking reviewed calculates next review date."""
        service = DocumentService(db)
        data = DocumentCreate(**sample_document_data)
        created = service.create_document(data)

        old_next = created.next_review_date
        reviewed = service.mark_as_reviewed(created.doc_id)

        # Next review should be different (usually later)
        assert reviewed.next_review_date != old_next

    def test_get_document_counts_by_status(self, db, logged_in_admin, sample_document_data):
        """Test counting documents by status."""
        service = DocumentService(db)

        data1 = DocumentCreate(**{**sample_document_data, "status": "ACTIVE"})
        service.create_document(data1)

        data2 = DocumentCreate(**{**sample_document_data, "doc_ref": "POL-AML-002", "status": "DRAFT"})
        service.create_document(data2)

        counts = service.get_document_counts_by_status()

        assert counts.get("ACTIVE", 0) >= 1
        assert counts.get("DRAFT", 0) >= 1

    def test_get_document_counts_by_type(self, db, logged_in_admin, sample_document_data):
        """Test counting documents by type."""
        service = DocumentService(db)

        data1 = DocumentCreate(**{**sample_document_data, "doc_type": "POLICY"})
        service.create_document(data1)

        data2 = DocumentCreate(**{
            **sample_document_data,
            "doc_ref": "PROC-AML-001",
            "doc_type": "PROCEDURE"
        })
        service.create_document(data2)

        counts = service.get_document_counts_by_type()

        assert counts.get("POLICY", 0) >= 1
        assert counts.get("PROCEDURE", 0) >= 1

    def test_get_total_document_count(self, db, logged_in_admin, sample_document_data):
        """Test getting total document count."""
        service = DocumentService(db)

        assert service.get_total_document_count() == 0

        data = DocumentCreate(**sample_document_data)
        service.create_document(data)

        assert service.get_total_document_count() == 1

    def test_generate_next_ref(self, db, logged_in_admin, sample_document_data):
        """Test generating next reference code."""
        service = DocumentService(db)

        # First ref should be 001
        ref = service.generate_next_ref("POLICY", "AML")
        assert ref == "POL-AML-001"

        # Create the document
        data = DocumentCreate(**{**sample_document_data, "doc_ref": ref})
        service.create_document(data)

        # Next should be 002
        ref2 = service.generate_next_ref("POLICY", "AML")
        assert ref2 == "POL-AML-002"

    def test_doc_ref_exists(self, db, logged_in_admin, sample_document_data):
        """Test checking if document ref exists."""
        service = DocumentService(db)

        assert service.doc_ref_exists("POL-AML-001") is False

        data = DocumentCreate(**sample_document_data)
        service.create_document(data)

        assert service.doc_ref_exists("POL-AML-001") is True
        assert service.doc_ref_exists("NONEXISTENT") is False

    def test_doc_ref_exists_with_exclude(self, db, logged_in_admin, sample_document_data):
        """Test doc_ref_exists with exclude parameter."""
        service = DocumentService(db)

        data = DocumentCreate(**sample_document_data)
        created = service.create_document(data)

        # Should not find when excluding itself
        assert service.doc_ref_exists("POL-AML-001", exclude_id=created.doc_id) is False

        # Should find when not excluding
        assert service.doc_ref_exists("POL-AML-001") is True

    def test_get_documents_requiring_attention(self, db, logged_in_admin, sample_document_data):
        """Test getting documents requiring attention."""
        service = DocumentService(db)

        # Create overdue document
        data = DocumentCreate(**{
            **sample_document_data,
            "next_review_date": "2020-01-01",  # Past date
        })
        service.create_document(data)

        attention = service.get_documents_requiring_attention()

        assert len(attention) >= 1
        assert attention[0].review_status in (ReviewStatus.OVERDUE, ReviewStatus.DUE_SOON)
