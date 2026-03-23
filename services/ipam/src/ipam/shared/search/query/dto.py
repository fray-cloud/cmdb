from uuid import UUID

from pydantic import BaseModel


class SearchResultDTO(BaseModel):
    entity_type: str
    entity_id: UUID
    display_text: str
    description: str
    relevance: float


class GlobalSearchResultDTO(BaseModel):
    results: list[SearchResultDTO]
    total: int
