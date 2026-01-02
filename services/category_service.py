"""
PolicyHub Category Service

Handles CRUD operations for document categories.
"""

import logging
from typing import List, Optional

from core.database import DatabaseManager
from core.permissions import Permission, require_permission
from models.category import Category, CategoryCreate, CategoryUpdate

logger = logging.getLogger(__name__)


class CategoryService:
    """
    Service for managing document categories.

    Categories are used to classify documents by functional area
    (e.g., AML, Governance, Operations).
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize the category service.

        Args:
            db: Database manager instance
        """
        self.db = db

    def get_all_categories(self, include_inactive: bool = False) -> List[Category]:
        """
        Get all categories.

        Args:
            include_inactive: Whether to include inactive categories

        Returns:
            List of Category objects, ordered by sort_order
        """
        if include_inactive:
            query = "SELECT * FROM categories ORDER BY sort_order, code"
        else:
            query = "SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order, code"

        rows = self.db.fetch_all(query)
        return [Category.from_row(row) for row in rows]

    def get_active_categories(self) -> List[Category]:
        """
        Get only active categories.

        Convenience method for populating dropdowns.

        Returns:
            List of active Category objects
        """
        return self.get_all_categories(include_inactive=False)

    def get_category_by_code(self, code: str) -> Optional[Category]:
        """
        Get a category by its code.

        Args:
            code: Category code (e.g., "AML", "GOV")

        Returns:
            Category object or None if not found
        """
        row = self.db.fetch_one(
            "SELECT * FROM categories WHERE code = ?",
            (code,),
        )
        return Category.from_row(row) if row else None

    def code_exists(self, code: str) -> bool:
        """
        Check if a category code already exists.

        Args:
            code: Category code to check

        Returns:
            True if code exists
        """
        row = self.db.fetch_one(
            "SELECT 1 FROM categories WHERE code = ?",
            (code,),
        )
        return row is not None

    def get_category_document_count(self, code: str) -> int:
        """
        Count documents using a category.

        Args:
            code: Category code

        Returns:
            Number of documents using this category
        """
        row = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM documents WHERE category = ?",
            (code,),
        )
        return row["count"] if row else 0

    @require_permission(Permission.MANAGE_CATEGORIES)
    def create_category(self, data: CategoryCreate) -> Category:
        """
        Create a new category.

        Args:
            data: Category creation data

        Returns:
            Created Category object

        Raises:
            ValueError: If code already exists
            PermissionError: If user lacks permission
        """
        # Check code availability
        if self.code_exists(data.code):
            raise ValueError(f"Category code '{data.code}' already exists")

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO categories (code, name, is_active, sort_order)
                VALUES (?, ?, ?, ?)
                """,
                (
                    data.code.upper(),
                    data.name,
                    1 if data.is_active else 0,
                    data.sort_order,
                ),
            )

        logger.info(f"Category created: {data.code}")
        return self.get_category_by_code(data.code.upper())

    @require_permission(Permission.MANAGE_CATEGORIES)
    def update_category(self, code: str, data: CategoryUpdate) -> Optional[Category]:
        """
        Update a category.

        Args:
            code: Category code
            data: Update data

        Returns:
            Updated Category object or None if not found

        Raises:
            PermissionError: If user lacks permission
        """
        category = self.get_category_by_code(code)
        if category is None:
            return None

        # Build update query
        updates = []
        params = []

        if data.name is not None:
            updates.append("name = ?")
            params.append(data.name)

        if data.is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if data.is_active else 0)

        if data.sort_order is not None:
            updates.append("sort_order = ?")
            params.append(data.sort_order)

        if not updates:
            return category  # Nothing to update

        params.append(code)
        query = f"UPDATE categories SET {', '.join(updates)} WHERE code = ?"

        with self.db.get_connection() as conn:
            conn.execute(query, tuple(params))

        logger.info(f"Category updated: {code}")
        return self.get_category_by_code(code)

    @require_permission(Permission.MANAGE_CATEGORIES)
    def deactivate_category(self, code: str) -> bool:
        """
        Deactivate a category (soft delete).

        Args:
            code: Category code

        Returns:
            True if successful

        Raises:
            ValueError: If category has documents assigned
            PermissionError: If user lacks permission
        """
        # Check if any documents use this category
        doc_count = self.get_category_document_count(code)
        if doc_count > 0:
            raise ValueError(
                f"Cannot deactivate: {doc_count} document(s) use this category"
            )

        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE categories SET is_active = 0 WHERE code = ?",
                (code,),
            )
            if cursor.rowcount > 0:
                logger.info(f"Category deactivated: {code}")
                return True
        return False

    @require_permission(Permission.MANAGE_CATEGORIES)
    def activate_category(self, code: str) -> bool:
        """
        Activate a category.

        Args:
            code: Category code

        Returns:
            True if successful

        Raises:
            PermissionError: If user lacks permission
        """
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE categories SET is_active = 1 WHERE code = ?",
                (code,),
            )
            if cursor.rowcount > 0:
                logger.info(f"Category activated: {code}")
                return True
        return False

    def get_category_usage_stats(self) -> dict:
        """
        Get document counts per category.

        Returns:
            Dictionary mapping category codes to document counts
        """
        rows = self.db.fetch_all(
            """
            SELECT category, COUNT(*) as count
            FROM documents
            GROUP BY category
            """
        )
        return {row["category"]: row["count"] for row in rows}
