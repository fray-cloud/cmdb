"""Unit tests for the IPRange aggregate root."""

from uuid import uuid4

import pytest
from ipam.ip_range.domain.events import (
    IPRangeCreated,
    IPRangeDeleted,
    IPRangeStatusChanged,
    IPRangeUpdated,
)
from ipam.ip_range.domain.ip_range import IPRange
from ipam.ip_range.domain.value_objects import IPRangeStatus
from ipam.shared.value_objects import IPAddressValue
from shared.domain.exceptions import BusinessRuleViolationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_ip_range(
    start_address: str = "192.168.1.1",
    end_address: str = "192.168.1.254",
    vrf_id=None,
    status: IPRangeStatus = IPRangeStatus.ACTIVE,
    tenant_id=None,
    description: str = "",
    custom_fields: dict | None = None,
    tags: list | None = None,
) -> IPRange:
    return IPRange.create(
        start_address=start_address,
        end_address=end_address,
        vrf_id=vrf_id,
        status=status,
        tenant_id=tenant_id,
        description=description,
        custom_fields=custom_fields,
        tags=tags,
    )


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------


class TestIPRangeCreate:
    def test_create_returns_ip_range_instance(self):
        ip_range = make_ip_range()
        assert isinstance(ip_range, IPRange)

    def test_create_sets_start_and_end_address(self):
        ip_range = make_ip_range(start_address="10.0.0.1", end_address="10.0.0.100")
        assert isinstance(ip_range.start_address, IPAddressValue)
        assert ip_range.start_address.address == "10.0.0.1"
        assert ip_range.end_address.address == "10.0.0.100"

    def test_create_with_custom_fields_and_tags(self):
        tag_id = uuid4()
        ip_range = make_ip_range(
            custom_fields={"env": "prod"},
            tags=[tag_id],
        )
        assert ip_range.custom_fields == {"env": "prod"}
        assert ip_range.tags == [tag_id]

    def test_create_start_gte_end_raises_error(self):
        with pytest.raises(BusinessRuleViolationError, match="less than"):
            make_ip_range(start_address="192.168.1.100", end_address="192.168.1.1")

    def test_create_start_equal_end_raises_error(self):
        with pytest.raises(BusinessRuleViolationError, match="less than"):
            make_ip_range(start_address="192.168.1.1", end_address="192.168.1.1")

    def test_create_different_ip_versions_raises_error(self):
        with pytest.raises(BusinessRuleViolationError, match="same IP version"):
            make_ip_range(start_address="192.168.1.1", end_address="2001:db8::1")

    def test_create_emits_ip_range_created_event(self):
        ip_range = make_ip_range()
        events = ip_range.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], IPRangeCreated)

    def test_create_version_is_1(self):
        ip_range = make_ip_range()
        assert ip_range.version == 1

    def test_create_is_not_deleted(self):
        ip_range = make_ip_range()
        assert ip_range._deleted is False

    def test_create_event_has_correct_aggregate_id(self):
        ip_range = make_ip_range()
        events = ip_range.collect_uncommitted_events()
        assert events[0].aggregate_id == ip_range.id

    def test_create_assigns_unique_ids(self):
        r1 = make_ip_range()
        r2 = make_ip_range()
        assert r1.id != r2.id


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------


class TestIPRangeUpdate:
    def test_update_description(self):
        ip_range = make_ip_range(description="old")
        ip_range.collect_uncommitted_events()
        ip_range.update(description="new description")
        assert ip_range.description == "new description"

    def test_update_custom_fields(self):
        ip_range = make_ip_range()
        ip_range.collect_uncommitted_events()
        ip_range.update(custom_fields={"region": "us-east"})
        assert ip_range.custom_fields == {"region": "us-east"}

    def test_update_tags(self):
        tag_id = uuid4()
        ip_range = make_ip_range()
        ip_range.collect_uncommitted_events()
        ip_range.update(tags=[tag_id])
        assert ip_range.tags == [tag_id]

    def test_update_produces_ip_range_updated_event(self):
        ip_range = make_ip_range()
        ip_range.collect_uncommitted_events()
        ip_range.update(description="updated")
        events = ip_range.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], IPRangeUpdated)

    def test_update_increments_version(self):
        ip_range = make_ip_range()
        ip_range.collect_uncommitted_events()
        ip_range.update(description="v2")
        assert ip_range.version == 2

    def test_update_deleted_raises_error(self):
        ip_range = make_ip_range()
        ip_range.collect_uncommitted_events()
        ip_range.delete()
        with pytest.raises(BusinessRuleViolationError, match="deleted"):
            ip_range.update(description="should fail")


# ---------------------------------------------------------------------------
# change_status()
# ---------------------------------------------------------------------------


