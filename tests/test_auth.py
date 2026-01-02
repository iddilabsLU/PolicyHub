"""
PolicyHub Authentication Tests

Tests for the authentication service.
"""

import pytest

from app.constants import UserRole
from core.database import DatabaseManager
from core.session import SessionManager
from services.auth_service import AuthService


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = AuthService.hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt prefix
        assert len(hashed) == 60  # bcrypt hash length

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "testpassword123"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed)

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "testpassword123"
        hashed = AuthService.hash_password(password)

        assert not AuthService.verify_password("wrongpassword", hashed)

    def test_hash_uniqueness(self):
        """Test that same password produces different hashes."""
        password = "testpassword123"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)

        # Hashes should be different (different salts)
        assert hash1 != hash2

        # But both should verify correctly
        assert AuthService.verify_password(password, hash1)
        assert AuthService.verify_password(password, hash2)


class TestAuthService:
    """Tests for AuthService class."""

    def test_create_first_admin(self, db: DatabaseManager, admin_user_data: dict):
        """Test creating the first admin user."""
        auth = AuthService(db)

        user = auth.create_first_admin(
            username=admin_user_data["username"],
            password=admin_user_data["password"],
            full_name=admin_user_data["full_name"],
            email=admin_user_data["email"],
        )

        assert user is not None
        assert user.username == admin_user_data["username"]
        assert user.full_name == admin_user_data["full_name"]
        assert user.email == admin_user_data["email"]
        assert user.role == UserRole.ADMIN.value
        assert user.is_active

    def test_create_first_admin_fails_if_users_exist(
        self, db: DatabaseManager, admin_user_data: dict
    ):
        """Test that creating first admin fails if users already exist."""
        auth = AuthService(db)

        # Create first admin
        auth.create_first_admin(
            username=admin_user_data["username"],
            password=admin_user_data["password"],
            full_name=admin_user_data["full_name"],
        )

        # Try to create another
        with pytest.raises(RuntimeError, match="users already exist"):
            auth.create_first_admin(
                username="another",
                password="password123",
                full_name="Another User",
            )

    def test_authenticate_success(self, db: DatabaseManager, admin_user_data: dict):
        """Test successful authentication."""
        auth = AuthService(db)

        # Create user
        auth.create_first_admin(
            username=admin_user_data["username"],
            password=admin_user_data["password"],
            full_name=admin_user_data["full_name"],
        )

        # Authenticate
        user = auth.authenticate(
            admin_user_data["username"],
            admin_user_data["password"],
        )

        assert user is not None
        assert user.username == admin_user_data["username"]

    def test_authenticate_wrong_password(
        self, db: DatabaseManager, admin_user_data: dict
    ):
        """Test authentication with wrong password."""
        auth = AuthService(db)

        # Create user
        auth.create_first_admin(
            username=admin_user_data["username"],
            password=admin_user_data["password"],
            full_name=admin_user_data["full_name"],
        )

        # Authenticate with wrong password
        user = auth.authenticate(admin_user_data["username"], "wrongpassword")

        assert user is None

    def test_authenticate_nonexistent_user(self, db: DatabaseManager):
        """Test authentication with nonexistent user."""
        auth = AuthService(db)

        user = auth.authenticate("nonexistent", "password")

        assert user is None

    def test_login_creates_session(
        self, db: DatabaseManager, admin_user_data: dict, session_manager: SessionManager
    ):
        """Test that login creates a session."""
        auth = AuthService(db)

        # Create user
        auth.create_first_admin(
            username=admin_user_data["username"],
            password=admin_user_data["password"],
            full_name=admin_user_data["full_name"],
        )

        # Login
        session = auth.login(
            admin_user_data["username"],
            admin_user_data["password"],
        )

        assert session is not None
        assert session.username == admin_user_data["username"]
        assert session_manager.is_authenticated
        assert session_manager.current_user.username == admin_user_data["username"]

    def test_login_fails_with_wrong_credentials(
        self, db: DatabaseManager, admin_user_data: dict, session_manager: SessionManager
    ):
        """Test that login fails with wrong credentials."""
        auth = AuthService(db)

        # Create user
        auth.create_first_admin(
            username=admin_user_data["username"],
            password=admin_user_data["password"],
            full_name=admin_user_data["full_name"],
        )

        # Login with wrong password
        session = auth.login(admin_user_data["username"], "wrongpassword")

        assert session is None
        assert not session_manager.is_authenticated

    def test_logout(
        self, db: DatabaseManager, admin_user_data: dict, session_manager: SessionManager
    ):
        """Test logout clears session."""
        auth = AuthService(db)

        # Create and login
        auth.create_first_admin(
            username=admin_user_data["username"],
            password=admin_user_data["password"],
            full_name=admin_user_data["full_name"],
        )
        auth.login(admin_user_data["username"], admin_user_data["password"])

        assert session_manager.is_authenticated

        # Logout
        auth.logout()

        assert not session_manager.is_authenticated
        assert session_manager.current_user is None

    def test_change_password(self, db: DatabaseManager, admin_user_data: dict):
        """Test changing password."""
        auth = AuthService(db)

        # Create user
        user = auth.create_first_admin(
            username=admin_user_data["username"],
            password=admin_user_data["password"],
            full_name=admin_user_data["full_name"],
        )

        # Change password
        new_password = "newpassword456"
        success, error = auth.change_password(
            user.user_id,
            admin_user_data["password"],
            new_password,
        )

        assert success
        assert error == ""

        # Old password should fail
        assert auth.authenticate(admin_user_data["username"], admin_user_data["password"]) is None

        # New password should work
        assert auth.authenticate(admin_user_data["username"], new_password) is not None

    def test_change_password_wrong_current(
        self, db: DatabaseManager, admin_user_data: dict
    ):
        """Test changing password with wrong current password."""
        auth = AuthService(db)

        # Create user
        user = auth.create_first_admin(
            username=admin_user_data["username"],
            password=admin_user_data["password"],
            full_name=admin_user_data["full_name"],
        )

        # Try to change with wrong current password
        success, error = auth.change_password(
            user.user_id,
            "wrongpassword",
            "newpassword456",
        )

        assert not success
        assert "incorrect" in error.lower()


