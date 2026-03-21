from uuid import uuid4

from webhook.domain.webhook import Webhook


class TestWebhookMatchesEvent:
    def test_exact_match(self):
        wh = Webhook(
            name="test", url="http://example.com", secret="s", event_types=["ipam.domain.events.PrefixCreated"]
        )
        assert wh.matches_event("ipam.domain.events.PrefixCreated") is True

    def test_no_match(self):
        wh = Webhook(
            name="test", url="http://example.com", secret="s", event_types=["ipam.domain.events.PrefixCreated"]
        )
        assert wh.matches_event("ipam.domain.events.PrefixDeleted") is False

    def test_wildcard_matches_all(self):
        wh = Webhook(name="test", url="http://example.com", secret="s", event_types=["*"])
        assert wh.matches_event("anything.here") is True

    def test_inactive_does_not_match(self):
        wh = Webhook(name="test", url="http://example.com", secret="s", event_types=["*"], is_active=False)
        assert wh.matches_event("anything") is False

    def test_multiple_event_types(self):
        wh = Webhook(name="test", url="http://example.com", secret="s", event_types=["a.Created", "a.Updated"])
        assert wh.matches_event("a.Created") is True
        assert wh.matches_event("a.Updated") is True
        assert wh.matches_event("a.Deleted") is False

    def test_empty_event_types_matches_nothing(self):
        wh = Webhook(name="test", url="http://example.com", secret="s", event_types=[])
        assert wh.matches_event("anything") is False


class TestWebhookActivation:
    def test_deactivate(self):
        wh = Webhook(name="test", url="http://example.com", secret="s", event_types=["*"])
        wh.deactivate()
        assert wh.is_active is False

    def test_activate(self):
        wh = Webhook(name="test", url="http://example.com", secret="s", event_types=["*"], is_active=False)
        wh.activate()
        assert wh.is_active is True

    def test_deactivate_updates_timestamp(self):
        wh = Webhook(name="test", url="http://example.com", secret="s", event_types=["*"])
        old_ts = wh.updated_at
        wh.deactivate()
        assert wh.updated_at >= old_ts


class TestWebhookCreation:
    def test_default_values(self):
        wh = Webhook(name="test", url="http://example.com", secret="s", event_types=["*"])
        assert wh.is_active is True
        assert wh.tenant_id is None
        assert wh.description == ""
        assert wh.id is not None

    def test_with_tenant(self):
        tid = uuid4()
        wh = Webhook(name="test", url="http://example.com", secret="s", event_types=["*"], tenant_id=tid)
        assert wh.tenant_id == tid
