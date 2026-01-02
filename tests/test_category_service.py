"""
Tests for CategoryService.

Tests category CRUD operations.
"""

import pytest

from models.category import CategoryCreate, CategoryUpdate
from services.category_service import CategoryService


class TestCategoryService:
    """Tests for CategoryService."""

    def test_get_all_categories_returns_default_categories(self, db):
        """Test that default categories are seeded."""
        service = CategoryService(db)
        categories = service.get_all_categories()

        # Default categories should exist
        assert len(categories) > 0
        codes = [c.code for c in categories]
        assert "AML" in codes
        assert "GOV" in codes
        assert "OPS" in codes

    def test_get_active_categories_excludes_inactive(self, db, logged_in_admin):
        """Test that inactive categories are excluded."""
        service = CategoryService(db)

        # Deactivate a category
        service.update_category("OTHER", CategoryUpdate(is_active=False))

        active = service.get_active_categories()
        all_cats = service.get_all_categories(include_inactive=True)

        assert len(active) < len(all_cats)
        assert not any(c.code == "OTHER" for c in active)

    def test_get_category_by_code(self, db):
        """Test retrieving a category by code."""
        service = CategoryService(db)
        category = service.get_category_by_code("AML")

        assert category is not None
        assert category.code == "AML"
        assert "Anti-Money Laundering" in category.name

    def test_get_category_by_code_not_found(self, db):
        """Test that non-existent category returns None."""
        service = CategoryService(db)
        category = service.get_category_by_code("NONEXISTENT")

        assert category is None

    def test_code_exists(self, db):
        """Test checking if category code exists."""
        service = CategoryService(db)

        assert service.code_exists("AML") is True
        assert service.code_exists("NONEXISTENT") is False

    def test_create_category(self, db, logged_in_admin):
        """Test creating a new category."""
        service = CategoryService(db)

        data = CategoryCreate(
            code="TEST",
            name="Test Category",
            sort_order=50,
        )
        category = service.create_category(data)

        assert category is not None
        assert category.code == "TEST"
        assert category.name == "Test Category"
        assert category.is_active is True

    def test_create_category_duplicate_code_raises(self, db, logged_in_admin):
        """Test that creating category with existing code raises error."""
        service = CategoryService(db)

        data = CategoryCreate(code="AML", name="Duplicate")

        with pytest.raises(ValueError, match="already exists"):
            service.create_category(data)

    def test_create_category_requires_permission(self, db):
        """Test that creating category requires permission."""
        service = CategoryService(db)
        data = CategoryCreate(code="TEST", name="Test")

        with pytest.raises(PermissionError):
            service.create_category(data)

    def test_update_category(self, db, logged_in_admin):
        """Test updating a category."""
        service = CategoryService(db)

        data = CategoryUpdate(name="Updated AML Name")
        updated = service.update_category("AML", data)

        assert updated is not None
        assert updated.name == "Updated AML Name"

    def test_update_category_not_found(self, db, logged_in_admin):
        """Test updating non-existent category returns None."""
        service = CategoryService(db)

        data = CategoryUpdate(name="New Name")
        result = service.update_category("NONEXISTENT", data)

        assert result is None

    def test_deactivate_category(self, db, logged_in_admin):
        """Test deactivating a category."""
        service = CategoryService(db)

        # OTHER category should have no documents
        result = service.deactivate_category("OTHER")

        assert result is True
        category = service.get_category_by_code("OTHER")
        assert category.is_active is False

    def test_deactivate_category_with_documents_raises(self, db, logged_in_admin, sample_document_data):
        """Test that deactivating category with documents raises error."""
        from services.document_service import DocumentService
        from models.document import DocumentCreate

        doc_service = DocumentService(db)
        doc_data = DocumentCreate(**sample_document_data)
        doc_service.create_document(doc_data)

        cat_service = CategoryService(db)

        with pytest.raises(ValueError, match="document"):
            cat_service.deactivate_category("AML")

    def test_activate_category(self, db, logged_in_admin):
        """Test activating a deactivated category."""
        service = CategoryService(db)

        # First deactivate
        service.deactivate_category("OTHER")

        # Then activate
        result = service.activate_category("OTHER")

        assert result is True
        category = service.get_category_by_code("OTHER")
        assert category.is_active is True

    def test_get_category_usage_stats(self, db, logged_in_admin, sample_document_data):
        """Test getting category usage statistics."""
        from services.document_service import DocumentService
        from models.document import DocumentCreate

        doc_service = DocumentService(db)
        doc_data = DocumentCreate(**sample_document_data)
        doc_service.create_document(doc_data)

        cat_service = CategoryService(db)
        stats = cat_service.get_category_usage_stats()

        assert "AML" in stats
        assert stats["AML"] >= 1
