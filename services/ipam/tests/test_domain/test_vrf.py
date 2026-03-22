"""Unit tests for the VRF aggregate root."""

from uuid import UUID, uuid4

import pytest
from ipam.domain.events import VRFCreated, VRFDeleted, VRFUpdated
from ipam.domain.value_objects import RouteDistinguisher
from ipam.domain.vrf import VRF
from pydantic import ValidationError
from shared.domain.exceptions import BusinessRuleViolationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_vrf(
    name: str = "default",
    rd: str | None = None,
    tenant_id: UUID | None = None,
    description: str = "",
) -> VRF:
    return VRF.create(
        name=name,
        rd=rd,
        tenant_id=tenant_id,
        description=description,
    )


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------


class TestVRFCreate:
    def test_create_returns_vrf_instance(self):
        vrf = make_vrf()
        assert isinstance(vrf, VRF)

    def test_create_sets_name(self):
        vrf = make_vrf(name="management")
        assert vrf.name == "management"

    def test_create_sets_rd_as_route_distinguisher(self):
        vrf = make_vrf(rd="65000:100")
        assert isinstance(vrf.rd, RouteDistinguisher)
        assert vrf.rd.rd == "65000:100"

    def test_create_sets_rd_none_by_default(self):
        vrf = make_vrf()
        assert vrf.rd is None

    def test_create_with_ip_based_rd(self):
        vrf = make_vrf(rd="192.168.1.1:100")
        assert vrf.rd.rd == "192.168.1.1:100"

    def test_create_with_invalid_rd_raises(self):
        with pytest.raises((ValueError, ValidationError)):
            make_vrf(rd="invalid-rd-format")

    def test_create_sets_tenant_id(self):
        tenant_id = uuid4()
        vrf = make_vrf(tenant_id=tenant_id)
        assert vrf.tenant_id == tenant_id

    def test_create_sets_tenant_id_none_by_default(self):
        vrf = make_vrf()
        assert vrf.tenant_id is None

    def test_create_sets_description(self):
        vrf = make_vrf(description="Customer A VRF")
        assert vrf.description == "Customer A VRF"

    def test_create_sets_empty_description_by_default(self):
        vrf = make_vrf()
        assert vrf.description == ""

    def test_create_version_is_1(self):
        vrf = make_vrf()
        assert vrf.version == 1

    def test_create_is_not_deleted(self):
        vrf = make_vrf()
        assert vrf._deleted is False

    def test_create_produces_one_event(self):
        vrf = make_vrf()
        events = vrf.collect_uncommitted_events()
        assert len(events) == 1

    def test_create_event_type_is_vrf_created(self):
        vrf = make_vrf()
        events = vrf.collect_uncommitted_events()
        assert isinstance(events[0], VRFCreated)

    def test_create_event_has_correct_aggregate_id(self):
        vrf = make_vrf()
        events = vrf.collect_uncommitted_events()
        assert events[0].aggregate_id == vrf.id

    def test_create_event_has_version_1(self):
        vrf = make_vrf()
        events = vrf.collect_uncommitted_events()
        assert events[0].version == 1

    def test_create_event_name_matches(self):
        vrf = make_vrf(name="transit")
        events = vrf.collect_uncommitted_events()
        assert events[0].name == "transit"

    def test_create_event_rd_matches(self):
        vrf = make_vrf(rd="65001:200")
        events = vrf.collect_uncommitted_events()
        assert events[0].rd == "65001:200"

    def test_create_assigns_unique_ids(self):
        v1 = make_vrf()
        v2 = make_vrf()
        assert v1.id != v2.id

    def test_collect_uncommitted_events_clears_queue(self):
        vrf = make_vrf()
        vrf.collect_uncommitted_events()
        assert vrf.collect_uncommitted_events() == []


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------


class TestVRFUpdate:
    def test_update_name_changes_name(self):
        vrf = make_vrf(name="old-name")
        vrf.collect_uncommitted_events()
        vrf.update(name="new-name")
        assert vrf.name == "new-name"

    def test_update_description_changes_description(self):
        vrf = make_vrf(description="old")
        vrf.collect_uncommitted_events()
        vrf.update(description="new description")
        assert vrf.description == "new description"

    def test_update_produces_vrf_updated_event(self):
        vrf = make_vrf()
        vrf.collect_uncommitted_events()
        vrf.update(name="updated")
        events = vrf.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], VRFUpdated)

    def test_update_increments_version(self):
        vrf = make_vrf()
        vrf.collect_uncommitted_events()
        vrf.update(name="v2")
        assert vrf.version == 2

    def test_update_event_has_correct_aggregate_id(self):
        vrf = make_vrf()
        vrf.collect_uncommitted_events()
        vrf.update(name="x")
        events = vrf.collect_uncommitted_events()
        assert events[0].aggregate_id == vrf.id

    def test_update_with_none_args_does_not_change_existing_values(self):
        vrf = make_vrf(name="keep", description="keep-desc")
        vrf.collect_uncommitted_events()
        vrf.update()  # all None
        assert vrf.name == "keep"
        assert vrf.description == "keep-desc"

    def test_update_after_delete_raises_business_rule_violation(self):
        vrf = make_vrf()
        vrf.collect_uncommitted_events()
        vrf.delete()
        with pytest.raises(BusinessRuleViolationError, match="deleted"):
            vrf.update(name="should fail")

    def test_multiple_updates_accumulate_version(self):
        vrf = make_vrf()
        vrf.collect_uncommitted_events()
        vrf.update(name="v2")
        vrf.collect_uncommitted_events()
        vrf.update(description="v3-desc")
        assert vrf.version == 3


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------


