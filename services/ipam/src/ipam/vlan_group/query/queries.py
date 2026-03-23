from uuid import UUID

from shared.cqrs.query import Query

from ipam.shared.query_utils import BaseListQuery


class GetVLANGroupQuery(Query):
    vlan_group_id: UUID


class ListVLANGroupsQuery(BaseListQuery):
    tenant_id: UUID | None = None
