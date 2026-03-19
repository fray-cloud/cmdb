"""Unit tests for the Prefix aggregate root."""

from uuid import UUID, uuid4

import pytest
from ipam.domain.events import (
    PrefixCreated,
    PrefixDeleted,
    PrefixStatusChanged,
    PrefixUpdated,
)
from ipam.domain.prefix import Prefix
from ipam.domain.value_objects import PrefixNetwork, PrefixStatus
from pydantic import ValidationError

from shared.domain.exceptions import BusinessRuleViolationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_prefix(
    network: str = "192.168.0.0/24",
    vrf_id: UUID | None = None,
    status: PrefixStatus = PrefixStatus.ACTIVE,
    role: str | None = None,
    tenant_id: UUID | None = None,
    description: str = "",
) -> Prefix:
    return Prefix.create(
        network=network,
        vrf_id=vrf_id,
        status=status,
        role=role,
        tenant_id=tenant_id,
        description=description,
    )


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------


class TestPrefixCreate:
    def test_create_returns_prefix_instance(self):
        prefix = make_prefix()
        assert isinstance(prefix, Prefix)

    def test_create_sets_network(self):
        prefix = make_prefix(network="10.0.0.0/8")
        assert isinstance(prefix.network, PrefixNetwork)
        assert prefix.network.network == "10.0.0.0/8"

    def test_create_normalises_host_bits_in_network(self):
        prefix = make_prefix(network="10.0.0.5/8")
        assert prefix.network.network == "10.0.0.0/8"

    def test_create_sets_default_status_active(self):
        prefix = make_prefix()
        assert prefix.status == PrefixStatus.ACTIVE

    def test_create_sets_explicit_status(self):
        prefix = make_prefix(status=PrefixStatus.RESERVED)
        assert prefix.status == PrefixStatus.RESERVED

    def test_create_sets_vrf_id(self):
        vrf_id = uuid4()
        prefix = make_prefix(vrf_id=vrf_id)
        assert prefix.vrf_id == vrf_id

    def test_create_sets_vrf_id_none_by_default(self):
        prefix = make_prefix()
        assert prefix.vrf_id is None

    def test_create_sets_role(self):
        prefix = make_prefix(role="loopback")
        assert prefix.role == "loopback"

    def test_create_sets_tenant_id(self):
        tenant_id = uuid4()
        prefix = make_prefix(tenant_id=tenant_id)
        assert prefix.tenant_id == tenant_id

    def test_create_sets_description(self):
        prefix = make_prefix(description="Management network")
        assert prefix.description == "Management network"

    def test_create_version_is_1(self):
        prefix = make_prefix()
        assert prefix.version == 1

    def test_create_is_not_deleted(self):
        prefix = make_prefix()
        assert prefix._deleted is False

    def test_create_produces_one_event(self):
        prefix = make_prefix()
        events = prefix.collect_uncommitted_events()
        assert len(events) == 1

    def test_create_event_type_is_prefix_created(self):
        prefix = make_prefix()
        events = prefix.collect_uncommitted_events()
        assert isinstance(events[0], PrefixCreated)

    def test_create_event_has_correct_aggregate_id(self):
        prefix = make_prefix()
        events = prefix.collect_uncommitted_events()
        assert events[0].aggregate_id == prefix.id

    def test_create_event_has_version_1(self):
        prefix = make_prefix()
        events = prefix.collect_uncommitted_events()
        assert events[0].version == 1

    def test_create_event_network_matches(self):
        prefix = make_prefix(network="172.16.0.0/12")
        events = prefix.collect_uncommitted_events()
        assert events[0].network == "172.16.0.0/12"

    def test_create_ipv6_prefix(self):
        prefix = make_prefix(network="2001:db8::/32")
        assert prefix.network.version == 6
        assert prefix.network.network == "2001:db8::/32"

    def test_create_ipv6_produces_prefix_created_event(self):
        prefix = make_prefix(network="fd00::/8")
        events = prefix.collect_uncommitted_events()
        assert isinstance(events[0], PrefixCreated)
        assert events[0].network == "fd00::/8"

    def test_create_with_invalid_network_raises(self):
        with pytest.raises((ValueError, ValidationError)):
            make_prefix(network="not-a-network")

    def test_create_assigns_unique_ids(self):
        p1 = make_prefix()
        p2 = make_prefix()
        assert p1.id != p2.id

    def test_collect_uncommitted_events_clears_queue(self):
        prefix = make_prefix()
        prefix.collect_uncommitted_events()
        assert prefix.collect_uncommitted_events() == []


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------


