"""RIR event projector — handles domain events to update the RIR read model."""

from uuid import UUID

from shared.event.domain_event import DomainEvent
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from ipam.rir.domain.events import RIRCreated, RIRUpdated
from ipam.rir.infra.models import RIRReadModel


async def _update_model(session_factory, model_cls, aggregate_id: UUID, values: dict) -> None:
    async with session_factory() as session:
        stmt = update(model_cls).where(model_cls.id == aggregate_id).values(**values)
        await session.execute(stmt)
        await session.commit()


async def handle_rir_created(session_factory, cache, event: DomainEvent) -> None:
    assert isinstance(event, RIRCreated)
    async with session_factory() as session:
        stmt = insert(RIRReadModel).values(
            id=event.aggregate_id,
            name=event.name,
            is_private=event.is_private,
            description=event.description,
            custom_fields=event.custom_fields,
            tags=[str(t) for t in event.tags],
            is_deleted=False,
        )
        stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded))
        await session.execute(stmt)
        await session.commit()


async def handle_rir_updated(session_factory, cache, event: DomainEvent) -> None:
    assert isinstance(event, RIRUpdated)
    values: dict = {}
    if event.description is not None:
        values["description"] = event.description
    if event.is_private is not None:
        values["is_private"] = event.is_private
    if event.custom_fields is not None:
        values["custom_fields"] = event.custom_fields
    if event.tags is not None:
        values["tags"] = [str(t) for t in event.tags]
    if values:
        await _update_model(session_factory, RIRReadModel, event.aggregate_id, values)


async def handle_rir_deleted(session_factory, cache, event: DomainEvent) -> None:
    await _update_model(session_factory, RIRReadModel, event.aggregate_id, {"is_deleted": True})
