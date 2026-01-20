"""
PolicyHub Categories Settings View

Category management view for administrators to add, edit, and manage document categories.
"""

from typing import TYPE_CHECKING, List

import customtkinter as ctk

from app.theme import (
    COLORS,
    SPACING,
    TYPOGRAPHY,
    configure_button_style,
    configure_card_style,
)
from dialogs.confirm_dialog import ConfirmDialog, InfoDialog
from models.category import Category
from services.category_service import CategoryService
from views.base_view import BaseView

if TYPE_CHECKING:
    from app.application import PolicyHubApp

# Try to import tksheet
try:
    from tksheet import Sheet
    TKSHEET_AVAILABLE = True
except ImportError:
    TKSHEET_AVAILABLE = False


class CategoriesSettingsView(BaseView):
    """
    Category management view for administrators.

    Features:
    - View all categories in a table
    - Add new categories
    - Edit existing categories
    - Activate/deactivate categories (if no documents assigned)
    """

    def __init__(self, parent: ctk.CTkFrame, app: "PolicyHubApp"):
        """
        Initialize the categories settings view.

        Args:
            parent: Parent widget
            app: Main application instance
        """
        super().__init__(parent, app)
        self.category_service = CategoryService(app.db)
        self.categories: List[Category] = []
        self.usage_stats: dict = {}
        self.show_inactive = False
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the categories management UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING.WINDOW_PADDING, pady=(SPACING.WINDOW_PADDING, 10))

        title = ctk.CTkLabel(
            header,
            text="Category Management",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title.pack(side="left")

        # Add button
        add_btn = ctk.CTkButton(
            header,
            text="+ Add Category",
            command=self._on_add_category,
            width=140,
        )
        configure_button_style(add_btn, "primary")
        add_btn.pack(side="right")

        # Show inactive toggle
        self.inactive_var = ctk.BooleanVar(value=False)
        inactive_check = ctk.CTkCheckBox(
            header,
            text="Show inactive categories",
            variable=self.inactive_var,
            command=self._refresh_table,
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        )
        inactive_check.pack(side="right", padx=(0, 20))

        # Table container
        table_card = ctk.CTkFrame(self, fg_color=COLORS.CARD)
        configure_card_style(table_card, with_shadow=True)
        table_card.pack(
            fill="both",
            expand=True,
            padx=SPACING.WINDOW_PADDING,
            pady=(0, SPACING.WINDOW_PADDING),
        )

        # Build table
        if TKSHEET_AVAILABLE:
            self._build_tksheet_table(table_card)
        else:
            self._build_fallback_table(table_card)

        # Status bar
        self.status_label = ctk.CTkLabel(
            table_card,
            text="Loading...",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        )
        self.status_label.pack(side="bottom", anchor="w", padx=SPACING.CARD_PADDING, pady=8)

    def _build_tksheet_table(self, parent) -> None:
        """Build the tksheet table."""
        self.table_card = parent  # Store reference for resize calculations

        self.table = Sheet(
            parent,
            headers=["Code", "Name", "Documents", "Sort Order", "Status"],
            header_bg=COLORS.MUTED,
            header_fg=COLORS.TEXT_PRIMARY,
            header_font=("Segoe UI", 11, "bold"),
            header_grid_fg=COLORS.BORDER,
            table_bg=COLORS.CARD,
            table_fg=COLORS.TEXT_PRIMARY,
            font=("Segoe UI", 11, "normal"),
            table_grid_fg=COLORS.BORDER,
            table_selected_cells_bg=COLORS.PRIMARY,
            table_selected_cells_fg=COLORS.PRIMARY_FOREGROUND,
            index_bg=COLORS.MUTED,
            top_left_bg=COLORS.MUTED,
            outline_thickness=1,
            outline_color=COLORS.BORDER,
            frame_bg=COLORS.CARD,
            show_row_index=False,
            show_top_left=False,
            default_row_height=36,
        )
        self.table.pack(fill="both", expand=True, padx=SPACING.CARD_PADDING, pady=(SPACING.CARD_PADDING, 0))

        # Enable features
        self.table.enable_bindings(
            "single_select",
            "row_select",
            "column_width_resize",
            "arrowkeys",
        )

        # Enable text wrapping for better display of long text
        self.table.set_options(
            auto_resize_row_height=True,  # Auto-resize rows for wrapped text
        )

        # Column proportions (weights) - Name gets the most space
        # [Code, Name, Documents, Sort Order, Status]
        self._column_weights = [0.8, 2.5, 0.8, 0.8, 0.8]
        self._column_min_widths = [80, 180, 80, 80, 80]

        # Set initial column widths
        self._resize_columns()

        # Bind to configure event for responsive resizing
        parent.bind("<Configure>", self._on_container_resize)
        self._resize_scheduled = False

        # Double-click to edit
        self.table.bind("<Double-Button-1>", self._on_double_click)

        # Right-click context menu
        self.table.bind("<Button-3>", self._show_context_menu)

    def _on_container_resize(self, event=None) -> None:
        """Handle container resize - debounced."""
        if not hasattr(self, '_resize_scheduled'):
            self._resize_scheduled = False
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
            available_width = self.table_card.winfo_width() - (SPACING.CARD_PADDING * 2) - 20

            if available_width < 400:  # Not yet rendered or too small
                # Use fallback widths
                fallback_widths = [100, 250, 100, 100, 100]
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

    def _build_fallback_table(self, parent) -> None:
        """Build a fallback table without tksheet."""
        self.table_scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.table_scroll.pack(fill="both", expand=True, padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        # Header row
        header = ctk.CTkFrame(self.table_scroll, fg_color=COLORS.MUTED)
        header.pack(fill="x")

        headers = ["Code", "Name", "Documents", "Status"]
        for text in headers:
            ctk.CTkLabel(
                header,
                text=text,
                font=TYPOGRAPHY.get_font(11, "bold"),
                width=150,
                anchor="w",
            ).pack(side="left", padx=10, pady=8)

        self.table = None

    def _update_fallback_table(self) -> None:
        """Update the fallback table."""
        # Clear existing rows
        children = self.table_scroll.winfo_children()
        for child in children[1:]:
            child.destroy()

        for cat in self.categories:
            row = ctk.CTkFrame(self.table_scroll, fg_color="transparent", cursor="hand2")
            row.pack(fill="x")
            row.bind("<Double-Button-1>", lambda e, c=cat: self._edit_category(c))

            doc_count = self.usage_stats.get(cat.code, 0)
            values = [
                cat.code,
                cat.name,
                str(doc_count),
                "Active" if cat.is_active else "Inactive",
            ]

            for val in values:
                label = ctk.CTkLabel(
                    row,
                    text=val,
                    font=TYPOGRAPHY.body,
                    width=150,
                    anchor="w",
                )
                label.pack(side="left", padx=10, pady=6)
                label.bind("<Double-Button-1>", lambda e, c=cat: self._edit_category(c))

            divider = ctk.CTkFrame(self.table_scroll, fg_color=COLORS.BORDER, height=1)
            divider.pack(fill="x")

    def _refresh_table(self) -> None:
        """Reload category data."""
        self.show_inactive = self.inactive_var.get()
        self.categories = self.category_service.get_all_categories(include_inactive=self.show_inactive)
        self.usage_stats = self.category_service.get_category_usage_stats()

        if TKSHEET_AVAILABLE and self.table:
            data = []
            for cat in self.categories:
                doc_count = self.usage_stats.get(cat.code, 0)
                data.append([
                    cat.code,
                    cat.name,
                    str(doc_count),
                    str(cat.sort_order),
                    "Active" if cat.is_active else "Inactive",
                ])
            self.table.set_sheet_data(data)
        else:
            self._update_fallback_table()

        self.status_label.configure(text=f"Showing {len(self.categories)} category(s)")

    def _on_add_category(self) -> None:
        """Handle add category button click."""
        from dialogs.category_dialog import CategoryDialog

        dialog = CategoryDialog(self.winfo_toplevel(), self.app.db)
        result = dialog.show()
        if result:
            self._refresh_table()

    def _on_double_click(self, event) -> None:
        """Handle double-click on table row."""
        if not TKSHEET_AVAILABLE or not self.table:
            return

        selected = self.table.get_currently_selected()
        if selected and len(self.categories) > 0:
            row = selected.row
            if 0 <= row < len(self.categories):
                self._edit_category(self.categories[row])

    def _edit_category(self, category: Category) -> None:
        """Open edit dialog for a category."""
        from dialogs.category_dialog import CategoryDialog

        dialog = CategoryDialog(self.winfo_toplevel(), self.app.db, category=category)
        result = dialog.show()
        if result:
            self._refresh_table()

    def _show_context_menu(self, event) -> None:
        """Show context menu on right-click."""
        if not TKSHEET_AVAILABLE or not self.table:
            return

        # Get clicked row
        try:
            row = self.table.identify_row(event, allow_end=False)
            if row is None or row >= len(self.categories):
                return
            category = self.categories[row]
        except Exception:
            return

        # Create context menu
        menu = ctk.CTkFrame(
            self.winfo_toplevel(),
            fg_color=COLORS.CARD,
            border_width=1,
            border_color=COLORS.BORDER,
            corner_radius=SPACING.CORNER_RADIUS,
        )

        # Menu items
        edit_btn = ctk.CTkButton(
            menu,
            text="Edit Category",
            command=lambda: [menu.destroy(), self._edit_category(category)],
            fg_color="transparent",
            text_color=COLORS.TEXT_PRIMARY,
            hover_color=COLORS.MUTED,
            anchor="w",
            height=32,
        )
        edit_btn.pack(fill="x", padx=4, pady=2)

        doc_count = self.usage_stats.get(category.code, 0)

        if category.is_active:
            deactivate_btn = ctk.CTkButton(
                menu,
                text="Deactivate" if doc_count == 0 else f"Deactivate ({doc_count} docs)",
                command=lambda: [menu.destroy(), self._toggle_active(category, False)],
                fg_color="transparent",
                text_color=COLORS.TEXT_PRIMARY if doc_count == 0 else COLORS.TEXT_MUTED,
                hover_color=COLORS.MUTED,
                anchor="w",
                height=32,
                state="normal" if doc_count == 0 else "disabled",
            )
            deactivate_btn.pack(fill="x", padx=4, pady=2)
        else:
            activate_btn = ctk.CTkButton(
                menu,
                text="Activate",
                command=lambda: [menu.destroy(), self._toggle_active(category, True)],
                fg_color="transparent",
                text_color=COLORS.TEXT_PRIMARY,
                hover_color=COLORS.MUTED,
                anchor="w",
                height=32,
            )
            activate_btn.pack(fill="x", padx=4, pady=2)

        # Position menu
        menu.place(x=event.x_root - self.winfo_toplevel().winfo_x(),
                   y=event.y_root - self.winfo_toplevel().winfo_y())

        # Close menu on click outside
        def close_menu(e):
            if menu.winfo_exists():
                menu.destroy()

        self.winfo_toplevel().bind("<Button-1>", close_menu, add="+")

    def _toggle_active(self, category: Category, activate: bool) -> None:
        """Activate or deactivate a category."""
        try:
            if activate:
                self.category_service.activate_category(category.code)
                InfoDialog.show_success(
                    self.winfo_toplevel(),
                    "Category Activated",
                    f"Category '{category.code}' has been activated.",
                )
            else:
                self.category_service.deactivate_category(category.code)
                InfoDialog.show_success(
                    self.winfo_toplevel(),
                    "Category Deactivated",
                    f"Category '{category.code}' has been deactivated.",
                )
            self._refresh_table()
        except ValueError as e:
            InfoDialog.show_error(
                self.winfo_toplevel(),
                "Cannot Deactivate",
                str(e),
            )
        except Exception as e:
            InfoDialog.show_error(
                self.winfo_toplevel(),
                "Error",
                str(e),
            )

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        self._refresh_table()
        # Force resize after view is fully rendered to ensure columns fill space
        self.after(50, self._resize_columns)
