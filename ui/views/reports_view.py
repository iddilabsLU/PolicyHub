"""
PolicyHub Reports View (PySide6)

View for generating document reports in PDF and Excel formats.
"""

import os
import subprocess
import tempfile
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QRadioButton,
    QButtonGroup,
    QComboBox,
    QProgressBar,
)

from app.constants import DocumentStatus, DocumentType, ReviewStatus
from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button, style_card
from ui.components.section_card import SectionCard
from ui.components.toast import Toast
from ui.dialogs.confirm_dialog import InfoDialog
from ui.views.base_view import BaseView
from services.category_service import CategoryService
from services.entity_service import EntityService
from services.report_service import ReportFilters, ReportService

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class ReportTypeCard(QFrame):
    """A selectable card for report type selection."""

    def __init__(
        self,
        parent,
        icon: str,
        title: str,
        description: str,
        report_type: str,
        on_select,
    ):
        super().__init__(parent)
        self._report_type = report_type
        self._selected = False
        self._on_select = on_select

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(260, 110)
        self._build_ui(icon, title, description)
        self._update_style()

    def _build_ui(self, icon: str, title: str, description: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px; background: transparent;")
        layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_label.setFont(TYPOGRAPHY.section_heading)
        title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(description)
        desc_label.setFont(TYPOGRAPHY.small)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(desc_label)

        layout.addStretch()

    def _update_style(self) -> None:
        if self._selected:
            self.setStyleSheet(f"""
                ReportTypeCard {{
                    background-color: {COLORS.FILTER_ACTIVE_BG};
                    border: 2px solid {COLORS.PRIMARY};
                    border-radius: {SPACING.CORNER_RADIUS_LARGE}px;
                }}
                ReportTypeCard QLabel {{
                    background: transparent;
                    border: none;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                ReportTypeCard {{
                    background-color: {COLORS.CARD};
                    border: none;
                    border-radius: {SPACING.CORNER_RADIUS_LARGE}px;
                }}
                ReportTypeCard:hover {{
                    background-color: {COLORS.MUTED};
                }}
                ReportTypeCard QLabel {{
                    background: transparent;
                    border: none;
                }}
            """)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._update_style()

    def is_selected(self) -> bool:
        return self._selected

    @property
    def report_type(self) -> str:
        return self._report_type

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_select(self)
        super().mousePressEvent(event)


class ReportsView(BaseView):
    """
    Reports generation view.

    Allows users to:
    - Select report type
    - Apply filters
    - Choose output format (PDF/Excel)
    - Generate and open reports
    """

    def __init__(self, parent: QWidget, app: "PolicyHubApp"):
        """
        Initialize the reports view.

        Args:
            parent: Parent widget
            app: Main application instance
        """
        super().__init__(parent, app)
        self.report_service = ReportService(app.db)
        self.category_service = CategoryService(app.db)
        self.entity_service = EntityService(app.db)
        self._categories = {}
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the reports view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
        )
        layout.setSpacing(16)

        # Header
        header = QFrame()
        header.setFixedHeight(60)
        style_card(header, with_shadow=True)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
        )

        title = QLabel("Reports")
        title.setFont(TYPOGRAPHY.window_title)
        title.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(header)

        # Report Type Section - Card-based selection
        type_section = SectionCard(self, "Report Type", "Select the type of report to generate")

        # Report type cards container
        cards_container = QFrame()
        cards_container.setStyleSheet("background: transparent; border: none;")
        cards_layout = QHBoxLayout(cards_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(16)

        self._report_cards = []
        report_types = [
            ("full_register", "📋", "Document Register", "Complete list of all documents"),
            ("review_schedule", "📅", "Review Schedule", "Upcoming and overdue reviews"),
            ("compliance_status", "✅", "Compliance Status", "Overview with status"),
        ]

        for type_id, icon, type_name, description in report_types:
            card = ReportTypeCard(
                self,
                icon=icon,
                title=type_name,
                description=description,
                report_type=type_id,
                on_select=self._on_report_type_select,
            )
            if type_id == "full_register":
                card.set_selected(True)
            self._report_cards.append(card)
            cards_layout.addWidget(card)

        cards_layout.addStretch()
        type_section.add_content(cards_container)
        layout.addWidget(type_section)

        # Filters Section
        filter_section = SectionCard(self, "Filters", "Optionally filter the report data")

        # Filter header with clear button
        filter_header = QFrame()
        filter_header.setStyleSheet("background: transparent; border: none;")
        filter_header_layout = QHBoxLayout(filter_header)
        filter_header_layout.setContentsMargins(0, 0, 0, 0)

        filter_header_layout.addStretch()

        self.clear_filters_btn = QPushButton("Clear Filters")
        self.clear_filters_btn.setFixedHeight(28)
        self.clear_filters_btn.setFont(TYPOGRAPHY.small)
        style_button(self.clear_filters_btn, "flat")
        self.clear_filters_btn.clicked.connect(self._clear_filters)
        self.clear_filters_btn.hide()  # Hidden until filters are active
        filter_header_layout.addWidget(self.clear_filters_btn)

        filter_section.add_content(filter_header)

        # Filter dropdowns grid - row 1
        filters_row1 = QFrame()
        filters_row1.setStyleSheet("background: transparent; border: none;")
        filters_row1_layout = QHBoxLayout(filters_row1)
        filters_row1_layout.setContentsMargins(0, 0, 0, 0)
        filters_row1_layout.setSpacing(20)

        # Status filter
        status_frame = self._create_filter_dropdown(
            "Status",
            ["All"] + [s.display_name for s in DocumentStatus],
            150,
        )
        self.status_dropdown = status_frame.findChild(QComboBox)
        self.status_dropdown.currentIndexChanged.connect(self._on_filter_changed)
        filters_row1_layout.addWidget(status_frame)

        # Type filter
        type_frame = self._create_filter_dropdown(
            "Document Type",
            ["All"] + [t.display_name for t in DocumentType],
            150,
        )
        self.doc_type_dropdown = type_frame.findChild(QComboBox)
        self.doc_type_dropdown.currentIndexChanged.connect(self._on_filter_changed)
        filters_row1_layout.addWidget(type_frame)

        # Category filter
        cat_frame = self._create_filter_dropdown("Category", ["All"], 180)
        self.category_dropdown = cat_frame.findChild(QComboBox)
        self.category_dropdown.currentIndexChanged.connect(self._on_filter_changed)
        filters_row1_layout.addWidget(cat_frame)

        # Review status filter
        review_frame = self._create_filter_dropdown(
            "Review Status",
            ["All"] + [r.display_name for r in ReviewStatus],
            150,
        )
        self.review_dropdown = review_frame.findChild(QComboBox)
        self.review_dropdown.currentIndexChanged.connect(self._on_filter_changed)
        filters_row1_layout.addWidget(review_frame)

        filters_row1_layout.addStretch()
        filter_section.add_content(filters_row1)

        # Filter dropdowns grid - row 2
        filters_row2 = QFrame()
        filters_row2.setStyleSheet("background: transparent; border: none;")
        filters_row2_layout = QHBoxLayout(filters_row2)
        filters_row2_layout.setContentsMargins(0, 0, 0, 0)
        filters_row2_layout.setSpacing(20)

        # Mandatory read filter
        mandatory_frame = self._create_filter_dropdown(
            "Mandatory Read",
            ["All", "Yes", "No"],
            120,
        )
        self.mandatory_dropdown = mandatory_frame.findChild(QComboBox)
        self.mandatory_dropdown.currentIndexChanged.connect(self._on_filter_changed)
        filters_row2_layout.addWidget(mandatory_frame)

        # Entity filter
        entity_frame = self._create_filter_dropdown("Applicable Entity", ["All"], 180)
        self.entity_dropdown = entity_frame.findChild(QComboBox)
        self.entity_dropdown.currentIndexChanged.connect(self._on_filter_changed)
        filters_row2_layout.addWidget(entity_frame)

        filters_row2_layout.addStretch()
        filter_section.add_content(filters_row2)

        layout.addWidget(filter_section)

        # Output Format & Generate Section
        output_section = SectionCard(self, "Output Format", "Choose the file format for your report")

        # Toggle buttons for format selection
        format_row = QFrame()
        format_row.setStyleSheet("background: transparent; border: none;")
        format_layout = QHBoxLayout(format_row)
        format_layout.setContentsMargins(0, 0, 0, 0)
        format_layout.setSpacing(0)

        self.pdf_btn = QPushButton("📄 PDF")
        self.pdf_btn.setFixedSize(100, 36)
        self.pdf_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pdf_btn.setProperty("format", "pdf")
        self.pdf_btn.clicked.connect(lambda: self._on_format_select("pdf"))
        format_layout.addWidget(self.pdf_btn)

        self.excel_btn = QPushButton("📊 Excel")
        self.excel_btn.setFixedSize(100, 36)
        self.excel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.excel_btn.setProperty("format", "excel")
        self.excel_btn.clicked.connect(lambda: self._on_format_select("excel"))
        format_layout.addWidget(self.excel_btn)

        format_layout.addStretch()
        output_section.add_content(format_row)

        # Set initial format selection
        self._selected_format = "pdf"
        self._update_format_buttons()

        output_section.add_spacing(16)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS.MUTED};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS.PRIMARY};
                border-radius: 3px;
            }}
        """)
        self.progress_bar.hide()
        output_section.add_content(self.progress_bar)

        # Generate button row
        btn_row = QFrame()
        btn_row.setStyleSheet("background: transparent; border: none;")
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        self.generate_btn = QPushButton("Generate Report")
        self.generate_btn.setFixedSize(180, 40)
        style_button(self.generate_btn, "primary")
        self.generate_btn.clicked.connect(self._on_generate)
        btn_layout.addWidget(self.generate_btn)

        btn_layout.addStretch()
        output_section.add_content(btn_row)

        layout.addWidget(output_section)
        layout.addStretch()

    def _on_report_type_select(self, selected_card: ReportTypeCard) -> None:
        """Handle report type card selection."""
        for card in self._report_cards:
            card.set_selected(card is selected_card)

    def _on_format_select(self, format_type: str) -> None:
        """Handle output format selection."""
        self._selected_format = format_type
        self._update_format_buttons()

    def _update_format_buttons(self) -> None:
        """Update the styling of format toggle buttons."""
        for btn, fmt in [(self.pdf_btn, "pdf"), (self.excel_btn, "excel")]:
            if fmt == self._selected_format:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS.PRIMARY};
                        color: {COLORS.PRIMARY_FOREGROUND};
                        border: 1px solid {COLORS.PRIMARY};
                        border-radius: 6px;
                        font-weight: 500;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS.PRIMARY_HOVER};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS.CARD};
                        color: {COLORS.TEXT_SECONDARY};
                        border: 1px solid {COLORS.BORDER};
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS.MUTED};
                        color: {COLORS.TEXT_PRIMARY};
                    }}
                """)

    def _on_filter_changed(self) -> None:
        """Handle filter dropdown change."""
        has_filters = self._has_active_filters()
        self.clear_filters_btn.setVisible(has_filters)

    def _has_active_filters(self) -> bool:
        """Check if any filters are active."""
        return (
            self.status_dropdown.currentIndex() != 0
            or self.doc_type_dropdown.currentIndex() != 0
            or self.category_dropdown.currentIndex() != 0
            or self.review_dropdown.currentIndex() != 0
            or self.mandatory_dropdown.currentIndex() != 0
            or self.entity_dropdown.currentIndex() != 0
        )

    def _clear_filters(self) -> None:
        """Clear all filter selections."""
        self.status_dropdown.setCurrentIndex(0)
        self.doc_type_dropdown.setCurrentIndex(0)
        self.category_dropdown.setCurrentIndex(0)
        self.review_dropdown.setCurrentIndex(0)
        self.mandatory_dropdown.setCurrentIndex(0)
        self.entity_dropdown.setCurrentIndex(0)
        self.clear_filters_btn.hide()

    def _create_filter_dropdown(
        self, label_text: str, values: list, width: int
    ) -> QFrame:
        """Create a filter dropdown with label."""
        frame = QFrame()
        frame.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel(label_text)
        label.setFont(TYPOGRAPHY.small)
        label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(label)

        dropdown = QComboBox()
        dropdown.addItems(values)
        dropdown.setFixedWidth(width)
        dropdown.setFont(TYPOGRAPHY.body)
        dropdown.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS.CARD};
                border: 1px solid {COLORS.BORDER};
                border-radius: 4px;
                padding: 6px 12px;
                color: {COLORS.TEXT_PRIMARY};
            }}
            QComboBox:hover {{
                border-color: {COLORS.PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS.CARD};
                border: 1px solid {COLORS.BORDER};
                selection-background-color: {COLORS.PRIMARY};
                selection-color: {COLORS.PRIMARY_FOREGROUND};
            }}
        """)
        layout.addWidget(dropdown)

        return frame

    def _load_categories(self) -> None:
        """Load categories for the dropdown."""
        try:
            categories = self.category_service.get_active_categories()
            values = ["All"] + [f"{cat.code} - {cat.name}" for cat in categories]
            self.category_dropdown.clear()
            self.category_dropdown.addItems(values)
            self._categories = {f"{cat.code} - {cat.name}": cat.code for cat in categories}
        except Exception:
            self._categories = {}

    def _load_entities(self) -> None:
        """Load entities for the dropdown."""
        try:
            entities = self.entity_service.get_entity_names()
            values = ["All"] + entities
            self.entity_dropdown.clear()
            self.entity_dropdown.addItems(values)
        except Exception:
            pass

    def _get_filters(self) -> ReportFilters:
        """Get the current filter values."""
        filters = ReportFilters()

        # Status
        status_display = self.status_dropdown.currentText()
        if status_display != "All":
            for s in DocumentStatus:
                if s.display_name == status_display:
                    filters.status = s.value
                    break

        # Document type
        type_display = self.doc_type_dropdown.currentText()
        if type_display != "All":
            for t in DocumentType:
                if t.display_name == type_display:
                    filters.doc_type = t.value
                    break

        # Category
        cat_display = self.category_dropdown.currentText()
        if cat_display != "All" and self._categories:
            filters.category = self._categories.get(cat_display)

        # Review status
        review_display = self.review_dropdown.currentText()
        if review_display != "All":
            for r in ReviewStatus:
                if r.display_name == review_display:
                    filters.review_status = r.value
                    break

        # Mandatory read
        mandatory_display = self.mandatory_dropdown.currentText()
        if mandatory_display == "Yes":
            filters.mandatory_read_all = True
        elif mandatory_display == "No":
            filters.mandatory_read_all = False

        # Applicable entity
        entity_display = self.entity_dropdown.currentText()
        if entity_display != "All":
            filters.applicable_entity = entity_display

        return filters

    def _on_generate(self) -> None:
        """Handle generate report button click."""
        self.generate_btn.setEnabled(False)
        self.progress_bar.show()

        # Force UI update
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            # Get report type from selected card
            report_type = "full_register"
            for card in self._report_cards:
                if card.is_selected():
                    report_type = card.report_type
                    break

            output_format = self._selected_format
            filters = self._get_filters()

            # Generate to temp directory
            output_dir = tempfile.gettempdir()

            # Generate report
            output_path = self.report_service.generate_report(
                report_type=report_type,
                output_format=output_format,
                output_dir=output_dir,
                filters=filters,
            )

            # Show success toast
            Toast.show_success(self, "Report generated successfully!")

            # Open the file
            self._open_file(output_path)

        except Exception as e:
            Toast.show_error(self, f"Failed to generate report: {str(e)}")

        finally:
            self.generate_btn.setEnabled(True)
            self.progress_bar.hide()

    def _open_file(self, file_path: str) -> None:
        """
        Open a file with the default application.

        Args:
            file_path: Path to the file to open
        """
        try:
            # Windows
            os.startfile(file_path)
        except AttributeError:
            # macOS / Linux
            try:
                subprocess.run(["open", file_path], check=True)
            except FileNotFoundError:
                subprocess.run(["xdg-open", file_path], check=True)
        except Exception:
            InfoDialog.show_info(
                self.window(),
                "Report Generated",
                f"Report saved to:\n{file_path}",
            )

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        self._load_categories()
        self._load_entities()
        self._on_filter_changed()  # Update clear button visibility
