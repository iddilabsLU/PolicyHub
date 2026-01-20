"""
PolicyHub Document Detail View

Displays complete information for a single document with actions.
"""

import os
import shutil
import subprocess
from pathlib import Path
from tkinter import filedialog
from typing import TYPE_CHECKING, Callable, List, Optional

import customtkinter as ctk

from app.constants import DocumentStatus
from app.theme import COLORS, SPACING, TYPOGRAPHY, configure_button_style
from components.status_badge import StatusBadge
from core.database import DatabaseManager
from core.permissions import PermissionChecker
from dialogs.confirm_dialog import ConfirmDialog, InfoDialog
from dialogs.document_dialog import DocumentDialog
from dialogs.link_dialog import LinkDialog
from dialogs.upload_dialog import UploadDialog
from models.attachment import Attachment
from models.document import Document
from models.history import HistoryEntry
from models.link import DocumentLink
from services.attachment_service import AttachmentService
from services.category_service import CategoryService
from services.document_service import DocumentService
from services.history_service import HistoryService
from services.link_service import LinkService, LinkedDocument
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
        self.attachment_service = AttachmentService(app.db)
        self.link_service = LinkService(app.db)
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
            segmented_button_unselected_color=COLORS.SECONDARY,  # Warm grey for unselected
            segmented_button_selected_hover_color=COLORS.PRIMARY_HOVER,
            segmented_button_unselected_hover_color=COLORS.BORDER,
            command=self._on_tab_changed,  # Callback to fix text colors
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

        # Fix initial tab text colors
        self._fix_tab_text_colors()

    def _on_tab_changed(self) -> None:
        """Handle tab change to fix text colors."""
        self._fix_tab_text_colors()

    def _fix_tab_text_colors(self) -> None:
        """Fix text colors for segmented button tabs."""
        try:
            segmented_button = self.tabview._segmented_button
            current_tab = self.tabview.get()

            # Update each button's text color based on selection state
            for tab_name, button in segmented_button._buttons_dict.items():
                if tab_name == current_tab:
                    # Selected - white text on dark background
                    button.configure(text_color=COLORS.PRIMARY_FOREGROUND)
                else:
                    # Unselected - dark text on light background
                    button.configure(text_color=COLORS.TEXT_PRIMARY)
        except Exception:
            pass  # Ignore errors if internal structure changes

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

        # Row 4: Applicable Entities, Mandatory Read
        if self.document.applicable_entity:
            # Format semicolon-separated entities as comma-separated for display
            entities = self.document.applicable_entity.split(";")
            entity_value = ", ".join(entities) if len(entities) <= 3 else f"{entities[0]}, {entities[1]} +{len(entities)-2} more"
        else:
            entity_value = "All Entities"
        mandatory_value = "Yes" if self.document.mandatory_read_all else "No"
        self._add_field(fields_frame, "Applicable Entities", entity_value, row, 0)
        self._add_field(fields_frame, "Mandatory Read", mandatory_value, row, 1)
        row += 1

        # Row 5: Review Frequency, Review Status
        self._add_field(fields_frame, "Review Frequency", self.document.frequency_display, row, 0)
        self._add_field(fields_frame, "Review Status", self.document.review_status_display, row, 1)
        row += 1

        # Row 6: Effective Date, Last Review
        self._add_field(fields_frame, "Effective Date", format_date(self.document.effective_date), row, 0)
        self._add_field(fields_frame, "Last Reviewed", format_date(self.document.last_review_date), row, 1)
        row += 1

        # Row 7: Next Review with action
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
        """Build the attachments tab with upload and list functionality."""
        tab = self.tabview.tab("Attachments")

        # Header with upload button
        header_frame = ctk.CTkFrame(tab, fg_color="transparent", height=50)
        header_frame.pack(fill="x", padx=10, pady=10)
        header_frame.pack_propagate(False)

        ctk.CTkLabel(
            header_frame,
            text="Attachments",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        ).pack(side="left")

        # Upload button (editor+)
        if self.permissions.can_edit():
            upload_btn = ctk.CTkButton(
                header_frame,
                text="+ Upload File",
                command=self._on_upload_attachment,
                width=120,
                height=32,
            )
            configure_button_style(upload_btn, "primary")
            upload_btn.pack(side="right")

        # Download All button
        self.download_all_btn = ctk.CTkButton(
            header_frame,
            text="Download All",
            command=self._on_download_all_attachments,
            width=110,
            height=32,
        )
        configure_button_style(self.download_all_btn, "secondary")
        self.download_all_btn.pack(side="right", padx=(0, 10))

        # Scrollable list container
        self.attachments_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.attachments_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Load attachments
        self._load_attachments()

    def _load_attachments(self) -> None:
        """Load and display attachments list."""
        # Clear existing
        for widget in self.attachments_scroll.winfo_children():
            widget.destroy()

        attachments = self.attachment_service.get_attachments_for_document(self.document.doc_id)

        # Update Download All button state
        if hasattr(self, 'download_all_btn'):
            if attachments:
                self.download_all_btn.configure(state="normal")
            else:
                self.download_all_btn.configure(state="disabled")

        if not attachments:
            ctk.CTkLabel(
                self.attachments_scroll,
                text="No attachments uploaded yet.",
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_SECONDARY,
            ).pack(pady=40)
            return

        # Display each attachment
        for attachment in attachments:
            self._create_attachment_row(attachment)

    def _create_attachment_row(self, attachment: Attachment) -> None:
        """Create a row for an attachment."""
        row = ctk.CTkFrame(
            self.attachments_scroll,
            fg_color=COLORS.MUTED,
            corner_radius=SPACING.CORNER_RADIUS,
        )
        row.pack(fill="x", pady=5)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=12)

        # Left side: file info
        info_frame = ctk.CTkFrame(inner, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        # Filename with current badge
        name_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        name_row.pack(anchor="w")

        ctk.CTkLabel(
            name_row,
            text=attachment.filename,
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        ).pack(side="left")

        if attachment.is_current:
            current_badge = ctk.CTkLabel(
                name_row,
                text="CURRENT",
                font=TYPOGRAPHY.get_font(10, "bold"),
                text_color=COLORS.PRIMARY_FOREGROUND,
                fg_color=COLORS.SUCCESS,
                corner_radius=4,
                padx=8,
                pady=2,
            )
            current_badge.pack(side="left", padx=(10, 0))

        # Meta info
        meta_text = f"v{attachment.version_label} | {attachment.size_display} | {format_datetime(attachment.uploaded_at)}"
        ctk.CTkLabel(
            info_frame,
            text=meta_text,
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        ).pack(anchor="w")

        # Right side: action buttons
        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(side="right")

        # Open button
        open_btn = ctk.CTkButton(
            actions,
            text="Open",
            command=lambda a=attachment: self._on_open_attachment(a),
            width=70,
            height=28,
            font=TYPOGRAPHY.small,
        )
        configure_button_style(open_btn, "secondary")
        open_btn.pack(side="left", padx=5)

        # Delete button (editor+)
        if self.permissions.can_edit():
            delete_btn = ctk.CTkButton(
                actions,
                text="Delete",
                command=lambda a=attachment: self._on_delete_attachment(a),
                width=70,
                height=28,
                font=TYPOGRAPHY.small,
            )
            configure_button_style(delete_btn, "danger")
            delete_btn.pack(side="left", padx=5)

    def _on_upload_attachment(self) -> None:
        """Handle upload attachment button click."""
        dialog = UploadDialog(
            self.winfo_toplevel(),
            doc_ref=self.document.doc_ref,
            current_version=self.document.version,
        )
        result = dialog.show()

        if result:
            file_path, version_label = result
            try:
                self.attachment_service.add_attachment(
                    doc_id=self.document.doc_id,
                    doc_ref=self.document.doc_ref,
                    source_path=file_path,
                    version_label=version_label,
                )
                InfoDialog.show_info(
                    self.winfo_toplevel(),
                    "Success",
                    f"File '{file_path.name}' uploaded successfully.",
                )
                self._load_attachments()
                self._load_history()
            except PermissionError as e:
                InfoDialog.show_error(self.winfo_toplevel(), "Permission Denied", str(e))
            except ValueError as e:
                InfoDialog.show_error(self.winfo_toplevel(), "Upload Error", str(e))
            except Exception as e:
                InfoDialog.show_error(self.winfo_toplevel(), "Error", f"Failed to upload: {str(e)}")

    def _on_open_attachment(self, attachment: Attachment) -> None:
        """Handle open attachment button click."""
        file_path = self.attachment_service.open_attachment(attachment.attachment_id)

        if file_path and file_path.exists():
            try:
                # Open file with default application (Windows)
                os.startfile(str(file_path))
            except Exception as e:
                InfoDialog.show_error(
                    self.winfo_toplevel(),
                    "Error",
                    f"Failed to open file: {str(e)}",
                )
        else:
            InfoDialog.show_error(
                self.winfo_toplevel(),
                "File Not Found",
                "The attachment file could not be found.",
            )

    def _on_delete_attachment(self, attachment: Attachment) -> None:
        """Handle delete attachment button click."""
        if ConfirmDialog.ask_delete(
            self.winfo_toplevel(),
            item_name=attachment.filename,
            item_type="attachment",
        ):
            try:
                self.attachment_service.delete_attachment(attachment.attachment_id)
                InfoDialog.show_info(
                    self.winfo_toplevel(),
                    "Deleted",
                    f"Attachment '{attachment.filename}' has been deleted.",
                )
                self._load_attachments()
                self._load_history()
            except PermissionError as e:
                InfoDialog.show_error(self.winfo_toplevel(), "Permission Denied", str(e))
            except Exception as e:
                InfoDialog.show_error(self.winfo_toplevel(), "Error", str(e))

    def _on_download_all_attachments(self) -> None:
        """Handle download all attachments button click."""
        attachments = self.attachment_service.get_attachments_for_document(self.document.doc_id)

        if not attachments:
            InfoDialog.show_info(
                self.winfo_toplevel(),
                "No Attachments",
                "There are no attachments to download.",
            )
            return

        # Ask for destination folder
        dest_folder = filedialog.askdirectory(
            parent=self.winfo_toplevel(),
            title="Select Download Folder",
        )

        if not dest_folder:
            return

        dest_path = Path(dest_folder)
        downloaded = 0
        failed = []

        for attachment in attachments:
            try:
                # Get the source file path
                source_path = self.attachment_service.open_attachment(attachment.attachment_id)
                if source_path and source_path.exists():
                    # Copy to destination
                    dest_file = dest_path / attachment.filename
                    # Handle duplicate filenames
                    counter = 1
                    while dest_file.exists():
                        stem = attachment.filename.rsplit('.', 1)[0] if '.' in attachment.filename else attachment.filename
                        ext = '.' + attachment.filename.rsplit('.', 1)[1] if '.' in attachment.filename else ''
                        dest_file = dest_path / f"{stem}_{counter}{ext}"
                        counter += 1
                    shutil.copy2(source_path, dest_file)
                    downloaded += 1
                else:
                    failed.append(attachment.filename)
            except Exception as e:
                failed.append(f"{attachment.filename}: {str(e)}")

        # Show result
        if failed:
            InfoDialog.show_info(
                self.winfo_toplevel(),
                "Download Complete",
                f"Downloaded {downloaded} file(s).\n\nFailed to download:\n" + "\n".join(failed[:5]),
            )
        else:
            InfoDialog.show_info(
                self.winfo_toplevel(),
                "Download Complete",
                f"Successfully downloaded {downloaded} file(s) to:\n{dest_folder}",
            )

    def _build_links_tab(self) -> None:
        """Build the linked documents tab with link management."""
        tab = self.tabview.tab("Linked Documents")

        # Header with add link button
        header_frame = ctk.CTkFrame(tab, fg_color="transparent", height=50)
        header_frame.pack(fill="x", padx=10, pady=10)
        header_frame.pack_propagate(False)

        ctk.CTkLabel(
            header_frame,
            text="Linked Documents",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        ).pack(side="left")

        # Add link button (editor+)
        if self.permissions.can_edit():
            add_link_btn = ctk.CTkButton(
                header_frame,
                text="+ Add Link",
                command=self._on_add_link,
                width=100,
                height=32,
            )
            configure_button_style(add_link_btn, "primary")
            add_link_btn.pack(side="right")

        # Scrollable list container
        self.links_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.links_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Load links
        self._load_links()

    def _load_links(self) -> None:
        """Load and display document links."""
        # Clear existing
        for widget in self.links_scroll.winfo_children():
            widget.destroy()

        links = self.link_service.get_links_for_document(self.document.doc_id)

        if not links:
            ctk.CTkLabel(
                self.links_scroll,
                text="No linked documents.",
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_SECONDARY,
            ).pack(pady=40)
            return

        # Display each link
        for linked_doc in links:
            self._create_link_row(linked_doc)

    def _create_link_row(self, linked_doc: LinkedDocument) -> None:
        """Create a row for a linked document."""
        row = ctk.CTkFrame(
            self.links_scroll,
            fg_color=COLORS.MUTED,
            corner_radius=SPACING.CORNER_RADIUS,
            cursor="hand2",
        )
        row.pack(fill="x", pady=5)

        # Make entire row clickable (except action buttons)
        row.bind("<Button-1>", lambda e, ld=linked_doc: self._on_click_linked_doc(ld))
        row.bind("<Enter>", lambda e: row.configure(fg_color=COLORS.BORDER))
        row.bind("<Leave>", lambda e: row.configure(fg_color=COLORS.MUTED))

        inner = ctk.CTkFrame(row, fg_color="transparent", cursor="hand2")
        inner.pack(fill="x", padx=15, pady=12)
        inner.bind("<Button-1>", lambda e, ld=linked_doc: self._on_click_linked_doc(ld))

        # Left side: link info
        info_frame = ctk.CTkFrame(inner, fg_color="transparent", cursor="hand2")
        info_frame.pack(side="left", fill="x", expand=True)
        info_frame.bind("<Button-1>", lambda e, ld=linked_doc: self._on_click_linked_doc(ld))

        # Relationship text
        relationship = linked_doc.link.get_relationship_text(linked_doc.is_parent)
        rel_text = f"{relationship}:"

        rel_label = ctk.CTkLabel(
            info_frame,
            text=rel_text,
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
            cursor="hand2",
        )
        rel_label.pack(anchor="w")
        rel_label.bind("<Button-1>", lambda e, ld=linked_doc: self._on_click_linked_doc(ld))

        # Document reference and title
        doc_row = ctk.CTkFrame(info_frame, fg_color="transparent", cursor="hand2")
        doc_row.pack(anchor="w")
        doc_row.bind("<Button-1>", lambda e, ld=linked_doc: self._on_click_linked_doc(ld))

        ref_label = ctk.CTkLabel(
            doc_row,
            text=linked_doc.doc_ref,
            font=TYPOGRAPHY.get_font(13, "bold"),
            text_color=COLORS.PRIMARY,
            cursor="hand2",
        )
        ref_label.pack(side="left")
        ref_label.bind("<Button-1>", lambda e, ld=linked_doc: self._on_click_linked_doc(ld))

        # Title
        title_text = f" - {linked_doc.title[:50]}" + ("..." if len(linked_doc.title) > 50 else "")
        title_label = ctk.CTkLabel(
            doc_row,
            text=title_text,
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
            cursor="hand2",
        )
        title_label.pack(side="left")
        title_label.bind("<Button-1>", lambda e, ld=linked_doc: self._on_click_linked_doc(ld))

        # Right side: action buttons
        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(side="right")

        # Delete button (editor+)
        if self.permissions.can_edit():
            delete_btn = ctk.CTkButton(
                actions,
                text="Remove",
                command=lambda ld=linked_doc: self._on_remove_link(ld),
                width=80,
                height=28,
                font=TYPOGRAPHY.small,
            )
            configure_button_style(delete_btn, "danger")
            delete_btn.pack(side="left", padx=5)

    def _on_add_link(self) -> None:
        """Handle add link button click."""
        dialog = LinkDialog(
            self.winfo_toplevel(),
            self.app.db,
            source_doc_id=self.document.doc_id,
            source_doc_ref=self.document.doc_ref,
        )
        result = dialog.show()

        if result:
            target_doc_id, link_type = result
            try:
                self.link_service.create_link(
                    parent_doc_id=self.document.doc_id,
                    child_doc_id=target_doc_id,
                    link_type=link_type,
                )
                InfoDialog.show_info(
                    self.winfo_toplevel(),
                    "Success",
                    "Document link created successfully.",
                )
                self._load_links()
                self._load_history()
            except PermissionError as e:
                InfoDialog.show_error(self.winfo_toplevel(), "Permission Denied", str(e))
            except ValueError as e:
                InfoDialog.show_error(self.winfo_toplevel(), "Error", str(e))
            except Exception as e:
                InfoDialog.show_error(self.winfo_toplevel(), "Error", f"Failed to create link: {str(e)}")

    def _on_click_linked_doc(self, linked_doc: LinkedDocument) -> None:
        """Handle click on linked document reference to navigate to it."""
        # Get the linked document ID
        if linked_doc.is_parent:
            # This doc is parent, linked doc is child
            target_doc_id = linked_doc.link.child_doc_id
        else:
            # This doc is child, linked doc is parent
            target_doc_id = linked_doc.link.parent_doc_id

        # Get the full document
        target_doc = self.doc_service.get_document_by_id(target_doc_id)
        if target_doc:
            # Navigate to the linked document via main_view
            main_view = self.app.current_view
            if hasattr(main_view, "_show_document_detail"):
                main_view._show_document_detail(target_doc)
            else:
                InfoDialog.show_error(
                    self.winfo_toplevel(),
                    "Navigation Error",
                    "Cannot navigate to the linked document.",
                )
        else:
            InfoDialog.show_error(
                self.winfo_toplevel(),
                "Document Not Found",
                f"Could not find document {linked_doc.doc_ref}.",
            )

    def _on_remove_link(self, linked_doc: LinkedDocument) -> None:
        """Handle remove link button click."""
        if ConfirmDialog.ask(
            self.winfo_toplevel(),
            "Remove Link",
            f"Remove link to {linked_doc.doc_ref}?",
            confirm_text="Remove",
        ):
            try:
                self.link_service.delete_link(linked_doc.link.link_id)
                InfoDialog.show_info(
                    self.winfo_toplevel(),
                    "Removed",
                    "Link has been removed.",
                )
                self._load_links()
                self._load_history()
            except PermissionError as e:
                InfoDialog.show_error(self.winfo_toplevel(), "Permission Denied", str(e))
            except Exception as e:
                InfoDialog.show_error(self.winfo_toplevel(), "Error", str(e))

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
