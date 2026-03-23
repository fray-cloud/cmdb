"""Unit tests for the VLAN aggregate root."""

from uuid import UUID, uuid4

import pytest
from ipam.vlan.domain.events import VLANCreated, VLANDeleted, VLANStatusChanged, VLANUpdated
from ipam.vlan.domain.value_objects import VLANId, VLANStatus
from ipam.vlan.domain.vlan import VLAN
from pydantic import ValidationError
from shared.domain.exceptions import BusinessRuleViolationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_vlan(
    vid: int = 100,
    name: str = "test-vlan",
    group_id: UUID | None = None,
    status: VLANStatus = VLANStatus.ACTIVE,
    role: str | None = None,
    tenant_id: UUID | None = None,
    description: str = "",
) -> VLAN:
    return VLAN.create(
        vid=vid,
        name=name,
        group_id=group_id,
        status=status,
        role=role,
        tenant_id=tenant_id,
        description=description,
    )


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------


class TestVLANCreate:
    def test_create_returns_vlan_instance(self):
        vlan = make_vlan()
        assert isinstance(vlan, VLAN)

    def test_create_sets_vid_as_vlan_id(self):
        vlan = make_vlan(vid=200)
        assert isinstance(vlan.vid, VLANId)
        assert vlan.vid.vid == 200

    def test_create_sets_minimum_valid_vid(self):
        vlan = make_vlan(vid=1)
        assert vlan.vid.vid == 1

    def test_create_sets_maximum_valid_vid(self):
        vlan = make_vlan(vid=4094)
        assert vlan.vid.vid == 4094

    def test_create_with_vid_zero_raises(self):
        with pytest.raises((ValidationError, ValueError)):
            make_vlan(vid=0)

    def test_create_with_vid_4095_raises(self):
        with pytest.raises((ValidationError, ValueError)):
            make_vlan(vid=4095)

    def test_create_with_negative_vid_raises(self):
        with pytest.raises((ValidationError, ValueError)):
            make_vlan(vid=-1)

    def test_create_sets_name(self):
        vlan = make_vlan(name="production")
        assert vlan.name == "production"

    def test_create_sets_group_id(self):
        group_id = uuid4()
        vlan = make_vlan(group_id=group_id)
        assert vlan.group_id == group_id

    def test_create_sets_group_id_none_by_default(self):
        vlan = make_vlan()
        assert vlan.group_id is None

    def test_create_sets_default_status_active(self):
        vlan = make_vlan()
        assert vlan.status == VLANStatus.ACTIVE

    def test_create_sets_explicit_status(self):
        vlan = make_vlan(status=VLANStatus.RESERVED)
        assert vlan.status == VLANStatus.RESERVED

    def test_create_sets_role(self):
        vlan = make_vlan(role="access")
        assert vlan.role == "access"

    def test_create_sets_role_none_by_default(self):
        vlan = make_vlan()
        assert vlan.role is None

    def test_create_sets_tenant_id(self):
        tenant_id = uuid4()
        vlan = make_vlan(tenant_id=tenant_id)
        assert vlan.tenant_id == tenant_id

    def test_create_sets_description(self):
        vlan = make_vlan(description="Production VLAN")
        assert vlan.description == "Production VLAN"

    def test_create_version_is_1(self):
        vlan = make_vlan()
        assert vlan.version == 1

    def test_create_is_not_deleted(self):
        vlan = make_vlan()
        assert vlan._deleted is False

    def test_create_produces_one_event(self):
        vlan = make_vlan()
        events = vlan.collect_uncommitted_events()
        assert len(events) == 1

    def test_create_event_type_is_vlan_created(self):
        vlan = make_vlan()
        events = vlan.collect_uncommitted_events()
        assert isinstance(events[0], VLANCreated)

    def test_create_event_has_correct_aggregate_id(self):
        vlan = make_vlan()
        events = vlan.collect_uncommitted_events()
        assert events[0].aggregate_id == vlan.id

    def test_create_event_has_version_1(self):
        vlan = make_vlan()
        events = vlan.collect_uncommitted_events()
        assert events[0].version == 1

    def test_create_event_vid_matches(self):
        vlan = make_vlan(vid=500)
        events = vlan.collect_uncommitted_events()
        assert events[0].vid == 500

    def test_create_event_name_matches(self):
        vlan = make_vlan(name="dmz")
        events = vlan.collect_uncommitted_events()
        assert events[0].name == "dmz"

    def test_create_assigns_unique_ids(self):
        v1 = make_vlan(vid=10)
        v2 = make_vlan(vid=20)
        assert v1.id != v2.id

    def test_collect_uncommitted_events_clears_queue(self):
        vlan = make_vlan()
        vlan.collect_uncommitted_events()
        assert vlan.collect_uncommitted_events() == []


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------


