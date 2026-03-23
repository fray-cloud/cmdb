from uuid import UUID

from shared.cqrs.query import Query

from ipam.shared.query_utils import BaseListQuery


class GetVRFQuery(Query):
    vrf_id: UUID


class ListVRFsQuery(BaseListQuery):
    tenant_id: UUID | None = None
