"""
PolicyHub File Utilities

Helper functions for file path handling, particularly for the shared folder
structure and attachment management.
"""

import logging
import os
import re
import uuid
from pathlib import Path
from typing import Optional

from app.constants import (
    DATABASE_FILENAME,
    SHARED_ATTACHMENTS_FOLDER,
    SHARED_DATA_FOLDER,
    SHARED_EXPORTS_FOLDER,
)
from core.config import ConfigManager

logger = logging.getLogger(__name__)


def get_shared_folder_path() -> Optional[Path]:
    """
    Get the configured shared folder path.

    Returns:
        Path to the shared folder, or None if not configured
    """
    config_manager = ConfigManager.get_instance()
    return config_manager.get_shared_folder_path()


def get_database_path() -> Optional[Path]:
    """
    Get the path to the SQLite database file.

    Returns:
        Path to policyhub.db in the shared folder's data/ directory,
        or None if shared folder not configured
    """
    shared_folder = get_shared_folder_path()
    if shared_folder is None:
        return None
    return shared_folder / SHARED_DATA_FOLDER / DATABASE_FILENAME


def get_attachments_path() -> Optional[Path]:
    """
    Get the path to the attachments folder.

    Returns:
        Path to the attachments/ directory in the shared folder,
        or None if shared folder not configured
    """
    shared_folder = get_shared_folder_path()
    if shared_folder is None:
        return None
    return shared_folder / SHARED_ATTACHMENTS_FOLDER


def get_exports_path() -> Optional[Path]:
    """
    Get the path to the exports folder.

    Returns:
        Path to the exports/ directory in the shared folder,
        or None if shared folder not configured
    """
    shared_folder = get_shared_folder_path()
    if shared_folder is None:
        return None
    return shared_folder / SHARED_EXPORTS_FOLDER


def ensure_shared_folder_structure(shared_folder: Path) -> bool:
    """
    Create the required folder structure in the shared folder.

    Creates:
    - data/
    - attachments/
    - exports/

    Args:
        shared_folder: Path to the shared folder root

    Returns:
        True if successful, False otherwise
    """
    try:
        (shared_folder / SHARED_DATA_FOLDER).mkdir(parents=True, exist_ok=True)
        (shared_folder / SHARED_ATTACHMENTS_FOLDER).mkdir(parents=True, exist_ok=True)
        (shared_folder / SHARED_EXPORTS_FOLDER).mkdir(parents=True, exist_ok=True)
        logger.info(f"Shared folder structure created at: {shared_folder}")
        return True
    except OSError as e:
        logger.error(f"Failed to create shared folder structure: {e}")
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to remove invalid characters.

    Removes characters that are not allowed in Windows filenames:
    < > : " / \\ | ? *

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for Windows file systems
    """
    # Remove invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, "_", filename)

    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(" .")

    # Ensure filename is not empty
    if not sanitized:
        sanitized = "unnamed"

    # Limit length (Windows max is 255, but we use 200 to be safe)
    max_length = 200
    if len(sanitized) > max_length:
        name, ext = os.path.splitext(sanitized)
        name = name[: max_length - len(ext)]
        sanitized = name + ext

    return sanitized


def generate_attachment_path(doc_ref: str, filename: str, version: str) -> str:
    """
    Generate the relative path for storing an attachment.

    Structure: {doc_ref}/{doc_ref}_v{version}_{timestamp}_{original_name}

    This ensures each file is unique and previous versions are preserved.

    Args:
        doc_ref: Document reference code (e.g., POL-AML-001)
        filename: Original filename
        version: Version label

    Returns:
        Relative path for the attachment
    """
    from datetime import datetime

    sanitized_filename = sanitize_filename(filename)

    # Create a unique filename with version, timestamp, and original name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    versioned_name = f"{doc_ref}_v{version}_{timestamp}_{sanitized_filename}"

    return f"{doc_ref}/{versioned_name}"


def get_attachment_absolute_path(relative_path: str) -> Optional[Path]:
    """
    Convert a relative attachment path to an absolute path.

    Args:
        relative_path: Relative path from the attachments folder

    Returns:
        Absolute path to the attachment, or None if attachments folder not configured
    """
    attachments_folder = get_attachments_path()
    if attachments_folder is None:
        return None
    return attachments_folder / relative_path


def generate_uuid() -> str:
    """
    Generate a new UUID for database records.

    Returns:
        UUID string (e.g., "550e8400-e29b-41d4-a716-446655440000")
    """
    return str(uuid.uuid4())


def get_file_size(file_path: Path) -> int:
    """
    Get the size of a file in bytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in bytes
    """
    return file_path.stat().st_size


def format_file_size(size_bytes: int) -> str:
    """
    Format a file size in bytes to a human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "2.5 MB", "150 KB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def get_file_extension(filename: str) -> str:
    """
    Get the lowercase file extension.

    Args:
        filename: Filename to extract extension from

    Returns:
        Lowercase extension including dot (e.g., ".pdf")
    """
    _, ext = os.path.splitext(filename)
    return ext.lower()


def is_valid_extension(filename: str, allowed_extensions: list[str]) -> bool:
    """
    Check if a file has an allowed extension.

    Args:
        filename: Filename to check
        allowed_extensions: List of allowed extensions (e.g., [".pdf", ".docx"])

    Returns:
        True if extension is allowed
    """
    ext = get_file_extension(filename)
    return ext in allowed_extensions


def copy_file(source: Path, destination: Path) -> bool:
    """
    Copy a file to a destination, creating directories as needed.

    Args:
        source: Source file path
        destination: Destination file path

    Returns:
        True if successful
    """
    import shutil

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        logger.info(f"File copied: {source} -> {destination}")
        return True
    except OSError as e:
        logger.error(f"Failed to copy file: {e}")
        return False


def delete_file(file_path: Path) -> bool:
    """
    Delete a file if it exists.

    Args:
        file_path: Path to the file to delete

    Returns:
        True if deleted or didn't exist, False if deletion failed
    """
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"File deleted: {file_path}")
        return True
    except OSError as e:
        logger.error(f"Failed to delete file: {e}")
        return False
