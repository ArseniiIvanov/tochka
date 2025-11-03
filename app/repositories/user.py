"""User repository."""
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, UserInventory, RoleEnum
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_id(self, user_id: str | UUID) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            Optional[User]: Found user or None
        """
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        return await self.session.get(User, user_id)

    async def get_by_name(self, name: str) -> Optional[User]:
        """
        Get user by name.

        Args:
            name: User name

        Returns:
            Optional[User]: Found user or None
        """
        stmt = select(User).where(User.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self, name: str, role: RoleEnum = RoleEnum.USER
    ) -> User:
        """
        Create new user with inventory for all instruments.

        Args:
            name: User name
            role: User role

        Returns:
            User: Created user
        """
        from app.repositories.instrument import InstrumentRepository

        new_user = User(name=name, role=role)
        self.session.add(new_user)
        await self.session.flush()

        # Create inventory for all existing instruments
        instrument_repo = InstrumentRepository(self.session)
        instruments = await instrument_repo.get_all()
        for instrument in instruments:
            inv = UserInventory(
                user=new_user, instrument=instrument, quantity=0.0
            )
            self.session.add(inv)

        await self.session.flush()
        await self.session.refresh(new_user)
        return new_user

    async def update_api_key(self, user_id: str, api_key: str) -> Optional[User]:
        """
        Update user API key.

        Args:
            user_id: User ID
            api_key: New API key

        Returns:
            Optional[User]: Updated user or None
        """
        user = await self.get_by_id(user_id)
        if user:
            user.api_key = api_key
            await self.session.flush()
            await self.session.refresh(user)
        return user

    async def get_user_orders(self, user_id: UUID) -> List:
        """
        Get all orders for user.

        Args:
            user_id: User ID

        Returns:
            List: List of orders
        """
        from app.models import Order

        stmt = select(Order).where(Order.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_inventory(
        self, user_id: UUID, ticker: Optional[str] = None
    ) -> List[UserInventory]:
        """
        Get user inventory.

        Args:
            user_id: User ID
            ticker: Optional instrument ticker filter

        Returns:
            List[UserInventory]: List of inventory items
        """
        stmt = select(UserInventory).where(UserInventory.user_id == user_id)
        if ticker:
            stmt = stmt.where(UserInventory.instrument_ticker == ticker)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

