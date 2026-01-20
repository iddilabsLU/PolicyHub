"""
PolicyHub Entity Service

Manages CRUD operations for entities (applicable entity dropdown values).
"""

import logging
from typing import List, Optional

from core.database import DatabaseManager
from models.entity import Entity
from utils.files import generate_uuid
from utils.dates import get_now

logger = logging.getLogger(__name__)


class EntityService:
    """
    Service for managing entities.

    Entities are used for the "Applicable Entity" dropdown field in documents.
    Users can select existing entities or type new ones, which are automatically
    saved for future use.
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize the entity service.

        Args:
            db: Database manager instance
        """
        self.db = db

    def get_all_entities(self) -> List[Entity]:
        """
        Get all entities, sorted alphabetically by name.

        Returns:
            List of all entities
        """
        rows = self.db.fetch_all(
            "SELECT * FROM entities ORDER BY name ASC"
        )
        return [Entity.from_row(row) for row in rows]

    def get_entity_by_id(self, entity_id: str) -> Optional[Entity]:
        """
        Get an entity by its ID.

        Args:
            entity_id: The entity ID to look up

        Returns:
            Entity if found, None otherwise
        """
        row = self.db.fetch_one(
            "SELECT * FROM entities WHERE entity_id = ?",
            (entity_id,)
        )
        return Entity.from_row(row) if row else None

    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """
        Get an entity by its name (case-insensitive).

        Args:
            name: The entity name to look up

        Returns:
            Entity if found, None otherwise
        """
        row = self.db.fetch_one(
            "SELECT * FROM entities WHERE name = ? COLLATE NOCASE",
            (name,)
        )
        return Entity.from_row(row) if row else None

    def entity_exists(self, name: str) -> bool:
        """
        Check if an entity with the given name exists (case-insensitive).

        Args:
            name: The entity name to check

        Returns:
            True if entity exists, False otherwise
        """
        return self.get_entity_by_name(name) is not None

    def create_entity(self, name: str) -> Entity:
        """
        Create a new entity.

        Args:
            name: The name for the new entity

        Returns:
            The created Entity

        Raises:
            ValueError: If entity with this name already exists
        """
        # Check for duplicate name
        if self.entity_exists(name):
            raise ValueError(f"Entity '{name}' already exists")

        entity_id = generate_uuid()
        created_at = get_now()

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO entities (entity_id, name, created_at)
                VALUES (?, ?, ?)
                """,
                (entity_id, name.strip(), created_at),
            )

        logger.info(f"Created entity: {name}")

        return Entity(
            entity_id=entity_id,
            name=name.strip(),
            created_at=created_at,
        )

    def get_or_create_entity(self, name: str) -> Entity:
        """
        Get an existing entity or create a new one if it doesn't exist.

        This is the main method to use when saving documents with an
        applicable entity - it handles both existing and new entities.

        Args:
            name: The entity name

        Returns:
            The existing or newly created Entity
        """
        name = name.strip()
        if not name:
            raise ValueError("Entity name cannot be empty")

        existing = self.get_entity_by_name(name)
        if existing:
            return existing

        return self.create_entity(name)

    def get_entity_names(self) -> List[str]:
        """
        Get a list of all entity names, sorted alphabetically.

        This is useful for populating dropdown/combobox values.

        Returns:
            List of entity names
        """
        rows = self.db.fetch_all(
            "SELECT name FROM entities ORDER BY name ASC"
        )
        return [row["name"] for row in rows]

    def delete_entity(self, entity_id: str) -> bool:
        """
        Delete an entity by ID.

        Note: This does not update documents that reference this entity.
        Consider updating documents first or using soft-delete.

        Args:
            entity_id: The entity ID to delete

        Returns:
            True if deleted, False if not found
        """
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM entities WHERE entity_id = ?",
                (entity_id,)
            )
            deleted = cursor.rowcount > 0

        if deleted:
            logger.info(f"Deleted entity: {entity_id}")

        return deleted

    # ============================================================
    # Multi-Entity Helpers
    # ============================================================

    @staticmethod
    def parse_entities(entity_string: Optional[str]) -> List[str]:
        """
        Parse a semicolon-separated entity string into a list.

        Args:
            entity_string: Semicolon-separated entity names (e.g., "Entity A;Entity B")

        Returns:
            List of entity names (empty list if input is None or empty)
        """
        if not entity_string:
            return []
        return [e.strip() for e in entity_string.split(";") if e.strip()]

    @staticmethod
    def format_entities(entities: List[str]) -> str:
        """
        Format a list of entity names into a semicolon-separated string.

        Args:
            entities: List of entity names

        Returns:
            Semicolon-separated string (empty string if list is empty)
        """
        if not entities:
            return ""
        return ";".join(e.strip() for e in entities if e.strip())

    def ensure_entities_exist(self, entity_string: Optional[str]) -> None:
        """
        Ensure all entities in a semicolon-separated string exist in the database.

        Creates any entities that don't exist.

        Args:
            entity_string: Semicolon-separated entity names
        """
        if not entity_string:
            return

        entities = self.parse_entities(entity_string)
        for entity_name in entities:
            self.get_or_create_entity(entity_name)

    def get_or_create_multiple(self, entity_names: List[str]) -> List[Entity]:
        """
        Get or create multiple entities at once.

        Args:
            entity_names: List of entity names

        Returns:
            List of Entity objects
        """
        entities = []
        for name in entity_names:
            if name.strip():
                entities.append(self.get_or_create_entity(name.strip()))
        return entities
