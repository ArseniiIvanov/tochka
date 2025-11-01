"""User and inventory models."""
import uuid
from enum import Enum as PyEnum

from sqlalchemy import Column, Float, ForeignKey, String, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class RoleEnum(PyEnum):
    """User role enumeration."""

    USER = "user"
    ADMIN = "admin"


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    role = Column(Enum(RoleEnum), default=RoleEnum.USER, nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    api_key = Column(String, nullable=True, index=True)

    # Relationships
    orders = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    transactions_sent = relationship(
        "Transaction",
        foreign_keys="Transaction.user_from_id",
        back_populates="user_from",
    )
    transactions_received = relationship(
        "Transaction",
        foreign_keys="Transaction.user_to_id",
        back_populates="user_to",
    )
    inventory = relationship(
        "UserInventory",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class UserInventory(Base):
    """User inventory model for storing instrument quantities."""

    __tablename__ = "user_inventories"

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
    quantity = Column(Float, nullable=False, default=0.0)

    # Relationships
    user = relationship("User", back_populates="inventory")
    instrument = relationship("Instrument", back_populates="inventories")

