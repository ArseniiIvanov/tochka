"""FastAPI dependencies."""
import uuid
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.exceptions import NotFoundError
from app.models import Instrument, User
from app.repositories.instrument import InstrumentRepository
from app.repositories.user import UserRepository

settings = get_settings()
security = HTTPBearer(scheme_name="TOKEN", auto_error=False)


async def get_token_from_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """
    Extract token from request.

    Args:
        request: FastAPI request
        credentials: HTTPBearer credentials

    Returns:
        str: JWT token

    Raises:
        HTTPException: If token is missing
    """
    if credentials:
        return credentials.credentials

    # Fallback: try to get from Authorization header directly
    authorization: Optional[str] = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": settings.token_prefix},
        )

    try:
        prefix, token = authorization.split(" ", 1)
        if prefix != settings.token_prefix:
            raise ValueError("Invalid token prefix")
        return token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format",
            headers={"WWW-Authenticate": settings.token_prefix},
        ) from e


async def get_current_user(
    token: str = Depends(get_token_from_request),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        User: Authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    from app.core.security import decode_jwt_token

    try:
        payload = decode_jwt_token(token)
        user_id: Optional[str] = payload.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": settings.token_prefix},
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": settings.token_prefix},
        ) from e

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": settings.token_prefix},
        )

    return user


async def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    """
    Get current admin user.

    Args:
        user: Current authenticated user

    Returns:
        User: Admin user

    Raises:
        HTTPException: If user is not admin
    """
    from app.models import RoleEnum

    if user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. Admin access required.",
            headers={"WWW-Authenticate": settings.token_prefix},
        )
    return user


async def get_instrument_by_ticker(
    ticker: str,
    db: AsyncSession = Depends(get_db_session),
) -> Instrument:
    """
    Get instrument by ticker or raise 404.

    Args:
        ticker: Instrument ticker
        db: Database session

    Returns:
        Instrument: Found instrument

    Raises:
        HTTPException: If instrument not found
    """
    repo = InstrumentRepository(db)
    instrument = await repo.get_by_ticker(ticker)
    if not instrument:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument with ticker '{ticker}' not found",
        )
    return instrument


async def get_user_by_id(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Get user by ID or raise 404.

    Args:
        user_id: User UUID
        db: Database session

    Returns:
        User: Found user

    Raises:
        HTTPException: If user not found
    """
    repo = UserRepository(db)
    user = await repo.get_by_id(str(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found",
        )
    return user



