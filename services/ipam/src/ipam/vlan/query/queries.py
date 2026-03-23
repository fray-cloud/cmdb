from uuid import UUID

from shared.cqrs.query import Query

from ipam.shared.query_utils import BaseListQuery


class GetVLANQuery(Query):
    vlan_id: UUID


class ListVLANsQuery(BaseListQuery):
    group_id: UUID | None = None
    status: str | None = None
    tenant_id: UUID | None = None
