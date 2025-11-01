"""Instrument model."""
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Instrument(Base):
    """Instrument model for trading assets."""

    __tablename__ = "instruments"

    ticker = Column(String(10), primary_key=True, unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)

    # Relationships
    inventories = relationship(
        "UserInventory",
        back_populates="instrument",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    orders = relationship(
        "Order",
        back_populates="instrument",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    transactions = relationship("Transaction", back_populates="instrument")

