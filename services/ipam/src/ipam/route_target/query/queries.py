from uuid import UUID

from shared.cqrs.query import Query

from ipam.shared.query_utils import BaseListQuery


class GetRouteTargetQuery(Query):
    route_target_id: UUID


class ListRouteTargetsQuery(BaseListQuery):
    tenant_id: UUID | None = None
