"""API v1 router."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import admin, order, public
from app.core.database import get_db_session
from app.core.dependencies import get_current_user
from app.models import User
from app.services.balance_service import BalanceService

router = APIRouter()

router.include_router(public.router, prefix="/public", tags=["public"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
router.include_router(order.router, prefix="/order", tags=["order"])


@router.get("/balance")
async def get_balance(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get user balance including all instruments and frozen amounts.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        dict: Balance dictionary with ticker as key
    """
    balance_service = BalanceService(db)
    balance = await balance_service.get_user_balance(user.id)
    return balance

