"""
PolicyHub Upload Dialog

Dialog for uploading file attachments to documents.
"""

from pathlib import Path
from tkinter import filedialog
from typing import Optional, Tuple

import customtkinter as ctk

from app.constants import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB
from app.theme import COLORS, SPACING, TYPOGRAPHY, configure_button_style
from dialogs.base_dialog import BaseDialog
from dialogs.confirm_dialog import InfoDialog
from utils.files import format_file_size, get_file_extension, get_file_size
from utils.validators import validate_file_upload


class UploadDialog(BaseDialog):
    """
    Dialog for selecting and uploading a file attachment.

    Usage:
        dialog = UploadDialog(parent, doc_ref="POL-AML-001", current_version="1.0")
        result = dialog.show()  # Returns (Path, version_label) or None
    """

    def __init__(
        self,
        parent,
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

        super().__init__(parent, "Upload Attachment", width=500, height=350)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text=f"Upload attachment for {self.doc_ref}",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title_label.pack(anchor="w", pady=(0, 15))

        # File selection area
        file_frame = ctk.CTkFrame(
            main_frame,
            fg_color=COLORS.MUTED,
            corner_radius=SPACING.CORNER_RADIUS,
            height=100,
        )
        file_frame.pack(fill="x", pady=(0, 15))
        file_frame.pack_propagate(False)

        # File info display
        self.file_label = ctk.CTkLabel(
            file_frame,
            text="No file selected",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_SECONDARY,
        )
        self.file_label.pack(expand=True)

        # Browse button
        browse_btn = ctk.CTkButton(
            main_frame,
            text="Browse Files...",
            command=self._browse_file,
            width=150,
            height=36,
        )
        configure_button_style(browse_btn, "secondary")
        browse_btn.pack(pady=(0, 20))

        # Version label input
        version_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        version_frame.pack(fill="x", pady=(0, 15))

        version_label = ctk.CTkLabel(
            version_frame,
            text="Version Label:",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        version_label.pack(side="left", padx=(0, 10))

        self.version_var = ctk.StringVar(value=self.current_version)
        self.version_entry = ctk.CTkEntry(
            version_frame,
            textvariable=self.version_var,
            width=100,
            height=36,
            font=TYPOGRAPHY.body,
            placeholder_text="e.g., 1.0",
        )
        self.version_entry.pack(side="left")

        # Help text
        help_text = f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}\nMax size: {MAX_FILE_SIZE_MB} MB"
        help_label = ctk.CTkLabel(
            main_frame,
            text=help_text,
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_MUTED,
            justify="left",
        )
        help_label.pack(anchor="w", pady=(0, 20))

        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", side="bottom")

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=100,
            height=36,
        )
        configure_button_style(cancel_btn, "secondary")
        cancel_btn.pack(side="right", padx=5)

        self.upload_btn = ctk.CTkButton(
            button_frame,
            text="Upload",
            command=self._on_upload,
            width=100,
            height=36,
            state="disabled",
        )
        configure_button_style(self.upload_btn, "primary")
        self.upload_btn.pack(side="right", padx=5)

    def _browse_file(self) -> None:
        """Open file browser to select a file."""
        # Build file type filter
        file_types = [
            ("All supported files", " ".join(f"*{ext}" for ext in ALLOWED_EXTENSIONS)),
            ("PDF files", "*.pdf"),
            ("Word documents", "*.doc *.docx"),
            ("Excel spreadsheets", "*.xls *.xlsx"),
            ("PowerPoint presentations", "*.ppt *.pptx"),
            ("Text files", "*.txt"),
            ("All files", "*.*"),
        ]

        file_path = filedialog.askopenfilename(
            parent=self,
            title="Select File to Upload",
            filetypes=file_types,
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
        self.file_label.configure(
            text=f"{file_path.name}\n({size_str})",
            text_color=COLORS.TEXT_PRIMARY,
        )

        # Enable upload button
        self.upload_btn.configure(state="normal")

    def _on_upload(self) -> None:
        """Handle upload button click."""
        if not self.selected_file:
            InfoDialog.show_error(self, "Error", "No file selected.")
            return

        version = self.version_var.get().strip()
        if not version:
            InfoDialog.show_error(self, "Error", "Version label is required.")
            return

        # Set result as tuple of (file_path, version_label)
        self.result = (self.selected_file, version)
        self.destroy()

    def show(self) -> Optional[Tuple[Path, str]]:
        """
        Show the dialog and wait for result.

        Returns:
            Tuple of (file_path, version_label) or None if cancelled
        """
        self.wait_window()
        return self.result
