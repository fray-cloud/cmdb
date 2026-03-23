"""Unit tests for the RouteTarget aggregate root."""

from uuid import uuid4

import pytest
from ipam.route_target import RouteTarget, RouteTargetCreated, RouteTargetDeleted, RouteTargetUpdated
from pydantic import ValidationError
from shared.domain.exceptions import BusinessRuleViolationError


def make_rt(
    name: str = "65000:100",
    tenant_id=None,
    description: str = "",
    custom_fields: dict | None = None,
    tags: list | None = None,
) -> RouteTarget:
    return RouteTarget.create(
        name=name,
        tenant_id=tenant_id,
        description=description,
        custom_fields=custom_fields,
        tags=tags,
    )


class TestRouteTargetCreate:
    def test_create_returns_instance(self):
        assert isinstance(make_rt(), RouteTarget)

    def test_create_sets_name(self):
        rt = make_rt(name="65001:200")
        assert rt.name.rd == "65001:200"

    def test_create_with_tenant(self):
        tid = uuid4()
        assert make_rt(tenant_id=tid).tenant_id == tid

    def test_create_with_custom_fields_and_tags(self):
        tag_id = uuid4()
        rt = make_rt(custom_fields={"note": "test"}, tags=[tag_id])
        assert rt.custom_fields == {"note": "test"}
        assert rt.tags == [tag_id]

    def test_create_emits_event(self):
        events = make_rt().collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], RouteTargetCreated)

    def test_create_version_is_1(self):
        assert make_rt().version == 1

    def test_create_invalid_name_raises_error(self):
        with pytest.raises((ValueError, ValidationError)):
            make_rt(name="invalid")


class TestRouteTargetUpdate:
    def test_update_description(self):
        rt = make_rt()
        rt.collect_uncommitted_events()
        rt.update(description="updated")
        assert rt.description == "updated"

    def test_update_produces_event(self):
        rt = make_rt()
        rt.collect_uncommitted_events()
        rt.update(description="new")
        events = rt.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], RouteTargetUpdated)

    def test_update_deleted_raises_error(self):
        rt = make_rt()
        rt.collect_uncommitted_events()
        rt.delete()
        with pytest.raises(BusinessRuleViolationError, match="deleted"):
            rt.update(description="fail")


class TestRouteTargetDelete:
    def test_delete_marks_deleted(self):
        rt = make_rt()
        rt.collect_uncommitted_events()
        rt.delete()
        assert rt._deleted is True

    def test_delete_produces_event(self):
        rt = make_rt()
        rt.collect_uncommitted_events()
        rt.delete()
        events = rt.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], RouteTargetDeleted)

    def test_double_delete_raises_error(self):
        rt = make_rt()
        rt.collect_uncommitted_events()
        rt.delete()
        with pytest.raises(BusinessRuleViolationError, match="already deleted"):
            rt.delete()


class TestRouteTargetLoadFromHistory:
    def test_load_from_history_restores_state(self):
        original = make_rt(name="65000:1", description="orig")
        original.update(description="updated")
        original.delete()
        events = original.collect_uncommitted_events()

        restored = RouteTarget()
        restored.load_from_history(events)
        assert restored.name.rd == "65000:1"
        assert restored.description == "updated"
        assert restored._deleted is True
        assert restored.version == 3


class TestRouteTargetSnapshot:
    def test_snapshot_roundtrip(self):
        tag_id = uuid4()
        tid = uuid4()
        rt = make_rt(name="65000:50", tenant_id=tid, description="test", custom_fields={"k": "v"}, tags=[tag_id])
        snap = rt.to_snapshot()
        restored = RouteTarget.from_snapshot(rt.id, snap, rt.version)
        assert restored.name.rd == "65000:50"
        assert restored.tenant_id == tid
        assert restored.description == "test"
        assert restored.custom_fields == {"k": "v"}
        assert restored.tags == [tag_id]
        assert restored.id == rt.id
