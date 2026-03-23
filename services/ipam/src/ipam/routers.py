"""Central router registry — collects all per-aggregate and shared routers."""

from ipam.asn.router import router as asn_router
from ipam.fhrp_group.router import router as fhrp_group_router
from ipam.ip_address.router import router as ip_address_router
from ipam.ip_range.router import router as ip_range_router
from ipam.prefix.router import router as prefix_router
from ipam.rir.router import router as rir_router
from ipam.route_target.router import router as route_target_router
from ipam.service_entity.router import router as service_router
from ipam.shared.import_export.router import router as import_export_router
from ipam.shared.saved_filter.router import router as saved_filter_router
from ipam.shared.search.router import router as search_router
from ipam.vlan.router import router as vlan_router
from ipam.vlan_group.router import router as vlan_group_router
from ipam.vrf.router import router as vrf_router

ALL_ROUTERS = [
    prefix_router,
    ip_address_router,
    vrf_router,
    vlan_router,
    ip_range_router,
    rir_router,
    asn_router,
    fhrp_group_router,
    route_target_router,
    vlan_group_router,
    service_router,
    saved_filter_router,
    search_router,
    import_export_router,
]

__all__ = ["ALL_ROUTERS"]
