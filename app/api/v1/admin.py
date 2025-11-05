"""Admin API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_admin, get_instrument_by_ticker, get_user_by_id
from app.models import User, Instrument
from app.repositories.instrument import InstrumentRepository
from app.services.balance_service import BalanceService
from app.api.v1.schemas import (
    InstrumentCreateRequest,
    BalanceChangeRequest,
    SuccessResponse,
    UserResponse,
)

router = APIRouter()


@router.post("/instrument", response_model=SuccessResponse)
async def create_instrument(
    instrument_data: InstrumentCreateRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Create new instrument (admin only).

    Args:
        instrument_data: Instrument data
        admin: Current admin user
        db: Database session

    Returns:
        SuccessResponse: Success status

    Raises:
        HTTPException: If instrument already exists
    """
    repo = InstrumentRepository(db)
    existing = await repo.get_by_ticker(instrument_data.ticker)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Instrument with ticker '{instrument_data.ticker}' already exists",
        )

    await repo.create_instrument(instrument_data.name, instrument_data.ticker)
    return SuccessResponse()


@router.post("/balance/deposit", response_model=SuccessResponse)
async def deposit_balance(
    balance_change: BalanceChangeRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Deposit balance to user (admin only).

    Args:
        balance_change: Balance change data
        admin: Current admin user
        db: Database session

    Returns:
        SuccessResponse: Success status

    Raises:
        HTTPException: If user or instrument not found
    """
    balance_service = BalanceService(db)
    await balance_service.change_balance(
        balance_change.user_id, balance_change.ticker, balance_change.amount
    )
    return SuccessResponse()


@router.post("/balance/withdraw", response_model=SuccessResponse)
async def withdraw_balance(
    balance_change: BalanceChangeRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Withdraw balance from user (admin only).

    Args:
        balance_change: Balance change data
        admin: Current admin user
        db: Database session

    Returns:
        SuccessResponse: Success status

    Raises:
        HTTPException: If user or instrument not found, or insufficient balance
    """
    balance_service = BalanceService(db)
    await balance_service.change_balance(
        balance_change.user_id, balance_change.ticker, -balance_change.amount
    )
    return SuccessResponse()


@router.delete("/user/{user_id}", response_model=UserResponse)
async def delete_user(
    user: User = Depends(get_user_by_id),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Delete user (admin only).

    Args:
        user: User to delete (from dependency)
        admin: Current admin user
        db: Database session

    Returns:
        UserResponse: Deleted user data
    """
    from app.repositories.user import UserRepository

    repo = UserRepository(db)
    await repo.delete(user)
    await db.commit()

    return UserResponse(
        name=user.name,
        id=str(user.id),
        role=user.role.value,
        api_key=user.api_key or "",
    )


@router.delete("/instrument/{ticker}", response_model=SuccessResponse)
async def delete_instrument(
    instrument: Instrument = Depends(get_instrument_by_ticker),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Delete instrument (admin only).

    Args:
        instrument: Instrument to delete (from dependency)
        admin: Current admin user
        db: Database session

    Returns:
        SuccessResponse: Success status
    """
    repo = InstrumentRepository(db)
    await repo.delete(instrument)
    await db.commit()
    return SuccessResponse()

