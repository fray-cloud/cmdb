"""Unit tests for the VLANGroup aggregate root."""

from uuid import uuid4

import pytest
from ipam.vlan_group.domain.events import VLANGroupCreated, VLANGroupDeleted, VLANGroupUpdated
from ipam.vlan_group.domain.vlan_group import VLANGroup
from shared.domain.exceptions import BusinessRuleViolationError


def make_vlan_group(
    name: str = "Default",
    slug: str = "default",
    min_vid: int = 1,
    max_vid: int = 4094,
    tenant_id=None,
    description: str = "",
    custom_fields: dict | None = None,
    tags: list | None = None,
) -> VLANGroup:
    return VLANGroup.create(
        name=name,
        slug=slug,
        min_vid=min_vid,
        max_vid=max_vid,
        tenant_id=tenant_id,
        description=description,
        custom_fields=custom_fields,
        tags=tags,
    )


class TestVLANGroupCreate:
    def test_create_returns_instance(self):
        assert isinstance(make_vlan_group(), VLANGroup)

    def test_create_sets_fields(self):
        vg = make_vlan_group(name="Test", slug="test", min_vid=100, max_vid=200)
        assert vg.name == "Test"
        assert vg.slug == "test"
        assert vg.min_vid == 100
        assert vg.max_vid == 200

    def test_create_emits_event(self):
        events = make_vlan_group().collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], VLANGroupCreated)

    def test_create_version_is_1(self):
        assert make_vlan_group().version == 1

    def test_create_invalid_min_vid(self):
        with pytest.raises(BusinessRuleViolationError):
            make_vlan_group(min_vid=0)

    def test_create_invalid_max_vid(self):
        with pytest.raises(BusinessRuleViolationError):
            make_vlan_group(max_vid=5000)

    def test_create_min_greater_than_max(self):
        with pytest.raises(BusinessRuleViolationError):
            make_vlan_group(min_vid=200, max_vid=100)


class TestVLANGroupUpdate:
    def test_update_name(self):
        vg = make_vlan_group()
        vg.collect_uncommitted_events()
        vg.update(name="Updated")
        assert vg.name == "Updated"

    def test_update_vid_range(self):
        vg = make_vlan_group()
        vg.collect_uncommitted_events()
        vg.update(min_vid=10, max_vid=100)
        assert vg.min_vid == 10
        assert vg.max_vid == 100

    def test_update_invalid_vid_range(self):
        vg = make_vlan_group()
        vg.collect_uncommitted_events()
        with pytest.raises(BusinessRuleViolationError):
            vg.update(min_vid=500, max_vid=100)

    def test_update_produces_event(self):
        vg = make_vlan_group()
        vg.collect_uncommitted_events()
        vg.update(name="new")
        events = vg.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], VLANGroupUpdated)

    def test_update_deleted_raises_error(self):
        vg = make_vlan_group()
        vg.collect_uncommitted_events()
        vg.delete()
        with pytest.raises(BusinessRuleViolationError, match="deleted"):
            vg.update(name="fail")


class TestVLANGroupDelete:
    def test_delete_marks_deleted(self):
        vg = make_vlan_group()
        vg.collect_uncommitted_events()
        vg.delete()
        assert vg._deleted is True

    def test_delete_produces_event(self):
        vg = make_vlan_group()
        vg.collect_uncommitted_events()
        vg.delete()
        events = vg.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], VLANGroupDeleted)

    def test_double_delete_raises_error(self):
        vg = make_vlan_group()
        vg.collect_uncommitted_events()
        vg.delete()
        with pytest.raises(BusinessRuleViolationError, match="already deleted"):
            vg.delete()


class TestVLANGroupLoadFromHistory:
    def test_load_from_history_restores_state(self):
        original = make_vlan_group(name="Orig", slug="orig", min_vid=10, max_vid=500)
        original.update(name="Updated")
        original.delete()
        events = original.collect_uncommitted_events()

        restored = VLANGroup()
        restored.load_from_history(events)
        assert restored.name == "Updated"
        assert restored.slug == "orig"
        assert restored.min_vid == 10
        assert restored.max_vid == 500
        assert restored._deleted is True
        assert restored.version == 3


class TestVLANGroupSnapshot:
    def test_snapshot_roundtrip(self):
        tag_id = uuid4()
        tid = uuid4()
        vg = make_vlan_group(
            name="Test",
            slug="test",
            min_vid=10,
            max_vid=200,
            tenant_id=tid,
            description="desc",
            custom_fields={"k": "v"},
            tags=[tag_id],
        )
        snap = vg.to_snapshot()
        restored = VLANGroup.from_snapshot(vg.id, snap, vg.version)
        assert restored.name == "Test"
        assert restored.slug == "test"
        assert restored.min_vid == 10
        assert restored.max_vid == 200
        assert restored.tenant_id == tid
        assert restored.tags == [tag_id]
        assert restored.id == vg.id
