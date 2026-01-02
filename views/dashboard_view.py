"""
PolicyHub Dashboard View

Main dashboard showing document statistics and items requiring attention.
"""

from typing import TYPE_CHECKING

import customtkinter as ctk

from app.constants import DocumentStatus, DocumentType, ReviewStatus
from app.theme import COLORS, SPACING, TYPOGRAPHY, configure_button_style
from components.stat_card import StatCard
from components.status_badge import StatusBadge
from core.database import DatabaseManager
from services.document_service import DocumentService
from services.category_service import CategoryService
from utils.dates import format_date, format_relative_date
from views.base_view import BaseView

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

    def __init__(self, parent: ctk.CTkFrame, app: "PolicyHubApp"):
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
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS.CARD, height=60)
        header.pack(fill="x", padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING)
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="Dashboard",
            font=TYPOGRAPHY.window_title,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title.pack(side="left", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        # Refresh button
        refresh_btn = ctk.CTkButton(
            header,
            text="↻ Refresh",
            command=self._refresh_data,
            width=100,
            height=32,
            font=TYPOGRAPHY.small,
        )
        configure_button_style(refresh_btn, "secondary")
        refresh_btn.pack(side="right", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        # Scrollable content
        self.content = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS.BACKGROUND,
        )
        self.content.pack(fill="both", expand=True, padx=SPACING.WINDOW_PADDING, pady=(0, SPACING.WINDOW_PADDING))

        # Build sections
        self._build_stats_section()
        self._build_review_status_section()
        self._build_attention_section()

    def _build_stats_section(self) -> None:
        """Build the statistics cards section."""
        # Section title
        section_title = ctk.CTkLabel(
            self.content,
            text="Document Statistics",
            font=TYPOGRAPHY.section_title,
            text_color=COLORS.TEXT_PRIMARY,
        )
        section_title.pack(anchor="w", pady=(0, 10))

        # Stats container
        self.stats_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(0, 20))

        # Row 1: Total, Active, Under Review
        row1 = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))

        self.total_card = StatCard(
            row1,
            value="0",
            label="Total Documents",
            accent_color=COLORS.PRIMARY,
            on_click=lambda: self._on_stat_click("total"),
        )
        self.total_card.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.active_card = StatCard(
            row1,
            value="0",
            label="Active",
            accent_color=COLORS.SUCCESS,
            on_click=lambda: self._on_stat_click("active"),
        )
        self.active_card.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.review_card = StatCard(
            row1,
            value="0",
            label="Under Review",
            accent_color=COLORS.WARNING,
            on_click=lambda: self._on_stat_click("under_review"),
        )
        self.review_card.pack(side="left", fill="x", expand=True)

        # Row 2: By Type
        row2 = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        row2.pack(fill="x")

        self.policies_card = StatCard(
            row2,
            value="0",
            label="Policies",
            accent_color="#6366F1",  # Indigo
            on_click=lambda: self._on_stat_click("policy"),
        )
        self.policies_card.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.procedures_card = StatCard(
            row2,
            value="0",
            label="Procedures",
            accent_color="#8B5CF6",  # Purple
            on_click=lambda: self._on_stat_click("procedure"),
        )
        self.procedures_card.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.manuals_card = StatCard(
            row2,
            value="0",
            label="Manuals",
            accent_color="#EC4899",  # Pink
            on_click=lambda: self._on_stat_click("manual"),
        )
        self.manuals_card.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.registers_card = StatCard(
            row2,
            value="0",
            label="Registers",
            accent_color="#14B8A6",  # Teal
            on_click=lambda: self._on_stat_click("register"),
        )
        self.registers_card.pack(side="left", fill="x", expand=True)

    def _build_review_status_section(self) -> None:
        """Build the review status summary section."""
        # Section title
        section_title = ctk.CTkLabel(
            self.content,
            text="Review Status Overview",
            font=TYPOGRAPHY.section_title,
            text_color=COLORS.TEXT_PRIMARY,
        )
        section_title.pack(anchor="w", pady=(10, 10))

        # Status cards row
        self.review_status_frame = ctk.CTkFrame(
            self.content,
            fg_color=COLORS.CARD,
            corner_radius=SPACING.CORNER_RADIUS_LARGE,
        )
        self.review_status_frame.pack(fill="x", pady=(0, 20))

        inner = ctk.CTkFrame(self.review_status_frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)

        # Overdue
        self.overdue_frame = self._create_review_status_item(
            inner, "Overdue", "0", "danger",
            lambda: self._on_review_status_click("OVERDUE")
        )
        self.overdue_frame.pack(side="left", fill="x", expand=True)

        # Separator
        sep1 = ctk.CTkFrame(inner, fg_color=COLORS.BORDER, width=1)
        sep1.pack(side="left", fill="y", padx=15)

        # Due Soon
        self.due_soon_frame = self._create_review_status_item(
            inner, "Due Soon", "0", "warning",
            lambda: self._on_review_status_click("DUE_SOON")
        )
        self.due_soon_frame.pack(side="left", fill="x", expand=True)

        # Separator
        sep2 = ctk.CTkFrame(inner, fg_color=COLORS.BORDER, width=1)
        sep2.pack(side="left", fill="y", padx=15)

        # Upcoming
        self.upcoming_frame = self._create_review_status_item(
            inner, "Upcoming", "0", "caution",
            lambda: self._on_review_status_click("UPCOMING")
        )
        self.upcoming_frame.pack(side="left", fill="x", expand=True)

        # Separator
        sep3 = ctk.CTkFrame(inner, fg_color=COLORS.BORDER, width=1)
        sep3.pack(side="left", fill="y", padx=15)

        # On Track
        self.on_track_frame = self._create_review_status_item(
            inner, "On Track", "0", "success",
            lambda: self._on_review_status_click("ON_TRACK")
        )
        self.on_track_frame.pack(side="left", fill="x", expand=True)

    def _create_review_status_item(
        self,
        parent,
        label: str,
        count: str,
        variant: str,
        on_click,
    ) -> ctk.CTkFrame:
        """Create a review status item with badge and count."""
        frame = ctk.CTkFrame(parent, fg_color="transparent", cursor="hand2")
        frame.bind("<Button-1>", lambda e: on_click())

        # Count (large)
        count_label = ctk.CTkLabel(
            frame,
            text=count,
            font=TYPOGRAPHY.get_font(24, "bold"),
            text_color=COLORS.TEXT_PRIMARY,
        )
        count_label.pack()
        count_label.bind("<Button-1>", lambda e: on_click())

        # Store reference to update later
        frame.count_label = count_label

        # Badge
        badge = StatusBadge(frame, text=label, variant=variant)
        badge.pack(pady=(5, 0))
        badge.bind("<Button-1>", lambda e: on_click())

        return frame

    def _build_attention_section(self) -> None:
        """Build the requires attention section."""
        # Section header
        header_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 10))

        section_title = ctk.CTkLabel(
            header_frame,
            text="Requires Attention",
            font=TYPOGRAPHY.section_title,
            text_color=COLORS.TEXT_PRIMARY,
        )
        section_title.pack(side="left")

        # Attention list container
        self.attention_frame = ctk.CTkFrame(
            self.content,
            fg_color=COLORS.CARD,
            corner_radius=SPACING.CORNER_RADIUS_LARGE,
        )
        self.attention_frame.pack(fill="x", pady=(0, 20))

        # Placeholder
        self.attention_list = ctk.CTkFrame(self.attention_frame, fg_color="transparent")
        self.attention_list.pack(fill="x", padx=10, pady=10)

    def _update_attention_list(self, documents) -> None:
        """Update the attention required list."""
        # Clear existing items
        for widget in self.attention_list.winfo_children():
            widget.destroy()

        if not documents:
            empty_label = ctk.CTkLabel(
                self.attention_list,
                text="No documents require attention at this time.",
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_SECONDARY,
            )
            empty_label.pack(pady=20)
            return

        # Create header row
        header = ctk.CTkFrame(self.attention_list, fg_color=COLORS.MUTED)
        header.pack(fill="x", pady=(0, 5))

        headers = [("Reference", 100), ("Title", 300), ("Next Review", 120), ("Status", 100)]
        for text, width in headers:
            ctk.CTkLabel(
                header,
                text=text,
                font=TYPOGRAPHY.get_font(12, "bold"),
                text_color=COLORS.TEXT_PRIMARY,
                width=width,
                anchor="w",
            ).pack(side="left", padx=10, pady=8)

        # Create document rows
        for doc in documents[:10]:  # Limit to 10 items
            row = ctk.CTkFrame(
                self.attention_list,
                fg_color="transparent",
                cursor="hand2",
            )
            row.pack(fill="x")
            row.bind("<Button-1>", lambda e, d=doc: self._on_document_click(d))

            # Reference
            ref_label = ctk.CTkLabel(
                row,
                text=doc.doc_ref,
                font=TYPOGRAPHY.body,
                text_color=COLORS.PRIMARY,
                width=100,
                anchor="w",
            )
            ref_label.pack(side="left", padx=10, pady=8)
            ref_label.bind("<Button-1>", lambda e, d=doc: self._on_document_click(d))

            # Title
            title_label = ctk.CTkLabel(
                row,
                text=doc.title[:50] + "..." if len(doc.title) > 50 else doc.title,
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_PRIMARY,
                width=300,
                anchor="w",
            )
            title_label.pack(side="left", padx=10, pady=8)
            title_label.bind("<Button-1>", lambda e, d=doc: self._on_document_click(d))

            # Next Review
            date_label = ctk.CTkLabel(
                row,
                text=format_relative_date(doc.next_review_date),
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_SECONDARY,
                width=120,
                anchor="w",
            )
            date_label.pack(side="left", padx=10, pady=8)
            date_label.bind("<Button-1>", lambda e, d=doc: self._on_document_click(d))

            # Status badge
            badge = StatusBadge.from_review_status(row, doc.review_status)
            badge.pack(side="left", padx=10, pady=8)
            badge.bind("<Button-1>", lambda e, d=doc: self._on_document_click(d))

            # Divider
            divider = ctk.CTkFrame(self.attention_list, fg_color=COLORS.BORDER, height=1)
            divider.pack(fill="x")

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
        self.registers_card.set_value(str(by_type.get(DocumentType.REGISTER.value, 0)))

        # Update review status counts
        self.overdue_frame.count_label.configure(
            text=str(review_counts.get(ReviewStatus.OVERDUE.value, 0))
        )
        self.due_soon_frame.count_label.configure(
            text=str(review_counts.get(ReviewStatus.DUE_SOON.value, 0))
        )
        self.upcoming_frame.count_label.configure(
            text=str(review_counts.get(ReviewStatus.UPCOMING.value, 0))
        )
        self.on_track_frame.count_label.configure(
            text=str(review_counts.get(ReviewStatus.ON_TRACK.value, 0))
        )

        # Update attention list
        self._update_attention_list(attention_docs)

    def _on_stat_click(self, stat_type: str) -> None:
        """Handle stat card click - navigate to filtered register."""
        # Navigate to register with filter
        main_view = self.app.current_view
        if hasattr(main_view, "_switch_content_view"):
            main_view._switch_content_view("register", filter_type=stat_type)

    def _on_review_status_click(self, status: str) -> None:
        """Handle review status click - navigate to filtered register."""
        main_view = self.app.current_view
        if hasattr(main_view, "_switch_content_view"):
            main_view._switch_content_view("register", review_status=status)

    def _on_document_click(self, document) -> None:
        """Handle document row click - navigate to detail view."""
        main_view = self.app.current_view
        if hasattr(main_view, "_show_document_detail"):
            main_view._show_document_detail(document)

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        self._refresh_data()
