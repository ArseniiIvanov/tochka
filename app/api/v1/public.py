"""Public API endpoints."""
from collections import defaultdict
from datetime import timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_instrument_by_ticker
from app.core.security import create_access_token
from app.models import Instrument, DirectionEnum
from app.repositories.instrument import InstrumentRepository
from app.repositories.order import OrderRepository
from app.repositories.transaction import TransactionRepository
from app.repositories.user import UserRepository
from app.api.v1.schemas import (
    UserAuth,
    UserResponse,
    InstrumentResponse,
    OrderbookResponse,
    OrderbookLevel,
    TransactionResponse,
)

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserAuth,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Register new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        UserResponse: Created user with API key
    """
    user_repo = UserRepository(db)
    user = await user_repo.create_user(user_data.name)

    # Delete all orders (as per original implementation)
    order_repo = OrderRepository(db)

    token_data = {
        "name": user.name,
        "id": str(user.id),
        "role": user.role.value,
    }
    token = create_access_token(token_data)

    return UserResponse(
        name=user.name,
        id=str(user.id),
        role=user.role.value,
        api_key=token,
    )


@router.get("/instrument", response_model=list[InstrumentResponse])
async def get_instruments(
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get all instruments.

    Args:
        db: Database session

    Returns:
        List[InstrumentResponse]: List of instruments
    """
    repo = InstrumentRepository(db)
    instruments = await repo.get_all()
    return [
        InstrumentResponse(name=i.name, ticker=i.ticker) for i in instruments
    ]


@router.get("/orderbook/{ticker}", response_model=OrderbookResponse)
async def get_orderbook(
    instrument: Instrument = Depends(get_instrument_by_ticker),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of levels"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get orderbook for instrument.

    Args:
        instrument: Instrument (from dependency)
        limit: Maximum number of levels per side
        db: Database session

    Returns:
        OrderbookResponse: Orderbook with bid and ask levels
    """
    order_repo = OrderRepository(db)

    async def aggregate_orders(direction: DirectionEnum):
        orders = await order_repo.get_orders(instrument.ticker, direction, limit=limit)
        aggregated = defaultdict(int)
        for order in orders:
            aggregated[order.price] += order.amount
        return [
            OrderbookLevel(price=price, qty=qty)
            for price, qty in sorted(
                aggregated.items(), reverse=(direction == DirectionEnum.BID)
            )
        ]

    bid_levels = await aggregate_orders(DirectionEnum.BID)
    ask_levels = await aggregate_orders(DirectionEnum.ASK)

    return OrderbookResponse(bid_levels=bid_levels, ask_levels=ask_levels)


@router.get("/transactions/{ticker}", response_model=list[TransactionResponse])
async def get_transactions(
    instrument: Instrument = Depends(get_instrument_by_ticker),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of transactions"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get recent transactions for instrument.

    Args:
        instrument: Instrument (from dependency)
        limit: Maximum number of transactions
        db: Database session

    Returns:
        List[TransactionResponse]: List of transactions
    """
    repo = TransactionRepository(db)
    transactions = await repo.get_by_ticker(instrument.ticker, limit=limit)

    return [
        TransactionResponse(
            ticker=t.instrument_ticker,
            amount=t.amount,
            price=t.price,
            timestamp=t.timestamp.astimezone(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
        )
        for t in transactions
    ]

