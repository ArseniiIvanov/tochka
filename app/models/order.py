"""Order model."""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DirectionEnum(PyEnum):
    """Order direction enumeration."""

    ASK = "ask"  # Sell order
    BID = "bid"  # Buy order


class OrderStatusEnum(PyEnum):
    """Order status enumeration."""

    NEW = "NEW"
    EXECUTED = "EXECUTED"
    PARTIALLY_EXECUTED = "PARTIALLY_EXECUTED"
    CANCELLED = "CANCELLED"


class Order(Base):
    """Order model for trading orders."""

    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    instrument_ticker = Column(
        String(10),
        ForeignKey("instruments.ticker", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount = Column(Integer, nullable=False)
    filled = Column(Integer, nullable=False, default=0)
    price = Column(Integer, nullable=True)  # None for market orders
    direction = Column(Enum(DirectionEnum), nullable=False, index=True)
    status = Column(Enum(OrderStatusEnum), default=OrderStatusEnum.NEW, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="orders")
    instrument = relationship("Instrument", back_populates="orders")

