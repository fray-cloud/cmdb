from uuid import uuid4

from webhook.domain.webhook_log import WebhookEventLog


class TestWebhookEventLog:
    def test_create_log(self):
        log = WebhookEventLog(
            webhook_id=uuid4(),
            event_type="test",
            event_id="123",
            request_url="http://example.com",
            request_body="{}",
        )
        assert log.success is False
        assert log.attempt == 1
        assert log.id is not None

    def test_create_successful_log(self):
        log = WebhookEventLog(
            webhook_id=uuid4(),
            event_type="test",
            event_id="123",
            request_url="http://example.com",
            request_body="{}",
            response_status=200,
            success=True,
            duration_ms=50,
        )
        assert log.success is True
        assert log.duration_ms == 50
