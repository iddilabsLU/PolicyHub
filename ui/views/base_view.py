"""
PolicyHub Base View (PySide6)

Base class for all views in the application.
Provides common functionality and styling.
"""

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.theme import COLORS, SPACING, style_card

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class BaseView(QWidget):
    """
    Base class for all application views.

    Provides:
    - Common styling
    - Access to the main application
    - Lifecycle methods (on_show, on_hide)

    Usage:
        class MyView(BaseView):
            def __init__(self, parent, app):
                super().__init__(parent, app)
                self._build_ui()

            def _build_ui(self):
                layout = QVBoxLayout(self)
                # Add widgets...

            def on_show(self):
                super().on_show()
                self._refresh_data()
    """

    def __init__(self, parent: Optional[QWidget], app: "PolicyHubApp"):
        """
        Initialize the base view.

        Args:
            parent: Parent widget
            app: Main application instance
        """
        super().__init__(parent)
        self.app = app
        self._is_visible = False

        # Set background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.GlobalColor.transparent)
        self.setPalette(palette)

        # Style via stylesheet for background
        self.setStyleSheet(f"BaseView {{ background-color: {COLORS.BACKGROUND}; }}")

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

    Usage:
        class LoginView(CenteredView):
            def __init__(self, parent, app):
                super().__init__(parent, app, max_width=400)
                self._build_ui()

            def _build_ui(self):
                # Access self.content_frame to add widgets
                layout = QVBoxLayout(self.content_frame)
                layout.addWidget(QLabel("Login"))
    """

    def __init__(
        self,
        parent: Optional[QWidget],
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

        # Main layout for centering
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING,
                                       SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING)

        # Left spacer
        main_layout.addStretch(1)

        # Vertical container for centering
        v_container = QWidget()
        v_container.setMaximumWidth(max_width)
        v_container.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        v_layout = QVBoxLayout(v_container)
        v_layout.setContentsMargins(0, 0, 0, 0)

        # Top spacer
        v_layout.addStretch(1)

        # Content card frame
        self.content_frame = QFrame()
        self.content_frame.setObjectName("contentCard")
        self.content_frame.setMinimumWidth(max_width)
        self.content_frame.setMaximumWidth(max_width)
        style_card(self.content_frame)

        v_layout.addWidget(self.content_frame)

        # Bottom spacer
        v_layout.addStretch(1)

        main_layout.addWidget(v_container)

        # Right spacer
        main_layout.addStretch(1)

    def set_content_padding(self, padding: Optional[int] = None) -> None:
        """
        Set the padding inside the content frame.

        Args:
            padding: Padding in pixels (defaults to SPACING.CARD_PADDING)
        """
        if padding is None:
            padding = SPACING.CARD_PADDING

        # Get or create layout for content_frame
        layout = self.content_frame.layout()
        if layout:
            layout.setContentsMargins(padding, padding, padding, padding)


class ScrollableView(BaseView):
    """
    A view with a scrollable content area.

    Useful for long lists or forms that may overflow the window.

    Usage:
        class SettingsView(ScrollableView):
            def __init__(self, parent, app):
                super().__init__(parent, app)
                self._build_ui()

            def _build_ui(self):
                # Access self.content to add widgets
                layout = QVBoxLayout(self.content)
                # Add many widgets...
    """

    def __init__(self, parent: Optional[QWidget], app: "PolicyHubApp"):
        """
        Initialize the scrollable view.

        Args:
            parent: Parent widget
            app: Main application instance
        """
        super().__init__(parent, app)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Scrollable content widget
        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet(f"background-color: {COLORS.BACKGROUND};")
        self._scroll_area.setWidget(self._scroll_content)

        main_layout.addWidget(self._scroll_area)

    @property
    def content(self) -> QWidget:
        """Get the scrollable content widget."""
        return self._scroll_content

    @property
    def scroll_area(self) -> QScrollArea:
        """Get the scroll area widget."""
        return self._scroll_area

    def scroll_to_top(self) -> None:
        """Scroll to the top of the content."""
        self._scroll_area.verticalScrollBar().setValue(0)

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the content."""
        self._scroll_area.verticalScrollBar().setValue(
            self._scroll_area.verticalScrollBar().maximum()
        )