class TestVLANUpdate:
    def test_update_name_changes_name(self):
        vlan = make_vlan(name="old")
        vlan.collect_uncommitted_events()
        vlan.update(name="new-name")
        assert vlan.name == "new-name"

    def test_update_role_changes_role(self):
        vlan = make_vlan(role="old-role")
        vlan.collect_uncommitted_events()
        vlan.update(role="trunk")
        assert vlan.role == "trunk"

    def test_update_description_changes_description(self):
        vlan = make_vlan(description="old")
        vlan.collect_uncommitted_events()
        vlan.update(description="new description")
        assert vlan.description == "new description"

    def test_update_produces_vlan_updated_event(self):
        vlan = make_vlan()
        vlan.collect_uncommitted_events()
        vlan.update(name="updated")
        events = vlan.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], VLANUpdated)

    def test_update_increments_version(self):
        vlan = make_vlan()
        vlan.collect_uncommitted_events()
        vlan.update(name="v2")
        assert vlan.version == 2

    def test_update_event_has_correct_aggregate_id(self):
        vlan = make_vlan()
        vlan.collect_uncommitted_events()
        vlan.update(name="x")
        events = vlan.collect_uncommitted_events()
        assert events[0].aggregate_id == vlan.id

    def test_update_with_none_args_does_not_change_existing_values(self):
        vlan = make_vlan(name="keep", role="access", description="keep-desc")
        vlan.collect_uncommitted_events()
        vlan.update()  # all None
        assert vlan.name == "keep"
        assert vlan.role == "access"
        assert vlan.description == "keep-desc"

    def test_update_after_delete_raises_business_rule_violation(self):
        vlan = make_vlan()
        vlan.collect_uncommitted_events()
        vlan.delete()
        with pytest.raises(BusinessRuleViolationError, match="deleted"):
            vlan.update(name="should fail")

    def test_multiple_updates_accumulate_version(self):
        vlan = make_vlan()
        vlan.collect_uncommitted_events()
        vlan.update(name="v2")
        vlan.collect_uncommitted_events()
        vlan.update(description="v3-desc")
        assert vlan.version == 3


# ---------------------------------------------------------------------------
# change_status()
# ---------------------------------------------------------------------------


class TestVLANChangeStatus:
    def test_change_status_updates_status(self):
        vlan = make_vlan(status=VLANStatus.ACTIVE)
        vlan.collect_uncommitted_events()
        vlan.change_status(VLANStatus.RESERVED)
        assert vlan.status == VLANStatus.RESERVED

    def test_change_status_to_deprecated(self):
        vlan = make_vlan(status=VLANStatus.ACTIVE)
        vlan.collect_uncommitted_events()
        vlan.change_status(VLANStatus.DEPRECATED)
        assert vlan.status == VLANStatus.DEPRECATED

    def test_change_status_produces_vlan_status_changed_event(self):
        vlan = make_vlan(status=VLANStatus.ACTIVE)
        vlan.collect_uncommitted_events()
        vlan.change_status(VLANStatus.DEPRECATED)
        events = vlan.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], VLANStatusChanged)

    def test_change_status_event_contains_old_and_new_status(self):
        vlan = make_vlan(status=VLANStatus.ACTIVE)
        vlan.collect_uncommitted_events()
        vlan.change_status(VLANStatus.RESERVED)
        events = vlan.collect_uncommitted_events()
        assert events[0].old_status == "active"
        assert events[0].new_status == "reserved"

    def test_change_status_increments_version(self):
        vlan = make_vlan()
        vlan.collect_uncommitted_events()
        vlan.change_status(VLANStatus.DEPRECATED)
        assert vlan.version == 2

    def test_change_status_to_same_status_raises_business_rule_violation(self):
        vlan = make_vlan(status=VLANStatus.ACTIVE)
        vlan.collect_uncommitted_events()
        with pytest.raises(BusinessRuleViolationError, match="already"):
            vlan.change_status(VLANStatus.ACTIVE)

    def test_change_status_after_delete_raises_business_rule_violation(self):
        vlan = make_vlan()
        vlan.collect_uncommitted_events()
        vlan.delete()
        with pytest.raises(BusinessRuleViolationError, match="deleted"):
            vlan.change_status(VLANStatus.RESERVED)


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------


