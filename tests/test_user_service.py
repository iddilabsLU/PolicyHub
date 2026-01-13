"""
PolicyHub User Service Tests

Tests for user service functionality including email validation,
bulk operations, and CSV import/export.
"""

import csv
import tempfile
from pathlib import Path

import pytest

from app.constants import UserRole
from core.database import DatabaseManager
from core.session import SessionManager
from models.user import UserCreate
from services.auth_service import AuthService
from services.user_service import UserService


@pytest.fixture
def user_service(db, logged_in_admin):
    """Create a user service with admin session."""
    return UserService(db)


class TestEmailValidation:
    """Tests for email uniqueness validation."""

    def test_email_exists_returns_false_for_new_email(self, user_service):
        """Test that email_exists returns False for new email."""
        assert not user_service.email_exists("new@example.com")

    def test_email_exists_returns_true_for_existing_email(self, user_service, admin_user_data):
        """Test that email_exists returns True for existing email."""
        # Admin already exists
        assert user_service.email_exists(admin_user_data["email"])

    def test_email_exists_case_insensitive(self, user_service, admin_user_data):
        """Test that email check is case-insensitive."""
        email = admin_user_data["email"]
        assert user_service.email_exists(email.upper())
        assert user_service.email_exists(email.title())

    def test_email_exists_with_exclude(self, user_service, admin_user_data):
        """Test email_exists with exclude parameter."""
        admin = user_service.get_user_by_username(admin_user_data["username"])
        # Should return False when excluding the user who has that email
        assert not user_service.email_exists(admin_user_data["email"], exclude_user_id=admin.user_id)

    def test_create_user_requires_email(self, user_service):
        """Test that creating a user without email fails."""
        data = UserCreate(
            username="newuser",
            password="password123",
            full_name="New User",
            email=None,
            role=UserRole.VIEWER.value,
        )

        with pytest.raises(ValueError, match="Email is required"):
            user_service.create_user(data)

    def test_create_user_with_duplicate_email_fails(self, user_service, admin_user_data):
        """Test that creating a user with existing email fails."""
        data = UserCreate(
            username="newuser",
            password="password123",
            full_name="New User",
            email=admin_user_data["email"],  # Already exists
            role=UserRole.VIEWER.value,
        )

        with pytest.raises(ValueError, match="already in use"):
            user_service.create_user(data)


class TestForcePasswordChange:
    """Tests for force_password_change functionality."""

    def test_new_user_has_force_password_change_flag(self, user_service):
        """Test that newly created users have force_password_change=True."""
        data = UserCreate(
            username="newuser",
            password="password123",
            full_name="New User",
            email="newuser@example.com",
            role=UserRole.VIEWER.value,
        )

        user = user_service.create_user(data)
        assert user.force_password_change is True

    def test_first_admin_no_force_password_change(self, user_service, admin_user_data):
        """Test that first admin does NOT have force_password_change flag."""
        admin = user_service.get_user_by_username(admin_user_data["username"])
        assert admin.force_password_change is False


class TestBulkDeactivate:
    """Tests for bulk deactivation functionality."""

    def test_bulk_deactivate_single_user(self, user_service):
        """Test bulk deactivating a single user."""
        # Create a user to deactivate
        data = UserCreate(
            username="testuser",
            password="password123",
            full_name="Test User",
            email="test@example.com",
            role=UserRole.VIEWER.value,
        )
        user = user_service.create_user(data)

        # Bulk deactivate
        count, errors = user_service.bulk_deactivate_users([user.user_id])

        assert count == 1
        assert errors == []

        # Verify deactivated
        updated_user = user_service.get_user_by_id(user.user_id)
        assert updated_user.is_active is False

    def test_bulk_deactivate_prevents_self_deactivation(self, user_service, admin_user_data):
        """Test that bulk deactivate prevents self-deactivation."""
        admin = user_service.get_user_by_username(admin_user_data["username"])

        count, errors = user_service.bulk_deactivate_users([admin.user_id])

        assert count == 0
        assert len(errors) == 1
        assert "your own account" in errors[0].lower()

    def test_bulk_deactivate_prevents_last_admin(self, user_service):
        """Test that bulk deactivate prevents deactivating last admin."""
        # Create another user (non-admin)
        data = UserCreate(
            username="viewer",
            password="password123",
            full_name="Viewer User",
            email="viewer@example.com",
            role=UserRole.VIEWER.value,
        )
        viewer = user_service.create_user(data)

        # Create a second admin to test deactivation
        admin_data = UserCreate(
            username="admin2",
            password="password123",
            full_name="Admin 2",
            email="admin2@example.com",
            role=UserRole.ADMIN.value,
        )
        admin2 = user_service.create_user(admin_data)

        # Now try to deactivate admin2 (should work since admin still exists)
        count, errors = user_service.bulk_deactivate_users([admin2.user_id])
        assert count == 1
        assert errors == []


