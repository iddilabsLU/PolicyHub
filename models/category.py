"""
PolicyHub Category Model

Represents a document category for classification.
"""

from dataclasses import dataclass
from sqlite3 import Row


@dataclass
class Category:
    """
    Represents a document category.

    Attributes:
        code: Unique category code (e.g., AML, GOV, OPS)
        name: Display name (e.g., "Anti-Money Laundering & CFT")
        is_active: Whether the category is active (visible)
        sort_order: Display order in lists
    """

    code: str
    name: str
    is_active: bool
    sort_order: int

    @classmethod
    def from_row(cls, row: Row) -> "Category":
        """
        Create a Category from a SQLite row.

        Args:
            row: SQLite Row object with category data

        Returns:
            Category instance
        """
        return cls(
            code=row["code"],
            name=row["name"],
            is_active=bool(row["is_active"]),
            sort_order=row["sort_order"],
        )

    def to_dict(self) -> dict:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation of the category
        """
        return {
            "code": self.code,
            "name": self.name,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
        }


@dataclass
class CategoryCreate:
    """Data required to create a new category."""

    code: str
    name: str
    sort_order: int = 99
    is_active: bool = True


@dataclass
class CategoryUpdate:
    """Data for updating an existing category."""

    name: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None
