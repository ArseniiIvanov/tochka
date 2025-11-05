"""Admin schemas."""
from uuid import UUID

from pydantic import BaseModel, Field, constr, field_validator


class InstrumentCreateRequest(BaseModel):
    """Create instrument request."""

    name: constr(min_length=1) = Field(..., description="Instrument name")
    ticker: constr(pattern="^[A-Z]{2,10}$") = Field(
        ..., description="Instrument ticker (2-10 uppercase letters)"
    )


class BalanceChangeRequest(BaseModel):
    """Balance change request."""

    user_id: UUID = Field(..., description="User ID")
    ticker: constr(min_length=2, max_length=10, pattern="^[A-Z]+$") = Field(
        ..., description="Instrument ticker"
    )
    amount: int = Field(..., description="Amount to change", gt=0)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: int) -> int:
        """Validate amount."""
        if v <= 0:
            raise ValueError("Amount must be > 0")
        return v


class SuccessResponse(BaseModel):
    """Success response."""

    success: bool = True

