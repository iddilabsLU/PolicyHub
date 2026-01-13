"""
PolicyHub Category Dialog

Dialog for adding and editing document categories.
"""

from typing import Optional

import customtkinter as ctk

from app.theme import (
    COLORS,
    SPACING,
    TYPOGRAPHY,
    configure_button_style,
    configure_input_style,
)
from core.database import DatabaseManager
from dialogs.base_dialog import BaseDialog
from dialogs.confirm_dialog import InfoDialog
from models.category import Category, CategoryCreate, CategoryUpdate
from services.category_service import CategoryService


class CategoryDialog(BaseDialog):
    """
    Dialog for adding or editing a category.

    In add mode: Shows code and name fields
    In edit mode: Code is read-only, can edit name and sort order
    """

    def __init__(
        self,
        parent,
        db: DatabaseManager,
        category: Optional[Category] = None,
    ):
        """
        Initialize the category dialog.

        Args:
            parent: Parent window
            db: Database manager
            category: Category to edit (None for add mode)
        """
        self.db = db
        self.category_service = CategoryService(db)
        self.category = category
        self.is_edit_mode = category is not None

        title = "Edit Category" if self.is_edit_mode else "Add Category"

        super().__init__(parent, title, width=400, height=320)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        # Form container
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING)

        # Code field
        self._create_label(form, "Category Code *")
        self.code_entry = ctk.CTkEntry(
            form,
            width=150,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
            placeholder_text="e.g., AML, GOV",
        )
        configure_input_style(self.code_entry)
        self.code_entry.pack(anchor="w", pady=(0, 12))

        if self.is_edit_mode:
            self.code_entry.insert(0, self.category.code)
            self.code_entry.configure(state="disabled")
        else:
            # Hint for code
            hint = ctk.CTkLabel(
                form,
                text="2-10 uppercase letters, cannot be changed later",
                font=TYPOGRAPHY.small,
                text_color=COLORS.TEXT_MUTED,
            )
            hint.pack(anchor="w", pady=(0, 12))

        # Name field
        self._create_label(form, "Category Name *")
        self.name_entry = ctk.CTkEntry(
            form,
            width=300,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
            placeholder_text="e.g., Anti-Money Laundering & CFT",
        )
        configure_input_style(self.name_entry)
        self.name_entry.pack(anchor="w", pady=(0, 12))

        if self.is_edit_mode:
            self.name_entry.insert(0, self.category.name)

        # Sort Order field
        self._create_label(form, "Sort Order")
        self.sort_entry = ctk.CTkEntry(
            form,
            width=100,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
            placeholder_text="99",
        )
        configure_input_style(self.sort_entry)
        self.sort_entry.pack(anchor="w", pady=(0, 4))

        if self.is_edit_mode:
            self.sort_entry.insert(0, str(self.category.sort_order))
        else:
            self.sort_entry.insert(0, "99")

        hint = ctk.CTkLabel(
            form,
            text="Lower numbers appear first in lists",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_MUTED,
        )
        hint.pack(anchor="w", pady=(0, 12))

        # Button frame
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING.WINDOW_PADDING, pady=(0, SPACING.WINDOW_PADDING))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self._on_cancel,
            width=100,
        )
        configure_button_style(cancel_btn, "secondary")
        cancel_btn.pack(side="right", padx=(8, 0))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save" if self.is_edit_mode else "Create Category",
            command=self._on_save,
            width=140,
        )
        configure_button_style(save_btn, "primary")
        save_btn.pack(side="right")

    def _create_label(self, parent, text: str) -> None:
        """Create a field label."""
        label = ctk.CTkLabel(
            parent,
            text=text,
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        label.pack(anchor="w", pady=(0, 4))

    def _on_save(self) -> None:
        """Handle save button click."""
        # Validate code
        code = self.code_entry.get().strip().upper()
        if not self.is_edit_mode:
            if not code or len(code) < 2:
                InfoDialog.show_error(self, "Invalid Code", "Category code must be at least 2 characters.")
                return

            if len(code) > 10:
                InfoDialog.show_error(self, "Invalid Code", "Category code must be 10 characters or less.")
                return

            if not code.isalpha():
                InfoDialog.show_error(self, "Invalid Code", "Category code must contain only letters.")
                return

            # Check if code exists
            if self.category_service.code_exists(code):
                InfoDialog.show_error(self, "Code Exists", f"Category code '{code}' is already in use.")
                return

        # Validate name
        name = self.name_entry.get().strip()
        if not name or len(name) < 2:
            InfoDialog.show_error(self, "Invalid Name", "Category name must be at least 2 characters.")
            return

        if len(name) > 100:
            InfoDialog.show_error(self, "Invalid Name", "Category name must be 100 characters or less.")
            return

        # Validate sort order
        sort_str = self.sort_entry.get().strip() or "99"
        try:
            sort_order = int(sort_str)
            if sort_order < 0 or sort_order > 999:
                raise ValueError()
        except ValueError:
            InfoDialog.show_error(self, "Invalid Sort Order", "Sort order must be a number between 0 and 999.")
            return

        try:
            if self.is_edit_mode:
                # Update category
                update_data = CategoryUpdate(
                    name=name,
                    sort_order=sort_order,
                )
                self.category_service.update_category(self.category.code, update_data)
                self.result = True
            else:
                # Create category
                create_data = CategoryCreate(
                    code=code,
                    name=name,
                    sort_order=sort_order,
                )
                self.category_service.create_category(create_data)
                self.result = True

            self.destroy()

        except PermissionError:
            InfoDialog.show_error(self, "Permission Denied", "You do not have permission to manage categories.")
        except ValueError as e:
            InfoDialog.show_error(self, "Validation Error", str(e))
        except Exception as e:
            InfoDialog.show_error(self, "Error", str(e))
