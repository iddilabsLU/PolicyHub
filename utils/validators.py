"""
PolicyHub Input Validators

Validation functions for user input in forms and dialogs.
"""

import re
from typing import Tuple

from app.constants import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    MIN_PASSWORD_LENGTH,
)


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate a password meets requirements.

    Requirements:
    - Minimum 8 characters

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"

    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"

    return True, ""


def validate_passwords_match(password: str, confirm_password: str) -> Tuple[bool, str]:
    """
    Validate that password and confirmation match.

    Args:
        password: The password
        confirm_password: The confirmation password

    Returns:
        Tuple of (is_valid, error_message)
    """
    if password != confirm_password:
        return False, "Passwords do not match"

    return True, ""


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate a username.

    Requirements:
    - Not empty
    - 3-50 characters
    - Only alphanumeric, underscore, and hyphen
    - Must start with a letter

    Args:
        username: Username to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"

    username = username.strip()

    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 50:
        return False, "Username must be less than 50 characters"

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", username):
        return False, "Username must start with a letter and contain only letters, numbers, underscores, and hyphens"

    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate an email address.

    Args:
        email: Email to validate (can be empty)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return True, ""  # Email is optional

    email = email.strip()

    # Basic email pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(pattern, email):
        return False, "Invalid email format"

    if len(email) > 254:
        return False, "Email address is too long"

    return True, ""


def validate_full_name(name: str) -> Tuple[bool, str]:
    """
    Validate a full name.

    Requirements:
    - Not empty
    - 2-100 characters

    Args:
        name: Full name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Full name is required"

    name = name.strip()

    if len(name) < 2:
        return False, "Full name must be at least 2 characters"

    if len(name) > 100:
        return False, "Full name must be less than 100 characters"

    return True, ""


def validate_doc_ref(ref: str) -> Tuple[bool, str]:
    """
    Validate a document reference code.

    Format: TYPE-CATEGORY-NUMBER (e.g., POL-AML-001)

    Requirements:
    - Not empty
    - Matches expected format
    - 5-30 characters

    Args:
        ref: Document reference to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not ref:
        return False, "Document reference is required"

    ref = ref.strip().upper()

    if len(ref) < 5:
        return False, "Document reference is too short"

    if len(ref) > 30:
        return False, "Document reference is too long"

    # Pattern: PREFIX-CATEGORY-NUMBER
    pattern = r"^[A-Z]{2,6}-[A-Z]{2,6}-\d{1,4}$"

    if not re.match(pattern, ref):
        return False, "Invalid reference format. Use: TYPE-CATEGORY-NUMBER (e.g., POL-AML-001)"

    return True, ""


def validate_document_title(title: str) -> Tuple[bool, str]:
    """
    Validate a document title.

    Requirements:
    - Not empty
    - 5-200 characters

    Args:
        title: Document title to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not title:
        return False, "Document title is required"

    title = title.strip()

    if len(title) < 5:
        return False, "Document title must be at least 5 characters"

    if len(title) > 200:
        return False, "Document title must be less than 200 characters"

    return True, ""


def validate_version(version: str) -> Tuple[bool, str]:
    """
    Validate a document version string.

    Format: Major.Minor (e.g., 1.0, 2.5, 10.1)

    Args:
        version: Version string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not version:
        return False, "Version is required"

    version = version.strip()

    # Pattern: one or more digits, dot, one or more digits
    pattern = r"^\d+\.\d+$"

    if not re.match(pattern, version):
        return False, "Invalid version format. Use: X.Y (e.g., 1.0, 2.5)"

    return True, ""


def validate_file_upload(
    filename: str,
    file_size: int,
    allowed_extensions: list[str] | None = None,
    max_size: int | None = None,
) -> Tuple[bool, str]:
    """
    Validate a file for upload.

    Args:
        filename: Name of the file
        file_size: Size of the file in bytes
        allowed_extensions: List of allowed extensions (defaults to ALLOWED_EXTENSIONS)
        max_size: Maximum file size in bytes (defaults to MAX_FILE_SIZE_BYTES)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS

    if max_size is None:
        max_size = MAX_FILE_SIZE_BYTES

    if not filename:
        return False, "Filename is required"

    # Check extension
    ext = filename.lower()
    ext = ext[ext.rfind("."):] if "." in ext else ""

    if ext not in allowed_extensions:
        allowed = ", ".join(allowed_extensions)
        return False, f"File type not allowed. Allowed types: {allowed}"

    # Check size
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        return False, f"File size exceeds maximum of {max_mb:.0f} MB"

    if file_size == 0:
        return False, "File is empty"

    return True, ""


def validate_required(value: str, field_name: str) -> Tuple[bool, str]:
    """
    Validate that a required field is not empty.

    Args:
        value: Value to validate
        field_name: Name of the field for error message

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value or not value.strip():
        return False, f"{field_name} is required"

    return True, ""


def validate_date_format(date_str: str) -> Tuple[bool, str]:
    """
    Validate a date string in ISO 8601 format (YYYY-MM-DD).

    Args:
        date_str: Date string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not date_str:
        return False, "Date is required"

    pattern = r"^\d{4}-\d{2}-\d{2}$"

    if not re.match(pattern, date_str):
        return False, "Invalid date format. Use: YYYY-MM-DD"

    # Validate the date is actually valid
    try:
        year, month, day = map(int, date_str.split("-"))

        if month < 1 or month > 12:
            return False, "Invalid month"

        if day < 1 or day > 31:
            return False, "Invalid day"

        # Basic validation for days in month
        if month in [4, 6, 9, 11] and day > 30:
            return False, "Invalid day for this month"

        if month == 2:
            # Leap year check
            is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
            max_day = 29 if is_leap else 28
            if day > max_day:
                return False, "Invalid day for February"

    except ValueError:
        return False, "Invalid date"

    return True, ""
