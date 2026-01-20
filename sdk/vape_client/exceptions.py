"""
VAP SDK Exceptions
Hierarchical exception classes for error handling
"""


class VAPEError(Exception):
    """Base exception for all VAP errors."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response or {}
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class VAPEAuthenticationError(VAPEError):
    """Raised when authentication fails (401)."""
    pass


class VAPEInsufficientBalanceError(VAPEError):
    """Raised when balance is insufficient (402)."""

    def __init__(self, message: str, balance: float = None, required: float = None, **kwargs):
        super().__init__(message, **kwargs)
        self.balance = balance
        self.required = required


class VAPERateLimitError(VAPEError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(self, message: str, retry_after: int = None, limit_type: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after
        self.limit_type = limit_type


class VAPEValidationError(VAPEError):
    """Raised when request validation fails (400)."""

    def __init__(self, message: str, errors: list = None, **kwargs):
        super().__init__(message, **kwargs)
        self.errors = errors or []


class VAPEServerError(VAPEError):
    """Raised when server encounters an error (5xx)."""
    pass


class VAPEConnectionError(VAPEError):
    """Raised when connection to API fails."""
    pass


class VAPETimeoutError(VAPEError):
    """Raised when request times out."""
    pass