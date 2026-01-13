"""
PolicyHub Application Constants

Defines all enums, static values, and configuration constants.
Based on PRD Section 7: Document Taxonomy.
"""

from enum import Enum
from typing import Dict, List, Tuple


class DocumentType(str, Enum):
    """Types of documents that can be managed."""

    POLICY = "POLICY"
    PROCEDURE = "PROCEDURE"
    MANUAL = "MANUAL"
    HR_OTHERS = "HR_OTHERS"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        names = {
            "POLICY": "Policy",
            "PROCEDURE": "Procedure",
            "MANUAL": "Manual",
            "HR_OTHERS": "HR Others",
        }
        return names[self.value]

    @property
    def code_prefix(self) -> str:
        """Reference code prefix for this document type."""
        prefixes = {
            "POLICY": "POL",
            "PROCEDURE": "PROC",
            "MANUAL": "MAN",
            "HR_OTHERS": "HR",
        }
        return prefixes[self.value]


class DocumentStatus(str, Enum):
    """Status of a document in its lifecycle."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        names = {
            "DRAFT": "Draft",
            "ACTIVE": "Active",
            "UNDER_REVIEW": "Under Review",
            "SUPERSEDED": "Superseded",
            "ARCHIVED": "Archived",
        }
        return names[self.value]


class ReviewFrequency(str, Enum):
    """How often a document should be reviewed."""

    ANNUAL = "ANNUAL"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    QUARTERLY = "QUARTERLY"
    AD_HOC = "AD_HOC"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        names = {
            "ANNUAL": "Annual",
            "SEMI_ANNUAL": "Semi-Annual",
            "QUARTERLY": "Quarterly",
            "AD_HOC": "Ad Hoc",
        }
        return names[self.value]

    @property
    def days(self) -> int | None:
        """Number of days between reviews (None for Ad Hoc)."""
        days_map = {
            "ANNUAL": 365,
            "SEMI_ANNUAL": 182,
            "QUARTERLY": 91,
            "AD_HOC": None,
        }
        return days_map[self.value]


class UserRole(str, Enum):
    """User roles for access control."""

    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        return self.value.title()

    @property
    def description(self) -> str:
        """Role description for UI."""
        descriptions = {
            "ADMIN": "Full access + user management",
            "EDITOR": "Add/edit documents",
            "VIEWER": "Read only",
        }
        return descriptions[self.value]


class LinkType(str, Enum):
    """Types of relationships between documents."""

    IMPLEMENTS = "IMPLEMENTS"
    REFERENCES = "REFERENCES"
    SUPERSEDES = "SUPERSEDES"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        return self.value.title()


class ReviewStatus(str, Enum):
    """Review status based on next review date."""

    OVERDUE = "OVERDUE"
    DUE_SOON = "DUE_SOON"  # < 30 days
    UPCOMING = "UPCOMING"  # < 90 days
    ON_TRACK = "ON_TRACK"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        names = {
            "OVERDUE": "Overdue",
            "DUE_SOON": "Due Soon",
            "UPCOMING": "Upcoming",
            "ON_TRACK": "On Track",
        }
        return names[self.value]


class HistoryAction(str, Enum):
    """Types of actions recorded in document history."""

    CREATED = "CREATED"
    UPDATED = "UPDATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    REVIEWED = "REVIEWED"
    ATTACHMENT_ADDED = "ATTACHMENT_ADDED"
    ATTACHMENT_REMOVED = "ATTACHMENT_REMOVED"
    LINK_ADDED = "LINK_ADDED"
    LINK_REMOVED = "LINK_REMOVED"


# Default categories (from PRD Section 7.2)
DEFAULT_CATEGORIES: List[Tuple[str, str, int]] = [
    ("AML", "Anti-Money Laundering & CFT", 1),
    ("GOV", "Corporate Governance", 2),
    ("OPS", "Operations", 3),
    ("ACC", "Accounting & Valuation", 4),
    ("IT", "Information Technology & Security", 5),
    ("HR", "Human Resources", 6),
    ("DP", "Data Protection / GDPR", 7),
    ("BCP", "Business Continuity", 8),
    ("RISK", "Risk Management", 9),
    ("REG", "Regulatory & Compliance", 10),
    ("OTHER", "Other", 99),
]

# Default settings (from PRD Section 8.8)
DEFAULT_SETTINGS: Dict[str, str] = {
    "company_name": "",
    "warning_threshold_days": "30",
    "upcoming_threshold_days": "90",
    "date_format": "DD/MM/YYYY",
    "default_review_frequency": "ANNUAL",
}

# File upload constraints
MAX_FILE_SIZE_MB: int = 25
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS: List[str] = [
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".txt",
]

ALLOWED_MIME_TYPES: Dict[str, str] = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain",
}

# Application info
APP_NAME: str = "PolicyHub"
APP_VERSION: str = "1.0.0"
APP_DESCRIPTION: str = "Policy & Procedure Lifecycle Manager"

# Database
DATABASE_FILENAME: str = "policyhub.db"
DATABASE_TIMEOUT: float = 30.0
DATABASE_BUSY_TIMEOUT: int = 30000

# Local folders
LOCAL_APP_FOLDER: str = "PolicyHub"
LOCAL_CONFIG_FILE: str = "config.json"
LOCAL_LOGS_FOLDER: str = "logs"

# Shared folder structure
SHARED_DATA_FOLDER: str = "data"
SHARED_ATTACHMENTS_FOLDER: str = "attachments"
SHARED_EXPORTS_FOLDER: str = "exports"

# Password requirements
MIN_PASSWORD_LENGTH: int = 8

# Pagination
DEFAULT_PAGE_SIZE: int = 25
PAGE_SIZE_OPTIONS: List[int] = [10, 25, 50, 100]

# Review thresholds (days)
WARNING_THRESHOLD_DAYS: int = 30
UPCOMING_THRESHOLD_DAYS: int = 90
