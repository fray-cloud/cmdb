from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Tag(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    slug: str
    color: str = "#9e9e9e"
