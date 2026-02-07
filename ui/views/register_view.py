"""
PolicyHub Register View (PySide6)

Document register showing all documents in a filterable, sortable table.
"""

import logging
from typing import TYPE_CHECKING, List, Optional

logger = logging.getLogger(__name__)

from PySide6.QtCore import Qt, QTimer, QSortFilterProxyModel
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QTableView,
    QHeaderView,
    QAbstractItemView,
)

from app.constants import DocumentStatus, DocumentType, ReviewStatus
from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button, style_card
from ui.components.empty_state import EmptyState
from ui.components.filter_bar import FilterBar
from ui.models.document_table_model import DocumentTableModel
from ui.delegates.status_delegate import StatusBadgeDelegate
from ui.views.base_view import BaseView
from core.permissions import PermissionChecker
from models.document import Document
from services.category_service import CategoryService
from services.document_service import DocumentService
from services.entity_service import EntityService
from utils.dates import format_date

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class RegisterView(BaseView):
    """
    Document register view with filtering and sorting.

    Features:
    - Full document table with QTableView
    - Filter bar for type, category, status, review status
    - Search functionality
    - Sorting by column headers
    - Double-click to view details
    - Add new document button (if permitted)
    """

    def __init__(
        self,
        parent: QWidget,
        app: "PolicyHubApp",
        initial_filter: Optional[dict] = None,
    ):
        """
        Initialize the register view.

        Args:
            parent: Parent widget
            app: Main application instance
            initial_filter: Optional initial filter to apply
        """
        super().__init__(parent, app)
        self.doc_service = DocumentService(app.db)
        self.category_service = CategoryService(app.db)
        self.entity_service = EntityService(app.db)
        self.permissions = PermissionChecker()
        self.documents: List[Document] = []
        self._total_document_count = 0
        self.initial_filter = initial_filter or {}
        self._sort_column = "doc_ref"
        self._sort_direction = "ASC"

        # Search debounce timer
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._refresh_table)

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the register UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
        )
        layout.setSpacing(10)

        # Header with card styling
        header = QFrame()
        header.setFixedHeight(60)
        style_card(header, with_shadow=True)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
        )

        # Title with document count
        self.title_label = QLabel("Document Register")
        self.title_label.setFont(TYPOGRAPHY.window_title)
        self.title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # Search entry with search icon in placeholder
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("🔍 Search title, reference...")
        self.search_entry.setFixedSize(220, 36)
        self.search_entry.setFont(TYPOGRAPHY.body)
        self.search_entry.textChanged.connect(self._on_search_key)
        self.search_entry.returnPressed.connect(self._on_filter_change)
        header_layout.addWidget(self.search_entry)

        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedSize(70, 36)
        style_button(self.clear_btn, "secondary")
        self.clear_btn.clicked.connect(self._on_clear_filters)
        header_layout.addWidget(self.clear_btn)

        # Add button (if can edit)
        if self.permissions.can_edit():
            add_btn = QPushButton("+ Add Document")
            add_btn.setFixedSize(130, 36)
            style_button(add_btn, "primary")
            add_btn.clicked.connect(self._on_add)
            header_layout.addWidget(add_btn)

        layout.addWidget(header)

        # Filter bar
        categories = self.category_service.get_active_categories()
        entities = self.entity_service.get_entity_names()
        self.filter_bar = FilterBar(
            self,
            categories=categories,
            on_filter_change=self._on_filter_change,
            entities=entities,
            show_search=False,  # Search is in header
        )
        layout.addWidget(self.filter_bar)

        # Apply initial filter if provided
        if self.initial_filter:
            for key, value in self.initial_filter.items():
                if value:
                    self.filter_bar.set_filter(key, value)

        # Table container with card styling
        self.table_container = QFrame()
        style_card(self.table_container, with_shadow=True)
        table_layout = QVBoxLayout(self.table_container)
        table_layout.setContentsMargins(
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
        )
        table_layout.setSpacing(0)

        # Build table
        self._build_table()
        table_layout.addWidget(self.table_view)

        # Empty state (hidden by default)
        self.empty_state = EmptyState(
            parent=self.table_container,
            icon=EmptyState.ICON_SEARCH,
            title="No documents found",
            message="Try adjusting your filters or add a new document.",
            action_text="Clear Filters" if not self.permissions.can_edit() else None,
            action_callback=self._on_clear_filters if not self.permissions.can_edit() else None,
        )
        self.empty_state.hide()
        table_layout.addWidget(self.empty_state)

        # Status bar
        status_bar = QFrame()
        status_bar.setFixedHeight(30)
        status_bar.setStyleSheet("background: transparent;")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(0, 5, 0, 5)

        self.status_label = QLabel("Loading...")
        self.status_label.setFont(TYPOGRAPHY.small)
        self.status_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        table_layout.addWidget(status_bar)

        layout.addWidget(self.table_container, 1)

    def _build_table(self) -> None:
        """Build the QTableView with model and delegates."""
        # Create model
        self.table_model = DocumentTableModel()

        # Create table view
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)

        # Configure table appearance
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.setSortingEnabled(True)
        self.table_view.setShowGrid(True)
        self.table_view.setGridStyle(Qt.PenStyle.SolidLine)
        self.table_view.verticalHeader().setVisible(False)

        # Row height
        self.table_view.verticalHeader().setDefaultSectionSize(36)

        # Header configuration
        header = self.table_view.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Set column widths (proportional)
        # Columns: Ref, Title, Type, Category, Status, Review Status, Next Review, Owner, Version
        column_widths = [90, 200, 80, 100, 90, 100, 100, 120, 60]
        for i, width in enumerate(column_widths):
            self.table_view.setColumnWidth(i, width)

        # Title column stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # Set delegates for status columns
        # Column 4: Status, Column 5: Review Status
        status_delegate = StatusBadgeDelegate(self.table_view)
        self.table_view.setItemDelegateForColumn(4, status_delegate)
        self.table_view.setItemDelegateForColumn(5, status_delegate)

        # Connect signals
        self.table_view.doubleClicked.connect(self._on_double_click)
        header.sectionClicked.connect(self._on_header_click)

        # Styling
        self.table_view.setStyleSheet(f"""
            QTableView {{
                background-color: {COLORS.CARD};
                border: none;
                border-radius: 4px;
                gridline-color: {COLORS.BORDER};
                selection-background-color: {COLORS.PRIMARY};
                selection-color: {COLORS.PRIMARY_FOREGROUND};
            }}
            QTableView::item {{
                padding: 8px;
                border-bottom: 1px solid {COLORS.BORDER};
                color: {COLORS.TEXT_PRIMARY};
            }}
            QTableView::item:hover:!selected {{
                background-color: {COLORS.MUTED};
            }}
            QTableView::item:selected {{
                background-color: {COLORS.PRIMARY};
                color: {COLORS.PRIMARY_FOREGROUND};
            }}
            QTableView::item:selected:hover {{
                background-color: {COLORS.PRIMARY_HOVER};
                color: {COLORS.PRIMARY_FOREGROUND};
            }}
            QHeaderView::section {{
                background-color: {COLORS.MUTED};
                color: {COLORS.TEXT_PRIMARY};
                font-weight: bold;
                padding: 8px;
                border: none;
                border-bottom: 1px solid {COLORS.BORDER};
                border-right: 1px solid {COLORS.BORDER};
            }}
            QHeaderView::section:hover {{
                background-color: {COLORS.SECONDARY};
            }}
        """)

    def _refresh_table(self) -> None:
        """Reload data with current filters."""
        filters = self.filter_bar.get_filters()

        # Get search term
        search_term = self.search_entry.text().strip()

        # Get total document count (without filters) for display
        self._total_document_count = self.doc_service.get_total_document_count()

        # Get documents with filters
        self.documents = self.doc_service.get_all_documents(
            status=filters.get("status"),
            doc_type=filters.get("doc_type"),
            category=filters.get("category"),
            review_status=filters.get("review_status"),
            search_term=search_term if search_term else None,
            mandatory_read_all=filters.get("mandatory_read_all"),
            applicable_entity=filters.get("applicable_entity"),
            order_by=self._sort_column,
            order_dir=self._sort_direction,
        )

        # Update entity filter dropdown in case new entities were added
        self.filter_bar.update_entities(self.entity_service.get_entity_names())

        # Update model
        self.table_model.set_documents(self.documents)

        # Update title with total count
        self.title_label.setText(f"Document Register ({self._total_document_count})")

        # Show/hide empty state and table
        has_documents = len(self.documents) > 0
        self.table_view.setVisible(has_documents)
        self.empty_state.setVisible(not has_documents)

        # Update status bar
        if self.filter_bar.has_active_filters() or search_term:
            self.status_label.setText(
                f"Showing {len(self.documents)} of {self._total_document_count} documents"
            )
        else:
            self.status_label.setText(f"Showing {len(self.documents)} documents")

    def _on_filter_change(self) -> None:
        """Handle filter change."""
        self._refresh_table()

    def _on_search_key(self, text: str) -> None:
        """Handle search text change with debounce."""
        # Cancel previous timer and start new one
        self._search_timer.stop()
        self._search_timer.start(300)

    def _on_clear_filters(self) -> None:
        """Clear all filters and search."""
        self.search_entry.clear()
        self.filter_bar.clear_filters()
        self._refresh_table()

    def _on_double_click(self, index) -> None:
        """Handle double-click on table row."""
        logger.debug(f"Double-click detected at row {index.row()}, valid={index.isValid()}")

        if not index.isValid():
            logger.warning("Double-click index is invalid")
            return

        # Get document directly from the model using UserRole (most reliable)
        doc = index.data(Qt.ItemDataRole.UserRole)
        logger.debug(f"Document from UserRole: {doc}")

        if doc:
            self._open_document(doc)
        else:
            logger.warning(f"No document found for row {index.row()}")

    def _on_header_click(self, column: int) -> None:
        """Handle header click for sorting."""
        column_map = {
            0: "doc_ref",
            1: "title",
            2: "doc_type",
            3: "category",
            4: "status",
            5: "review_status",
            6: "effective_date",
            7: "owner",
            8: "version",
        }

        if column in column_map:
            new_column = column_map[column]
            if new_column == self._sort_column:
                # Toggle direction
                self._sort_direction = "DESC" if self._sort_direction == "ASC" else "ASC"
            else:
                self._sort_column = new_column
                self._sort_direction = "ASC"

            self._refresh_table()

    def _on_add(self) -> None:
        """Handle add document button click."""
        from ui.dialogs.document_dialog import DocumentDialog

        categories = self.category_service.get_active_categories()
        dialog = DocumentDialog(
            self,
            self.app.db,
            categories=categories,
        )
        if dialog.exec():
            self._refresh_table()

    def _open_document(self, document: Document) -> None:
        """Open document detail view."""
        logger.info(f"Opening document: {document.doc_ref} - {document.title}")
        main_view = self.app.current_view
        logger.debug(f"main_view type: {type(main_view).__name__}")
        logger.debug(f"has _show_document_detail: {hasattr(main_view, '_show_document_detail')}")

        if hasattr(main_view, "_show_document_detail"):
            main_view._show_document_detail(document)
        else:
            logger.error(f"main_view ({type(main_view).__name__}) does not have _show_document_detail method")

    def apply_filter(
        self, filter_type: Optional[str] = None, review_status: Optional[str] = None
    ) -> None:
        """
        Apply a filter programmatically.

        Args:
            filter_type: Document type or status filter
            review_status: Review status filter
        """
        # Map filter_type to actual filter
        if filter_type:
            if filter_type == "total":
                self.filter_bar.clear_filters()
            elif filter_type == "active":
                self.filter_bar.set_filter("status", DocumentStatus.ACTIVE.value)
            elif filter_type == "under_review":
                self.filter_bar.set_filter("status", DocumentStatus.UNDER_REVIEW.value)
            elif filter_type in ["policy", "procedure", "manual", "hr", "others"]:
                self.filter_bar.set_filter("doc_type", filter_type.upper())

        if review_status:
            self.filter_bar.set_filter("review_status", review_status)

        self._refresh_table()

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        self._refresh_table()
