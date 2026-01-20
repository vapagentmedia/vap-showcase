"""
VAP Webhook Helpers
Utilities for webhook signature verification
"""

import hmac
import hashlib
import json
import time
from typing import Union


def verify_webhook_signature(
    payload: Union[dict, str, bytes],
    signature: str,
    timestamp: Union[str, int],
    secret: str,
    max_age_seconds: int = 300,
) -> bool:
    """
    Verify VAP webhook signature.

    VAP sends webhooks with HMAC-SHA256 signatures for security.
    Use this function to verify that webhooks are authentic.

    Args:
        payload: Webhook payload (dict, JSON string, or bytes)
        signature: Value from X-VAP-Signature header
        timestamp: Value from X-VAP-Timestamp header
        secret: Your webhook secret (from webhook registration)
        max_age_seconds: Maximum age of signature (default: 5 minutes)

    Returns:
        True if signature is valid and not expired, False otherwise

    Example:
        from vap_client import verify_webhook_signature

        @app.post("/webhooks/vape")
        def handle_webhook(request):
            is_valid = verify_webhook_signature(
                payload=request.body,
                signature=request.headers["X-VAP-Signature"],
                timestamp=request.headers["X-VAP-Timestamp"],
                secret="your_webhook_secret"
            )

            if not is_valid:
                return {"error": "Invalid signature"}, 401

            # Process webhook...
    """
    try:
        # Convert timestamp to int
        ts = int(timestamp)

        # Check timestamp age
        current_time = int(time.time())
        if abs(current_time - ts) > max_age_seconds:
            return False

        # Normalize payload to JSON string
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        if isinstance(payload, dict):
            payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        else:
            # Try to parse and re-serialize for consistent formatting
            try:
                parsed = json.loads(payload)
                payload_json = json.dumps(parsed, separators=(",", ":"), sort_keys=True)
            except:
                payload_json = payload

        # Create signed payload
        signed_payload = f"{ts}.{payload_json}"

        # Generate expected signature
        expected_signature = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison
        return hmac.compare_digest(signature, expected_signature)

    except (ValueError, TypeError, AttributeError):
        return False


def generate_webhook_signature(
    payload: Union[dict, str],
    secret: str,
    timestamp: int = None,
) -> tuple:
    """
    Generate webhook signature (for testing purposes).

    Args:
        payload: Webhook payload
        secret: Webhook secret
        timestamp: Unix timestamp (default: current time)

    Returns:
        Tuple of (signature, timestamp)

    Example:
        signature, timestamp = generate_webhook_signature(
            payload={"event": "test"},
            secret="your_secret"
        )
    """
    if timestamp is None:
        timestamp = int(time.time())

    # Normalize payload
    if isinstance(payload, dict):
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    else:
        try:
            parsed = json.loads(payload)
            payload_json = json.dumps(parsed, separators=(",", ":"), sort_keys=True)
        except:
            payload_json = payload

    # Create signed payload
    signed_payload = f"{timestamp}.{payload_json}"

    # Generate signature
    signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return signature, timestamp


class WebhookEvent:
    """
    Parsed webhook event.

    Usage:
        event = WebhookEvent.from_request(payload, signature, timestamp, secret)
        if event.is_valid:
            print(f"Event type: {event.event_type}")
            print(f"Data: {event.data}")
    """

    def __init__(
        self,
        payload: dict,
        is_valid: bool,
        event_type: str = None,
        timestamp: str = None,
    ):
        self.payload = payload
        self.is_valid = is_valid
        self.event_type = event_type or payload.get("event", "unknown")
        self.timestamp = timestamp or payload.get("timestamp")
        self.data = payload

    @classmethod
    def from_request(
        cls,
        payload: Union[dict, str, bytes],
        signature: str,
        timestamp: Union[str, int],
        secret: str,
        max_age_seconds: int = 300,
    ) -> "WebhookEvent":
        """
        Create WebhookEvent from request data.

        Args:
            payload: Request body
            signature: X-VAP-Signature header
            timestamp: X-VAP-Timestamp header
            secret: Your webhook secret
            max_age_seconds: Max signature age

        Returns:
            WebhookEvent with is_valid flag
        """
        # Verify signature
        is_valid = verify_webhook_signature(
            payload=payload,
            signature=signature,
            timestamp=timestamp,
            secret=secret,
            max_age_seconds=max_age_seconds,
        )

        # Parse payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except:
                payload = {"raw": payload}

        return cls(
            payload=payload,
            is_valid=is_valid,
            timestamp=str(timestamp),
        )

    def __repr__(self):
        return f"WebhookEvent(event_type={self.event_type!r}, is_valid={self.is_valid})"


# Webhook event types
WEBHOOK_EVENTS = {
    "generation.complete": "Image generation completed",
    "balance.low": "Account balance is low",
    "balance.depleted": "Account balance is depleted",
    "rate.limit.exceeded": "Rate limit exceeded",
    "test": "Test webhook",
}