"""
PolicyHub Document Detail View

Displays complete information for a single document with actions.
"""

from typing import TYPE_CHECKING, Callable, List, Optional

import customtkinter as ctk

from app.constants import DocumentStatus
from app.theme import COLORS, SPACING, TYPOGRAPHY, configure_button_style
from components.status_badge import StatusBadge
from core.database import DatabaseManager
from core.permissions import PermissionChecker
from dialogs.confirm_dialog import ConfirmDialog, InfoDialog
from dialogs.document_dialog import DocumentDialog
from models.document import Document
from models.history import HistoryEntry
from services.category_service import CategoryService
from services.document_service import DocumentService
from services.history_service import HistoryService
from utils.dates import format_date, format_datetime
from views.base_view import BaseView

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class DocumentDetailView(BaseView):
    """
    Document detail view showing all document information.

    Features:
    - Full document metadata display
    - Edit and delete actions (if permitted)
    - Mark as reviewed action
    - Tabbed sections: Details, Attachments, Links, History
    - Back navigation
    """

    def __init__(
        self,
        parent: ctk.CTkFrame,
        app: "PolicyHubApp",
        document: Document,
        on_back: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the document detail view.

        Args:
            parent: Parent widget
            app: Main application instance
            document: Document to display
            on_back: Callback when back button is clicked
        """
        super().__init__(parent, app)
        self.document = document
        self.on_back = on_back
        self.doc_service = DocumentService(app.db)
        self.history_service = HistoryService(app.db)
        self.category_service = CategoryService(app.db)
        self.permissions = PermissionChecker()

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the document detail UI."""
        # Header with back button and actions
        self._build_header()

        # Title and badges section
        self._build_title_section()

        # Tabbed content
        self._build_tabs()

    def _build_header(self) -> None:
        """Build the header with navigation and actions."""
        header = ctk.CTkFrame(self, fg_color=COLORS.CARD, height=60)
        header.pack(fill="x", padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING)
        header.pack_propagate(False)

        # Back button
        back_btn = ctk.CTkButton(
            header,
            text="< Back",
            command=self._on_back,
            width=80,
            height=32,
            font=TYPOGRAPHY.body,
        )
        configure_button_style(back_btn, "secondary")
        back_btn.pack(side="left", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        # Document reference
        ref_label = ctk.CTkLabel(
            header,
            text=self.document.doc_ref,
            font=TYPOGRAPHY.get_font(16, "bold"),
            text_color=COLORS.TEXT_PRIMARY,
        )
        ref_label.pack(side="left", padx=20, pady=SPACING.CARD_PADDING)

        # Action buttons (right side)
        actions_frame = ctk.CTkFrame(header, fg_color="transparent")
        actions_frame.pack(side="right", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        # Delete button (admin only)
        if self.permissions.can_delete():
            delete_btn = ctk.CTkButton(
                actions_frame,
                text="Delete",
                command=self._on_delete,
                width=80,
                height=32,
                font=TYPOGRAPHY.small,
            )
            configure_button_style(delete_btn, "danger")
            delete_btn.pack(side="right", padx=5)

        # Edit button (editor+)
        if self.permissions.can_edit():
            edit_btn = ctk.CTkButton(
                actions_frame,
                text="Edit",
                command=self._on_edit,
                width=80,
                height=32,
                font=TYPOGRAPHY.small,
            )
            configure_button_style(edit_btn, "secondary")
            edit_btn.pack(side="right", padx=5)

    def _build_title_section(self) -> None:
        """Build the title and badges section."""
        title_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS.CARD,
            corner_radius=SPACING.CORNER_RADIUS,
        )
        title_frame.pack(fill="x", padx=SPACING.WINDOW_PADDING, pady=(0, 10))

        inner = ctk.CTkFrame(title_frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)

        # Title
        title_label = ctk.CTkLabel(
            inner,
            text=self.document.title,
            font=TYPOGRAPHY.window_title,
            text_color=COLORS.TEXT_PRIMARY,
            wraplength=700,
            justify="left",
        )
        title_label.pack(anchor="w")

        # Badges row
        badges_frame = ctk.CTkFrame(inner, fg_color="transparent")
        badges_frame.pack(anchor="w", pady=(10, 0))

        # Type badge
        type_badge = StatusBadge(badges_frame, text=self.document.type_display, variant="primary")
        type_badge.pack(side="left", padx=(0, 10))

        # Status badge
        status_badge = StatusBadge.from_status(badges_frame, self.document.status)
        status_badge.pack(side="left", padx=(0, 10))

        # Review status badge
        review_badge = StatusBadge.from_review_status(badges_frame, self.document.review_status)
        review_badge.pack(side="left")

    def _build_tabs(self) -> None:
        """Build the tabbed content area."""
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=COLORS.CARD,
            segmented_button_fg_color=COLORS.MUTED,
            segmented_button_selected_color=COLORS.PRIMARY,
            segmented_button_unselected_color=COLORS.MUTED,
            text_color=COLORS.TEXT_PRIMARY,
            segmented_button_selected_hover_color=COLORS.PRIMARY_HOVER,
        )
        self.tabview.pack(
            fill="both",
            expand=True,
            padx=SPACING.WINDOW_PADDING,
            pady=(0, SPACING.WINDOW_PADDING),
        )

        # Add tabs
        self.tabview.add("Details")
        self.tabview.add("Attachments")
        self.tabview.add("Linked Documents")
        self.tabview.add("History")

        # Build tab contents
        self._build_details_tab()
        self._build_attachments_tab()
        self._build_links_tab()
        self._build_history_tab()

    def _build_details_tab(self) -> None:
        """Build the details tab content."""
        tab = self.tabview.tab("Details")

        # Scrollable frame
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Two-column layout for fields
        fields_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        fields_frame.pack(fill="x")
        fields_frame.columnconfigure(0, weight=1)
        fields_frame.columnconfigure(1, weight=1)

        row = 0

        # Row 1: Type, Category
        self._add_field(fields_frame, "Document Type", self.document.type_display, row, 0)
        self._add_field(fields_frame, "Category", self.document.category, row, 1)
        row += 1

        # Row 2: Version, Status
        self._add_field(fields_frame, "Version", self.document.version, row, 0)
        self._add_field(fields_frame, "Status", self.document.status_display, row, 1)
        row += 1

        # Row 3: Owner, Approver
        self._add_field(fields_frame, "Owner", self.document.owner, row, 0)
        self._add_field(fields_frame, "Approver", self.document.approver or "-", row, 1)
        row += 1

        # Row 4: Review Frequency, Review Status
        self._add_field(fields_frame, "Review Frequency", self.document.frequency_display, row, 0)
        self._add_field(fields_frame, "Review Status", self.document.review_status_display, row, 1)
        row += 1

        # Row 5: Effective Date, Last Review
        self._add_field(fields_frame, "Effective Date", format_date(self.document.effective_date), row, 0)
        self._add_field(fields_frame, "Last Reviewed", format_date(self.document.last_review_date), row, 1)
        row += 1

        # Row 6: Next Review with action
        next_review_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
        next_review_frame.grid(row=row, column=0, sticky="w", padx=10, pady=10)

        ctk.CTkLabel(
            next_review_frame,
            text="Next Review",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        ).pack(anchor="w")

        date_row = ctk.CTkFrame(next_review_frame, fg_color="transparent")
        date_row.pack(anchor="w")

        ctk.CTkLabel(
            date_row,
            text=format_date(self.document.next_review_date),
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        ).pack(side="left")

        # Mark reviewed button
        if self.permissions.can_edit() and self.document.status == DocumentStatus.ACTIVE.value:
            review_btn = ctk.CTkButton(
                date_row,
                text="Mark Reviewed",
                command=self._on_mark_reviewed,
                width=110,
                height=28,
                font=TYPOGRAPHY.small,
            )
            configure_button_style(review_btn, "primary")
            review_btn.pack(side="left", padx=(15, 0))

        row += 1

        # Description (full width)
        if self.document.description:
            desc_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            desc_frame.pack(fill="x", pady=(10, 0))

            ctk.CTkLabel(
                desc_frame,
                text="Description",
                font=TYPOGRAPHY.small,
                text_color=COLORS.TEXT_SECONDARY,
            ).pack(anchor="w", padx=10)

            desc_text = ctk.CTkTextbox(
                desc_frame,
                height=80,
                font=TYPOGRAPHY.body,
                fg_color=COLORS.MUTED,
                border_width=0,
                state="disabled",
            )
            desc_text.pack(fill="x", padx=10, pady=(5, 0))
            desc_text.configure(state="normal")
            desc_text.insert("1.0", self.document.description)
            desc_text.configure(state="disabled")

        # Notes (full width)
        if self.document.notes:
            notes_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            notes_frame.pack(fill="x", pady=(10, 0))

            ctk.CTkLabel(
                notes_frame,
                text="Notes",
                font=TYPOGRAPHY.small,
                text_color=COLORS.TEXT_SECONDARY,
            ).pack(anchor="w", padx=10)

            notes_text = ctk.CTkTextbox(
                notes_frame,
                height=60,
                font=TYPOGRAPHY.body,
                fg_color=COLORS.MUTED,
                border_width=0,
                state="disabled",
            )
            notes_text.pack(fill="x", padx=10, pady=(5, 0))
            notes_text.configure(state="normal")
            notes_text.insert("1.0", self.document.notes)
            notes_text.configure(state="disabled")

        # Metadata
        meta_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        meta_frame.pack(fill="x", pady=(20, 0))

        ctk.CTkLabel(
            meta_frame,
            text=f"Created: {format_datetime(self.document.created_at)} | "
                 f"Last Updated: {format_datetime(self.document.updated_at)}",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        ).pack(anchor="w", padx=10)

    def _add_field(self, parent, label: str, value: str, row: int, col: int) -> None:
        """Add a field display to the grid."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, sticky="w", padx=10, pady=10)

        ctk.CTkLabel(
            frame,
            text=label,
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            frame,
            text=value,
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        ).pack(anchor="w")

    def _build_attachments_tab(self) -> None:
        """Build the attachments tab (placeholder for Phase 5)."""
        tab = self.tabview.tab("Attachments")

        placeholder = ctk.CTkLabel(
            tab,
            text="Attachment management will be available in a future update.",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_SECONDARY,
        )
        placeholder.pack(expand=True)

    def _build_links_tab(self) -> None:
        """Build the linked documents tab (placeholder for Phase 5)."""
        tab = self.tabview.tab("Linked Documents")

        placeholder = ctk.CTkLabel(
            tab,
            text="Document linking will be available in a future update.",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_SECONDARY,
        )
        placeholder.pack(expand=True)

    def _build_history_tab(self) -> None:
        """Build the history tab showing audit trail."""
        tab = self.tabview.tab("History")

        # Scrollable frame
        self.history_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.history_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Load history
        self._load_history()

    def _load_history(self) -> None:
        """Load and display document history."""
        history = self.history_service.get_document_history(self.document.doc_id, limit=50)

        # Clear existing
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        if not history:
            ctk.CTkLabel(
                self.history_scroll,
                text="No history entries found.",
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_SECONDARY,
            ).pack(pady=20)
            return

        # Header
        header = ctk.CTkFrame(self.history_scroll, fg_color=COLORS.MUTED)
        header.pack(fill="x")

        for text, width in [("Date/Time", 150), ("Action", 120), ("Details", 300), ("User", 100)]:
            ctk.CTkLabel(
                header,
                text=text,
                font=TYPOGRAPHY.get_font(11, "bold"),
                width=width,
                anchor="w",
            ).pack(side="left", padx=10, pady=8)

        # History entries
        for entry in history:
            row = ctk.CTkFrame(self.history_scroll, fg_color="transparent")
            row.pack(fill="x")

            # Date/Time
            ctk.CTkLabel(
                row,
                text=format_datetime(entry.changed_at),
                font=TYPOGRAPHY.small,
                text_color=COLORS.TEXT_SECONDARY,
                width=150,
                anchor="w",
            ).pack(side="left", padx=10, pady=6)

            # Action
            ctk.CTkLabel(
                row,
                text=entry.action_display,
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_PRIMARY,
                width=120,
                anchor="w",
            ).pack(side="left", padx=10, pady=6)

            # Details
            ctk.CTkLabel(
                row,
                text=entry.get_change_description()[:50],
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_PRIMARY,
                width=300,
                anchor="w",
            ).pack(side="left", padx=10, pady=6)

            # User (would need to resolve user ID to name)
            ctk.CTkLabel(
                row,
                text=entry.changed_by[:8] + "..." if entry.changed_by else "-",
                font=TYPOGRAPHY.small,
                text_color=COLORS.TEXT_SECONDARY,
                width=100,
                anchor="w",
            ).pack(side="left", padx=10, pady=6)

            # Divider
            divider = ctk.CTkFrame(self.history_scroll, fg_color=COLORS.BORDER, height=1)
            divider.pack(fill="x")

    def _on_back(self) -> None:
        """Handle back button click."""
        if self.on_back:
            self.on_back()

    def _on_edit(self) -> None:
        """Handle edit button click."""
        categories = self.category_service.get_active_categories()
        dialog = DocumentDialog(
            self.winfo_toplevel(),
            self.app.db,
            categories=categories,
            document=self.document,
        )
        result = dialog.show()
        if result:
            self.document = result
            self._refresh_display()

    def _on_delete(self) -> None:
        """Handle delete button click."""
        if ConfirmDialog.ask_delete(
            self.winfo_toplevel(),
            item_name=self.document.doc_ref,
            item_type="document",
        ):
            try:
                self.doc_service.delete_document(self.document.doc_id)
                InfoDialog.show_info(
                    self.winfo_toplevel(),
                    "Deleted",
                    f"Document {self.document.doc_ref} has been deleted.",
                )
                self._on_back()
            except PermissionError as e:
                InfoDialog.show_error(self.winfo_toplevel(), "Permission Denied", str(e))
            except Exception as e:
                InfoDialog.show_error(self.winfo_toplevel(), "Error", str(e))

    def _on_mark_reviewed(self) -> None:
        """Handle mark reviewed button click."""
        try:
            result = self.doc_service.mark_as_reviewed(self.document.doc_id)
            if result:
                self.document = result
                self._refresh_display()
                InfoDialog.show_info(
                    self.winfo_toplevel(),
                    "Reviewed",
                    f"Document marked as reviewed. Next review: {format_date(result.next_review_date)}",
                )
        except PermissionError as e:
            InfoDialog.show_error(self.winfo_toplevel(), "Permission Denied", str(e))
        except Exception as e:
            InfoDialog.show_error(self.winfo_toplevel(), "Error", str(e))

    def _refresh_display(self) -> None:
        """Refresh the entire display with updated document data."""
        # Clear and rebuild
        for widget in self.winfo_children():
            widget.destroy()

        self._build_ui()

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        # Reload history in case it changed
        self._load_history()
