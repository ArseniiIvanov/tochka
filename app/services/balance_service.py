"""Balance service for managing user balances."""
from typing import Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import InsufficientBalanceError, NotFoundError
from app.models import User, UserInventory
from app.repositories.inventory import InventoryRepository
from app.repositories.order import OrderRepository
from app.repositories.user import UserRepository
from app.models import OrderStatusEnum, DirectionEnum

settings = get_settings()


class BalanceService:
    """Service for balance operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize balance service.

        Args:
            session: Database session
        """
        self.session = session
        self.user_repo = UserRepository(session)
        self.inventory_repo = InventoryRepository(session)
        self.order_repo = OrderRepository(session)

    async def get_user_balance(self, user_id: UUID) -> Dict[str, float]:
        """
        Get user balance including all instruments and frozen amounts.

        Args:
            user_id: User ID

        Returns:
            Dict[str, float]: Balance dictionary with ticker as key
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))

        # Get inventory
        inventory = await self.user_repo.get_user_inventory(user_id)
        result: Dict[str, float] = {
            item.instrument_ticker: item.quantity for item in inventory
        }
        result[settings.base_instrument_ticker] = user.balance

        # Add frozen amounts from active orders
        orders = await self.user_repo.get_user_orders(user_id)
        for order in orders:
            if order.status in [OrderStatusEnum.NEW, OrderStatusEnum.PARTIALLY_EXECUTED]:
                if order.direction == DirectionEnum.ASK:
                    # Sell order - freeze instruments
                    ticker = order.instrument_ticker
                    result[ticker] = result.get(ticker, 0.0) + order.amount
                elif order.direction == DirectionEnum.BID:
                    # Buy order - freeze base currency
                    if order.price:
                        result[settings.base_instrument_ticker] += order.amount * order.price

        return result

    async def change_balance(
        self, user_id: UUID, ticker: str, amount: float
    ) -> User:
        """
        Change user balance for given ticker.

        Args:
            user_id: User ID
            ticker: Instrument ticker
            amount: Amount to change (positive for deposit, negative for withdraw)

        Returns:
            User: Updated user

        Raises:
            NotFoundError: If user or instrument not found
            InsufficientBalanceError: If balance would become negative
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))

        if ticker == settings.base_instrument_ticker:
            # Change base currency balance
            new_balance = user.balance + amount
            if new_balance < 0:
                raise InsufficientBalanceError(
                    ticker, abs(amount), user.balance
                )
            user.balance = new_balance
            await self.session.flush()
            await self.session.refresh(user)
            return user
        else:
            # Change instrument inventory
            inventory = await self.inventory_repo.get_by_user_and_ticker(
                user_id, ticker
            )
            if not inventory:
                raise NotFoundError("Instrument", ticker)

            new_quantity = inventory.quantity + amount
            if new_quantity < 0:
                raise InsufficientBalanceError(
                    ticker, abs(amount), inventory.quantity
                )
            inventory.quantity = new_quantity
            await self.session.flush()
            await self.session.refresh(user)
            return user

