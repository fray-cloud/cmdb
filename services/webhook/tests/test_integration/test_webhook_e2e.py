"""Webhook E2E tests: event matching + delivery via httpx_mock.

No Docker required — these run as regular (non-integration) tests.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from uuid import uuid4

import pytest_asyncio
from webhook.domain.webhook import Webhook
from webhook.infrastructure.webhook_delivery import WebhookDeliveryService

# ---------------------------------------------------------------------------
# TestWebhookEventMatching
# ---------------------------------------------------------------------------


class TestWebhookEventMatching:
    """Webhook.matches_event() returns correct results based on event_types and is_active."""

    def test_matching_event_returns_true(self) -> None:
        webhook = Webhook(
            name="test-hook",
            url="http://example.com/hook",
            secret="s3cret",
            event_types=["PrefixCreated"],
        )
        assert webhook.matches_event("PrefixCreated") is True

    def test_non_matching_event_returns_false(self) -> None:
        webhook = Webhook(
            name="test-hook",
            url="http://example.com/hook",
            secret="s3cret",
            event_types=["PrefixCreated"],
        )
        assert webhook.matches_event("VLANCreated") is False

    def test_inactive_webhook_does_not_match(self) -> None:
        webhook = Webhook(
            name="test-hook",
            url="http://example.com/hook",
            secret="s3cret",
            event_types=["PrefixCreated"],
            is_active=False,
        )
        assert webhook.matches_event("PrefixCreated") is False

    def test_wildcard_matches_any_event(self) -> None:
        webhook = Webhook(
            name="catch-all",
            url="http://example.com/hook",
            secret="s3cret",
            event_types=["*"],
        )
        assert webhook.matches_event("PrefixCreated") is True
        assert webhook.matches_event("VLANDeleted") is True

    def test_deactivated_webhook_does_not_match(self) -> None:
        webhook = Webhook(
            name="test-hook",
            url="http://example.com/hook",
            secret="s3cret",
            event_types=["PrefixCreated"],
        )
        webhook.deactivate()
        assert webhook.matches_event("PrefixCreated") is False

    def test_reactivated_webhook_matches_again(self) -> None:
        webhook = Webhook(
            name="test-hook",
            url="http://example.com/hook",
            secret="s3cret",
            event_types=["PrefixCreated"],
        )
        webhook.deactivate()
        webhook.activate()
        assert webhook.matches_event("PrefixCreated") is True

    def test_multiple_event_types(self) -> None:
        webhook = Webhook(
            name="multi-hook",
            url="http://example.com/hook",
            secret="s3cret",
            event_types=["PrefixCreated", "PrefixDeleted"],
        )
        assert webhook.matches_event("PrefixCreated") is True
        assert webhook.matches_event("PrefixDeleted") is True
        assert webhook.matches_event("PrefixUpdated") is False


# ---------------------------------------------------------------------------
# TestWebhookDeliveryE2E
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def delivery_service():
    svc = WebhookDeliveryService(timeout=5.0)
    await svc.start()
    yield svc
    await svc.stop()


class TestWebhookDeliveryE2E:
    """Create webhook -> deliver event -> verify HTTP POST sent with correct headers."""

    async def test_deliver_event_sends_http_post(self, delivery_service, httpx_mock) -> None:
        httpx_mock.add_response(status_code=200, text="OK")

        webhook = Webhook(
            name="delivery-test",
            url="http://example.com/hook",
            secret="my-secret",
            event_types=["PrefixCreated"],
        )

        payload = {
            "event_type": "PrefixCreated",
            "aggregate_id": str(uuid4()),
            "network": "10.0.0.0/8",
        }

        result = await delivery_service.deliver(
            url=webhook.url,
            payload=payload,
            secret=webhook.secret,
            event_type="PrefixCreated",
            webhook_id=str(webhook.id),
        )

        assert result.success is True
        assert result.status_code == 200

        # Verify that an HTTP request was actually sent
        request = httpx_mock.get_request()
        assert request is not None
        assert request.method == "POST"

    async def test_deliver_event_has_hmac_signature(self, delivery_service, httpx_mock) -> None:
        httpx_mock.add_response(status_code=200)

        webhook = Webhook(
            name="sig-test",
            url="http://example.com/hook",
            secret="hmac-secret-key",
            event_types=["PrefixCreated"],
        )

        payload = {"event_type": "PrefixCreated", "network": "192.168.1.0/24"}

        await delivery_service.deliver(
            url=webhook.url,
            payload=payload,
            secret=webhook.secret,
            event_type="PrefixCreated",
            webhook_id=str(webhook.id),
        )

        request = httpx_mock.get_request()
        assert "X-Webhook-Signature" in request.headers

        # Verify the HMAC signature is correct
        body = json.dumps(payload, default=str)
        expected_sig = hmac.new(webhook.secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        assert request.headers["X-Webhook-Signature"] == f"sha256={expected_sig}"

    async def test_deliver_event_contains_event_data(self, delivery_service, httpx_mock) -> None:
        httpx_mock.add_response(status_code=200)

        webhook = Webhook(
            name="payload-test",
            url="http://example.com/hook",
            secret="test-secret",
            event_types=["PrefixCreated"],
        )

        agg_id = str(uuid4())
        payload = {
            "event_type": "PrefixCreated",
            "aggregate_id": agg_id,
            "network": "172.16.0.0/12",
            "status": "active",
        }

        await delivery_service.deliver(
            url=webhook.url,
            payload=payload,
            secret=webhook.secret,
            event_type="PrefixCreated",
            webhook_id=str(webhook.id),
        )

        request = httpx_mock.get_request()

        # Verify payload was sent as JSON body
        sent_body = json.loads(request.content.decode())
        assert sent_body["event_type"] == "PrefixCreated"
        assert sent_body["aggregate_id"] == agg_id
        assert sent_body["network"] == "172.16.0.0/12"

        # Verify headers contain event metadata
        assert request.headers["X-Webhook-Event"] == "PrefixCreated"
        assert request.headers["X-Webhook-ID"] == str(webhook.id)
        assert request.headers["Content-Type"] == "application/json"
