"""
PolicyHub IddiLabs View (PySide6)

Displays information about IddiLabs and the project philosophy.
"""

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.theme import COLORS, SPACING, TYPOGRAPHY, style_card
from ui.views.base_view import BaseView

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class IddiLabsView(BaseView):
    """
    IddiLabs branding and information view.

    Displays information about IddiLabs, the philosophy behind
    the project, and contact details.
    """

    def __init__(self, parent: Optional[QWidget], app: "PolicyHubApp"):
        """
        Initialize the IddiLabs view.

        Args:
            parent: Parent widget
            app: Main application instance
        """
        super().__init__(parent, app)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the IddiLabs information UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        # Scrollable content
        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background-color: {COLORS.BACKGROUND};")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(
            SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING, SPACING.WINDOW_PADDING
        )
        scroll_layout.setSpacing(SPACING.SECTION_SPACING)

        # Main title
        title = QLabel("Who is IddiLabs?")
        title.setFont(TYPOGRAPHY.window_title)
        title.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        scroll_layout.addWidget(title)

        # Description card
        description_card = QFrame()
        style_card(description_card)
        card_layout = QVBoxLayout(description_card)
        card_layout.setContentsMargins(
            SPACING.CARD_PADDING, SPACING.CARD_PADDING,
            SPACING.CARD_PADDING, SPACING.CARD_PADDING
        )
        card_layout.setSpacing(0)

        # Intro text
        intro = QLabel(
            "I am a Risk Manager working in Luxembourg's financial sector with no coding background. "
            "I am using AI tools and applied expertise to build small software solutions, free and open to everyone.\n\n"
            "IddiLabs is not a software company, not a VAT registered individual, not a team of developers."
        )
        intro.setFont(TYPOGRAPHY.body)
        intro.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        intro.setWordWrap(True)
        card_layout.addWidget(intro)
        card_layout.addSpacing(SPACING.SECTION_SPACING)

        # Why I'm doing this section
        self._create_section(
            card_layout,
            "Why I'm doing this",
            (
                "I believe we're at the beginning of a shift where domain expertise becomes the differentiator "
                "as technical implementation becomes increasingly automated. A risk manager who effectively uses AI "
                "will be more valuable than one who does not."
            ),
        )

        # Why it's free section
        self._create_section(
            card_layout,
            "Why it's free",
            (
                "Lot of companies, especially small and medium enterprises, do not have budget for this type of tools and keep using excel sheets. "
                "This software is production ready and free to use, so that everyone can benefit from it.\n\n"
                "Additionally I'm doing it for my personal upskilling, career development and to prove what "
                "Subject Matter Experts and AI can bring to companies."
            ),
        )

        # Learn More section
        self._create_section(
            card_layout,
            "Learn More",
            (
                "In-depth guides about this software are available at iddi-labs.com, in the 'Blog'. "
                "Visit the 'Project' section for further tools."
            ),
        )

        # Get in touch section
        contact_text = (
            "Website: www.iddi-labs.com\n"
            "LinkedIn: IddiLabs\n"
            "Email: contact@iddi-labs.com\n\n"
            "Feel free to reach out for any questions or suggestions! Feedback is always welcome."
        )
        self._create_section(card_layout, "Get in touch", contact_text)

        scroll_layout.addWidget(description_card)
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def _create_section(
        self,
        parent_layout: QVBoxLayout,
        title: str,
        text: str,
    ) -> None:
        """
        Create a section with a title and text.

        Args:
            parent_layout: Parent layout to add widgets to
            title: Section title
            text: Section text content
        """
        # Separator line
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {COLORS.BORDER};")
        parent_layout.addSpacing(16)
        parent_layout.addWidget(separator)
        parent_layout.addSpacing(12)

        # Section title
        title_label = QLabel(title)
        title_label.setFont(TYPOGRAPHY.section_heading)
        title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        parent_layout.addWidget(title_label)
        parent_layout.addSpacing(4)

        # Section text
        text_label = QLabel(text)
        text_label.setFont(TYPOGRAPHY.body)
        text_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        text_label.setWordWrap(True)
        parent_layout.addWidget(text_label)

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        # Static content, no refresh needed
