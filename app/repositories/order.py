"""Order repository."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, DirectionEnum, OrderStatusEnum
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """Repository for Order operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Order)

    async def get_by_id(self, order_id: str | UUID) -> Optional[Order]:
        """
        Get order by ID.

        Args:
            order_id: Order ID

        Returns:
            Optional[Order]: Found order or None
        """
        if isinstance(order_id, str):
            order_id = UUID(order_id)
        return await self.session.get(Order, order_id)

    async def get_orders(
        self,
        ticker: str,
        direction: DirectionEnum,
        limit: int = 10,
        statuses: Optional[List[OrderStatusEnum]] = None,
    ) -> List[Order]:
        """
        Get orders by ticker and direction.

        Args:
            ticker: Instrument ticker
            direction: Order direction
            limit: Maximum number of orders
            statuses: Optional list of statuses to filter

        Returns:
            List[Order]: List of orders
        """
        if statuses is None:
            statuses = [OrderStatusEnum.NEW, OrderStatusEnum.PARTIALLY_EXECUTED]

        stmt = (
            select(Order)
            .where(
                Order.instrument_ticker == ticker,
                Order.direction == direction,
                Order.status.in_(statuses),
            )
            .order_by(
                desc(Order.price) if direction == DirectionEnum.BID else asc(Order.price),
                Order.created_at,
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_orders(self, user_id: UUID) -> List[Order]:
        """
        Get all orders for user.

        Args:
            user_id: User ID

        Returns:
            List[Order]: List of orders
        """
        stmt = select(Order).where(Order.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

