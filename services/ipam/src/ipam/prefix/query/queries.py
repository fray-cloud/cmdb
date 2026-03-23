from uuid import UUID

from shared.cqrs.query import Query

from ipam.shared.query_utils import BaseListQuery


class GetPrefixQuery(Query):
    prefix_id: UUID


class ListPrefixesQuery(BaseListQuery):
    vrf_id: UUID | None = None
    status: str | None = None
    tenant_id: UUID | None = None
    role: str | None = None


class GetPrefixChildrenQuery(Query):
    prefix_id: UUID


class GetPrefixUtilizationQuery(Query):
    prefix_id: UUID


class GetAvailablePrefixesQuery(Query):
    prefix_id: UUID
    desired_prefix_length: int


class GetAvailableIPsQuery(Query):
    prefix_id: UUID
    count: int = 1
