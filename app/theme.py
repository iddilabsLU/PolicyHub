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
    WARNING: str = "#B45309"  # Due soon (< 30 days)
    WARNING_BG: str = "#FEF3C7"  # Warning row highlight
    CAUTION: str = "#A16207"  # Upcoming (< 90 days)
    CAUTION_BG: str = "#FEF9C3"  # Caution row highlight
    SUCCESS: str = "#15803D"  # On track, success states
    SUCCESS_BG: str = "#DCFCE7"  # Success row highlight


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
            hover_color="#991B1B",  # Darker red for hover
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


def configure_card_style(frame) -> None:
    """
    Apply card styling to a CustomTkinter frame.

    Args:
        frame: The CTkFrame instance to style
    """
    frame.configure(
        fg_color=COLORS.CARD,
        corner_radius=SPACING.CORNER_RADIUS_LARGE,
        border_width=1,
        border_color=COLORS.BORDER,
    )
