from uuid import UUID

from shared.cqrs.query import Query


class GetUserQuery(Query):
    user_id: UUID


class ListUsersQuery(Query):
    tenant_id: UUID
    offset: int = 0
    limit: int = 50
