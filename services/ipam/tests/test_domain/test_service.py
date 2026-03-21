"""Unit tests for the Service aggregate root."""

from uuid import uuid4

import pytest
from ipam.domain.events import ServiceCreated, ServiceDeleted, ServiceUpdated
from ipam.domain.service import Service
from ipam.domain.value_objects import ServiceProtocol

from shared.domain.exceptions import BusinessRuleViolationError


def make_service(
    name: str = "HTTP",
    protocol: ServiceProtocol = ServiceProtocol.TCP,
    ports: list[int] | None = None,
    ip_addresses: list | None = None,
    description: str = "",
    custom_fields: dict | None = None,
    tags: list | None = None,
) -> Service:
    return Service.create(
        name=name,
        protocol=protocol,
        ports=ports or [80],
        ip_addresses=ip_addresses,
        description=description,
        custom_fields=custom_fields,
        tags=tags,
    )


class TestServiceCreate:
    def test_create_returns_instance(self):
        assert isinstance(make_service(), Service)

    def test_create_sets_fields(self):
        svc = make_service(name="SSH", protocol=ServiceProtocol.TCP, ports=[22])
        assert svc.name == "SSH"
        assert svc.protocol == ServiceProtocol.TCP
        assert svc.ports == [22]

    def test_create_with_ip_addresses(self):
        ip_id = uuid4()
        svc = make_service(ip_addresses=[ip_id])
        assert svc.ip_addresses == [ip_id]

    def test_create_emits_event(self):
        events = make_service().collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ServiceCreated)

    def test_create_version_is_1(self):
        assert make_service().version == 1

    def test_create_empty_ports_raises_error(self):
        with pytest.raises(BusinessRuleViolationError, match="at least one port"):
            Service.create(name="Test", protocol=ServiceProtocol.TCP, ports=[])

    def test_create_invalid_port_raises_error(self):
        with pytest.raises(BusinessRuleViolationError):
            make_service(ports=[0])

    def test_create_port_too_large_raises_error(self):
        with pytest.raises(BusinessRuleViolationError):
            make_service(ports=[70000])

    def test_create_multiple_ports(self):
        svc = make_service(ports=[80, 443, 8080])
        assert svc.ports == [80, 443, 8080]


class TestServiceUpdate:
    def test_update_name(self):
        svc = make_service()
        svc.collect_uncommitted_events()
        svc.update(name="HTTPS")
        assert svc.name == "HTTPS"

    def test_update_ports(self):
        svc = make_service()
        svc.collect_uncommitted_events()
        svc.update(ports=[443])
        assert svc.ports == [443]

    def test_update_protocol(self):
        svc = make_service()
        svc.collect_uncommitted_events()
        svc.update(protocol="udp")
        assert svc.protocol == ServiceProtocol.UDP

    def test_update_invalid_ports(self):
        svc = make_service()
        svc.collect_uncommitted_events()
        with pytest.raises(BusinessRuleViolationError):
            svc.update(ports=[0])

    def test_update_produces_event(self):
        svc = make_service()
        svc.collect_uncommitted_events()
        svc.update(name="new")
        events = svc.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ServiceUpdated)

    def test_update_deleted_raises_error(self):
        svc = make_service()
        svc.collect_uncommitted_events()
        svc.delete()
        with pytest.raises(BusinessRuleViolationError, match="deleted"):
            svc.update(name="fail")


class TestServiceDelete:
    def test_delete_marks_deleted(self):
        svc = make_service()
        svc.collect_uncommitted_events()
        svc.delete()
        assert svc._deleted is True

    def test_delete_produces_event(self):
        svc = make_service()
        svc.collect_uncommitted_events()
        svc.delete()
        events = svc.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ServiceDeleted)

    def test_double_delete_raises_error(self):
        svc = make_service()
        svc.collect_uncommitted_events()
        svc.delete()
        with pytest.raises(BusinessRuleViolationError, match="already deleted"):
            svc.delete()


class TestServiceLoadFromHistory:
    def test_load_from_history_restores_state(self):
        ip_id = uuid4()
        original = make_service(name="HTTP", ports=[80, 443], ip_addresses=[ip_id])
        original.update(name="HTTPS", ports=[443])
        original.delete()
        events = original.collect_uncommitted_events()

        restored = Service()
        restored.load_from_history(events)
        assert restored.name == "HTTPS"
        assert restored.ports == [443]
        assert restored.ip_addresses == [ip_id]
        assert restored._deleted is True
        assert restored.version == 3


class TestServiceSnapshot:
    def test_snapshot_roundtrip(self):
        tag_id = uuid4()
        ip_id = uuid4()
        svc = make_service(
            name="DNS",
            protocol=ServiceProtocol.UDP,
            ports=[53],
            ip_addresses=[ip_id],
            description="DNS server",
            custom_fields={"zone": "internal"},
            tags=[tag_id],
        )
        snap = svc.to_snapshot()
        restored = Service.from_snapshot(svc.id, snap, svc.version)
        assert restored.name == "DNS"
        assert restored.protocol == ServiceProtocol.UDP
        assert restored.ports == [53]
        assert restored.ip_addresses == [ip_id]
        assert restored.description == "DNS server"
        assert restored.custom_fields == {"zone": "internal"}
        assert restored.tags == [tag_id]
        assert restored.id == svc.id
