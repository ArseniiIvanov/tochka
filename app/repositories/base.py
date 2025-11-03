"""Base repository with common methods."""
from typing import Generic, TypeVar, Optional, List, Type
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        """
        Initialize repository.

        Args:
            session: Database session
            model: SQLAlchemy model class
        """
        self.session = session
        self.model = model

    async def get_by_id(self, id: str | UUID) -> Optional[ModelType]:
        """
        Get entity by ID.

        Args:
            id: Entity ID

        Returns:
            Optional[ModelType]: Found entity or None
        """
        if isinstance(id, str):
            id = UUID(id)
        return await self.session.get(self.model, id)

    async def get_all(self, limit: Optional[int] = None) -> List[ModelType]:
        """
        Get all entities.

        Args:
            limit: Optional limit

        Returns:
            List[ModelType]: List of entities
        """
        stmt = select(self.model)
        if limit:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, entity: ModelType) -> ModelType:
        """
        Create new entity.

        Args:
            entity: Entity to create

        Returns:
            ModelType: Created entity
        """
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: ModelType) -> None:
        """
        Delete entity.

        Args:
            entity: Entity to delete
        """
        await self.session.delete(entity)
        await self.session.flush()

    async def delete_all(self) -> int:
        """
        Delete all entities.

        Returns:
            int: Number of deleted entities
        """
        stmt = delete(self.model)
        result = await self.session.execute(stmt)
        return result.rowcount or 0

