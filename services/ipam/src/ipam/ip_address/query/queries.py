"""Query definitions for IPAddress read operations."""

from uuid import UUID

from shared.cqrs.query import Query

from ipam.shared.query_utils import BaseListQuery


class GetIPAddressQuery(Query):
    ip_id: UUID


class ListIPAddressesQuery(BaseListQuery):
    vrf_id: UUID | None = None
    status: str | None = None
    tenant_id: UUID | None = None
