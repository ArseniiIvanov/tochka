"""Order schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, constr, conint, field_validator


class CreateOrderRequest(BaseModel):
    """Create order request."""

    direction: str = Field(..., description="Order direction: BUY or SELL")
    ticker: constr(min_length=2, max_length=10, pattern="^[A-Z]+$") = Field(
        ..., description="Instrument ticker"
    )
    qty: conint(gt=0) = Field(..., description="Quantity (must be > 0)")
    price: Optional[conint(gt=0)] = Field(
        None, description="Price per unit (None for market orders)"
    )

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        """Validate direction."""
        if v.upper() not in ["BUY", "SELL"]:
            raise ValueError("Direction must be 'BUY' or 'SELL'")
        return v.upper()


class OrderResponse(BaseModel):
    """Order response."""

    id: UUID
    status: str
    user_id: UUID
    timestamp: str
    body: dict
    filled: int

    class Config:
        from_attributes = True