class TestVLANDelete:
    def test_delete_marks_vlan_as_deleted(self):
        vlan = make_vlan()
        vlan.collect_uncommitted_events()
        vlan.delete()
        assert vlan._deleted is True

    def test_delete_produces_vlan_deleted_event(self):
        vlan = make_vlan()
        vlan.collect_uncommitted_events()
        vlan.delete()
        events = vlan.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], VLANDeleted)

    def test_delete_increments_version(self):
        vlan = make_vlan()
        vlan.collect_uncommitted_events()
        vlan.delete()
        assert vlan.version == 2

    def test_delete_twice_raises_business_rule_violation(self):
        vlan = make_vlan()
        vlan.collect_uncommitted_events()
        vlan.delete()
        with pytest.raises(BusinessRuleViolationError, match="already deleted"):
            vlan.delete()

    def test_update_after_delete_is_blocked(self):
        vlan = make_vlan()
        vlan.collect_uncommitted_events()
        vlan.delete()
        with pytest.raises(BusinessRuleViolationError):
            vlan.update(name="blocked")

    def test_change_status_after_delete_is_blocked(self):
        vlan = make_vlan()
        vlan.collect_uncommitted_events()
        vlan.delete()
        with pytest.raises(BusinessRuleViolationError):
            vlan.change_status(VLANStatus.DEPRECATED)


# ---------------------------------------------------------------------------
# load_from_history()
# ---------------------------------------------------------------------------


class TestVLANLoadFromHistory:
    def test_load_from_history_restores_vid(self):
        original = make_vlan(vid=300)
        events = original.collect_uncommitted_events()

        restored = VLAN()
        restored.load_from_history(events)

        assert restored.vid.vid == 300

    def test_load_from_history_restores_name(self):
        original = make_vlan(name="corp-lan")
        events = original.collect_uncommitted_events()

        restored = VLAN()
        restored.load_from_history(events)

        assert restored.name == "corp-lan"

    def test_load_from_history_restores_group_id(self):
        group_id = uuid4()
        original = make_vlan(group_id=group_id)
        events = original.collect_uncommitted_events()

        restored = VLAN()
        restored.load_from_history(events)

        assert restored.group_id == group_id

    def test_load_from_history_restores_status(self):
        original = make_vlan(status=VLANStatus.RESERVED)
        events = original.collect_uncommitted_events()

        restored = VLAN()
        restored.load_from_history(events)

        assert restored.status == VLANStatus.RESERVED

    def test_load_from_history_restores_after_update(self):
        vlan = make_vlan(name="original")
        vlan.update(name="updated", role="access", description="new-desc")
        events = vlan.collect_uncommitted_events()

        restored = VLAN()
        restored.load_from_history(events)

        assert restored.name == "updated"
        assert restored.role == "access"
        assert restored.description == "new-desc"
        assert restored.version == 2

    def test_load_from_history_restores_status_change(self):
        vlan = make_vlan(status=VLANStatus.ACTIVE)
        vlan.change_status(VLANStatus.DEPRECATED)
        events = vlan.collect_uncommitted_events()

        restored = VLAN()
        restored.load_from_history(events)

        assert restored.status == VLANStatus.DEPRECATED

    def test_load_from_history_restores_deleted_state(self):
        vlan = make_vlan()
        vlan.delete()
        events = vlan.collect_uncommitted_events()

        restored = VLAN()
        restored.load_from_history(events)

        assert restored._deleted is True
        assert restored.version == 2

    def test_load_from_history_does_not_add_uncommitted_events(self):
        vlan = make_vlan()
        vlan.update(name="v2")
        events = vlan.collect_uncommitted_events()

        restored = VLAN()
        restored.load_from_history(events)

        assert restored.collect_uncommitted_events() == []