class TestPrefixUpdate:
    def test_update_description_changes_description(self):
        prefix = make_prefix(description="old")
        prefix.collect_uncommitted_events()  # flush create event
        prefix.update(description="new description")
        assert prefix.description == "new description"

    def test_update_role_changes_role(self):
        prefix = make_prefix(role="old-role")
        prefix.collect_uncommitted_events()
        prefix.update(role="loopback")
        assert prefix.role == "loopback"

    def test_update_tenant_id_changes_tenant_id(self):
        prefix = make_prefix()
        prefix.collect_uncommitted_events()
        new_tenant = uuid4()
        prefix.update(tenant_id=new_tenant)
        assert prefix.tenant_id == new_tenant

    def test_update_produces_prefix_updated_event(self):
        prefix = make_prefix()
        prefix.collect_uncommitted_events()
        prefix.update(description="updated")
        events = prefix.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], PrefixUpdated)

    def test_update_increments_version(self):
        prefix = make_prefix()
        prefix.collect_uncommitted_events()
        prefix.update(description="v2")
        assert prefix.version == 2

    def test_update_event_has_correct_aggregate_id(self):
        prefix = make_prefix()
        prefix.collect_uncommitted_events()
        prefix.update(description="x")
        events = prefix.collect_uncommitted_events()
        assert events[0].aggregate_id == prefix.id

    def test_update_with_none_args_does_not_change_existing_values(self):
        prefix = make_prefix(description="keep", role="keep-role")
        prefix.collect_uncommitted_events()
        prefix.update()  # all None
        assert prefix.description == "keep"
        assert prefix.role == "keep-role"

    def test_update_after_delete_raises_business_rule_violation(self):
        prefix = make_prefix()
        prefix.collect_uncommitted_events()
        prefix.delete()
        with pytest.raises(BusinessRuleViolationError, match="deleted"):
            prefix.update(description="should fail")


# ---------------------------------------------------------------------------
# change_status()
# ---------------------------------------------------------------------------


class TestPrefixChangeStatus:
    def test_change_status_updates_status(self):
        prefix = make_prefix(status=PrefixStatus.ACTIVE)
        prefix.collect_uncommitted_events()
        prefix.change_status(PrefixStatus.RESERVED)
        assert prefix.status == PrefixStatus.RESERVED

    def test_change_status_produces_prefix_status_changed_event(self):
        prefix = make_prefix(status=PrefixStatus.ACTIVE)
        prefix.collect_uncommitted_events()
        prefix.change_status(PrefixStatus.DEPRECATED)
        events = prefix.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], PrefixStatusChanged)

    def test_change_status_event_contains_old_and_new_status(self):
        prefix = make_prefix(status=PrefixStatus.ACTIVE)
        prefix.collect_uncommitted_events()
        prefix.change_status(PrefixStatus.RESERVED)
        events = prefix.collect_uncommitted_events()
        assert events[0].old_status == "active"
        assert events[0].new_status == "reserved"

    def test_change_status_increments_version(self):
        prefix = make_prefix()
        prefix.collect_uncommitted_events()
        prefix.change_status(PrefixStatus.DEPRECATED)
        assert prefix.version == 2

    def test_change_status_to_same_status_raises_business_rule_violation(self):
        prefix = make_prefix(status=PrefixStatus.ACTIVE)
        prefix.collect_uncommitted_events()
        with pytest.raises(BusinessRuleViolationError, match="already"):
            prefix.change_status(PrefixStatus.ACTIVE)

    def test_change_status_after_delete_raises_business_rule_violation(self):
        prefix = make_prefix()
        prefix.collect_uncommitted_events()
        prefix.delete()
        with pytest.raises(BusinessRuleViolationError, match="deleted"):
            prefix.change_status(PrefixStatus.RESERVED)

    def test_change_status_to_container(self):
        prefix = make_prefix(status=PrefixStatus.ACTIVE)
        prefix.collect_uncommitted_events()
        prefix.change_status(PrefixStatus.CONTAINER)
        assert prefix.status == PrefixStatus.CONTAINER


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------


