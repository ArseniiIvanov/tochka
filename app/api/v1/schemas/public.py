"""Public API schemas."""
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class InstrumentResponse(BaseModel):
    """Instrument response."""

    name: str
    ticker: str

    class Config:
        from_attributes = True


class OrderbookLevel(BaseModel):
    """Orderbook level."""

    price: int
    qty: int


class OrderbookResponse(BaseModel):
    """Orderbook response."""

    bid_levels: List[OrderbookLevel] = Field(..., description="Buy orders")
    ask_levels: List[OrderbookLevel] = Field(..., description="Sell orders")


class TransactionResponse(BaseModel):
    """Transaction response."""

    ticker: str
    amount: float
    price: float
    timestamp: str

    class Config:
        from_attributes = True

