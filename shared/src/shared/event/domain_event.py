from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class DomainEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=uuid4)
    aggregate_id: UUID
    timestamp: datetime = Field(default_factory=datetime.now)
    version: int
    event_type: str = ""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if "event_type" in cls.model_fields:
            cls.model_fields["event_type"].default = f"{cls.__module__}.{cls.__qualname__}"
            cls.model_rebuild(force=True)