class TestVRFDelete:
    def test_delete_marks_vrf_as_deleted(self):
        vrf = make_vrf()
        vrf.collect_uncommitted_events()
        vrf.delete()
        assert vrf._deleted is True

    def test_delete_produces_vrf_deleted_event(self):
        vrf = make_vrf()
        vrf.collect_uncommitted_events()
        vrf.delete()
        events = vrf.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], VRFDeleted)

    def test_delete_increments_version(self):
        vrf = make_vrf()
        vrf.collect_uncommitted_events()
        vrf.delete()
        assert vrf.version == 2

    def test_delete_twice_raises_business_rule_violation(self):
        vrf = make_vrf()
        vrf.collect_uncommitted_events()
        vrf.delete()
        with pytest.raises(BusinessRuleViolationError, match="already deleted"):
            vrf.delete()

    def test_update_after_delete_is_blocked(self):
        vrf = make_vrf()
        vrf.collect_uncommitted_events()
        vrf.delete()
        with pytest.raises(BusinessRuleViolationError):
            vrf.update(name="blocked")


# ---------------------------------------------------------------------------
# load_from_history()
# ---------------------------------------------------------------------------


class TestVRFLoadFromHistory:
    def test_load_from_history_restores_name(self):
        original = make_vrf(name="customer-a")
        events = original.collect_uncommitted_events()

        restored = VRF()
        restored.load_from_history(events)

        assert restored.name == "customer-a"

    def test_load_from_history_restores_rd(self):
        original = make_vrf(rd="65000:999")
        events = original.collect_uncommitted_events()

        restored = VRF()
        restored.load_from_history(events)

        assert restored.rd is not None
        assert restored.rd.rd == "65000:999"

    def test_load_from_history_restores_tenant_id(self):
        tenant_id = uuid4()
        original = make_vrf(tenant_id=tenant_id)
        events = original.collect_uncommitted_events()

        restored = VRF()
        restored.load_from_history(events)

        assert restored.tenant_id == tenant_id

    def test_load_from_history_restores_description(self):
        original = make_vrf(description="testing")
        events = original.collect_uncommitted_events()

        restored = VRF()
        restored.load_from_history(events)

        assert restored.description == "testing"

    def test_load_from_history_restores_version(self):
        original = make_vrf()
        events = original.collect_uncommitted_events()

        restored = VRF()
        restored.load_from_history(events)

        assert restored.version == 1

    def test_load_from_history_restores_state_after_update(self):
        vrf = make_vrf(name="original")
        vrf.update(name="updated", description="new-desc")
        events = vrf.collect_uncommitted_events()

        restored = VRF()
        restored.load_from_history(events)

        assert restored.name == "updated"
        assert restored.description == "new-desc"
        assert restored.version == 2

    def test_load_from_history_restores_deleted_state(self):
        vrf = make_vrf()
        vrf.delete()
        events = vrf.collect_uncommitted_events()

        restored = VRF()
        restored.load_from_history(events)

        assert restored._deleted is True
        assert restored.version == 2

    def test_load_from_history_does_not_add_uncommitted_events(self):
        vrf = make_vrf()
        vrf.update(name="v2")
        events = vrf.collect_uncommitted_events()

        restored = VRF()
        restored.load_from_history(events)

        assert restored.collect_uncommitted_events() == []

    def test_load_from_history_restores_aggregate_id(self):
        vrf = make_vrf()
        original_id = vrf.id
        events = vrf.collect_uncommitted_events()

        restored = VRF()
        restored.load_from_history(events)

        # The aggregate ID comes from the event, not the shell object
        assert restored.id != original_id  # shell object has a different UUID
        # The event aggregate_id matches the original
        assert events[0].aggregate_id == original_id


# ---------------------------------------------------------------------------
# Snapshot round-trip
# ---------------------------------------------------------------------------


