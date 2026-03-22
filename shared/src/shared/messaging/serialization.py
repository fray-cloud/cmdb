import json

from shared.event.domain_event import DomainEvent


class EventSerializer:
    def __init__(self) -> None:
        self._registry: dict[str, type[DomainEvent]] = {}

    def register(self, event_cls: type[DomainEvent]) -> None:
        key = f"{event_cls.__module__}.{event_cls.__qualname__}"
        self._registry[key] = event_cls

    def serialize(self, event: DomainEvent) -> bytes:
        return event.model_dump_json().encode("utf-8")

    def deserialize(self, data: bytes) -> DomainEvent:
        raw = json.loads(data)
        event_type = raw.get("event_type", "")
        cls = self._registry.get(event_type, DomainEvent)
        return cls.model_validate(raw)