class TestIPRangeChangeStatus:
    def test_change_status(self):
        ip_range = make_ip_range(status=IPRangeStatus.ACTIVE)
        ip_range.collect_uncommitted_events()
        ip_range.change_status(IPRangeStatus.RESERVED)
        assert ip_range.status == IPRangeStatus.RESERVED

    def test_change_status_produces_event(self):
        ip_range = make_ip_range(status=IPRangeStatus.ACTIVE)
        ip_range.collect_uncommitted_events()
        ip_range.change_status(IPRangeStatus.DEPRECATED)
        events = ip_range.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], IPRangeStatusChanged)

    def test_change_status_event_contains_old_and_new(self):
        ip_range = make_ip_range(status=IPRangeStatus.ACTIVE)
        ip_range.collect_uncommitted_events()
        ip_range.change_status(IPRangeStatus.RESERVED)
        events = ip_range.collect_uncommitted_events()
        assert events[0].old_status == "active"
        assert events[0].new_status == "reserved"

    def test_same_status_raises_error(self):
        ip_range = make_ip_range(status=IPRangeStatus.ACTIVE)
        ip_range.collect_uncommitted_events()
        with pytest.raises(BusinessRuleViolationError, match="already"):
            ip_range.change_status(IPRangeStatus.ACTIVE)

    def test_deleted_raises_error(self):
        ip_range = make_ip_range()
        ip_range.collect_uncommitted_events()
        ip_range.delete()
        with pytest.raises(BusinessRuleViolationError, match="deleted"):
            ip_range.change_status(IPRangeStatus.RESERVED)


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------


class TestIPRangeDelete:
    def test_delete_marks_as_deleted(self):
        ip_range = make_ip_range()
        ip_range.collect_uncommitted_events()
        ip_range.delete()
        assert ip_range._deleted is True

    def test_delete_produces_ip_range_deleted_event(self):
        ip_range = make_ip_range()
        ip_range.collect_uncommitted_events()
        ip_range.delete()
        events = ip_range.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], IPRangeDeleted)

    def test_delete_increments_version(self):
        ip_range = make_ip_range()
        ip_range.collect_uncommitted_events()
        ip_range.delete()
        assert ip_range.version == 2

    def test_double_delete_raises_error(self):
        ip_range = make_ip_range()
        ip_range.collect_uncommitted_events()
        ip_range.delete()
        with pytest.raises(BusinessRuleViolationError, match="already deleted"):
            ip_range.delete()


# ---------------------------------------------------------------------------
# load_from_history()
# ---------------------------------------------------------------------------


class TestIPRangeLoadFromHistory:
    def test_load_from_history_restores_state(self):
        original = make_ip_range(
            start_address="10.0.0.1",
            end_address="10.0.0.100",
            description="original",
        )
        original.update(description="updated")
        original.change_status(IPRangeStatus.RESERVED)
        original.delete()
        events = original.collect_uncommitted_events()

        restored = IPRange()
        restored.load_from_history(events)

        assert restored.start_address.address == "10.0.0.1"
        assert restored.end_address.address == "10.0.0.100"
        assert restored.description == "updated"
        assert restored.status == IPRangeStatus.RESERVED
        assert restored._deleted is True
        assert restored.version == 4

    def test_load_from_history_does_not_add_uncommitted_events(self):
        ip_range = make_ip_range()
        events = ip_range.collect_uncommitted_events()

        restored = IPRange()
        restored.load_from_history(events)

        assert restored.collect_uncommitted_events() == []


# ---------------------------------------------------------------------------
# Snapshot round-trip
# ---------------------------------------------------------------------------


class TestIPRangeSnapshot:
    def test_to_snapshot_returns_dict(self):
        ip_range = make_ip_range()
        snap = ip_range.to_snapshot()
        assert isinstance(snap, dict)

    def test_snapshot_keys(self):
        ip_range = make_ip_range()
        snap = ip_range.to_snapshot()
        expected_keys = {
            "start_address",
            "end_address",
            "vrf_id",
            "status",
            "tenant_id",
            "description",
            "custom_fields",
            "tags",
            "deleted",
        }
        assert expected_keys == snap.keys()

    def test_snapshot_roundtrip_preserves_state(self):
        tag_id = uuid4()
        tenant_id = uuid4()
        ip_range = make_ip_range(
            start_address="10.0.0.1",
            end_address="10.0.0.100",
            tenant_id=tenant_id,
            description="test",
            custom_fields={"env": "prod"},
            tags=[tag_id],
        )
        snap = ip_range.to_snapshot()
        restored = IPRange.from_snapshot(ip_range.id, snap, ip_range.version)

        assert restored.start_address.address == "10.0.0.1"
        assert restored.end_address.address == "10.0.0.100"
        assert restored.tenant_id == tenant_id
        assert restored.description == "test"
        assert restored.custom_fields == {"env": "prod"}
        assert restored.tags == [tag_id]
        assert restored.id == ip_range.id
        assert restored.version == ip_range.version
        assert restored.collect_uncommitted_events() == []
