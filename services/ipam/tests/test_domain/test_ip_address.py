"""Unit tests for the IPAddress aggregate root."""

from uuid import UUID, uuid4

import pytest
from ipam.ip_address import (
    IPAddress,
    IPAddressCreated,
    IPAddressDeleted,
    IPAddressStatus,
    IPAddressStatusChanged,
    IPAddressUpdated,
)
from ipam.shared import IPAddressValue
from pydantic import ValidationError
from shared.domain.exceptions import BusinessRuleViolationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_ip(
    address: str = "192.168.1.1",
    vrf_id: UUID | None = None,
    status: IPAddressStatus = IPAddressStatus.ACTIVE,
    dns_name: str = "",
    tenant_id: UUID | None = None,
    description: str = "",
) -> IPAddress:
    return IPAddress.create(
        address=address,
        vrf_id=vrf_id,
        status=status,
        dns_name=dns_name,
        tenant_id=tenant_id,
        description=description,
    )


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------


class TestIPAddressCreate:
    def test_create_returns_ip_address_instance(self):
        ip = make_ip()
        assert isinstance(ip, IPAddress)

    def test_create_sets_address(self):
        ip = make_ip(address="10.0.0.1")
        assert isinstance(ip.address, IPAddressValue)
        assert ip.address.address == "10.0.0.1"

    def test_create_ipv4_address(self):
        ip = make_ip(address="192.168.100.200")
        assert ip.address.version == 4

    def test_create_ipv6_address(self):
        ip = make_ip(address="2001:db8::1")
        assert ip.address.version == 6
        assert ip.address.address == "2001:db8::1"

    def test_create_ipv6_loopback(self):
        ip = make_ip(address="::1")
        assert ip.address.address == "::1"

    def test_create_sets_default_status_active(self):
        ip = make_ip()
        assert ip.status == IPAddressStatus.ACTIVE

    def test_create_sets_explicit_status(self):
        ip = make_ip(status=IPAddressStatus.DHCP)
        assert ip.status == IPAddressStatus.DHCP

    def test_create_sets_vrf_id(self):
        vrf_id = uuid4()
        ip = make_ip(vrf_id=vrf_id)
        assert ip.vrf_id == vrf_id

    def test_create_sets_vrf_id_none_by_default(self):
        ip = make_ip()
        assert ip.vrf_id is None

    def test_create_sets_dns_name(self):
        ip = make_ip(dns_name="server.example.com")
        assert ip.dns_name == "server.example.com"

    def test_create_sets_empty_dns_name_by_default(self):
        ip = make_ip()
        assert ip.dns_name == ""

    def test_create_sets_tenant_id(self):
        tenant_id = uuid4()
        ip = make_ip(tenant_id=tenant_id)
        assert ip.tenant_id == tenant_id

    def test_create_sets_description(self):
        ip = make_ip(description="Gateway address")
        assert ip.description == "Gateway address"

    def test_create_version_is_1(self):
        ip = make_ip()
        assert ip.version == 1

    def test_create_is_not_deleted(self):
        ip = make_ip()
        assert ip._deleted is False

    def test_create_produces_one_event(self):
        ip = make_ip()
        events = ip.collect_uncommitted_events()
        assert len(events) == 1

    def test_create_event_type_is_ip_address_created(self):
        ip = make_ip()
        events = ip.collect_uncommitted_events()
        assert isinstance(events[0], IPAddressCreated)

    def test_create_event_has_correct_aggregate_id(self):
        ip = make_ip()
        events = ip.collect_uncommitted_events()
        assert events[0].aggregate_id == ip.id

    def test_create_event_has_version_1(self):
        ip = make_ip()
        events = ip.collect_uncommitted_events()
        assert events[0].version == 1

    def test_create_event_address_matches(self):
        ip = make_ip(address="172.16.0.1")
        events = ip.collect_uncommitted_events()
        assert events[0].address == "172.16.0.1"

    def test_create_with_invalid_address_raises(self):
        with pytest.raises((ValueError, ValidationError)):
            make_ip(address="not-an-ip")

    def test_create_assigns_unique_ids(self):
        ip1 = make_ip()
        ip2 = make_ip()
        assert ip1.id != ip2.id

    def test_collect_uncommitted_events_clears_queue(self):
        ip = make_ip()
        ip.collect_uncommitted_events()
        assert ip.collect_uncommitted_events() == []

    def test_create_slaac_status(self):
        ip = make_ip(status=IPAddressStatus.SLAAC)
        assert ip.status == IPAddressStatus.SLAAC


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------


