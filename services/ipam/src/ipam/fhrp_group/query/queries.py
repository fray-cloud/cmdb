"""FHRP Group query definitions — get and list queries."""

from uuid import UUID

from shared.cqrs.query import Query

from ipam.shared.query_utils import BaseListQuery


class GetFHRPGroupQuery(Query):
    fhrp_group_id: UUID


class ListFHRPGroupsQuery(BaseListQuery):
    pass
