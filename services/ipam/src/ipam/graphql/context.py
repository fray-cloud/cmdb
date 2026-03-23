"""GraphQL context factory — builds query bus with all IPAM handlers per request."""

from shared.cqrs.bus import QueryBus
from starlette.requests import Request

from ipam.asn.infra import PostgresASNReadModelRepository
from ipam.asn.query import GetASNHandler, GetASNQuery, ListASNsHandler, ListASNsQuery
from ipam.fhrp_group.infra import PostgresFHRPGroupReadModelRepository
from ipam.fhrp_group.query import GetFHRPGroupHandler, GetFHRPGroupQuery, ListFHRPGroupsHandler, ListFHRPGroupsQuery
from ipam.ip_address.infra import PostgresIPAddressReadModelRepository
from ipam.ip_address.query import GetIPAddressHandler, GetIPAddressQuery, ListIPAddressesHandler, ListIPAddressesQuery
from ipam.ip_range.infra import PostgresIPRangeReadModelRepository
from ipam.ip_range.query import GetIPRangeHandler, GetIPRangeQuery, ListIPRangesHandler, ListIPRangesQuery
from ipam.prefix.infra import PostgresPrefixReadModelRepository
from ipam.prefix.query import GetPrefixHandler, GetPrefixQuery, ListPrefixesHandler, ListPrefixesQuery
from ipam.rir.infra import PostgresRIRReadModelRepository
from ipam.rir.query import GetRIRHandler, GetRIRQuery, ListRIRsHandler, ListRIRsQuery
from ipam.route_target.infra import PostgresRouteTargetReadModelRepository
from ipam.route_target.query import (
    GetRouteTargetHandler,
    GetRouteTargetQuery,
    ListRouteTargetsHandler,
    ListRouteTargetsQuery,
)
from ipam.service_entity.infra import PostgresServiceReadModelRepository
from ipam.service_entity.query import GetServiceHandler, GetServiceQuery, ListServicesHandler, ListServicesQuery
from ipam.vlan.infra import PostgresVLANReadModelRepository
from ipam.vlan.query import GetVLANHandler, GetVLANQuery, ListVLANsHandler, ListVLANsQuery
from ipam.vlan_group.infra import PostgresVLANGroupReadModelRepository
from ipam.vlan_group.query import GetVLANGroupHandler, GetVLANGroupQuery, ListVLANGroupsHandler, ListVLANGroupsQuery
from ipam.vrf.infra import PostgresVRFReadModelRepository
from ipam.vrf.query import GetVRFHandler, GetVRFQuery, ListVRFsHandler, ListVRFsQuery


async def get_graphql_context(request: Request) -> dict:
    database = request.app.state.database
    session = database.session()

    # Build query bus with all handlers
    query_bus = QueryBus()

    prefix_repo = PostgresPrefixReadModelRepository(session)
    ip_repo = PostgresIPAddressReadModelRepository(session)
    vrf_repo = PostgresVRFReadModelRepository(session)
    vlan_repo = PostgresVLANReadModelRepository(session)
    ip_range_repo = PostgresIPRangeReadModelRepository(session)
    rir_repo = PostgresRIRReadModelRepository(session)
    asn_repo = PostgresASNReadModelRepository(session)
    fhrp_group_repo = PostgresFHRPGroupReadModelRepository(session)
    route_target_repo = PostgresRouteTargetReadModelRepository(session)
    vlan_group_repo = PostgresVLANGroupReadModelRepository(session)
    service_repo = PostgresServiceReadModelRepository(session)

    query_bus.register(GetPrefixQuery, GetPrefixHandler(prefix_repo))
    query_bus.register(ListPrefixesQuery, ListPrefixesHandler(prefix_repo))
    query_bus.register(GetIPAddressQuery, GetIPAddressHandler(ip_repo))
    query_bus.register(ListIPAddressesQuery, ListIPAddressesHandler(ip_repo))
    query_bus.register(GetVRFQuery, GetVRFHandler(vrf_repo))
    query_bus.register(ListVRFsQuery, ListVRFsHandler(vrf_repo))
    query_bus.register(GetVLANQuery, GetVLANHandler(vlan_repo))
    query_bus.register(ListVLANsQuery, ListVLANsHandler(vlan_repo))
    query_bus.register(GetIPRangeQuery, GetIPRangeHandler(ip_range_repo))
    query_bus.register(ListIPRangesQuery, ListIPRangesHandler(ip_range_repo))
    query_bus.register(GetRIRQuery, GetRIRHandler(rir_repo))
    query_bus.register(ListRIRsQuery, ListRIRsHandler(rir_repo))
    query_bus.register(GetASNQuery, GetASNHandler(asn_repo))
    query_bus.register(ListASNsQuery, ListASNsHandler(asn_repo))
    query_bus.register(GetFHRPGroupQuery, GetFHRPGroupHandler(fhrp_group_repo))
    query_bus.register(ListFHRPGroupsQuery, ListFHRPGroupsHandler(fhrp_group_repo))
    query_bus.register(GetRouteTargetQuery, GetRouteTargetHandler(route_target_repo))
    query_bus.register(ListRouteTargetsQuery, ListRouteTargetsHandler(route_target_repo))
    query_bus.register(GetVLANGroupQuery, GetVLANGroupHandler(vlan_group_repo))
    query_bus.register(ListVLANGroupsQuery, ListVLANGroupsHandler(vlan_group_repo))
    query_bus.register(GetServiceQuery, GetServiceHandler(service_repo))
    query_bus.register(ListServicesQuery, ListServicesHandler(service_repo))

    return {"query_bus": query_bus}
