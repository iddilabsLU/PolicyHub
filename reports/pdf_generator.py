"""
PolicyHub PDF Generator

Generates PDF reports using ReportLab.
"""

import logging
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, LETTER, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from reports.base_report import BaseReportGenerator, ReportData

logger = logging.getLogger(__name__)


# Professional color palette
COLORS = {
    "primary": colors.HexColor("#1E3A8A"),      # Deep blue
    "secondary": colors.HexColor("#64748B"),    # Slate gray
    "header_bg": colors.HexColor("#1E3A8A"),    # Deep blue
    "header_fg": colors.white,
    "row_alt": colors.HexColor("#F8FAFC"),      # Light gray
    "border": colors.HexColor("#E2E8F0"),       # Border gray
    "text": colors.HexColor("#1E293B"),         # Dark text
    "muted": colors.HexColor("#64748B"),        # Muted text
}


class PDFGenerator(BaseReportGenerator):
    """
    Generates PDF reports using ReportLab.

    Creates professional documents with:
    - Header with title and generation date
    - Optional summary statistics
    - Data table with alternating row colors
    - Footer with page numbers
    """

    def __init__(self, report_data: ReportData):
        """
        Initialize the PDF generator.

        Args:
            report_data: Report configuration and data
        """
        super().__init__(report_data)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        """Set up custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name="ReportTitle",
            parent=self.styles["Heading1"],
            fontSize=18,
            textColor=COLORS["primary"],
            spaceAfter=6,
        ))

        self.styles.add(ParagraphStyle(
            name="ReportSubtitle",
            parent=self.styles["Normal"],
            fontSize=11,
            textColor=COLORS["muted"],
            spaceAfter=20,
        ))

        self.styles.add(ParagraphStyle(
            name="SummaryLabel",
            parent=self.styles["Normal"],
            fontSize=9,
            textColor=COLORS["muted"],
        ))

        self.styles.add(ParagraphStyle(
            name="SummaryValue",
            parent=self.styles["Normal"],
            fontSize=12,
            textColor=COLORS["text"],
            fontName="Helvetica-Bold",
        ))

        self.styles.add(ParagraphStyle(
            name="FilterText",
            parent=self.styles["Normal"],
            fontSize=9,
            textColor=COLORS["muted"],
            spaceAfter=12,
        ))

    def generate(self, output_path: str) -> str:
        """
        Generate the PDF report.

        Args:
            output_path: Path to save the PDF

        Returns:
            Path to the generated file
        """
        # Determine page size - always use landscape for better table display
        base_size = LETTER if self.data.config.page_size == "LETTER" else A4
        page_size = landscape(base_size)

        # Store page dimensions for width calculations
        self.page_width = page_size[0]
        self.page_height = page_size[1]

        doc = SimpleDocTemplate(
            output_path,
            pagesize=page_size,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        # Build content
        story = []

        # Title
        story.append(Paragraph(self.data.config.title, self.styles["ReportTitle"]))

        # Subtitle with generation info
        subtitle = self.data.config.subtitle or ""
        gen_info = f"Generated: {self.data.generated_at.strftime('%Y-%m-%d %H:%M')}"
        if subtitle:
            subtitle_text = f"{subtitle}<br/>{gen_info}"
        else:
            subtitle_text = gen_info
        story.append(Paragraph(subtitle_text, self.styles["ReportSubtitle"]))

        # Filters applied
        if self.data.filters_applied:
            filter_parts = [f"{k}: {v}" for k, v in self.data.filters_applied.items() if v]
            if filter_parts:
                filter_text = "Filters: " + " | ".join(filter_parts)
                story.append(Paragraph(filter_text, self.styles["FilterText"]))

        # Summary section
        if self.data.config.include_summary and self.data.summary:
            story.append(self._build_summary_section())
            story.append(Spacer(1, 12))

        # Data table
        if self.data.rows:
            story.append(self._build_data_table())
        else:
            story.append(Paragraph("No data to display.", self.styles["Normal"]))

        # Footer note
        if self.data.config.include_footer:
            story.append(Spacer(1, 20))
            footer_text = f"Total records: {self.data.row_count}"
            story.append(Paragraph(footer_text, self.styles["FilterText"]))

        # Build PDF
        doc.build(story)
        logger.info(f"PDF report generated: {output_path}")

        return output_path

    def _build_summary_section(self) -> Table:
        """
        Build the summary statistics section.

        Returns:
            Table with summary statistics
        """
        # Create summary cards in a row
        summary_data = []
        labels = []
        values = []

        for key, value in self.data.summary.items():
            labels.append(Paragraph(key, self.styles["SummaryLabel"]))
            values.append(Paragraph(str(value), self.styles["SummaryValue"]))

        if labels:
            summary_data = [labels, values]
            col_count = len(labels)
            # Use stored page width for landscape, fallback to A4 landscape width
            available_width = getattr(self, 'page_width', 297 * mm) - 30 * mm
            col_width = available_width / col_count

            table = Table(
                summary_data,
                colWidths=[col_width] * col_count,
            )

            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 1, COLORS["border"]),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLORS["border"]),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]))

            return table

        return Spacer(1, 0)

    def _build_data_table(self) -> Table:
        """
        Build the main data table.

        Returns:
            Table with document data
        """
        # Build header row
        headers = [col.header for col in self.data.columns]
        table_data = [headers]

        # Build data rows
        for row in self.data.rows:
            row_data = []
            for col in self.data.columns:
                value = row.get(col.key, "")
                formatted = self._format_value(value)
                # Wrap long text in Paragraph
                if len(formatted) > 30:
                    para = Paragraph(formatted, self.styles["Normal"])
                    row_data.append(para)
                else:
                    row_data.append(formatted)
            table_data.append(row_data)

        # Calculate column widths - use landscape page width
        available_width = getattr(self, 'page_width', 297 * mm) - 30 * mm  # Page width minus margins
        total_defined_width = sum(col.width for col in self.data.columns)
        scale = available_width / total_defined_width if total_defined_width > 0 else 1

        col_widths = [col.width * scale for col in self.data.columns]

        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Build table style
        style_commands = [
            # Header styling
            ("BACKGROUND", (0, 0), (-1, 0), COLORS["header_bg"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLORS["header_fg"]),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),

            # Body styling
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("TEXTCOLOR", (0, 1), (-1, -1), COLORS["text"]),

            # Borders and padding
            ("BOX", (0, 0), (-1, -1), 1, COLORS["border"]),
            ("LINEBELOW", (0, 0), (-1, 0), 1, COLORS["primary"]),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLORS["border"]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]

        # Add alternating row colors
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                style_commands.append(
                    ("BACKGROUND", (0, i), (-1, i), COLORS["row_alt"])
                )

        # Add column alignment
        for col_idx, col in enumerate(self.data.columns):
            if col.align == "center":
                style_commands.append(
                    ("ALIGN", (col_idx, 0), (col_idx, -1), "CENTER")
                )
            elif col.align == "right":
                style_commands.append(
                    ("ALIGN", (col_idx, 0), (col_idx, -1), "RIGHT")
                )

        table.setStyle(TableStyle(style_commands))
        return table
