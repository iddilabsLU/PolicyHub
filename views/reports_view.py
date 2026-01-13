"""
PolicyHub Reports View

View for generating document reports in PDF and Excel formats.
"""

import os
import subprocess
import tempfile
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk

from app.constants import DocumentStatus, DocumentType, ReviewStatus
from app.theme import (
    COLORS,
    SPACING,
    TYPOGRAPHY,
    configure_button_style,
    configure_card_style,
    configure_dropdown_style,
)
from dialogs.confirm_dialog import InfoDialog
from services.category_service import CategoryService
from services.entity_service import EntityService
from services.report_service import ReportFilters, ReportService
from views.base_view import BaseView

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class ReportsView(BaseView):
    """
    Reports generation view.

    Allows users to:
    - Select report type
    - Apply filters
    - Choose output format (PDF/Excel)
    - Generate and open reports
    """

    def __init__(self, parent: ctk.CTkFrame, app: "PolicyHubApp"):
        """
        Initialize the reports view.

        Args:
            parent: Parent widget
            app: Main application instance
        """
        super().__init__(parent, app)
        self.report_service = ReportService(app.db)
        self.category_service = CategoryService(app.db)
        self.entity_service = EntityService(app.db)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the reports view UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS.CARD, height=60)
        configure_card_style(header, with_shadow=True)
        header.pack(fill="x", padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING)
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="Reports",
            font=TYPOGRAPHY.window_title,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title.pack(side="left", padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        # Main content card
        content = ctk.CTkFrame(self, fg_color=COLORS.CARD)
        configure_card_style(content, with_shadow=True)
        content.pack(
            fill="both",
            expand=True,
            padx=SPACING.WINDOW_PADDING,
            pady=(0, SPACING.WINDOW_PADDING),
        )

        # Inner padding
        inner = ctk.CTkFrame(content, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=SPACING.CARD_PADDING, pady=SPACING.CARD_PADDING)

        # Report Type Section
        type_section = ctk.CTkFrame(inner, fg_color="transparent")
        type_section.pack(fill="x", pady=(0, 20))

        type_label = ctk.CTkLabel(
            type_section,
            text="Report Type",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        type_label.pack(anchor="w", pady=(0, 8))

        # Report type radio buttons
        self.report_type_var = ctk.StringVar(value="full_register")

        report_types = [
            ("full_register", "Document Register", "Complete list of all policies and procedures"),
            ("review_schedule", "Review Schedule", "Upcoming and overdue document reviews"),
            ("compliance_status", "Compliance Status", "Policy compliance overview with status"),
        ]

        for type_id, type_name, description in report_types:
            frame = ctk.CTkFrame(type_section, fg_color="transparent")
            frame.pack(fill="x", pady=4)

            radio = ctk.CTkRadioButton(
                frame,
                text=type_name,
                variable=self.report_type_var,
                value=type_id,
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_PRIMARY,
                fg_color=COLORS.PRIMARY,
                hover_color=COLORS.PRIMARY_HOVER,
            )
            radio.pack(side="left")

            desc = ctk.CTkLabel(
                frame,
                text=f"  -  {description}",
                font=TYPOGRAPHY.small,
                text_color=COLORS.TEXT_MUTED,
            )
            desc.pack(side="left")

        # Divider
        divider = ctk.CTkFrame(inner, fg_color=COLORS.BORDER, height=1)
        divider.pack(fill="x", pady=16)

        # Filters Section
        filter_section = ctk.CTkFrame(inner, fg_color="transparent")
        filter_section.pack(fill="x", pady=(0, 20))

        filter_label = ctk.CTkLabel(
            filter_section,
            text="Filters (Optional)",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        filter_label.pack(anchor="w", pady=(0, 12))

        # Filter dropdowns grid
        filters_grid = ctk.CTkFrame(filter_section, fg_color="transparent")
        filters_grid.pack(fill="x")

        # Status filter
        status_frame = ctk.CTkFrame(filters_grid, fg_color="transparent")
        status_frame.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            status_frame,
            text="Status",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 4))

        self.status_var = ctk.StringVar(value="All")
        status_values = ["All"] + [s.display_name for s in DocumentStatus]
        self.status_dropdown = ctk.CTkOptionMenu(
            status_frame,
            values=status_values,
            variable=self.status_var,
            width=150,
            font=TYPOGRAPHY.body,
            dropdown_font=TYPOGRAPHY.body,
        )
        configure_dropdown_style(self.status_dropdown)
        self.status_dropdown.pack()

        # Type filter
        type_frame = ctk.CTkFrame(filters_grid, fg_color="transparent")
        type_frame.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            type_frame,
            text="Document Type",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 4))

        self.doc_type_var = ctk.StringVar(value="All")
        type_values = ["All"] + [t.display_name for t in DocumentType]
        self.doc_type_dropdown = ctk.CTkOptionMenu(
            type_frame,
            values=type_values,
            variable=self.doc_type_var,
            width=150,
            font=TYPOGRAPHY.body,
            dropdown_font=TYPOGRAPHY.body,
        )
        configure_dropdown_style(self.doc_type_dropdown)
        self.doc_type_dropdown.pack()

        # Category filter
        cat_frame = ctk.CTkFrame(filters_grid, fg_color="transparent")
        cat_frame.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            cat_frame,
            text="Category",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 4))

        self.category_var = ctk.StringVar(value="All")
        self.category_dropdown = ctk.CTkOptionMenu(
            cat_frame,
            values=["All"],  # Will be populated on show
            variable=self.category_var,
            width=180,
            font=TYPOGRAPHY.body,
            dropdown_font=TYPOGRAPHY.body,
        )
        configure_dropdown_style(self.category_dropdown)
        self.category_dropdown.pack()

        # Review status filter
        review_frame = ctk.CTkFrame(filters_grid, fg_color="transparent")
        review_frame.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            review_frame,
            text="Review Status",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 4))

        self.review_var = ctk.StringVar(value="All")
        review_values = ["All"] + [r.display_name for r in ReviewStatus]
        self.review_dropdown = ctk.CTkOptionMenu(
            review_frame,
            values=review_values,
            variable=self.review_var,
            width=150,
            font=TYPOGRAPHY.body,
            dropdown_font=TYPOGRAPHY.body,
        )
        configure_dropdown_style(self.review_dropdown)
        self.review_dropdown.pack()

        # Second row of filters
        filters_grid2 = ctk.CTkFrame(filter_section, fg_color="transparent")
        filters_grid2.pack(fill="x", pady=(12, 0))

        # Mandatory read filter
        mandatory_frame = ctk.CTkFrame(filters_grid2, fg_color="transparent")
        mandatory_frame.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            mandatory_frame,
            text="Mandatory Read",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 4))

        self.mandatory_var = ctk.StringVar(value="All")
        mandatory_values = ["All", "Yes", "No"]
        self.mandatory_dropdown = ctk.CTkOptionMenu(
            mandatory_frame,
            values=mandatory_values,
            variable=self.mandatory_var,
            width=120,
            font=TYPOGRAPHY.body,
            dropdown_font=TYPOGRAPHY.body,
        )
        configure_dropdown_style(self.mandatory_dropdown)
        self.mandatory_dropdown.pack()

        # Entity filter
        entity_frame = ctk.CTkFrame(filters_grid2, fg_color="transparent")
        entity_frame.pack(side="left")

        ctk.CTkLabel(
            entity_frame,
            text="Applicable Entity",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 4))

        self.entity_var = ctk.StringVar(value="All")
        self.entity_dropdown = ctk.CTkOptionMenu(
            entity_frame,
            values=["All"],  # Will be populated on show
            variable=self.entity_var,
            width=180,
            font=TYPOGRAPHY.body,
            dropdown_font=TYPOGRAPHY.body,
        )
        configure_dropdown_style(self.entity_dropdown)
        self.entity_dropdown.pack()

        # Divider
        divider2 = ctk.CTkFrame(inner, fg_color=COLORS.BORDER, height=1)
        divider2.pack(fill="x", pady=16)

        # Output Format Section
        format_section = ctk.CTkFrame(inner, fg_color="transparent")
        format_section.pack(fill="x", pady=(0, 20))

        format_label = ctk.CTkLabel(
            format_section,
            text="Output Format",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        format_label.pack(anchor="w", pady=(0, 8))

        self.format_var = ctk.StringVar(value="pdf")

        formats_frame = ctk.CTkFrame(format_section, fg_color="transparent")
        formats_frame.pack(fill="x")

        pdf_radio = ctk.CTkRadioButton(
            formats_frame,
            text="PDF Document",
            variable=self.format_var,
            value="pdf",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
            fg_color=COLORS.PRIMARY,
            hover_color=COLORS.PRIMARY_HOVER,
        )
        pdf_radio.pack(side="left", padx=(0, 30))

        excel_radio = ctk.CTkRadioButton(
            formats_frame,
            text="Excel Spreadsheet",
            variable=self.format_var,
            value="excel",
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
            fg_color=COLORS.PRIMARY,
            hover_color=COLORS.PRIMARY_HOVER,
        )
        excel_radio.pack(side="left")

        # Generate Button
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))

        self.generate_btn = ctk.CTkButton(
            btn_frame,
            text="Generate Report",
            command=self._on_generate,
            width=180,
            height=40,
        )
        configure_button_style(self.generate_btn, "primary")
        self.generate_btn.pack(side="left")

        # Status label
        self.status_label = ctk.CTkLabel(
            btn_frame,
            text="",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_MUTED,
        )
        self.status_label.pack(side="left", padx=(16, 0))

    def _load_categories(self) -> None:
        """Load categories for the dropdown."""
        try:
            categories = self.category_service.get_active_categories()
            values = ["All"] + [f"{cat.code} - {cat.name}" for cat in categories]
            self.category_dropdown.configure(values=values)
            self._categories = {f"{cat.code} - {cat.name}": cat.code for cat in categories}
        except Exception as e:
            self._categories = {}

    def _load_entities(self) -> None:
        """Load entities for the dropdown."""
        try:
            entities = self.entity_service.get_entity_names()
            values = ["All"] + entities
            self.entity_dropdown.configure(values=values)
        except Exception:
            pass

    def _get_filters(self) -> ReportFilters:
        """Get the current filter values."""
        filters = ReportFilters()

        # Status
        status_display = self.status_var.get()
        if status_display != "All":
            for s in DocumentStatus:
                if s.display_name == status_display:
                    filters.status = s.value
                    break

        # Document type
        type_display = self.doc_type_var.get()
        if type_display != "All":
            for t in DocumentType:
                if t.display_name == type_display:
                    filters.doc_type = t.value
                    break

        # Category
        cat_display = self.category_var.get()
        if cat_display != "All" and hasattr(self, "_categories"):
            filters.category = self._categories.get(cat_display)

        # Review status
        review_display = self.review_var.get()
        if review_display != "All":
            for r in ReviewStatus:
                if r.display_name == review_display:
                    filters.review_status = r.value
                    break

        # Mandatory read
        mandatory_display = self.mandatory_var.get()
        if mandatory_display == "Yes":
            filters.mandatory_read_all = True
        elif mandatory_display == "No":
            filters.mandatory_read_all = False

        # Applicable entity
        entity_display = self.entity_var.get()
        if entity_display != "All":
            filters.applicable_entity = entity_display

        return filters

    def _on_generate(self) -> None:
        """Handle generate report button click."""
        self.generate_btn.configure(state="disabled")
        self.status_label.configure(text="Generating report...")
        self.update_idletasks()

        try:
            # Get report parameters
            report_type = self.report_type_var.get()
            output_format = self.format_var.get()
            filters = self._get_filters()

            # Generate to temp directory
            output_dir = tempfile.gettempdir()

            # Generate report
            output_path = self.report_service.generate_report(
                report_type=report_type,
                output_format=output_format,
                output_dir=output_dir,
                filters=filters,
            )

            self.status_label.configure(text="Report generated successfully!")

            # Open the file
            self._open_file(output_path)

        except Exception as e:
            InfoDialog.show_error(
                self.winfo_toplevel(),
                "Report Error",
                f"Failed to generate report: {str(e)}",
            )
            self.status_label.configure(text="")

        finally:
            self.generate_btn.configure(state="normal")

    def _open_file(self, file_path: str) -> None:
        """
        Open a file with the default application.

        Args:
            file_path: Path to the file to open
        """
        try:
            # Windows
            os.startfile(file_path)
        except AttributeError:
            # macOS / Linux
            try:
                subprocess.run(["open", file_path], check=True)
            except FileNotFoundError:
                subprocess.run(["xdg-open", file_path], check=True)
        except Exception as e:
            InfoDialog.show_info(
                self.winfo_toplevel(),
                "Report Generated",
                f"Report saved to:\n{file_path}",
            )

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        self._load_categories()
        self._load_entities()
        self.status_label.configure(text="")
