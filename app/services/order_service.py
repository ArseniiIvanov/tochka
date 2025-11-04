"""Order service for managing trading orders."""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    InsufficientBalanceError,
    NotFoundError,
    OrderExecutionError,
)
from app.models import User, Order, DirectionEnum, OrderStatusEnum
from app.repositories.inventory import InventoryRepository
from app.repositories.order import OrderRepository
from app.repositories.user import UserRepository
from app.repositories.transaction import TransactionRepository
from app.models import Transaction

settings = get_settings()


class OrderService:
    """Service for order operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize order service.

        Args:
            session: Database session
        """
        self.session = session
        self.order_repo = OrderRepository(session)
        self.user_repo = UserRepository(session)
        self.inventory_repo = InventoryRepository(session)
        self.transaction_repo = TransactionRepository(session)

    async def create_limit_buy_order(
        self, ticker: str, qty: int, price: int, user: User
    ) -> Order:
        """
        Create limit buy order.

        Args:
            ticker: Instrument ticker
            qty: Quantity to buy
            price: Maximum price per unit
            user: User creating the order

        Returns:
            Order: Created order
        """
        # Get matching sell orders
        orderbook = await self.order_repo.get_orders(
            ticker, DirectionEnum.ASK, limit=qty
        )

        new_order = Order(
            user_id=user.id,
            instrument_ticker=ticker,
            amount=qty,
            filled=0,
            price=price,
            direction=DirectionEnum.BID,
            status=OrderStatusEnum.NEW,
        )

        try:
            # Execute against matching orders
            for order in orderbook:
                if new_order.amount == 0 or (price and order.price > price):
                    break

                count_to_buy = min(order.amount, new_order.amount)
                await self._execute_buy(
                    order.user_id, user.id, ticker, order.price, count_to_buy
                )
                await self._partially_execute_order(order, count_to_buy)
                await self._partially_execute_order(new_order, count_to_buy)

            # Freeze balance for remaining order
            if new_order.status != OrderStatusEnum.EXECUTED:
                if price:
                    await self._freeze_balance(
                        user.id, settings.base_instrument_ticker, new_order.amount * new_order.price
                    )
                else:
                    raise OrderExecutionError("Not enough orders for market buy")

            self.session.add(new_order)
            await self.session.flush()
            await self.session.refresh(new_order)
            return new_order

        except Exception as e:
            await self.session.rollback()
            new_order.filled = 0
            new_order.amount = qty
            new_order.status = OrderStatusEnum.CANCELLED
            self.session.add(new_order)
            await self.session.flush()
            raise OrderExecutionError(str(e)) from e

    async def create_limit_sell_order(
        self, ticker: str, qty: int, price: int, user: User
    ) -> Order:
        """
        Create limit sell order.

        Args:
            ticker: Instrument ticker
            qty: Quantity to sell
            price: Minimum price per unit
            user: User creating the order

        Returns:
            Order: Created order
        """
        # Get matching buy orders
        orderbook = await self.order_repo.get_orders(
            ticker, DirectionEnum.BID, limit=qty
        )

        new_order = Order(
            user_id=user.id,
            instrument_ticker=ticker,
            amount=qty,
            filled=0,
            price=price,
            direction=DirectionEnum.ASK,
            status=OrderStatusEnum.NEW,
        )

        try:
            # Execute against matching orders
            for order in orderbook:
                if new_order.amount == 0 or (price and order.price < price):
                    break

                count_to_sell = min(order.amount, new_order.amount)
                await self._execute_sell(
                    user.id, order.user_id, ticker, order.price, count_to_sell
                )
                await self._partially_execute_order(order, count_to_sell)
                await self._partially_execute_order(new_order, count_to_sell)

            # Freeze instruments for remaining order
            if new_order.status != OrderStatusEnum.EXECUTED:
                if price:
                    await self._freeze_balance(user.id, ticker, new_order.amount)
                else:
                    raise OrderExecutionError("Not enough orders for market sell")

            self.session.add(new_order)
            await self.session.flush()
            await self.session.refresh(new_order)
            return new_order

        except Exception as e:
            await self.session.rollback()
            new_order.filled = 0
            new_order.amount = qty
            new_order.status = OrderStatusEnum.CANCELLED
            self.session.add(new_order)
            await self.session.flush()
            raise OrderExecutionError(str(e)) from e

    async def create_market_buy_order(
        self, ticker: str, qty: int, user: User
    ) -> Order:
        """
        Create market buy order.

        Args:
            ticker: Instrument ticker
            qty: Quantity to buy
            user: User creating the order

        Returns:
            Order: Created order
        """
        return await self.create_limit_buy_order(ticker, qty, None, user)

    async def create_market_sell_order(
        self, ticker: str, qty: int, user: User
    ) -> Order:
        """
        Create market sell order.

        Args:
            ticker: Instrument ticker
            qty: Quantity to sell
            user: User creating the order

        Returns:
            Order: Created order
        """
        return await self.create_limit_sell_order(ticker, qty, None, user)

    async def cancel_order(self, order_id: UUID, user_id: UUID) -> Order:
        """
        Cancel order and unfreeze balance.

        Args:
            order_id: Order ID
            user_id: User ID (must match order owner)

        Returns:
            Order: Cancelled order

        Raises:
            NotFoundError: If order not found
            OrderExecutionError: If order cannot be cancelled
        """
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundError("Order", str(order_id))

        if order.user_id != user_id:
            raise OrderExecutionError("Order does not belong to user")

        if order.status in [
            OrderStatusEnum.PARTIALLY_EXECUTED,
            OrderStatusEnum.EXECUTED,
            OrderStatusEnum.CANCELLED,
        ]:
            raise OrderExecutionError(
                "Order already executed/partially_executed/cancelled"
            )

        if order.price is None:
            raise OrderExecutionError("Cannot cancel market order")

        # Unfreeze balance
        if order.direction == DirectionEnum.ASK:
            await self._unfreeze_balance(user_id, order.instrument_ticker, order.amount)
        elif order.direction == DirectionEnum.BID:
            await self._unfreeze_balance(
                user_id, settings.base_instrument_ticker, order.amount * order.price
            )

        order.status = OrderStatusEnum.CANCELLED
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def _execute_buy(
        self,
        seller_id: UUID,
        buyer_id: UUID,
        ticker: str,
        price: int,
        amount: int,
    ) -> Transaction:
        """Execute buy transaction."""
        buyer = await self.user_repo.get_by_id(buyer_id)
        seller = await self.user_repo.get_by_id(seller_id)
        buyer_inv = await self.inventory_repo.get_by_user_and_ticker(
            buyer_id, ticker
        )

        if not buyer or not seller or not buyer_inv:
            raise NotFoundError("User or inventory", str(buyer_id))

        total_cost = amount * price
        if buyer.balance < total_cost:
            raise InsufficientBalanceError(
                settings.base_instrument_ticker, total_cost, buyer.balance
            )

        transaction = Transaction(
            user_from_id=seller_id,
            user_to_id=buyer_id,
            instrument_ticker=ticker,
            amount=amount,
            price=float(price),
        )
        self.session.add(transaction)

        seller.balance += total_cost
        buyer.balance -= total_cost
        buyer_inv.quantity += amount

        await self.session.flush()
        return transaction

    async def _execute_sell(
        self,
        seller_id: UUID,
        buyer_id: UUID,
        ticker: str,
        price: int,
        amount: int,
    ) -> Transaction:
        """Execute sell transaction."""
        seller = await self.user_repo.get_by_id(seller_id)
        buyer = await self.user_repo.get_by_id(buyer_id)
        seller_inv = await self.inventory_repo.get_by_user_and_ticker(
            seller_id, ticker
        )
        buyer_inv = await self.inventory_repo.get_by_user_and_ticker(
            buyer_id, ticker
        )

        if not seller or not buyer or not seller_inv or not buyer_inv:
            raise NotFoundError("User or inventory", str(seller_id))

        if seller_inv.quantity < amount:
            raise InsufficientBalanceError(
                ticker, amount, seller_inv.quantity
            )

        total_cost = amount * price
        transaction = Transaction(
            user_from_id=seller_id,
            user_to_id=buyer_id,
            instrument_ticker=ticker,
            amount=amount,
            price=float(price),
        )
        self.session.add(transaction)

        seller.balance += total_cost
        seller_inv.quantity -= amount
        buyer_inv.quantity += amount

        await self.session.flush()
        return transaction

    async def _partially_execute_order(self, order: Order, amount: int) -> None:
        """Partially execute order."""
        if order.amount < amount:
            raise OrderExecutionError("Order amount insufficient")
        order.amount -= amount
        order.filled += amount
        order.status = (
            OrderStatusEnum.EXECUTED
            if order.amount == 0
            else OrderStatusEnum.PARTIALLY_EXECUTED
        )
        await self.session.flush()

    async def _freeze_balance(
        self, user_id: UUID, ticker: str, amount: int
    ) -> None:
        """Freeze balance for order."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))

        if ticker == settings.base_instrument_ticker:
            if user.balance < amount:
                raise InsufficientBalanceError(ticker, amount, user.balance)
            user.balance -= amount
        else:
            inventory = await self.inventory_repo.get_by_user_and_ticker(
                user_id, ticker
            )
            if not inventory:
                raise NotFoundError("Inventory", ticker)
            if inventory.quantity < amount:
                raise InsufficientBalanceError(ticker, amount, inventory.quantity)
            inventory.quantity -= amount

        await self.session.flush()

    async def _unfreeze_balance(
        self, user_id: UUID, ticker: str, amount: int
    ) -> None:
        """Unfreeze balance after order cancellation."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))

        if ticker == settings.base_instrument_ticker:
            user.balance += amount
        else:
            inventory = await self.inventory_repo.get_by_user_and_ticker(
                user_id, ticker
            )
            if inventory:
                inventory.quantity += amount

        await self.session.flush()

