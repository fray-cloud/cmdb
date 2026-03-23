"""IPAM event projector — registers all domain event handlers with Kafka consumer."""

import logging
from functools import partial

from shared.messaging.consumer import KafkaEventConsumer

from ipam.asn import ASNCreated, ASNDeleted, ASNUpdated
from ipam.asn.infra import handle_asn_created, handle_asn_deleted, handle_asn_updated
from ipam.fhrp_group import FHRPGroupCreated, FHRPGroupDeleted, FHRPGroupUpdated
from ipam.fhrp_group.infra import (
    handle_fhrp_group_created,
    handle_fhrp_group_deleted,
    handle_fhrp_group_updated,
)
from ipam.ip_address import IPAddressCreated, IPAddressDeleted, IPAddressStatusChanged, IPAddressUpdated
from ipam.ip_address.infra import (
    handle_ip_address_created,
    handle_ip_address_deleted,
    handle_ip_address_status_changed,
    handle_ip_address_updated,
)
from ipam.ip_range import IPRangeCreated, IPRangeDeleted, IPRangeStatusChanged, IPRangeUpdated
from ipam.ip_range.infra import (
    handle_ip_range_created,
    handle_ip_range_deleted,
    handle_ip_range_status_changed,
    handle_ip_range_updated,
)
from ipam.prefix import PrefixCreated, PrefixDeleted, PrefixStatusChanged, PrefixUpdated
from ipam.prefix.infra import (
    handle_prefix_created,
    handle_prefix_deleted,
    handle_prefix_status_changed,
    handle_prefix_updated,
)
from ipam.rir import RIRCreated, RIRDeleted, RIRUpdated
from ipam.rir.infra import handle_rir_created, handle_rir_deleted, handle_rir_updated
from ipam.route_target import RouteTargetCreated, RouteTargetDeleted, RouteTargetUpdated
from ipam.route_target.infra import (
    handle_route_target_created,
    handle_route_target_deleted,
    handle_route_target_updated,
)
from ipam.service_entity import ServiceCreated, ServiceDeleted, ServiceUpdated
from ipam.service_entity.infra import handle_service_created, handle_service_deleted, handle_service_updated
from ipam.vlan import VLANCreated, VLANDeleted, VLANStatusChanged, VLANUpdated
from ipam.vlan.infra import (
    handle_vlan_created,
    handle_vlan_deleted,
    handle_vlan_status_changed,
    handle_vlan_updated,
)
from ipam.vlan_group import VLANGroupCreated, VLANGroupDeleted, VLANGroupUpdated
from ipam.vlan_group.infra import (
    handle_vlan_group_created,
    handle_vlan_group_deleted,
    handle_vlan_group_updated,
)
from ipam.vrf import VRFCreated, VRFDeleted, VRFUpdated
from ipam.vrf.infra import handle_vrf_created, handle_vrf_deleted, handle_vrf_updated

logger = logging.getLogger(__name__)


class IPAMEventProjector:
    """Registers all IPAM domain event handlers for read model projection."""

    def __init__(self, session_factory: object, cache: object | None = None) -> None:
        self._session_factory = session_factory
        self._cache = cache

    def register_all(self, consumer: KafkaEventConsumer) -> None:
        sf = self._session_factory
        cache = self._cache

        # Prefix
        consumer.subscribe(PrefixCreated, partial(handle_prefix_created, sf, cache))
        consumer.subscribe(PrefixUpdated, partial(handle_prefix_updated, sf, cache))
        consumer.subscribe(PrefixStatusChanged, partial(handle_prefix_status_changed, sf, cache))
        consumer.subscribe(PrefixDeleted, partial(handle_prefix_deleted, sf, cache))

        # IPAddress
        consumer.subscribe(IPAddressCreated, partial(handle_ip_address_created, sf, cache))
        consumer.subscribe(IPAddressUpdated, partial(handle_ip_address_updated, sf, cache))
        consumer.subscribe(IPAddressStatusChanged, partial(handle_ip_address_status_changed, sf, cache))
        consumer.subscribe(IPAddressDeleted, partial(handle_ip_address_deleted, sf, cache))

        # VRF
        consumer.subscribe(VRFCreated, partial(handle_vrf_created, sf, cache))
        consumer.subscribe(VRFUpdated, partial(handle_vrf_updated, sf, cache))
        consumer.subscribe(VRFDeleted, partial(handle_vrf_deleted, sf, cache))

        # VLAN
        consumer.subscribe(VLANCreated, partial(handle_vlan_created, sf, cache))
        consumer.subscribe(VLANUpdated, partial(handle_vlan_updated, sf, cache))
        consumer.subscribe(VLANStatusChanged, partial(handle_vlan_status_changed, sf, cache))
        consumer.subscribe(VLANDeleted, partial(handle_vlan_deleted, sf, cache))

        # IPRange
        consumer.subscribe(IPRangeCreated, partial(handle_ip_range_created, sf, cache))
        consumer.subscribe(IPRangeUpdated, partial(handle_ip_range_updated, sf, cache))
        consumer.subscribe(IPRangeStatusChanged, partial(handle_ip_range_status_changed, sf, cache))
        consumer.subscribe(IPRangeDeleted, partial(handle_ip_range_deleted, sf, cache))

        # RIR
        consumer.subscribe(RIRCreated, partial(handle_rir_created, sf, cache))
        consumer.subscribe(RIRUpdated, partial(handle_rir_updated, sf, cache))
        consumer.subscribe(RIRDeleted, partial(handle_rir_deleted, sf, cache))

        # ASN
        consumer.subscribe(ASNCreated, partial(handle_asn_created, sf, cache))
        consumer.subscribe(ASNUpdated, partial(handle_asn_updated, sf, cache))
        consumer.subscribe(ASNDeleted, partial(handle_asn_deleted, sf, cache))

        # FHRPGroup
        consumer.subscribe(FHRPGroupCreated, partial(handle_fhrp_group_created, sf, cache))
        consumer.subscribe(FHRPGroupUpdated, partial(handle_fhrp_group_updated, sf, cache))
        consumer.subscribe(FHRPGroupDeleted, partial(handle_fhrp_group_deleted, sf, cache))

        # RouteTarget
        consumer.subscribe(RouteTargetCreated, partial(handle_route_target_created, sf, cache))
        consumer.subscribe(RouteTargetUpdated, partial(handle_route_target_updated, sf, cache))
        consumer.subscribe(RouteTargetDeleted, partial(handle_route_target_deleted, sf, cache))

        # VLANGroup
        consumer.subscribe(VLANGroupCreated, partial(handle_vlan_group_created, sf, cache))
        consumer.subscribe(VLANGroupUpdated, partial(handle_vlan_group_updated, sf, cache))
        consumer.subscribe(VLANGroupDeleted, partial(handle_vlan_group_deleted, sf, cache))

        # Service
        consumer.subscribe(ServiceCreated, partial(handle_service_created, sf, cache))
        consumer.subscribe(ServiceUpdated, partial(handle_service_updated, sf, cache))
        consumer.subscribe(ServiceDeleted, partial(handle_service_deleted, sf, cache))
