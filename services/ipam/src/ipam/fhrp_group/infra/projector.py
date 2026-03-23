"""FHRP Group event projector — handles domain events to update the read model."""

from uuid import UUID

from shared.event.domain_event import DomainEvent
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from ipam.fhrp_group.domain.events import FHRPGroupCreated, FHRPGroupUpdated
from ipam.fhrp_group.infra.models import FHRPGroupReadModel


async def _update_model(session_factory, model_cls, aggregate_id: UUID, values: dict) -> None:
    async with session_factory() as session:
        stmt = update(model_cls).where(model_cls.id == aggregate_id).values(**values)
        await session.execute(stmt)
        await session.commit()


async def handle_fhrp_group_created(session_factory, cache, event: DomainEvent) -> None:
    assert isinstance(event, FHRPGroupCreated)
    async with session_factory() as session:
        stmt = insert(FHRPGroupReadModel).values(
            id=event.aggregate_id,
            protocol=event.protocol,
            group_id_value=event.group_id_value,
            auth_type=event.auth_type,
            auth_key=event.auth_key,
            name=event.name,
            description=event.description,
            custom_fields=event.custom_fields,
            tags=[str(t) for t in event.tags],
            is_deleted=False,
        )
        stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded))
        await session.execute(stmt)
        await session.commit()


async def handle_fhrp_group_updated(session_factory, cache, event: DomainEvent) -> None:
    assert isinstance(event, FHRPGroupUpdated)
    values: dict = {}
    if event.name is not None:
        values["name"] = event.name
    if event.auth_type is not None:
        values["auth_type"] = event.auth_type
    if event.auth_key is not None:
        values["auth_key"] = event.auth_key
    if event.description is not None:
        values["description"] = event.description
    if event.custom_fields is not None:
        values["custom_fields"] = event.custom_fields
    if event.tags is not None:
        values["tags"] = [str(t) for t in event.tags]
    if values:
        await _update_model(session_factory, FHRPGroupReadModel, event.aggregate_id, values)


async def handle_fhrp_group_deleted(session_factory, cache, event: DomainEvent) -> None:
    await _update_model(session_factory, FHRPGroupReadModel, event.aggregate_id, {"is_deleted": True})
