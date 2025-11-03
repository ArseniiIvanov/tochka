"""Instrument repository."""
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Instrument
from app.repositories.base import BaseRepository


class InstrumentRepository(BaseRepository[Instrument]):
    """Repository for Instrument operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Instrument)

    async def get_by_ticker(self, ticker: str) -> Optional[Instrument]:
        """
        Get instrument by ticker.

        Args:
            ticker: Instrument ticker

        Returns:
            Optional[Instrument]: Found instrument or None
        """
        stmt = select(Instrument).where(Instrument.ticker == ticker)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_instrument(
        self, name: str, ticker: str
    ) -> Instrument:
        """
        Create new instrument and inventory for all users.

        Args:
            name: Instrument name
            ticker: Instrument ticker

        Returns:
            Instrument: Created instrument
        """
        from app.models import UserInventory
        from app.repositories.user import UserRepository

        new_instrument = Instrument(name=name, ticker=ticker)
        self.session.add(new_instrument)
        await self.session.flush()

        # Create inventory for all existing users
        user_repo = UserRepository(self.session)
        users = await user_repo.get_all()
        for user in users:
            inv = UserInventory(
                user=user, instrument=new_instrument, quantity=0.0
            )
            self.session.add(inv)

        await self.session.flush()
        await self.session.refresh(new_instrument)
        return new_instrument

