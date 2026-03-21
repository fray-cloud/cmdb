import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class DeliveryResult:
    success: bool
    status_code: int | None
    response_body: str | None
    error_message: str | None
    duration_ms: int


class WebhookDeliveryService:
    def __init__(self, timeout: float = 10.0) -> None:
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        self._client = httpx.AsyncClient(timeout=self._timeout)

    async def stop(self) -> None:
        if self._client:
            await self._client.aclose()

    async def deliver(self, url: str, payload: dict, secret: str, event_type: str, webhook_id: str) -> DeliveryResult:
        body = json.dumps(payload, default=str)
        signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": event_type,
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-ID": webhook_id,
        }
        start_time = time.monotonic()
        try:
            resp = await self._client.post(url, content=body, headers=headers)
            duration = int((time.monotonic() - start_time) * 1000)
            return DeliveryResult(
                success=200 <= resp.status_code < 300,
                status_code=resp.status_code,
                response_body=resp.text[:4096] if resp.text else None,
                error_message=None if resp.status_code < 300 else f"HTTP {resp.status_code}",
                duration_ms=duration,
            )
        except Exception as e:
            duration = int((time.monotonic() - start_time) * 1000)
            return DeliveryResult(
                success=False,
                status_code=None,
                response_body=None,
                error_message=str(e),
                duration_ms=duration,
            )
