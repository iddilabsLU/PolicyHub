"""
PolicyHub Categories Settings View (PySide6)

Category management view for administrators to add, edit, and manage document categories.
"""

from typing import TYPE_CHECKING, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QCheckBox,
    QTableView,
    QHeaderView,
    QAbstractItemView,
    QMenu,
)
from PySide6.QtCore import QAbstractTableModel, QModelIndex

from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button, style_card
from ui.components.empty_state import EmptyState
from ui.components.toast import Toast
from ui.dialogs.confirm_dialog import ConfirmDialog, InfoDialog
from ui.views.base_view import BaseView
from models.category import Category
from services.category_service import CategoryService

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class CategoryTableModel(QAbstractTableModel):
    """Table model for categories."""

    COLUMNS = ["Code", "Name", "Documents", "Sort Order", "Status"]

    def __init__(self):
        super().__init__()
        self._categories: List[Category] = []
        self._usage_stats: dict = {}

    def set_data(self, categories: List[Category], usage_stats: dict) -> None:
        """Set the category data."""
        self.beginResetModel()
        self._categories = categories
        self._usage_stats = usage_stats
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._categories)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        cat = self._categories[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return cat.code
            elif col == 1:
                return cat.name
            elif col == 2:
                return str(self._usage_stats.get(cat.code, 0))
            elif col == 3:
                return str(cat.sort_order)
            elif col == 4:
                return "Active" if cat.is_active else "Inactive"

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in [2, 3]:
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        elif role == Qt.ItemDataRole.ForegroundRole:
            if col == 4:
                from PySide6.QtGui import QColor
                if cat.is_active:
                    return QColor(COLORS.SUCCESS)
                else:
                    return QColor(COLORS.TEXT_MUTED)

        return None

    def headerData(self, section: int, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None

    def get_category(self, row: int) -> Category:
        """Get category at row index."""
        if 0 <= row < len(self._categories):
            return self._categories[row]
        return None


class CategoriesSettingsView(BaseView):
    """
    Category management view for administrators.

    Features:
    - View all categories in a table
    - Add new categories
    - Edit existing categories
    - Activate/deactivate categories (if no documents assigned)
    """

    def __init__(self, parent: QWidget, app: "PolicyHubApp"):
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
        )
        layout.setSpacing(10)

        # Header
        header = QFrame()
        header.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Category Management")
        title.setFont(TYPOGRAPHY.section_heading)
        title.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Show inactive checkbox
        self.inactive_checkbox = QCheckBox("Show inactive categories")
        self.inactive_checkbox.setFont(TYPOGRAPHY.small)
        self.inactive_checkbox.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        self.inactive_checkbox.stateChanged.connect(self._refresh_table)
        header_layout.addWidget(self.inactive_checkbox)

        # Add button
        add_btn = QPushButton("+ Add Category")
        add_btn.setFixedSize(140, 36)
        style_button(add_btn, "primary")
        add_btn.clicked.connect(self._on_add_category)
        header_layout.addWidget(add_btn)

        layout.addWidget(header)

        # Table container
        table_card = QFrame()
        style_card(table_card, with_shadow=True)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
        )
        table_layout.setSpacing(0)

        # Table
        self.table_model = CategoryTableModel()
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)

        # Configure table
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.setShowGrid(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.verticalHeader().setDefaultSectionSize(36)

        # Header configuration
        header_view = self.table_view.horizontalHeader()
        header_view.setStretchLastSection(True)
        header_view.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # Column widths
        self.table_view.setColumnWidth(0, 100)
        self.table_view.setColumnWidth(1, 250)
        self.table_view.setColumnWidth(2, 100)
        self.table_view.setColumnWidth(3, 100)
        self.table_view.setColumnWidth(4, 100)

        # Signals
        self.table_view.doubleClicked.connect(self._on_double_click)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self._show_context_menu)

        # Styling
        self.table_view.setStyleSheet(f"""
            QTableView {{
                background-color: {COLORS.CARD};
                border: none;
                border-radius: 4px;
                gridline-color: {COLORS.BORDER};
            }}
            QTableView::item {{
                padding: 8px;
            }}
            QTableView::item:selected {{
                background-color: {COLORS.PRIMARY};
                color: {COLORS.PRIMARY_FOREGROUND};
            }}
            QHeaderView::section {{
                background-color: {COLORS.MUTED};
                color: {COLORS.TEXT_PRIMARY};
                font-weight: bold;
                padding: 8px;
                border: none;
                border-bottom: 1px solid {COLORS.BORDER};
            }}
        """)

        table_layout.addWidget(self.table_view)

        # Empty state (hidden by default)
        self.empty_state = EmptyState(
            parent=table_card,
            icon=EmptyState.ICON_FOLDER,
            title="No categories",
            message="Create categories to organize your documents.",
            action_text="Add Category",
            action_callback=self._on_add_category,
        )
        self.empty_state.hide()
        table_layout.addWidget(self.empty_state)

        # Status bar
        self.status_label = QLabel("Loading...")
        self.status_label.setFont(TYPOGRAPHY.small)
        self.status_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        table_layout.addWidget(self.status_label)

        layout.addWidget(table_card, 1)

    def _refresh_table(self) -> None:
        """Reload category data."""
        self.show_inactive = self.inactive_checkbox.isChecked()
        self.categories = self.category_service.get_all_categories(include_inactive=self.show_inactive)
        self.usage_stats = self.category_service.get_category_usage_stats()

        self.table_model.set_data(self.categories, self.usage_stats)

        # Show/hide empty state
        has_categories = len(self.categories) > 0
        self.table_view.setVisible(has_categories)
        self.empty_state.setVisible(not has_categories)

        self.status_label.setText(f"Showing {len(self.categories)} category(s)")

    def _on_add_category(self) -> None:
        """Handle add category button click."""
        from ui.dialogs.category_dialog import CategoryDialog

        dialog = CategoryDialog(self.window(), self.app.db)
        if dialog.exec():
            Toast.show_success(self, "Category created successfully")
            self._refresh_table()

    def _on_double_click(self, index: QModelIndex) -> None:
        """Handle double-click on table row."""
        cat = self.table_model.get_category(index.row())
        if cat:
            self._edit_category(cat)

    def _edit_category(self, category: Category) -> None:
        """Open edit dialog for a category."""
        from ui.dialogs.category_dialog import CategoryDialog

        dialog = CategoryDialog(self.window(), self.app.db, category=category)
        if dialog.exec():
            Toast.show_success(self, "Category updated successfully")
            self._refresh_table()

    def _show_context_menu(self, pos) -> None:
        """Show context menu on right-click."""
        index = self.table_view.indexAt(pos)
        if not index.isValid():
            return

        cat = self.table_model.get_category(index.row())
        if not cat:
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS.CARD};
                border: 1px solid {COLORS.BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS.MUTED};
            }}
        """)

        edit_action = menu.addAction("Edit Category")
        edit_action.triggered.connect(lambda: self._edit_category(cat))

        doc_count = self.usage_stats.get(cat.code, 0)

        if cat.is_active:
            deactivate_action = menu.addAction(
                "Deactivate" if doc_count == 0 else f"Deactivate ({doc_count} docs)"
            )
            deactivate_action.setEnabled(doc_count == 0)
            deactivate_action.triggered.connect(lambda: self._toggle_active(cat, False))
        else:
            activate_action = menu.addAction("Activate")
            activate_action.triggered.connect(lambda: self._toggle_active(cat, True))

        menu.exec(self.table_view.viewport().mapToGlobal(pos))

    def _toggle_active(self, category: Category, activate: bool) -> None:
        """Activate or deactivate a category."""
        try:
            if activate:
                self.category_service.activate_category(category.code)
                Toast.show_success(self, f"Category '{category.code}' activated")
            else:
                self.category_service.deactivate_category(category.code)
                Toast.show_success(self, f"Category '{category.code}' deactivated")
            self._refresh_table()
        except ValueError as e:
            Toast.show_warning(self, str(e))
        except Exception as e:
            Toast.show_error(self, str(e))

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        self._refresh_table()
