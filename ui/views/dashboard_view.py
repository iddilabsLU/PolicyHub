"""
PolicyHub Dashboard View (PySide6)

Main dashboard showing document statistics and items requiring attention.
"""

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.constants import DocumentStatus, DocumentType, ReviewStatus
from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button, style_card
from models.document import Document
from services.document_service import DocumentService
from services.category_service import CategoryService
from ui.components.stat_card import StatCard
from ui.components.status_badge import StatusBadge
from ui.views.base_view import BaseView
from utils.dates import format_date, format_relative_date

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class DashboardView(BaseView):
    """
    Dashboard view with statistics and attention-required documents.

    Displays:
    - Document count statistics
    - Review status summary
    - Documents requiring attention (overdue/due soon)
    """

    def __init__(self, parent: Optional[QWidget], app: "PolicyHubApp"):
        """
        Initialize the dashboard view.

        Args:
            parent: Parent widget
            app: Main application instance
        """
        super().__init__(parent, app)
        self.doc_service = DocumentService(app.db)
        self.category_service = CategoryService(app.db)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dashboard UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(60)
        style_card(header)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.CARD_PADDING, 0, SPACING.CARD_PADDING, 0)

        title = QLabel("Dashboard")
        title.setFont(TYPOGRAPHY.window_title)
        title.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedSize(100, 32)
        refresh_btn.setFont(TYPOGRAPHY.small)
        refresh_btn.clicked.connect(self._refresh_data)
        style_button(refresh_btn, "secondary")
        header_layout.addWidget(refresh_btn)

        main_layout.addWidget(header)
        main_layout.addSpacing(SPACING.WINDOW_PADDING)

        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        # Scrollable content
        self.content = QWidget()
        self.content.setStyleSheet(f"background-color: {COLORS.BACKGROUND};")
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(
            SPACING.WINDOW_PADDING, 0,
            SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING
        )
        content_layout.setSpacing(0)

        # Build sections
        self._build_stats_section(content_layout)
        self._build_review_status_section(content_layout)
        self._build_attention_section(content_layout)

        content_layout.addStretch()

        scroll_area.setWidget(self.content)
        main_layout.addWidget(scroll_area)

    def _build_stats_section(self, parent_layout: QVBoxLayout) -> None:
        """Build the statistics cards section."""
        # Section title
        section_title = QLabel("Document Statistics")
        section_title.setFont(TYPOGRAPHY.section_heading)
        section_title.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        parent_layout.addWidget(section_title)
        parent_layout.addSpacing(SPACING.CARD_PADDING - 4)

        # Row 1: Total, Active, Under Review
        row1 = QWidget()
        row1_layout = QHBoxLayout(row1)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.setSpacing(10)

        self.total_card = StatCard(
            value="0",
            label="Total Documents",
            accent_color=COLORS.PRIMARY,
            on_click=lambda: self._on_stat_click("total"),
        )
        row1_layout.addWidget(self.total_card)

        self.active_card = StatCard(
            value="0",
            label="Active",
            accent_color=COLORS.SUCCESS,
            on_click=lambda: self._on_stat_click("active"),
        )
        row1_layout.addWidget(self.active_card)

        self.review_card = StatCard(
            value="0",
            label="Under Review",
            accent_color=COLORS.WARNING,
            on_click=lambda: self._on_stat_click("under_review"),
        )
        row1_layout.addWidget(self.review_card)

        parent_layout.addWidget(row1)
        parent_layout.addSpacing(8)

        # Row 2: By Type
        row2 = QWidget()
        row2_layout = QHBoxLayout(row2)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.setSpacing(10)

        self.policies_card = StatCard(
            value="0",
            label="Policies",
            accent_color=COLORS.ACCENT_POLICY,
            on_click=lambda: self._on_stat_click("policy"),
        )
        row2_layout.addWidget(self.policies_card)

        self.procedures_card = StatCard(
            value="0",
            label="Procedures",
            accent_color=COLORS.ACCENT_PROCEDURE,
            on_click=lambda: self._on_stat_click("procedure"),
        )
        row2_layout.addWidget(self.procedures_card)

        self.manuals_card = StatCard(
            value="0",
            label="Manuals",
            accent_color=COLORS.ACCENT_MANUAL,
            on_click=lambda: self._on_stat_click("manual"),
        )
        row2_layout.addWidget(self.manuals_card)

        self.hr_card = StatCard(
            value="0",
            label="HR",
            accent_color=COLORS.ACCENT_HR,
            on_click=lambda: self._on_stat_click("hr"),
        )
        row2_layout.addWidget(self.hr_card)

        self.others_card = StatCard(
            value="0",
            label="Others",
            accent_color=COLORS.ACCENT_OTHERS,
            on_click=lambda: self._on_stat_click("others"),
        )
        row2_layout.addWidget(self.others_card)

        parent_layout.addWidget(row2)
        parent_layout.addSpacing(24)

    def _build_review_status_section(self, parent_layout: QVBoxLayout) -> None:
        """Build the review status summary section."""
        # Section title
        section_title = QLabel("Review Status Overview")
        section_title.setFont(TYPOGRAPHY.section_heading)
        section_title.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        parent_layout.addWidget(section_title)
        parent_layout.addSpacing(SPACING.CARD_PADDING - 4)

        # Status cards container
        review_frame = QFrame()
        style_card(review_frame)
        review_layout = QHBoxLayout(review_frame)
        review_layout.setContentsMargins(24, 20, 24, 20)
        review_layout.setSpacing(24)

        # Overdue
        self.overdue_frame, self.overdue_count = self._create_review_status_item(
            "Overdue", "0", "danger",
            lambda: self._on_review_status_click("OVERDUE")
        )
        review_layout.addWidget(self.overdue_frame)

        # Due Soon
        self.due_soon_frame, self.due_soon_count = self._create_review_status_item(
            "Due Soon", "0", "warning",
            lambda: self._on_review_status_click("DUE_SOON")
        )
        review_layout.addWidget(self.due_soon_frame)

        # Upcoming
        self.upcoming_frame, self.upcoming_count = self._create_review_status_item(
            "Upcoming", "0", "caution",
            lambda: self._on_review_status_click("UPCOMING")
        )
        review_layout.addWidget(self.upcoming_frame)

        # On Track
        self.on_track_frame, self.on_track_count = self._create_review_status_item(
            "On Track", "0", "success",
            lambda: self._on_review_status_click("ON_TRACK")
        )
        review_layout.addWidget(self.on_track_frame)

        parent_layout.addWidget(review_frame)
        parent_layout.addSpacing(24)

    def _create_review_status_item(
        self,
        label: str,
        count: str,
        variant: str,
        on_click,
    ) -> tuple[QFrame, QLabel]:
        """Create a review status item with badge and count."""
        bg_colors = {
            "danger": COLORS.DANGER_BG,
            "warning": COLORS.WARNING_BG,
            "caution": COLORS.CAUTION_BG,
            "success": COLORS.SUCCESS_BG,
        }
        bg_color = bg_colors.get(variant, COLORS.MUTED)

        frame = ClickableFrame(on_click)
        frame.setStyleSheet(f"""
            ClickableFrame {{
                background-color: {bg_color};
                border-radius: {SPACING.CORNER_RADIUS_LARGE}px;
                border: none;
            }}
            ClickableFrame:hover {{
                background-color: {bg_color};
                opacity: 0.85;
            }}
        """)
        frame.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Count (large)
        count_label = QLabel(count)
        count_label.setFont(TYPOGRAPHY.get_font(32, TYPOGRAPHY.WEIGHT_BOLD))
        count_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(count_label)

        # Label
        label_widget = QLabel(label)
        label_widget.setFont(TYPOGRAPHY.get_font(12, TYPOGRAPHY.WEIGHT_REGULAR))
        label_widget.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_widget)

        return frame, count_label

    def _build_attention_section(self, parent_layout: QVBoxLayout) -> None:
        """Build the requires attention section."""
        # Section header
        header_frame = QWidget()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        # Title badge
        title_badge = QFrame()
        title_badge.setFixedHeight(32)
        title_badge.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.WARNING_BG};
                border-radius: 16px;
            }}
        """)
        badge_layout = QHBoxLayout(title_badge)
        badge_layout.setContentsMargins(12, 0, 12, 0)

        icon_label = QLabel("!")
        icon_label.setFont(TYPOGRAPHY.get_font(14, TYPOGRAPHY.WEIGHT_BOLD))
        icon_label.setStyleSheet(f"color: {COLORS.WARNING}; background: transparent;")
        badge_layout.addWidget(icon_label)

        section_title = QLabel("Requires Attention")
        section_title.setFont(TYPOGRAPHY.get_font(13, TYPOGRAPHY.WEIGHT_SEMIBOLD))
        section_title.setStyleSheet(f"color: {COLORS.WARNING}; background: transparent;")
        badge_layout.addWidget(section_title)

        header_layout.addWidget(title_badge)

        # Item count
        self.attention_count_label = QLabel("")
        self.attention_count_label.setFont(TYPOGRAPHY.small)
        self.attention_count_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        header_layout.addWidget(self.attention_count_label)

        header_layout.addStretch()

        parent_layout.addWidget(header_frame)
        parent_layout.addSpacing(12)

        # Attention list container
        self.attention_frame = QFrame()
        style_card(self.attention_frame)
        self.attention_layout = QVBoxLayout(self.attention_frame)
        self.attention_layout.setContentsMargins(
            SPACING.WINDOW_PADDING, SPACING.CARD_PADDING,
            SPACING.WINDOW_PADDING, SPACING.CARD_PADDING
        )
        self.attention_layout.setSpacing(0)

        parent_layout.addWidget(self.attention_frame)

    def _update_attention_list(self, documents: list) -> None:
        """Update the attention required list."""
        # Clear existing items
        while self.attention_layout.count():
            item = self.attention_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Update count
        if documents:
            self.attention_count_label.setText(f"({len(documents)} items)")
        else:
            self.attention_count_label.setText("")

        if not documents:
            # Empty state
            empty_frame = QWidget()
            empty_layout = QVBoxLayout(empty_frame)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.setContentsMargins(0, 40, 0, 40)

            empty_icon = QLabel("✓")
            empty_icon.setFont(TYPOGRAPHY.get_font(32, TYPOGRAPHY.WEIGHT_BOLD))
            empty_icon.setStyleSheet(f"color: {COLORS.SUCCESS};")
            empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_icon)

            empty_label = QLabel("All documents are up to date!")
            empty_label.setFont(TYPOGRAPHY.body)
            empty_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_label)

            self.attention_layout.addWidget(empty_frame)
            return

        # Header row
        header_row = QFrame()
        header_row.setFixedHeight(36)
        header_row.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.MUTED};
                border-radius: {SPACING.CORNER_RADIUS_SMALL}px;
            }}
        """)
        header_grid = QGridLayout(header_row)
        header_grid.setContentsMargins(16, 0, 16, 0)

        headers = ["Reference", "Title", "Next Review", "Status"]
        col_stretches = [1, 3, 1, 1]
        for col, (text, stretch) in enumerate(zip(headers, col_stretches)):
            lbl = QLabel(text)
            lbl.setFont(TYPOGRAPHY.table_header)
            lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
            header_grid.addWidget(lbl, 0, col)
            header_grid.setColumnStretch(col, stretch)

        self.attention_layout.addWidget(header_row)
        self.attention_layout.addSpacing(8)

        # Document rows
        for doc in documents[:10]:
            row = self._create_attention_row(doc)
            self.attention_layout.addWidget(row)
            self.attention_layout.addSpacing(2)

    def _create_attention_row(self, doc: Document) -> QWidget:
        """Create a document row for the attention list."""
        row = ClickableFrame(lambda d=doc: self._on_document_click(d))
        row.setFixedHeight(40)
        row.setStyleSheet(f"""
            ClickableFrame {{
                background-color: transparent;
                border-radius: {SPACING.CORNER_RADIUS_SMALL}px;
            }}
            ClickableFrame:hover {{
                background-color: {COLORS.MUTED};
            }}
        """)
        row.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        grid = QGridLayout(row)
        grid.setContentsMargins(16, 0, 16, 0)

        # Reference
        ref_label = QLabel(doc.doc_ref)
        ref_label.setFont(TYPOGRAPHY.body)
        ref_label.setStyleSheet(f"color: {COLORS.PRIMARY}; background: transparent;")
        grid.addWidget(ref_label, 0, 0)
        grid.setColumnStretch(0, 1)

        # Title
        title_label = QLabel(doc.title)
        title_label.setFont(TYPOGRAPHY.body)
        title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        title_label.setWordWrap(True)
        grid.addWidget(title_label, 0, 1)
        grid.setColumnStretch(1, 3)

        # Next Review
        date_label = QLabel(format_relative_date(doc.next_review_date))
        date_label.setFont(TYPOGRAPHY.body)
        date_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        grid.addWidget(date_label, 0, 2)
        grid.setColumnStretch(2, 1)

        # Status badge
        badge = StatusBadge.from_review_status(row, doc.review_status)
        grid.addWidget(badge, 0, 3)
        grid.setColumnStretch(3, 1)

        return row

    def _refresh_data(self) -> None:
        """Refresh all dashboard data."""
        # Get statistics
        total = self.doc_service.get_total_document_count()
        by_status = self.doc_service.get_document_counts_by_status()
        by_type = self.doc_service.get_document_counts_by_type()
        review_counts = self.doc_service.get_review_status_counts()
        attention_docs = self.doc_service.get_documents_requiring_attention(10)

        # Update stat cards
        self.total_card.set_value(str(total))
        self.active_card.set_value(str(by_status.get(DocumentStatus.ACTIVE.value, 0)))
        self.review_card.set_value(str(by_status.get(DocumentStatus.UNDER_REVIEW.value, 0)))

        self.policies_card.set_value(str(by_type.get(DocumentType.POLICY.value, 0)))
        self.procedures_card.set_value(str(by_type.get(DocumentType.PROCEDURE.value, 0)))
        self.manuals_card.set_value(str(by_type.get(DocumentType.MANUAL.value, 0)))
        self.hr_card.set_value(str(by_type.get(DocumentType.HR.value, 0)))
        self.others_card.set_value(str(by_type.get(DocumentType.OTHERS.value, 0)))

        # Update review status counts
        self.overdue_count.setText(str(review_counts.get(ReviewStatus.OVERDUE.value, 0)))
        self.due_soon_count.setText(str(review_counts.get(ReviewStatus.DUE_SOON.value, 0)))
        self.upcoming_count.setText(str(review_counts.get(ReviewStatus.UPCOMING.value, 0)))
        self.on_track_count.setText(str(review_counts.get(ReviewStatus.ON_TRACK.value, 0)))

        # Update attention list
        self._update_attention_list(attention_docs)

    def _on_stat_click(self, stat_type: str) -> None:
        """Handle stat card click - navigate to filtered register."""
        main_view = self.app.current_view
        if hasattr(main_view, "_switch_content_view"):
            main_view._switch_content_view("register", filter_type=stat_type)

    def _on_review_status_click(self, status: str) -> None:
        """Handle review status click - navigate to filtered register."""
        main_view = self.app.current_view
        if hasattr(main_view, "_switch_content_view"):
            main_view._switch_content_view("register", review_status=status)

    def _on_document_click(self, document: Document) -> None:
        """Handle document row click - navigate to detail view."""
        main_view = self.app.current_view
        if hasattr(main_view, "_show_document_detail"):
            main_view._show_document_detail(document)

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        self._refresh_data()


class ClickableFrame(QFrame):
    """A QFrame that handles click events."""

    def __init__(self, on_click=None, parent=None):
        super().__init__(parent)
        self._on_click = on_click

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._on_click:
            self._on_click()
        super().mousePressEvent(event)