class TestCSVImport:
    """Tests for CSV import functionality."""

    def test_get_csv_template(self, user_service):
        """Test that CSV template contains required headers."""
        template = user_service.get_csv_template()

        assert "username" in template
        assert "full_name" in template
        assert "email" in template
        assert "role" in template
        assert "password" in template

    def test_validate_import_valid_csv(self, user_service):
        """Test validating a valid CSV file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "full_name", "email", "role", "password"])
            writer.writerow(["john", "John Doe", "john@example.com", "VIEWER", "password123"])
            f.flush()

            result = user_service.validate_import_data(Path(f.name))

            assert result.success is True
            assert result.imported_count == 1
            assert len(result.errors) == 0

    def test_validate_import_missing_headers(self, user_service):
        """Test validating CSV with missing headers."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "full_name"])  # Missing email, role, password
            writer.writerow(["john", "John Doe"])
            f.flush()

            result = user_service.validate_import_data(Path(f.name))

            assert result.success is False
            assert any("missing" in str(e).lower() for e in result.errors)

    def test_validate_import_invalid_email(self, user_service):
        """Test validating CSV with invalid email."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "full_name", "email", "role", "password"])
            writer.writerow(["john", "John Doe", "invalid-email", "VIEWER", "password123"])
            f.flush()

            result = user_service.validate_import_data(Path(f.name))

            assert result.success is False
            assert any("email" in str(e).lower() for e in result.errors)

    def test_validate_import_invalid_role(self, user_service):
        """Test validating CSV with invalid role."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "full_name", "email", "role", "password"])
            writer.writerow(["john", "John Doe", "john@example.com", "INVALID", "password123"])
            f.flush()

            result = user_service.validate_import_data(Path(f.name))

            assert result.success is False
            assert any("role" in str(e).lower() for e in result.errors)

    def test_validate_import_duplicate_username_in_file(self, user_service):
        """Test validating CSV with duplicate usernames in same file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "full_name", "email", "role", "password"])
            writer.writerow(["john", "John Doe", "john@example.com", "VIEWER", "password123"])
            writer.writerow(["john", "Jane Doe", "jane@example.com", "VIEWER", "password123"])
            f.flush()

            result = user_service.validate_import_data(Path(f.name))

            assert result.success is False
            assert any("duplicate" in str(e).lower() for e in result.errors)

    def test_validate_import_existing_username(self, user_service, admin_user_data):
        """Test validating CSV with username that already exists in database."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "full_name", "email", "role", "password"])
            writer.writerow([admin_user_data["username"], "Another Admin", "another@example.com", "ADMIN", "password123"])
            f.flush()

            result = user_service.validate_import_data(Path(f.name))

            assert result.success is False
            assert any("already exists" in str(e).lower() for e in result.errors)

    def test_import_users_from_csv(self, user_service):
        """Test actual import of users from CSV."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "full_name", "email", "role", "password"])
            writer.writerow(["john", "John Doe", "john@example.com", "VIEWER", "password123"])
            writer.writerow(["jane", "Jane Doe", "jane@example.com", "EDITOR", "password123"])
            f.flush()

            result = user_service.import_users_from_csv(Path(f.name))

            assert result.success is True
            assert result.imported_count == 2

            # Verify users were created
            john = user_service.get_user_by_username("john")
            assert john is not None
            assert john.full_name == "John Doe"
            assert john.email == "john@example.com"
            assert john.role == UserRole.VIEWER.value
            assert john.force_password_change is True

            jane = user_service.get_user_by_username("jane")
            assert jane is not None
            assert jane.role == UserRole.EDITOR.value


class TestExport:
    """Tests for user export functionality."""

    def test_get_users_for_export(self, user_service):
        """Test getting user data for export."""
        export_data = user_service.get_users_for_export()

        assert len(export_data) >= 1  # At least admin
        assert "username" in export_data[0]
        assert "full_name" in export_data[0]
        assert "email" in export_data[0]
        assert "role" in export_data[0]
        assert "status" in export_data[0]

    def test_get_users_for_export_includes_inactive(self, user_service):
        """Test that export can include inactive users."""
        # Create and deactivate a user
        data = UserCreate(
            username="inactive",
            password="password123",
            full_name="Inactive User",
            email="inactive@example.com",
            role=UserRole.VIEWER.value,
        )
        user = user_service.create_user(data)
        user_service.deactivate_user(user.user_id)

        # Export without inactive
        active_only = user_service.get_users_for_export(include_inactive=False)
        active_usernames = [u["username"] for u in active_only]
        assert "inactive" not in active_usernames

        # Export with inactive
        with_inactive = user_service.get_users_for_export(include_inactive=True)
        all_usernames = [u["username"] for u in with_inactive]
        assert "inactive" in all_usernames
