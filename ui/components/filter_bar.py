"""
PolicyHub Filter Bar Component (PySide6)

A horizontal bar with filter dropdowns and search for document filtering.
"""

from typing import Callable, Dict, List, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.constants import DocumentStatus, DocumentType, ReviewStatus
from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button
from models.category import Category


def _update_filter_active_style(dropdown: QComboBox, is_active: bool) -> None:
    """Update the visual style of a dropdown based on active filter state."""
    dropdown.setProperty("filterActive", is_active)
    dropdown.style().unpolish(dropdown)
    dropdown.style().polish(dropdown)


class FilterBar(QFrame):
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
        parent=None,
        categories: Optional[List[Category]] = None,
        on_filter_change: Optional[Callable[[], None]] = None,
        entities: Optional[List[str]] = None,
        show_search: bool = True,
    ):
        """
        Initialize the filter bar.

        Args:
            parent: Parent widget
            categories: List of Category objects for dropdown
            on_filter_change: Callback when any filter changes
            entities: Optional list of entity names for dropdown
            show_search: Whether to show search field
        """
        super().__init__(parent)

        self.categories = categories or []
        self.entities = entities or []
        self.on_filter_change = on_filter_change
        self._search_timer: Optional[QTimer] = None

        self.setStyleSheet("QFrame { background: transparent; }")
        self._build_ui(show_search)

    def _build_ui(self, show_search: bool) -> None:
        """Build the filter bar UI."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        # Document Type dropdown
        type_container = self._create_filter_dropdown(
            "Type:",
            ["All Types"] + [t.display_name for t in DocumentType],
            140
        )
        self.type_dropdown = type_container.findChild(QComboBox)
        main_layout.addWidget(type_container)

        # Category dropdown
        category_values = ["All Categories"] + [
            f"{c.code} - {c.name}" for c in self.categories
        ]
        cat_container = self._create_filter_dropdown(
            "Category:", category_values, 170
        )
        self.category_dropdown = cat_container.findChild(QComboBox)
        main_layout.addWidget(cat_container)

        # Status dropdown
        status_values = ["All Statuses"] + [s.display_name for s in DocumentStatus]
        status_container = self._create_filter_dropdown(
            "Status:", status_values, 140
        )
        self.status_dropdown = status_container.findChild(QComboBox)
        main_layout.addWidget(status_container)

        # Review Status dropdown
        review_values = ["All States"] + [r.display_name for r in ReviewStatus]
        review_container = self._create_filter_dropdown(
            "Review:", review_values, 140
        )
        self.review_dropdown = review_container.findChild(QComboBox)
        main_layout.addWidget(review_container)

        # Mandatory dropdown
        mandatory_container = self._create_filter_dropdown(
            "Mandatory:", ["All", "Yes", "No"], 100
        )
        self.mandatory_dropdown = mandatory_container.findChild(QComboBox)
        main_layout.addWidget(mandatory_container)

        # Entity dropdown
        entity_values = ["All Entities"] + self.entities
        entity_container = self._create_filter_dropdown(
            "Entity:", entity_values, 150
        )
        self.entity_dropdown = entity_container.findChild(QComboBox)
        main_layout.addWidget(entity_container)

        if show_search:
            # Spacer
            main_layout.addStretch()

            # Search entry
            search_container = QWidget()
            search_layout = QVBoxLayout(search_container)
            search_layout.setContentsMargins(0, 0, 0, 0)
            search_layout.setSpacing(2)

            search_label = QLabel("Search:")
            search_label.setFont(TYPOGRAPHY.small)
            search_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
            search_layout.addWidget(search_label)

            self.search_entry = QLineEdit()
            self.search_entry.setPlaceholderText("Title, reference...")
            self.search_entry.setFixedWidth(180)
            self.search_entry.setFixedHeight(32)
            self.search_entry.setFont(TYPOGRAPHY.small)
            self.search_entry.returnPressed.connect(self._on_filter_changed)
            self.search_entry.textChanged.connect(self._on_search_key)
            search_layout.addWidget(self.search_entry)

            main_layout.addWidget(search_container)

            # Clear button
            self.clear_btn = QPushButton("Clear")
            self.clear_btn.setFixedWidth(70)
            self.clear_btn.setFixedHeight(32)
            self.clear_btn.setFont(TYPOGRAPHY.small)
            self.clear_btn.clicked.connect(self.clear_filters)
            style_button(self.clear_btn, "secondary")
            main_layout.addWidget(self.clear_btn, alignment=Qt.AlignmentFlag.AlignBottom)
        else:
            self.search_entry = None
            self.clear_btn = None

    def _create_filter_dropdown(
        self, label_text: str, values: List[str], width: int
    ) -> QWidget:
        """Create a labeled filter dropdown."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        label = QLabel(label_text)
        label.setFont(TYPOGRAPHY.small)
        label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        layout.addWidget(label)

        dropdown = QComboBox()
        dropdown.addItems(values)
        dropdown.setFixedWidth(width)
        dropdown.setFixedHeight(32)
        dropdown.setFont(TYPOGRAPHY.small)
        dropdown.currentTextChanged.connect(self._on_filter_changed)
        layout.addWidget(dropdown)

        return container

    def _on_filter_changed(self, *args) -> None:
        """Handle filter dropdown change."""
        # Update active filter styling
        self._update_active_filter_styles()

        if self.on_filter_change:
            self.on_filter_change()

    def _update_active_filter_styles(self) -> None:
        """Update the styling of all dropdowns based on their active state."""
        _update_filter_active_style(
            self.type_dropdown,
            self.type_dropdown.currentIndex() != 0
        )
        _update_filter_active_style(
            self.category_dropdown,
            self.category_dropdown.currentIndex() != 0
        )
        _update_filter_active_style(
            self.status_dropdown,
            self.status_dropdown.currentIndex() != 0
        )
        _update_filter_active_style(
            self.review_dropdown,
            self.review_dropdown.currentIndex() != 0
        )
        _update_filter_active_style(
            self.mandatory_dropdown,
            self.mandatory_dropdown.currentIndex() != 0
        )
        _update_filter_active_style(
            self.entity_dropdown,
            self.entity_dropdown.currentIndex() != 0
        )

    def get_active_filter_count(self) -> int:
        """
        Get the count of currently active filters.

        Returns:
            Number of filters that are not set to "All"
        """
        count = 0
        if self.type_dropdown.currentIndex() != 0:
            count += 1
        if self.category_dropdown.currentIndex() != 0:
            count += 1
        if self.status_dropdown.currentIndex() != 0:
            count += 1
        if self.review_dropdown.currentIndex() != 0:
            count += 1
        if self.mandatory_dropdown.currentIndex() != 0:
            count += 1
        if self.entity_dropdown.currentIndex() != 0:
            count += 1
        if self.search_entry and self.search_entry.text().strip():
            count += 1
        return count

    def has_active_filters(self) -> bool:
        """
        Check if any filters are currently active.

        Returns:
            True if at least one filter is active
        """
        return self.get_active_filter_count() > 0

    def _on_search_key(self, text: str) -> None:
        """Handle search key release with debounce."""
        # Cancel previous timer
        if self._search_timer:
            self._search_timer.stop()

        # Schedule new search after 300ms
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._on_filter_changed)
        self._search_timer.start(300)

    def get_filters(self) -> Dict[str, Optional[str]]:
        """
        Get current filter values.

        Returns:
            Dictionary with filter keys and values (None if "All")
        """
        filters = {}

        # Document Type
        type_val = self.type_dropdown.currentText()
        if type_val != "All Types":
            for t in DocumentType:
                if t.display_name == type_val:
                    filters["doc_type"] = t.value
                    break
        else:
            filters["doc_type"] = None

        # Category
        cat_val = self.category_dropdown.currentText()
        if cat_val != "All Categories":
            code = cat_val.split(" - ")[0]
            filters["category"] = code
        else:
            filters["category"] = None

        # Status
        status_val = self.status_dropdown.currentText()
        if status_val != "All Statuses":
            for s in DocumentStatus:
                if s.display_name == status_val:
                    filters["status"] = s.value
                    break
        else:
            filters["status"] = None

        # Review Status
        review_val = self.review_dropdown.currentText()
        if review_val != "All States":
            for r in ReviewStatus:
                if r.display_name == review_val:
                    filters["review_status"] = r.value
                    break
        else:
            filters["review_status"] = None

        # Mandatory Read
        mandatory_val = self.mandatory_dropdown.currentText()
        if mandatory_val == "Yes":
            filters["mandatory_read_all"] = True
        elif mandatory_val == "No":
            filters["mandatory_read_all"] = False
        else:
            filters["mandatory_read_all"] = None

        # Applicable Entity
        entity_val = self.entity_dropdown.currentText()
        if entity_val != "All Entities":
            filters["applicable_entity"] = entity_val
        else:
            filters["applicable_entity"] = None

        # Search
        if self.search_entry:
            search = self.search_entry.text().strip()
            filters["search_term"] = search if search else None
        else:
            filters["search_term"] = None

        return filters

    def clear_filters(self) -> None:
        """Reset all filters to default values."""
        self.type_dropdown.setCurrentIndex(0)
        self.category_dropdown.setCurrentIndex(0)
        self.status_dropdown.setCurrentIndex(0)
        self.review_dropdown.setCurrentIndex(0)
        self.mandatory_dropdown.setCurrentIndex(0)
        self.entity_dropdown.setCurrentIndex(0)
        if self.search_entry:
            self.search_entry.clear()
        if self.on_filter_change:
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
                index = self.type_dropdown.findText(display_name)
                if index >= 0:
                    self.type_dropdown.setCurrentIndex(index)
            except ValueError:
                pass
        elif filter_name == "category":
            for i, cat in enumerate(self.categories):
                if cat.code == value:
                    self.category_dropdown.setCurrentIndex(i + 1)  # +1 for "All"
                    break
        elif filter_name == "status":
            try:
                display_name = DocumentStatus(value).display_name
                index = self.status_dropdown.findText(display_name)
                if index >= 0:
                    self.status_dropdown.setCurrentIndex(index)
            except ValueError:
                pass
        elif filter_name == "review_status":
            try:
                display_name = ReviewStatus(value).display_name
                index = self.review_dropdown.findText(display_name)
                if index >= 0:
                    self.review_dropdown.setCurrentIndex(index)
            except ValueError:
                pass
        elif filter_name == "mandatory_read_all":
            if value is True or value == "True":
                self.mandatory_dropdown.setCurrentText("Yes")
            elif value is False or value == "False":
                self.mandatory_dropdown.setCurrentText("No")
            else:
                self.mandatory_dropdown.setCurrentIndex(0)
        elif filter_name == "applicable_entity":
            if value and value in self.entities:
                index = self.entity_dropdown.findText(value)
                if index >= 0:
                    self.entity_dropdown.setCurrentIndex(index)
            else:
                self.entity_dropdown.setCurrentIndex(0)

        if self.on_filter_change:
            self.on_filter_change()

    def update_categories(self, categories: List[Category]) -> None:
        """
        Update the category dropdown with new categories.

        Args:
            categories: New list of Category objects
        """
        self.categories = categories
        self.category_dropdown.clear()
        self.category_dropdown.addItem("All Categories")
        for cat in categories:
            self.category_dropdown.addItem(f"{cat.code} - {cat.name}")

    def update_entities(self, entities: List[str]) -> None:
        """
        Update the entity dropdown with new entities.

        Args:
            entities: New list of entity names
        """
        self.entities = entities
        self.entity_dropdown.clear()
        self.entity_dropdown.addItem("All Entities")
        for entity in entities:
            self.entity_dropdown.addItem(entity)
