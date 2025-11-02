"""Custom exceptions for the application."""
from typing import Optional


class BaseAppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or message
        super().__init__(self.message)


class NotFoundError(BaseAppException):
    """Resource not found exception."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            detail=f"{resource} with identifier '{identifier}' not found",
        )


class ValidationError(BaseAppException):
    """Validation error exception."""

    def __init__(self, message: str):
        super().__init__(message=message, status_code=422, detail=message)


class InsufficientBalanceError(BaseAppException):
    """Insufficient balance exception."""

    def __init__(self, ticker: str, required: float, available: float):
        super().__init__(
            message="Insufficient balance",
            status_code=400,
            detail=(
                f"Insufficient {ticker} balance. "
                f"Required: {required}, Available: {available}"
            ),
        )


class OrderExecutionError(BaseAppException):
    """Order execution error exception."""

    def __init__(self, message: str):
        super().__init__(message=message, status_code=422, detail=message)


class PermissionDeniedError(BaseAppException):
    """Permission denied exception."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, status_code=403, detail=message)

