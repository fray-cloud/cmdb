"""ASN data transfer objects for query results."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ASNDTO(BaseModel):
    id: UUID
    asn: int
    rir_id: UUID | None
    tenant_id: UUID | None
    description: str
    custom_fields: dict
    tags: list[UUID]
    created_at: datetime
    updated_at: datetime
