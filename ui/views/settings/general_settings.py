"""
PolicyHub General Settings View (PySide6)

Application settings form for company name, thresholds, and display preferences.
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QFrame,
    QScrollArea,
)

from app.constants import ReviewFrequency
from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button, style_card
from ui.components.section_card import SectionCard
from ui.components.toast import Toast
from ui.dialogs.confirm_dialog import InfoDialog
from ui.views.base_view import BaseView
from services.settings_service import SettingsService

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

    def __init__(self, parent: QWidget, app: "PolicyHubApp"):
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Scrollable container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(16)

        # Company Information Section
        company_section = SectionCard(
            self,
            title="Company Information",
            description="Company details shown in reports and headers"
        )

        company_fields = QWidget()
        company_fields.setStyleSheet("background: transparent; border: none;")
        company_layout = QGridLayout(company_fields)
        company_layout.setContentsMargins(0, 0, 0, 0)
        company_layout.setHorizontalSpacing(16)
        company_layout.setVerticalSpacing(12)

        self._create_field_label(company_layout, 0, "Company Name",
                                 "Appears in report headers")
        self.company_name_entry = QLineEdit()
        self.company_name_entry.setFixedWidth(400)
        self.company_name_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        self.company_name_entry.setPlaceholderText("Leave blank for generic headers")
        self.company_name_entry.setFont(TYPOGRAPHY.body)
        self._style_input(self.company_name_entry)
        company_layout.addWidget(self.company_name_entry, 0, 1, Qt.AlignmentFlag.AlignLeft)

        company_layout.setColumnMinimumWidth(0, 150)
        company_layout.setColumnStretch(1, 1)
        company_section.add_content(company_fields)
        scroll_layout.addWidget(company_section)

        # Review Thresholds Section
        thresholds_section = SectionCard(
            self,
            title="Review Thresholds",
            description="Configure when documents are flagged for review"
        )

        thresholds_fields = QWidget()
        thresholds_fields.setStyleSheet("background: transparent; border: none;")
        thresholds_layout = QGridLayout(thresholds_fields)
        thresholds_layout.setContentsMargins(0, 0, 0, 0)
        thresholds_layout.setHorizontalSpacing(16)
        thresholds_layout.setVerticalSpacing(12)

        self._create_field_label(thresholds_layout, 0, "Warning Days",
                                 "Show 'Due Soon' within this many days")
        self.warning_entry = QLineEdit()
        self.warning_entry.setFixedWidth(100)
        self.warning_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        self.warning_entry.setFont(TYPOGRAPHY.body)
        self._style_input(self.warning_entry)
        thresholds_layout.addWidget(self.warning_entry, 0, 1, Qt.AlignmentFlag.AlignLeft)

        self._create_field_label(thresholds_layout, 1, "Upcoming Days",
                                 "Show 'Upcoming' within this many days")
        self.upcoming_entry = QLineEdit()
        self.upcoming_entry.setFixedWidth(100)
        self.upcoming_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        self.upcoming_entry.setFont(TYPOGRAPHY.body)
        self._style_input(self.upcoming_entry)
        thresholds_layout.addWidget(self.upcoming_entry, 1, 1, Qt.AlignmentFlag.AlignLeft)

        thresholds_layout.setColumnMinimumWidth(0, 150)
        thresholds_layout.setColumnStretch(1, 1)
        thresholds_section.add_content(thresholds_fields)
        scroll_layout.addWidget(thresholds_section)

        # Display Preferences Section
        display_section = SectionCard(
            self,
            title="Display Preferences",
            description="Configure how information is displayed"
        )

        display_fields = QWidget()
        display_fields.setStyleSheet("background: transparent; border: none;")
        display_layout = QGridLayout(display_fields)
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.setHorizontalSpacing(16)
        display_layout.setVerticalSpacing(12)

        self._create_field_label(display_layout, 0, "Date Format",
                                 "How dates appear in the app")
        self.date_format_dropdown = QComboBox()
        self.date_format_dropdown.addItems(["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"])
        self.date_format_dropdown.setFixedWidth(150)
        self.date_format_dropdown.setFont(TYPOGRAPHY.body)
        self._style_dropdown(self.date_format_dropdown)
        display_layout.addWidget(self.date_format_dropdown, 0, 1, Qt.AlignmentFlag.AlignLeft)

        self._create_field_label(display_layout, 1, "Default Frequency",
                                 "Pre-selected for new documents")
        self.frequency_dropdown = QComboBox()
        self.frequency_dropdown.addItems([f.display_name for f in ReviewFrequency])
        self.frequency_dropdown.setFixedWidth(150)
        self.frequency_dropdown.setFont(TYPOGRAPHY.body)
        self._style_dropdown(self.frequency_dropdown)
        display_layout.addWidget(self.frequency_dropdown, 1, 1, Qt.AlignmentFlag.AlignLeft)

        display_layout.setColumnMinimumWidth(0, 150)
        display_layout.setColumnStretch(1, 1)
        display_section.add_content(display_fields)
        scroll_layout.addWidget(display_section)

        # Save button row
        btn_frame = QWidget()
        btn_frame.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        save_btn = QPushButton("Save Settings")
        save_btn.setFixedSize(140, 36)
        style_button(save_btn, "primary")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)
        btn_layout.addStretch()

        scroll_layout.addWidget(btn_frame)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Load current values
        self._load_settings()

    def _create_field_label(self, layout: QGridLayout, row: int, label: str, description: str) -> None:
        """Create a labeled field with description."""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(2)

        lbl = QLabel(label)
        lbl.setFont(TYPOGRAPHY.body)
        lbl.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        container_layout.addWidget(lbl)

        desc = QLabel(description)
        desc.setFont(TYPOGRAPHY.small)
        desc.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        desc.setWordWrap(True)
        desc.setMaximumWidth(180)
        container_layout.addWidget(desc)

        layout.addWidget(container, row, 0, Qt.AlignmentFlag.AlignTop)

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
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS.CARD};
                border: 1px solid {COLORS.BORDER};
                selection-background-color: {COLORS.PRIMARY};
                selection-color: {COLORS.PRIMARY_FOREGROUND};
            }}
        """)

    def _load_settings(self) -> None:
        """Load current settings into form fields."""
        self.company_name_entry.setText(self.settings_service.get_company_name())
        self.warning_entry.setText(str(self.settings_service.get_warning_threshold_days()))
        self.upcoming_entry.setText(str(self.settings_service.get_upcoming_threshold_days()))

        date_format = self.settings_service.get_date_format()
        index = self.date_format_dropdown.findText(date_format)
        if index >= 0:
            self.date_format_dropdown.setCurrentIndex(index)

        # Map frequency code to display name
        freq_code = self.settings_service.get_default_review_frequency()
        try:
            freq = ReviewFrequency(freq_code)
            index = self.frequency_dropdown.findText(freq.display_name)
            if index >= 0:
                self.frequency_dropdown.setCurrentIndex(index)
        except ValueError:
            index = self.frequency_dropdown.findText(ReviewFrequency.ANNUAL.display_name)
            if index >= 0:
                self.frequency_dropdown.setCurrentIndex(index)

    def _on_save(self) -> None:
        """Handle save button click."""
        # Validate threshold values
        try:
            warning = int(self.warning_entry.text())
            if warning < 1 or warning > 365:
                raise ValueError("Warning threshold must be between 1 and 365")
        except ValueError as e:
            InfoDialog.show_error(
                self.window(),
                "Invalid Warning Threshold",
                str(e) if "between" in str(e) else "Warning threshold must be a number between 1 and 365",
            )
            return

        try:
            upcoming = int(self.upcoming_entry.text())
            if upcoming < 1 or upcoming > 365:
                raise ValueError("Upcoming threshold must be between 1 and 365")
        except ValueError as e:
            InfoDialog.show_error(
                self.window(),
                "Invalid Upcoming Threshold",
                str(e) if "between" in str(e) else "Upcoming threshold must be a number between 1 and 365",
            )
            return

        # Validate threshold relationship
        if upcoming <= warning:
            InfoDialog.show_error(
                self.window(),
                "Invalid Thresholds",
                "Upcoming threshold must be greater than warning threshold",
            )
            return

        # Get frequency code from display name
        freq_display = self.frequency_dropdown.currentText()
        freq_code = "ANNUAL"
        for f in ReviewFrequency:
            if f.display_name == freq_display:
                freq_code = f.value
                break

        # Save settings
        try:
            settings = {
                SettingsService.COMPANY_NAME: self.company_name_entry.text().strip(),
                SettingsService.WARNING_THRESHOLD: str(warning),
                SettingsService.UPCOMING_THRESHOLD: str(upcoming),
                SettingsService.DATE_FORMAT: self.date_format_dropdown.currentText(),
                SettingsService.DEFAULT_REVIEW_FREQUENCY: freq_code,
            }
            self.settings_service.update_settings(settings)

            Toast.show_success(self, "Settings saved successfully!")
        except PermissionError:
            Toast.show_error(self, "Permission denied. Cannot change settings.")
        except Exception as e:
            Toast.show_error(self, f"Error saving settings: {str(e)}")

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        self._load_settings()
