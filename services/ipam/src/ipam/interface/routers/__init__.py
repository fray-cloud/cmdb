from ipam.interface.routers.asn_router import router as asn_router
from ipam.interface.routers.fhrp_group_router import router as fhrp_group_router
from ipam.interface.routers.ip_address_router import router as ip_address_router
from ipam.interface.routers.ip_range_router import router as ip_range_router
from ipam.interface.routers.prefix_router import router as prefix_router
from ipam.interface.routers.rir_router import router as rir_router
from ipam.interface.routers.vlan_router import router as vlan_router
from ipam.interface.routers.vrf_router import router as vrf_router

__all__ = [
    "asn_router",
    "fhrp_group_router",
    "ip_address_router",
    "ip_range_router",
    "prefix_router",
    "rir_router",
    "vlan_router",
    "vrf_router",
]
