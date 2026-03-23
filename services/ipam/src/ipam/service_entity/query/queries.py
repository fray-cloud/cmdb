"""Service query definitions — get and list queries."""

from uuid import UUID

from shared.cqrs.query import Query

from ipam.shared.query_utils import BaseListQuery


class GetServiceQuery(Query):
    service_id: UUID


class ListServicesQuery(BaseListQuery):
    pass
