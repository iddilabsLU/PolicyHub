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

from PySide6.QtGui import QFont


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
    ACCENT_HR: str = "#14B8A6"         # Teal
    ACCENT_OTHERS: str = "#F59E0B"     # Amber

    # Filter Active State
    FILTER_ACTIVE_BG: str = "#E0F2FE"  # Light blue background
    FILTER_ACTIVE_BORDER: str = "#0EA5E9"  # Blue border

    # Info Colors (for toast notifications)
    INFO: str = "#0369A1"  # Info text color
    INFO_BG: str = "#E0F2FE"  # Info background

    # Error alias (same as DANGER)
    ERROR: str = "#B91C1C"  # Error states (alias for DANGER)


@dataclass(frozen=True)
class Typography:
    """Font configuration using Segoe UI (Windows system font)."""

    FONT_FAMILY: str = "Segoe UI"

    # Font sizes (in pixels/points)
    SIZE_WINDOW_TITLE: int = 16
    SIZE_SECTION_HEADING: int = 14
    SIZE_BODY: int = 13
    SIZE_SMALL: int = 11
    SIZE_BUTTON: int = 13
    SIZE_TABLE_HEADER: int = 12
    SIZE_TABLE_CELL: int = 12

    # Font weights (Qt uses integers: 400=normal, 500=medium, 600=semibold, 700=bold)
    WEIGHT_REGULAR: int = QFont.Weight.Normal
    WEIGHT_MEDIUM: int = QFont.Weight.Medium
    WEIGHT_SEMIBOLD: int = QFont.Weight.DemiBold
    WEIGHT_BOLD: int = QFont.Weight.Bold

    def get_font(self, size: int, weight: int = QFont.Weight.Normal) -> QFont:
        """Return a QFont for PySide6 widgets."""
        font = QFont(self.FONT_FAMILY, size)
        font.setWeight(weight)
        return font

    @property
    def window_title(self) -> QFont:
        """Font for window titles."""
        return self.get_font(self.SIZE_WINDOW_TITLE, self.WEIGHT_SEMIBOLD)

    @property
    def section_heading(self) -> QFont:
        """Font for section headings."""
        return self.get_font(self.SIZE_SECTION_HEADING, self.WEIGHT_SEMIBOLD)

    @property
    def section_title(self) -> QFont:
        """Alias for section_heading (for compatibility)."""
        return self.section_heading

    @property
    def body(self) -> QFont:
        """Font for body text."""
        return self.get_font(self.SIZE_BODY, self.WEIGHT_REGULAR)

    @property
    def small(self) -> QFont:
        """Font for small/caption text."""
        return self.get_font(self.SIZE_SMALL, self.WEIGHT_REGULAR)

    @property
    def button(self) -> QFont:
        """Font for button text."""
        return self.get_font(self.SIZE_BUTTON, self.WEIGHT_MEDIUM)

    @property
    def table_header(self) -> QFont:
        """Font for table headers."""
        return self.get_font(self.SIZE_TABLE_HEADER, self.WEIGHT_SEMIBOLD)

    @property
    def table_cell(self) -> QFont:
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


def style_button(button, style: str = "primary") -> None:
    """
    Apply consistent styling to a PySide6 QPushButton.

    Args:
        button: The QPushButton instance to style
        style: 'primary', 'secondary', or 'danger'
    """
    base_style = f"""
        QPushButton {{
            border-radius: {SPACING.CORNER_RADIUS}px;
            padding: {SPACING.BUTTON_PADDING_Y}px {SPACING.BUTTON_PADDING_X}px;
            font-family: {TYPOGRAPHY.FONT_FAMILY};
            font-size: {TYPOGRAPHY.SIZE_BUTTON}px;
            font-weight: 500;
            min-height: {SPACING.BUTTON_HEIGHT}px;
        }}
    """

    if style == "primary":
        button.setStyleSheet(base_style + f"""
            QPushButton {{
                background-color: {COLORS.PRIMARY};
                color: {COLORS.PRIMARY_FOREGROUND};
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.PRIMARY};
            }}
            QPushButton:disabled {{
                background-color: {COLORS.MUTED};
                color: {COLORS.TEXT_MUTED};
            }}
        """)
    elif style == "secondary":
        button.setStyleSheet(base_style + f"""
            QPushButton {{
                background-color: {COLORS.CARD};
                color: {COLORS.TEXT_PRIMARY};
                border: 1px solid {COLORS.INPUT_BORDER};
            }}
            QPushButton:hover {{
                background-color: {COLORS.MUTED};
                border: 1px solid {COLORS.SECONDARY_BORDER};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.SECONDARY};
            }}
            QPushButton:disabled {{
                background-color: {COLORS.MUTED};
                color: {COLORS.TEXT_MUTED};
            }}
        """)
    elif style == "danger":
        button.setStyleSheet(base_style + f"""
            QPushButton {{
                background-color: {COLORS.DANGER};
                color: {COLORS.PRIMARY_FOREGROUND};
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS.DANGER_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.DANGER};
            }}
            QPushButton:disabled {{
                background-color: {COLORS.MUTED};
                color: {COLORS.TEXT_MUTED};
            }}
        """)
    elif style == "flat":
        button.setStyleSheet(base_style + f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS.PRIMARY};
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS.MUTED};
                color: {COLORS.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.SECONDARY};
            }}
            QPushButton:disabled {{
                color: {COLORS.TEXT_MUTED};
            }}
        """)


def style_card(widget, with_shadow: bool = False) -> None:
    """
    Apply card styling to a PySide6 QWidget/QFrame.

    Args:
        widget: The QWidget or QFrame instance to style as a card
        with_shadow: If True, not used (kept for API compatibility)
    """
    widget.setStyleSheet(f"""
        QFrame, QWidget {{
            background-color: {COLORS.CARD};
            border-radius: {SPACING.CORNER_RADIUS_LARGE}px;
            border: none;
        }}
    """)
