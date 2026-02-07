"""
PolicyHub Document Dialog (PySide6)

Dialog for creating and editing documents.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QFrame,
    QScrollArea,
    QFileDialog,
)

from app.constants import (
    ALLOWED_EXTENSIONS,
    DocumentStatus,
    DocumentType,
    LinkType,
    MAX_FILE_SIZE_MB,
    ReviewFrequency,
)
from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button
from core.database import DatabaseManager
from ui.dialogs.base_dialog import BaseDialog
from ui.dialogs.confirm_dialog import InfoDialog
from models.category import Category
from models.document import Document, DocumentCreate, DocumentUpdate
from services.attachment_service import AttachmentService
from services.document_service import DocumentService
from services.entity_service import EntityService
from services.link_service import LinkService
from utils.dates import calculate_next_review, get_today, parse_display_date, format_date
from utils.files import format_file_size, get_file_size
from utils.validators import (
    validate_document_ref,
    validate_file_upload,
    validate_required,
    validate_version,
)


class DocumentDialog(BaseDialog):
    """
    Dialog for adding or editing a document.

    Usage:
        dialog = DocumentDialog(parent, db, categories=cat_list)
        if dialog.exec():
            result = dialog.result  # Document
    """

    def __init__(
        self,
        parent: QWidget,
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

        # Services
        self.doc_service = DocumentService(db)
        self.entity_service = EntityService(db)
        self.attachment_service = AttachmentService(db)
        self.link_service = LinkService(db)

        # Pending items
        self.pending_attachments: List[Tuple[Path, str]] = []
        self.pending_links: List[Tuple[str, str, str]] = []

        # Entity tracking
        self._entity_names = self.entity_service.get_entity_names()
        self._entity_checkboxes: dict = {}

        title = "Edit Document" if self.is_edit else "Add New Document"
        super().__init__(parent, title, width=850, height=900)

        self._build_ui()
        if self.is_edit:
            self._populate_form()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        # Scrollable form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"background-color: {COLORS.CARD}; border-radius: {SPACING.CORNER_RADIUS}px;")

        form = QWidget()
        form.setStyleSheet("background: transparent;")
        self.form_layout = QVBoxLayout(form)
        self.form_layout.setContentsMargins(15, 15, 15, 15)
        self.form_layout.setSpacing(12)

        self._build_form()

        scroll.setWidget(form)
        layout.addWidget(scroll, 1)

        # Footer
        footer = QWidget()
        footer.setFixedHeight(50)
        footer.setStyleSheet("background: transparent;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 15, 0, 0)
        footer_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 36)
        style_button(cancel_btn, "secondary")
        cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Document")
        save_btn.setFixedSize(130, 36)
        style_button(save_btn, "primary")
        save_btn.clicked.connect(self._on_save)
        footer_layout.addWidget(save_btn)

        layout.addWidget(footer)

    def _build_form(self) -> None:
        """Build all form fields."""
        # Document Type
        self._create_label("Document Type *")
        type_row = QHBoxLayout()
        type_row.setSpacing(8)

        self.type_group = QButtonGroup(self)
        for doc_type in DocumentType:
            rb = QRadioButton(doc_type.display_name)
            rb.setFont(TYPOGRAPHY.body)
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            rb.setStyleSheet(f"""
                QRadioButton {{
                    color: {COLORS.TEXT_PRIMARY};
                    background-color: {COLORS.MUTED};
                    padding: 10px 20px;
                    border-radius: 6px;
                    border: 1px solid transparent;
                }}
                QRadioButton:checked {{
                    background-color: {COLORS.PRIMARY};
                    color: {COLORS.PRIMARY_FOREGROUND};
                }}
                QRadioButton:hover:!checked {{
                    background-color: {COLORS.SECONDARY};
                    border: 1px solid {COLORS.BORDER};
                }}
                QRadioButton::indicator {{
                    width: 0px;
                    height: 0px;
                    margin: 0px;
                    padding: 0px;
                }}
            """)
            rb.setProperty("doc_type", doc_type.value)
            if doc_type == DocumentType.POLICY:
                rb.setChecked(True)
            rb.toggled.connect(self._on_type_change)
            self.type_group.addButton(rb)
            type_row.addWidget(rb)

        type_row.addStretch()
        self.form_layout.addLayout(type_row)

        # Reference and Version row
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        # Reference
        ref_frame = QWidget()
        ref_frame.setStyleSheet("background: transparent;")
        ref_layout = QVBoxLayout(ref_frame)
        ref_layout.setContentsMargins(0, 0, 0, 0)
        ref_layout.setSpacing(4)

        ref_label = QLabel("Reference Code *")
        ref_label.setFont(TYPOGRAPHY.body)
        ref_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        ref_layout.addWidget(ref_label)

        self.ref_entry = QLineEdit()
        self.ref_entry.setPlaceholderText("e.g., POL-AML-001")
        self.ref_entry.setFixedHeight(36)
        self.ref_entry.setFont(TYPOGRAPHY.body)
        self._style_input(self.ref_entry)
        ref_layout.addWidget(self.ref_entry)

        if not self.is_edit:
            suggest_btn = QPushButton("Suggest")
            suggest_btn.setFixedSize(70, 28)
            suggest_btn.setFont(TYPOGRAPHY.small)
            style_button(suggest_btn, "secondary")
            suggest_btn.clicked.connect(self._suggest_ref)
            ref_layout.addWidget(suggest_btn)

        row1.addWidget(ref_frame, 2)

        # Version
        ver_frame = QWidget()
        ver_frame.setStyleSheet("background: transparent;")
        ver_layout = QVBoxLayout(ver_frame)
        ver_layout.setContentsMargins(0, 0, 0, 0)
        ver_layout.setSpacing(4)

        ver_label = QLabel("Version *")
        ver_label.setFont(TYPOGRAPHY.body)
        ver_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        ver_layout.addWidget(ver_label)

        self.version_entry = QLineEdit()
        self.version_entry.setText("1.0")
        self.version_entry.setPlaceholderText("e.g., 1.0")
        self.version_entry.setFixedHeight(36)
        self.version_entry.setFont(TYPOGRAPHY.body)
        self._style_input(self.version_entry)
        ver_layout.addWidget(self.version_entry)

        if not self.is_edit:
            ver_layout.addSpacing(28)

        row1.addWidget(ver_frame, 1)
        self.form_layout.addLayout(row1)

        # Title
        self._create_label("Title *")
        self.title_entry = QLineEdit()
        self.title_entry.setPlaceholderText("Enter document title")
        self.title_entry.setFixedHeight(36)
        self.title_entry.setFont(TYPOGRAPHY.body)
        self._style_input(self.title_entry)
        self.form_layout.addWidget(self.title_entry)

        # Category and Status row
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        # Category
        cat_frame = self._create_dropdown_field("Category *", 250)
        self.category_dropdown = cat_frame.findChild(QComboBox)
        category_values = [f"{c.code} - {c.name}" for c in self.categories]
        self.category_dropdown.addItems(category_values)
        self.category_dropdown.currentTextChanged.connect(self._on_category_change)
        row2.addWidget(cat_frame, 1)

        # Status
        status_frame = self._create_dropdown_field("Status *", 200)
        self.status_dropdown = status_frame.findChild(QComboBox)
        status_values = [s.display_name for s in DocumentStatus]
        self.status_dropdown.addItems(status_values)
        row2.addWidget(status_frame, 1)

        self.form_layout.addLayout(row2)

        # Owner and Approver row
        row3 = QHBoxLayout()
        row3.setSpacing(10)

        # Owner
        owner_frame = QWidget()
        owner_frame.setStyleSheet("background: transparent;")
        owner_layout = QVBoxLayout(owner_frame)
        owner_layout.setContentsMargins(0, 0, 0, 0)
        owner_layout.setSpacing(4)

        owner_label = QLabel("Owner *")
        owner_label.setFont(TYPOGRAPHY.body)
        owner_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        owner_layout.addWidget(owner_label)

        self.owner_entry = QLineEdit()
        self.owner_entry.setPlaceholderText("Responsible person or role")
        self.owner_entry.setFixedHeight(36)
        self.owner_entry.setFont(TYPOGRAPHY.body)
        self._style_input(self.owner_entry)
        owner_layout.addWidget(self.owner_entry)
        row3.addWidget(owner_frame, 1)

        # Approver
        approver_frame = QWidget()
        approver_frame.setStyleSheet("background: transparent;")
        approver_layout = QVBoxLayout(approver_frame)
        approver_layout.setContentsMargins(0, 0, 0, 0)
        approver_layout.setSpacing(4)

        approver_label = QLabel("Approver")
        approver_label.setFont(TYPOGRAPHY.body)
        approver_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        approver_layout.addWidget(approver_label)

        self.approver_entry = QLineEdit()
        self.approver_entry.setPlaceholderText("Final approver (optional)")
        self.approver_entry.setFixedHeight(36)
        self.approver_entry.setFont(TYPOGRAPHY.body)
        self._style_input(self.approver_entry)
        approver_layout.addWidget(self.approver_entry)
        row3.addWidget(approver_frame, 1)

        self.form_layout.addLayout(row3)

        # Description
        self._create_label("Description")
        self.description_text = QTextEdit()
        self.description_text.setMinimumHeight(60)
        self.description_text.setMaximumHeight(120)
        self.description_text.setFont(TYPOGRAPHY.body)
        self.description_text.setPlaceholderText("Brief description of the document purpose...")
        self._style_textbox(self.description_text)
        self.form_layout.addWidget(self.description_text)

        # Review Settings
        self._create_label("Review Settings")
        row4 = QHBoxLayout()
        row4.setSpacing(10)

        # Frequency
        freq_frame = self._create_dropdown_field("Frequency *", 150, small_label=True)
        self.frequency_dropdown = freq_frame.findChild(QComboBox)
        freq_values = [f.display_name for f in ReviewFrequency]
        self.frequency_dropdown.addItems(freq_values)
        self.frequency_dropdown.setCurrentText(ReviewFrequency.ANNUAL.display_name)
        self.frequency_dropdown.currentTextChanged.connect(self._on_frequency_change)
        row4.addWidget(freq_frame, 1)

        # Effective Date
        eff_frame = self._create_input_field("Effective Date *", "DD/MM/YYYY", small_label=True)
        self.effective_entry = eff_frame.findChild(QLineEdit)
        self.effective_entry.setText(format_date(get_today()))
        row4.addWidget(eff_frame, 1)

        # Last Review Date
        last_frame = self._create_input_field("Last Review *", "DD/MM/YYYY", small_label=True)
        self.last_review_entry = last_frame.findChild(QLineEdit)
        self.last_review_entry.setText(format_date(get_today()))
        self.last_review_entry.editingFinished.connect(self._calculate_next_review)
        row4.addWidget(last_frame, 1)

        self.form_layout.addLayout(row4)

        # Next Review Date
        row5 = QHBoxLayout()
        row5.setSpacing(10)

        next_frame = self._create_input_field("Next Review *", "DD/MM/YYYY", small_label=True, width=150)
        self.next_review_entry = next_frame.findChild(QLineEdit)
        row5.addWidget(next_frame, 0)

        calc_btn = QPushButton("Calculate")
        calc_btn.setFixedSize(80, 28)
        calc_btn.setFont(TYPOGRAPHY.small)
        style_button(calc_btn, "secondary")
        calc_btn.clicked.connect(self._calculate_next_review)
        row5.addWidget(calc_btn, 0, Qt.AlignmentFlag.AlignBottom)
        row5.addStretch()

        self.form_layout.addLayout(row5)
        self._calculate_next_review()

        # Notes
        self._create_label("Notes")
        self.notes_text = QTextEdit()
        self.notes_text.setMinimumHeight(60)
        self.notes_text.setMaximumHeight(150)
        self.notes_text.setFont(TYPOGRAPHY.body)
        self.notes_text.setPlaceholderText("Additional notes or comments...")
        self._style_textbox(self.notes_text)
        self.form_layout.addWidget(self.notes_text)

        # Attachments
        self._create_label("Attachments")
        self._build_attachments_section()

        # Linked Documents
        self._create_label("Linked Documents")
        self._build_links_section()

        # Additional Settings
        self._create_label("Additional Settings")
        self._build_additional_settings()

    def _create_label(self, text: str) -> None:
        """Create a form label."""
        label = QLabel(text)
        label.setFont(TYPOGRAPHY.body)
        label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        self.form_layout.addWidget(label)

    def _create_dropdown_field(self, label: str, width: int, small_label: bool = False) -> QWidget:
        """Create a dropdown field with label."""
        frame = QWidget()
        frame.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl = QLabel(label)
        lbl.setFont(TYPOGRAPHY.small if small_label else TYPOGRAPHY.body)
        lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY if small_label else COLORS.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(lbl)

        dropdown = QComboBox()
        dropdown.setFixedWidth(width)
        dropdown.setFixedHeight(36)
        dropdown.setFont(TYPOGRAPHY.body)
        self._style_dropdown(dropdown)
        layout.addWidget(dropdown)

        return frame

    def _create_input_field(self, label: str, placeholder: str, small_label: bool = False, width: int = None) -> QWidget:
        """Create an input field with label."""
        frame = QWidget()
        frame.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl = QLabel(label)
        lbl.setFont(TYPOGRAPHY.small if small_label else TYPOGRAPHY.body)
        lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY if small_label else COLORS.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(lbl)

        entry = QLineEdit()
        entry.setPlaceholderText(placeholder)
        entry.setFixedHeight(36)
        if width:
            entry.setFixedWidth(width)
        entry.setFont(TYPOGRAPHY.body)
        self._style_input(entry)
        layout.addWidget(entry)

        return frame

    def _style_input(self, widget: QLineEdit) -> None:
        """Apply input styling."""
        widget.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS.CARD};
                border: 1px solid {COLORS.BORDER};
                border-radius: 4px;
                padding: 0 12px;
                color: {COLORS.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {COLORS.PRIMARY};
            }}
        """)

    def _style_textbox(self, widget: QTextEdit) -> None:
        """Apply textbox styling."""
        widget.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS.CARD};
                border: 1px solid {COLORS.BORDER};
                border-radius: 4px;
                padding: 8px;
                color: {COLORS.TEXT_PRIMARY};
            }}
        """)

    def _style_dropdown(self, widget: QComboBox) -> None:
        """Apply dropdown styling."""
        widget.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS.CARD};
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

    def _build_attachments_section(self) -> None:
        """Build attachments section."""
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.MUTED};
                border-radius: {SPACING.CORNER_RADIUS}px;
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(5)

        self.attachment_list = QWidget()
        self.attachment_list.setStyleSheet("background: transparent;")
        self.attachment_list_layout = QVBoxLayout(self.attachment_list)
        self.attachment_list_layout.setContentsMargins(0, 0, 0, 0)
        self.attachment_list_layout.setSpacing(4)
        container_layout.addWidget(self.attachment_list)

        add_btn = QPushButton("+ Add Attachment")
        add_btn.setFixedSize(140, 30)
        add_btn.setFont(TYPOGRAPHY.small)
        style_button(add_btn, "secondary")
        add_btn.clicked.connect(self._on_add_attachment)
        container_layout.addWidget(add_btn, 0, Qt.AlignmentFlag.AlignLeft)

        help_text = f"Allowed: {', '.join(ALLOWED_EXTENSIONS[:5])}... | Max: {MAX_FILE_SIZE_MB} MB"
        help_label = QLabel(help_text)
        help_label.setFont(TYPOGRAPHY.small)
        help_label.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; background: transparent;")
        container_layout.addWidget(help_label)

        self.form_layout.addWidget(container)
        self._refresh_attachment_list()

    def _build_links_section(self) -> None:
        """Build linked documents section."""
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.MUTED};
                border-radius: {SPACING.CORNER_RADIUS}px;
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(5)

        self.link_list = QWidget()
        self.link_list.setStyleSheet("background: transparent;")
        self.link_list_layout = QVBoxLayout(self.link_list)
        self.link_list_layout.setContentsMargins(0, 0, 0, 0)
        self.link_list_layout.setSpacing(4)
        container_layout.addWidget(self.link_list)

        add_btn = QPushButton("+ Add Link")
        add_btn.setFixedSize(100, 30)
        add_btn.setFont(TYPOGRAPHY.small)
        style_button(add_btn, "secondary")
        add_btn.clicked.connect(self._on_add_link)
        container_layout.addWidget(add_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self.form_layout.addWidget(container)
        self._refresh_link_list()

    def _build_additional_settings(self) -> None:
        """Build additional settings section."""
        row = QHBoxLayout()
        row.setSpacing(24)  # More spacing between sections

        # Applicable Entities
        entity_frame = QWidget()
        entity_frame.setStyleSheet("background: transparent;")
        entity_layout = QVBoxLayout(entity_frame)
        entity_layout.setContentsMargins(0, 0, 0, 0)
        entity_layout.setSpacing(6)

        # Entity label row with "All" button
        entity_header = QHBoxLayout()
        entity_header.setSpacing(8)

        entity_label = QLabel("Applicable Entities")
        entity_label.setFont(TYPOGRAPHY.small)
        entity_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        entity_header.addWidget(entity_label)

        entity_header.addStretch()

        # Select All / Clear All buttons
        select_all_btn = QPushButton("All")
        select_all_btn.setFixedSize(40, 22)
        select_all_btn.setFont(TYPOGRAPHY.small)
        select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        select_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.MUTED};
                color: {COLORS.TEXT_PRIMARY};
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.SECONDARY};
            }}
        """)
        select_all_btn.clicked.connect(self._on_select_all_entities)
        entity_header.addWidget(select_all_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedSize(45, 22)
        clear_btn.setFont(TYPOGRAPHY.small)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.MUTED};
                color: {COLORS.TEXT_PRIMARY};
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.SECONDARY};
            }}
        """)
        clear_btn.clicked.connect(self._on_clear_all_entities)
        entity_header.addWidget(clear_btn)

        entity_layout.addLayout(entity_header)

        entity_scroll = QScrollArea()
        entity_scroll.setWidgetResizable(True)
        entity_scroll.setFixedHeight(100)
        entity_scroll.setStyleSheet(f"background-color: {COLORS.CARD}; border: 1px solid {COLORS.BORDER}; border-radius: 4px;")

        entity_content = QWidget()
        entity_content.setStyleSheet("background: transparent;")
        entity_content_layout = QVBoxLayout(entity_content)
        entity_content_layout.setContentsMargins(8, 8, 8, 8)
        entity_content_layout.setSpacing(4)

        # Store reference to content layout for adding new entities
        self._entity_content_layout = entity_content_layout
        self._entity_scroll_content = entity_content

        if self._entity_names:
            for name in self._entity_names:
                cb = QCheckBox(name)
                cb.setFont(TYPOGRAPHY.small)
                cb.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
                self._entity_checkboxes[name] = cb
                entity_content_layout.addWidget(cb)
        else:
            self._no_entity_label = QLabel("No entities defined yet")
            self._no_entity_label.setFont(TYPOGRAPHY.small)
            self._no_entity_label.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; background: transparent;")
            entity_content_layout.addWidget(self._no_entity_label)

        entity_content_layout.addStretch()
        entity_scroll.setWidget(entity_content)
        entity_layout.addWidget(entity_scroll)

        # Add new entity row
        add_entity_row = QHBoxLayout()
        add_entity_row.setSpacing(5)

        self.new_entity_entry = QLineEdit()
        self.new_entity_entry.setPlaceholderText("New entity name...")
        self.new_entity_entry.setFixedHeight(28)
        self.new_entity_entry.setFont(TYPOGRAPHY.small)
        self._style_input(self.new_entity_entry)
        self.new_entity_entry.returnPressed.connect(self._on_add_entity)
        add_entity_row.addWidget(self.new_entity_entry)

        add_entity_btn = QPushButton("Add")
        add_entity_btn.setFixedSize(50, 28)
        add_entity_btn.setFont(TYPOGRAPHY.small)
        style_button(add_entity_btn, "secondary")
        add_entity_btn.clicked.connect(self._on_add_entity)
        add_entity_row.addWidget(add_entity_btn)

        entity_layout.addLayout(add_entity_row)

        help_text = QLabel("Leave empty for all entities")
        help_text.setFont(TYPOGRAPHY.small)
        help_text.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; background: transparent;")
        entity_layout.addWidget(help_text)

        row.addWidget(entity_frame, 1)

        # Mandatory Read - with more visual separation
        mandatory_frame = QWidget()
        mandatory_frame.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS.MUTED};
                border-radius: 8px;
            }}
        """)
        mandatory_layout = QVBoxLayout(mandatory_frame)
        mandatory_layout.setContentsMargins(16, 12, 16, 12)
        mandatory_layout.setSpacing(8)

        mandatory_label = QLabel("Policy Settings")
        mandatory_label.setFont(TYPOGRAPHY.get_font(12, TYPOGRAPHY.WEIGHT_SEMIBOLD))
        mandatory_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        mandatory_layout.addWidget(mandatory_label)

        self.mandatory_checkbox = QCheckBox("Mandatory Read for All")
        self.mandatory_checkbox.setFont(TYPOGRAPHY.body)
        self.mandatory_checkbox.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        mandatory_layout.addWidget(self.mandatory_checkbox)

        mandatory_help = QLabel("Employees must read and acknowledge\nthis document")
        mandatory_help.setFont(TYPOGRAPHY.small)
        mandatory_help.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; background: transparent;")
        mandatory_layout.addWidget(mandatory_help)

        mandatory_layout.addStretch()
        row.addWidget(mandatory_frame, 1)

        self.form_layout.addLayout(row)

    def _on_add_entity(self) -> None:
        """Handle adding a new entity."""
        entity_name = self.new_entity_entry.text().strip()
        if not entity_name:
            return

        # Check if entity already exists
        if entity_name in self._entity_checkboxes:
            # Just check the existing checkbox
            self._entity_checkboxes[entity_name].setChecked(True)
            self.new_entity_entry.clear()
            return

        # Remove "no entities" label if present
        if hasattr(self, '_no_entity_label') and self._no_entity_label:
            self._no_entity_label.setParent(None)
            self._no_entity_label.deleteLater()
            self._no_entity_label = None

        # Create new checkbox
        cb = QCheckBox(entity_name)
        cb.setFont(TYPOGRAPHY.small)
        cb.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        cb.setChecked(True)  # Auto-check newly added entity
        self._entity_checkboxes[entity_name] = cb

        # Insert before the stretch (last item)
        count = self._entity_content_layout.count()
        self._entity_content_layout.insertWidget(count - 1, cb)

        # Clear input
        self.new_entity_entry.clear()

    def _on_select_all_entities(self) -> None:
        """Select all entity checkboxes."""
        for cb in self._entity_checkboxes.values():
            cb.setChecked(True)

    def _on_clear_all_entities(self) -> None:
        """Clear all entity checkboxes."""
        for cb in self._entity_checkboxes.values():
            cb.setChecked(False)

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
        """Suggest a reference code."""
        checked = self.type_group.checkedButton()
        doc_type = checked.property("doc_type") if checked else DocumentType.POLICY.value
        cat_value = self.category_dropdown.currentText()

        if cat_value:
            category = cat_value.split(" - ")[0]
            suggested = self.doc_service.suggest_ref(doc_type, category)
            self.ref_entry.setText(suggested)

    def _calculate_next_review(self) -> None:
        """Calculate next review date."""
        last_review_display = self.last_review_entry.text()
        last_review_iso = parse_display_date(last_review_display)

        if not last_review_iso:
            return

        freq_display = self.frequency_dropdown.currentText()
        frequency = None
        for f in ReviewFrequency:
            if f.display_name == freq_display:
                frequency = f.value
                break

        if frequency:
            next_date = calculate_next_review(last_review_iso, frequency)
            if next_date:
                self.next_review_entry.setText(format_date(next_date))

    def _populate_form(self) -> None:
        """Populate form with existing document data."""
        doc = self.document

        # Type
        for btn in self.type_group.buttons():
            if btn.property("doc_type") == doc.doc_type:
                btn.setChecked(True)
                break

        self.ref_entry.setText(doc.doc_ref)
        self.version_entry.setText(doc.version)
        self.title_entry.setText(doc.title)

        # Category
        for cat in self.categories:
            if cat.code == doc.category:
                index = self.category_dropdown.findText(f"{cat.code} - {cat.name}")
                if index >= 0:
                    self.category_dropdown.setCurrentIndex(index)
                break

        # Status
        for status in DocumentStatus:
            if status.value == doc.status:
                index = self.status_dropdown.findText(status.display_name)
                if index >= 0:
                    self.status_dropdown.setCurrentIndex(index)
                break

        self.owner_entry.setText(doc.owner)
        self.approver_entry.setText(doc.approver or "")

        if doc.description:
            self.description_text.setPlainText(doc.description)

        # Frequency
        for freq in ReviewFrequency:
            if freq.value == doc.review_frequency:
                index = self.frequency_dropdown.findText(freq.display_name)
                if index >= 0:
                    self.frequency_dropdown.setCurrentIndex(index)
                break

        self.effective_entry.setText(format_date(doc.effective_date))
        self.last_review_entry.setText(format_date(doc.last_review_date))
        self.next_review_entry.setText(format_date(doc.next_review_date))

        if doc.notes:
            self.notes_text.setPlainText(doc.notes)

        self.mandatory_checkbox.setChecked(doc.mandatory_read_all)

        # Entities
        if doc.applicable_entity:
            entities = EntityService.parse_entities(doc.applicable_entity)
            for name in entities:
                if name in self._entity_checkboxes:
                    self._entity_checkboxes[name].setChecked(True)

    def _on_add_attachment(self) -> None:
        """Handle add attachment."""
        all_supported = " ".join(f"*{ext}" for ext in ALLOWED_EXTENSIONS)
        file_filter = f"All supported ({all_supported});;PDF (*.pdf);;Word (*.doc *.docx);;All (*.*)"

        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", file_filter)

        if file_path:
            path = Path(file_path)
            if not path.exists():
                InfoDialog.show_error(self, "Error", "File does not exist.")
                return

            file_size = get_file_size(path)
            is_valid, error = validate_file_upload(path.name, file_size)
            if not is_valid:
                InfoDialog.show_error(self, "Invalid File", error)
                return

            version = self.version_entry.text().strip() or "1.0"
            self.pending_attachments.append((path, version))
            self._refresh_attachment_list()

    def _remove_attachment(self, index: int) -> None:
        """Remove pending attachment."""
        if 0 <= index < len(self.pending_attachments):
            self.pending_attachments.pop(index)
            self._refresh_attachment_list()

    def _refresh_attachment_list(self) -> None:
        """Refresh attachment list."""
        while self.attachment_list_layout.count():
            item = self.attachment_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.pending_attachments:
            no_attach = QLabel("No attachments added")
            no_attach.setFont(TYPOGRAPHY.small)
            no_attach.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; background: transparent;")
            self.attachment_list_layout.addWidget(no_attach)
            return

        for idx, (path, version) in enumerate(self.pending_attachments):
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)

            size_str = format_file_size(get_file_size(path))
            label = QLabel(f"{path.name} ({size_str}) - v{version}")
            label.setFont(TYPOGRAPHY.small)
            label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
            row_layout.addWidget(label)
            row_layout.addStretch()

            remove_btn = QPushButton("×")
            remove_btn.setFixedSize(24, 24)
            remove_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS.DANGER};
                    color: white;
                    border: none;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: #dc2626;
                }}
            """)
            remove_btn.clicked.connect(lambda checked, i=idx: self._remove_attachment(i))
            row_layout.addWidget(remove_btn)

            self.attachment_list_layout.addWidget(row)

    def _on_add_link(self) -> None:
        """Handle add link."""
        from ui.dialogs.link_dialog import LinkDialog

        exclude_id = self.document.doc_id if self.is_edit else None
        dialog = LinkDialog(
            self,
            self.db,
            source_doc_id=exclude_id or "",
            source_doc_ref=self.ref_entry.text() or "New Document",
        )

        if dialog.exec() and dialog.result:
            target_doc_id, link_type = dialog.result
            # Get doc_ref from available docs
            doc_ref = target_doc_id  # Fallback
            available = self.link_service.get_available_documents_for_linking(exclude_id)
            for d in available:
                if d["doc_id"] == target_doc_id:
                    doc_ref = d["doc_ref"]
                    break
            self.pending_links.append((target_doc_id, link_type, doc_ref))
            self._refresh_link_list()

    def _remove_link(self, index: int) -> None:
        """Remove pending link."""
        if 0 <= index < len(self.pending_links):
            self.pending_links.pop(index)
            self._refresh_link_list()

    def _refresh_link_list(self) -> None:
        """Refresh link list."""
        while self.link_list_layout.count():
            item = self.link_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.pending_links:
            no_link = QLabel("No linked documents")
            no_link.setFont(TYPOGRAPHY.small)
            no_link.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; background: transparent;")
            self.link_list_layout.addWidget(no_link)
            return

        for idx, (doc_id, link_type, doc_ref) in enumerate(self.pending_links):
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)

            link_display = link_type.replace("_", " ").title()
            label = QLabel(f"{doc_ref} ({link_display})")
            label.setFont(TYPOGRAPHY.small)
            label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
            row_layout.addWidget(label)
            row_layout.addStretch()

            remove_btn = QPushButton("×")
            remove_btn.setFixedSize(24, 24)
            remove_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS.DANGER};
                    color: white;
                    border: none;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: #dc2626;
                }}
            """)
            remove_btn.clicked.connect(lambda checked, i=idx: self._remove_link(i))
            row_layout.addWidget(remove_btn)

            self.link_list_layout.addWidget(row)

    def _get_selected_entities(self) -> Optional[str]:
        """Get selected entities as semicolon-separated string."""
        selected = [name for name, cb in self._entity_checkboxes.items() if cb.isChecked()]
        if not selected:
            return None
        return ";".join(selected)

    def _validate_form(self) -> Tuple[bool, str]:
        """Validate form fields."""
        ref_valid, ref_err = validate_required(self.ref_entry.text(), "Reference code")
        if not ref_valid:
            return False, ref_err

        ref_result = validate_document_ref(self.ref_entry.text())
        if not ref_result[0]:
            return False, ref_result[1]

        title_valid, title_err = validate_required(self.title_entry.text(), "Title")
        if not title_valid:
            return False, title_err

        if len(self.title_entry.text()) < 5:
            return False, "Title must be at least 5 characters"

        owner_valid, owner_err = validate_required(self.owner_entry.text(), "Owner")
        if not owner_valid:
            return False, owner_err

        version_result = validate_version(self.version_entry.text())
        if not version_result[0]:
            return False, version_result[1]

        if not parse_display_date(self.effective_entry.text()):
            return False, "Invalid effective date format (use DD/MM/YYYY)"

        if not parse_display_date(self.last_review_entry.text()):
            return False, "Invalid last review date format (use DD/MM/YYYY)"

        if not parse_display_date(self.next_review_entry.text()):
            return False, "Invalid next review date format (use DD/MM/YYYY)"

        if not self.is_edit:
            if self.doc_service.doc_ref_exists(self.ref_entry.text()):
                return False, f"Reference '{self.ref_entry.text()}' already exists"
        else:
            if self.doc_service.doc_ref_exists(self.ref_entry.text(), exclude_id=self.document.doc_id):
                return False, f"Reference '{self.ref_entry.text()}' already exists"

        return True, ""

    def _get_form_data(self) -> dict:
        """Get form data as dictionary."""
        cat_display = self.category_dropdown.currentText()
        category = cat_display.split(" - ")[0] if cat_display else ""

        status_display = self.status_dropdown.currentText()
        status = DocumentStatus.ACTIVE.value
        for s in DocumentStatus:
            if s.display_name == status_display:
                status = s.value
                break

        freq_display = self.frequency_dropdown.currentText()
        frequency = ReviewFrequency.ANNUAL.value
        for f in ReviewFrequency:
            if f.display_name == freq_display:
                frequency = f.value
                break

        checked = self.type_group.checkedButton()
        doc_type = checked.property("doc_type") if checked else DocumentType.POLICY.value

        return {
            "doc_type": doc_type,
            "doc_ref": self.ref_entry.text().upper(),
            "title": self.title_entry.text().strip(),
            "category": category,
            "owner": self.owner_entry.text().strip(),
            "approver": self.approver_entry.text().strip() or None,
            "status": status,
            "version": self.version_entry.text().strip(),
            "description": self.description_text.toPlainText().strip() or None,
            "review_frequency": frequency,
            "effective_date": parse_display_date(self.effective_entry.text()),
            "last_review_date": parse_display_date(self.last_review_entry.text()),
            "next_review_date": parse_display_date(self.next_review_entry.text()),
            "notes": self.notes_text.toPlainText().strip() or None,
            "mandatory_read_all": self.mandatory_checkbox.isChecked(),
            "applicable_entity": self._get_selected_entities(),
        }

    def _on_save(self) -> None:
        """Handle save button click."""
        is_valid, error = self._validate_form()
        if not is_valid:
            InfoDialog.show_error(self, "Validation Error", error)
            return

        try:
            data = self._get_form_data()

            if data.get("applicable_entity"):
                self.entity_service.ensure_entities_exist(data["applicable_entity"])

            if self.is_edit:
                update_data = DocumentUpdate(**{k: v for k, v in data.items() if k not in ("doc_type", "doc_ref")})
                self.result = self.doc_service.update_document(self.document.doc_id, update_data)
                doc_id = self.document.doc_id
            else:
                create_data = DocumentCreate(**data)
                self.result = self.doc_service.create_document(create_data)
                doc_id = self.result.doc_id

            doc_ref = self.result.doc_ref if self.result else self.document.doc_ref

            for file_path, version in self.pending_attachments:
                try:
                    self.attachment_service.add_attachment(
                        doc_id=doc_id,
                        doc_ref=doc_ref,
                        source_path=file_path,
                        version_label=version,
                    )
                except Exception as e:
                    InfoDialog.show_error(self, "Attachment Error", f"Failed to add {file_path.name}: {str(e)}")

            for target_doc_id, link_type, _ in self.pending_links:
                try:
                    self.link_service.create_link(doc_id, target_doc_id, link_type)
                except Exception as e:
                    InfoDialog.show_error(self, "Link Error", f"Failed to create link: {str(e)}")

            self.accept()

        except PermissionError as e:
            InfoDialog.show_error(self, "Permission Denied", str(e))
        except ValueError as e:
            InfoDialog.show_error(self, "Error", str(e))
        except Exception as e:
            InfoDialog.show_error(self, "Error", f"Failed to save document: {str(e)}")
