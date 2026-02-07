"""
PolicyHub Upload Dialog (PySide6)

Dialog for uploading file attachments to documents.
"""

from pathlib import Path
from typing import Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QFileDialog,
)

from app.constants import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB
from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button
from ui.dialogs.base_dialog import BaseDialog
from ui.dialogs.confirm_dialog import InfoDialog
from utils.files import format_file_size, get_file_size
from utils.validators import validate_file_upload


class UploadDialog(BaseDialog):
    """
    Dialog for selecting and uploading a file attachment.

    Usage:
        dialog = UploadDialog(parent, doc_ref="POL-AML-001", current_version="1.0")
        if dialog.exec():
            result = dialog.result  # (Path, version_label)
    """

    def __init__(
        self,
        parent: QWidget,
        doc_ref: str,
        current_version: str = "1.0",
    ):
        """
        Initialize the upload dialog.

        Args:
            parent: Parent window
            doc_ref: Document reference code
            current_version: Current document version for default label
        """
        self.doc_ref = doc_ref
        self.current_version = current_version
        self.selected_file: Optional[Path] = None

        super().__init__(parent, "Upload Attachment", width=500, height=380)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = QLabel(f"Upload attachment for {self.doc_ref}")
        title_label.setFont(TYPOGRAPHY.section_heading)
        title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title_label)

        # File selection area
        file_frame = QFrame()
        file_frame.setFixedHeight(80)
        file_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.MUTED};
                border-radius: {SPACING.CORNER_RADIUS}px;
            }}
        """)
        file_layout = QVBoxLayout(file_frame)
        file_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.file_label = QLabel("No file selected")
        self.file_label.setFont(TYPOGRAPHY.body)
        self.file_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_layout.addWidget(self.file_label)

        layout.addWidget(file_frame)

        # Browse button
        browse_btn = QPushButton("Browse Files...")
        browse_btn.setFixedSize(150, 36)
        style_button(browse_btn, "secondary")
        browse_btn.clicked.connect(self._browse_file)
        layout.addWidget(browse_btn, 0, Qt.AlignmentFlag.AlignLeft)

        # Version label input
        version_row = QHBoxLayout()
        version_row.setSpacing(10)

        version_label = QLabel("Version Label:")
        version_label.setFont(TYPOGRAPHY.body)
        version_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        version_row.addWidget(version_label)

        self.version_entry = QLineEdit()
        self.version_entry.setFixedSize(100, 36)
        self.version_entry.setFont(TYPOGRAPHY.body)
        self.version_entry.setPlaceholderText("e.g., 1.0")
        self.version_entry.setText(self.current_version)
        self._style_input(self.version_entry)
        version_row.addWidget(self.version_entry)
        version_row.addStretch()

        layout.addLayout(version_row)

        # Help text
        help_text = f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}\nMax size: {MAX_FILE_SIZE_MB} MB"
        help_label = QLabel(help_text)
        help_label.setFont(TYPOGRAPHY.small)
        help_label.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; background: transparent;")
        layout.addWidget(help_label)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 36)
        style_button(cancel_btn, "secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self.upload_btn = QPushButton("Upload")
        self.upload_btn.setFixedSize(100, 36)
        style_button(self.upload_btn, "primary")
        self.upload_btn.setEnabled(False)
        self.upload_btn.clicked.connect(self._on_upload)
        btn_row.addWidget(self.upload_btn)

        layout.addLayout(btn_row)

    def _style_input(self, widget: QLineEdit) -> None:
        """Apply input styling."""
        widget.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS.BACKGROUND};
                border: 1px solid {COLORS.BORDER};
                border-radius: 4px;
                padding: 0 12px;
                color: {COLORS.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {COLORS.PRIMARY};
            }}
        """)

    def _browse_file(self) -> None:
        """Open file browser to select a file."""
        # Build file type filter
        all_supported = " ".join(f"*{ext}" for ext in ALLOWED_EXTENSIONS)
        file_filter = (
            f"All supported files ({all_supported});;"
            "PDF files (*.pdf);;"
            "Word documents (*.doc *.docx);;"
            "Excel spreadsheets (*.xls *.xlsx);;"
            "PowerPoint presentations (*.ppt *.pptx);;"
            "Text files (*.txt);;"
            "All files (*.*)"
        )

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Upload",
            "",
            file_filter,
        )

        if file_path:
            self._select_file(Path(file_path))

    def _select_file(self, file_path: Path) -> None:
        """
        Select a file for upload.

        Args:
            file_path: Path to the selected file
        """
        if not file_path.exists():
            InfoDialog.show_error(self, "Error", "Selected file does not exist.")
            return

        # Validate file
        file_size = get_file_size(file_path)
        is_valid, error = validate_file_upload(file_path.name, file_size)

        if not is_valid:
            InfoDialog.show_error(self, "Invalid File", error)
            return

        self.selected_file = file_path

        # Update display
        size_str = format_file_size(file_size)
        self.file_label.setText(f"{file_path.name}\n({size_str})")
        self.file_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")

        # Enable upload button
        self.upload_btn.setEnabled(True)

    def _on_upload(self) -> None:
        """Handle upload button click."""
        if not self.selected_file:
            InfoDialog.show_error(self, "Error", "No file selected.")
            return

        version = self.version_entry.text().strip()
        if not version:
            InfoDialog.show_error(self, "Error", "Version label is required.")
            return

        # Set result as tuple of (file_path, version_label)
        self.result = (self.selected_file, version)
        self.accept()
