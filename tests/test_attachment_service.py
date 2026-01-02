"""
Tests for AttachmentService.
"""

import os
import tempfile
from pathlib import Path

import pytest

from app.constants import SHARED_ATTACHMENTS_FOLDER, UserRole
from core.config import ConfigManager
from core.database import DatabaseManager
from core.session import SessionManager
from models.document import DocumentCreate
from services.attachment_service import AttachmentService
from services.auth_service import AuthService
from services.document_service import DocumentService


@pytest.fixture
def temp_shared_folder(temp_dir):
    """Create a temporary shared folder structure with attachments."""
    # Create folder structure
    (temp_dir / "data").mkdir(exist_ok=True)
    (temp_dir / SHARED_ATTACHMENTS_FOLDER).mkdir(exist_ok=True)

    # Configure the app to use this folder
    ConfigManager._instance = None
    ConfigManager._config = None
    config_mgr = ConfigManager.get_instance()
    config_mgr.update(shared_folder_path=str(temp_dir))

    yield temp_dir

    # Cleanup
    ConfigManager._instance = None
    ConfigManager._config = None


@pytest.fixture
def sample_document(db, logged_in_admin):
    """Create a sample document for testing."""
    doc_service = DocumentService(db)
    doc_data = DocumentCreate(
        doc_type="POLICY",
        doc_ref="POL-TEST-001",
        title="Test Policy for Attachments",
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
def sample_file(temp_dir):
    """Create a sample file for upload testing."""
    file_path = temp_dir / "test_document.pdf"
    file_path.write_text("This is a test PDF file content")
    return file_path


class TestAttachmentService:
    """Tests for AttachmentService."""

    def test_get_attachments_for_document_empty(self, db, sample_document, logged_in_admin):
        """Test getting attachments when none exist."""
        service = AttachmentService(db)
        attachments = service.get_attachments_for_document(sample_document.doc_id)
        assert attachments == []

    def test_add_attachment(self, db, sample_document, sample_file, logged_in_admin, temp_shared_folder):
        """Test adding an attachment to a document."""
        service = AttachmentService(db)

        attachment = service.add_attachment(
            doc_id=sample_document.doc_id,
            doc_ref=sample_document.doc_ref,
            source_path=sample_file,
            version_label="1.0",
        )

        assert attachment.doc_id == sample_document.doc_id
        assert attachment.filename == "test_document.pdf"
        assert attachment.version_label == "1.0"
        assert attachment.is_current is True

    def test_add_attachment_marks_previous_not_current(
        self, db, sample_document, sample_file, logged_in_admin, temp_shared_folder
    ):
        """Test that adding a new attachment marks previous as not current."""
        service = AttachmentService(db)

        # Add first attachment
        first = service.add_attachment(
            doc_id=sample_document.doc_id,
            doc_ref=sample_document.doc_ref,
            source_path=sample_file,
            version_label="1.0",
        )
        assert first.is_current is True

        # Add second attachment
        second = service.add_attachment(
            doc_id=sample_document.doc_id,
            doc_ref=sample_document.doc_ref,
            source_path=sample_file,
            version_label="1.1",
        )
        assert second.is_current is True

        # Check first is no longer current
        first_updated = service.get_attachment_by_id(first.attachment_id)
        assert first_updated.is_current is False

    def test_get_current_attachment(self, db, sample_document, sample_file, logged_in_admin, temp_shared_folder):
        """Test getting the current attachment."""
        service = AttachmentService(db)

        # Add attachments
        service.add_attachment(
            doc_id=sample_document.doc_id,
            doc_ref=sample_document.doc_ref,
            source_path=sample_file,
            version_label="1.0",
        )
        latest = service.add_attachment(
            doc_id=sample_document.doc_id,
            doc_ref=sample_document.doc_ref,
            source_path=sample_file,
            version_label="1.1",
        )

        current = service.get_current_attachment(sample_document.doc_id)
        assert current.attachment_id == latest.attachment_id

    def test_delete_attachment(self, db, sample_document, sample_file, logged_in_admin, temp_shared_folder):
        """Test deleting an attachment."""
        service = AttachmentService(db)

        attachment = service.add_attachment(
            doc_id=sample_document.doc_id,
            doc_ref=sample_document.doc_ref,
            source_path=sample_file,
            version_label="1.0",
        )

        result = service.delete_attachment(attachment.attachment_id)
        assert result is True

        # Verify deleted
        deleted = service.get_attachment_by_id(attachment.attachment_id)
        assert deleted is None

    def test_get_attachment_count(self, db, sample_document, sample_file, logged_in_admin, temp_shared_folder):
        """Test getting attachment count."""
        service = AttachmentService(db)

        assert service.get_attachment_count(sample_document.doc_id) == 0

        service.add_attachment(
            doc_id=sample_document.doc_id,
            doc_ref=sample_document.doc_ref,
            source_path=sample_file,
            version_label="1.0",
        )

        assert service.get_attachment_count(sample_document.doc_id) == 1

    def test_validate_file_invalid_extension(self, db):
        """Test file validation with invalid extension."""
        service = AttachmentService(db)

        is_valid, error = service.validate_file("test.exe", 1000)
        assert is_valid is False
        assert "not allowed" in error.lower()

    def test_validate_file_too_large(self, db):
        """Test file validation with file too large."""
        from app.constants import MAX_FILE_SIZE_BYTES

        service = AttachmentService(db)

        is_valid, error = service.validate_file("test.pdf", MAX_FILE_SIZE_BYTES + 1)
        assert is_valid is False
        assert "exceeds" in error.lower()

    def test_validate_file_valid(self, db):
        """Test file validation with valid file."""
        service = AttachmentService(db)

        is_valid, error = service.validate_file("test.pdf", 1000)
        assert is_valid is True
        assert error == ""

    def test_add_attachment_file_not_found(self, db, sample_document, logged_in_admin, temp_shared_folder):
        """Test adding attachment with non-existent file."""
        service = AttachmentService(db)

        with pytest.raises(FileNotFoundError):
            service.add_attachment(
                doc_id=sample_document.doc_id,
                doc_ref=sample_document.doc_ref,
                source_path=Path("/nonexistent/file.pdf"),
                version_label="1.0",
            )
