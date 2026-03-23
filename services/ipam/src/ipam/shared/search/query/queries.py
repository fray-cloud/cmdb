"""Global search query definitions."""

from shared.cqrs.query import Query


class GlobalSearchQuery(Query):
    q: str
    entity_types: list[str] | None = None
    offset: int = 0
    limit: int = 20