class TestPrefixDelete:
    def test_delete_marks_prefix_as_deleted(self):
        prefix = make_prefix()
        prefix.collect_uncommitted_events()
        prefix.delete()
        assert prefix._deleted is True

    def test_delete_produces_prefix_deleted_event(self):
        prefix = make_prefix()
        prefix.collect_uncommitted_events()
        prefix.delete()
        events = prefix.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], PrefixDeleted)

    def test_delete_increments_version(self):
        prefix = make_prefix()
        prefix.collect_uncommitted_events()
        prefix.delete()
        assert prefix.version == 2

    def test_delete_twice_raises_business_rule_violation(self):
        prefix = make_prefix()
        prefix.collect_uncommitted_events()
        prefix.delete()
        with pytest.raises(BusinessRuleViolationError, match="already deleted"):
            prefix.delete()


# ---------------------------------------------------------------------------
# load_from_history()
# ---------------------------------------------------------------------------


class TestPrefixLoadFromHistory:
    def test_load_from_history_restores_state_after_create(self):
        original = make_prefix(
            network="10.1.0.0/16",
            description="original",
            role="transit",
        )
        events = original.collect_uncommitted_events()

        restored = Prefix()
        restored.load_from_history(events)

        assert restored.network.network == "10.1.0.0/16"
        assert restored.description == "original"
        assert restored.role == "transit"
        assert restored.version == 1

    def test_load_from_history_restores_state_after_update(self):
        prefix = make_prefix(description="old")
        prefix.update(description="new", role="loopback")
        events = prefix.collect_uncommitted_events()

        restored = Prefix()
        restored.load_from_history(events)

        assert restored.description == "new"
        assert restored.role == "loopback"
        assert restored.version == 2

    def test_load_from_history_restores_status_change(self):
        prefix = make_prefix(status=PrefixStatus.ACTIVE)
        prefix.change_status(PrefixStatus.DEPRECATED)
        events = prefix.collect_uncommitted_events()

        restored = Prefix()
        restored.load_from_history(events)

        assert restored.status == PrefixStatus.DEPRECATED

    def test_load_from_history_restores_deleted_state(self):
        prefix = make_prefix()
        prefix.delete()
        events = prefix.collect_uncommitted_events()

        restored = Prefix()
        restored.load_from_history(events)

        assert restored._deleted is True
        assert restored.version == 2

    def test_load_from_history_does_not_add_uncommitted_events(self):
        prefix = make_prefix()
        prefix.update(description="v2")
        events = prefix.collect_uncommitted_events()

        restored = Prefix()
        restored.load_from_history(events)

        assert restored.collect_uncommitted_events() == []

    def test_load_from_history_restores_vrf_id(self):
        vrf_id = uuid4()
        prefix = make_prefix(vrf_id=vrf_id)
        events = prefix.collect_uncommitted_events()

        restored = Prefix()
        restored.load_from_history(events)

        assert restored.vrf_id == vrf_id

    def test_load_from_history_restores_tenant_id(self):
        tenant_id = uuid4()
        prefix = make_prefix(tenant_id=tenant_id)
        events = prefix.collect_uncommitted_events()

        restored = Prefix()
        restored.load_from_history(events)

        assert restored.tenant_id == tenant_id


