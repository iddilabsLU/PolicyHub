"""
PolicyHub Document Table Model (PySide6)

QAbstractTableModel implementation for the document register table.
"""

from typing import Any, List, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QBrush, QColor

from app.constants import DocumentStatus, ReviewStatus
from app.theme import COLORS
from models.document import Document
from utils.dates import format_date


class DocumentTableModel(QAbstractTableModel):
    """
    Table model for displaying documents in a QTableView.

    Columns:
    - Reference
    - Title
    - Type
    - Category
    - Status
    - Review Status
    - Next Review
    - Owner
    - Version
    """

    COLUMNS = [
        ("doc_ref", "Reference"),
        ("title", "Title"),
        ("doc_type", "Type"),
        ("category", "Category"),
        ("status", "Status"),
        ("review_status", "Review Status"),
        ("effective_date", "Effective Date"),
        ("owner", "Owner"),
        ("version", "Version"),
    ]

    def __init__(self, parent=None):
        """Initialize the document table model."""
        super().__init__(parent)
        self._documents: List[Document] = []

    def set_documents(self, documents: List[Document]) -> None:
        """
        Set the documents to display.

        Args:
            documents: List of Document objects.
        """
        self.beginResetModel()
        self._documents = documents
        self.endResetModel()

    def get_document(self, row: int) -> Optional[Document]:
        """
        Get a document by row index.

        Args:
            row: Row index.

        Returns:
            Document at the row, or None if invalid.
        """
        if 0 <= row < len(self._documents):
            return self._documents[row]
        return None

    def get_document_by_id(self, doc_id: str) -> Optional[Document]:
        """
        Get a document by its ID.

        Args:
            doc_id: Document ID.

        Returns:
            Document with the ID, or None if not found.
        """
        for doc in self._documents:
            if doc.doc_id == doc_id:
                return doc
        return None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows."""
        if parent.isValid():
            return 0
        return len(self._documents)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns."""
        if parent.isValid():
            return 0
        return len(self.COLUMNS)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        """Return header data for the table."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self.COLUMNS):
                return self.COLUMNS[section][1]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return data for a cell."""
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row < 0 or row >= len(self._documents):
            return None

        doc = self._documents[row]
        col_key = self.COLUMNS[col][0]

        if role == Qt.ItemDataRole.DisplayRole:
            return self._get_display_value(doc, col_key)

        elif role == Qt.ItemDataRole.BackgroundRole:
            return self._get_row_background(doc)

        elif role == Qt.ItemDataRole.ForegroundRole:
            return self._get_cell_foreground(doc, col_key)

        elif role == Qt.ItemDataRole.UserRole:
            # Return the document object
            return doc

        return None

    def _get_display_value(self, doc: Document, col_key: str) -> str:
        """Get the display value for a column."""
        if col_key == "doc_ref":
            return doc.doc_ref
        elif col_key == "title":
            return doc.title
        elif col_key == "doc_type":
            return doc.type_display
        elif col_key == "category":
            return doc.category
        elif col_key == "status":
            return doc.status_display
        elif col_key == "review_status":
            return doc.review_status_display
        elif col_key == "effective_date":
            return format_date(doc.effective_date)
        elif col_key == "owner":
            return doc.owner
        elif col_key == "version":
            return doc.version
        return ""

    def _get_row_background(self, doc: Document) -> Optional[QBrush]:
        """Get the background color for a row based on review status."""
        # Only highlight for active documents
        if doc.status != DocumentStatus.ACTIVE.value:
            return None

        review_status = doc.review_status

        if review_status == ReviewStatus.OVERDUE:
            return QBrush(QColor(COLORS.DANGER_BG))
        elif review_status == ReviewStatus.DUE_SOON:
            return QBrush(QColor(COLORS.WARNING_BG))
        elif review_status == ReviewStatus.UPCOMING:
            return QBrush(QColor(COLORS.CAUTION_BG))

        return None

    def _get_cell_foreground(self, doc: Document, col_key: str) -> Optional[QBrush]:
        """Get the foreground color for a cell."""
        if col_key == "status":
            status = doc.status
            if status == DocumentStatus.ACTIVE.value:
                return QBrush(QColor(COLORS.SUCCESS))
            elif status == DocumentStatus.DRAFT.value:
                return QBrush(QColor(COLORS.TEXT_MUTED))
            elif status == DocumentStatus.UNDER_REVIEW.value:
                return QBrush(QColor(COLORS.CAUTION))
            elif status == DocumentStatus.ARCHIVED.value:
                return QBrush(QColor(COLORS.TEXT_MUTED))

        elif col_key == "review_status":
            # Only show review status colors for active documents
            if doc.status == DocumentStatus.ACTIVE.value:
                review_status = doc.review_status
                if review_status == ReviewStatus.OVERDUE:
                    return QBrush(QColor(COLORS.DANGER))
                elif review_status == ReviewStatus.DUE_SOON:
                    return QBrush(QColor(COLORS.WARNING))
                elif review_status == ReviewStatus.UPCOMING:
                    return QBrush(QColor(COLORS.CAUTION))
                elif review_status == ReviewStatus.ON_TRACK:
                    return QBrush(QColor(COLORS.SUCCESS))

        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        """Sort the table by a column."""
        if column < 0 or column >= len(self.COLUMNS):
            return

        col_key = self.COLUMNS[column][0]
        reverse = order == Qt.SortOrder.DescendingOrder

        self.beginResetModel()

        def get_sort_key(doc: Document) -> Any:
            if col_key == "doc_ref":
                return doc.doc_ref.lower()
            elif col_key == "title":
                return doc.title.lower()
            elif col_key == "doc_type":
                return doc.type_display.lower()
            elif col_key == "category":
                return doc.category.lower()
            elif col_key == "status":
                return doc.status_display.lower()
            elif col_key == "review_status":
                # Sort by urgency: OVERDUE first, then DUE_SOON, etc.
                order_map = {
                    ReviewStatus.OVERDUE.value: 0,
                    ReviewStatus.DUE_SOON.value: 1,
                    ReviewStatus.UPCOMING.value: 2,
                    ReviewStatus.ON_TRACK.value: 3,
                }
                return order_map.get(doc.review_status.value, 4)
            elif col_key == "effective_date":
                return doc.effective_date or ""
            elif col_key == "owner":
                return doc.owner.lower()
            elif col_key == "version":
                return doc.version
            return ""

        self._documents.sort(key=get_sort_key, reverse=reverse)
        self.endResetModel()
