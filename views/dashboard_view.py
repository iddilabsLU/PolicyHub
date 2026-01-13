"""
PolicyHub Dashboard View

Main dashboard showing document statistics and items requiring attention.
"""

from typing import TYPE_CHECKING

import customtkinter as ctk

from app.constants import DocumentStatus, DocumentType, ReviewStatus
from app.theme import COLORS, SPACING, TYPOGRAPHY, configure_button_style, configure_card_style
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
        configure_card_style(header, with_shadow=True)

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
            font=TYPOGRAPHY.section_heading,
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
            accent_color=COLORS.ACCENT_POLICY,
            on_click=lambda: self._on_stat_click("policy"),
        )
        self.policies_card.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.procedures_card = StatCard(
            row2,
            value="0",
            label="Procedures",
            accent_color=COLORS.ACCENT_PROCEDURE,
            on_click=lambda: self._on_stat_click("procedure"),
        )
        self.procedures_card.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.manuals_card = StatCard(
            row2,
            value="0",
            label="Manuals",
            accent_color=COLORS.ACCENT_MANUAL,
            on_click=lambda: self._on_stat_click("manual"),
        )
        self.manuals_card.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.hr_others_card = StatCard(
            row2,
            value="0",
            label="HR Others",
            accent_color=COLORS.ACCENT_HR_OTHERS,
            on_click=lambda: self._on_stat_click("hr_others"),
        )
        self.hr_others_card.pack(side="left", fill="x", expand=True)

    def _build_review_status_section(self) -> None:
        """Build the review status summary section."""
        # Section title
        section_title = ctk.CTkLabel(
            self.content,
            text="Review Status Overview",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        section_title.pack(anchor="w", pady=(10, 12))

        # Status cards row - using grid for equal distribution
        self.review_status_frame = ctk.CTkFrame(
            self.content,
            fg_color=COLORS.CARD,
            corner_radius=SPACING.CORNER_RADIUS_LARGE,
        )
        self.review_status_frame.pack(fill="x", pady=(0, 20))
        configure_card_style(self.review_status_frame, with_shadow=True)

        # Inner container with grid layout
        inner = ctk.CTkFrame(self.review_status_frame, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=20)

        # Configure equal columns
        for i in range(4):
            inner.grid_columnconfigure(i, weight=1)

        # Overdue
        self.overdue_frame = self._create_review_status_item(
            inner, "Overdue", "0", "danger",
            lambda: self._on_review_status_click("OVERDUE")
        )
        self.overdue_frame.grid(row=0, column=0, sticky="nsew", padx=8)

        # Due Soon
        self.due_soon_frame = self._create_review_status_item(
            inner, "Due Soon", "0", "warning",
            lambda: self._on_review_status_click("DUE_SOON")
        )
        self.due_soon_frame.grid(row=0, column=1, sticky="nsew", padx=8)

        # Upcoming
        self.upcoming_frame = self._create_review_status_item(
            inner, "Upcoming", "0", "caution",
            lambda: self._on_review_status_click("UPCOMING")
        )
        self.upcoming_frame.grid(row=0, column=2, sticky="nsew", padx=8)

        # On Track
        self.on_track_frame = self._create_review_status_item(
            inner, "On Track", "0", "success",
            lambda: self._on_review_status_click("ON_TRACK")
        )
        self.on_track_frame.grid(row=0, column=3, sticky="nsew", padx=8)

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
        # Section header with icon
        header_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 12))

        # Alert icon (using unicode warning symbol)
        icon_label = ctk.CTkLabel(
            header_frame,
            text="⚠",
            font=TYPOGRAPHY.get_font(16, "bold"),
            text_color=COLORS.WARNING,
        )
        icon_label.pack(side="left", padx=(0, 8))

        section_title = ctk.CTkLabel(
            header_frame,
            text="Requires Attention",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        section_title.pack(side="left")

        # Item count badge
        self.attention_count_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        )
        self.attention_count_label.pack(side="left", padx=(10, 0))

        # Attention list container with enhanced styling
        self.attention_frame = ctk.CTkFrame(
            self.content,
            fg_color=COLORS.CARD,
            corner_radius=SPACING.CORNER_RADIUS_LARGE,
        )
        self.attention_frame.pack(fill="both", expand=True, pady=(0, 20))
        configure_card_style(self.attention_frame, with_shadow=True)

        # Inner container for the list
        self.attention_list = ctk.CTkFrame(self.attention_frame, fg_color="transparent")
        self.attention_list.pack(fill="both", expand=True, padx=20, pady=16)

    def _update_attention_list(self, documents) -> None:
        """Update the attention required list."""
        # Clear existing items
        for widget in self.attention_list.winfo_children():
            widget.destroy()

        # Update count badge
        if hasattr(self, 'attention_count_label'):
            if documents:
                self.attention_count_label.configure(text=f"({len(documents)} items)")
            else:
                self.attention_count_label.configure(text="")

        if not documents:
            # Empty state with icon
            empty_frame = ctk.CTkFrame(self.attention_list, fg_color="transparent")
            empty_frame.pack(expand=True, pady=40)

            empty_icon = ctk.CTkLabel(
                empty_frame,
                text="✓",
                font=TYPOGRAPHY.get_font(32, "bold"),
                text_color=COLORS.SUCCESS,
            )
            empty_icon.pack()

            empty_label = ctk.CTkLabel(
                empty_frame,
                text="All documents are up to date!",
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_SECONDARY,
            )
            empty_label.pack(pady=(8, 0))
            return

        # Use grid layout for better column control
        # Configure column weights for proportional sizing
        self.attention_list.grid_columnconfigure(0, weight=1, minsize=120)   # Reference
        self.attention_list.grid_columnconfigure(1, weight=3, minsize=200)   # Title (stretches most)
        self.attention_list.grid_columnconfigure(2, weight=1, minsize=120)   # Next Review
        self.attention_list.grid_columnconfigure(3, weight=1, minsize=100)   # Status

        # Create header row
        header_frame = ctk.CTkFrame(
            self.attention_list,
            fg_color=COLORS.MUTED,
            corner_radius=SPACING.CORNER_RADIUS_SMALL,
            height=40,
        )
        header_frame.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 4))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=3)
        header_frame.grid_columnconfigure(2, weight=1)
        header_frame.grid_columnconfigure(3, weight=1)

        headers = ["Reference", "Title", "Next Review", "Status"]
        for col, text in enumerate(headers):
            ctk.CTkLabel(
                header_frame,
                text=text,
                font=TYPOGRAPHY.table_header,
                text_color=COLORS.TEXT_PRIMARY,
                anchor="w",
            ).grid(row=0, column=col, sticky="w", padx=16, pady=10)

        # Create document rows with hover effect
        for i, doc in enumerate(documents[:10]):  # Limit to 10 items
            row_num = i + 1

            # Row container for hover effect
            row_frame = ctk.CTkFrame(
                self.attention_list,
                fg_color="transparent",
                cursor="hand2",
                corner_radius=SPACING.CORNER_RADIUS_SMALL,
                height=44,
            )
            row_frame.grid(row=row_num, column=0, columnspan=4, sticky="ew", pady=1)
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=3)
            row_frame.grid_columnconfigure(2, weight=1)
            row_frame.grid_columnconfigure(3, weight=1)

            # Bind hover and click to row
            row_frame.bind("<Button-1>", lambda e, d=doc: self._on_document_click(d))
            row_frame.bind("<Enter>", lambda e, r=row_frame: r.configure(fg_color=COLORS.MUTED))
            row_frame.bind("<Leave>", lambda e, r=row_frame: r.configure(fg_color="transparent"))

            # Reference - clickable link style
            ref_label = ctk.CTkLabel(
                row_frame,
                text=doc.doc_ref,
                font=TYPOGRAPHY.body,
                text_color=COLORS.PRIMARY,
                anchor="w",
                cursor="hand2",
            )
            ref_label.grid(row=0, column=0, sticky="w", padx=16, pady=12)
            ref_label.bind("<Button-1>", lambda e, d=doc: self._on_document_click(d))
            ref_label.bind("<Enter>", lambda e, r=row_frame: r.configure(fg_color=COLORS.MUTED))
            ref_label.bind("<Leave>", lambda e, r=row_frame: r.configure(fg_color="transparent"))

            # Title - truncate with ellipsis if needed
            title_text = doc.title if len(doc.title) <= 60 else doc.title[:57] + "..."
            title_label = ctk.CTkLabel(
                row_frame,
                text=title_text,
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_PRIMARY,
                anchor="w",
                cursor="hand2",
            )
            title_label.grid(row=0, column=1, sticky="w", padx=16, pady=12)
            title_label.bind("<Button-1>", lambda e, d=doc: self._on_document_click(d))
            title_label.bind("<Enter>", lambda e, r=row_frame: r.configure(fg_color=COLORS.MUTED))
            title_label.bind("<Leave>", lambda e, r=row_frame: r.configure(fg_color="transparent"))

            # Next Review date
            date_label = ctk.CTkLabel(
                row_frame,
                text=format_relative_date(doc.next_review_date),
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_SECONDARY,
                anchor="w",
                cursor="hand2",
            )
            date_label.grid(row=0, column=2, sticky="w", padx=16, pady=12)
            date_label.bind("<Button-1>", lambda e, d=doc: self._on_document_click(d))
            date_label.bind("<Enter>", lambda e, r=row_frame: r.configure(fg_color=COLORS.MUTED))
            date_label.bind("<Leave>", lambda e, r=row_frame: r.configure(fg_color="transparent"))

            # Status badge
            badge = StatusBadge.from_review_status(row_frame, doc.review_status)
            badge.grid(row=0, column=3, sticky="w", padx=16, pady=12)
            badge.bind("<Button-1>", lambda e, d=doc: self._on_document_click(d))

            # Divider (except for last item)
            if i < min(len(documents), 10) - 1:
                divider = ctk.CTkFrame(self.attention_list, fg_color=COLORS.BORDER, height=1)
                divider.grid(row=row_num, column=0, columnspan=4, sticky="ew", padx=12, pady=0)

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
        self.hr_others_card.set_value(str(by_type.get(DocumentType.HR_OTHERS.value, 0)))

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
