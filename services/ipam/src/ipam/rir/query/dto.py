"""RIR data transfer objects for query results."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RIRDTO(BaseModel):
    id: UUID
    name: str
    is_private: bool
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime
