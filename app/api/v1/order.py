"""Order API endpoints."""
from datetime import timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user
from app.core.exceptions import OrderExecutionError
from app.models import User, OrderStatusEnum, DirectionEnum
from app.repositories.order import OrderRepository
from app.services.order_service import OrderService
from app.api.v1.schemas import CreateOrderRequest, OrderResponse, SuccessResponse

router = APIRouter()


def _format_order_response(order) -> OrderResponse:
    """Format order for response."""
    datetime_utc = order.created_at.astimezone(timezone.utc)
    formatted_timestamp = datetime_utc.isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )

    return OrderResponse(
        id=order.id,
        status=order.status.value,
        user_id=order.user_id,
        timestamp=formatted_timestamp,
        body={
            "direction": "BUY" if order.direction == DirectionEnum.BID else "SELL",
            "ticker": order.instrument_ticker,
            "qty": order.amount + order.filled,
            "price": order.price,
        },
        filled=order.filled,
    )


@router.get("", response_model=list[OrderResponse])
async def get_orders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get all orders for current user.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        List[OrderResponse]: List of user orders
    """
    order_repo = OrderRepository(db)
    orders = await order_repo.get_user_orders(user.id)
    return [_format_order_response(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get order by ID.

    Args:
        order_id: Order ID
        user: Current authenticated user
        db: Database session

    Returns:
        OrderResponse: Order data

    Raises:
        HTTPException: If order not found or doesn't belong to user
    """
    order_repo = OrderRepository(db)
    order = await order_repo.get_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    if order.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Order does not belong to user",
        )

    return _format_order_response(order)


@router.post("", response_model=dict)
async def create_order(
    order_data: CreateOrderRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Create new order.

    Args:
        order_data: Order data
        user: Current authenticated user
        db: Database session

    Returns:
        dict: Success status and order ID

    Raises:
        HTTPException: If instrument not found or order execution fails
    """
    from app.repositories.instrument import InstrumentRepository

    instrument_repo = InstrumentRepository(db)
    instrument = await instrument_repo.get_by_ticker(order_data.ticker)
    if not instrument:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument with ticker '{order_data.ticker}' not found",
        )

    order_service = OrderService(db)

    try:
        if order_data.direction == "BUY":
            if order_data.price:
                order = await order_service.create_limit_buy_order(
                    order_data.ticker, order_data.qty, order_data.price, user
                )
            else:
                order = await order_service.create_market_buy_order(
                    order_data.ticker, order_data.qty, user
                )
        else:  # SELL
            if order_data.price:
                order = await order_service.create_limit_sell_order(
                    order_data.ticker, order_data.qty, order_data.price, user
                )
            else:
                order = await order_service.create_market_sell_order(
                    order_data.ticker, order_data.qty, user
                )

        await db.commit()

        if order.status == OrderStatusEnum.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="ORDER CANCELLED",
            )

        return {"success": True, "order_id": str(order.id)}

    except OrderExecutionError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e


@router.delete("/{order_id}", response_model=SuccessResponse)
async def cancel_order(
    order_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Cancel order.

    Args:
        order_id: Order ID
        user: Current authenticated user
        db: Database session

    Returns:
        SuccessResponse: Success status

    Raises:
        HTTPException: If order not found or cannot be cancelled
    """
    order_service = OrderService(db)

    try:
        await order_service.cancel_order(order_id, user.id)
        await db.commit()
        return SuccessResponse()
    except OrderExecutionError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

