"""Saved filter query definitions — get and list queries."""

from uuid import UUID

from shared.cqrs.query import Query


class GetSavedFilterQuery(Query):
    filter_id: UUID


class ListSavedFiltersQuery(Query):
    user_id: UUID
    entity_type: str | None = None
