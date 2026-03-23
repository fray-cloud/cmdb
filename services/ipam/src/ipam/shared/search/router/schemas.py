from uuid import UUID

from pydantic import BaseModel


class SearchResultResponse(BaseModel):
    entity_type: str
    entity_id: UUID
    display_text: str
    description: str
    relevance: float


class GlobalSearchResponse(BaseModel):
    results: list[SearchResultResponse]
    total: int
