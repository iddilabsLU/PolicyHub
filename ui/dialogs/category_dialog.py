"""
PolicyHub Category Dialog (PySide6)

Dialog for adding and editing document categories.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button
from core.database import DatabaseManager
from models.category import Category, CategoryCreate, CategoryUpdate
from services.category_service import CategoryService
from ui.dialogs.base_dialog import BaseDialog
from ui.dialogs.confirm_dialog import InfoDialog


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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING
        )
        layout.setSpacing(0)

        # Code field
        self._create_label(layout, "Category Code *")
        self.code_entry = QLineEdit()
        self.code_entry.setPlaceholderText("e.g., AML, GOV")
        self.code_entry.setFixedWidth(150)
        self.code_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        layout.addWidget(self.code_entry)
        layout.addSpacing(4)

        if self.is_edit_mode:
            self.code_entry.setText(self.category.code)
            self.code_entry.setEnabled(False)
            layout.addSpacing(8)
        else:
            # Hint for code
            hint = QLabel("2-10 uppercase letters, cannot be changed later")
            hint.setFont(TYPOGRAPHY.small)
            hint.setStyleSheet(f"color: {COLORS.TEXT_MUTED};")
            layout.addWidget(hint)
            layout.addSpacing(12)

        # Name field
        self._create_label(layout, "Category Name *")
        self.name_entry = QLineEdit()
        self.name_entry.setPlaceholderText("e.g., Anti-Money Laundering & CFT")
        self.name_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        layout.addWidget(self.name_entry)
        layout.addSpacing(12)

        if self.is_edit_mode:
            self.name_entry.setText(self.category.name)

        # Sort Order field
        self._create_label(layout, "Sort Order")
        self.sort_entry = QLineEdit()
        self.sort_entry.setPlaceholderText("99")
        self.sort_entry.setFixedWidth(100)
        self.sort_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        layout.addWidget(self.sort_entry)
        layout.addSpacing(4)

        if self.is_edit_mode:
            self.sort_entry.setText(str(self.category.sort_order))
        else:
            self.sort_entry.setText("99")

        hint = QLabel("Lower numbers appear first in lists")
        hint.setFont(TYPOGRAPHY.small)
        hint.setStyleSheet(f"color: {COLORS.TEXT_MUTED};")
        layout.addWidget(hint)

        layout.addStretch()

        # Button frame
        btn_frame = QWidget()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)

        btn_layout.addStretch()

        save_btn = QPushButton("Save" if self.is_edit_mode else "Create Category")
        save_btn.setFixedWidth(140)
        save_btn.clicked.connect(self._on_save)
        style_button(save_btn, "primary")
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self._on_cancel)
        style_button(cancel_btn, "secondary")
        btn_layout.addWidget(cancel_btn)

        layout.addWidget(btn_frame)

    def _create_label(self, layout: QVBoxLayout, text: str) -> None:
        """Create a field label."""
        label = QLabel(text)
        label.setFont(TYPOGRAPHY.body)
        label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        layout.addWidget(label)
        layout.addSpacing(4)

    def _on_save(self) -> None:
        """Handle save button click."""
        # Validate code
        code = self.code_entry.text().strip().upper()
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
        name = self.name_entry.text().strip()
        if not name or len(name) < 2:
            InfoDialog.show_error(self, "Invalid Name", "Category name must be at least 2 characters.")
            return

        if len(name) > 100:
            InfoDialog.show_error(self, "Invalid Name", "Category name must be 100 characters or less.")
            return

        # Validate sort order
        sort_str = self.sort_entry.text().strip() or "99"
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

            self.accept()

        except PermissionError:
            InfoDialog.show_error(self, "Permission Denied", "You do not have permission to manage categories.")
        except ValueError as e:
            InfoDialog.show_error(self, "Validation Error", str(e))
        except Exception as e:
            InfoDialog.show_error(self, "Error", str(e))
