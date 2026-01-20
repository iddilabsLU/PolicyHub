"""
PolicyHub Link Dialog

Dialog for creating links between documents.
"""

from typing import List, Optional, Tuple

import customtkinter as ctk

from app.constants import LinkType
from app.theme import COLORS, SPACING, TYPOGRAPHY, configure_button_style
from core.database import DatabaseManager
from dialogs.base_dialog import BaseDialog
from dialogs.confirm_dialog import InfoDialog
from services.link_service import LinkService


class LinkDialog(BaseDialog):
    """
    Dialog for linking two documents.

    Usage:
        dialog = LinkDialog(
            parent,
            db,
            source_doc_id="...",
            source_doc_ref="POL-AML-001",
        )
        result = dialog.show()  # Returns (target_doc_id, link_type) or None
    """

    def __init__(
        self,
        parent,
        db: DatabaseManager,
        source_doc_id: str,
        source_doc_ref: str,
    ):
        """
        Initialize the link dialog.

        Args:
            parent: Parent window
            db: Database manager instance
            source_doc_id: ID of the source document
            source_doc_ref: Reference of the source document
        """
        self.db = db
        self.source_doc_id = source_doc_id
        self.source_doc_ref = source_doc_ref
        self.link_service = LinkService(db)
        self.selected_doc: Optional[dict] = None
        self.available_docs: List[dict] = []

        super().__init__(parent, "Link Documents", width=600, height=550)
        self._build_ui()
        self._load_available_documents()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # IMPORTANT: Pack buttons FIRST at bottom to guarantee visibility
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(side="bottom", fill="x", pady=(15, 0))

        self.link_btn = ctk.CTkButton(
            button_frame,
            text="Create Link",
            command=self._on_create_link,
            width=120,
            height=36,
            state="disabled",
        )
        configure_button_style(self.link_btn, "primary")
        self.link_btn.pack(side="right", padx=(5, 0))

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=100,
            height=36,
        )
        configure_button_style(cancel_btn, "secondary")
        cancel_btn.pack(side="right")

        # Selected document display (pack second from bottom)
        self.selected_frame = ctk.CTkFrame(
            main_frame,
            fg_color=COLORS.MUTED,
            corner_radius=SPACING.CORNER_RADIUS,
            height=45,
        )
        self.selected_frame.pack(side="bottom", fill="x", pady=(10, 0))
        self.selected_frame.pack_propagate(False)

        self.selected_label = ctk.CTkLabel(
            self.selected_frame,
            text="No document selected",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_SECONDARY,
        )
        self.selected_label.pack(expand=True)

        # Content area (fills remaining space above)
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(side="top", fill="both", expand=True)

        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text=f"Create link from {self.source_doc_ref}",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title_label.pack(anchor="w", pady=(0, 15))

        # Link type selection
        type_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        type_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            type_frame,
            text="Link Type:",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        ).pack(side="left", padx=(0, 10))

        link_types = [
            (LinkType.IMPLEMENTS.value, "Implements (procedure implements policy)"),
            (LinkType.REFERENCES.value, "References (document references another)"),
            (LinkType.SUPERSEDES.value, "Supersedes (new version replaces old)"),
        ]

        self.link_type_var = ctk.StringVar(value=LinkType.REFERENCES.value)
        self.link_type_dropdown = ctk.CTkOptionMenu(
            type_frame,
            values=[t[1] for t in link_types],
            variable=ctk.StringVar(value=link_types[1][1]),
            width=350,
            height=36,
            font=TYPOGRAPHY.body,
            dropdown_font=TYPOGRAPHY.body,
            command=self._on_link_type_change,
        )
        self.link_type_dropdown.pack(side="left")
        self._link_type_map = {t[1]: t[0] for t in link_types}

        # Search box
        search_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            search_frame,
            text="Search Document:",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        ).pack(side="left", padx=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._on_search())
        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            width=300,
            height=36,
            font=TYPOGRAPHY.body,
            placeholder_text="Search by reference or title...",
        )
        self.search_entry.pack(side="left", fill="x", expand=True)

        # Document list
        list_frame = ctk.CTkFrame(
            content_frame,
            fg_color=COLORS.CARD,
            corner_radius=SPACING.CORNER_RADIUS,
        )
        list_frame.pack(fill="both", expand=True)

        self.doc_list_scroll = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.doc_list_scroll.pack(fill="both", expand=True, padx=5, pady=5)

    def _on_link_type_change(self, value: str) -> None:
        """Handle link type change."""
        self.link_type_var.set(self._link_type_map.get(value, LinkType.REFERENCES.value))

    def _on_search(self) -> None:
        """Handle search input change."""
        self._load_available_documents(self.search_var.get())

    def _load_available_documents(self, search_term: str = "") -> None:
        """Load available documents for linking."""
        # Clear existing list
        for widget in self.doc_list_scroll.winfo_children():
            widget.destroy()

        # Get available documents
        search = search_term.strip() if search_term else None
        self.available_docs = self.link_service.get_available_documents_for_linking(
            self.source_doc_id,
            search_term=search,
        )

        if not self.available_docs:
            ctk.CTkLabel(
                self.doc_list_scroll,
                text="No documents available for linking." if not search else "No matching documents found.",
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_SECONDARY,
            ).pack(pady=20)
            return

        # Display documents
        for doc in self.available_docs:
            self._create_doc_row(doc)

    def _create_doc_row(self, doc: dict) -> None:
        """Create a row for a document in the list."""
        is_selected = self.selected_doc and self.selected_doc["doc_id"] == doc["doc_id"]

        row = ctk.CTkFrame(
            self.doc_list_scroll,
            fg_color=COLORS.PRIMARY if is_selected else "transparent",
            corner_radius=4,
            height=40,
        )
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        # Make row clickable
        row.bind("<Button-1>", lambda e, d=doc: self._select_document(d))

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=5)
        inner.bind("<Button-1>", lambda e, d=doc: self._select_document(d))

        # Reference
        ref_label = ctk.CTkLabel(
            inner,
            text=doc["doc_ref"],
            font=TYPOGRAPHY.get_font(12, "bold"),
            text_color=COLORS.PRIMARY_FOREGROUND if is_selected else COLORS.TEXT_PRIMARY,
            width=120,
            anchor="w",
        )
        ref_label.pack(side="left")
        ref_label.bind("<Button-1>", lambda e, d=doc: self._select_document(d))

        # Title (truncated)
        title_text = doc["title"][:40] + "..." if len(doc["title"]) > 40 else doc["title"]
        title_label = ctk.CTkLabel(
            inner,
            text=title_text,
            font=TYPOGRAPHY.body,
            text_color=COLORS.PRIMARY_FOREGROUND if is_selected else COLORS.TEXT_PRIMARY,
            anchor="w",
        )
        title_label.pack(side="left", fill="x", expand=True)
        title_label.bind("<Button-1>", lambda e, d=doc: self._select_document(d))

        # Type badge
        type_label = ctk.CTkLabel(
            inner,
            text=doc["doc_type"],
            font=TYPOGRAPHY.small,
            text_color=COLORS.PRIMARY_FOREGROUND if is_selected else COLORS.TEXT_SECONDARY,
        )
        type_label.pack(side="right")
        type_label.bind("<Button-1>", lambda e, d=doc: self._select_document(d))

    def _select_document(self, doc: dict) -> None:
        """Select a document for linking."""
        self.selected_doc = doc

        # Update selected display
        self.selected_label.configure(
            text=f"Selected: {doc['doc_ref']} - {doc['title'][:50]}",
            text_color=COLORS.TEXT_PRIMARY,
        )

        # Enable link button
        self.link_btn.configure(state="normal")

        # Refresh list to show selection
        self._load_available_documents(self.search_var.get())

    def _on_create_link(self) -> None:
        """Handle create link button click."""
        if not self.selected_doc:
            InfoDialog.show_error(self, "Error", "Please select a document to link.")
            return

        link_type = self.link_type_var.get()
        target_doc_id = self.selected_doc["doc_id"]

        # Set result as tuple of (target_doc_id, link_type)
        self.result = (target_doc_id, link_type)
        self.destroy()

    def show(self) -> Optional[Tuple[str, str]]:
        """
        Show the dialog and wait for result.

        Returns:
            Tuple of (target_doc_id, link_type) or None if cancelled
        """
        self.wait_window()
        return self.result
