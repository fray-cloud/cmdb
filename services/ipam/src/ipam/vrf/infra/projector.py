"""Event projectors that sync VRF domain events to the read model."""

from uuid import UUID

from shared.event.domain_event import DomainEvent
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from ipam.vrf.domain.events import VRFCreated, VRFUpdated
from ipam.vrf.infra.models import VRFReadModel


async def _update_model(session_factory, model_cls, aggregate_id: UUID, values: dict) -> None:
    async with session_factory() as session:
        stmt = update(model_cls).where(model_cls.id == aggregate_id).values(**values)
        await session.execute(stmt)
        await session.commit()


async def handle_vrf_created(session_factory, cache, event: DomainEvent) -> None:
    """Project a VRFCreated event into the read model via upsert."""
    assert isinstance(event, VRFCreated)
    async with session_factory() as session:
        stmt = insert(VRFReadModel).values(
            id=event.aggregate_id,
            name=event.name,
            rd=event.rd,
            import_targets=[str(t) for t in event.import_targets],
            export_targets=[str(t) for t in event.export_targets],
            tenant_id=event.tenant_id,
            description=event.description,
            custom_fields=event.custom_fields,
            tags=[str(t) for t in event.tags],
            is_deleted=False,
        )
        stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded))
        await session.execute(stmt)
        await session.commit()


async def handle_vrf_updated(session_factory, cache, event: DomainEvent) -> None:
    """Project a VRFUpdated event by updating changed fields."""
    assert isinstance(event, VRFUpdated)
    values: dict = {}
    if event.name is not None:
        values["name"] = event.name
    if event.import_targets is not None:
        values["import_targets"] = [str(t) for t in event.import_targets]
    if event.export_targets is not None:
        values["export_targets"] = [str(t) for t in event.export_targets]
    if event.description is not None:
        values["description"] = event.description
    if event.custom_fields is not None:
        values["custom_fields"] = event.custom_fields
    if event.tags is not None:
        values["tags"] = [str(t) for t in event.tags]
    if values:
        await _update_model(session_factory, VRFReadModel, event.aggregate_id, values)


async def handle_vrf_deleted(session_factory, cache, event: DomainEvent) -> None:
    """Project a VRFDeleted event by marking the read model as deleted."""
    await _update_model(session_factory, VRFReadModel, event.aggregate_id, {"is_deleted": True})
