from typing import Any, Self
from uuid import UUID, uuid4

from shared.event.domain_event import DomainEvent


class AggregateRoot:
    def __init__(self, aggregate_id: UUID | None = None) -> None:
        self.id: UUID = aggregate_id or uuid4()
        self.version: int = 0
        self._uncommitted_events: list[DomainEvent] = []

    def apply_event(self, event: DomainEvent, *, is_new: bool = True) -> None:
        self._apply(event)
        self.version = event.version
        if is_new:
            self._uncommitted_events.append(event)

    def _apply(self, event: DomainEvent) -> None:
        method_name = f"_apply_{type(event).__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise NotImplementedError(f"{type(self).__name__} missing {method_name}")
        method(event)

    def load_from_history(self, events: list[DomainEvent]) -> None:
        for event in events:
            self.apply_event(event, is_new=False)

    def collect_uncommitted_events(self) -> list[DomainEvent]:
        events = list(self._uncommitted_events)
        self._uncommitted_events.clear()
        return events

    def _next_version(self) -> int:
        return self.version + 1

    def to_snapshot(self) -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def from_snapshot(cls, aggregate_id: UUID, state: dict[str, Any], version: int) -> Self:
        raise NotImplementedError
