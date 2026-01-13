"""
PolicyHub Entity Model

Represents an applicable entity that documents can be associated with.
Entities are used for the "Applicable Entity" dropdown field in documents.
"""

from dataclasses import dataclass
from sqlite3 import Row


@dataclass
class Entity:
    """
    Represents an applicable entity.

    Attributes:
        entity_id: Unique identifier (UUID)
        name: Entity name (e.g., "Branch A", "Head Office")
        created_at: Creation timestamp (ISO 8601)
    """

    entity_id: str
    name: str
    created_at: str

    @classmethod
    def from_row(cls, row: Row) -> "Entity":
        """
        Create an Entity from a SQLite row.

        Args:
            row: SQLite Row object with entity data

        Returns:
            Entity instance
        """
        return cls(
            entity_id=row["entity_id"],
            name=row["name"],
            created_at=row["created_at"],
        )

    def to_dict(self) -> dict:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation of the entity
        """
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "created_at": self.created_at,
        }