class TestSessionManager:
    """Tests for SessionManager class."""

    def test_singleton_pattern(self):
        """Test that SessionManager is a singleton."""
        SessionManager.reset_instance()

        manager1 = SessionManager.get_instance()
        manager2 = SessionManager.get_instance()

        assert manager1 is manager2

        SessionManager.reset_instance()

    def test_login_creates_session(self, session_manager: SessionManager):
        """Test creating a session."""
        session = session_manager.login(
            user_id="test-id",
            username="testuser",
            full_name="Test User",
            role="ADMIN",
        )

        assert session is not None
        assert session.user_id == "test-id"
        assert session.username == "testuser"
        assert session.full_name == "Test User"
        assert session.role == "ADMIN"

    def test_is_authenticated(self, session_manager: SessionManager):
        """Test authentication check."""
        assert not session_manager.is_authenticated

        session_manager.login(
            user_id="test-id",
            username="testuser",
            full_name="Test User",
            role="ADMIN",
        )

        assert session_manager.is_authenticated

    def test_logout_clears_session(self, session_manager: SessionManager):
        """Test logout clears session."""
        session_manager.login(
            user_id="test-id",
            username="testuser",
            full_name="Test User",
            role="ADMIN",
        )

        assert session_manager.is_authenticated

        session_manager.logout()

        assert not session_manager.is_authenticated
        assert session_manager.current_user is None

    def test_can_edit(self, session_manager: SessionManager):
        """Test can_edit for different roles."""
        # Admin can edit
        session_manager.login("id", "user", "User", "ADMIN")
        assert session_manager.can_edit()
        session_manager.logout()

        # Editor can edit
        session_manager.login("id", "user", "User", "EDITOR")
        assert session_manager.can_edit()
        session_manager.logout()

        # Viewer cannot edit
        session_manager.login("id", "user", "User", "VIEWER")
        assert not session_manager.can_edit()

    def test_is_admin(self, session_manager: SessionManager):
        """Test is_admin check."""
        session_manager.login("id", "user", "User", "ADMIN")
        assert session_manager.is_admin()
        session_manager.logout()

        session_manager.login("id", "user", "User", "EDITOR")
        assert not session_manager.is_admin()
