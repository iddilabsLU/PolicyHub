"""
Tests for LinkService.
"""

import pytest

from app.constants import LinkType, UserRole
from core.database import DatabaseManager
from core.session import SessionManager
from models.document import DocumentCreate
from services.auth_service import AuthService
from services.document_service import DocumentService
from services.link_service import LinkService


@pytest.fixture
def policy_document(db, logged_in_admin):
    """Create a sample policy document."""
    doc_service = DocumentService(db)
    doc_data = DocumentCreate(
        doc_type="POLICY",
        doc_ref="POL-AML-001",
        title="AML Policy",
        category="AML",
        owner="Test Owner",
        status="ACTIVE",
        version="1.0",
        review_frequency="ANNUAL",
        effective_date="2024-01-01",
        last_review_date="2024-01-01",
        next_review_date="2025-01-01",
    )
    return doc_service.create_document(doc_data)


@pytest.fixture
def procedure_document(db, logged_in_admin):
    """Create a sample procedure document."""
    doc_service = DocumentService(db)
    doc_data = DocumentCreate(
        doc_type="PROCEDURE",
        doc_ref="PROC-AML-001",
        title="AML Procedure",
        category="AML",
        owner="Test Owner",
        status="ACTIVE",
        version="1.0",
        review_frequency="ANNUAL",
        effective_date="2024-01-01",
        last_review_date="2024-01-01",
        next_review_date="2025-01-01",
    )
    return doc_service.create_document(doc_data)


@pytest.fixture
def another_document(db, logged_in_admin):
    """Create another sample document."""
    doc_service = DocumentService(db)
    doc_data = DocumentCreate(
        doc_type="MANUAL",
        doc_ref="MAN-OPS-001",
        title="Operations Manual",
        category="OPS",
        owner="Test Owner",
        status="ACTIVE",
        version="1.0",
        review_frequency="ANNUAL",
        effective_date="2024-01-01",
        last_review_date="2024-01-01",
        next_review_date="2025-01-01",
    )
    return doc_service.create_document(doc_data)


