"""
VAP Python SDK
Official Python client for VAP AI Image Generation API
"""

__version__ = "1.0.0"
__author__ = "VAP Team"

from .client import VAPEClient
from .async_client import AsyncVAPEClient
from .models import (
    GenerateResult,
    UpscaleResult,
    ValidateResult,
    HealthStatus,
    Balance,
    VideoResult,
    MusicResult,
    TaskResult,
    TaskListResult,
)
from .exceptions import (
    VAPEError,
    VAPEAuthenticationError,
    VAPEInsufficientBalanceError,
    VAPERateLimitError,
    VAPEValidationError,
    VAPEServerError,
    VAPEConnectionError,
    VAPETimeoutError,
)
from .webhooks import (
    verify_webhook_signature,
    generate_webhook_signature,
    WebhookEvent,
    WEBHOOK_EVENTS,
)

__all__ = [
    # Version
    "__version__",
    # Clients
    "VAPEClient",
    "AsyncVAPEClient",
    # Models
    "GenerateResult",
    "UpscaleResult",
    "ValidateResult",
    "HealthStatus",
    "Balance",
    "VideoResult",
    "MusicResult",
    "TaskResult",
    "TaskListResult",
    # Exceptions
    "VAPEError",
    "VAPEAuthenticationError",
    "VAPEInsufficientBalanceError",
    "VAPERateLimitError",
    "VAPEValidationError",
    "VAPEServerError",
    "VAPEConnectionError",
    "VAPETimeoutError",
    # Webhooks
    "verify_webhook_signature",
    "generate_webhook_signature",
    "WebhookEvent",
    "WEBHOOK_EVENTS",
]
