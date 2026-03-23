"""Event projectors that sync VLAN domain events to the read model."""

from uuid import UUID

from shared.event.domain_event import DomainEvent
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from ipam.vlan.domain.events import VLANCreated, VLANStatusChanged, VLANUpdated
from ipam.vlan.infra.models import VLANReadModel


async def _update_model(session_factory, model_cls, aggregate_id: UUID, values: dict) -> None:
    async with session_factory() as session:
        stmt = update(model_cls).where(model_cls.id == aggregate_id).values(**values)
        await session.execute(stmt)
        await session.commit()


async def handle_vlan_created(session_factory, cache, event: DomainEvent) -> None:
    """Project a VLANCreated event into the read model via upsert."""
    assert isinstance(event, VLANCreated)
    async with session_factory() as session:
        stmt = insert(VLANReadModel).values(
            id=event.aggregate_id,
            vid=event.vid,
            name=event.name,
            group_id=event.group_id,
            status=event.status,
            role=event.role,
            tenant_id=event.tenant_id,
            description=event.description,
            custom_fields=event.custom_fields,
            tags=[str(t) for t in event.tags],
            is_deleted=False,
        )
        stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded))
        await session.execute(stmt)
        await session.commit()


async def handle_vlan_updated(session_factory, cache, event: DomainEvent) -> None:
    """Project a VLANUpdated event by updating changed fields."""
    assert isinstance(event, VLANUpdated)
    values: dict = {}
    if event.name is not None:
        values["name"] = event.name
    if event.role is not None:
        values["role"] = event.role
    if event.description is not None:
        values["description"] = event.description
    if event.custom_fields is not None:
        values["custom_fields"] = event.custom_fields
    if event.tags is not None:
        values["tags"] = [str(t) for t in event.tags]
    if values:
        await _update_model(session_factory, VLANReadModel, event.aggregate_id, values)


async def handle_vlan_status_changed(session_factory, cache, event: DomainEvent) -> None:
    """Project a VLANStatusChanged event by updating the status field."""
    assert isinstance(event, VLANStatusChanged)
    await _update_model(session_factory, VLANReadModel, event.aggregate_id, {"status": event.new_status})


async def handle_vlan_deleted(session_factory, cache, event: DomainEvent) -> None:
    """Project a VLANDeleted event by marking the read model as deleted."""
    await _update_model(session_factory, VLANReadModel, event.aggregate_id, {"is_deleted": True})