class TestLinkService:
    """Tests for LinkService."""

    def test_create_link(self, db, policy_document, procedure_document, logged_in_admin):
        """Test creating a link between documents."""
        service = LinkService(db)

        link = service.create_link(
            parent_doc_id=policy_document.doc_id,
            child_doc_id=procedure_document.doc_id,
            link_type=LinkType.IMPLEMENTS.value,
        )

        assert link.parent_doc_id == policy_document.doc_id
        assert link.child_doc_id == procedure_document.doc_id
        assert link.link_type == LinkType.IMPLEMENTS.value

    def test_create_link_duplicate_raises(self, db, policy_document, procedure_document, logged_in_admin):
        """Test that creating duplicate link raises error."""
        service = LinkService(db)

        # Create first link
        service.create_link(
            parent_doc_id=policy_document.doc_id,
            child_doc_id=procedure_document.doc_id,
            link_type=LinkType.IMPLEMENTS.value,
        )

        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            service.create_link(
                parent_doc_id=policy_document.doc_id,
                child_doc_id=procedure_document.doc_id,
                link_type=LinkType.IMPLEMENTS.value,
            )

    def test_create_link_self_reference_raises(self, db, policy_document, logged_in_admin):
        """Test that linking a document to itself raises error."""
        service = LinkService(db)

        with pytest.raises(ValueError, match="Cannot link a document to itself"):
            service.create_link(
                parent_doc_id=policy_document.doc_id,
                child_doc_id=policy_document.doc_id,
                link_type=LinkType.REFERENCES.value,
            )

    def test_create_link_invalid_type_raises(self, db, policy_document, procedure_document, logged_in_admin):
        """Test that invalid link type raises error."""
        service = LinkService(db)

        with pytest.raises(ValueError, match="Invalid link type"):
            service.create_link(
                parent_doc_id=policy_document.doc_id,
                child_doc_id=procedure_document.doc_id,
                link_type="INVALID",
            )

    def test_get_links_for_document(self, db, policy_document, procedure_document, another_document, logged_in_admin):
        """Test getting all links for a document."""
        service = LinkService(db)

        # Create links
        service.create_link(
            parent_doc_id=policy_document.doc_id,
            child_doc_id=procedure_document.doc_id,
            link_type=LinkType.IMPLEMENTS.value,
        )
        service.create_link(
            parent_doc_id=policy_document.doc_id,
            child_doc_id=another_document.doc_id,
            link_type=LinkType.REFERENCES.value,
        )

        # Get links for policy (as parent)
        links = service.get_links_for_document(policy_document.doc_id)
        assert len(links) == 2

        # Get links for procedure (as child)
        links = service.get_links_for_document(procedure_document.doc_id)
        assert len(links) == 1
        assert links[0].doc_ref == policy_document.doc_ref

    def test_delete_link(self, db, policy_document, procedure_document, logged_in_admin):
        """Test deleting a link."""
        service = LinkService(db)

        link = service.create_link(
            parent_doc_id=policy_document.doc_id,
            child_doc_id=procedure_document.doc_id,
            link_type=LinkType.IMPLEMENTS.value,
        )

        result = service.delete_link(link.link_id)
        assert result is True

        # Verify deleted
        links = service.get_links_for_document(policy_document.doc_id)
        assert len(links) == 0

    def test_delete_link_not_found_raises(self, db, logged_in_admin):
        """Test deleting non-existent link raises error."""
        service = LinkService(db)

        with pytest.raises(ValueError, match="Link not found"):
            service.delete_link("nonexistent-id")

    def test_link_exists(self, db, policy_document, procedure_document, logged_in_admin):
        """Test checking if link exists."""
        service = LinkService(db)

        assert service.link_exists(policy_document.doc_id, procedure_document.doc_id) is False

        service.create_link(
            parent_doc_id=policy_document.doc_id,
            child_doc_id=procedure_document.doc_id,
            link_type=LinkType.IMPLEMENTS.value,
        )

        assert service.link_exists(policy_document.doc_id, procedure_document.doc_id) is True
        assert service.link_exists(
            policy_document.doc_id,
            procedure_document.doc_id,
            link_type=LinkType.IMPLEMENTS.value
        ) is True
        assert service.link_exists(
            policy_document.doc_id,
            procedure_document.doc_id,
            link_type=LinkType.REFERENCES.value
        ) is False

    def test_get_link_count(self, db, policy_document, procedure_document, another_document, logged_in_admin):
        """Test getting link count for a document."""
        service = LinkService(db)

        assert service.get_link_count(policy_document.doc_id) == 0

        service.create_link(
            parent_doc_id=policy_document.doc_id,
            child_doc_id=procedure_document.doc_id,
            link_type=LinkType.IMPLEMENTS.value,
        )

        assert service.get_link_count(policy_document.doc_id) == 1
        assert service.get_link_count(procedure_document.doc_id) == 1  # Also counts as child

    def test_get_available_documents_for_linking(
        self, db, policy_document, procedure_document, another_document, logged_in_admin
    ):
        """Test getting documents available for linking."""
        service = LinkService(db)

        # Initially all other docs are available
        available = service.get_available_documents_for_linking(policy_document.doc_id)
        doc_refs = [d["doc_ref"] for d in available]
        assert procedure_document.doc_ref in doc_refs
        assert another_document.doc_ref in doc_refs
        assert policy_document.doc_ref not in doc_refs

        # After linking, linked doc is excluded
        service.create_link(
            parent_doc_id=policy_document.doc_id,
            child_doc_id=procedure_document.doc_id,
            link_type=LinkType.IMPLEMENTS.value,
        )

        available = service.get_available_documents_for_linking(policy_document.doc_id)
        doc_refs = [d["doc_ref"] for d in available]
        assert procedure_document.doc_ref not in doc_refs
        assert another_document.doc_ref in doc_refs

    def test_get_available_documents_with_search(
        self, db, policy_document, procedure_document, another_document, logged_in_admin
    ):
        """Test searching available documents for linking."""
        service = LinkService(db)

        # Search by reference
        available = service.get_available_documents_for_linking(
            policy_document.doc_id,
            search_term="PROC",
        )
        assert len(available) == 1
        assert available[0]["doc_ref"] == procedure_document.doc_ref

        # Search by title
        available = service.get_available_documents_for_linking(
            policy_document.doc_id,
            search_term="Manual",
        )
        assert len(available) == 1
        assert available[0]["doc_ref"] == another_document.doc_ref

    def test_linked_document_info(self, db, policy_document, procedure_document, logged_in_admin):
        """Test that linked document includes correct info."""
        service = LinkService(db)

        service.create_link(
            parent_doc_id=policy_document.doc_id,
            child_doc_id=procedure_document.doc_id,
            link_type=LinkType.IMPLEMENTS.value,
        )

        links = service.get_links_for_document(policy_document.doc_id)
        assert len(links) == 1

        linked_doc = links[0]
        assert linked_doc.doc_ref == procedure_document.doc_ref
        assert linked_doc.title == procedure_document.title
        assert linked_doc.status == procedure_document.status
        assert linked_doc.is_parent is True  # policy is parent

    def test_document_relationship_text(self, db, policy_document, procedure_document, logged_in_admin):
        """Test relationship text from different perspectives."""
        service = LinkService(db)

        service.create_link(
            parent_doc_id=policy_document.doc_id,
            child_doc_id=procedure_document.doc_id,
            link_type=LinkType.IMPLEMENTS.value,
        )

        # From policy's perspective
        policy_links = service.get_links_for_document(policy_document.doc_id)
        assert policy_links[0].is_parent is True
        assert policy_links[0].link.get_relationship_text(True) == "Implemented by"

        # From procedure's perspective
        proc_links = service.get_links_for_document(procedure_document.doc_id)
        assert proc_links[0].is_parent is False
        assert proc_links[0].link.get_relationship_text(False) == "Implements"
