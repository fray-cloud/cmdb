"""Event flow tests: EventSerializer serialization/deserialization roundtrip for all IPAM events.

No Docker required — these run as regular (non-integration) tests.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from ipam.asn.domain.events import ASNCreated, ASNDeleted, ASNUpdated
from ipam.fhrp_group.domain.events import FHRPGroupCreated, FHRPGroupDeleted, FHRPGroupUpdated
from ipam.ip_address.domain.events import (
    IPAddressCreated,
    IPAddressDeleted,
    IPAddressStatusChanged,
    IPAddressUpdated,
)
from ipam.ip_range.domain.events import (
    IPRangeCreated,
    IPRangeDeleted,
    IPRangeStatusChanged,
    IPRangeUpdated,
)
from ipam.prefix.domain.events import (
    PrefixCreated,
    PrefixDeleted,
    PrefixStatusChanged,
    PrefixUpdated,
)
from ipam.rir.domain.events import RIRCreated, RIRDeleted, RIRUpdated
from ipam.route_target.domain.events import RouteTargetCreated, RouteTargetDeleted, RouteTargetUpdated
from ipam.service_entity.domain.events import ServiceCreated, ServiceDeleted, ServiceUpdated
from ipam.vlan.domain.events import VLANCreated, VLANDeleted, VLANStatusChanged, VLANUpdated
from ipam.vlan_group.domain.events import VLANGroupCreated, VLANGroupDeleted, VLANGroupUpdated
from ipam.vrf.domain.events import VRFCreated, VRFDeleted, VRFUpdated
from shared.messaging.serialization import EventSerializer


def _make_serializer() -> EventSerializer:
    """Create an EventSerializer with all IPAM event types registered."""
    serializer = EventSerializer()
    all_event_types = [
        PrefixCreated,
        PrefixUpdated,
        PrefixDeleted,
        PrefixStatusChanged,
        IPAddressCreated,
        IPAddressUpdated,
        IPAddressDeleted,
        IPAddressStatusChanged,
        IPRangeCreated,
        IPRangeUpdated,
        IPRangeDeleted,
        IPRangeStatusChanged,
        VRFCreated,
        VRFUpdated,
        VRFDeleted,
        VLANCreated,
        VLANUpdated,
        VLANDeleted,
        VLANStatusChanged,
        VLANGroupCreated,
        VLANGroupUpdated,
        VLANGroupDeleted,
        RIRCreated,
        RIRUpdated,
        RIRDeleted,
        ASNCreated,
        ASNUpdated,
        ASNDeleted,
        FHRPGroupCreated,
        FHRPGroupUpdated,
        FHRPGroupDeleted,
        RouteTargetCreated,
        RouteTargetUpdated,
        RouteTargetDeleted,
        ServiceCreated,
        ServiceUpdated,
        ServiceDeleted,
    ]
    for event_cls in all_event_types:
        serializer.register(event_cls)
    return serializer


def _make_sample_events() -> list:
    """Create one sample instance of each IPAM event type."""
    agg_id = uuid4()
    vrf_id = uuid4()
    vlan_id = uuid4()
    tenant_id = uuid4()
    rir_id = uuid4()
    group_id = uuid4()
    tag_id = uuid4()
    ip_addr_id = uuid4()

    return [
        # Prefix events
        PrefixCreated(
            aggregate_id=agg_id,
            version=1,
            network="10.0.0.0/8",
            vrf_id=vrf_id,
            vlan_id=vlan_id,
            status="active",
            role="infrastructure",
            tenant_id=tenant_id,
            description="Test prefix",
            custom_fields={"site": "dc1"},
            tags=[tag_id],
        ),
        PrefixUpdated(
            aggregate_id=agg_id,
            version=2,
            description="Updated description",
            role="production",
        ),
        PrefixDeleted(
            aggregate_id=agg_id,
            version=3,
        ),
        PrefixStatusChanged(
            aggregate_id=agg_id,
            version=2,
            old_status="active",
            new_status="reserved",
        ),
        # IPAddress events
        IPAddressCreated(
            aggregate_id=uuid4(),
            version=1,
            address="10.0.0.1/32",
            vrf_id=vrf_id,
            status="active",
            dns_name="host1.example.com",
            tenant_id=tenant_id,
            description="Host 1",
            custom_fields={"env": "prod"},
            tags=[tag_id],
        ),
        IPAddressUpdated(
            aggregate_id=uuid4(),
            version=2,
            dns_name="host1-updated.example.com",
            description="Updated host",
        ),
        IPAddressDeleted(
            aggregate_id=uuid4(),
            version=3,
        ),
        IPAddressStatusChanged(
            aggregate_id=uuid4(),
            version=2,
            old_status="active",
            new_status="deprecated",
        ),
        # IPRange events
        IPRangeCreated(
            aggregate_id=uuid4(),
            version=1,
            start_address="10.0.0.1",
            end_address="10.0.0.255",
            vrf_id=vrf_id,
            status="active",
            tenant_id=tenant_id,
            description="Range 1",
        ),
        IPRangeUpdated(
            aggregate_id=uuid4(),
            version=2,
            description="Updated range",
        ),
        IPRangeDeleted(
            aggregate_id=uuid4(),
            version=3,
        ),
        IPRangeStatusChanged(
            aggregate_id=uuid4(),
            version=2,
            old_status="active",
            new_status="reserved",
        ),
        # VRF events
        VRFCreated(
            aggregate_id=uuid4(),
            version=1,
            name="VRF-1",
            rd="65000:1",
            import_targets=[uuid4()],
            export_targets=[uuid4()],
            tenant_id=tenant_id,
            description="Test VRF",
        ),
        VRFUpdated(
            aggregate_id=uuid4(),
            version=2,
            name="VRF-1-updated",
            description="Updated VRF",
        ),
        VRFDeleted(
            aggregate_id=uuid4(),
            version=3,
        ),
        # VLAN events
        VLANCreated(
            aggregate_id=uuid4(),
            version=1,
            vid=100,
            name="VLAN-100",
            group_id=group_id,
            status="active",
            role="production",
            tenant_id=tenant_id,
            description="Production VLAN",
        ),
        VLANUpdated(
            aggregate_id=uuid4(),
            version=2,
            name="VLAN-100-updated",
        ),
        VLANDeleted(
            aggregate_id=uuid4(),
            version=3,
        ),
        VLANStatusChanged(
            aggregate_id=uuid4(),
            version=2,
            old_status="active",
            new_status="deprecated",
        ),
        # VLANGroup events
        VLANGroupCreated(
            aggregate_id=uuid4(),
            version=1,
            name="Group-1",
            slug="group-1",
            min_vid=1,
            max_vid=4094,
            tenant_id=tenant_id,
            description="Test group",
        ),
        VLANGroupUpdated(
            aggregate_id=uuid4(),
            version=2,
            name="Group-1-updated",
        ),
        VLANGroupDeleted(
            aggregate_id=uuid4(),
            version=3,
        ),
        # RIR events
        RIRCreated(
            aggregate_id=uuid4(),
            version=1,
            name="ARIN",
            is_private=False,
            description="American Registry",
        ),
        RIRUpdated(
            aggregate_id=uuid4(),
            version=2,
            description="Updated RIR",
            is_private=True,
        ),
        RIRDeleted(
            aggregate_id=uuid4(),
            version=3,
        ),
        # ASN events
        ASNCreated(
            aggregate_id=uuid4(),
            version=1,
            asn=65000,
            rir_id=rir_id,
            tenant_id=tenant_id,
            description="Test ASN",
        ),
        ASNUpdated(
            aggregate_id=uuid4(),
            version=2,
            description="Updated ASN",
        ),
        ASNDeleted(
            aggregate_id=uuid4(),
            version=3,
        ),
        # FHRPGroup events
        FHRPGroupCreated(
            aggregate_id=uuid4(),
            version=1,
            protocol="vrrp",
            group_id_value=1,
            auth_type="plaintext",
            auth_key="secret",
            name="FHRP-1",
            description="Test FHRP",
        ),
        FHRPGroupUpdated(
            aggregate_id=uuid4(),
            version=2,
            name="FHRP-1-updated",
        ),
        FHRPGroupDeleted(
            aggregate_id=uuid4(),
            version=3,
        ),
        # RouteTarget events
        RouteTargetCreated(
            aggregate_id=uuid4(),
            version=1,
            name="65000:100",
            tenant_id=tenant_id,
            description="Test RT",
        ),
        RouteTargetUpdated(
            aggregate_id=uuid4(),
            version=2,
            description="Updated RT",
        ),
        RouteTargetDeleted(
            aggregate_id=uuid4(),
            version=3,
        ),
        # Service events
        ServiceCreated(
            aggregate_id=uuid4(),
            version=1,
            name="HTTP",
            protocol="tcp",
            ports=[80, 443],
            ip_addresses=[ip_addr_id],
            description="Web service",
        ),
        ServiceUpdated(
            aggregate_id=uuid4(),
            version=2,
            name="HTTPS",
            ports=[443],
        ),
        ServiceDeleted(
            aggregate_id=uuid4(),
            version=3,
        ),
    ]


class TestEventSerializerRoundtrip:
    """Verify serialize → deserialize roundtrip for every IPAM event type."""

    @pytest.fixture
    def serializer(self) -> EventSerializer:
        return _make_serializer()

    @pytest.fixture
    def sample_events(self) -> list:
        return _make_sample_events()

    async def test_all_events_roundtrip(self, serializer: EventSerializer, sample_events: list) -> None:
        """Every IPAM event should survive a serialize/deserialize roundtrip."""
        for original in sample_events:
            serialized = serializer.serialize(original)
            assert isinstance(serialized, bytes)

            deserialized = serializer.deserialize(serialized)
            assert type(deserialized) is type(original), (
                f"Type mismatch: expected {type(original).__name__}, got {type(deserialized).__name__}"
            )
            assert deserialized.aggregate_id == original.aggregate_id
            assert deserialized.version == original.version
            assert deserialized.event_type == original.event_type

    @pytest.mark.parametrize(
        "event",
        _make_sample_events(),
        ids=lambda e: type(e).__name__,
    )
    async def test_individual_event_roundtrip(self, serializer: EventSerializer, event) -> None:
        """Parameterized test: each event type individually."""
        serialized = serializer.serialize(event)
        deserialized = serializer.deserialize(serialized)

        assert type(deserialized) is type(event)
        assert deserialized.aggregate_id == event.aggregate_id
        assert deserialized.version == event.version

        # Compare all non-meta fields
        original_data = event.model_dump(exclude={"event_id", "timestamp"})
        roundtrip_data = deserialized.model_dump(exclude={"event_id", "timestamp"})
        assert roundtrip_data == original_data, (
            f"Field mismatch for {type(event).__name__}: {original_data} != {roundtrip_data}"
        )

    async def test_serialized_format_is_json_bytes(self, serializer: EventSerializer) -> None:
        """Serialized output should be valid JSON bytes."""
        import json

        event = PrefixCreated(
            aggregate_id=uuid4(),
            version=1,
            network="10.0.0.0/8",
        )
        serialized = serializer.serialize(event)
        parsed = json.loads(serialized)
        assert isinstance(parsed, dict)
        assert parsed["network"] == "10.0.0.0/8"
        assert "event_type" in parsed

    async def test_event_type_field_contains_module_path(self, serializer: EventSerializer) -> None:
        """The event_type field should contain the full module-qualified name."""
        event = PrefixCreated(
            aggregate_id=uuid4(),
            version=1,
            network="10.0.0.0/8",
        )
        assert "PrefixCreated" in event.event_type
        assert "ipam.prefix.domain.events" in event.event_type
