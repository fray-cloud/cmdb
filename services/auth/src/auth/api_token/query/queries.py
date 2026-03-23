"""API token query definitions for CQRS read operations."""

from uuid import UUID

from shared.cqrs.query import Query


class ListAPITokensQuery(Query):
    user_id: UUID
    offset: int = 0
    limit: int = 50


class ValidateTokenQuery(Query):
    token: str