# ---------------------------------------------------------------------------
# Snapshot round-trip
# ---------------------------------------------------------------------------


class TestVLANSnapshot:
    def test_to_snapshot_returns_dict(self):
        vlan = make_vlan()
        snap = vlan.to_snapshot()
        assert isinstance(snap, dict)

    def test_to_snapshot_contains_expected_keys(self):
        vlan = make_vlan()
        snap = vlan.to_snapshot()
        expected = {
            "vid",
            "name",
            "group_id",
            "status",
            "role",
            "tenant_id",
            "description",
            "custom_fields",
            "tags",
            "deleted",
        }
        assert expected == snap.keys()

    def test_snapshot_roundtrip_preserves_vid(self):
        vlan = make_vlan(vid=777)
        snap = vlan.to_snapshot()
        restored = VLAN.from_snapshot(vlan.id, snap, vlan.version)
        assert restored.vid.vid == 777

    def test_snapshot_roundtrip_preserves_name(self):
        vlan = make_vlan(name="data-center")
        snap = vlan.to_snapshot()
        restored = VLAN.from_snapshot(vlan.id, snap, vlan.version)
        assert restored.name == "data-center"

    def test_snapshot_roundtrip_preserves_status(self):
        vlan = make_vlan(status=VLANStatus.DEPRECATED)
        snap = vlan.to_snapshot()
        restored = VLAN.from_snapshot(vlan.id, snap, vlan.version)
        assert restored.status == VLANStatus.DEPRECATED

    def test_snapshot_roundtrip_preserves_group_id(self):
        group_id = uuid4()
        vlan = make_vlan(group_id=group_id)
        snap = vlan.to_snapshot()
        restored = VLAN.from_snapshot(vlan.id, snap, vlan.version)
        assert restored.group_id == group_id

    def test_snapshot_roundtrip_preserves_none_group_id(self):
        vlan = make_vlan(group_id=None)
        snap = vlan.to_snapshot()
        restored = VLAN.from_snapshot(vlan.id, snap, vlan.version)
        assert restored.group_id is None

    def test_snapshot_roundtrip_preserves_role(self):
        vlan = make_vlan(role="access")
        snap = vlan.to_snapshot()
        restored = VLAN.from_snapshot(vlan.id, snap, vlan.version)
        assert restored.role == "access"

    def test_snapshot_roundtrip_preserves_description(self):
        vlan = make_vlan(description="my vlan")
        snap = vlan.to_snapshot()
        restored = VLAN.from_snapshot(vlan.id, snap, vlan.version)
        assert restored.description == "my vlan"

    def test_snapshot_roundtrip_preserves_aggregate_id(self):
        vlan = make_vlan()
        snap = vlan.to_snapshot()
        restored = VLAN.from_snapshot(vlan.id, snap, vlan.version)
        assert restored.id == vlan.id

    def test_snapshot_roundtrip_preserves_version(self):
        vlan = make_vlan()
        vlan.collect_uncommitted_events()
        vlan.update(name="v2")
        snap = vlan.to_snapshot()
        restored = VLAN.from_snapshot(vlan.id, snap, vlan.version)
        assert restored.version == 2

    def test_snapshot_roundtrip_preserves_deleted_state(self):
        vlan = make_vlan()
        vlan.collect_uncommitted_events()
        vlan.delete()
        snap = vlan.to_snapshot()
        restored = VLAN.from_snapshot(vlan.id, snap, vlan.version)
        assert restored._deleted is True

    def test_from_snapshot_does_not_produce_uncommitted_events(self):
        vlan = make_vlan()
        snap = vlan.to_snapshot()
        restored = VLAN.from_snapshot(vlan.id, snap, vlan.version)
        assert restored.collect_uncommitted_events() == []
