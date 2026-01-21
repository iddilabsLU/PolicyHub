"""
PolicyHub IddiLabs View

Displays information about IddiLabs and the project philosophy.
"""

from typing import TYPE_CHECKING

import customtkinter as ctk

from app.theme import (
    COLORS,
    SPACING,
    TYPOGRAPHY,
    configure_card_style,
)
from views.base_view import BaseView

if TYPE_CHECKING:
    from app.application import PolicyHubApp


class IddiLabsView(BaseView):
    """
    IddiLabs branding and information view.

    Displays information about IddiLabs, the philosophy behind
    the project, and contact details.
    """

    def __init__(self, parent: ctk.CTkFrame, app: "PolicyHubApp"):
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
        # Scrollable container
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(
            fill="both",
            expand=True,
            padx=SPACING.WINDOW_PADDING,
            pady=SPACING.WINDOW_PADDING,
        )

        # Main title
        title = ctk.CTkLabel(
            scroll,
            text="Who is IddiLabs?",
            font=TYPOGRAPHY.window_title,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title.pack(anchor="w", pady=(0, SPACING.SECTION_SPACING))

        # Description card
        description_card = ctk.CTkFrame(scroll, fg_color=COLORS.CARD)
        configure_card_style(description_card, with_shadow=True)
        description_card.pack(fill="x", pady=(0, SPACING.SECTION_SPACING))

        card_content = ctk.CTkFrame(description_card, fg_color="transparent")
        card_content.pack(
            fill="x",
            padx=SPACING.CARD_PADDING,
            pady=SPACING.CARD_PADDING,
        )

        # Intro text
        intro = ctk.CTkLabel(
            card_content,
            text=(
                "I am a Risk Manager working in Luxembourg's financial sector with no coding background. "
                "I am using AI tools and applied expertise to build small software solutions, free and open to everyone.\n\n"
                "IddiLabs is not a software company, not a VAT registered individual, not a team of developers."
            ),
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
            wraplength=700,
            justify="left",
        )
        intro.pack(anchor="w", pady=(0, SPACING.SECTION_SPACING))

        # Why I'm doing this section
        self._create_section(
            card_content,
            "Why I'm doing this",
            (
                "I believe we're at the beginning of a shift where domain expertise becomes the differentiator "
                "as technical implementation becomes increasingly automated. A risk manager who effectively uses AI "
                "will be more valuable than one who does not."
            ),
        )

        # Why it's free section
        self._create_section(
            card_content,
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
            card_content,
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
        self._create_section(card_content, "Get in touch", contact_text)

    def _create_section(
        self,
        parent: ctk.CTkFrame,
        title: str,
        text: str,
    ) -> None:
        """
        Create a section with a title and text.

        Args:
            parent: Parent widget
            title: Section title
            text: Section text content
        """
        # Section title
        title_label = ctk.CTkLabel(
            parent,
            text=title,
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        title_label.pack(anchor="w", pady=(16, 4))

        # Section text
        text_label = ctk.CTkLabel(
            parent,
            text=text,
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
            wraplength=700,
            justify="left",
        )
        text_label.pack(anchor="w", pady=(0, SPACING.SECTION_SPACING))

    def on_show(self) -> None:
        """Called when the view becomes visible."""
        super().on_show()
        # Static content, no refresh needed
