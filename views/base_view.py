"""
PolicyHub Base View

Base class for all views in the application.
Provides common functionality and styling.
"""

import customtkinter as ctk
from typing import TYPE_CHECKING, Optional

from app.theme import COLORS, SPACING

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class BaseView(ctk.CTkFrame):
    """
    Base class for all application views.

    Provides:
    - Common styling
    - Access to the main application
    - Lifecycle methods (on_show, on_hide)
    """

    def __init__(self, parent: ctk.CTkFrame, app: "PolicyHubApp"):
        """
        Initialize the base view.

        Args:
            parent: Parent widget
            app: Main application instance
        """
        super().__init__(
            parent,
            fg_color=COLORS.BACKGROUND,
            corner_radius=0,
        )
        self.app = app
        self._is_visible = False

    def on_show(self) -> None:
        """
        Called when the view becomes visible.

        Override this method to refresh data or update the UI
        when the view is displayed.
        """
        self._is_visible = True

    def on_hide(self) -> None:
        """
        Called when the view is hidden.

        Override this method to clean up or save state
        when the view is no longer visible.
        """
        self._is_visible = False

    @property
    def is_visible(self) -> bool:
        """Check if this view is currently visible."""
        return self._is_visible


class CenteredView(BaseView):
    """
    A view that centers its content both horizontally and vertically.

    Useful for login screens, setup wizards, and other centered layouts.
    """

    def __init__(
        self,
        parent: ctk.CTkFrame,
        app: "PolicyHubApp",
        max_width: int = 400,
    ):
        """
        Initialize the centered view.

        Args:
            parent: Parent widget
            app: Main application instance
            max_width: Maximum width of the centered content
        """
        super().__init__(parent, app)
        self.max_width = max_width

        # Configure grid for centering
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        # Create centered content frame
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS.CARD,
            corner_radius=SPACING.CORNER_RADIUS_LARGE,
            border_width=1,
            border_color=COLORS.BORDER,
        )
        self.content_frame.grid(row=1, column=1, sticky="nsew")

    def set_content_padding(self, padding: int = None) -> None:
        """
        Set the padding inside the content frame.

        Args:
            padding: Padding in pixels (defaults to SPACING.CARD_PADDING)
        """
        if padding is None:
            padding = SPACING.CARD_PADDING

        self.content_frame.configure(
            padx=padding,
            pady=padding,
        )


class ScrollableView(BaseView):
    """
    A view with a scrollable content area.

    Useful for long lists or forms that may overflow the window.
    """

    def __init__(self, parent: ctk.CTkFrame, app: "PolicyHubApp"):
        """
        Initialize the scrollable view.

        Args:
            parent: Parent widget
            app: Main application instance
        """
        super().__init__(parent, app)

        # Create scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS.BACKGROUND,
            corner_radius=0,
        )
        self.scrollable_frame.pack(fill="both", expand=True)

    @property
    def content(self) -> ctk.CTkScrollableFrame:
        """Get the scrollable content frame."""
        return self.scrollable_frame
