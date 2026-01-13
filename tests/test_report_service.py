"""
Tests for ReportService.

Tests report generation functionality.
"""

import os
import tempfile

import pytest

from models.document import DocumentCreate
from services.document_service import DocumentService
from services.report_service import ReportFilters, ReportService


class TestReportService:
    """Tests for ReportService."""

    @pytest.fixture
    def report_service(self, db):
        """Create a ReportService instance."""
        return ReportService(db)

    @pytest.fixture
    def sample_documents(self, db, logged_in_admin, sample_document_data):
        """Create sample documents for testing."""
        doc_service = DocumentService(db)

        docs = []
        # Create a few test documents
        for i, status in enumerate(["ACTIVE", "ACTIVE", "DRAFT"]):
            data = DocumentCreate(
                doc_type="POLICY",
                doc_ref=f"POL-TEST-{i+1:03d}",
                title=f"Test Policy {i+1}",
                category="AML",
                owner="Test Owner",
                status=status,
                version="1.0",
                effective_date="2024-01-15",
                last_review_date="2024-01-15",
                next_review_date="2025-01-15",
                review_frequency="ANNUAL",
            )
            doc = doc_service.create_document(data)
            docs.append(doc)

        return docs

    def test_get_report_types(self, report_service):
        """Test getting available report types."""
        types = report_service.get_report_types()

        assert len(types) == 3
        ids = [t["id"] for t in types]
        assert "full_register" in ids
        assert "review_schedule" in ids
        assert "compliance_status" in ids

    def test_generate_pdf_report(self, report_service, sample_documents, logged_in_admin):
        """Test generating a PDF report."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = report_service.generate_report(
                report_type="full_register",
                output_format="pdf",
                output_dir=temp_dir,
            )

            assert output_path is not None
            assert os.path.exists(output_path)
            assert output_path.endswith(".pdf")

    def test_generate_excel_report(self, report_service, sample_documents, logged_in_admin):
        """Test generating an Excel report."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = report_service.generate_report(
                report_type="full_register",
                output_format="excel",
                output_dir=temp_dir,
            )

            assert output_path is not None
            assert os.path.exists(output_path)
            assert output_path.endswith(".xlsx")

    def test_generate_review_schedule_report(self, report_service, sample_documents, logged_in_admin):
        """Test generating a review schedule report."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = report_service.generate_report(
                report_type="review_schedule",
                output_format="pdf",
                output_dir=temp_dir,
            )

            assert output_path is not None
            assert os.path.exists(output_path)

    def test_generate_compliance_status_report(self, report_service, sample_documents, logged_in_admin):
        """Test generating a compliance status report."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = report_service.generate_report(
                report_type="compliance_status",
                output_format="excel",
                output_dir=temp_dir,
            )

            assert output_path is not None
            assert os.path.exists(output_path)

    def test_generate_report_with_filters(self, report_service, sample_documents, logged_in_admin):
        """Test generating a report with filters applied."""
        filters = ReportFilters(status="ACTIVE")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = report_service.generate_report(
                report_type="full_register",
                output_format="pdf",
                output_dir=temp_dir,
                filters=filters,
            )

            assert output_path is not None
            assert os.path.exists(output_path)

    def test_generate_report_invalid_type_raises(self, report_service, logged_in_admin):
        """Test that invalid report type raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError, match="Unknown report type"):
                report_service.generate_report(
                    report_type="invalid_type",
                    output_format="pdf",
                    output_dir=temp_dir,
                )

    def test_generate_report_invalid_format_raises(self, report_service, logged_in_admin):
        """Test that invalid format raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError, match="Unknown format"):
                report_service.generate_report(
                    report_type="full_register",
                    output_format="invalid",
                    output_dir=temp_dir,
                )

    def test_report_filters_dataclass(self):
        """Test ReportFilters dataclass."""
        filters = ReportFilters(
            status="ACTIVE",
            doc_type="POLICY",
            category="AML",
            review_status="OVERDUE",
        )

        assert filters.status == "ACTIVE"
        assert filters.doc_type == "POLICY"
        assert filters.category == "AML"
        assert filters.review_status == "OVERDUE"

    def test_empty_report_generation(self, report_service, logged_in_admin):
        """Test generating a report with no documents."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Should not raise, just generate empty report
            output_path = report_service.generate_report(
                report_type="full_register",
                output_format="pdf",
                output_dir=temp_dir,
            )

            assert output_path is not None
            assert os.path.exists(output_path)
