"""
PolicyHub Theme Configuration

Defines all colors, fonts, and spacing constants for the application UI.
Based on PRD Section 6: UI/UX Design Philosophy.

Design Principles:
- Professional & Serious (financial compliance tool)
- Clean & Uncluttered with whitespace
- Sophisticated Neutrality (muted tones)
- Light-Mode Only
- Desktop-First (1920x1080 target)
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Colors:
    """Application color palette."""

    # Primary Colors (Professional & Trustworthy)
    PRIMARY: str = "#2D3E50"  # Ink Blue - headers, primary buttons, sidebar
    PRIMARY_HOVER: str = "#3D5166"  # Button hover states
    PRIMARY_FOREGROUND: str = "#FFFFFF"  # Text on primary color

    # Secondary/Accent (Warm Neutrals)
    SECONDARY: str = "#E6E2DA"  # Warm Grey-Beige - secondary buttons, borders
    SECONDARY_HOVER: str = "#DDD8CF"  # Secondary button hover
    SECONDARY_FOREGROUND: str = "#2D3E50"  # Text on secondary color
    SECONDARY_BORDER: str = "#D1CCC3"  # Border for secondary buttons

    # Backgrounds
    BACKGROUND: str = "#F9FAFB"  # Main window background
    CARD: str = "#FFFFFF"  # Cards, panels, modals
    MUTED: str = "#F3F4F6"  # Table row stripes, input backgrounds
    BORDER: str = "#E5E7EB"  # Borders, dividers
    INPUT_BORDER: str = "#D1D5DB"  # Input field borders

    # Text Colors
    TEXT_PRIMARY: str = "#1F2937"  # Main body text, headings
    TEXT_SECONDARY: str = "#6B7280"  # Labels, helper text, timestamps
    TEXT_MUTED: str = "#9CA3AF"  # Placeholder text, disabled text

    # Status Indicators (Muted Versions)
    DANGER: str = "#B91C1C"  # Overdue, error states
    DANGER_BG: str = "#FEE2E2"  # Overdue row highlight
    DANGER_HOVER: str = "#991B1B"  # Darker red for hover states
    WARNING: str = "#B45309"  # Due soon (< 30 days)
    WARNING_BG: str = "#FEF3C7"  # Warning row highlight
    CAUTION: str = "#A16207"  # Upcoming (< 90 days)
    CAUTION_BG: str = "#FEF9C3"  # Caution row highlight
    SUCCESS: str = "#15803D"  # On track, success states
    SUCCESS_BG: str = "#DCFCE7"  # Success row highlight

    # Document Type Accent Colors (for dashboard stats)
    ACCENT_POLICY: str = "#6366F1"     # Indigo
    ACCENT_PROCEDURE: str = "#8B5CF6"  # Purple
    ACCENT_MANUAL: str = "#EC4899"     # Pink
    ACCENT_HR_OTHERS: str = "#14B8A6"  # Teal


@dataclass(frozen=True)
class Typography:
    """Font configuration using Segoe UI (Windows system font)."""

    FONT_FAMILY: str = "Segoe UI"

    # Font sizes (in pixels)
    SIZE_WINDOW_TITLE: int = 16
    SIZE_SECTION_HEADING: int = 14
    SIZE_BODY: int = 13
    SIZE_SMALL: int = 11
    SIZE_BUTTON: int = 13
    SIZE_TABLE_HEADER: int = 12
    SIZE_TABLE_CELL: int = 12

    # Font weights
    WEIGHT_REGULAR: str = "normal"
    WEIGHT_MEDIUM: str = "bold"  # CustomTkinter uses 'bold' for medium
    WEIGHT_SEMIBOLD: str = "bold"

    def get_font(
        self, size: int, weight: str = "normal"
    ) -> Tuple[str, int, str]:
        """Return a font tuple for CustomTkinter widgets."""
        return (self.FONT_FAMILY, size, weight)

    @property
    def window_title(self) -> Tuple[str, int, str]:
        """Font for window titles."""
        return self.get_font(self.SIZE_WINDOW_TITLE, self.WEIGHT_SEMIBOLD)

    @property
    def section_heading(self) -> Tuple[str, int, str]:
        """Font for section headings."""
        return self.get_font(self.SIZE_SECTION_HEADING, self.WEIGHT_SEMIBOLD)

    @property
    def section_title(self) -> Tuple[str, int, str]:
        """Alias for section_heading (for compatibility)."""
        return self.section_heading

    @property
    def body(self) -> Tuple[str, int, str]:
        """Font for body text."""
        return self.get_font(self.SIZE_BODY, self.WEIGHT_REGULAR)

    @property
    def small(self) -> Tuple[str, int, str]:
        """Font for small/caption text."""
        return self.get_font(self.SIZE_SMALL, self.WEIGHT_REGULAR)

    @property
    def button(self) -> Tuple[str, int, str]:
        """Font for button text."""
        return self.get_font(self.SIZE_BUTTON, self.WEIGHT_MEDIUM)

    @property
    def table_header(self) -> Tuple[str, int, str]:
        """Font for table headers."""
        return self.get_font(self.SIZE_TABLE_HEADER, self.WEIGHT_SEMIBOLD)

    @property
    def table_cell(self) -> Tuple[str, int, str]:
        """Font for table cells."""
        return self.get_font(self.SIZE_TABLE_CELL, self.WEIGHT_REGULAR)


@dataclass(frozen=True)
class Spacing:
    """Spacing and layout constants."""

    # Window
    WINDOW_PADDING: int = 20
    SECTION_SPACING: int = 24
    CARD_PADDING: int = 16

    # Components
    BUTTON_PADDING_X: int = 10
    BUTTON_PADDING_Y: int = 8
    INPUT_PADDING_X: int = 12
    INPUT_PADDING_Y: int = 8

    # Heights
    INPUT_HEIGHT: int = 36
    BUTTON_HEIGHT: int = 36
    TABLE_ROW_HEIGHT: int = 32

    # Widths
    SIDEBAR_WIDTH: int = 200

    # Corner radius
    CORNER_RADIUS: int = 6
    CORNER_RADIUS_LARGE: int = 8
    CORNER_RADIUS_SMALL: int = 4


@dataclass(frozen=True)
class WindowSize:
    """Window size constants."""

    MIN_WIDTH: int = 1024
    MIN_HEIGHT: int = 700
    DEFAULT_WIDTH: int = 1280
    DEFAULT_HEIGHT: int = 800


# Singleton instances for easy access
COLORS = Colors()
TYPOGRAPHY = Typography()
SPACING = Spacing()
WINDOW_SIZE = WindowSize()


def configure_button_style(button, style: str = "primary") -> None:
    """
    Apply consistent styling to a CustomTkinter button.

    Args:
        button: The CTkButton instance to style
        style: 'primary', 'secondary', or 'danger'
    """
    if style == "primary":
        button.configure(
            fg_color=COLORS.PRIMARY,
            hover_color=COLORS.PRIMARY_HOVER,
            text_color=COLORS.PRIMARY_FOREGROUND,
            corner_radius=SPACING.CORNER_RADIUS,
            height=SPACING.BUTTON_HEIGHT,
            font=TYPOGRAPHY.button,
        )
    elif style == "secondary":
        button.configure(
            fg_color=COLORS.SECONDARY,
            hover_color=COLORS.SECONDARY_HOVER,
            text_color=COLORS.SECONDARY_FOREGROUND,
            border_width=1,
            border_color=COLORS.SECONDARY_BORDER,
            corner_radius=SPACING.CORNER_RADIUS,
            height=SPACING.BUTTON_HEIGHT,
            font=TYPOGRAPHY.button,
        )
    elif style == "danger":
        button.configure(
            fg_color=COLORS.DANGER,
            hover_color=COLORS.DANGER_HOVER,
            text_color=COLORS.PRIMARY_FOREGROUND,
            corner_radius=SPACING.CORNER_RADIUS,
            height=SPACING.BUTTON_HEIGHT,
            font=TYPOGRAPHY.button,
        )


def configure_input_style(entry) -> None:
    """
    Apply consistent styling to a CustomTkinter entry.

    Args:
        entry: The CTkEntry instance to style
    """
    entry.configure(
        fg_color=COLORS.CARD,
        border_color=COLORS.INPUT_BORDER,
        text_color=COLORS.TEXT_PRIMARY,
        placeholder_text_color=COLORS.TEXT_MUTED,
        corner_radius=SPACING.CORNER_RADIUS,
        height=SPACING.INPUT_HEIGHT,
        font=TYPOGRAPHY.body,
        border_width=1,
    )


def configure_card_style(frame, with_shadow: bool = False) -> None:
    """
    Apply card styling to a CustomTkinter frame.

    Args:
        frame: The CTkFrame instance to style
        with_shadow: If True, use a slightly darker border for shadow effect
    """
    border_color = "#D1D5DB" if with_shadow else COLORS.BORDER
    frame.configure(
        fg_color=COLORS.CARD,
        corner_radius=SPACING.CORNER_RADIUS_LARGE,
        border_width=1,
        border_color=border_color,
    )


def configure_dropdown_style(dropdown) -> None:
    """
    Apply consistent light styling to a CTkOptionMenu.

    Fixes the dark blue dropdown issue by using lighter colors
    that match the professional theme.

    Args:
        dropdown: The CTkOptionMenu instance to style
    """
    dropdown.configure(
        fg_color=COLORS.CARD,
        button_color=COLORS.SECONDARY,
        button_hover_color=COLORS.SECONDARY_HOVER,
        dropdown_fg_color=COLORS.CARD,
        dropdown_hover_color=COLORS.MUTED,
        text_color=COLORS.TEXT_PRIMARY,
        corner_radius=SPACING.CORNER_RADIUS,
    )


def configure_label_style(label, style: str = "body") -> None:
    """
    Apply consistent styling to a CustomTkinter label.

    Args:
        label: The CTkLabel instance to style
        style: 'heading', 'body', 'secondary', or 'muted'
    """
    styles = {
        "heading": (TYPOGRAPHY.section_heading, COLORS.TEXT_PRIMARY),
        "body": (TYPOGRAPHY.body, COLORS.TEXT_PRIMARY),
        "secondary": (TYPOGRAPHY.body, COLORS.TEXT_SECONDARY),
        "muted": (TYPOGRAPHY.small, COLORS.TEXT_MUTED),
    }
    font, color = styles.get(style, styles["body"])
    label.configure(font=font, text_color=color)


def get_table_header_style() -> dict:
    """
    Get styling dictionary for tksheet headers.

    Returns:
        Dictionary of header styling options for tksheet
    """
    return {
        "header_bg": COLORS.MUTED,
        "header_fg": COLORS.TEXT_PRIMARY,
        "header_grid_fg": COLORS.BORDER,
        "header_border_fg": COLORS.BORDER,
        "header_selected_cells_bg": COLORS.SECONDARY,
        "header_selected_cells_fg": COLORS.TEXT_PRIMARY,
    }


def get_table_body_style() -> dict:
    """
    Get styling dictionary for tksheet body/cells.

    Returns:
        Dictionary of body styling options for tksheet
    """
    return {
        "table_bg": COLORS.CARD,
        "table_fg": COLORS.TEXT_PRIMARY,
        "table_grid_fg": COLORS.BORDER,
        "table_selected_cells_border_fg": COLORS.PRIMARY,
        "table_selected_cells_bg": COLORS.PRIMARY,
        "table_selected_cells_fg": COLORS.PRIMARY_FOREGROUND,
    }


def get_table_index_style() -> dict:
    """
    Get styling dictionary for tksheet row index.

    Returns:
        Dictionary of index styling options for tksheet
    """
    return {
        "index_bg": COLORS.MUTED,
        "index_fg": COLORS.TEXT_SECONDARY,
        "index_grid_fg": COLORS.BORDER,
        "index_border_fg": COLORS.BORDER,
        "index_selected_cells_bg": COLORS.SECONDARY,
        "index_selected_cells_fg": COLORS.TEXT_PRIMARY,
    }


def configure_table_style(table) -> None:
    """
    Apply full styling to a tksheet Table/Sheet widget.

    Args:
        table: The tksheet Sheet instance to style
    """
    # Header styling
    table.set_options(**get_table_header_style())

    # Body styling
    table.set_options(**get_table_body_style())

    # Index styling (if shown)
    table.set_options(**get_table_index_style())

    # General options
    table.set_options(
        font=("Segoe UI", 11, "normal"),
        header_font=("Segoe UI", 11, "bold"),
        index_font=("Segoe UI", 10, "normal"),
        outline_thickness=1,
        outline_color=COLORS.BORDER,
        frame_bg=COLORS.CARD,
        top_left_bg=COLORS.MUTED,
        top_left_fg=COLORS.TEXT_SECONDARY,
    )