class TestIPAddressUpdate:
    def test_update_dns_name_changes_dns_name(self):
        ip = make_ip(dns_name="old.example.com")
        ip.collect_uncommitted_events()
        ip.update(dns_name="new.example.com")
        assert ip.dns_name == "new.example.com"

    def test_update_description_changes_description(self):
        ip = make_ip(description="old")
        ip.collect_uncommitted_events()
        ip.update(description="new description")
        assert ip.description == "new description"

    def test_update_produces_ip_address_updated_event(self):
        ip = make_ip()
        ip.collect_uncommitted_events()
        ip.update(dns_name="host.local")
        events = ip.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], IPAddressUpdated)

    def test_update_increments_version(self):
        ip = make_ip()
        ip.collect_uncommitted_events()
        ip.update(description="v2")
        assert ip.version == 2

    def test_update_event_has_correct_aggregate_id(self):
        ip = make_ip()
        ip.collect_uncommitted_events()
        ip.update(description="x")
        events = ip.collect_uncommitted_events()
        assert events[0].aggregate_id == ip.id

    def test_update_with_none_args_does_not_change_existing_values(self):
        ip = make_ip(dns_name="keep.example.com", description="keep this")
        ip.collect_uncommitted_events()
        ip.update()  # all None
        assert ip.dns_name == "keep.example.com"
        assert ip.description == "keep this"

    def test_update_after_delete_raises_business_rule_violation(self):
        ip = make_ip()
        ip.collect_uncommitted_events()
        ip.delete()
        with pytest.raises(BusinessRuleViolationError, match="deleted"):
            ip.update(dns_name="should.fail")

    def test_multiple_updates_accumulate_version(self):
        ip = make_ip()
        ip.collect_uncommitted_events()
        ip.update(description="v2")
        ip.collect_uncommitted_events()
        ip.update(dns_name="v3.example.com")
        assert ip.version == 3


# ---------------------------------------------------------------------------
# change_status()
# ---------------------------------------------------------------------------


class TestIPAddressChangeStatus:
    def test_change_status_updates_status(self):
        ip = make_ip(status=IPAddressStatus.ACTIVE)
        ip.collect_uncommitted_events()
        ip.change_status(IPAddressStatus.RESERVED)
        assert ip.status == IPAddressStatus.RESERVED

    def test_change_status_to_dhcp(self):
        ip = make_ip(status=IPAddressStatus.ACTIVE)
        ip.collect_uncommitted_events()
        ip.change_status(IPAddressStatus.DHCP)
        assert ip.status == IPAddressStatus.DHCP

    def test_change_status_to_slaac(self):
        ip = make_ip(status=IPAddressStatus.ACTIVE)
        ip.collect_uncommitted_events()
        ip.change_status(IPAddressStatus.SLAAC)
        assert ip.status == IPAddressStatus.SLAAC

    def test_change_status_produces_ip_address_status_changed_event(self):
        ip = make_ip(status=IPAddressStatus.ACTIVE)
        ip.collect_uncommitted_events()
        ip.change_status(IPAddressStatus.DEPRECATED)
        events = ip.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], IPAddressStatusChanged)

    def test_change_status_event_contains_old_and_new_status(self):
        ip = make_ip(status=IPAddressStatus.ACTIVE)
        ip.collect_uncommitted_events()
        ip.change_status(IPAddressStatus.RESERVED)
        events = ip.collect_uncommitted_events()
        assert events[0].old_status == "active"
        assert events[0].new_status == "reserved"

    def test_change_status_increments_version(self):
        ip = make_ip()
        ip.collect_uncommitted_events()
        ip.change_status(IPAddressStatus.DEPRECATED)
        assert ip.version == 2

    def test_change_status_to_same_status_raises_business_rule_violation(self):
        ip = make_ip(status=IPAddressStatus.ACTIVE)
        ip.collect_uncommitted_events()
        with pytest.raises(BusinessRuleViolationError, match="already"):
            ip.change_status(IPAddressStatus.ACTIVE)

    def test_change_status_after_delete_raises_business_rule_violation(self):
        ip = make_ip()
        ip.collect_uncommitted_events()
        ip.delete()
        with pytest.raises(BusinessRuleViolationError, match="deleted"):
            ip.change_status(IPAddressStatus.RESERVED)


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------


class TestIPAddressDelete:
    def test_delete_marks_ip_address_as_deleted(self):
        ip = make_ip()
        ip.collect_uncommitted_events()
        ip.delete()
        assert ip._deleted is True

    def test_delete_produces_ip_address_deleted_event(self):
        ip = make_ip()
        ip.collect_uncommitted_events()
        ip.delete()
        events = ip.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], IPAddressDeleted)

    def test_delete_increments_version(self):
        ip = make_ip()
        ip.collect_uncommitted_events()
        ip.delete()
        assert ip.version == 2

    def test_delete_twice_raises_business_rule_violation(self):
        ip = make_ip()
        ip.collect_uncommitted_events()
        ip.delete()
        with pytest.raises(BusinessRuleViolationError, match="already deleted"):
            ip.delete()

    def test_update_after_delete_is_blocked(self):
        ip = make_ip()
        ip.collect_uncommitted_events()
        ip.delete()
        with pytest.raises(BusinessRuleViolationError):
            ip.update(dns_name="blocked.example.com")

    def test_change_status_after_delete_is_blocked(self):
        ip = make_ip()
        ip.collect_uncommitted_events()
        ip.delete()
        with pytest.raises(BusinessRuleViolationError):
            ip.change_status(IPAddressStatus.DEPRECATED)


