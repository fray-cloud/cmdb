from uuid import UUID

from shared.event.domain_event import DomainEvent
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from ipam.asn.domain.events import ASNCreated, ASNUpdated
from ipam.asn.infra.models import ASNReadModel


async def _update_model(session_factory, model_cls, aggregate_id: UUID, values: dict) -> None:
    async with session_factory() as session:
        stmt = update(model_cls).where(model_cls.id == aggregate_id).values(**values)
        await session.execute(stmt)
        await session.commit()


async def handle_asn_created(session_factory, cache, event: DomainEvent) -> None:
    assert isinstance(event, ASNCreated)
    async with session_factory() as session:
        stmt = insert(ASNReadModel).values(
            id=event.aggregate_id,
            asn=event.asn,
            rir_id=event.rir_id,
            tenant_id=event.tenant_id,
            description=event.description,
            custom_fields=event.custom_fields,
            tags=[str(t) for t in event.tags],
            is_deleted=False,
        )
        stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded))
        await session.execute(stmt)
        await session.commit()


async def handle_asn_updated(session_factory, cache, event: DomainEvent) -> None:
    assert isinstance(event, ASNUpdated)
    values: dict = {}
    if event.description is not None:
        values["description"] = event.description
    if event.tenant_id is not None:
        values["tenant_id"] = event.tenant_id
    if event.custom_fields is not None:
        values["custom_fields"] = event.custom_fields
    if event.tags is not None:
        values["tags"] = [str(t) for t in event.tags]
    if values:
        await _update_model(session_factory, ASNReadModel, event.aggregate_id, values)


async def handle_asn_deleted(session_factory, cache, event: DomainEvent) -> None:
    await _update_model(session_factory, ASNReadModel, event.aggregate_id, {"is_deleted": True})