# ---------------------------------------------------------------------------
# Snapshot round-trip
# ---------------------------------------------------------------------------


class TestPrefixSnapshot:
    def test_to_snapshot_returns_dict(self):
        prefix = make_prefix()
        snap = prefix.to_snapshot()
        assert isinstance(snap, dict)

    def test_to_snapshot_contains_expected_keys(self):
        prefix = make_prefix()
        snap = prefix.to_snapshot()
        expected_keys = {
            "network",
            "vrf_id",
            "vlan_id",
            "status",
            "role",
            "tenant_id",
            "description",
            "custom_fields",
            "tags",
            "deleted",
        }
        assert expected_keys == snap.keys()

    def test_snapshot_roundtrip_preserves_network(self):
        prefix = make_prefix(network="172.20.0.0/14")
        snap = prefix.to_snapshot()
        restored = Prefix.from_snapshot(prefix.id, snap, prefix.version)
        assert restored.network.network == "172.20.0.0/14"

    def test_snapshot_roundtrip_preserves_status(self):
        prefix = make_prefix(status=PrefixStatus.RESERVED)
        snap = prefix.to_snapshot()
        restored = Prefix.from_snapshot(prefix.id, snap, prefix.version)
        assert restored.status == PrefixStatus.RESERVED

    def test_snapshot_roundtrip_preserves_vrf_id(self):
        vrf_id = uuid4()
        prefix = make_prefix(vrf_id=vrf_id)
        snap = prefix.to_snapshot()
        restored = Prefix.from_snapshot(prefix.id, snap, prefix.version)
        assert restored.vrf_id == vrf_id

    def test_snapshot_roundtrip_preserves_tenant_id(self):
        tenant_id = uuid4()
        prefix = make_prefix(tenant_id=tenant_id)
        snap = prefix.to_snapshot()
        restored = Prefix.from_snapshot(prefix.id, snap, prefix.version)
        assert restored.tenant_id == tenant_id

    def test_snapshot_roundtrip_preserves_role(self):
        prefix = make_prefix(role="infrastructure")
        snap = prefix.to_snapshot()
        restored = Prefix.from_snapshot(prefix.id, snap, prefix.version)
        assert restored.role == "infrastructure"

    def test_snapshot_roundtrip_preserves_description(self):
        prefix = make_prefix(description="test description")
        snap = prefix.to_snapshot()
        restored = Prefix.from_snapshot(prefix.id, snap, prefix.version)
        assert restored.description == "test description"

    def test_snapshot_roundtrip_preserves_aggregate_id(self):
        prefix = make_prefix()
        snap = prefix.to_snapshot()
        restored = Prefix.from_snapshot(prefix.id, snap, prefix.version)
        assert restored.id == prefix.id

    def test_snapshot_roundtrip_preserves_version(self):
        prefix = make_prefix()
        prefix.collect_uncommitted_events()
        prefix.update(description="v2")
        snap = prefix.to_snapshot()
        restored = Prefix.from_snapshot(prefix.id, snap, prefix.version)
        assert restored.version == 2

    def test_snapshot_roundtrip_preserves_deleted_state(self):
        prefix = make_prefix()
        prefix.collect_uncommitted_events()
        prefix.delete()
        snap = prefix.to_snapshot()
        restored = Prefix.from_snapshot(prefix.id, snap, prefix.version)
        assert restored._deleted is True

    def test_snapshot_roundtrip_with_none_vrf_id(self):
        prefix = make_prefix(vrf_id=None)
        snap = prefix.to_snapshot()
        restored = Prefix.from_snapshot(prefix.id, snap, prefix.version)
        assert restored.vrf_id is None

    def test_from_snapshot_does_not_produce_uncommitted_events(self):
        prefix = make_prefix()
        snap = prefix.to_snapshot()
        restored = Prefix.from_snapshot(prefix.id, snap, prefix.version)
        assert restored.collect_uncommitted_events() == []
