"""
Tests for SettingsService.

Tests settings CRUD operations.
"""

import pytest

from services.settings_service import SettingsService


class TestSettingsService:
    """Tests for SettingsService."""

    def test_get_all_settings_returns_defaults(self, db):
        """Test that default settings are seeded."""
        service = SettingsService(db)
        settings = service.get_all_settings()

        # Default settings should exist
        assert len(settings) > 0
        assert SettingsService.COMPANY_NAME in settings
        assert SettingsService.WARNING_THRESHOLD in settings
        assert SettingsService.DATE_FORMAT in settings

    def test_get_setting_returns_value(self, db):
        """Test retrieving a specific setting."""
        service = SettingsService(db)
        value = service.get_setting(SettingsService.DATE_FORMAT)

        assert value is not None
        assert value in ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"]

    def test_get_setting_not_found_returns_none(self, db):
        """Test that non-existent setting returns None."""
        service = SettingsService(db)
        value = service.get_setting("nonexistent_key")

        assert value is None

    def test_set_setting_creates_new(self, db, logged_in_admin):
        """Test creating a new setting."""
        service = SettingsService(db)

        service.set_setting("custom_key", "custom_value")
        value = service.get_setting("custom_key")

        assert value == "custom_value"

    def test_set_setting_updates_existing(self, db, logged_in_admin):
        """Test updating an existing setting."""
        service = SettingsService(db)

        original = service.get_setting(SettingsService.COMPANY_NAME)
        service.set_setting(SettingsService.COMPANY_NAME, "New Company Name")
        updated = service.get_setting(SettingsService.COMPANY_NAME)

        assert updated == "New Company Name"
        assert updated != original

    def test_set_setting_requires_permission(self, db):
        """Test that setting a value requires permission."""
        service = SettingsService(db)

        with pytest.raises(PermissionError):
            service.set_setting("key", "value")

    def test_update_settings_bulk(self, db, logged_in_admin):
        """Test updating multiple settings at once."""
        service = SettingsService(db)

        updates = {
            SettingsService.COMPANY_NAME: "Bulk Company",
            SettingsService.WARNING_THRESHOLD: "45",
            SettingsService.DATE_FORMAT: "YYYY-MM-DD",
        }

        service.update_settings(updates)

        assert service.get_setting(SettingsService.COMPANY_NAME) == "Bulk Company"
        assert service.get_setting(SettingsService.WARNING_THRESHOLD) == "45"
        assert service.get_setting(SettingsService.DATE_FORMAT) == "YYYY-MM-DD"

    def test_update_settings_requires_permission(self, db):
        """Test that bulk update requires permission."""
        service = SettingsService(db)

        with pytest.raises(PermissionError):
            service.update_settings({"key": "value"})

    def test_get_company_name(self, db, logged_in_admin):
        """Test getting company name via typed getter."""
        service = SettingsService(db)

        service.set_setting(SettingsService.COMPANY_NAME, "Test Corp")
        name = service.get_company_name()

        assert name == "Test Corp"

    def test_get_warning_threshold_days(self, db, logged_in_admin):
        """Test getting warning threshold via typed getter."""
        service = SettingsService(db)

        service.set_setting(SettingsService.WARNING_THRESHOLD, "45")
        days = service.get_warning_threshold_days()

        assert days == 45

    def test_get_warning_threshold_days_default(self, db):
        """Test that warning threshold returns default on invalid value."""
        service = SettingsService(db)
        days = service.get_warning_threshold_days()

        # Should return a valid integer (the default)
        assert isinstance(days, int)
        assert days > 0

    def test_get_upcoming_threshold_days(self, db, logged_in_admin):
        """Test getting upcoming threshold via typed getter."""
        service = SettingsService(db)

        service.set_setting(SettingsService.UPCOMING_THRESHOLD, "90")
        days = service.get_upcoming_threshold_days()

        assert days == 90

    def test_get_date_format(self, db, logged_in_admin):
        """Test getting date format via typed getter."""
        service = SettingsService(db)

        service.set_setting(SettingsService.DATE_FORMAT, "MM/DD/YYYY")
        format_str = service.get_date_format()

        assert format_str == "MM/DD/YYYY"

    def test_get_default_review_frequency(self, db, logged_in_admin):
        """Test getting default review frequency via typed getter."""
        service = SettingsService(db)

        service.set_setting(SettingsService.DEFAULT_REVIEW_FREQUENCY, "QUARTERLY")
        frequency = service.get_default_review_frequency()

        assert frequency == "QUARTERLY"
