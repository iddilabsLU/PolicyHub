"""
PolicyHub Base Dialog

Base class for modal dialog windows.
"""

from typing import Any, Optional

import customtkinter as ctk

from app.theme import COLORS


class BaseDialog(ctk.CTkToplevel):
    """
    Base class for modal dialogs.

    Features:
    - Modal behavior (grabs focus)
    - Centered positioning on parent
    - Consistent styling
    - Close on Escape key
    - Result storage

    Usage:
        class MyDialog(BaseDialog):
            def __init__(self, parent, **kwargs):
                super().__init__(parent, "My Dialog", width=400, height=300)
                self._build_ui()

            def _build_ui(self):
                # Build your UI here
                pass

        # Show dialog and get result
        dialog = MyDialog(parent)
        result = dialog.show()
    """

    def __init__(
        self,
        parent,
        title: str,
        width: int = 500,
        height: int = 400,
        resizable: bool = False,
    ):
        """
        Initialize the base dialog.

        Args:
            parent: Parent window
            title: Dialog title
            width: Dialog width in pixels
            height: Dialog height in pixels
            resizable: Whether the dialog can be resized
        """
        super().__init__(parent)

        self.title(title)

        # Get screen dimensions and cap dialog size at 90% of screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        max_width = int(screen_width * 0.9)
        max_height = int(screen_height * 0.85)

        # Ensure dialog fits on screen
        final_width = min(width, max_width)
        final_height = min(height, max_height)

        self.geometry(f"{final_width}x{final_height}")
        self.resizable(resizable, resizable)
        self.configure(fg_color=COLORS.BACKGROUND)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self._center_on_parent(parent, final_width, final_height)

        # Close on Escape
        self.bind("<Escape>", lambda e: self._on_cancel())

        # Handle window close button
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Result storage
        self.result: Optional[Any] = None
        self._cancelled = False

    def _center_on_parent(self, parent, width: int, height: int) -> None:
        """
        Center the dialog on the parent window.

        Args:
            parent: Parent window
            width: Dialog width
            height: Dialog height
        """
        parent.update_idletasks()

        # Get parent position and size
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()

        # Calculate centered position
        x = px + (pw - width) // 2
        y = py + (ph - height) // 2

        # Ensure dialog is on screen
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        x = max(0, min(x, screen_width - width))
        y = max(0, min(y, screen_height - height))

        self.geometry(f"{width}x{height}+{x}+{y}")

    def _on_cancel(self) -> None:
        """Handle cancel/close action."""
        self._cancelled = True
        self.result = None
        self.destroy()

    def _on_confirm(self) -> None:
        """Handle confirm action. Override to set result."""
        self.destroy()

    def show(self) -> Optional[Any]:
        """
        Show the dialog and wait for it to close.

        Returns:
            The dialog result, or None if cancelled
        """
        # Wait for the window to be destroyed
        self.wait_window()
        return self.result

    @property
    def was_cancelled(self) -> bool:
        """Check if the dialog was cancelled."""
        return self._cancelled
