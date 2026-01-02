"""
PolicyHub Filter Bar Component

A horizontal bar with filter dropdowns and search for document filtering.
"""

from typing import Callable, Dict, List, Optional

import customtkinter as ctk

from app.constants import DocumentStatus, DocumentType, ReviewStatus
from app.theme import COLORS, SPACING, TYPOGRAPHY, configure_button_style
from models.category import Category


class FilterBar(ctk.CTkFrame):
    """
    A filter bar with dropdowns and search for document filtering.

    Usage:
        filter_bar = FilterBar(
            parent,
            categories=category_list,
            on_filter_change=self._refresh_table,
        )

        # Get current filter values
        filters = filter_bar.get_filters()
        # Returns: {"doc_type": "POLICY", "category": None, "status": None, ...}
    """

    def __init__(
        self,
        parent,
        categories: List[Category],
        on_filter_change: Callable[[], None],
        show_search: bool = True,
        **kwargs
    ):
        """
        Initialize the filter bar.

        Args:
            parent: Parent widget
            categories: List of Category objects for dropdown
            on_filter_change: Callback when any filter changes
            show_search: Whether to show search field
            **kwargs: Additional frame options
        """
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.categories = categories
        self.on_filter_change = on_filter_change
        self._search_after_id = None

        self._build_ui(show_search)

    def _build_ui(self, show_search: bool) -> None:
        """Build the filter bar UI."""
        # Document Type dropdown
        type_frame = ctk.CTkFrame(self, fg_color="transparent")
        type_frame.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            type_frame,
            text="Type:",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        ).pack(anchor="w")

        self.type_var = ctk.StringVar(value="All Types")
        type_values = ["All Types"] + [t.display_name for t in DocumentType]
        self.type_dropdown = ctk.CTkOptionMenu(
            type_frame,
            values=type_values,
            variable=self.type_var,
            command=self._on_filter_changed,
            width=130,
            font=TYPOGRAPHY.small,
            dropdown_font=TYPOGRAPHY.small,
        )
        self.type_dropdown.pack()

        # Category dropdown
        cat_frame = ctk.CTkFrame(self, fg_color="transparent")
        cat_frame.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            cat_frame,
            text="Category:",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        ).pack(anchor="w")

        self.category_var = ctk.StringVar(value="All Categories")
        category_values = ["All Categories"] + [
            f"{c.code} - {c.name}" for c in self.categories
        ]
        self.category_dropdown = ctk.CTkOptionMenu(
            cat_frame,
            values=category_values,
            variable=self.category_var,
            command=self._on_filter_changed,
            width=180,
            font=TYPOGRAPHY.small,
            dropdown_font=TYPOGRAPHY.small,
        )
        self.category_dropdown.pack()

        # Status dropdown
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            status_frame,
            text="Status:",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        ).pack(anchor="w")

        self.status_var = ctk.StringVar(value="All Statuses")
        status_values = ["All Statuses"] + [s.display_name for s in DocumentStatus]
        self.status_dropdown = ctk.CTkOptionMenu(
            status_frame,
            values=status_values,
            variable=self.status_var,
            command=self._on_filter_changed,
            width=130,
            font=TYPOGRAPHY.small,
            dropdown_font=TYPOGRAPHY.small,
        )
        self.status_dropdown.pack()

        # Review Status dropdown
        review_frame = ctk.CTkFrame(self, fg_color="transparent")
        review_frame.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            review_frame,
            text="Review:",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        ).pack(anchor="w")

        self.review_var = ctk.StringVar(value="All States")
        review_values = ["All States"] + [r.display_name for r in ReviewStatus]
        self.review_dropdown = ctk.CTkOptionMenu(
            review_frame,
            values=review_values,
            variable=self.review_var,
            command=self._on_filter_changed,
            width=120,
            font=TYPOGRAPHY.small,
            dropdown_font=TYPOGRAPHY.small,
        )
        self.review_dropdown.pack()

        # Spacer
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(side="left", fill="x", expand=True)

        # Clear button
        self.clear_btn = ctk.CTkButton(
            self,
            text="Clear",
            command=self.clear_filters,
            width=70,
            height=32,
            font=TYPOGRAPHY.small,
            fg_color=COLORS.SECONDARY,
            hover_color=COLORS.SECONDARY_HOVER,
            text_color=COLORS.TEXT_PRIMARY,
        )
        self.clear_btn.pack(side="right", padx=(8, 0))

        # Search entry
        if show_search:
            search_frame = ctk.CTkFrame(self, fg_color="transparent")
            search_frame.pack(side="right", padx=(0, 8))

            ctk.CTkLabel(
                search_frame,
                text="Search:",
                font=TYPOGRAPHY.small,
                text_color=COLORS.TEXT_SECONDARY,
            ).pack(anchor="w")

            self.search_var = ctk.StringVar()
            self.search_entry = ctk.CTkEntry(
                search_frame,
                placeholder_text="Title, reference...",
                textvariable=self.search_var,
                width=180,
                height=32,
                font=TYPOGRAPHY.small,
            )
            self.search_entry.pack()
            self.search_entry.bind("<Return>", lambda e: self._on_filter_changed())
            self.search_entry.bind("<KeyRelease>", self._on_search_key)
        else:
            self.search_var = ctk.StringVar()

    def _on_filter_changed(self, *args) -> None:
        """Handle filter dropdown change."""
        self.on_filter_change()

    def _on_search_key(self, event) -> None:
        """Handle search key release with debounce."""
        # Cancel previous scheduled search
        if self._search_after_id:
            self.after_cancel(self._search_after_id)

        # Schedule new search after 300ms
        self._search_after_id = self.after(300, self.on_filter_change)

    def get_filters(self) -> Dict[str, Optional[str]]:
        """
        Get current filter values.

        Returns:
            Dictionary with filter keys and values (None if "All")
        """
        filters = {}

        # Document Type
        type_val = self.type_var.get()
        if type_val != "All Types":
            # Convert display name back to enum value
            for t in DocumentType:
                if t.display_name == type_val:
                    filters["doc_type"] = t.value
                    break
        else:
            filters["doc_type"] = None

        # Category
        cat_val = self.category_var.get()
        if cat_val != "All Categories":
            # Extract code from "CODE - Name" format
            code = cat_val.split(" - ")[0]
            filters["category"] = code
        else:
            filters["category"] = None

        # Status
        status_val = self.status_var.get()
        if status_val != "All Statuses":
            for s in DocumentStatus:
                if s.display_name == status_val:
                    filters["status"] = s.value
                    break
        else:
            filters["status"] = None

        # Review Status
        review_val = self.review_var.get()
        if review_val != "All States":
            for r in ReviewStatus:
                if r.display_name == review_val:
                    filters["review_status"] = r.value
                    break
        else:
            filters["review_status"] = None

        # Search
        search = self.search_var.get().strip()
        filters["search_term"] = search if search else None

        return filters

    def clear_filters(self) -> None:
        """Reset all filters to default values."""
        self.type_var.set("All Types")
        self.category_var.set("All Categories")
        self.status_var.set("All Statuses")
        self.review_var.set("All States")
        self.search_var.set("")
        self.on_filter_change()

    def set_filter(self, filter_name: str, value: str) -> None:
        """
        Set a specific filter value.

        Args:
            filter_name: Name of the filter (doc_type, category, status, review_status)
            value: Value to set
        """
        if filter_name == "doc_type":
            try:
                display_name = DocumentType(value).display_name
                self.type_var.set(display_name)
            except ValueError:
                pass
        elif filter_name == "category":
            for cat in self.categories:
                if cat.code == value:
                    self.category_var.set(f"{cat.code} - {cat.name}")
                    break
        elif filter_name == "status":
            try:
                display_name = DocumentStatus(value).display_name
                self.status_var.set(display_name)
            except ValueError:
                pass
        elif filter_name == "review_status":
            try:
                display_name = ReviewStatus(value).display_name
                self.review_var.set(display_name)
            except ValueError:
                pass

        self.on_filter_change()

    def update_categories(self, categories: List[Category]) -> None:
        """
        Update the category dropdown with new categories.

        Args:
            categories: New list of Category objects
        """
        self.categories = categories
        category_values = ["All Categories"] + [
            f"{c.code} - {c.name}" for c in categories
        ]
        self.category_dropdown.configure(values=category_values)
        self.category_var.set("All Categories")
