"""Role query definitions for CQRS read operations."""

from uuid import UUID

from shared.cqrs.query import Query


class GetRoleQuery(Query):
    role_id: UUID


class ListRolesQuery(Query):
    tenant_id: UUID
    offset: int = 0
    limit: int = 50


class CheckPermissionQuery(Query):
    user_id: UUID
    object_type: str
    action: str
