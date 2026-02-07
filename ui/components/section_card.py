"""
SectionCard Component

Card wrapper for form sections with title and optional description.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.theme import COLORS, SPACING, TYPOGRAPHY


class SectionCard(QFrame):
    """
    A card wrapper for form sections with title and optional description.

    Usage:
        card = SectionCard(
            parent=self,
            title="Company Information",
            description="Enter your company details below."
        )
        card.add_content(my_form_widget)
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        title: str = "",
        description: Optional[str] = None,
    ):
        """
        Initialize the SectionCard.

        Args:
            parent: Parent widget
            title: Section title
            description: Optional description text below the title
        """
        super().__init__(parent)

        self._title = title
        self._description = description

        self.setProperty("sectionCard", True)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the card UI."""
        self.setStyleSheet(f"""
            QFrame[sectionCard="true"] {{
                background-color: {COLORS.CARD};
                border: none;
                border-radius: {SPACING.CORNER_RADIUS_LARGE}px;
            }}
        """)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
            SPACING.CARD_PADDING,
        )
        self._layout.setSpacing(12)

        # Header section (title + description)
        if self._title:
            header_frame = QFrame()
            header_frame.setStyleSheet("background: transparent; border: none;")
            header_layout = QVBoxLayout(header_frame)
            header_layout.setContentsMargins(0, 0, 0, 0)
            header_layout.setSpacing(4)

            # Title
            self.title_label = QLabel(self._title)
            self.title_label.setFont(TYPOGRAPHY.section_heading)
            self.title_label.setStyleSheet(f"""
                color: {COLORS.TEXT_PRIMARY};
                background: transparent;
            """)
            header_layout.addWidget(self.title_label)

            # Description
            if self._description:
                self.description_label = QLabel(self._description)
                self.description_label.setFont(TYPOGRAPHY.small)
                self.description_label.setWordWrap(True)
                self.description_label.setStyleSheet(f"""
                    color: {COLORS.TEXT_SECONDARY};
                    background: transparent;
                """)
                header_layout.addWidget(self.description_label)

            self._layout.addWidget(header_frame)

            # Separator line
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFixedHeight(1)
            separator.setStyleSheet(f"background-color: {COLORS.BORDER};")
            self._layout.addWidget(separator)

        # Content container
        self._content_container = QFrame()
        self._content_container.setStyleSheet("background: transparent; border: none;")
        self._content_layout = QVBoxLayout(self._content_container)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(12)
        self._layout.addWidget(self._content_container)

    def add_content(self, widget: QWidget) -> None:
        """
        Add a widget to the card's content area.

        Args:
            widget: Widget to add
        """
        self._content_layout.addWidget(widget)

    def add_layout(self, layout) -> None:
        """
        Add a layout to the card's content area.

        Args:
            layout: Layout to add
        """
        self._content_layout.addLayout(layout)

    def add_spacing(self, spacing: int) -> None:
        """
        Add spacing to the content area.

        Args:
            spacing: Pixels of spacing to add
        """
        self._content_layout.addSpacing(spacing)

    def add_stretch(self, stretch: int = 1) -> None:
        """
        Add stretch to the content area.

        Args:
            stretch: Stretch factor
        """
        self._content_layout.addStretch(stretch)

    def set_title(self, title: str) -> None:
        """Update the title."""
        self._title = title
        if hasattr(self, "title_label"):
            self.title_label.setText(title)

    def set_description(self, description: str) -> None:
        """Update the description."""
        self._description = description
        if hasattr(self, "description_label"):
            self.description_label.setText(description)

    @property
    def content_layout(self) -> QVBoxLayout:
        """Get the content layout for direct manipulation."""
        return self._content_layout
