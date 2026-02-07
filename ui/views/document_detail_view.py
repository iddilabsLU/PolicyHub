"""
PolicyHub Document Detail View (PySide6)

Displays complete information for a single document with actions.
"""

import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGridLayout,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QFileDialog,
)

from app.constants import DocumentStatus
from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button
from ui.components.status_badge import StatusBadge
from core.database import DatabaseManager
from core.permissions import PermissionChecker
from ui.dialogs.confirm_dialog import ConfirmDialog, InfoDialog
from ui.dialogs.document_dialog import DocumentDialog
from ui.dialogs.link_dialog import LinkDialog
from ui.dialogs.upload_dialog import UploadDialog
from models.attachment import Attachment
from models.document import Document
from models.history import HistoryEntry
from models.link import DocumentLink
from services.attachment_service import AttachmentService
from services.category_service import CategoryService
from services.document_service import DocumentService
from services.history_service import HistoryService
from services.link_service import LinkService, LinkedDocument
from utils.dates import format_date, format_datetime
from ui.views.base_view import BaseView

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class DocumentDetailView(BaseView):
    """
    Document detail view showing all document information.

    Features:
    - Full document metadata display
    - Edit and delete actions (if permitted)
    - Mark as reviewed action
    - Tabbed sections: Details, Attachments, Links, History
    - Back navigation
    """

    def __init__(
        self,
        parent: QWidget,
        app: "PolicyHubApp",
        document: Document,
        on_back: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the document detail view.

        Args:
            parent: Parent widget
            app: Main application instance
            document: Document to display
            on_back: Callback when back button is clicked
        """
        super().__init__(parent, app)
        self.document = document
        self.on_back_callback = on_back
        self.doc_service = DocumentService(app.db)
        self.history_service = HistoryService(app.db)
        self.category_service = CategoryService(app.db)
        self.attachment_service = AttachmentService(app.db)
        self.link_service = LinkService(app.db)
        self.permissions = PermissionChecker()

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the document detail UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with back button and actions
        self._build_header(layout)

        # Title and badges section
        self._build_title_section(layout)

        # Tabbed content
        self._build_tabs(layout)

    def _build_header(self, parent_layout: QVBoxLayout) -> None:
        """Build the header with navigation and actions."""
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.CARD};
                border: none;
            }}
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.WINDOW_PADDING, 10, SPACING.WINDOW_PADDING, 10)

        # Back button
        back_btn = QPushButton("< Back")
        back_btn.setFixedSize(80, 32)
        back_btn.setFont(TYPOGRAPHY.body)
        style_button(back_btn, "secondary")
        back_btn.clicked.connect(self._on_back)
        header_layout.addWidget(back_btn)

        # Document reference
        ref_label = QLabel(self.document.doc_ref)
        ref_label.setFont(TYPOGRAPHY.get_font(16, TYPOGRAPHY.WEIGHT_BOLD))
        ref_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(ref_label)

        header_layout.addStretch()

        # Action buttons (right side)
        # Delete button (admin only)
        if self.permissions.can_delete():
            delete_btn = QPushButton("Delete")
            delete_btn.setFixedSize(80, 32)
            delete_btn.setFont(TYPOGRAPHY.small)
            style_button(delete_btn, "danger")
            delete_btn.clicked.connect(self._on_delete)
            header_layout.addWidget(delete_btn)

        # Edit button (editor+)
        if self.permissions.can_edit():
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedSize(80, 32)
            edit_btn.setFont(TYPOGRAPHY.small)
            style_button(edit_btn, "secondary")
            edit_btn.clicked.connect(self._on_edit)
            header_layout.addWidget(edit_btn)

        parent_layout.addWidget(header)

    def _build_title_section(self, parent_layout: QVBoxLayout) -> None:
        """Build the title and badges section."""
        title_frame = QFrame()
        title_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.CARD};
                border-radius: {SPACING.CORNER_RADIUS}px;
            }}
        """)

        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(20, 15, 20, 15)

        # Title
        title_label = QLabel(self.document.title)
        title_label.setFont(TYPOGRAPHY.window_title)
        title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        title_label.setWordWrap(True)
        title_layout.addWidget(title_label)

        # Badges row
        badges_layout = QHBoxLayout()
        badges_layout.setContentsMargins(0, 10, 0, 0)
        badges_layout.setSpacing(10)

        # Type badge
        type_badge = StatusBadge(text=self.document.type_display, variant="primary")
        badges_layout.addWidget(type_badge)

        # Status badge
        status_badge = StatusBadge.from_status(None, self.document.status)
        badges_layout.addWidget(status_badge)

        # Review status badge
        review_badge = StatusBadge.from_review_status(None, self.document.review_status)
        badges_layout.addWidget(review_badge)

        badges_layout.addStretch()
        title_layout.addLayout(badges_layout)

        # Add with margins
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(SPACING.WINDOW_PADDING, 0, SPACING.WINDOW_PADDING, 10)
        container_layout.addWidget(title_frame)
        parent_layout.addWidget(container)

    def _build_tabs(self, parent_layout: QVBoxLayout) -> None:
        """Build the tabbed content area."""
        # Tab container with margins
        tab_container = QWidget()
        tab_container_layout = QVBoxLayout(tab_container)
        tab_container_layout.setContentsMargins(
            SPACING.WINDOW_PADDING, 0, SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING
        )

        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(TYPOGRAPHY.body)
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                background-color: {COLORS.CARD};
                border: none;
                border-radius: {SPACING.CORNER_RADIUS}px;
            }}
            QTabBar::tab {{
                background-color: {COLORS.MUTED};
                color: {COLORS.TEXT_PRIMARY};
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS.PRIMARY};
                color: {COLORS.PRIMARY_FOREGROUND};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {COLORS.BORDER};
            }}
        """)

        # Create tabs
        self._build_details_tab()
        self._build_attachments_tab()
        self._build_links_tab()
        self._build_history_tab()

        tab_container_layout.addWidget(self.tab_widget)
        parent_layout.addWidget(tab_container, 1)

    def _build_details_tab(self) -> None:
        """Build the details tab content."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)

        # Scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)

        # Fields in a compact grid - constrained width
        fields_widget = QWidget()
        fields_widget.setStyleSheet("background: transparent;")
        fields_widget.setMaximumWidth(800)  # Constrain width for readability
        fields_layout = QGridLayout(fields_widget)
        fields_layout.setHorizontalSpacing(40)  # Space between columns
        fields_layout.setVerticalSpacing(16)    # Space between rows
        fields_layout.setColumnStretch(0, 1)    # Equal column widths
        fields_layout.setColumnStretch(1, 1)

        row = 0

        # Row 1: Type, Category
        self._add_field(fields_layout, "Document Type", self.document.type_display, row, 0)
        self._add_field(fields_layout, "Category", self.document.category, row, 1)
        row += 1

        # Row 2: Version, Status
        self._add_field(fields_layout, "Version", self.document.version, row, 0)
        self._add_field(fields_layout, "Status", self.document.status_display, row, 1)
        row += 1

        # Row 3: Owner, Approver
        self._add_field(fields_layout, "Owner", self.document.owner, row, 0)
        self._add_field(fields_layout, "Approver", self.document.approver or "-", row, 1)
        row += 1

        # Row 4: Applicable Entities, Mandatory Read
        if self.document.applicable_entity:
            entities = self.document.applicable_entity.split(";")
            entity_value = ", ".join(entities) if len(entities) <= 3 else f"{entities[0]}, {entities[1]} +{len(entities)-2} more"
        else:
            entity_value = "All Entities"
        mandatory_value = "Yes" if self.document.mandatory_read_all else "No"
        self._add_field(fields_layout, "Applicable Entities", entity_value, row, 0)
        self._add_field(fields_layout, "Mandatory Read", mandatory_value, row, 1)
        row += 1

        # Row 5: Review Frequency, Review Status
        self._add_field(fields_layout, "Review Frequency", self.document.frequency_display, row, 0)
        self._add_field(fields_layout, "Review Status", self.document.review_status_display, row, 1)
        row += 1

        # Row 6: Effective Date, Last Review
        self._add_field(fields_layout, "Effective Date", format_date(self.document.effective_date), row, 0)
        self._add_field(fields_layout, "Last Reviewed", format_date(self.document.last_review_date), row, 1)
        row += 1

        # Row 7: Next Review with action
        next_review_widget = QWidget()
        next_review_widget.setStyleSheet("background: transparent;")
        next_review_layout = QVBoxLayout(next_review_widget)
        next_review_layout.setContentsMargins(0, 0, 0, 0)
        next_review_layout.setSpacing(2)

        nr_label = QLabel("Next Review")
        nr_label.setFont(TYPOGRAPHY.small)
        nr_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        next_review_layout.addWidget(nr_label)

        date_row = QHBoxLayout()
        date_row.setSpacing(12)

        date_label = QLabel(format_date(self.document.next_review_date))
        date_label.setFont(TYPOGRAPHY.body)
        date_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        date_row.addWidget(date_label)

        # Mark reviewed button
        if self.permissions.can_edit() and self.document.status == DocumentStatus.ACTIVE.value:
            review_btn = QPushButton("Mark Reviewed")
            review_btn.setFixedSize(110, 28)
            review_btn.setFont(TYPOGRAPHY.small)
            style_button(review_btn, "primary")
            review_btn.clicked.connect(self._on_mark_reviewed)
            date_row.addWidget(review_btn)

        date_row.addStretch()
        next_review_layout.addLayout(date_row)
        fields_layout.addWidget(next_review_widget, row, 0)

        content_layout.addWidget(fields_widget)

        # Description (constrained width)
        if self.document.description:
            desc_widget = QWidget()
            desc_widget.setStyleSheet("background: transparent;")
            desc_widget.setMaximumWidth(800)
            desc_layout = QVBoxLayout(desc_widget)
            desc_layout.setContentsMargins(0, 0, 0, 0)
            desc_layout.setSpacing(4)

            desc_label = QLabel("Description")
            desc_label.setFont(TYPOGRAPHY.small)
            desc_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
            desc_layout.addWidget(desc_label)

            desc_text = QTextEdit()
            desc_text.setMinimumHeight(60)
            desc_text.setMaximumHeight(100)
            desc_text.setFont(TYPOGRAPHY.body)
            desc_text.setReadOnly(True)
            desc_text.setPlainText(self.document.description)
            desc_text.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {COLORS.MUTED};
                    border: none;
                    border-radius: 6px;
                    padding: 10px 12px;
                    color: {COLORS.TEXT_PRIMARY};
                }}
            """)
            desc_layout.addWidget(desc_text)
            content_layout.addWidget(desc_widget)

        # Notes (constrained width)
        if self.document.notes:
            notes_widget = QWidget()
            notes_widget.setStyleSheet("background: transparent;")
            notes_widget.setMaximumWidth(800)
            notes_layout = QVBoxLayout(notes_widget)
            notes_layout.setContentsMargins(0, 0, 0, 0)
            notes_layout.setSpacing(4)

            notes_label = QLabel("Notes")
            notes_label.setFont(TYPOGRAPHY.small)
            notes_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
            notes_layout.addWidget(notes_label)

            notes_text = QTextEdit()
            notes_text.setMinimumHeight(50)
            notes_text.setMaximumHeight(80)
            notes_text.setFont(TYPOGRAPHY.body)
            notes_text.setReadOnly(True)
            notes_text.setPlainText(self.document.notes)
            notes_text.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {COLORS.MUTED};
                    border: none;
                    border-radius: 6px;
                    padding: 10px 12px;
                    color: {COLORS.TEXT_PRIMARY};
                }}
            """)
            notes_layout.addWidget(notes_text)
            content_layout.addWidget(notes_widget)

        # Metadata
        meta_label = QLabel(
            f"Created: {format_datetime(self.document.created_at)} | "
            f"Last Updated: {format_datetime(self.document.updated_at)}"
        )
        meta_label.setFont(TYPOGRAPHY.small)
        meta_label.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; background: transparent;")
        meta_label.setContentsMargins(0, 8, 0, 0)
        content_layout.addWidget(meta_label)

        content_layout.addStretch()
        scroll.setWidget(scroll_content)
        tab_layout.addWidget(scroll)
        self.tab_widget.addTab(tab, "Details")

    def _add_field(self, layout: QGridLayout, label: str, value: str, row: int, col: int) -> None:
        """Add a field display to the grid."""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        field_layout = QVBoxLayout(widget)
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(2)

        label_widget = QLabel(label)
        label_widget.setFont(TYPOGRAPHY.small)
        label_widget.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        field_layout.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setFont(TYPOGRAPHY.body)
        value_widget.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        field_layout.addWidget(value_widget)

        layout.addWidget(widget, row, col)

    def _build_attachments_tab(self) -> None:
        """Build the attachments tab with upload and list functionality."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(10, 10, 10, 10)

        # Header with upload button
        header_layout = QHBoxLayout()

        header_label = QLabel("Attachments")
        header_label.setFont(TYPOGRAPHY.section_heading)
        header_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Download All button
        self.download_all_btn = QPushButton("Download All")
        self.download_all_btn.setFixedSize(110, 32)
        style_button(self.download_all_btn, "secondary")
        self.download_all_btn.clicked.connect(self._on_download_all_attachments)
        header_layout.addWidget(self.download_all_btn)

        # Upload button (editor+)
        if self.permissions.can_edit():
            upload_btn = QPushButton("+ Upload File")
            upload_btn.setFixedSize(120, 32)
            style_button(upload_btn, "primary")
            upload_btn.clicked.connect(self._on_upload_attachment)
            header_layout.addWidget(upload_btn)

        tab_layout.addLayout(header_layout)

        # Scrollable list container
        self.attachments_scroll = QScrollArea()
        self.attachments_scroll.setWidgetResizable(True)
        self.attachments_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.attachments_scroll.setStyleSheet("background: transparent;")

        self.attachments_content = QWidget()
        self.attachments_content.setStyleSheet("background: transparent;")
        self.attachments_layout = QVBoxLayout(self.attachments_content)
        self.attachments_layout.setContentsMargins(0, 0, 0, 0)
        self.attachments_layout.setSpacing(5)

        self.attachments_scroll.setWidget(self.attachments_content)
        tab_layout.addWidget(self.attachments_scroll, 1)

        self.tab_widget.addTab(tab, "Attachments")

        # Load attachments
        self._load_attachments()

    def _load_attachments(self) -> None:
        """Load and display attachments list."""
        # Clear existing
        while self.attachments_layout.count():
            item = self.attachments_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        attachments = self.attachment_service.get_attachments_for_document(self.document.doc_id)

        # Update Download All button state
        if hasattr(self, 'download_all_btn'):
            self.download_all_btn.setEnabled(bool(attachments))

        if not attachments:
            no_label = QLabel("No attachments uploaded yet.")
            no_label.setFont(TYPOGRAPHY.body)
            no_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
            no_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.attachments_layout.addWidget(no_label)
            self.attachments_layout.addStretch()
            return

        # Display each attachment
        for attachment in attachments:
            self._create_attachment_row(attachment)

        self.attachments_layout.addStretch()

    def _create_attachment_row(self, attachment: Attachment) -> None:
        """Create a row for an attachment."""
        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.MUTED};
                border-radius: {SPACING.CORNER_RADIUS}px;
            }}
        """)

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(15, 12, 15, 12)

        # Left side: file info
        info_widget = QWidget()
        info_widget.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        # Filename with current badge
        name_layout = QHBoxLayout()
        name_layout.setSpacing(10)

        name_label = QLabel(attachment.filename)
        name_label.setFont(TYPOGRAPHY.body)
        name_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        name_layout.addWidget(name_label)

        if attachment.is_current:
            current_badge = QLabel("CURRENT")
            current_badge.setFont(TYPOGRAPHY.get_font(10, TYPOGRAPHY.WEIGHT_BOLD))
            current_badge.setStyleSheet(f"""
                background-color: {COLORS.SUCCESS};
                color: {COLORS.PRIMARY_FOREGROUND};
                border-radius: 4px;
                padding: 2px 8px;
            """)
            name_layout.addWidget(current_badge)

        name_layout.addStretch()
        info_layout.addLayout(name_layout)

        # Meta info
        meta_text = f"v{attachment.version_label} | {attachment.size_display} | {format_datetime(attachment.uploaded_at)}"
        meta_label = QLabel(meta_text)
        meta_label.setFont(TYPOGRAPHY.small)
        meta_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        info_layout.addWidget(meta_label)

        row_layout.addWidget(info_widget, 1)

        # Right side: action buttons
        # Open button
        open_btn = QPushButton("Open")
        open_btn.setFixedSize(70, 28)
        open_btn.setFont(TYPOGRAPHY.small)
        style_button(open_btn, "secondary")
        open_btn.clicked.connect(lambda checked, a=attachment: self._on_open_attachment(a))
        row_layout.addWidget(open_btn)

        # Delete button (editor+)
        if self.permissions.can_edit():
            delete_btn = QPushButton("Delete")
            delete_btn.setFixedSize(70, 28)
            delete_btn.setFont(TYPOGRAPHY.small)
            style_button(delete_btn, "danger")
            delete_btn.clicked.connect(lambda checked, a=attachment: self._on_delete_attachment(a))
            row_layout.addWidget(delete_btn)

        self.attachments_layout.addWidget(row)

    def _on_upload_attachment(self) -> None:
        """Handle upload attachment button click."""
        dialog = UploadDialog(
            self.window(),
            doc_ref=self.document.doc_ref,
            current_version=self.document.version,
        )
        if dialog.exec():
            result = dialog.result
            if result:
                file_path, version_label = result
                try:
                    self.attachment_service.add_attachment(
                        doc_id=self.document.doc_id,
                        doc_ref=self.document.doc_ref,
                        source_path=file_path,
                        version_label=version_label,
                    )
                    InfoDialog.show_info(
                        self.window(),
                        "Success",
                        f"File '{file_path.name}' uploaded successfully.",
                    )
                    self._load_attachments()
                    self._load_history()
                except PermissionError as e:
                    InfoDialog.show_error(self.window(), "Permission Denied", str(e))
                except ValueError as e:
                    InfoDialog.show_error(self.window(), "Upload Error", str(e))
                except Exception as e:
                    InfoDialog.show_error(self.window(), "Error", f"Failed to upload: {str(e)}")

    def _on_open_attachment(self, attachment: Attachment) -> None:
        """Handle open attachment button click."""
        file_path = self.attachment_service.open_attachment(attachment.attachment_id)

        if file_path and file_path.exists():
            try:
                # Open file with default application (Windows)
                os.startfile(str(file_path))
            except Exception as e:
                InfoDialog.show_error(
                    self.window(),
                    "Error",
                    f"Failed to open file: {str(e)}",
                )
        else:
            InfoDialog.show_error(
                self.window(),
                "File Not Found",
                "The attachment file could not be found.",
            )

    def _on_delete_attachment(self, attachment: Attachment) -> None:
        """Handle delete attachment button click."""
        if ConfirmDialog.ask_delete(
            self.window(),
            item_name=attachment.filename,
            item_type="attachment",
        ):
            try:
                self.attachment_service.delete_attachment(attachment.attachment_id)
                InfoDialog.show_info(
                    self.window(),
                    "Deleted",
                    f"Attachment '{attachment.filename}' has been deleted.",
                )
                self._load_attachments()
                self._load_history()
            except PermissionError as e:
                InfoDialog.show_error(self.window(), "Permission Denied", str(e))
            except Exception as e:
                InfoDialog.show_error(self.window(), "Error", str(e))

    def _on_download_all_attachments(self) -> None:
        """Handle download all attachments button click."""
        attachments = self.attachment_service.get_attachments_for_document(self.document.doc_id)

        if not attachments:
            InfoDialog.show_info(
                self.window(),
                "No Attachments",
                "There are no attachments to download.",
            )
            return

        # Ask for destination folder
        dest_folder = QFileDialog.getExistingDirectory(
            self,
            "Select Download Folder",
            "",
        )

        if not dest_folder:
            return

        dest_path = Path(dest_folder)
        downloaded = 0
        failed = []

        for attachment in attachments:
            try:
                # Get the source file path
                source_path = self.attachment_service.open_attachment(attachment.attachment_id)
                if source_path and source_path.exists():
                    # Copy to destination
                    dest_file = dest_path / attachment.filename
                    # Handle duplicate filenames
                    counter = 1
                    while dest_file.exists():
                        stem = attachment.filename.rsplit('.', 1)[0] if '.' in attachment.filename else attachment.filename
                        ext = '.' + attachment.filename.rsplit('.', 1)[1] if '.' in attachment.filename else ''
                        dest_file = dest_path / f"{stem}_{counter}{ext}"
                        counter += 1
                    shutil.copy2(source_path, dest_file)
                    downloaded += 1
                else:
                    failed.append(attachment.filename)
            except Exception as e:
                failed.append(f"{attachment.filename}: {str(e)}")

        # Show result
        if failed:
            InfoDialog.show_info(
                self.window(),
                "Download Complete",
                f"Downloaded {downloaded} file(s).\n\nFailed to download:\n" + "\n".join(failed[:5]),
            )
        else:
            InfoDialog.show_info(
                self.window(),
                "Download Complete",
                f"Successfully downloaded {downloaded} file(s) to:\n{dest_folder}",
            )

    def _build_links_tab(self) -> None:
        """Build the linked documents tab with link management."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(10, 10, 10, 10)

        # Header with add link button
        header_layout = QHBoxLayout()

        header_label = QLabel("Linked Documents")
        header_label.setFont(TYPOGRAPHY.section_heading)
        header_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Add link button (editor+)
        if self.permissions.can_edit():
            add_link_btn = QPushButton("+ Add Link")
            add_link_btn.setFixedSize(100, 32)
            style_button(add_link_btn, "primary")
            add_link_btn.clicked.connect(self._on_add_link)
            header_layout.addWidget(add_link_btn)

        tab_layout.addLayout(header_layout)

        # Scrollable list container
        self.links_scroll = QScrollArea()
        self.links_scroll.setWidgetResizable(True)
        self.links_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.links_scroll.setStyleSheet("background: transparent;")

        self.links_content = QWidget()
        self.links_content.setStyleSheet("background: transparent;")
        self.links_layout = QVBoxLayout(self.links_content)
        self.links_layout.setContentsMargins(0, 0, 0, 0)
        self.links_layout.setSpacing(5)

        self.links_scroll.setWidget(self.links_content)
        tab_layout.addWidget(self.links_scroll, 1)

        self.tab_widget.addTab(tab, "Linked Documents")

        # Load links
        self._load_links()

    def _load_links(self) -> None:
        """Load and display document links."""
        # Clear existing
        while self.links_layout.count():
            item = self.links_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        links = self.link_service.get_links_for_document(self.document.doc_id)

        if not links:
            no_label = QLabel("No linked documents.")
            no_label.setFont(TYPOGRAPHY.body)
            no_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
            no_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.links_layout.addWidget(no_label)
            self.links_layout.addStretch()
            return

        # Display each link
        for linked_doc in links:
            self._create_link_row(linked_doc)

        self.links_layout.addStretch()

    def _create_link_row(self, linked_doc: LinkedDocument) -> None:
        """Create a row for a linked document."""
        row = QFrame()
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.MUTED};
                border-radius: {SPACING.CORNER_RADIUS}px;
            }}
            QFrame:hover {{
                background-color: {COLORS.BORDER};
            }}
        """)
        row.mousePressEvent = lambda e, ld=linked_doc: self._on_click_linked_doc(ld)

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(15, 12, 15, 12)

        # Left side: link info
        info_widget = QWidget()
        info_widget.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        # Relationship text
        relationship = linked_doc.link.get_relationship_text(linked_doc.is_parent)
        rel_label = QLabel(f"{relationship}:")
        rel_label.setFont(TYPOGRAPHY.small)
        rel_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        info_layout.addWidget(rel_label)

        # Document reference and title
        doc_layout = QHBoxLayout()
        doc_layout.setSpacing(5)

        ref_label = QLabel(linked_doc.doc_ref)
        ref_label.setFont(TYPOGRAPHY.get_font(13, TYPOGRAPHY.WEIGHT_BOLD))
        ref_label.setStyleSheet(f"color: {COLORS.PRIMARY}; background: transparent;")
        doc_layout.addWidget(ref_label)

        title_text = f" - {linked_doc.title[:50]}" + ("..." if len(linked_doc.title) > 50 else "")
        title_label = QLabel(title_text)
        title_label.setFont(TYPOGRAPHY.body)
        title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        doc_layout.addWidget(title_label)
        doc_layout.addStretch()

        info_layout.addLayout(doc_layout)
        row_layout.addWidget(info_widget, 1)

        # Right side: delete button (editor+)
        if self.permissions.can_edit():
            delete_btn = QPushButton("Remove")
            delete_btn.setFixedSize(80, 28)
            delete_btn.setFont(TYPOGRAPHY.small)
            style_button(delete_btn, "danger")
            delete_btn.clicked.connect(lambda checked, ld=linked_doc: self._on_remove_link(ld))
            row_layout.addWidget(delete_btn)

        self.links_layout.addWidget(row)

    def _on_add_link(self) -> None:
        """Handle add link button click."""
        dialog = LinkDialog(
            self.window(),
            self.app.db,
            source_doc_id=self.document.doc_id,
            source_doc_ref=self.document.doc_ref,
        )
        if dialog.exec():
            result = dialog.result
            if result:
                target_doc_id, link_type = result
                try:
                    self.link_service.create_link(
                        parent_doc_id=self.document.doc_id,
                        child_doc_id=target_doc_id,
                        link_type=link_type,
                    )
                    InfoDialog.show_info(
                        self.window(),
                        "Success",
                        "Document link created successfully.",
                    )
                    self._load_links()
                    self._load_history()
                except PermissionError as e:
                    InfoDialog.show_error(self.window(), "Permission Denied", str(e))
                except ValueError as e:
                    InfoDialog.show_error(self.window(), "Error", str(e))
                except Exception as e:
                    InfoDialog.show_error(self.window(), "Error", f"Failed to create link: {str(e)}")

    def _on_click_linked_doc(self, linked_doc: LinkedDocument) -> None:
        """Handle click on linked document reference to navigate to it."""
        # Get the linked document ID
        if linked_doc.is_parent:
            target_doc_id = linked_doc.link.child_doc_id
        else:
            target_doc_id = linked_doc.link.parent_doc_id

        # Get the full document
        target_doc = self.doc_service.get_document_by_id(target_doc_id)
        if target_doc:
            # Navigate to the linked document via main_view
            main_view = self.app.current_view
            if hasattr(main_view, "_show_document_detail"):
                main_view._show_document_detail(target_doc)
            else:
                InfoDialog.show_error(
                    self.window(),
                    "Navigation Error",
                    "Cannot navigate to the linked document.",
                )
        else:
            InfoDialog.show_error(
                self.window(),
                "Document Not Found",
                f"Could not find document {linked_doc.doc_ref}.",
            )

    def _on_remove_link(self, linked_doc: LinkedDocument) -> None:
        """Handle remove link button click."""
        if ConfirmDialog.ask(
            self.window(),
            "Remove Link",
            f"Remove link to {linked_doc.doc_ref}?",
            confirm_text="Remove",
        ):
            try:
                self.link_service.delete_link(linked_doc.link.link_id)
                InfoDialog.show_info(
                    self.window(),
                    "Removed",
                    "Link has been removed.",
                )
                self._load_links()
                self._load_history()
            except PermissionError as e:
                InfoDialog.show_error(self.window(), "Permission Denied", str(e))
            except Exception as e:
                InfoDialog.show_error(self.window(), "Error", str(e))

    def _build_history_tab(self) -> None:
        """Build the history tab showing audit trail."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(10, 10, 10, 10)

        # Scrollable list
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.history_scroll.setStyleSheet("background: transparent;")

        self.history_content = QWidget()
        self.history_content.setStyleSheet("background: transparent;")
        self.history_layout = QVBoxLayout(self.history_content)
        self.history_layout.setContentsMargins(0, 0, 0, 0)
        self.history_layout.setSpacing(0)

        self.history_scroll.setWidget(self.history_content)
        tab_layout.addWidget(self.history_scroll, 1)

        self.tab_widget.addTab(tab, "History")

        # Load history
        self._load_history()

    def _load_history(self) -> None:
        """Load and display document history."""
        history = self.history_service.get_document_history(self.document.doc_id, limit=50)

        # Clear existing
        while self.history_layout.count():
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not history:
            no_label = QLabel("No history entries found.")
            no_label.setFont(TYPOGRAPHY.body)
            no_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
            no_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_layout.addWidget(no_label)
            self.history_layout.addStretch()
            return

        # Header
        header = QFrame()
        header.setStyleSheet(f"background-color: {COLORS.MUTED};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 8, 10, 8)

        for text, width in [("Date/Time", 150), ("Action", 120), ("Details", 300), ("User", 100)]:
            label = QLabel(text)
            label.setFont(TYPOGRAPHY.get_font(11, TYPOGRAPHY.WEIGHT_BOLD))
            label.setFixedWidth(width)
            label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
            header_layout.addWidget(label)

        header_layout.addStretch()
        self.history_layout.addWidget(header)

        # History entries
        for entry in history:
            row = QFrame()
            row.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 6, 10, 6)

            # Date/Time
            date_label = QLabel(format_datetime(entry.changed_at))
            date_label.setFont(TYPOGRAPHY.small)
            date_label.setFixedWidth(150)
            date_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
            row_layout.addWidget(date_label)

            # Action
            action_label = QLabel(entry.action_display)
            action_label.setFont(TYPOGRAPHY.body)
            action_label.setFixedWidth(120)
            action_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
            row_layout.addWidget(action_label)

            # Details
            details_label = QLabel(entry.get_change_description()[:50])
            details_label.setFont(TYPOGRAPHY.body)
            details_label.setFixedWidth(300)
            details_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
            row_layout.addWidget(details_label)

            # User
            user_text = entry.changed_by if entry.changed_by else "-"
            user_label = QLabel(user_text)
            user_label.setFont(TYPOGRAPHY.small)
            user_label.setFixedWidth(100)
            user_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
            row_layout.addWidget(user_label)

            row_layout.addStretch()
            self.history_layout.addWidget(row)

            # Divider
            divider = QFrame()
            divider.setFixedHeight(1)
            divider.setStyleSheet(f"background-color: {COLORS.BORDER};")
            self.history_layout.addWidget(divider)

        self.history_layout.addStretch()

    def _on_back(self) -> None:
        """Handle back button click."""
        if self.on_back_callback:
            self.on_back_callback()

    def _on_edit(self) -> None:
        """Handle edit button click."""
        categories = self.category_service.get_active_categories()
        dialog = DocumentDialog(
            self.window(),
            self.app.db,
            categories=categories,
            document=self.document,
        )
        if dialog.exec():
            result = dialog.result
            if result:
                # Navigate to a fresh document detail view via main_view
                main_view = self.app.current_view
                if hasattr(main_view, "_show_document_detail"):
                    main_view._show_document_detail(result)
                else:
                    # Fallback: update locally
                    self.document = result
                    self._refresh_display()

    def _on_delete(self) -> None:
        """Handle delete button click."""
        if ConfirmDialog.ask_delete(
            self.window(),
            item_name=self.document.doc_ref,
            item_type="document",
        ):
            try:
                self.doc_service.delete_document(self.document.doc_id)
                InfoDialog.show_info(
                    self.window(),
                    "Deleted",
                    f"Document {self.document.doc_ref} has been deleted.",
                )
                self._on_back()
            except PermissionError as e:
                InfoDialog.show_error(self.window(), "Permission Denied", str(e))
            except Exception as e:
                InfoDialog.show_error(self.window(), "Error", str(e))

    def _on_mark_reviewed(self) -> None:
        """Handle mark reviewed button click."""
        try:
            result = self.doc_service.mark_as_reviewed(self.document.doc_id)
            if result:
                self.document = result
                self._refresh_display()
                InfoDialog.show_info(
                    self.window(),
                    "Reviewed",
                    f"Document marked as reviewed. Next review: {format_date(result.next_review_date)}",
                )
        except PermissionError as e:
            InfoDialog.show_error(self.window(), "Permission Denied", str(e))
        except Exception as e:
            InfoDialog.show_error(self.window(), "Error", str(e))

    def _refresh_display(self) -> None:
        """Refresh the entire display with updated document data."""
        # Clear and rebuild
        layout = self.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._build_ui()

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        # Reload history in case it changed
        self._load_history()
