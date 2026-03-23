from uuid import UUID

from shared.event.domain_event import DomainEvent
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from ipam.vlan_group.domain.events import VLANGroupCreated, VLANGroupUpdated
from ipam.vlan_group.infra.models import VLANGroupReadModel


async def _update_model(session_factory, model_cls, aggregate_id: UUID, values: dict) -> None:
    async with session_factory() as session:
        stmt = update(model_cls).where(model_cls.id == aggregate_id).values(**values)
        await session.execute(stmt)
        await session.commit()


async def handle_vlan_group_created(session_factory, cache, event: DomainEvent) -> None:
    assert isinstance(event, VLANGroupCreated)
    async with session_factory() as session:
        stmt = insert(VLANGroupReadModel).values(
            id=event.aggregate_id,
            name=event.name,
            slug=event.slug,
            min_vid=event.min_vid,
            max_vid=event.max_vid,
            tenant_id=event.tenant_id,
            description=event.description,
            custom_fields=event.custom_fields,
            tags=[str(t) for t in event.tags],
            is_deleted=False,
        )
        stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded))
        await session.execute(stmt)
        await session.commit()


async def handle_vlan_group_updated(session_factory, cache, event: DomainEvent) -> None:
    assert isinstance(event, VLANGroupUpdated)
    values: dict = {}
    if event.name is not None:
        values["name"] = event.name
    if event.description is not None:
        values["description"] = event.description
    if event.min_vid is not None:
        values["min_vid"] = event.min_vid
    if event.max_vid is not None:
        values["max_vid"] = event.max_vid
    if event.custom_fields is not None:
        values["custom_fields"] = event.custom_fields
    if event.tags is not None:
        values["tags"] = [str(t) for t in event.tags]
    if values:
        await _update_model(session_factory, VLANGroupReadModel, event.aggregate_id, values)


async def handle_vlan_group_deleted(session_factory, cache, event: DomainEvent) -> None:
    await _update_model(session_factory, VLANGroupReadModel, event.aggregate_id, {"is_deleted": True})