# ---------------------------------------------------------------------------
# load_from_history()
# ---------------------------------------------------------------------------


class TestIPAddressLoadFromHistory:
    def test_load_from_history_restores_address(self):
        original = make_ip(address="10.10.10.10")
        events = original.collect_uncommitted_events()

        restored = IPAddress()
        restored.load_from_history(events)

        assert restored.address.address == "10.10.10.10"

    def test_load_from_history_restores_status(self):
        original = make_ip(status=IPAddressStatus.DHCP)
        events = original.collect_uncommitted_events()

        restored = IPAddress()
        restored.load_from_history(events)

        assert restored.status == IPAddressStatus.DHCP

    def test_load_from_history_restores_after_update(self):
        ip = make_ip(dns_name="original.example.com")
        ip.update(dns_name="updated.example.com", description="changed")
        events = ip.collect_uncommitted_events()

        restored = IPAddress()
        restored.load_from_history(events)

        assert restored.dns_name == "updated.example.com"
        assert restored.description == "changed"
        assert restored.version == 2

    def test_load_from_history_restores_status_change(self):
        ip = make_ip(status=IPAddressStatus.ACTIVE)
        ip.change_status(IPAddressStatus.RESERVED)
        events = ip.collect_uncommitted_events()

        restored = IPAddress()
        restored.load_from_history(events)

        assert restored.status == IPAddressStatus.RESERVED

    def test_load_from_history_restores_deleted_state(self):
        ip = make_ip()
        ip.delete()
        events = ip.collect_uncommitted_events()

        restored = IPAddress()
        restored.load_from_history(events)

        assert restored._deleted is True
        assert restored.version == 2

    def test_load_from_history_does_not_add_uncommitted_events(self):
        ip = make_ip()
        ip.update(description="v2")
        events = ip.collect_uncommitted_events()

        restored = IPAddress()
        restored.load_from_history(events)

        assert restored.collect_uncommitted_events() == []

    def test_load_from_history_restores_vrf_id(self):
        vrf_id = uuid4()
        ip = make_ip(vrf_id=vrf_id)
        events = ip.collect_uncommitted_events()

        restored = IPAddress()
        restored.load_from_history(events)

        assert restored.vrf_id == vrf_id

    def test_load_from_history_restores_ipv6_address(self):
        ip = make_ip(address="fd00::1")
        events = ip.collect_uncommitted_events()

        restored = IPAddress()
        restored.load_from_history(events)

        assert restored.address.address == "fd00::1"
        assert restored.address.version == 6


# ---------------------------------------------------------------------------
# Snapshot round-trip
# ---------------------------------------------------------------------------


class TestIPAddressSnapshot:
    def test_to_snapshot_returns_dict(self):
        ip = make_ip()
        snap = ip.to_snapshot()
        assert isinstance(snap, dict)

    def test_to_snapshot_contains_expected_keys(self):
        ip = make_ip()
        snap = ip.to_snapshot()
        expected = {
            "address",
            "vrf_id",
            "status",
            "dns_name",
            "tenant_id",
            "description",
            "custom_fields",
            "tags",
            "deleted",
        }
        assert expected == snap.keys()

    def test_snapshot_roundtrip_preserves_address(self):
        ip = make_ip(address="10.20.30.40")
        snap = ip.to_snapshot()
        restored = IPAddress.from_snapshot(ip.id, snap, ip.version)
        assert restored.address.address == "10.20.30.40"

    def test_snapshot_roundtrip_preserves_status(self):
        ip = make_ip(status=IPAddressStatus.SLAAC)
        snap = ip.to_snapshot()
        restored = IPAddress.from_snapshot(ip.id, snap, ip.version)
        assert restored.status == IPAddressStatus.SLAAC

    def test_snapshot_roundtrip_preserves_dns_name(self):
        ip = make_ip(dns_name="host.example.com")
        snap = ip.to_snapshot()
        restored = IPAddress.from_snapshot(ip.id, snap, ip.version)
        assert restored.dns_name == "host.example.com"

    def test_snapshot_roundtrip_preserves_vrf_id(self):
        vrf_id = uuid4()
        ip = make_ip(vrf_id=vrf_id)
        snap = ip.to_snapshot()
        restored = IPAddress.from_snapshot(ip.id, snap, ip.version)
        assert restored.vrf_id == vrf_id

    def test_snapshot_roundtrip_preserves_aggregate_id(self):
        ip = make_ip()
        snap = ip.to_snapshot()
        restored = IPAddress.from_snapshot(ip.id, snap, ip.version)
        assert restored.id == ip.id

    def test_snapshot_roundtrip_preserves_deleted_state(self):
        ip = make_ip()
        ip.collect_uncommitted_events()
        ip.delete()
        snap = ip.to_snapshot()
        restored = IPAddress.from_snapshot(ip.id, snap, ip.version)
        assert restored._deleted is True

    def test_from_snapshot_does_not_produce_uncommitted_events(self):
        ip = make_ip()
        snap = ip.to_snapshot()
        restored = IPAddress.from_snapshot(ip.id, snap, ip.version)
        assert restored.collect_uncommitted_events() == []
