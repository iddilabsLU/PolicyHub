"""
PolicyHub Document Dialog

Dialog for creating and editing documents.
"""

from pathlib import Path
from tkinter import filedialog
from typing import List, Optional, Tuple

import customtkinter as ctk

from app.constants import (
    ALLOWED_EXTENSIONS,
    DocumentStatus,
    DocumentType,
    LinkType,
    MAX_FILE_SIZE_MB,
    ReviewFrequency,
)
from app.theme import COLORS, SPACING, TYPOGRAPHY, configure_button_style
from core.database import DatabaseManager
from dialogs.base_dialog import BaseDialog
from dialogs.confirm_dialog import InfoDialog
from models.category import Category
from models.document import Document, DocumentCreate, DocumentUpdate
from services.attachment_service import AttachmentService
from services.document_service import DocumentService
from services.entity_service import EntityService
from services.link_service import LinkService
from utils.dates import calculate_next_review, get_today, parse_display_date, format_date
from utils.files import format_file_size, get_file_size
from utils.validators import (
    validate_document_ref,
    validate_file_upload,
    validate_required,
    validate_version,
)


class DocumentDialog(BaseDialog):
    """
    Dialog for adding or editing a document.

    Usage:
        # Create new document
        dialog = DocumentDialog(parent, db, categories=cat_list)
        result = dialog.show()  # Returns Document or None

        # Edit existing document
        dialog = DocumentDialog(parent, db, categories=cat_list, document=doc)
        result = dialog.show()
    """

    def __init__(
        self,
        parent,
        db: DatabaseManager,
        categories: List[Category],
        document: Optional[Document] = None,
    ):
        """
        Initialize the document dialog.

        Args:
            parent: Parent window
            db: Database manager instance
            categories: List of available categories
            document: Document to edit (None for new document)
        """
        self.db = db
        self.categories = categories
        self.document = document
        self.is_edit = document is not None

        # Services
        self.doc_service = DocumentService(db)
        self.entity_service = EntityService(db)
        self.attachment_service = AttachmentService(db)
        self.link_service = LinkService(db)

        # Pending items for new documents (applied after save)
        self.pending_attachments: List[Tuple[Path, str]] = []  # (file_path, version)
        self.pending_links: List[Tuple[str, str, str]] = []  # (target_doc_id, link_type, doc_ref)

        # Get available documents for linking (exclude self if editing)
        exclude_id = document.doc_id if document else None
        self.available_docs = self.link_service.get_available_documents_for_linking(exclude_id) if self.is_edit else []

        title = "Edit Document" if self.is_edit else "Add New Document"
        super().__init__(parent, title, width=700, height=900, resizable=True)

        self._build_ui()

        if self.is_edit:
            self._populate_form()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Scrollable form
        self.form_frame = ctk.CTkScrollableFrame(
            main_frame,
            fg_color=COLORS.CARD,
            corner_radius=SPACING.CORNER_RADIUS,
        )
        self.form_frame.pack(fill="both", expand=True)

        # Build form fields
        self._build_form()

        # Footer with buttons
        footer = ctk.CTkFrame(main_frame, fg_color="transparent", height=50)
        footer.pack(fill="x", pady=(15, 0))
        footer.pack_propagate(False)

        # Cancel button
        cancel_btn = ctk.CTkButton(
            footer,
            text="Cancel",
            command=self._on_cancel,
            width=100,
            height=36,
        )
        configure_button_style(cancel_btn, "secondary")
        cancel_btn.pack(side="right", padx=5)

        # Save button
        save_btn = ctk.CTkButton(
            footer,
            text="Save Document",
            command=self._on_save,
            width=130,
            height=36,
        )
        configure_button_style(save_btn, "primary")
        save_btn.pack(side="right", padx=5)

    def _build_form(self) -> None:
        """Build all form fields."""
        form = self.form_frame
        padx = 15
        pady = 8

        # --- Document Type ---
        self._create_label(form, "Document Type *")
        type_frame = ctk.CTkFrame(form, fg_color="transparent")
        type_frame.pack(fill="x", padx=padx, pady=(0, pady))

        self.type_var = ctk.StringVar(value=DocumentType.POLICY.value)
        for doc_type in DocumentType:
            rb = ctk.CTkRadioButton(
                type_frame,
                text=doc_type.display_name,
                variable=self.type_var,
                value=doc_type.value,
                font=TYPOGRAPHY.body,
                command=self._on_type_change,
            )
            rb.pack(side="left", padx=(0, 20))

        # --- Reference and Version row ---
        row1 = ctk.CTkFrame(form, fg_color="transparent")
        row1.pack(fill="x", padx=padx, pady=pady)
        row1.columnconfigure(0, weight=2)
        row1.columnconfigure(1, weight=1)

        # Reference
        ref_frame = ctk.CTkFrame(row1, fg_color="transparent")
        ref_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self._create_label(ref_frame, "Reference Code *", pack=True)
        self.ref_var = ctk.StringVar()
        self.ref_entry = ctk.CTkEntry(
            ref_frame,
            textvariable=self.ref_var,
            height=36,
            font=TYPOGRAPHY.body,
            placeholder_text="e.g., POL-AML-001",
        )
        self.ref_entry.pack(fill="x")

        # Version
        ver_frame = ctk.CTkFrame(row1, fg_color="transparent")
        ver_frame.grid(row=0, column=1, sticky="ew")
        self._create_label(ver_frame, "Version *", pack=True)
        self.version_var = ctk.StringVar(value="1.0")
        self.version_entry = ctk.CTkEntry(
            ver_frame,
            textvariable=self.version_var,
            height=36,
            font=TYPOGRAPHY.body,
            placeholder_text="e.g., 1.0",
        )
        self.version_entry.pack(fill="x")

        # Suggest reference button
        if not self.is_edit:
            suggest_btn = ctk.CTkButton(
                ref_frame,
                text="Suggest",
                command=self._suggest_ref,
                width=70,
                height=28,
                font=TYPOGRAPHY.small,
            )
            configure_button_style(suggest_btn, "secondary")
            suggest_btn.pack(pady=(5, 0))

        # --- Title ---
        self._create_label(form, "Title *")
        self.title_var = ctk.StringVar()
        self.title_entry = ctk.CTkEntry(
            form,
            textvariable=self.title_var,
            height=36,
            font=TYPOGRAPHY.body,
            placeholder_text="Enter document title",
        )
        self.title_entry.pack(fill="x", padx=padx, pady=(0, pady))

        # --- Category and Status row ---
        row2 = ctk.CTkFrame(form, fg_color="transparent")
        row2.pack(fill="x", padx=padx, pady=pady)
        row2.columnconfigure(0, weight=1)
        row2.columnconfigure(1, weight=1)

        # Category
        cat_frame = ctk.CTkFrame(row2, fg_color="transparent")
        cat_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self._create_label(cat_frame, "Category *", pack=True)
        category_values = [f"{c.code} - {c.name}" for c in self.categories]
        self.category_var = ctk.StringVar()
        self.category_dropdown = ctk.CTkOptionMenu(
            cat_frame,
            values=category_values,
            variable=self.category_var,
            width=250,
            height=36,
            font=TYPOGRAPHY.body,
            dropdown_font=TYPOGRAPHY.body,
            command=self._on_category_change,
        )
        self.category_dropdown.pack(fill="x")
        if category_values:
            self.category_var.set(category_values[0])

        # Status
        status_frame = ctk.CTkFrame(row2, fg_color="transparent")
        status_frame.grid(row=0, column=1, sticky="ew")
        self._create_label(status_frame, "Status *", pack=True)
        status_values = [s.display_name for s in DocumentStatus]
        self.status_var = ctk.StringVar(value=DocumentStatus.ACTIVE.display_name)
        self.status_dropdown = ctk.CTkOptionMenu(
            status_frame,
            values=status_values,
            variable=self.status_var,
            width=200,
            height=36,
            font=TYPOGRAPHY.body,
            dropdown_font=TYPOGRAPHY.body,
        )
        self.status_dropdown.pack(fill="x")

        # --- Owner and Approver row ---
        row3 = ctk.CTkFrame(form, fg_color="transparent")
        row3.pack(fill="x", padx=padx, pady=pady)
        row3.columnconfigure(0, weight=1)
        row3.columnconfigure(1, weight=1)

        # Owner
        owner_frame = ctk.CTkFrame(row3, fg_color="transparent")
        owner_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self._create_label(owner_frame, "Owner *", pack=True)
        self.owner_var = ctk.StringVar()
        self.owner_entry = ctk.CTkEntry(
            owner_frame,
            textvariable=self.owner_var,
            height=36,
            font=TYPOGRAPHY.body,
            placeholder_text="Responsible person or role",
        )
        self.owner_entry.pack(fill="x")

        # Approver
        approver_frame = ctk.CTkFrame(row3, fg_color="transparent")
        approver_frame.grid(row=0, column=1, sticky="ew")
        self._create_label(approver_frame, "Approver", pack=True)
        self.approver_var = ctk.StringVar()
        self.approver_entry = ctk.CTkEntry(
            approver_frame,
            textvariable=self.approver_var,
            height=36,
            font=TYPOGRAPHY.body,
            placeholder_text="Final approver (optional)",
        )
        self.approver_entry.pack(fill="x")

        # --- Description ---
        self._create_label(form, "Description")
        self.description_text = ctk.CTkTextbox(
            form,
            height=60,
            font=TYPOGRAPHY.body,
            fg_color=COLORS.CARD,
            border_width=1,
            border_color=COLORS.BORDER,
        )
        self.description_text.pack(fill="x", padx=padx, pady=(0, pady))

        # --- Review Frequency and Dates ---
        self._create_label(form, "Review Settings")

        row4 = ctk.CTkFrame(form, fg_color="transparent")
        row4.pack(fill="x", padx=padx, pady=pady)
        row4.columnconfigure(0, weight=1)
        row4.columnconfigure(1, weight=1)
        row4.columnconfigure(2, weight=1)

        # Review Frequency
        freq_frame = ctk.CTkFrame(row4, fg_color="transparent")
        freq_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(freq_frame, text="Frequency *", font=TYPOGRAPHY.small, text_color=COLORS.TEXT_SECONDARY).pack(anchor="w")
        freq_values = [f.display_name for f in ReviewFrequency]
        self.frequency_var = ctk.StringVar(value=ReviewFrequency.ANNUAL.display_name)
        self.frequency_dropdown = ctk.CTkOptionMenu(
            freq_frame,
            values=freq_values,
            variable=self.frequency_var,
            width=150,
            height=36,
            font=TYPOGRAPHY.body,
            dropdown_font=TYPOGRAPHY.body,
            command=self._on_frequency_change,
        )
        self.frequency_dropdown.pack(fill="x")

        # Effective Date
        eff_frame = ctk.CTkFrame(row4, fg_color="transparent")
        eff_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(eff_frame, text="Effective Date *", font=TYPOGRAPHY.small, text_color=COLORS.TEXT_SECONDARY).pack(anchor="w")
        self.effective_var = ctk.StringVar(value=format_date(get_today()))
        self.effective_entry = ctk.CTkEntry(
            eff_frame,
            textvariable=self.effective_var,
            height=36,
            font=TYPOGRAPHY.body,
            placeholder_text="DD/MM/YYYY",
        )
        self.effective_entry.pack(fill="x")

        # Last Review Date
        last_frame = ctk.CTkFrame(row4, fg_color="transparent")
        last_frame.grid(row=0, column=2, sticky="ew")
        ctk.CTkLabel(last_frame, text="Last Review *", font=TYPOGRAPHY.small, text_color=COLORS.TEXT_SECONDARY).pack(anchor="w")
        self.last_review_var = ctk.StringVar(value=format_date(get_today()))
        self.last_review_entry = ctk.CTkEntry(
            last_frame,
            textvariable=self.last_review_var,
            height=36,
            font=TYPOGRAPHY.body,
            placeholder_text="DD/MM/YYYY",
        )
        self.last_review_entry.pack(fill="x")
        self.last_review_entry.bind("<FocusOut>", lambda e: self._calculate_next_review())

        # Next Review Date (calculated)
        row5 = ctk.CTkFrame(form, fg_color="transparent")
        row5.pack(fill="x", padx=padx, pady=pady)

        next_frame = ctk.CTkFrame(row5, fg_color="transparent")
        next_frame.pack(side="left")
        ctk.CTkLabel(next_frame, text="Next Review *", font=TYPOGRAPHY.small, text_color=COLORS.TEXT_SECONDARY).pack(anchor="w")
        self.next_review_var = ctk.StringVar()
        self.next_review_entry = ctk.CTkEntry(
            next_frame,
            textvariable=self.next_review_var,
            height=36,
            width=150,
            font=TYPOGRAPHY.body,
            placeholder_text="DD/MM/YYYY",
        )
        self.next_review_entry.pack()

        # Calculate button
        calc_btn = ctk.CTkButton(
            row5,
            text="Calculate",
            command=self._calculate_next_review,
            width=80,
            height=28,
            font=TYPOGRAPHY.small,
        )
        configure_button_style(calc_btn, "secondary")
        calc_btn.pack(side="left", padx=(10, 0), pady=(18, 0))

        # Auto-calculate on init
        self._calculate_next_review()

        # --- Notes ---
        self._create_label(form, "Notes")
        self.notes_text = ctk.CTkTextbox(
            form,
            height=80,
            font=TYPOGRAPHY.body,
            fg_color=COLORS.CARD,
            border_width=1,
            border_color=COLORS.BORDER,
        )
        self.notes_text.pack(fill="x", padx=padx, pady=(0, pady))

        # --- Attachments ---
        self._create_label(form, "Attachments")
        attach_container = ctk.CTkFrame(
            form,
            fg_color=COLORS.MUTED,
            corner_radius=SPACING.CORNER_RADIUS,
        )
        attach_container.pack(fill="x", padx=padx, pady=(0, pady))

        # Attachment list (scrollable if many)
        self.attachment_list_frame = ctk.CTkFrame(attach_container, fg_color="transparent")
        self.attachment_list_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Add attachment button
        add_attach_btn = ctk.CTkButton(
            attach_container,
            text="+ Add Attachment",
            command=self._on_add_attachment,
            width=140,
            height=30,
            font=TYPOGRAPHY.small,
        )
        configure_button_style(add_attach_btn, "secondary")
        add_attach_btn.pack(anchor="w", padx=10, pady=(0, 10))

        # Help text for attachments
        attach_help = f"Allowed: {', '.join(ALLOWED_EXTENSIONS[:5])}... | Max: {MAX_FILE_SIZE_MB} MB"
        ctk.CTkLabel(
            attach_container,
            text=attach_help,
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_MUTED,
        ).pack(anchor="w", padx=10, pady=(0, 10))

        # --- Linked Documents ---
        self._create_label(form, "Linked Documents")
        link_container = ctk.CTkFrame(
            form,
            fg_color=COLORS.MUTED,
            corner_radius=SPACING.CORNER_RADIUS,
        )
        link_container.pack(fill="x", padx=padx, pady=(0, pady))

        # Link list
        self.link_list_frame = ctk.CTkFrame(link_container, fg_color="transparent")
        self.link_list_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Add link button
        add_link_btn = ctk.CTkButton(
            link_container,
            text="+ Add Link",
            command=self._on_add_link,
            width=100,
            height=30,
            font=TYPOGRAPHY.small,
        )
        configure_button_style(add_link_btn, "secondary")
        add_link_btn.pack(anchor="w", padx=10, pady=(0, 10))

        # Refresh UI for any existing items (edit mode)
        self._refresh_attachment_list()
        self._refresh_link_list()

        # --- Additional Settings ---
        self._create_label(form, "Additional Settings")

        row_additional = ctk.CTkFrame(form, fg_color="transparent")
        row_additional.pack(fill="x", padx=padx, pady=pady)
        row_additional.columnconfigure(0, weight=1)
        row_additional.columnconfigure(1, weight=1)

        # Applicable Entities (multi-select with checkboxes)
        entity_frame = ctk.CTkFrame(row_additional, fg_color="transparent")
        entity_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(
            entity_frame,
            text="Applicable Entities",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY
        ).pack(anchor="w")

        # Get existing entities for checkboxes
        self._entity_names = self.entity_service.get_entity_names()
        self._entity_vars = {}

        # Display button showing selected count
        self._entity_display_var = ctk.StringVar(value="Click to select entities...")
        self.entity_button = ctk.CTkButton(
            entity_frame,
            textvariable=self._entity_display_var,
            width=250,
            height=36,
            font=TYPOGRAPHY.body,
            fg_color=COLORS.BACKGROUND,
            hover_color=COLORS.MUTED,
            text_color=COLORS.TEXT_PRIMARY,
            border_width=1,
            border_color=COLORS.BORDER,
            anchor="w",
            command=self._toggle_entity_dropdown,
        )
        self.entity_button.pack(fill="x")

        # Collapsible dropdown frame for entity selection
        self.entity_dropdown_frame = ctk.CTkFrame(
            entity_frame,
            fg_color=COLORS.CARD,
            border_width=1,
            border_color=COLORS.BORDER,
            corner_radius=8,
        )
        # Initially hidden

        # Scrollable list of entities
        entity_scroll = ctk.CTkScrollableFrame(
            self.entity_dropdown_frame,
            fg_color="transparent",
            height=100,
        )
        entity_scroll.pack(fill="x", padx=8, pady=8)

        if self._entity_names:
            for entity_name in self._entity_names:
                var = ctk.BooleanVar(value=False)
                self._entity_vars[entity_name] = var
                cb = ctk.CTkCheckBox(
                    entity_scroll,
                    text=entity_name,
                    variable=var,
                    font=TYPOGRAPHY.small,
                    text_color=COLORS.TEXT_PRIMARY,
                    command=self._update_entity_display,
                )
                cb.pack(anchor="w", pady=2)
        else:
            ctk.CTkLabel(
                entity_scroll,
                text="No entities defined yet",
                font=TYPOGRAPHY.small,
                text_color=COLORS.TEXT_MUTED,
            ).pack(anchor="w")

        # New entity entry frame
        new_entity_frame = ctk.CTkFrame(self.entity_dropdown_frame, fg_color="transparent")
        new_entity_frame.pack(fill="x", padx=8, pady=(0, 8))

        self.new_entity_entry = ctk.CTkEntry(
            new_entity_frame,
            placeholder_text="Add new entity...",
            width=180,
            height=28,
            font=TYPOGRAPHY.small,
        )
        self.new_entity_entry.pack(side="left")

        add_entity_btn = ctk.CTkButton(
            new_entity_frame,
            text="Add",
            width=50,
            height=28,
            command=self._add_new_entity,
        )
        add_entity_btn.pack(side="left", padx=(4, 0))

        # Helper text for entity field
        ctk.CTkLabel(
            entity_frame,
            text="Select multiple entities (separated by ; in reports)",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        self._entity_dropdown_visible = False
        self._entity_scroll_frame = entity_scroll  # Store reference for dynamic updates

        # Mandatory Read All checkbox
        mandatory_frame = ctk.CTkFrame(row_additional, fg_color="transparent")
        mandatory_frame.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(
            mandatory_frame,
            text="Policy Settings",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY
        ).pack(anchor="w")

        self.mandatory_var = ctk.BooleanVar(value=False)
        self.mandatory_checkbox = ctk.CTkCheckBox(
            mandatory_frame,
            text="Mandatory Read for All",
            variable=self.mandatory_var,
            font=TYPOGRAPHY.body,
            checkbox_height=20,
            checkbox_width=20,
        )
        self.mandatory_checkbox.pack(anchor="w", pady=(8, 0))

        # Helper text for mandatory
        ctk.CTkLabel(
            mandatory_frame,
            text="Employees must read this document",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

    def _create_label(self, parent, text: str, pack: bool = False) -> ctk.CTkLabel:
        """Create a form field label."""
        label = ctk.CTkLabel(
            parent,
            text=text,
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        if pack:
            label.pack(anchor="w", pady=(0, 2))
        else:
            label.pack(anchor="w", padx=15, pady=(10, 2))
        return label

    def _on_type_change(self) -> None:
        """Handle document type change."""
        if not self.is_edit:
            self._suggest_ref()

    def _on_category_change(self, value: str) -> None:
        """Handle category change."""
        if not self.is_edit:
            self._suggest_ref()

    def _on_frequency_change(self, value: str) -> None:
        """Handle frequency change."""
        self._calculate_next_review()

    def _toggle_entity_dropdown(self) -> None:
        """Toggle the entity selection dropdown visibility."""
        if self._entity_dropdown_visible:
            self.entity_dropdown_frame.pack_forget()
            self._entity_dropdown_visible = False
        else:
            self.entity_dropdown_frame.pack(fill="x", pady=(4, 0))
            self._entity_dropdown_visible = True

    def _update_entity_display(self) -> None:
        """Update the entity button display with selected count."""
        selected = [name for name, var in self._entity_vars.items() if var.get()]
        if not selected:
            self._entity_display_var.set("Click to select entities...")
        elif len(selected) == 1:
            self._entity_display_var.set(selected[0])
        else:
            self._entity_display_var.set(f"{len(selected)} entities selected")

    def _add_new_entity(self) -> None:
        """Add a new entity from the entry field."""
        new_name = self.new_entity_entry.get().strip()
        if not new_name:
            return

        # Check if already exists
        if new_name in self._entity_vars:
            # Just select it
            self._entity_vars[new_name].set(True)
            self._update_entity_display()
            self.new_entity_entry.delete(0, "end")
            return

        # Add new checkbox to the scroll frame
        var = ctk.BooleanVar(value=True)  # Auto-select the new entity
        self._entity_vars[new_name] = var
        cb = ctk.CTkCheckBox(
            self._entity_scroll_frame,
            text=new_name,
            variable=var,
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_PRIMARY,
            command=self._update_entity_display,
        )
        cb.pack(anchor="w", pady=2)

        # Update the list of entity names
        self._entity_names.append(new_name)

        # Clear the entry and update display
        self.new_entity_entry.delete(0, "end")
        self._update_entity_display()

    def _get_selected_entities(self) -> Optional[str]:
        """Get selected entities as semicolon-separated string."""
        selected = [name for name, var in self._entity_vars.items() if var.get()]
        if not selected:
            return None
        return ";".join(selected)

    def _suggest_ref(self) -> None:
        """Suggest a reference code based on type and category."""
        doc_type = self.type_var.get()
        cat_value = self.category_var.get()

        if cat_value:
            category = cat_value.split(" - ")[0]
            suggested = self.doc_service.suggest_ref(doc_type, category)
            self.ref_var.set(suggested)

    def _calculate_next_review(self) -> None:
        """Calculate and set the next review date."""
        last_review_display = self.last_review_var.get()
        last_review_iso = parse_display_date(last_review_display)

        if not last_review_iso:
            return

        # Get frequency
        freq_display = self.frequency_var.get()
        frequency = None
        for f in ReviewFrequency:
            if f.display_name == freq_display:
                frequency = f.value
                break

        if frequency:
            next_date = calculate_next_review(last_review_iso, frequency)
            if next_date:
                self.next_review_var.set(format_date(next_date))

    def _populate_form(self) -> None:
        """Populate form fields with existing document data."""
        doc = self.document

        self.type_var.set(doc.doc_type)
        self.ref_var.set(doc.doc_ref)
        self.version_var.set(doc.version)
        self.title_var.set(doc.title)

        # Find matching category display value
        for cat in self.categories:
            if cat.code == doc.category:
                self.category_var.set(f"{cat.code} - {cat.name}")
                break

        # Find matching status display value
        for status in DocumentStatus:
            if status.value == doc.status:
                self.status_var.set(status.display_name)
                break

        self.owner_var.set(doc.owner)
        self.approver_var.set(doc.approver or "")

        if doc.description:
            self.description_text.delete("1.0", "end")
            self.description_text.insert("1.0", doc.description)

        # Find matching frequency display value
        for freq in ReviewFrequency:
            if freq.value == doc.review_frequency:
                self.frequency_var.set(freq.display_name)
                break

        self.effective_var.set(format_date(doc.effective_date))
        self.last_review_var.set(format_date(doc.last_review_date))
        self.next_review_var.set(format_date(doc.next_review_date))

        if doc.notes:
            self.notes_text.delete("1.0", "end")
            self.notes_text.insert("1.0", doc.notes)

        # Set mandatory read and applicable entities
        self.mandatory_var.set(doc.mandatory_read_all)
        if doc.applicable_entity:
            # Parse semicolon-separated entities and check corresponding boxes
            entities = EntityService.parse_entities(doc.applicable_entity)
            for entity_name in entities:
                if entity_name in self._entity_vars:
                    self._entity_vars[entity_name].set(True)
                else:
                    # Entity exists in document but not in list - add it
                    var = ctk.BooleanVar(value=True)
                    self._entity_vars[entity_name] = var
                    cb = ctk.CTkCheckBox(
                        self._entity_scroll_frame,
                        text=entity_name,
                        variable=var,
                        font=TYPOGRAPHY.small,
                        text_color=COLORS.TEXT_PRIMARY,
                        command=self._update_entity_display,
                    )
                    cb.pack(anchor="w", pady=2)
            self._update_entity_display()

    def _validate_form(self) -> Tuple[bool, str]:
        """
        Validate all form fields.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Required fields
        ref_valid, ref_err = validate_required(self.ref_var.get(), "Reference code")
        if not ref_valid:
            return False, ref_err

        ref_result = validate_document_ref(self.ref_var.get())
        if not ref_result[0]:
            return False, ref_result[1]

        title_valid, title_err = validate_required(self.title_var.get(), "Title")
        if not title_valid:
            return False, title_err

        if len(self.title_var.get()) < 5:
            return False, "Title must be at least 5 characters"

        owner_valid, owner_err = validate_required(self.owner_var.get(), "Owner")
        if not owner_valid:
            return False, owner_err

        version_result = validate_version(self.version_var.get())
        if not version_result[0]:
            return False, version_result[1]

        # Validate dates
        effective = parse_display_date(self.effective_var.get())
        if not effective:
            return False, "Invalid effective date format (use DD/MM/YYYY)"

        last_review = parse_display_date(self.last_review_var.get())
        if not last_review:
            return False, "Invalid last review date format (use DD/MM/YYYY)"

        next_review = parse_display_date(self.next_review_var.get())
        if not next_review:
            return False, "Invalid next review date format (use DD/MM/YYYY)"

        # Check reference uniqueness (for new documents)
        if not self.is_edit:
            if self.doc_service.doc_ref_exists(self.ref_var.get()):
                return False, f"Reference '{self.ref_var.get()}' already exists"
        else:
            if self.doc_service.doc_ref_exists(self.ref_var.get(), exclude_id=self.document.doc_id):
                return False, f"Reference '{self.ref_var.get()}' already exists"

        return True, ""

    # --- Attachment Methods ---

    def _on_add_attachment(self) -> None:
        """Handle add attachment button click."""
        # Build file type filter
        file_types = [
            ("All supported files", " ".join(f"*{ext}" for ext in ALLOWED_EXTENSIONS)),
            ("PDF files", "*.pdf"),
            ("Word documents", "*.doc *.docx"),
            ("Excel spreadsheets", "*.xls *.xlsx"),
            ("All files", "*.*"),
        ]

        file_path = filedialog.askopenfilename(
            parent=self,
            title="Select File to Attach",
            filetypes=file_types,
        )

        if file_path:
            path = Path(file_path)
            if not path.exists():
                InfoDialog.show_error(self, "Error", "Selected file does not exist.")
                return

            # Validate file
            file_size = get_file_size(path)
            is_valid, error = validate_file_upload(path.name, file_size)
            if not is_valid:
                InfoDialog.show_error(self, "Invalid File", error)
                return

            # Get version label (default to current version field)
            version = self.version_var.get().strip() or "1.0"

            # Add to pending list
            self.pending_attachments.append((path, version))
            self._refresh_attachment_list()

    def _remove_pending_attachment(self, index: int) -> None:
        """Remove a pending attachment by index."""
        if 0 <= index < len(self.pending_attachments):
            self.pending_attachments.pop(index)
            self._refresh_attachment_list()

    def _refresh_attachment_list(self) -> None:
        """Refresh the attachment list display."""
        # Clear existing items
        for widget in self.attachment_list_frame.winfo_children():
            widget.destroy()

        if not self.pending_attachments:
            ctk.CTkLabel(
                self.attachment_list_frame,
                text="No attachments added",
                font=TYPOGRAPHY.small,
                text_color=COLORS.TEXT_MUTED,
            ).pack(anchor="w")
            return

        # Display pending attachments
        for idx, (path, version) in enumerate(self.pending_attachments):
            row = ctk.CTkFrame(self.attachment_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            # File info
            size_str = format_file_size(get_file_size(path))
            ctk.CTkLabel(
                row,
                text=f"{path.name} ({size_str}) - v{version}",
                font=TYPOGRAPHY.small,
                text_color=COLORS.TEXT_PRIMARY,
            ).pack(side="left")

            # Remove button
            remove_btn = ctk.CTkButton(
                row,
                text="×",
                command=lambda i=idx: self._remove_pending_attachment(i),
                width=24,
                height=24,
                font=TYPOGRAPHY.small,
                fg_color=COLORS.DESTRUCTIVE,
                hover_color="#dc2626",
            )
            remove_btn.pack(side="right")

    # --- Link Methods ---

    def _on_add_link(self) -> None:
        """Handle add link button click."""
        # For new documents, we need to get available docs fresh
        if not self.is_edit:
            self.available_docs = self.link_service.get_available_documents_for_linking(None)

        # Filter out already linked docs
        linked_ids = {link[0] for link in self.pending_links}
        available = [d for d in self.available_docs if d["doc_id"] not in linked_ids]

        if not available:
            InfoDialog.show_info(self, "No Documents", "No documents available for linking.")
            return

        # Show link selection dialog
        dialog = LinkSelectionDialog(
            self,
            available_docs=available,
        )
        result = dialog.show()

        if result:
            target_doc_id, link_type, target_ref = result
            self.pending_links.append((target_doc_id, link_type, target_ref))
            self._refresh_link_list()

    def _remove_pending_link(self, index: int) -> None:
        """Remove a pending link by index."""
        if 0 <= index < len(self.pending_links):
            self.pending_links.pop(index)
            self._refresh_link_list()

    def _refresh_link_list(self) -> None:
        """Refresh the link list display."""
        # Clear existing items
        for widget in self.link_list_frame.winfo_children():
            widget.destroy()

        if not self.pending_links:
            ctk.CTkLabel(
                self.link_list_frame,
                text="No linked documents",
                font=TYPOGRAPHY.small,
                text_color=COLORS.TEXT_MUTED,
            ).pack(anchor="w")
            return

        # Display pending links
        for idx, (doc_id, link_type, doc_ref) in enumerate(self.pending_links):
            row = ctk.CTkFrame(self.link_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            # Link info
            link_type_display = link_type.replace("_", " ").title()
            ctk.CTkLabel(
                row,
                text=f"{doc_ref} ({link_type_display})",
                font=TYPOGRAPHY.small,
                text_color=COLORS.TEXT_PRIMARY,
            ).pack(side="left")

            # Remove button
            remove_btn = ctk.CTkButton(
                row,
                text="×",
                command=lambda i=idx: self._remove_pending_link(i),
                width=24,
                height=24,
                font=TYPOGRAPHY.small,
                fg_color=COLORS.DESTRUCTIVE,
                hover_color="#dc2626",
            )
            remove_btn.pack(side="right")

    def _get_form_data(self) -> dict:
        """Get form data as a dictionary."""
        # Get category code from display value
        cat_display = self.category_var.get()
        category = cat_display.split(" - ")[0] if cat_display else ""

        # Get status value from display name
        status_display = self.status_var.get()
        status = DocumentStatus.ACTIVE.value
        for s in DocumentStatus:
            if s.display_name == status_display:
                status = s.value
                break

        # Get frequency value from display name
        freq_display = self.frequency_var.get()
        frequency = ReviewFrequency.ANNUAL.value
        for f in ReviewFrequency:
            if f.display_name == freq_display:
                frequency = f.value
                break

        # Get applicable entities (semicolon-separated)
        entity_value = self._get_selected_entities()

        return {
            "doc_type": self.type_var.get(),
            "doc_ref": self.ref_var.get().upper(),
            "title": self.title_var.get().strip(),
            "category": category,
            "owner": self.owner_var.get().strip(),
            "approver": self.approver_var.get().strip() or None,
            "status": status,
            "version": self.version_var.get().strip(),
            "description": self.description_text.get("1.0", "end-1c").strip() or None,
            "review_frequency": frequency,
            "effective_date": parse_display_date(self.effective_var.get()),
            "last_review_date": parse_display_date(self.last_review_var.get()),
            "next_review_date": parse_display_date(self.next_review_var.get()),
            "notes": self.notes_text.get("1.0", "end-1c").strip() or None,
            "mandatory_read_all": self.mandatory_var.get(),
            "applicable_entity": entity_value,
        }

    def _on_save(self) -> None:
        """Handle save button click."""
        is_valid, error = self._validate_form()
        if not is_valid:
            InfoDialog.show_error(self, "Validation Error", error)
            return

        try:
            data = self._get_form_data()

            # Ensure all selected entities exist (create if new)
            if data.get("applicable_entity"):
                self.entity_service.ensure_entities_exist(data["applicable_entity"])

            if self.is_edit:
                update_data = DocumentUpdate(**{k: v for k, v in data.items() if k != "doc_type" and k != "doc_ref"})
                self.result = self.doc_service.update_document(self.document.doc_id, update_data)
                doc_id = self.document.doc_id
            else:
                create_data = DocumentCreate(**data)
                self.result = self.doc_service.create_document(create_data)
                doc_id = self.result.doc_id

            # Get doc_ref for attachments
            doc_ref = self.result.doc_ref if self.result else self.document.doc_ref

            # Apply pending attachments
            for file_path, version in self.pending_attachments:
                try:
                    self.attachment_service.add_attachment(
                        doc_id=doc_id,
                        doc_ref=doc_ref,
                        source_path=file_path,
                        version_label=version,
                    )
                except Exception as e:
                    InfoDialog.show_error(
                        self,
                        "Attachment Error",
                        f"Failed to add {file_path.name}: {str(e)}"
                    )

            # Apply pending links
            for target_doc_id, link_type, _ in self.pending_links:
                try:
                    self.link_service.create_link(doc_id, target_doc_id, link_type)
                except Exception as e:
                    InfoDialog.show_error(
                        self,
                        "Link Error",
                        f"Failed to create link: {str(e)}"
                    )

            self.destroy()

        except PermissionError as e:
            InfoDialog.show_error(self, "Permission Denied", str(e))
        except ValueError as e:
            InfoDialog.show_error(self, "Error", str(e))
        except Exception as e:
            InfoDialog.show_error(self, "Error", f"Failed to save document: {str(e)}")


class LinkSelectionDialog(BaseDialog):
    """
    Simple dialog for selecting a document to link.

    Returns (target_doc_id, link_type, doc_ref) or None.
    """

    def __init__(self, parent, available_docs: List[dict]):
        """
        Initialize the link selection dialog.

        Args:
            parent: Parent window
            available_docs: List of documents available for linking
        """
        self.available_docs = available_docs
        self.selected_doc: Optional[dict] = None

        super().__init__(parent, "Select Document to Link", width=500, height=450)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Buttons at bottom first
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(side="bottom", fill="x", pady=(15, 0))

        self.link_btn = ctk.CTkButton(
            button_frame,
            text="Add Link",
            command=self._on_add,
            width=100,
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

        # Content area
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(side="top", fill="both", expand=True)

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
            (LinkType.IMPLEMENTS.value, "Implements"),
            (LinkType.REFERENCES.value, "References"),
            (LinkType.SUPERSEDES.value, "Supersedes"),
        ]

        self.link_type_var = ctk.StringVar(value=LinkType.REFERENCES.value)
        self.link_type_dropdown = ctk.CTkOptionMenu(
            type_frame,
            values=[t[1] for t in link_types],
            variable=ctk.StringVar(value="References"),
            width=200,
            height=36,
            font=TYPOGRAPHY.body,
            dropdown_font=TYPOGRAPHY.body,
            command=self._on_link_type_change,
        )
        self.link_type_dropdown.pack(side="left")
        self._link_type_map = {t[1]: t[0] for t in link_types}

        # Search
        search_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_docs())
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            height=36,
            font=TYPOGRAPHY.body,
            placeholder_text="Search documents...",
        )
        search_entry.pack(fill="x")

        # Document list
        list_frame = ctk.CTkFrame(
            content_frame,
            fg_color=COLORS.CARD,
            corner_radius=SPACING.CORNER_RADIUS,
        )
        list_frame.pack(fill="both", expand=True)

        self.doc_list_scroll = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.doc_list_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        self._filter_docs()

    def _on_link_type_change(self, value: str) -> None:
        """Handle link type change."""
        self.link_type_var.set(self._link_type_map.get(value, LinkType.REFERENCES.value))

    def _filter_docs(self) -> None:
        """Filter and display documents."""
        for widget in self.doc_list_scroll.winfo_children():
            widget.destroy()

        search = self.search_var.get().lower()
        filtered = [
            d for d in self.available_docs
            if not search or search in d["doc_ref"].lower() or search in d["title"].lower()
        ]

        if not filtered:
            ctk.CTkLabel(
                self.doc_list_scroll,
                text="No documents found",
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_SECONDARY,
            ).pack(pady=20)
            return

        for doc in filtered:
            self._create_doc_row(doc)

    def _create_doc_row(self, doc: dict) -> None:
        """Create a row for a document."""
        is_selected = self.selected_doc and self.selected_doc["doc_id"] == doc["doc_id"]

        row = ctk.CTkFrame(
            self.doc_list_scroll,
            fg_color=COLORS.PRIMARY if is_selected else "transparent",
            corner_radius=4,
            height=36,
            cursor="hand2",
        )
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)
        row.bind("<Button-1>", lambda e, d=doc: self._select_doc(d))

        inner = ctk.CTkFrame(row, fg_color="transparent", cursor="hand2")
        inner.pack(fill="x", padx=10, pady=6)
        inner.bind("<Button-1>", lambda e, d=doc: self._select_doc(d))

        ref_label = ctk.CTkLabel(
            inner,
            text=doc["doc_ref"],
            font=TYPOGRAPHY.get_font(12, "bold"),
            text_color=COLORS.PRIMARY_FOREGROUND if is_selected else COLORS.TEXT_PRIMARY,
            width=100,
            anchor="w",
            cursor="hand2",
        )
        ref_label.pack(side="left")
        ref_label.bind("<Button-1>", lambda e, d=doc: self._select_doc(d))

        title_text = doc["title"][:35] + "..." if len(doc["title"]) > 35 else doc["title"]
        title_label = ctk.CTkLabel(
            inner,
            text=title_text,
            font=TYPOGRAPHY.body,
            text_color=COLORS.PRIMARY_FOREGROUND if is_selected else COLORS.TEXT_PRIMARY,
            anchor="w",
            cursor="hand2",
        )
        title_label.pack(side="left", fill="x", expand=True)
        title_label.bind("<Button-1>", lambda e, d=doc: self._select_doc(d))

    def _select_doc(self, doc: dict) -> None:
        """Select a document."""
        self.selected_doc = doc
        self.link_btn.configure(state="normal")
        self._filter_docs()

    def _on_add(self) -> None:
        """Handle add button click."""
        if self.selected_doc:
            link_type = self.link_type_var.get()
            self.result = (
                self.selected_doc["doc_id"],
                link_type,
                self.selected_doc["doc_ref"],
            )
            self.destroy()

    def show(self) -> Optional[Tuple[str, str, str]]:
        """
        Show the dialog and wait for result.

        Returns:
            Tuple of (target_doc_id, link_type, doc_ref) or None
        """
        self.wait_window()
        return self.result
