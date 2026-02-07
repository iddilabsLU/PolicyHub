"""
PolicyHub Link Dialog (PySide6)

Dialog for creating links between documents.
"""

from typing import List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QFrame,
    QScrollArea,
)

from app.constants import LinkType
from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button
from core.database import DatabaseManager
from ui.dialogs.base_dialog import BaseDialog
from ui.dialogs.confirm_dialog import InfoDialog
from services.link_service import LinkService


class LinkDialog(BaseDialog):
    """
    Dialog for linking two documents.

    Usage:
        dialog = LinkDialog(
            parent,
            db,
            source_doc_id="...",
            source_doc_ref="POL-AML-001",
        )
        if dialog.exec():
            result = dialog.result  # (target_doc_id, link_type)
    """

    def __init__(
        self,
        parent: QWidget,
        db: DatabaseManager,
        source_doc_id: str,
        source_doc_ref: str,
    ):
        """
        Initialize the link dialog.

        Args:
            parent: Parent window
            db: Database manager instance
            source_doc_id: ID of the source document
            source_doc_ref: Reference of the source document
        """
        self.db = db
        self.source_doc_id = source_doc_id
        self.source_doc_ref = source_doc_ref
        self.link_service = LinkService(db)
        self.selected_doc: Optional[dict] = None
        self.available_docs: List[dict] = []

        super().__init__(parent, "Link Documents", width=600, height=550)
        self._build_ui()
        self._load_available_documents()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = QLabel(f"Create link from {self.source_doc_ref}")
        title_label.setFont(TYPOGRAPHY.section_heading)
        title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title_label)

        # Link type selection
        type_row = QHBoxLayout()
        type_row.setSpacing(10)

        type_label = QLabel("Link Type:")
        type_label.setFont(TYPOGRAPHY.body)
        type_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        type_row.addWidget(type_label)

        self.link_types = [
            (LinkType.IMPLEMENTS.value, "Implements (procedure implements policy)"),
            (LinkType.REFERENCES.value, "References (document references another)"),
            (LinkType.SUPERSEDES.value, "Supersedes (new version replaces old)"),
        ]

        self.link_type_dropdown = QComboBox()
        self.link_type_dropdown.addItems([t[1] for t in self.link_types])
        self.link_type_dropdown.setCurrentIndex(1)  # Default to References
        self.link_type_dropdown.setFixedWidth(350)
        self.link_type_dropdown.setFont(TYPOGRAPHY.body)
        self._style_dropdown(self.link_type_dropdown)
        type_row.addWidget(self.link_type_dropdown)
        type_row.addStretch()

        layout.addLayout(type_row)

        # Search box
        search_row = QHBoxLayout()
        search_row.setSpacing(10)

        search_label = QLabel("Search Document:")
        search_label.setFont(TYPOGRAPHY.body)
        search_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        search_row.addWidget(search_label)

        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Search by reference or title...")
        self.search_entry.setFont(TYPOGRAPHY.body)
        self._style_input(self.search_entry)
        self.search_entry.textChanged.connect(self._on_search)
        search_row.addWidget(self.search_entry)

        layout.addLayout(search_row)

        # Document list
        list_frame = QFrame()
        list_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.CARD};
                border: none;
                border-radius: {SPACING.CORNER_RADIUS}px;
            }}
        """)
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(5, 5, 5, 5)

        self.doc_list_scroll = QScrollArea()
        self.doc_list_scroll.setWidgetResizable(True)
        self.doc_list_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.doc_list_scroll.setStyleSheet("background: transparent;")

        self.doc_list_content = QWidget()
        self.doc_list_content.setStyleSheet("background: transparent;")
        self.doc_list_layout = QVBoxLayout(self.doc_list_content)
        self.doc_list_layout.setContentsMargins(0, 0, 0, 0)
        self.doc_list_layout.setSpacing(4)

        self.doc_list_scroll.setWidget(self.doc_list_content)
        list_layout.addWidget(self.doc_list_scroll)

        layout.addWidget(list_frame, 1)

        # Selected document display
        self.selected_frame = QFrame()
        self.selected_frame.setFixedHeight(45)
        self.selected_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.MUTED};
                border-radius: {SPACING.CORNER_RADIUS}px;
            }}
        """)
        selected_layout = QVBoxLayout(self.selected_frame)
        selected_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.selected_label = QLabel("No document selected")
        self.selected_label.setFont(TYPOGRAPHY.body)
        self.selected_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        self.selected_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        selected_layout.addWidget(self.selected_label)

        layout.addWidget(self.selected_frame)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 36)
        style_button(cancel_btn, "secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self.link_btn = QPushButton("Create Link")
        self.link_btn.setFixedSize(120, 36)
        style_button(self.link_btn, "primary")
        self.link_btn.setEnabled(False)
        self.link_btn.clicked.connect(self._on_create_link)
        btn_row.addWidget(self.link_btn)

        layout.addLayout(btn_row)

    def _style_input(self, widget: QLineEdit) -> None:
        """Apply input styling."""
        widget.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS.BACKGROUND};
                border: 1px solid {COLORS.BORDER};
                border-radius: 4px;
                padding: 8px 12px;
                color: {COLORS.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {COLORS.PRIMARY};
            }}
        """)

    def _style_dropdown(self, widget: QComboBox) -> None:
        """Apply dropdown styling."""
        widget.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS.BACKGROUND};
                border: 1px solid {COLORS.BORDER};
                border-radius: 4px;
                padding: 6px 12px;
                color: {COLORS.TEXT_PRIMARY};
            }}
            QComboBox:hover {{
                border-color: {COLORS.PRIMARY};
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS.CARD};
                border: 1px solid {COLORS.BORDER};
                selection-background-color: {COLORS.PRIMARY};
                selection-color: {COLORS.PRIMARY_FOREGROUND};
            }}
        """)

    def _on_search(self, text: str) -> None:
        """Handle search input change."""
        self._load_available_documents(text)

    def _load_available_documents(self, search_term: str = "") -> None:
        """Load available documents for linking."""
        # Clear existing list
        while self.doc_list_layout.count():
            item = self.doc_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get available documents
        search = search_term.strip() if search_term else None
        self.available_docs = self.link_service.get_available_documents_for_linking(
            self.source_doc_id,
            search_term=search,
        )

        if not self.available_docs:
            no_docs_label = QLabel(
                "No documents available for linking." if not search else "No matching documents found."
            )
            no_docs_label.setFont(TYPOGRAPHY.body)
            no_docs_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
            no_docs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.doc_list_layout.addWidget(no_docs_label)
            return

        # Display documents
        for doc in self.available_docs:
            self._create_doc_row(doc)

        self.doc_list_layout.addStretch()

    def _create_doc_row(self, doc: dict) -> None:
        """Create a row for a document in the list."""
        is_selected = self.selected_doc and self.selected_doc["doc_id"] == doc["doc_id"]

        row = QFrame()
        row.setFixedHeight(40)
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.PRIMARY if is_selected else 'transparent'};
                border-radius: 4px;
            }}
            QFrame:hover {{
                background-color: {COLORS.PRIMARY if is_selected else COLORS.MUTED};
            }}
        """)
        row.mousePressEvent = lambda e, d=doc: self._select_document(d)

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(10, 5, 10, 5)

        # Reference
        ref_label = QLabel(doc["doc_ref"])
        ref_label.setFont(TYPOGRAPHY.body)
        ref_label.setStyleSheet(f"""
            color: {COLORS.PRIMARY_FOREGROUND if is_selected else COLORS.TEXT_PRIMARY};
            background: transparent;
            font-weight: bold;
        """)
        ref_label.setFixedWidth(120)
        row_layout.addWidget(ref_label)

        # Title
        title_text = doc["title"][:40] + "..." if len(doc["title"]) > 40 else doc["title"]
        title_label = QLabel(title_text)
        title_label.setFont(TYPOGRAPHY.body)
        title_label.setStyleSheet(f"""
            color: {COLORS.PRIMARY_FOREGROUND if is_selected else COLORS.TEXT_PRIMARY};
            background: transparent;
        """)
        row_layout.addWidget(title_label, 1)

        # Type badge
        type_label = QLabel(doc["doc_type"])
        type_label.setFont(TYPOGRAPHY.small)
        type_label.setStyleSheet(f"""
            color: {COLORS.PRIMARY_FOREGROUND if is_selected else COLORS.TEXT_SECONDARY};
            background: transparent;
        """)
        row_layout.addWidget(type_label)

        self.doc_list_layout.addWidget(row)

    def _select_document(self, doc: dict) -> None:
        """Select a document for linking."""
        self.selected_doc = doc

        # Update selected display
        self.selected_label.setText(f"Selected: {doc['doc_ref']} - {doc['title'][:50]}")
        self.selected_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")

        # Enable link button
        self.link_btn.setEnabled(True)

        # Refresh list to show selection
        self._load_available_documents(self.search_entry.text())

    def _on_create_link(self) -> None:
        """Handle create link button click."""
        if not self.selected_doc:
            InfoDialog.show_error(self, "Error", "Please select a document to link.")
            return

        # Get selected link type
        selected_index = self.link_type_dropdown.currentIndex()
        link_type = self.link_types[selected_index][0]
        target_doc_id = self.selected_doc["doc_id"]

        # Set result as tuple of (target_doc_id, link_type)
        self.result = (target_doc_id, link_type)
        self.accept()
