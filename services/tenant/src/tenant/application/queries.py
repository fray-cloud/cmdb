from uuid import UUID

from shared.cqrs.query import Query


class GetTenantQuery(Query):
    tenant_id: UUID


class ListTenantsQuery(Query):
    offset: int = 0
    limit: int = 50
