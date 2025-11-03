"""Inventory repository."""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserInventory
from app.repositories.base import BaseRepository


class InventoryRepository(BaseRepository[UserInventory]):
    """Repository for UserInventory operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserInventory)

    async def get_by_user_and_ticker(
        self, user_id: UUID, ticker: str
    ) -> Optional[UserInventory]:
        """
        Get inventory by user and ticker.

        Args:
            user_id: User ID
            ticker: Instrument ticker

        Returns:
            Optional[UserInventory]: Found inventory or None
        """
        stmt = select(UserInventory).where(
            UserInventory.user_id == user_id,
            UserInventory.instrument_ticker == ticker,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

