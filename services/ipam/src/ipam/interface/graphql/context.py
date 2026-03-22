from starlette.requests import Request

from ipam.application.queries import (
    GetASNQuery,
    GetFHRPGroupQuery,
    GetIPAddressQuery,
    GetIPRangeQuery,
    GetPrefixQuery,
    GetRIRQuery,
    GetRouteTargetQuery,
    GetServiceQuery,
    GetVLANGroupQuery,
    GetVLANQuery,
    GetVRFQuery,
    ListASNsQuery,
    ListFHRPGroupsQuery,
    ListIPAddressesQuery,
    ListIPRangesQuery,
    ListPrefixesQuery,
    ListRIRsQuery,
    ListRouteTargetsQuery,
    ListServicesQuery,
    ListVLANGroupsQuery,
    ListVLANsQuery,
    ListVRFsQuery,
)
from ipam.application.query_handlers import (
    GetASNHandler,
    GetFHRPGroupHandler,
    GetIPAddressHandler,
    GetIPRangeHandler,
    GetPrefixHandler,
    GetRIRHandler,
    GetRouteTargetHandler,
    GetServiceHandler,
    GetVLANGroupHandler,
    GetVLANHandler,
    GetVRFHandler,
    ListASNsHandler,
    ListFHRPGroupsHandler,
    ListIPAddressesHandler,
    ListIPRangesHandler,
    ListPrefixesHandler,
    ListRIRsHandler,
    ListRouteTargetsHandler,
    ListServicesHandler,
    ListVLANGroupsHandler,
    ListVLANsHandler,
    ListVRFsHandler,
)
from ipam.infrastructure.read_model_repository import (
    PostgresASNReadModelRepository,
    PostgresFHRPGroupReadModelRepository,
    PostgresIPAddressReadModelRepository,
    PostgresIPRangeReadModelRepository,
    PostgresPrefixReadModelRepository,
    PostgresRIRReadModelRepository,
    PostgresRouteTargetReadModelRepository,
    PostgresServiceReadModelRepository,
    PostgresVLANGroupReadModelRepository,
    PostgresVLANReadModelRepository,
    PostgresVRFReadModelRepository,
)
from shared.cqrs.bus import QueryBus


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
