"""Authentication schemas."""
from pydantic import BaseModel, Field, constr


class UserAuth(BaseModel):
    """User registration request."""

    name: constr(min_length=3) = Field(..., description="User name (min 3 characters)")


class UserResponse(BaseModel):
    """User response."""

    name: str
    id: str
    role: str
    api_key: str

    class Config:
        from_attributes = True

