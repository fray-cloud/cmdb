from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from shared.event.domain_event import DomainEvent


class EventStore(ABC):
    @abstractmethod
    async def append(
        self,
        aggregate_id: UUID,
        events: list[DomainEvent],
        expected_version: int,
    ) -> None: ...

    @abstractmethod
    async def load_stream(
        self,
        aggregate_id: UUID,
        after_version: int = 0,
    ) -> list[DomainEvent]: ...

    @abstractmethod
    async def load_snapshot(
        self,
        aggregate_id: UUID,
    ) -> tuple[dict[str, Any], int] | None: ...

    @abstractmethod
    async def save_snapshot(
        self,
        aggregate_id: UUID,
        state: dict[str, Any],
        version: int,
    ) -> None: ...
