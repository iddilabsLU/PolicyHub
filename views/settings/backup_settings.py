"""
PolicyHub Backup & Restore Settings View

Provides UI for creating backups and restoring from backups.
"""

import threading
from pathlib import Path
from tkinter import filedialog
from typing import TYPE_CHECKING

import customtkinter as ctk

from app.theme import (
    COLORS,
    SPACING,
    TYPOGRAPHY,
    configure_button_style,
    configure_card_style,
    configure_input_style,
)
from dialogs.confirm_dialog import ConfirmDialog, InfoDialog
from services.backup_service import BackupService
from views.base_view import BaseView

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

    def __init__(self, parent: ctk.CTkFrame, app: "PolicyHubApp"):
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
        # Scrollable container
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING)

        # Create Backup Section
        self._build_backup_section(scroll)

        # Restore Section
        self._build_restore_section(scroll)

        # History Section
        self._build_history_section(scroll)

    def _build_backup_section(self, parent: ctk.CTkFrame) -> None:
        """Build the create backup section."""
        card = ctk.CTkFrame(parent, fg_color=COLORS.CARD)
        configure_card_style(card, with_shadow=True)
        card.pack(fill="x", pady=(0, SPACING.SECTION_SPACING))

        # Title
        title = ctk.CTkLabel(
            card,
            text="Create Backup",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title.pack(anchor="w", padx=SPACING.CARD_PADDING, pady=(SPACING.CARD_PADDING, 8))

        # Description
        desc = ctk.CTkLabel(
            card,
            text="Create a complete backup of all data including documents, attachments, users, and settings.",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
            wraplength=600,
            justify="left",
        )
        desc.pack(anchor="w", padx=SPACING.CARD_PADDING, pady=(0, SPACING.CARD_PADDING))

        # Divider
        divider = ctk.CTkFrame(card, fg_color=COLORS.BORDER, height=1)
        divider.pack(fill="x", padx=SPACING.CARD_PADDING)

        # Form container
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        # Backup location
        loc_label = ctk.CTkLabel(
            form,
            text="Backup Location:",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        loc_label.grid(row=0, column=0, sticky="w", pady=8)

        loc_frame = ctk.CTkFrame(form, fg_color="transparent")
        loc_frame.grid(row=0, column=1, sticky="w", padx=(16, 0), pady=8)

        self.backup_path_entry = ctk.CTkEntry(
            loc_frame,
            width=350,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
            placeholder_text="Select backup location...",
        )
        configure_input_style(self.backup_path_entry)
        self.backup_path_entry.pack(side="left")

        browse_btn = ctk.CTkButton(
            loc_frame,
            text="Browse...",
            width=80,
            height=SPACING.INPUT_HEIGHT,
            command=self._browse_backup_location,
        )
        configure_button_style(browse_btn, "secondary")
        browse_btn.pack(side="left", padx=(8, 0))

        # Notes
        notes_label = ctk.CTkLabel(
            form,
            text="Notes (optional):",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        notes_label.grid(row=1, column=0, sticky="nw", pady=8)

        self.notes_entry = ctk.CTkTextbox(
            form,
            width=450,
            height=60,
            font=TYPOGRAPHY.body,
            fg_color=COLORS.BACKGROUND,
            border_color=COLORS.BORDER,
            border_width=1,
        )
        self.notes_entry.grid(row=1, column=1, sticky="w", padx=(16, 0), pady=8)

        # Backup button
        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.grid(row=2, column=1, sticky="w", padx=(16, 0), pady=(8, 0))

        self.backup_btn = ctk.CTkButton(
            btn_frame,
            text="Create Backup",
            width=140,
            height=36,
            command=self._on_create_backup,
        )
        configure_button_style(self.backup_btn, "primary")
        self.backup_btn.pack(side="left")

        # Progress label
        self.backup_status = ctk.CTkLabel(
            btn_frame,
            text="",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        )
        self.backup_status.pack(side="left", padx=(16, 0))

    def _build_restore_section(self, parent: ctk.CTkFrame) -> None:
        """Build the restore from backup section."""
        card = ctk.CTkFrame(parent, fg_color=COLORS.CARD)
        configure_card_style(card, with_shadow=True)
        card.pack(fill="x", pady=(0, SPACING.SECTION_SPACING))

        # Title
        title = ctk.CTkLabel(
            card,
            text="Restore from Backup",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title.pack(anchor="w", padx=SPACING.CARD_PADDING, pady=(SPACING.CARD_PADDING, 8))

        # Warning
        warning = ctk.CTkLabel(
            card,
            text="Warning: Restoring will replace ALL current data. A safety backup will be created first.",
            font=TYPOGRAPHY.small,
            text_color=COLORS.WARNING,
            wraplength=600,
            justify="left",
        )
        warning.pack(anchor="w", padx=SPACING.CARD_PADDING, pady=(0, SPACING.CARD_PADDING))

        # Divider
        divider = ctk.CTkFrame(card, fg_color=COLORS.BORDER, height=1)
        divider.pack(fill="x", padx=SPACING.CARD_PADDING)

        # Form container
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        # Restore file selection
        file_label = ctk.CTkLabel(
            form,
            text="Backup File:",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        file_label.grid(row=0, column=0, sticky="w", pady=8)

        file_frame = ctk.CTkFrame(form, fg_color="transparent")
        file_frame.grid(row=0, column=1, sticky="w", padx=(16, 0), pady=8)

        self.restore_path_entry = ctk.CTkEntry(
            file_frame,
            width=350,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
            placeholder_text="Select backup file to restore...",
        )
        configure_input_style(self.restore_path_entry)
        self.restore_path_entry.pack(side="left")

        browse_btn = ctk.CTkButton(
            file_frame,
            text="Browse...",
            width=80,
            height=SPACING.INPUT_HEIGHT,
            command=self._browse_restore_file,
        )
        configure_button_style(browse_btn, "secondary")
        browse_btn.pack(side="left", padx=(8, 0))

        # Backup info display
        self.backup_info_label = ctk.CTkLabel(
            form,
            text="",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
            wraplength=450,
            justify="left",
        )
        self.backup_info_label.grid(row=1, column=1, sticky="w", padx=(16, 0), pady=4)

        # Restore button
        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.grid(row=2, column=1, sticky="w", padx=(16, 0), pady=(8, 0))

        self.restore_btn = ctk.CTkButton(
            btn_frame,
            text="Restore Backup",
            width=140,
            height=36,
            command=self._on_restore_backup,
            fg_color=COLORS.WARNING,
            hover_color="#C0392B",
        )
        self.restore_btn.pack(side="left")

        # Progress label
        self.restore_status = ctk.CTkLabel(
            btn_frame,
            text="",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        )
        self.restore_status.pack(side="left", padx=(16, 0))

    def _build_history_section(self, parent: ctk.CTkFrame) -> None:
        """Build the backup history section."""
        card = ctk.CTkFrame(parent, fg_color=COLORS.CARD)
        configure_card_style(card, with_shadow=True)
        card.pack(fill="x", pady=(0, SPACING.SECTION_SPACING))

        # Title
        title = ctk.CTkLabel(
            card,
            text="Backup History",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title.pack(anchor="w", padx=SPACING.CARD_PADDING, pady=(SPACING.CARD_PADDING, 8))

        # Divider
        divider = ctk.CTkFrame(card, fg_color=COLORS.BORDER, height=1)
        divider.pack(fill="x", padx=SPACING.CARD_PADDING)

        # History container
        self.history_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.history_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

    def _load_history(self) -> None:
        """Load and display backup history."""
        # Clear existing
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        history = self.backup_service.get_backup_history(limit=10)

        if not history:
            no_data = ctk.CTkLabel(
                self.history_frame,
                text="No backups have been created yet.",
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_SECONDARY,
            )
            no_data.pack(anchor="w", pady=8)
            return

        # Header row
        header = ctk.CTkFrame(self.history_frame, fg_color=COLORS.MUTED)
        header.pack(fill="x", pady=(0, 4))

        headers = [("Date", 150), ("Size", 80), ("Notes", 300)]
        for text, width in headers:
            lbl = ctk.CTkLabel(
                header,
                text=text,
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_PRIMARY,
                width=width,
                anchor="w",
            )
            lbl.pack(side="left", padx=8, pady=6)

        # Data rows
        for backup in history:
            row = ctk.CTkFrame(self.history_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            # Date
            date_str = backup.created_at[:16].replace("T", " ") if backup.created_at else "N/A"
            date_lbl = ctk.CTkLabel(
                row,
                text=date_str,
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_PRIMARY,
                width=150,
                anchor="w",
            )
            date_lbl.pack(side="left", padx=8)

            # Size
            size_str = self.backup_service.format_backup_size(backup.size_bytes)
            size_lbl = ctk.CTkLabel(
                row,
                text=size_str,
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_PRIMARY,
                width=80,
                anchor="w",
            )
            size_lbl.pack(side="left", padx=8)

            # Notes
            notes_str = backup.notes or "-"
            if len(notes_str) > 40:
                notes_str = notes_str[:37] + "..."
            notes_lbl = ctk.CTkLabel(
                row,
                text=notes_str,
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_SECONDARY,
                width=300,
                anchor="w",
            )
            notes_lbl.pack(side="left", padx=8)

    def _browse_backup_location(self) -> None:
        """Open file dialog to select backup location."""
        path = filedialog.asksaveasfilename(
            title="Save Backup As",
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip")],
            initialfile="PolicyHub_Backup",
        )
        if path:
            self.backup_path_entry.delete(0, "end")
            self.backup_path_entry.insert(0, path)

    def _browse_restore_file(self) -> None:
        """Open file dialog to select backup file."""
        path = filedialog.askopenfilename(
            title="Select Backup File",
            filetypes=[("ZIP files", "*.zip")],
        )
        if path:
            self.restore_path_entry.delete(0, "end")
            self.restore_path_entry.insert(0, path)
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

            self.backup_info_label.configure(text=info_text, text_color=COLORS.TEXT_SECONDARY)
        else:
            self.backup_info_label.configure(text=f"Invalid: {message}", text_color=COLORS.ERROR)

    def _on_create_backup(self) -> None:
        """Handle create backup button click."""
        if self._is_busy:
            return

        path = self.backup_path_entry.get().strip()
        if not path:
            InfoDialog.show_error(self, "Please select a backup location.")
            return

        notes = self.notes_entry.get("1.0", "end-1c").strip()

        self._is_busy = True
        self.backup_btn.configure(state="disabled")
        self.backup_status.configure(text="Creating backup...")

        # Run backup in background thread
        def do_backup():
            try:
                result_path = self.backup_service.create_backup(Path(path), notes)
                self.after(0, lambda: self._on_backup_complete(True, result_path))
            except Exception as e:
                self.after(0, lambda: self._on_backup_complete(False, str(e)))

        thread = threading.Thread(target=do_backup, daemon=True)
        thread.start()

    def _on_backup_complete(self, success: bool, message: str) -> None:
        """Handle backup completion."""
        self._is_busy = False
        self.backup_btn.configure(state="normal")
        self.backup_status.configure(text="")

        if success:
            InfoDialog.show_success(self, f"Backup created successfully!\n\n{message}")
            self.backup_path_entry.delete(0, "end")
            self.notes_entry.delete("1.0", "end")
            self._load_history()
        else:
            InfoDialog.show_error(self, f"Backup failed:\n{message}")

    def _on_restore_backup(self) -> None:
        """Handle restore backup button click."""
        if self._is_busy:
            return

        path = self.restore_path_entry.get().strip()
        if not path:
            InfoDialog.show_error(self, "Please select a backup file to restore.")
            return

        # Validate first
        is_valid, message, _ = self.backup_service.validate_backup(Path(path))
        if not is_valid:
            InfoDialog.show_error(self, f"Invalid backup file:\n{message}")
            return

        # Confirm restore
        if not ConfirmDialog.ask(
            self,
            "Restore Backup",
            "This will REPLACE all current data with the backup.\n\n"
            "A safety backup of your current data will be created first.\n\n"
            "Are you sure you want to continue?",
        ):
            return

        self._is_busy = True
        self.restore_btn.configure(state="disabled")
        self.restore_status.configure(text="Restoring backup...")

        # Run restore in background thread
        def do_restore():
            try:
                self.backup_service.restore_backup(Path(path))
                self.after(0, lambda: self._on_restore_complete(True, ""))
            except Exception as e:
                self.after(0, lambda: self._on_restore_complete(False, str(e)))

        thread = threading.Thread(target=do_restore, daemon=True)
        thread.start()

    def _on_restore_complete(self, success: bool, message: str) -> None:
        """Handle restore completion."""
        self._is_busy = False
        self.restore_btn.configure(state="normal")
        self.restore_status.configure(text="")

        if success:
            InfoDialog.show_success(
                self,
                "Backup restored successfully!\n\n"
                "Please restart the application for changes to take effect.",
            )
            self.restore_path_entry.delete(0, "end")
            self.backup_info_label.configure(text="")
        else:
            InfoDialog.show_error(self, f"Restore failed:\n{message}")

    def on_show(self) -> None:
        """Called when view becomes visible."""
        super().on_show()
        self._load_history()
