"""Transaction repository."""
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    """Repository for Transaction operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Transaction)

    async def get_by_ticker(
        self, ticker: str, limit: int = 10
    ) -> List[Transaction]:
        """
        Get transactions by instrument ticker.

        Args:
            ticker: Instrument ticker
            limit: Maximum number of transactions

        Returns:
            List[Transaction]: List of transactions
        """
        stmt = (
            select(Transaction)
            .where(Transaction.instrument_ticker == ticker)
            .order_by(Transaction.timestamp.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

