import hashlib
import hmac
import json

import httpx
import pytest
import pytest_asyncio
from webhook.infrastructure.webhook_delivery import WebhookDeliveryService


@pytest_asyncio.fixture
async def delivery_service():
    svc = WebhookDeliveryService(timeout=5.0)
    await svc.start()
    yield svc
    await svc.stop()


class TestWebhookDeliveryService:
    @pytest.mark.asyncio
    async def test_successful_delivery(self, delivery_service, httpx_mock):
        httpx_mock.add_response(status_code=200, text="OK")
        result = await delivery_service.deliver(
            "http://example.com/hook", {"key": "value"}, "secret123", "test.event", "wh-1"
        )
        assert result.success is True
        assert result.status_code == 200
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_failed_delivery(self, delivery_service, httpx_mock):
        httpx_mock.add_response(status_code=500, text="Error")
        result = await delivery_service.deliver(
            "http://example.com/hook", {"key": "value"}, "secret123", "test.event", "wh-1"
        )
        assert result.success is False
        assert result.status_code == 500

    @pytest.mark.asyncio
    async def test_timeout_delivery(self, delivery_service, httpx_mock):
        httpx_mock.add_exception(httpx.ReadTimeout("timeout"))
        result = await delivery_service.deliver("http://example.com/hook", {}, "secret", "test", "wh-1")
        assert result.success is False
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_hmac_signature(self, delivery_service, httpx_mock):
        httpx_mock.add_response(status_code=200)
        payload = {"test": "data"}
        secret = "my-secret"
        await delivery_service.deliver("http://example.com/hook", payload, secret, "test.event", "wh-1")
        request = httpx_mock.get_request()
        body = json.dumps(payload, default=str)
        expected_sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        assert request.headers["X-Webhook-Signature"] == f"sha256={expected_sig}"
        assert request.headers["X-Webhook-Event"] == "test.event"
        assert request.headers["X-Webhook-ID"] == "wh-1"
