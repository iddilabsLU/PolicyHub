"""
PolicyHub Register View

Document register showing all documents in a filterable, sortable table.
"""

from typing import TYPE_CHECKING, List, Optional

import customtkinter as ctk

from app.constants import DEFAULT_PAGE_SIZE, DocumentStatus, DocumentType, ReviewStatus
from app.theme import COLORS, SPACING, TYPOGRAPHY, configure_button_style, configure_card_style
from components.filter_bar import FilterBar
from core.database import DatabaseManager
from core.permissions import PermissionChecker
from dialogs.document_dialog import DocumentDialog
from models.document import Document
from services.category_service import CategoryService
from services.document_service import DocumentService
from services.entity_service import EntityService
from utils.dates import format_date
from views.base_view import BaseView

if TYPE_CHECKING:
    from app.application import PolicyHubApp

# Try to import tksheet, fall back to simple list if not available
try:
    from tksheet import Sheet
    TKSHEET_AVAILABLE = True
except ImportError:
    TKSHEET_AVAILABLE = False


class RegisterView(BaseView):
    """
    Document register view with filtering and sorting.

    Features:
    - Full document table with tksheet
    - Filter bar for type, category, status, review status
    - Search functionality
    - Sorting by column headers
    - Double-click to view details
    - Add new document button (if permitted)
    """

    def __init__(
        self,
        parent: ctk.CTkFrame,
        app: "PolicyHubApp",
        initial_filter: Optional[dict] = None,
    ):
        """
        Initialize the register view.

        Args:
            parent: Parent widget
            app: Main application instance
            initial_filter: Optional initial filter to apply
        """
        super().__init__(parent, app)
        self.doc_service = DocumentService(app.db)
        self.category_service = CategoryService(app.db)
        self.entity_service = EntityService(app.db)
        self.permissions = PermissionChecker()
        self.documents: List[Document] = []
        self.initial_filter = initial_filter or {}
        self._sort_column = "doc_ref"
        self._sort_direction = "ASC"

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the register UI."""
        # Header with subtle shadow - includes title, search, and add button
        header = ctk.CTkFrame(self, fg_color=COLORS.CARD, height=60)
        configure_card_style(header, with_shadow=True)
        header.pack(fill="x", padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING)
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="Document Register",
            font=TYPOGRAPHY.window_title,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title.pack(side="left", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        # Add button (if can edit) - on the right
        if self.permissions.can_edit():
            add_btn = ctk.CTkButton(
                header,
                text="+ Add Document",
                command=self._on_add,
                width=130,
                height=36,
            )
            configure_button_style(add_btn, "primary")
            add_btn.pack(side="right", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        # Search and Clear buttons in header (center-right area)
        search_frame = ctk.CTkFrame(header, fg_color="transparent")
        search_frame.pack(side="right", padx=(0, 16), pady=SPACING.CARD_PADDING)

        # Clear button
        self.clear_btn = ctk.CTkButton(
            search_frame,
            text="Clear",
            command=self._on_clear_filters,
            width=70,
            height=36,
        )
        configure_button_style(self.clear_btn, "secondary")
        self.clear_btn.pack(side="right", padx=(8, 0))

        # Search entry
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search title, reference...",
            textvariable=self.search_var,
            width=220,
            height=36,
            font=TYPOGRAPHY.body,
        )
        self.search_entry.pack(side="right")
        self.search_entry.bind("<Return>", lambda e: self._on_filter_change())
        self.search_entry.bind("<KeyRelease>", self._on_search_key)
        self._search_after_id = None

        # Filter bar (without search - we moved it to header)
        categories = self.category_service.get_active_categories()
        entities = self.entity_service.get_entity_names()
        self.filter_bar = FilterBar(
            self,
            categories=categories,
            on_filter_change=self._on_filter_change,
            entities=entities,
            show_search=False,  # Search is now in header
        )
        self.filter_bar.pack(fill="x", padx=SPACING.WINDOW_PADDING, pady=(0, 10))

        # Apply initial filter if provided
        if self.initial_filter:
            for key, value in self.initial_filter.items():
                if value:
                    self.filter_bar.set_filter(key, value)

        # Table container with card styling
        self.table_container = ctk.CTkFrame(self, fg_color=COLORS.CARD)
        configure_card_style(self.table_container, with_shadow=True)
        self.table_container.pack(
            fill="both",
            expand=True,
            padx=SPACING.WINDOW_PADDING,
            pady=(0, SPACING.WINDOW_PADDING),
        )

        # Build table
        if TKSHEET_AVAILABLE:
            self._build_tksheet_table()
        else:
            self._build_fallback_table()

        # Status bar
        self.status_bar = ctk.CTkFrame(self.table_container, fg_color="transparent", height=30)
        self.status_bar.pack(fill="x", side="bottom", padx=10, pady=5)

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Loading...",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        )
        self.status_label.pack(side="left")

    def _build_tksheet_table(self) -> None:
        """Build the tksheet table with professional styling."""
        self.table = Sheet(
            self.table_container,
            headers=["Ref", "Title", "Type", "Category", "Owner", "Status", "Review", "Next Review"],
            # Header styling - light professional look
            header_bg=COLORS.MUTED,
            header_fg=COLORS.TEXT_PRIMARY,
            header_font=("Segoe UI", 11, "bold"),
            header_grid_fg=COLORS.BORDER,
            header_border_fg=COLORS.BORDER,
            header_selected_cells_bg=COLORS.SECONDARY,
            header_selected_cells_fg=COLORS.TEXT_PRIMARY,
            # Table body styling
            table_bg=COLORS.CARD,
            table_fg=COLORS.TEXT_PRIMARY,
            font=("Segoe UI", 11, "normal"),
            table_grid_fg=COLORS.BORDER,
            table_selected_cells_border_fg=COLORS.PRIMARY,
            table_selected_cells_bg=COLORS.PRIMARY,
            table_selected_cells_fg=COLORS.PRIMARY_FOREGROUND,
            # Index styling (hidden but set for consistency)
            index_bg=COLORS.MUTED,
            index_fg=COLORS.TEXT_SECONDARY,
            # Frame styling
            top_left_bg=COLORS.MUTED,
            outline_thickness=1,
            outline_color=COLORS.BORDER,
            frame_bg=COLORS.CARD,
            show_row_index=False,
            show_top_left=False,
            # Row height for better readability
            default_row_height=36,
        )
        self.table.pack(fill="both", expand=True, padx=SPACING.CARD_PADDING, pady=(SPACING.CARD_PADDING, 0))

        # Enable features
        self.table.enable_bindings(
            "single_select",
            "row_select",
            "column_width_resize",
            "arrowkeys",
            "copy",
        )

        # Column proportions (weights) - Title gets the most space
        # [Ref, Title, Type, Category, Owner, Status, Review, Next Review]
        self._column_weights = [1.0, 2.5, 0.8, 1.0, 1.2, 0.9, 0.8, 1.0]
        self._column_min_widths = [90, 150, 70, 80, 100, 80, 70, 90]

        # Set initial column widths
        self._resize_columns()

        # Bind to configure event for responsive resizing
        self.table_container.bind("<Configure>", self._on_container_resize)
        self._resize_scheduled = False

        # Bind events
        self.table.extra_bindings([
            ("cell_select", self._on_cell_select),
            ("row_select", self._on_row_select),
        ])

        # Double-click to open detail
        self.table.bind("<Double-Button-1>", self._on_double_click)

        # Header click for sorting
        self.table.extra_bindings([("column_header_click", self._on_header_click)])

    def _on_container_resize(self, event=None) -> None:
        """Handle container resize - debounced."""
        if not self._resize_scheduled:
            self._resize_scheduled = True
            self.after(100, self._do_resize)

    def _do_resize(self) -> None:
        """Perform the actual resize."""
        self._resize_scheduled = False
        self._resize_columns()

    def _resize_columns(self) -> None:
        """Resize columns to fill available width proportionally."""
        if not TKSHEET_AVAILABLE or not self.table:
            return

        try:
            # Get available width (container width minus padding and scrollbar)
            available_width = self.table_container.winfo_width() - (SPACING.CARD_PADDING * 2) - 20

            if available_width < 400:  # Not yet rendered or too small
                # Use fallback widths
                fallback_widths = [110, 280, 90, 100, 130, 100, 90, 100]
                for i, width in enumerate(fallback_widths):
                    self.table.column_width(i, width)
                return

            # Calculate total weight
            total_weight = sum(self._column_weights)

            # Calculate widths based on weights
            for i, (weight, min_width) in enumerate(zip(self._column_weights, self._column_min_widths)):
                proportional_width = int((weight / total_weight) * available_width)
                final_width = max(proportional_width, min_width)
                self.table.column_width(i, final_width)

        except Exception:
            pass  # Ignore errors during resize

    def _build_fallback_table(self) -> None:
        """Build a fallback table without tksheet."""
        # Simple scrollable frame with labels
        self.table_scroll = ctk.CTkScrollableFrame(
            self.table_container,
            fg_color="transparent",
        )
        self.table_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Header row
        header = ctk.CTkFrame(self.table_scroll, fg_color=COLORS.MUTED)
        header.pack(fill="x")

        headers = ["Ref", "Title", "Type", "Category", "Status", "Next Review"]
        for text in headers:
            ctk.CTkLabel(
                header,
                text=text,
                font=TYPOGRAPHY.get_font(11, "bold"),
                width=120,
                anchor="w",
            ).pack(side="left", padx=10, pady=8)

        self.table = None  # Mark as fallback mode

    def _update_fallback_table(self, documents: List[Document]) -> None:
        """Update the fallback table."""
        # Clear existing rows (keep header)
        children = self.table_scroll.winfo_children()
        for child in children[1:]:  # Skip header
            child.destroy()

        for doc in documents:
            row = ctk.CTkFrame(self.table_scroll, fg_color="transparent", cursor="hand2")
            row.pack(fill="x")
            row.bind("<Button-1>", lambda e, d=doc: self._open_document(d))
            row.bind("<Double-Button-1>", lambda e, d=doc: self._open_document(d))

            values = [
                doc.doc_ref,
                doc.title[:30] + "..." if len(doc.title) > 30 else doc.title,
                doc.type_display,
                doc.category,
                doc.status_display,
                format_date(doc.next_review_date),
            ]

            for val in values:
                label = ctk.CTkLabel(
                    row,
                    text=val,
                    font=TYPOGRAPHY.body,
                    width=120,
                    anchor="w",
                )
                label.pack(side="left", padx=10, pady=6)
                label.bind("<Button-1>", lambda e, d=doc: self._open_document(d))

            divider = ctk.CTkFrame(self.table_scroll, fg_color=COLORS.BORDER, height=1)
            divider.pack(fill="x")

    def _refresh_table(self) -> None:
        """Reload data with current filters."""
        filters = self.filter_bar.get_filters()

        # Get search term from our search entry (not filter bar)
        search_term = self.search_var.get().strip() if hasattr(self, 'search_var') else filters.get("search_term")

        # Get documents
        self.documents = self.doc_service.get_all_documents(
            status=filters.get("status"),
            doc_type=filters.get("doc_type"),
            category=filters.get("category"),
            review_status=filters.get("review_status"),
            search_term=search_term if search_term else None,
            mandatory_read_all=filters.get("mandatory_read_all"),
            applicable_entity=filters.get("applicable_entity"),
            order_by=self._sort_column,
            order_dir=self._sort_direction,
        )

        # Update entity filter dropdown in case new entities were added
        self.filter_bar.update_entities(self.entity_service.get_entity_names())

        # Update table
        if TKSHEET_AVAILABLE and self.table:
            data = []
            for doc in self.documents:
                data.append([
                    doc.doc_ref,
                    doc.title,
                    doc.type_display,
                    doc.category,
                    doc.owner,
                    doc.status_display,
                    doc.review_status_display,
                    format_date(doc.next_review_date),
                ])
            self.table.set_sheet_data(data)
        else:
            self._update_fallback_table(self.documents)

        # Update status
        self.status_label.configure(text=f"Showing {len(self.documents)} document(s)")

    def _on_filter_change(self) -> None:
        """Handle filter change."""
        self._refresh_table()

    def _on_search_key(self, event) -> None:
        """Handle search key release with debounce."""
        # Cancel previous scheduled search
        if self._search_after_id:
            self.after_cancel(self._search_after_id)

        # Schedule new search after 300ms
        self._search_after_id = self.after(300, self._refresh_table)

    def _on_clear_filters(self) -> None:
        """Clear all filters and search."""
        self.search_var.set("")
        self.filter_bar.clear_filters()

    def _on_cell_select(self, event) -> None:
        """Handle cell selection."""
        pass  # Can be used for future features

    def _on_row_select(self, event) -> None:
        """Handle row selection."""
        pass  # Can be used for future features

    def _on_double_click(self, event) -> None:
        """Handle double-click on table row."""
        if not TKSHEET_AVAILABLE or not self.table:
            return

        # Get selected row
        selected = self.table.get_currently_selected()
        if selected and len(self.documents) > 0:
            row = selected.row
            if 0 <= row < len(self.documents):
                self._open_document(self.documents[row])

    def _on_header_click(self, event) -> None:
        """Handle header click for sorting."""
        if not hasattr(event, 'column'):
            return

        column_map = {
            0: "doc_ref",
            1: "title",
            2: "doc_type",
            3: "category",
            4: "owner",
            5: "status",
            6: "next_review_date",  # Use date for Review column
            7: "next_review_date",
        }

        col = event.column
        if col in column_map:
            new_column = column_map[col]
            if new_column == self._sort_column:
                # Toggle direction
                self._sort_direction = "DESC" if self._sort_direction == "ASC" else "ASC"
            else:
                self._sort_column = new_column
                self._sort_direction = "ASC"

            self._refresh_table()

    def _on_add(self) -> None:
        """Handle add document button click."""
        categories = self.category_service.get_active_categories()
        dialog = DocumentDialog(
            self.winfo_toplevel(),
            self.app.db,
            categories=categories,
        )
        result = dialog.show()
        if result:
            self._refresh_table()

    def _open_document(self, document: Document) -> None:
        """Open document detail view."""
        main_view = self.app.current_view
        if hasattr(main_view, "_show_document_detail"):
            main_view._show_document_detail(document)

    def apply_filter(self, filter_type: Optional[str] = None, review_status: Optional[str] = None) -> None:
        """
        Apply a filter programmatically.

        Args:
            filter_type: Document type or status filter
            review_status: Review status filter
        """
        # Map filter_type to actual filter
        if filter_type:
            if filter_type == "total":
                self.filter_bar.clear_filters()
            elif filter_type == "active":
                self.filter_bar.set_filter("status", DocumentStatus.ACTIVE.value)
            elif filter_type == "under_review":
                self.filter_bar.set_filter("status", DocumentStatus.UNDER_REVIEW.value)
            elif filter_type in ["policy", "procedure", "manual", "hr_others"]:
                self.filter_bar.set_filter("doc_type", filter_type.upper())

        if review_status:
            self.filter_bar.set_filter("review_status", review_status)

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        self._refresh_table()
