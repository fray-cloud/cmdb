from shared.cqrs.bus import QueryBus
from starlette.requests import Request

from ipam.asn.infra.repository import PostgresASNReadModelRepository
from ipam.asn.query.handlers import GetASNHandler, ListASNsHandler
from ipam.asn.query.queries import GetASNQuery, ListASNsQuery
from ipam.fhrp_group.infra.repository import PostgresFHRPGroupReadModelRepository
from ipam.fhrp_group.query.handlers import GetFHRPGroupHandler, ListFHRPGroupsHandler
from ipam.fhrp_group.query.queries import GetFHRPGroupQuery, ListFHRPGroupsQuery
from ipam.ip_address.infra.repository import PostgresIPAddressReadModelRepository
from ipam.ip_address.query.handlers import GetIPAddressHandler, ListIPAddressesHandler
from ipam.ip_address.query.queries import GetIPAddressQuery, ListIPAddressesQuery
from ipam.ip_range.infra.repository import PostgresIPRangeReadModelRepository
from ipam.ip_range.query.handlers import GetIPRangeHandler, ListIPRangesHandler
from ipam.ip_range.query.queries import GetIPRangeQuery, ListIPRangesQuery
from ipam.prefix.infra.repository import PostgresPrefixReadModelRepository
from ipam.prefix.query.handlers import GetPrefixHandler, ListPrefixesHandler
from ipam.prefix.query.queries import GetPrefixQuery, ListPrefixesQuery
from ipam.rir.infra.repository import PostgresRIRReadModelRepository
from ipam.rir.query.handlers import GetRIRHandler, ListRIRsHandler
from ipam.rir.query.queries import GetRIRQuery, ListRIRsQuery
from ipam.route_target.infra.repository import PostgresRouteTargetReadModelRepository
from ipam.route_target.query.handlers import GetRouteTargetHandler, ListRouteTargetsHandler
from ipam.route_target.query.queries import GetRouteTargetQuery, ListRouteTargetsQuery
from ipam.service_entity.infra.repository import PostgresServiceReadModelRepository
from ipam.service_entity.query.handlers import GetServiceHandler, ListServicesHandler
from ipam.service_entity.query.queries import GetServiceQuery, ListServicesQuery
from ipam.vlan.infra.repository import PostgresVLANReadModelRepository
from ipam.vlan.query.handlers import GetVLANHandler, ListVLANsHandler
from ipam.vlan.query.queries import GetVLANQuery, ListVLANsQuery
from ipam.vlan_group.infra.repository import PostgresVLANGroupReadModelRepository
from ipam.vlan_group.query.handlers import GetVLANGroupHandler, ListVLANGroupsHandler
from ipam.vlan_group.query.queries import GetVLANGroupQuery, ListVLANGroupsQuery
from ipam.vrf.infra.repository import PostgresVRFReadModelRepository
from ipam.vrf.query.handlers import GetVRFHandler, ListVRFsHandler
from ipam.vrf.query.queries import GetVRFQuery, ListVRFsQuery


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
