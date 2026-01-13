"""
PolicyHub General Settings View

Application settings form for company name, thresholds, and display preferences.
"""

from typing import TYPE_CHECKING

import customtkinter as ctk

from app.constants import ReviewFrequency
from app.theme import (
    COLORS,
    SPACING,
    TYPOGRAPHY,
    configure_button_style,
    configure_card_style,
    configure_dropdown_style,
    configure_input_style,
)
from dialogs.confirm_dialog import InfoDialog
from services.settings_service import SettingsService
from views.base_view import BaseView

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class GeneralSettingsView(BaseView):
    """
    General application settings form.

    Allows admins to configure:
    - Company name (appears in reports)
    - Warning threshold days
    - Upcoming threshold days
    - Date format
    - Default review frequency
    """

    def __init__(self, parent: ctk.CTkFrame, app: "PolicyHubApp"):
        """
        Initialize the general settings view.

        Args:
            parent: Parent widget
            app: Main application instance
        """
        super().__init__(parent, app)
        self.settings_service = SettingsService(app.db)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the settings form UI."""
        # Scrollable container
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING)

        # Form card
        form_card = ctk.CTkFrame(scroll, fg_color=COLORS.CARD)
        configure_card_style(form_card, with_shadow=True)
        form_card.pack(fill="x", pady=(0, SPACING.SECTION_SPACING))

        # Section title
        title = ctk.CTkLabel(
            form_card,
            text="Application Settings",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title.pack(anchor="w", padx=SPACING.CARD_PADDING, pady=(SPACING.CARD_PADDING, 8))

        # Description
        desc = ctk.CTkLabel(
            form_card,
            text="Configure global application settings. These settings affect all users.",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        )
        desc.pack(anchor="w", padx=SPACING.CARD_PADDING, pady=(0, SPACING.CARD_PADDING))

        # Divider
        divider = ctk.CTkFrame(form_card, fg_color=COLORS.BORDER, height=1)
        divider.pack(fill="x", padx=SPACING.CARD_PADDING)

        # Form fields container
        fields = ctk.CTkFrame(form_card, fg_color="transparent")
        fields.pack(fill="x", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        # Company Name
        self._create_field(
            fields,
            "Company Name",
            "Appears in report headers (leave blank for generic headers)",
            row=0,
        )
        self.company_name_entry = ctk.CTkEntry(
            fields,
            width=400,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
        )
        configure_input_style(self.company_name_entry)
        self.company_name_entry.grid(row=0, column=1, padx=(0, 0), pady=8, sticky="w")

        # Warning Threshold
        self._create_field(
            fields,
            "Warning Threshold (days)",
            "Documents due within this many days show as 'Due Soon'",
            row=1,
        )
        self.warning_entry = ctk.CTkEntry(
            fields,
            width=100,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
        )
        configure_input_style(self.warning_entry)
        self.warning_entry.grid(row=1, column=1, padx=(0, 0), pady=8, sticky="w")

        # Upcoming Threshold
        self._create_field(
            fields,
            "Upcoming Threshold (days)",
            "Documents due within this many days show as 'Upcoming'",
            row=2,
        )
        self.upcoming_entry = ctk.CTkEntry(
            fields,
            width=100,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
        )
        configure_input_style(self.upcoming_entry)
        self.upcoming_entry.grid(row=2, column=1, padx=(0, 0), pady=8, sticky="w")

        # Date Format
        self._create_field(
            fields,
            "Date Format",
            "How dates are displayed throughout the application",
            row=3,
        )
        self.date_format_var = ctk.StringVar()
        self.date_format_dropdown = ctk.CTkOptionMenu(
            fields,
            values=["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"],
            variable=self.date_format_var,
            width=150,
            font=TYPOGRAPHY.body,
            dropdown_font=TYPOGRAPHY.body,
        )
        configure_dropdown_style(self.date_format_dropdown)
        self.date_format_dropdown.grid(row=3, column=1, padx=(0, 0), pady=8, sticky="w")

        # Default Review Frequency
        self._create_field(
            fields,
            "Default Review Frequency",
            "Pre-selected frequency when creating new documents",
            row=4,
        )
        self.frequency_var = ctk.StringVar()
        frequency_values = [f.display_name for f in ReviewFrequency]
        self.frequency_dropdown = ctk.CTkOptionMenu(
            fields,
            values=frequency_values,
            variable=self.frequency_var,
            width=150,
            font=TYPOGRAPHY.body,
            dropdown_font=TYPOGRAPHY.body,
        )
        configure_dropdown_style(self.frequency_dropdown)
        self.frequency_dropdown.grid(row=4, column=1, padx=(0, 0), pady=8, sticky="w")

        # Configure grid weights
        fields.grid_columnconfigure(0, weight=0, minsize=200)
        fields.grid_columnconfigure(1, weight=1)

        # Save button
        btn_frame = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING.CARD_PADDING, pady=(0, SPACING.CARD_PADDING))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save Settings",
            command=self._on_save,
            width=140,
        )
        configure_button_style(save_btn, "primary")
        save_btn.pack(side="right")

        # Load current values
        self._load_settings()

    def _create_field(self, parent, label: str, description: str, row: int) -> None:
        """Create a labeled field with description."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="nw", pady=8)

        lbl = ctk.CTkLabel(
            frame,
            text=label,
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        lbl.pack(anchor="w")

        desc = ctk.CTkLabel(
            frame,
            text=description,
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
            wraplength=180,
        )
        desc.pack(anchor="w")

    def _load_settings(self) -> None:
        """Load current settings into form fields."""
        self.company_name_entry.delete(0, "end")
        self.company_name_entry.insert(0, self.settings_service.get_company_name())

        self.warning_entry.delete(0, "end")
        self.warning_entry.insert(0, str(self.settings_service.get_warning_threshold_days()))

        self.upcoming_entry.delete(0, "end")
        self.upcoming_entry.insert(0, str(self.settings_service.get_upcoming_threshold_days()))

        self.date_format_var.set(self.settings_service.get_date_format())

        # Map frequency code to display name
        freq_code = self.settings_service.get_default_review_frequency()
        try:
            freq = ReviewFrequency(freq_code)
            self.frequency_var.set(freq.display_name)
        except ValueError:
            self.frequency_var.set(ReviewFrequency.ANNUAL.display_name)

    def _on_save(self) -> None:
        """Handle save button click."""
        # Validate threshold values
        try:
            warning = int(self.warning_entry.get())
            if warning < 1 or warning > 365:
                raise ValueError("Warning threshold must be between 1 and 365")
        except ValueError as e:
            InfoDialog.show_error(
                self.winfo_toplevel(),
                "Invalid Warning Threshold",
                str(e) if "between" in str(e) else "Warning threshold must be a number between 1 and 365",
            )
            return

        try:
            upcoming = int(self.upcoming_entry.get())
            if upcoming < 1 or upcoming > 365:
                raise ValueError("Upcoming threshold must be between 1 and 365")
        except ValueError as e:
            InfoDialog.show_error(
                self.winfo_toplevel(),
                "Invalid Upcoming Threshold",
                str(e) if "between" in str(e) else "Upcoming threshold must be a number between 1 and 365",
            )
            return

        # Validate threshold relationship
        if upcoming <= warning:
            InfoDialog.show_error(
                self.winfo_toplevel(),
                "Invalid Thresholds",
                "Upcoming threshold must be greater than warning threshold",
            )
            return

        # Get frequency code from display name
        freq_display = self.frequency_var.get()
        freq_code = "ANNUAL"
        for f in ReviewFrequency:
            if f.display_name == freq_display:
                freq_code = f.value
                break

        # Save settings
        try:
            settings = {
                SettingsService.COMPANY_NAME: self.company_name_entry.get().strip(),
                SettingsService.WARNING_THRESHOLD: str(warning),
                SettingsService.UPCOMING_THRESHOLD: str(upcoming),
                SettingsService.DATE_FORMAT: self.date_format_var.get(),
                SettingsService.DEFAULT_REVIEW_FREQUENCY: freq_code,
            }
            self.settings_service.update_settings(settings)

            InfoDialog.show_success(
                self.winfo_toplevel(),
                "Settings Saved",
                "Application settings have been updated successfully.",
            )
        except PermissionError:
            InfoDialog.show_error(
                self.winfo_toplevel(),
                "Permission Denied",
                "You do not have permission to change settings.",
            )
        except Exception as e:
            InfoDialog.show_error(
                self.winfo_toplevel(),
                "Error Saving Settings",
                str(e),
            )

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        self._load_settings()