class TestVRFSnapshot:
    def test_to_snapshot_returns_dict(self):
        vrf = make_vrf()
        snap = vrf.to_snapshot()
        assert isinstance(snap, dict)

    def test_to_snapshot_contains_expected_keys(self):
        vrf = make_vrf()
        snap = vrf.to_snapshot()
        expected = {
            "name",
            "rd",
            "import_targets",
            "export_targets",
            "tenant_id",
            "description",
            "custom_fields",
            "tags",
            "deleted",
        }
        assert expected == snap.keys()

    def test_snapshot_roundtrip_preserves_name(self):
        vrf = make_vrf(name="backbone")
        snap = vrf.to_snapshot()
        restored = VRF.from_snapshot(vrf.id, snap, vrf.version)
        assert restored.name == "backbone"

    def test_snapshot_roundtrip_preserves_rd(self):
        vrf = make_vrf(rd="65500:1")
        snap = vrf.to_snapshot()
        restored = VRF.from_snapshot(vrf.id, snap, vrf.version)
        assert restored.rd is not None
        assert restored.rd.rd == "65500:1"

    def test_snapshot_roundtrip_preserves_none_rd(self):
        vrf = make_vrf(rd=None)
        snap = vrf.to_snapshot()
        restored = VRF.from_snapshot(vrf.id, snap, vrf.version)
        assert restored.rd is None

    def test_snapshot_roundtrip_preserves_tenant_id(self):
        tenant_id = uuid4()
        vrf = make_vrf(tenant_id=tenant_id)
        snap = vrf.to_snapshot()
        restored = VRF.from_snapshot(vrf.id, snap, vrf.version)
        assert restored.tenant_id == tenant_id

    def test_snapshot_roundtrip_preserves_description(self):
        vrf = make_vrf(description="my vrf")
        snap = vrf.to_snapshot()
        restored = VRF.from_snapshot(vrf.id, snap, vrf.version)
        assert restored.description == "my vrf"

    def test_snapshot_roundtrip_preserves_aggregate_id(self):
        vrf = make_vrf()
        snap = vrf.to_snapshot()
        restored = VRF.from_snapshot(vrf.id, snap, vrf.version)
        assert restored.id == vrf.id

    def test_snapshot_roundtrip_preserves_version(self):
        vrf = make_vrf()
        vrf.collect_uncommitted_events()
        vrf.update(name="v2")
        snap = vrf.to_snapshot()
        restored = VRF.from_snapshot(vrf.id, snap, vrf.version)
        assert restored.version == 2

    def test_snapshot_roundtrip_preserves_deleted_state(self):
        vrf = make_vrf()
        vrf.collect_uncommitted_events()
        vrf.delete()
        snap = vrf.to_snapshot()
        restored = VRF.from_snapshot(vrf.id, snap, vrf.version)
        assert restored._deleted is True

    def test_from_snapshot_does_not_produce_uncommitted_events(self):
        vrf = make_vrf()
        snap = vrf.to_snapshot()
        restored = VRF.from_snapshot(vrf.id, snap, vrf.version)
        assert restored.collect_uncommitted_events() == []


# ---------------------------------------------------------------------------
# Route Targets (import/export)
# ---------------------------------------------------------------------------


class TestVRFRouteTargets:
    def test_create_with_import_targets(self):
        rt_id = uuid4()
        vrf = VRF.create(name="test", import_targets=[rt_id])
        assert vrf.import_targets == [rt_id]

    def test_create_with_export_targets(self):
        rt_id = uuid4()
        vrf = VRF.create(name="test", export_targets=[rt_id])
        assert vrf.export_targets == [rt_id]

    def test_create_default_empty_targets(self):
        vrf = make_vrf()
        assert vrf.import_targets == []
        assert vrf.export_targets == []

    def test_update_import_targets(self):
        vrf = make_vrf()
        vrf.collect_uncommitted_events()
        rt_id = uuid4()
        vrf.update(import_targets=[rt_id])
        assert vrf.import_targets == [rt_id]

    def test_update_export_targets(self):
        vrf = make_vrf()
        vrf.collect_uncommitted_events()
        rt_id = uuid4()
        vrf.update(export_targets=[rt_id])
        assert vrf.export_targets == [rt_id]

    def test_event_has_import_export_targets(self):
        rt1 = uuid4()
        rt2 = uuid4()
        vrf = VRF.create(name="test", import_targets=[rt1], export_targets=[rt2])
        events = vrf.collect_uncommitted_events()
        assert events[0].import_targets == [rt1]
        assert events[0].export_targets == [rt2]

    def test_snapshot_preserves_targets(self):
        rt1, rt2 = uuid4(), uuid4()
        vrf = VRF.create(name="test", import_targets=[rt1], export_targets=[rt2])
        snap = vrf.to_snapshot()
        restored = VRF.from_snapshot(vrf.id, snap, vrf.version)
        assert restored.import_targets == [rt1]
        assert restored.export_targets == [rt2]

    def test_load_from_history_restores_targets(self):
        rt1, rt2 = uuid4(), uuid4()
        vrf = VRF.create(name="test", import_targets=[rt1], export_targets=[rt2])
        events = vrf.collect_uncommitted_events()
        restored = VRF()
        restored.load_from_history(events)
        assert restored.import_targets == [rt1]
        assert restored.export_targets == [rt2]
