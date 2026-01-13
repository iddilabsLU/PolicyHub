"""
PolicyHub User Service

Handles CRUD operations for user accounts.
"""

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.constants import UserRole
from core.database import DatabaseManager
from core.permissions import Permission, require_permission
from core.session import SessionManager
from models.user import User, UserCreate, UserUpdate
from services.auth_service import AuthService
from utils.dates import get_now
from utils.files import generate_uuid
from utils.validators import (
    validate_email,
    validate_full_name,
    validate_password,
    validate_username,
)

logger = logging.getLogger(__name__)


@dataclass
class ImportValidationError:
    """Represents a validation error during CSV import."""

    row: int
    field: str
    message: str

    def __str__(self) -> str:
        return f"Row {self.row}: {self.field} - {self.message}"


@dataclass
class ImportResult:
    """Result of a CSV import operation."""

    success: bool
    imported_count: int
    errors: List[ImportValidationError]

    @property
    def error_messages(self) -> List[str]:
        return [str(e) for e in self.errors]


class UserService:
    """
    Service for user management operations.

    All mutating operations require appropriate permissions.
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize the user service.

        Args:
            db: Database manager instance
        """
        self.db = db
        self.auth_service = AuthService(db)

    def get_all_users(self, include_inactive: bool = False) -> List[User]:
        """
        Get all users.

        Args:
            include_inactive: Whether to include inactive users

        Returns:
            List of User objects
        """
        if include_inactive:
            query = "SELECT * FROM users ORDER BY username"
            rows = self.db.fetch_all(query)
        else:
            query = "SELECT * FROM users WHERE is_active = 1 ORDER BY username"
            rows = self.db.fetch_all(query)

        return [User.from_row(row) for row in rows]

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: User's unique ID

        Returns:
            User object or None if not found
        """
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        )
        return User.from_row(row) if row else None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.

        Args:
            username: Username to search for

        Returns:
            User object or None if not found
        """
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        )
        return User.from_row(row) if row else None

    def username_exists(self, username: str, exclude_user_id: Optional[str] = None) -> bool:
        """
        Check if a username is already taken.

        Args:
            username: Username to check
            exclude_user_id: User ID to exclude from check (for updates)

        Returns:
            True if username exists
        """
        if exclude_user_id:
            row = self.db.fetch_one(
                "SELECT 1 FROM users WHERE username = ? AND user_id != ?",
                (username, exclude_user_id),
            )
        else:
            row = self.db.fetch_one(
                "SELECT 1 FROM users WHERE username = ?",
                (username,),
            )
        return row is not None

    def email_exists(self, email: str, exclude_user_id: Optional[str] = None) -> bool:
        """
        Check if an email is already taken.

        Args:
            email: Email to check
            exclude_user_id: User ID to exclude from check (for updates)

        Returns:
            True if email exists
        """
        if not email:
            return False

        email = email.strip().lower()

        if exclude_user_id:
            row = self.db.fetch_one(
                "SELECT 1 FROM users WHERE LOWER(email) = ? AND user_id != ?",
                (email, exclude_user_id),
            )
        else:
            row = self.db.fetch_one(
                "SELECT 1 FROM users WHERE LOWER(email) = ?",
                (email,),
            )
        return row is not None

    @require_permission(Permission.MANAGE_USERS)
    def create_user(self, data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            data: User creation data

        Returns:
            Created User object

        Raises:
            ValueError: If username or email already exists
            PermissionError: If current user lacks permission
        """
        # Check username availability
        if self.username_exists(data.username):
            raise ValueError(f"Username '{data.username}' is already taken")

        # Check email uniqueness (email is required)
        if not data.email:
            raise ValueError("Email is required")
        if self.email_exists(data.email):
            raise ValueError(f"Email '{data.email}' is already in use")

        user_id = generate_uuid()
        password_hash = self.auth_service.hash_password(data.password)
        now = get_now()
        created_by = SessionManager.get_instance().user_id

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (
                    user_id, username, password_hash, full_name, email,
                    role, is_active, force_password_change, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, 1, 1, ?, ?)
                """,
                (
                    user_id,
                    data.username,
                    password_hash,
                    data.full_name,
                    data.email,
                    data.role,
                    now,
                    created_by,
                ),
            )

        logger.info(f"User created: {data.username} by {created_by}")

        return self.get_user_by_id(user_id)

    @require_permission(Permission.MANAGE_USERS)
    def update_user(self, user_id: str, data: UserUpdate) -> Optional[User]:
        """
        Update a user's information.

        Args:
            user_id: User's ID
            data: Update data

        Returns:
            Updated User object or None if not found

        Raises:
            PermissionError: If current user lacks permission
        """
        user = self.get_user_by_id(user_id)
        if user is None:
            return None

        # Build update query
        updates = []
        params = []

        if data.full_name is not None:
            updates.append("full_name = ?")
            params.append(data.full_name)

        if data.email is not None:
            # Check email uniqueness
            if data.email and self.email_exists(data.email, exclude_user_id=user_id):
                raise ValueError(f"Email '{data.email}' is already in use")
            updates.append("email = ?")
            params.append(data.email)

        if data.role is not None:
            # Prevent removing the last admin
            if user.role == UserRole.ADMIN.value and data.role != UserRole.ADMIN.value:
                if self.count_admins() <= 1:
                    raise ValueError("Cannot change role: this is the last admin")
            updates.append("role = ?")
            params.append(data.role)

        if data.is_active is not None:
            # Prevent deactivating the last admin
            if user.role == UserRole.ADMIN.value and not data.is_active:
                if self.count_active_admins() <= 1:
                    raise ValueError("Cannot deactivate: this is the last active admin")
            updates.append("is_active = ?")
            params.append(1 if data.is_active else 0)

        if not updates:
            return user  # Nothing to update

        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"

        with self.db.get_connection() as conn:
            conn.execute(query, tuple(params))

        logger.info(f"User updated: {user.username}")
        return self.get_user_by_id(user_id)

    @require_permission(Permission.MANAGE_USERS)
    def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user account.

        Args:
            user_id: User's ID

        Returns:
            True if successful

        Raises:
            ValueError: If trying to deactivate the last admin
            PermissionError: If current user lacks permission
        """
        user = self.get_user_by_id(user_id)
        if user is None:
            return False

        # Prevent deactivating the last admin
        if user.role == UserRole.ADMIN.value:
            if self.count_active_admins() <= 1:
                raise ValueError("Cannot deactivate: this is the last active admin")

        # Prevent self-deactivation
        current_user_id = SessionManager.get_instance().user_id
        if user_id == current_user_id:
            raise ValueError("Cannot deactivate your own account")

        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE users SET is_active = 0 WHERE user_id = ?",
                (user_id,),
            )

        logger.info(f"User deactivated: {user.username}")
        return True

    @require_permission(Permission.MANAGE_USERS)
    def activate_user(self, user_id: str) -> bool:
        """
        Activate a user account.

        Args:
            user_id: User's ID

        Returns:
            True if successful

        Raises:
            PermissionError: If current user lacks permission
        """
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE users SET is_active = 1 WHERE user_id = ?",
                (user_id,),
            )
            if cursor.rowcount > 0:
                logger.info(f"User activated: {user_id}")
                return True
        return False

    @require_permission(Permission.MANAGE_USERS)
    def reset_user_password(self, user_id: str, new_password: str) -> bool:
        """
        Reset a user's password (admin function).

        Args:
            user_id: User's ID
            new_password: New password to set

        Returns:
            True if successful

        Raises:
            PermissionError: If current user lacks permission
        """
        return self.auth_service.reset_password(user_id, new_password)

    def count_users(self) -> int:
        """
        Count all users.

        Returns:
            Total user count
        """
        return self.db.count_users()

    def count_admins(self) -> int:
        """
        Count all admin users.

        Returns:
            Admin count
        """
        row = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM users WHERE role = ?",
            (UserRole.ADMIN.value,),
        )
        return row["count"] if row else 0

    def count_active_admins(self) -> int:
        """
        Count active admin users.

        Returns:
            Active admin count
        """
        row = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM users WHERE role = ? AND is_active = 1",
            (UserRole.ADMIN.value,),
        )
        return row["count"] if row else 0

    def get_users_by_role(self, role: str) -> List[User]:
        """
        Get all users with a specific role.

        Args:
            role: Role to filter by

        Returns:
            List of User objects
        """
        rows = self.db.fetch_all(
            "SELECT * FROM users WHERE role = ? AND is_active = 1 ORDER BY username",
            (role,),
        )
        return [User.from_row(row) for row in rows]

    @require_permission(Permission.MANAGE_USERS)
    def bulk_deactivate_users(self, user_ids: List[str]) -> tuple[int, List[str]]:
        """
        Deactivate multiple users at once.

        Args:
            user_ids: List of user IDs to deactivate

        Returns:
            Tuple of (count of deactivated users, list of error messages)

        Raises:
            PermissionError: If current user lacks permission
        """
        current_user_id = SessionManager.get_instance().user_id
        errors = []
        deactivated = 0

        for user_id in user_ids:
            # Skip self-deactivation
            if user_id == current_user_id:
                errors.append("Cannot deactivate your own account")
                continue

            user = self.get_user_by_id(user_id)
            if user is None:
                errors.append(f"User not found: {user_id}")
                continue

            # Check if this is the last active admin
            if user.role == UserRole.ADMIN.value:
                if self.count_active_admins() <= 1:
                    errors.append(f"Cannot deactivate {user.username}: last active admin")
                    continue

            # Deactivate the user
            with self.db.get_connection() as conn:
                conn.execute(
                    "UPDATE users SET is_active = 0 WHERE user_id = ?",
                    (user_id,),
                )

            logger.info(f"User deactivated (bulk): {user.username}")
            deactivated += 1

        return deactivated, errors

    def get_users_for_export(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Get user data formatted for export.

        Args:
            include_inactive: Whether to include inactive users

        Returns:
            List of dictionaries with user data for export
        """
        users = self.get_all_users(include_inactive=include_inactive)

        export_data = []
        for user in users:
            export_data.append({
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email or "",
                "role": user.role,
                "status": "Active" if user.is_active else "Inactive",
                "created_at": user.created_at[:10] if user.created_at else "",
                "last_login": user.last_login[:10] if user.last_login else "Never",
            })

        return export_data

    def get_csv_template(self) -> str:
        """
        Get the CSV template content for user import.

        Returns:
            CSV template string with headers and example
        """
        lines = [
            "username,full_name,email,role,password",
            "# Example row (remove this line before importing):",
            "# jsmith,John Smith,john.smith@example.com,VIEWER,TempPass123",
            "# Roles: ADMIN, EDITOR, VIEWER",
            "# Password must be at least 8 characters",
        ]
        return "\n".join(lines)

    def validate_import_data(self, file_path: Path) -> ImportResult:
        """
        Validate CSV import data without actually importing.

        Checks all rows and collects all errors before returning.

        Args:
            file_path: Path to the CSV file

        Returns:
            ImportResult with validation status and any errors
        """
        errors: List[ImportValidationError] = []
        valid_rows = 0

        # Track usernames and emails within the file for duplicates
        seen_usernames: set[str] = set()
        seen_emails: set[str] = set()

        valid_roles = {r.value for r in UserRole}

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)

                # Check headers
                required_headers = {"username", "full_name", "email", "role", "password"}
                if reader.fieldnames is None:
                    errors.append(ImportValidationError(0, "File", "CSV file is empty or has no headers"))
                    return ImportResult(success=False, imported_count=0, errors=errors)

                actual_headers = {h.strip().lower() for h in reader.fieldnames}
                missing_headers = required_headers - actual_headers

                if missing_headers:
                    errors.append(ImportValidationError(
                        0, "Headers", f"Missing required columns: {', '.join(missing_headers)}"
                    ))
                    return ImportResult(success=False, imported_count=0, errors=errors)

                for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                    # Skip comment lines
                    if row.get("username", "").startswith("#"):
                        continue

                    # Normalize keys to lowercase
                    row = {k.strip().lower(): v.strip() if v else "" for k, v in row.items()}

                    # Validate username
                    username = row.get("username", "")
                    is_valid, msg = validate_username(username)
                    if not is_valid:
                        errors.append(ImportValidationError(row_num, "username", msg))
                    elif username.lower() in seen_usernames:
                        errors.append(ImportValidationError(row_num, "username", "Duplicate username in file"))
                    elif self.username_exists(username):
                        errors.append(ImportValidationError(row_num, "username", "Username already exists"))
                    else:
                        seen_usernames.add(username.lower())

                    # Validate full name
                    full_name = row.get("full_name", "")
                    is_valid, msg = validate_full_name(full_name)
                    if not is_valid:
                        errors.append(ImportValidationError(row_num, "full_name", msg))

                    # Validate email (required and unique)
                    email = row.get("email", "")
                    if not email:
                        errors.append(ImportValidationError(row_num, "email", "Email is required"))
                    else:
                        is_valid, msg = validate_email(email)
                        if not is_valid:
                            errors.append(ImportValidationError(row_num, "email", msg))
                        elif email.lower() in seen_emails:
                            errors.append(ImportValidationError(row_num, "email", "Duplicate email in file"))
                        elif self.email_exists(email):
                            errors.append(ImportValidationError(row_num, "email", "Email already exists"))
                        else:
                            seen_emails.add(email.lower())

                    # Validate role
                    role = row.get("role", "").upper()
                    if not role:
                        errors.append(ImportValidationError(row_num, "role", "Role is required"))
                    elif role not in valid_roles:
                        errors.append(ImportValidationError(
                            row_num, "role", f"Invalid role. Must be one of: {', '.join(valid_roles)}"
                        ))

                    # Validate password
                    password = row.get("password", "")
                    is_valid, msg = validate_password(password)
                    if not is_valid:
                        errors.append(ImportValidationError(row_num, "password", msg))

                    # If no errors for this row, count it as valid
                    row_has_error = any(e.row == row_num for e in errors)
                    if not row_has_error:
                        valid_rows += 1

        except FileNotFoundError:
            errors.append(ImportValidationError(0, "File", "File not found"))
        except UnicodeDecodeError:
            errors.append(ImportValidationError(0, "File", "File encoding error. Please use UTF-8"))
        except csv.Error as e:
            errors.append(ImportValidationError(0, "File", f"CSV parsing error: {str(e)}"))
        except Exception as e:
            errors.append(ImportValidationError(0, "File", f"Unexpected error: {str(e)}"))

        return ImportResult(
            success=len(errors) == 0,
            imported_count=valid_rows,
            errors=errors,
        )

    @require_permission(Permission.MANAGE_USERS)
    def import_users_from_csv(self, file_path: Path) -> ImportResult:
        """
        Import users from a CSV file.

        Validates ALL rows first. Only imports if there are no errors.

        Args:
            file_path: Path to the CSV file

        Returns:
            ImportResult with import status and any errors

        Raises:
            PermissionError: If current user lacks permission
        """
        # First validate everything
        validation = self.validate_import_data(file_path)
        if not validation.success:
            return validation

        # Now actually import
        imported_count = 0
        created_by = SessionManager.get_instance().user_id
        now = get_now()

        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Skip comment lines
                if row.get("username", "").startswith("#"):
                    continue

                # Normalize keys
                row = {k.strip().lower(): v.strip() if v else "" for k, v in row.items()}

                user_id = generate_uuid()
                password_hash = self.auth_service.hash_password(row["password"])

                with self.db.get_connection() as conn:
                    conn.execute(
                        """
                        INSERT INTO users (
                            user_id, username, password_hash, full_name, email,
                            role, is_active, force_password_change, created_at, created_by
                        ) VALUES (?, ?, ?, ?, ?, ?, 1, 1, ?, ?)
                        """,
                        (
                            user_id,
                            row["username"],
                            password_hash,
                            row["full_name"],
                            row["email"],
                            row["role"].upper(),
                            now,
                            created_by,
                        ),
                    )

                logger.info(f"User imported: {row['username']} by {created_by}")
                imported_count += 1

        return ImportResult(
            success=True,
            imported_count=imported_count,
            errors=[],
        )
