"""
PolicyHub Status Badge Component

A colored badge for displaying document or review status.
"""

from typing import Optional

import customtkinter as ctk

from app.constants import DocumentStatus, ReviewStatus
from app.theme import COLORS, TYPOGRAPHY


# Badge color variants
BADGE_VARIANTS = {
    "success": (COLORS.SUCCESS_BG, COLORS.SUCCESS),
    "warning": (COLORS.WARNING_BG, COLORS.WARNING),
    "danger": (COLORS.DANGER_BG, COLORS.DANGER),
    "caution": ("#FEF3C7", COLORS.CAUTION),  # Light yellow background
    "muted": (COLORS.MUTED, COLORS.TEXT_SECONDARY),
    "primary": (COLORS.PRIMARY, COLORS.PRIMARY_FOREGROUND),
}


def get_status_variant(status: str) -> str:
    """
    Map a status value to a badge variant.

    Args:
        status: DocumentStatus or ReviewStatus value

    Returns:
        Badge variant name (success, warning, danger, caution, muted)
    """
    mapping = {
        # Document statuses
        DocumentStatus.ACTIVE.value: "success",
        DocumentStatus.DRAFT.value: "muted",
        DocumentStatus.UNDER_REVIEW.value: "caution",
        DocumentStatus.SUPERSEDED.value: "muted",
        DocumentStatus.ARCHIVED.value: "muted",
        # Review statuses
        ReviewStatus.OVERDUE.value: "danger",
        ReviewStatus.DUE_SOON.value: "warning",
        ReviewStatus.UPCOMING.value: "caution",
        ReviewStatus.ON_TRACK.value: "success",
    }
    return mapping.get(status, "muted")


class StatusBadge(ctk.CTkFrame):
    """
    A colored badge for displaying status.

    Usage:
        badge = StatusBadge(parent, text="Active", variant="success")
        badge = StatusBadge(parent, text="Overdue", variant="danger")

        # Or auto-detect variant from status
        badge = StatusBadge.from_status(parent, "ACTIVE")
    """

    def __init__(
        self,
        parent,
        text: str,
        variant: str = "muted",
        **kwargs
    ):
        """
        Initialize the status badge.

        Args:
            parent: Parent widget
            text: Badge text
            variant: Color variant (success, warning, danger, caution, muted, primary)
            **kwargs: Additional frame options
        """
        bg_color, text_color = BADGE_VARIANTS.get(
            variant, BADGE_VARIANTS["muted"]
        )

        super().__init__(
            parent,
            fg_color=bg_color,
            corner_radius=4,
            **kwargs
        )

        self.label = ctk.CTkLabel(
            self,
            text=text,
            font=TYPOGRAPHY.small,
            text_color=text_color,
        )
        self.label.pack(padx=8, pady=2)

    def set_text(self, text: str) -> None:
        """
        Update the badge text.

        Args:
            text: New text to display
        """
        self.label.configure(text=text)

    def set_variant(self, variant: str) -> None:
        """
        Update the badge variant/color.

        Args:
            variant: New color variant
        """
        bg_color, text_color = BADGE_VARIANTS.get(
            variant, BADGE_VARIANTS["muted"]
        )
        self.configure(fg_color=bg_color)
        self.label.configure(text_color=text_color)

    @classmethod
    def from_status(
        cls,
        parent,
        status: str,
        display_text: Optional[str] = None,
        **kwargs
    ) -> "StatusBadge":
        """
        Create a badge from a status value.

        Args:
            parent: Parent widget
            status: DocumentStatus or ReviewStatus value
            display_text: Override text (defaults to status display name)
            **kwargs: Additional frame options

        Returns:
            StatusBadge instance
        """
        variant = get_status_variant(status)

        # Get display name
        if display_text is None:
            try:
                display_text = DocumentStatus(status).display_name
            except ValueError:
                try:
                    display_text = ReviewStatus(status).display_name
                except ValueError:
                    display_text = status.replace("_", " ").title()

        return cls(parent, text=display_text, variant=variant, **kwargs)

    @classmethod
    def from_review_status(cls, parent, review_status: ReviewStatus, **kwargs) -> "StatusBadge":
        """
        Create a badge from a ReviewStatus enum.

        Args:
            parent: Parent widget
            review_status: ReviewStatus enum value
            **kwargs: Additional frame options

        Returns:
            StatusBadge instance
        """
        return cls.from_status(parent, review_status.value, review_status.display_name, **kwargs)

    @classmethod
    def from_document_status(cls, parent, doc_status: DocumentStatus, **kwargs) -> "StatusBadge":
        """
        Create a badge from a DocumentStatus enum.

        Args:
            parent: Parent widget
            doc_status: DocumentStatus enum value
            **kwargs: Additional frame options

        Returns:
            StatusBadge instance
        """
        return cls.from_status(parent, doc_status.value, doc_status.display_name, **kwargs)
