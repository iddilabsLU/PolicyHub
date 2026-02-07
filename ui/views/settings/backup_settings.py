"""
PolicyHub Backup & Restore Settings View (PySide6)

Provides UI for creating backups and restoring from backups.
"""

import threading
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QFrame,
    QScrollArea,
    QFileDialog,
)

from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button, style_card
from ui.components.section_card import SectionCard
from ui.components.toast import Toast
from ui.dialogs.confirm_dialog import ConfirmDialog, InfoDialog
from ui.views.base_view import BaseView
from services.backup_service import BackupService

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class BackupSettingsView(BaseView):
    """
    Backup and restore settings view.

    Allows admins to:
    - Create comprehensive backups
    - Restore from existing backups
    - View backup history
    """

    def __init__(self, parent: QWidget, app: "PolicyHubApp"):
        """
        Initialize the backup settings view.

        Args:
            parent: Parent widget
            app: Main application instance
        """
        super().__init__(parent, app)
        self.backup_service = BackupService(app.db)
        self._is_busy = False
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the backup settings UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
        )
        layout.setSpacing(0)

        # Scrollable container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(SPACING.SECTION_SPACING)

        # Create Backup Section
        self._build_backup_section(scroll_layout)

        # Restore Section
        self._build_restore_section(scroll_layout)

        # History Section
        self._build_history_section(scroll_layout)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def _build_backup_section(self, parent_layout: QVBoxLayout) -> None:
        """Build the create backup section."""
        card = SectionCard(
            self,
            title="Create Backup",
            description="Create a complete backup of all data including documents, attachments, users, and settings."
        )

        # Form
        form = QWidget()
        form.setStyleSheet("background: transparent;")
        form_layout = QGridLayout(form)
        form_layout.setContentsMargins(0, 8, 0, 0)
        form_layout.setHorizontalSpacing(16)
        form_layout.setVerticalSpacing(8)

        # Backup location
        loc_label = QLabel("Backup Location:")
        loc_label.setFont(TYPOGRAPHY.body)
        loc_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        form_layout.addWidget(loc_label, 0, 0, Qt.AlignmentFlag.AlignLeft)

        loc_row = QHBoxLayout()
        self.backup_path_entry = QLineEdit()
        self.backup_path_entry.setFixedWidth(350)
        self.backup_path_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        self.backup_path_entry.setFont(TYPOGRAPHY.body)
        self.backup_path_entry.setPlaceholderText("Select backup location...")
        self._style_input(self.backup_path_entry)
        loc_row.addWidget(self.backup_path_entry)

        browse_btn = QPushButton("Browse...")
        browse_btn.setFixedSize(70, 28)
        style_button(browse_btn, "secondary")
        browse_btn.clicked.connect(self._browse_backup_location)
        loc_row.addWidget(browse_btn)
        loc_row.addStretch()

        form_layout.addLayout(loc_row, 0, 1)

        # Notes
        notes_label = QLabel("Notes (optional):")
        notes_label.setFont(TYPOGRAPHY.body)
        notes_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        form_layout.addWidget(notes_label, 1, 0, Qt.AlignmentFlag.AlignTop)

        self.notes_entry = QTextEdit()
        self.notes_entry.setFixedSize(450, 60)
        self.notes_entry.setFont(TYPOGRAPHY.body)
        self.notes_entry.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS.BACKGROUND};
                border: 1px solid {COLORS.BORDER};
                border-radius: 4px;
                padding: 8px;
                color: {COLORS.TEXT_PRIMARY};
            }}
        """)
        form_layout.addWidget(self.notes_entry, 1, 1, Qt.AlignmentFlag.AlignLeft)

        # Backup button row
        btn_row = QHBoxLayout()
        self.backup_btn = QPushButton("Create Backup")
        self.backup_btn.setFixedSize(140, 36)
        style_button(self.backup_btn, "primary")
        self.backup_btn.clicked.connect(self._on_create_backup)
        btn_row.addWidget(self.backup_btn)

        self.backup_status = QLabel("")
        self.backup_status.setFont(TYPOGRAPHY.small)
        self.backup_status.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        btn_row.addWidget(self.backup_status)
        btn_row.addStretch()

        form_layout.addLayout(btn_row, 2, 1)

        card.add_content(form)
        parent_layout.addWidget(card)

    def _build_restore_section(self, parent_layout: QVBoxLayout) -> None:
        """Build the restore from backup section."""
        card = SectionCard(
            self,
            title="Restore from Backup",
            description="⚠️ Warning: Restoring will replace ALL current data. A safety backup will be created first."
        )

        # Form
        form = QWidget()
        form.setStyleSheet("background: transparent;")
        form_layout = QGridLayout(form)
        form_layout.setContentsMargins(0, 8, 0, 0)
        form_layout.setHorizontalSpacing(16)
        form_layout.setVerticalSpacing(8)

        # File selection
        file_label = QLabel("Backup File:")
        file_label.setFont(TYPOGRAPHY.body)
        file_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        form_layout.addWidget(file_label, 0, 0, Qt.AlignmentFlag.AlignLeft)

        file_row = QHBoxLayout()
        self.restore_path_entry = QLineEdit()
        self.restore_path_entry.setFixedWidth(350)
        self.restore_path_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        self.restore_path_entry.setFont(TYPOGRAPHY.body)
        self.restore_path_entry.setPlaceholderText("Select backup file to restore...")
        self._style_input(self.restore_path_entry)
        file_row.addWidget(self.restore_path_entry)

        browse_btn = QPushButton("Browse...")
        browse_btn.setFixedSize(70, 28)
        style_button(browse_btn, "secondary")
        browse_btn.clicked.connect(self._browse_restore_file)
        file_row.addWidget(browse_btn)
        file_row.addStretch()

        form_layout.addLayout(file_row, 0, 1)

        # Backup info display
        self.backup_info_label = QLabel("")
        self.backup_info_label.setFont(TYPOGRAPHY.small)
        self.backup_info_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        self.backup_info_label.setWordWrap(True)
        form_layout.addWidget(self.backup_info_label, 1, 1, Qt.AlignmentFlag.AlignLeft)

        # Restore button row
        btn_row = QHBoxLayout()
        self.restore_btn = QPushButton("Restore Backup")
        self.restore_btn.setFixedSize(140, 36)
        self.restore_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.WARNING};
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #C0392B;
            }}
            QPushButton:disabled {{
                background-color: {COLORS.MUTED};
                color: {COLORS.TEXT_MUTED};
            }}
        """)
        self.restore_btn.clicked.connect(self._on_restore_backup)
        btn_row.addWidget(self.restore_btn)

        self.restore_status = QLabel("")
        self.restore_status.setFont(TYPOGRAPHY.small)
        self.restore_status.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        btn_row.addWidget(self.restore_status)
        btn_row.addStretch()

        form_layout.addLayout(btn_row, 2, 1)

        card.add_content(form)
        parent_layout.addWidget(card)

    def _build_history_section(self, parent_layout: QVBoxLayout) -> None:
        """Build the backup history section."""
        card = SectionCard(
            self,
            title="Backup History",
            description="Recent backups created from this application"
        )

        # History container
        self.history_frame = QWidget()
        self.history_frame.setStyleSheet("background: transparent; border: none;")
        self.history_layout = QVBoxLayout(self.history_frame)
        self.history_layout.setContentsMargins(0, 0, 0, 0)
        self.history_layout.setSpacing(4)

        card.add_content(self.history_frame)
        parent_layout.addWidget(card)

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

    def _load_history(self) -> None:
        """Load and display backup history."""
        # Clear existing
        while self.history_layout.count():
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        history = self.backup_service.get_backup_history(limit=10)

        if not history:
            no_data = QLabel("No backups have been created yet.")
            no_data.setFont(TYPOGRAPHY.body)
            no_data.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
            self.history_layout.addWidget(no_data)
            return

        # Header row
        header = QFrame()
        header.setStyleSheet(f"background-color: {COLORS.MUTED}; border-radius: 4px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 6, 8, 6)

        headers = [("Date", 150), ("Size", 80), ("Notes", 300)]
        for text, width in headers:
            lbl = QLabel(text)
            lbl.setFont(TYPOGRAPHY.body)
            lbl.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
            lbl.setFixedWidth(width)
            header_layout.addWidget(lbl)
        header_layout.addStretch()

        self.history_layout.addWidget(header)

        # Data rows
        for backup in history:
            row = QFrame()
            row.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 2, 8, 2)

            date_str = backup.created_at[:16].replace("T", " ") if backup.created_at else "N/A"
            date_lbl = QLabel(date_str)
            date_lbl.setFont(TYPOGRAPHY.body)
            date_lbl.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
            date_lbl.setFixedWidth(150)
            row_layout.addWidget(date_lbl)

            size_str = self.backup_service.format_backup_size(backup.size_bytes)
            size_lbl = QLabel(size_str)
            size_lbl.setFont(TYPOGRAPHY.body)
            size_lbl.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
            size_lbl.setFixedWidth(80)
            row_layout.addWidget(size_lbl)

            notes_str = backup.notes or "-"
            if len(notes_str) > 40:
                notes_str = notes_str[:37] + "..."
            notes_lbl = QLabel(notes_str)
            notes_lbl.setFont(TYPOGRAPHY.body)
            notes_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
            notes_lbl.setFixedWidth(300)
            row_layout.addWidget(notes_lbl)

            row_layout.addStretch()
            self.history_layout.addWidget(row)

    def _browse_backup_location(self) -> None:
        """Open file dialog to select backup location."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Backup As",
            "PolicyHub_Backup.zip",
            "ZIP files (*.zip)",
        )
        if path:
            self.backup_path_entry.setText(path)

    def _browse_restore_file(self) -> None:
        """Open file dialog to select backup file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup File",
            "",
            "ZIP files (*.zip)",
        )
        if path:
            self.restore_path_entry.setText(path)
            self._validate_restore_file(path)

    def _validate_restore_file(self, path: str) -> None:
        """Validate the selected backup file and show info."""
        is_valid, message, info = self.backup_service.validate_backup(Path(path))

        if is_valid and info:
            created_at = info.get("created_at", "Unknown")[:16].replace("T", " ")
            created_by = info.get("created_by", "Unknown")
            notes = info.get("notes", "")

            info_text = f"Created: {created_at} by {created_by}"
            if notes:
                info_text += f"\nNotes: {notes}"

            self.backup_info_label.setText(info_text)
            self.backup_info_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        else:
            self.backup_info_label.setText(f"Invalid: {message}")
            self.backup_info_label.setStyleSheet(f"color: {COLORS.ERROR}; background: transparent;")

    def _on_create_backup(self) -> None:
        """Handle create backup button click."""
        if self._is_busy:
            return

        path = self.backup_path_entry.text().strip()
        if not path:
            InfoDialog.show_error(self.window(), "Error", "Please select a backup location.")
            return

        notes = self.notes_entry.toPlainText().strip()

        self._is_busy = True
        self.backup_btn.setEnabled(False)
        self.backup_status.setText("Creating backup...")

        # Run backup in background thread
        def do_backup():
            try:
                result_path = self.backup_service.create_backup(Path(path), notes)
                QTimer.singleShot(0, lambda: self._on_backup_complete(True, str(result_path)))
            except Exception as e:
                QTimer.singleShot(0, lambda: self._on_backup_complete(False, str(e)))

        thread = threading.Thread(target=do_backup, daemon=True)
        thread.start()

    def _on_backup_complete(self, success: bool, message: str) -> None:
        """Handle backup completion."""
        self._is_busy = False
        self.backup_btn.setEnabled(True)
        self.backup_status.setText("")

        if success:
            Toast.show_success(self, "Backup created successfully!")
            self.backup_path_entry.clear()
            self.notes_entry.clear()
            self._load_history()
        else:
            Toast.show_error(self, f"Backup failed: {message}")

    def _on_restore_backup(self) -> None:
        """Handle restore backup button click."""
        if self._is_busy:
            return

        path = self.restore_path_entry.text().strip()
        if not path:
            InfoDialog.show_error(self.window(), "Error", "Please select a backup file to restore.")
            return

        # Validate first
        is_valid, message, _ = self.backup_service.validate_backup(Path(path))
        if not is_valid:
            InfoDialog.show_error(self.window(), "Error", f"Invalid backup file:\n{message}")
            return

        # Confirm restore
        if not ConfirmDialog.ask(
            self.window(),
            "Restore Backup",
            "This will REPLACE all current data with the backup.\n\n"
            "A safety backup of your current data will be created first.\n\n"
            "Are you sure you want to continue?",
        ):
            return

        self._is_busy = True
        self.restore_btn.setEnabled(False)
        self.restore_status.setText("Restoring backup...")

        # Run restore in background thread
        def do_restore():
            try:
                self.backup_service.restore_backup(Path(path))
                QTimer.singleShot(0, lambda: self._on_restore_complete(True, ""))
            except Exception as e:
                QTimer.singleShot(0, lambda: self._on_restore_complete(False, str(e)))

        thread = threading.Thread(target=do_restore, daemon=True)
        thread.start()

    def _on_restore_complete(self, success: bool, message: str) -> None:
        """Handle restore completion."""
        self._is_busy = False
        self.restore_btn.setEnabled(True)
        self.restore_status.setText("")

        if success:
            Toast.show_success(self, "Backup restored! Please restart the application.")
            self.restore_path_entry.clear()
            self.backup_info_label.setText("")
        else:
            Toast.show_error(self, f"Restore failed: {message}")

    def on_show(self) -> None:
        """Called when view becomes visible."""
        super().on_show()
        self._load_history()
