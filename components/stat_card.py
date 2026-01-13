"""
PolicyHub Stat Card Component

A card displaying a statistic with value and label.
"""

from typing import Callable, Optional

import customtkinter as ctk

from app.theme import COLORS, SPACING, TYPOGRAPHY


class StatCard(ctk.CTkFrame):
    """
    A card displaying a statistic with value, label, and optional accent.

    Usage:
        card = StatCard(
            parent,
            value="42",
            label="Active Documents",
            accent_color=COLORS.SUCCESS,
        )

        # With click handler
        card = StatCard(
            parent,
            value="5",
            label="Overdue",
            accent_color=COLORS.DANGER,
            on_click=lambda: navigate_to_overdue(),
        )
    """

    def __init__(
        self,
        parent,
        value: str,
        label: str,
        accent_color: Optional[str] = None,
        on_click: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """
        Initialize the stat card.

        Args:
            parent: Parent widget
            value: The main value to display (e.g., "42")
            label: Description label (e.g., "Active Documents")
            accent_color: Color for the left accent bar (defaults to primary)
            on_click: Optional callback when card is clicked
            **kwargs: Additional frame options
        """
        # Use input border color for subtle shadow effect
        shadow_border = COLORS.INPUT_BORDER
        super().__init__(
            parent,
            fg_color=COLORS.CARD,
            corner_radius=SPACING.CORNER_RADIUS_LARGE,
            border_width=1,
            border_color=shadow_border,
            height=90,  # Ensure consistent card height
            **kwargs
        )
        self._default_border = shadow_border

        self._on_click = on_click
        self._accent_color = accent_color or COLORS.PRIMARY

        # Build UI
        self._build_ui(value, label)

        # Make clickable if handler provided
        if on_click:
            self._make_clickable()

    def _build_ui(self, value: str, label: str) -> None:
        """Build the card UI."""
        # Main container with horizontal layout
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=0, pady=0)

        # Left accent bar
        self.accent = ctk.CTkFrame(
            container,
            fg_color=self._accent_color,
            width=4,
            corner_radius=2,
        )
        self.accent.pack(side="left", fill="y", padx=(12, 0), pady=12)

        # Content frame
        content = ctk.CTkFrame(container, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=16, pady=12)

        # Value (large number)
        self.value_label = ctk.CTkLabel(
            content,
            text=value,
            font=TYPOGRAPHY.get_font(28, "bold"),
            text_color=COLORS.TEXT_PRIMARY,
        )
        self.value_label.pack(anchor="w")

        # Label
        self.label_widget = ctk.CTkLabel(
            content,
            text=label,
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_SECONDARY,
        )
        self.label_widget.pack(anchor="w")

    def _make_clickable(self) -> None:
        """Make the card respond to clicks."""
        self.configure(cursor="hand2")

        # Bind click events to self and all children
        self.bind("<Button-1>", self._handle_click)
        for widget in self.winfo_children():
            widget.bind("<Button-1>", self._handle_click)
            for child in widget.winfo_children():
                child.bind("<Button-1>", self._handle_click)
                for grandchild in child.winfo_children():
                    grandchild.bind("<Button-1>", self._handle_click)

        # Add hover effect
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _handle_click(self, event) -> None:
        """Handle click event."""
        if self._on_click:
            self._on_click()

    def _on_enter(self, event) -> None:
        """Handle mouse enter (hover)."""
        self.configure(border_color=self._accent_color)

    def _on_leave(self, event) -> None:
        """Handle mouse leave."""
        self.configure(border_color=self._default_border)

    def set_value(self, value: str) -> None:
        """
        Update the displayed value.

        Args:
            value: New value to display
        """
        self.value_label.configure(text=value)

    def set_label(self, label: str) -> None:
        """
        Update the label text.

        Args:
            label: New label text
        """
        self.label_widget.configure(text=label)

    def set_accent_color(self, color: str) -> None:
        """
        Update the accent color.

        Args:
            color: New accent color
        """
        self._accent_color = color
        self.accent.configure(fg_color=color)
