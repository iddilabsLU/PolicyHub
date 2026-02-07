"""
PolicyHub Status Badge Component (PySide6)

A colored badge for displaying document or review status.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy

from app.constants import DocumentStatus, ReviewStatus
from app.theme import COLORS, TYPOGRAPHY


# Badge color variants: (background_color, text_color)
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
        DocumentStatus.ARCHIVED.value: "muted",
        # Review statuses
        ReviewStatus.OVERDUE.value: "danger",
        ReviewStatus.DUE_SOON.value: "warning",
        ReviewStatus.UPCOMING.value: "caution",
        ReviewStatus.ON_TRACK.value: "success",
    }
    return mapping.get(status, "muted")


class StatusBadge(QFrame):
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
        parent=None,
        text: str = "",
        variant: str = "muted",
    ):
        """
        Initialize the status badge.

        Args:
            parent: Parent widget
            text: Badge text
            variant: Color variant (success, warning, danger, caution, muted, primary)
        """
        super().__init__(parent)

        self._variant = variant

        # Set up layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(0)

        # Label
        self.label = QLabel(text)
        self.label.setFont(TYPOGRAPHY.small)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        # Size policy
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Apply variant styling
        self._apply_variant(variant)

    def _apply_variant(self, variant: str) -> None:
        """Apply styling for the given variant."""
        bg_color, text_color = BADGE_VARIANTS.get(
            variant, BADGE_VARIANTS["muted"]
        )

        self.setStyleSheet(f"""
            StatusBadge {{
                background-color: {bg_color};
                border-radius: 4px;
            }}
        """)
        self.label.setStyleSheet(f"color: {text_color}; background: transparent;")

    def set_text(self, text: str) -> None:
        """
        Update the badge text.

        Args:
            text: New text to display
        """
        self.label.setText(text)

    def set_variant(self, variant: str) -> None:
        """
        Update the badge variant/color.

        Args:
            variant: New color variant
        """
        self._variant = variant
        self._apply_variant(variant)

    @classmethod
    def from_status(
        cls,
        parent,
        status: str,
        display_text: Optional[str] = None,
    ) -> "StatusBadge":
        """
        Create a badge from a status value.

        Args:
            parent: Parent widget
            status: DocumentStatus or ReviewStatus value
            display_text: Override text (defaults to status display name)

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

        return cls(parent, text=display_text, variant=variant)

    @classmethod
    def from_review_status(
        cls, parent, review_status: ReviewStatus
    ) -> "StatusBadge":
        """
        Create a badge from a ReviewStatus enum.

        Args:
            parent: Parent widget
            review_status: ReviewStatus enum value

        Returns:
            StatusBadge instance
        """
        return cls.from_status(
            parent, review_status.value, review_status.display_name
        )

    @classmethod
    def from_document_status(
        cls, parent, doc_status: DocumentStatus
    ) -> "StatusBadge":
        """
        Create a badge from a DocumentStatus enum.

        Args:
            parent: Parent widget
            doc_status: DocumentStatus enum value

        Returns:
            StatusBadge instance
        """
        return cls.from_status(
            parent, doc_status.value, doc_status.display_name
        )
