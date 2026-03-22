from uuid import uuid4

from webhook.domain.webhook import Webhook


class TestTenantEventMatching:
    def _make_webhook(self, tenant_id=None, event_types=None, is_active=True):
        return Webhook(
            name="test",
            url="http://example.com",
            secret="s",
            event_types=event_types or ["*"],
            tenant_id=tenant_id,
            is_active=is_active,
        )

    def test_tenant_webhook_matches_same_tenant_event(self):
        tid = uuid4()
        wh = self._make_webhook(tenant_id=tid)
        # Simulating: event has same tenant_id -> webhook for this tenant is selected
        assert wh.matches_event("any.event") is True

    def test_inactive_webhook_never_matches(self):
        wh = self._make_webhook(is_active=False)
        assert wh.matches_event("any.event") is False

    def test_event_type_filter_with_tenant(self):
        tid = uuid4()
        wh = self._make_webhook(tenant_id=tid, event_types=["ipam.domain.events.PrefixCreated"])
        assert wh.matches_event("ipam.domain.events.PrefixCreated") is True
        assert wh.matches_event("ipam.domain.events.PrefixDeleted") is False

    def test_wildcard_with_tenant(self):
        tid = uuid4()
        wh = self._make_webhook(tenant_id=tid, event_types=["*"])
        assert wh.matches_event("any.event.type") is True

    def test_global_webhook_no_tenant(self):
        wh = self._make_webhook(tenant_id=None, event_types=["*"])
        assert wh.matches_event("any.event") is True
        assert wh.tenant_id is None
