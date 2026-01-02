"""
PolicyHub Date Utilities

Helper functions for date formatting, parsing, and calculations.
All dates are stored internally as ISO 8601 strings (YYYY-MM-DD).
"""

from datetime import date, datetime, timedelta
from typing import Optional

from app.constants import ReviewFrequency, ReviewStatus


def get_today() -> str:
    """
    Get today's date as an ISO 8601 string.

    Returns:
        Today's date in YYYY-MM-DD format
    """
    return date.today().isoformat()


def get_now() -> str:
    """
    Get the current datetime as an ISO 8601 string.

    Returns:
        Current datetime in YYYY-MM-DDTHH:MM:SS format
    """
    return datetime.now().isoformat(timespec="seconds")


def format_date(iso_date: str, format_str: str = "DD/MM/YYYY") -> str:
    """
    Format an ISO 8601 date string for display.

    Args:
        iso_date: Date in YYYY-MM-DD format
        format_str: Display format (DD/MM/YYYY or MM/DD/YYYY)

    Returns:
        Formatted date string, or the original string if parsing fails
    """
    if not iso_date:
        return ""

    try:
        # Handle both date-only and datetime strings
        if "T" in iso_date:
            dt = datetime.fromisoformat(iso_date)
        else:
            dt = datetime.strptime(iso_date, "%Y-%m-%d")

        if format_str == "DD/MM/YYYY":
            return dt.strftime("%d/%m/%Y")
        elif format_str == "MM/DD/YYYY":
            return dt.strftime("%m/%d/%Y")
        else:
            return dt.strftime("%d/%m/%Y")

    except ValueError:
        return iso_date


def format_datetime(iso_datetime: str) -> str:
    """
    Format an ISO 8601 datetime string for display.

    Args:
        iso_datetime: Datetime in YYYY-MM-DDTHH:MM:SS format

    Returns:
        Formatted datetime string (e.g., "15/01/2025 14:32")
    """
    if not iso_datetime:
        return ""

    try:
        dt = datetime.fromisoformat(iso_datetime)
        return dt.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return iso_datetime


def parse_display_date(display_date: str, format_str: str = "DD/MM/YYYY") -> Optional[str]:
    """
    Parse a display date string to ISO 8601 format.

    Args:
        display_date: Date in display format (e.g., "15/01/2025")
        format_str: The format of the display date

    Returns:
        Date in YYYY-MM-DD format, or None if parsing fails
    """
    if not display_date:
        return None

    try:
        if format_str == "DD/MM/YYYY":
            dt = datetime.strptime(display_date, "%d/%m/%Y")
        elif format_str == "MM/DD/YYYY":
            dt = datetime.strptime(display_date, "%m/%d/%Y")
        else:
            dt = datetime.strptime(display_date, "%d/%m/%Y")

        return dt.strftime("%Y-%m-%d")

    except ValueError:
        return None


def calculate_next_review(
    last_review_date: str,
    frequency: str | ReviewFrequency,
) -> Optional[str]:
    """
    Calculate the next review date based on the last review and frequency.

    Args:
        last_review_date: Last review date in YYYY-MM-DD format
        frequency: Review frequency (ANNUAL, SEMI_ANNUAL, QUARTERLY, AD_HOC)

    Returns:
        Next review date in YYYY-MM-DD format, or None for AD_HOC
    """
    if not last_review_date:
        return None

    # Convert string to enum if needed
    if isinstance(frequency, str):
        try:
            frequency = ReviewFrequency(frequency)
        except ValueError:
            return None

    # AD_HOC has no automatic calculation
    if frequency == ReviewFrequency.AD_HOC:
        return None

    days = frequency.days
    if days is None:
        return None

    try:
        last_date = datetime.strptime(last_review_date, "%Y-%m-%d").date()
        next_date = last_date + timedelta(days=days)
        return next_date.isoformat()
    except ValueError:
        return None


def days_until(target_date: str) -> Optional[int]:
    """
    Calculate the number of days until a target date.

    Args:
        target_date: Target date in YYYY-MM-DD format

    Returns:
        Number of days (negative if past), or None if parsing fails
    """
    if not target_date:
        return None

    try:
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
        today = date.today()
        delta = target - today
        return delta.days
    except ValueError:
        return None


def get_review_status(
    next_review_date: str,
    warning_days: int = 30,
    upcoming_days: int = 90,
) -> ReviewStatus:
    """
    Determine the review status based on the next review date.

    Args:
        next_review_date: Next review date in YYYY-MM-DD format
        warning_days: Days threshold for "Due Soon" status
        upcoming_days: Days threshold for "Upcoming" status

    Returns:
        ReviewStatus enum value
    """
    if not next_review_date:
        return ReviewStatus.ON_TRACK

    days = days_until(next_review_date)

    if days is None:
        return ReviewStatus.ON_TRACK

    if days < 0:
        return ReviewStatus.OVERDUE
    elif days <= warning_days:
        return ReviewStatus.DUE_SOON
    elif days <= upcoming_days:
        return ReviewStatus.UPCOMING
    else:
        return ReviewStatus.ON_TRACK


def is_overdue(next_review_date: str) -> bool:
    """
    Check if a document is overdue for review.

    Args:
        next_review_date: Next review date in YYYY-MM-DD format

    Returns:
        True if the date has passed
    """
    days = days_until(next_review_date)
    return days is not None and days < 0


def add_days(date_str: str, days: int) -> Optional[str]:
    """
    Add a number of days to a date.

    Args:
        date_str: Date in YYYY-MM-DD format
        days: Number of days to add (can be negative)

    Returns:
        New date in YYYY-MM-DD format, or None if parsing fails
    """
    if not date_str:
        return None

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").date()
        new_date = dt + timedelta(days=days)
        return new_date.isoformat()
    except ValueError:
        return None


def get_month_name(month: int) -> str:
    """
    Get the name of a month.

    Args:
        month: Month number (1-12)

    Returns:
        Month name (e.g., "January")
    """
    months = [
        "January", "February", "March", "April",
        "May", "June", "July", "August",
        "September", "October", "November", "December"
    ]
    if 1 <= month <= 12:
        return months[month - 1]
    return ""


def format_relative_date(iso_date: str) -> str:
    """
    Format a date relative to today (e.g., "3 days ago", "in 5 days").

    Args:
        iso_date: Date in YYYY-MM-DD format

    Returns:
        Relative date string
    """
    days = days_until(iso_date)

    if days is None:
        return format_date(iso_date)

    if days == 0:
        return "Today"
    elif days == 1:
        return "Tomorrow"
    elif days == -1:
        return "Yesterday"
    elif days > 1:
        return f"In {days} days"
    else:
        return f"{abs(days)} days ago"
