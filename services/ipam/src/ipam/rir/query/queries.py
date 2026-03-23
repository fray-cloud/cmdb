"""RIR query definitions — get and list queries."""

from uuid import UUID

from shared.cqrs.query import Query

from ipam.shared.query_utils import BaseListQuery


class GetRIRQuery(Query):
    rir_id: UUID


class ListRIRsQuery(BaseListQuery):
    pass
