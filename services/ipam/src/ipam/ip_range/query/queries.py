"""Query definitions for IPRange read operations."""

from uuid import UUID

from shared.cqrs.query import Query

from ipam.shared.query_utils import BaseListQuery


class GetIPRangeQuery(Query):
    range_id: UUID


class ListIPRangesQuery(BaseListQuery):
    vrf_id: UUID | None = None
    status: str | None = None
    tenant_id: UUID | None = None


class GetIPRangeUtilizationQuery(Query):
    range_id: UUID
