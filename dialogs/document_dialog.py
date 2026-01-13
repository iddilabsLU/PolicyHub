"""
PolicyHub Document Dialog

Dialog for creating and editing documents.
"""

from typing import List, Optional, Tuple

import customtkinter as ctk

from app.constants import DocumentStatus, DocumentType, ReviewFrequency
from app.theme import COLORS, SPACING, TYPOGRAPHY, configure_button_style
from core.database import DatabaseManager
from dialogs.base_dialog import BaseDialog
from dialogs.confirm_dialog import InfoDialog
from models.category import Category
from models.document import Document, DocumentCreate, DocumentUpdate
from services.document_service import DocumentService
from services.entity_service import EntityService
from utils.dates import calculate_next_review, get_today, parse_display_date, format_date
from utils.validators import (
    validate_document_ref,
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

        title = "Edit Document" if self.is_edit else "Add New Document"
        super().__init__(parent, title, width=700, height=750, resizable=True)

        self.doc_service = DocumentService(db)
        self.entity_service = EntityService(db)
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

        # --- Additional Settings ---
        self._create_label(form, "Additional Settings")

        row_additional = ctk.CTkFrame(form, fg_color="transparent")
        row_additional.pack(fill="x", padx=padx, pady=pady)
        row_additional.columnconfigure(0, weight=1)
        row_additional.columnconfigure(1, weight=1)

        # Applicable Entity (combobox that allows new entries)
        entity_frame = ctk.CTkFrame(row_additional, fg_color="transparent")
        entity_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(
            entity_frame,
            text="Applicable Entity",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY
        ).pack(anchor="w")

        # Get existing entities for dropdown
        entity_names = self.entity_service.get_entity_names()
        self.entity_var = ctk.StringVar()
        self.entity_combobox = ctk.CTkComboBox(
            entity_frame,
            values=entity_names,
            variable=self.entity_var,
            width=250,
            height=36,
            font=TYPOGRAPHY.body,
            dropdown_font=TYPOGRAPHY.body,
        )
        self.entity_combobox.pack(fill="x")
        self.entity_combobox.set("")  # Start empty

        # Helper text for entity field
        ctk.CTkLabel(
            entity_frame,
            text="Select or type a new entity",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

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

        # Set mandatory read and applicable entity
        self.mandatory_var.set(doc.mandatory_read_all)
        if doc.applicable_entity:
            self.entity_var.set(doc.applicable_entity)

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

        # Get applicable entity (may be new or existing)
        entity_value = self.entity_var.get().strip() if self.entity_var.get() else None

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

            # If an entity was entered, ensure it exists (create if new)
            if data.get("applicable_entity"):
                self.entity_service.get_or_create_entity(data["applicable_entity"])

            if self.is_edit:
                update_data = DocumentUpdate(**{k: v for k, v in data.items() if k != "doc_type" and k != "doc_ref"})
                self.result = self.doc_service.update_document(self.document.doc_id, update_data)
            else:
                create_data = DocumentCreate(**data)
                self.result = self.doc_service.create_document(create_data)

            self.destroy()

        except PermissionError as e:
            InfoDialog.show_error(self, "Permission Denied", str(e))
        except ValueError as e:
            InfoDialog.show_error(self, "Error", str(e))
        except Exception as e:
            InfoDialog.show_error(self, "Error", f"Failed to save document: {str(e)}")
