from uuid import UUID

from shared.cqrs.query import Query

from ipam.shared.query_utils import BaseListQuery


class GetASNQuery(Query):
    asn_id: UUID


class ListASNsQuery(BaseListQuery):
    rir_id: UUID | None = None
    tenant_id: UUID | None = None
