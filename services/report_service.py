"""
PolicyHub Report Service

Coordinates report generation for documents.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from app.constants import DocumentStatus, DocumentType, ReviewStatus
from core.database import DatabaseManager
from core.session import SessionManager
from models.document import Document
from reports.base_report import ReportColumn, ReportConfig, ReportData
from reports.excel_generator import ExcelGenerator
from reports.pdf_generator import PDFGenerator
from services.category_service import CategoryService
from services.document_service import DocumentService
from services.settings_service import SettingsService

logger = logging.getLogger(__name__)


@dataclass
class ReportFilters:
    """Filters for report generation."""

    status: Optional[str] = None
    doc_type: Optional[str] = None
    category: Optional[str] = None
    review_status: Optional[str] = None
    mandatory_read_all: Optional[bool] = None
    applicable_entity: Optional[str] = None


class ReportService:
    """
    Service for generating document reports.

    Supports PDF and Excel formats with customizable filters.
    """

    # Report type configurations
    REPORT_TYPES = {
        "full_register": {
            "title": "Document Register",
            "subtitle": "Complete Policy & Procedure Register",
            "columns": [
                ReportColumn("doc_ref", "Reference", 80, "left"),
                ReportColumn("title", "Title", 150, "left"),
                ReportColumn("doc_type", "Type", 70, "center"),
                ReportColumn("category", "Category", 70, "center"),
                ReportColumn("status", "Status", 60, "center"),
                ReportColumn("version", "Ver", 40, "center"),
                ReportColumn("owner", "Owner", 100, "left"),
                ReportColumn("next_review_date", "Next Review", 80, "center"),
            ],
        },
        "review_schedule": {
            "title": "Review Schedule",
            "subtitle": "Upcoming and Overdue Reviews",
            "columns": [
                ReportColumn("doc_ref", "Reference", 80, "left"),
                ReportColumn("title", "Title", 180, "left"),
                ReportColumn("owner", "Owner", 100, "left"),
                ReportColumn("last_review_date", "Last Review", 80, "center"),
                ReportColumn("next_review_date", "Next Review", 80, "center"),
                ReportColumn("review_status", "Status", 70, "center"),
            ],
        },
        "compliance_status": {
            "title": "Compliance Status Report",
            "subtitle": "Policy Compliance Overview",
            "columns": [
                ReportColumn("doc_ref", "Reference", 80, "left"),
                ReportColumn("title", "Title", 180, "left"),
                ReportColumn("category", "Category", 70, "center"),
                ReportColumn("status", "Status", 60, "center"),
                ReportColumn("review_status", "Review Status", 80, "center"),
                ReportColumn("effective_date", "Effective", 80, "center"),
            ],
        },
    }

    def __init__(self, db: DatabaseManager):
        """
        Initialize the report service.

        Args:
            db: Database manager instance
        """
        self.db = db
        self.document_service = DocumentService(db)
        self.category_service = CategoryService(db)
        self.settings_service = SettingsService(db)

    def get_report_types(self) -> List[Dict[str, str]]:
        """
        Get available report types.

        Returns:
            List of report type dictionaries with id and title
        """
        return [
            {"id": "full_register", "title": "Document Register"},
            {"id": "review_schedule", "title": "Review Schedule"},
            {"id": "compliance_status", "title": "Compliance Status Report"},
        ]

    def generate_report(
        self,
        report_type: str,
        output_format: str,
        output_dir: str,
        filters: Optional[ReportFilters] = None,
    ) -> str:
        """
        Generate a report.

        Args:
            report_type: Type of report (full_register, review_schedule, etc.)
            output_format: Format (pdf or excel)
            output_dir: Directory to save the report
            filters: Optional filters to apply

        Returns:
            Path to the generated report

        Raises:
            ValueError: If report type or format is invalid
        """
        if report_type not in self.REPORT_TYPES:
            raise ValueError(f"Unknown report type: {report_type}")

        if output_format not in ("pdf", "excel"):
            raise ValueError(f"Unknown format: {output_format}")

        # Get report configuration
        config = self.REPORT_TYPES[report_type]

        # Fetch and prepare data
        report_data = self._prepare_report_data(report_type, config, filters)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = "pdf" if output_format == "pdf" else "xlsx"
        filename = f"{report_type}_{timestamp}.{ext}"
        output_path = os.path.join(output_dir, filename)

        # Generate report
        if output_format == "pdf":
            generator = PDFGenerator(report_data)
        else:
            generator = ExcelGenerator(report_data)

        result_path = generator.generate(output_path)

        # Log generation
        session = SessionManager.get_instance()
        logger.info(
            f"Report generated: {report_type} ({output_format}) by {session.username}"
        )

        return result_path

    def _prepare_report_data(
        self,
        report_type: str,
        config: Dict,
        filters: Optional[ReportFilters],
    ) -> ReportData:
        """
        Prepare report data from documents.

        Args:
            report_type: Type of report
            config: Report configuration
            filters: Optional filters

        Returns:
            ReportData object
        """
        # Fetch documents with filters
        documents = self.document_service.get_all_documents(
            status=filters.status if filters else None,
            doc_type=filters.doc_type if filters else None,
            category=filters.category if filters else None,
            review_status=filters.review_status if filters else None,
            mandatory_read_all=filters.mandatory_read_all if filters else None,
            applicable_entity=filters.applicable_entity if filters else None,
        )

        # For review schedule, filter to relevant review statuses
        if report_type == "review_schedule":
            documents = [
                doc for doc in documents
                if doc.review_status in (ReviewStatus.OVERDUE, ReviewStatus.DUE_SOON, ReviewStatus.UPCOMING)
            ]
            # Sort by next review date
            documents.sort(key=lambda d: d.next_review_date or "9999-99-99")

        # Get category names for display
        categories = {cat.code: cat.name for cat in self.category_service.get_all_categories(include_inactive=True)}

        # Convert documents to row data
        rows = []
        for doc in documents:
            row = {
                "doc_ref": doc.doc_ref,
                "title": doc.title,
                "doc_type": doc.type_display,
                "category": categories.get(doc.category, doc.category),
                "status": doc.status_display,
                "version": doc.version,
                "owner": doc.owner,
                "approver": doc.approver or "",
                "effective_date": self._format_date(doc.effective_date),
                "last_review_date": self._format_date(doc.last_review_date),
                "next_review_date": self._format_date(doc.next_review_date),
                "review_status": doc.review_status_display,
                "review_frequency": doc.frequency_display,
            }
            rows.append(row)

        # Build summary statistics
        summary = self._build_summary(documents, report_type)

        # Build filters applied display
        filters_applied = {}
        if filters:
            if filters.status:
                try:
                    filters_applied["Status"] = DocumentStatus(filters.status).display_name
                except ValueError:
                    filters_applied["Status"] = filters.status
            if filters.doc_type:
                try:
                    filters_applied["Type"] = DocumentType(filters.doc_type).display_name
                except ValueError:
                    filters_applied["Type"] = filters.doc_type
            if filters.category:
                filters_applied["Category"] = categories.get(filters.category, filters.category)
            if filters.review_status:
                try:
                    filters_applied["Review Status"] = ReviewStatus(filters.review_status).display_name
                except ValueError:
                    filters_applied["Review Status"] = filters.review_status

        # Get company name from settings
        company_name = self.settings_service.get_company_name()
        subtitle = config["subtitle"]
        if company_name and company_name != "Your Company Name":
            subtitle = f"{company_name} - {subtitle}"

        return ReportData(
            config=ReportConfig(
                title=config["title"],
                subtitle=subtitle,
                generated_by="PolicyHub",
            ),
            columns=config["columns"],
            rows=rows,
            summary=summary,
            filters_applied=filters_applied,
        )

    def _build_summary(self, documents: List[Document], report_type: str) -> Dict[str, any]:
        """
        Build summary statistics for the report.

        Args:
            documents: List of documents
            report_type: Type of report

        Returns:
            Dictionary of summary statistics
        """
        summary = {"Total Documents": len(documents)}

        if report_type == "full_register":
            # Count by status
            active = sum(1 for d in documents if d.status == DocumentStatus.ACTIVE.value)
            draft = sum(1 for d in documents if d.status == DocumentStatus.DRAFT.value)
            summary["Active"] = active
            summary["Draft"] = draft

        elif report_type == "review_schedule":
            # Count by review status
            overdue = sum(1 for d in documents if d.review_status == ReviewStatus.OVERDUE)
            due_soon = sum(1 for d in documents if d.review_status == ReviewStatus.DUE_SOON)
            upcoming = sum(1 for d in documents if d.review_status == ReviewStatus.UPCOMING)
            summary["Overdue"] = overdue
            summary["Due Soon"] = due_soon
            summary["Upcoming"] = upcoming

        elif report_type == "compliance_status":
            # Count active and overdue
            active = sum(1 for d in documents if d.status == DocumentStatus.ACTIVE.value)
            overdue = sum(1 for d in documents if d.review_status == ReviewStatus.OVERDUE)
            compliance_rate = round((active - overdue) / active * 100) if active > 0 else 100
            summary["Active"] = active
            summary["Overdue"] = overdue
            summary["Compliance Rate"] = f"{compliance_rate}%"

        return summary

    def _format_date(self, date_str: Optional[str]) -> str:
        """
        Format a date string for display.

        Args:
            date_str: ISO date string or None

        Returns:
            Formatted date string
        """
        if not date_str:
            return ""

        try:
            # Parse ISO date
            if "T" in date_str:
                date_str = date_str.split("T")[0]

            date_obj = datetime.strptime(date_str, "%Y-%m-%d")

            # Get format from settings
            format_setting = self.settings_service.get_date_format()

            format_map = {
                "DD/MM/YYYY": "%d/%m/%Y",
                "MM/DD/YYYY": "%m/%d/%Y",
                "YYYY-MM-DD": "%Y-%m-%d",
            }

            date_format = format_map.get(format_setting, "%Y-%m-%d")
            return date_obj.strftime(date_format)

        except (ValueError, TypeError):
            return date_str or ""
