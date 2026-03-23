"""Event projectors that sync Prefix domain events to the read model."""

from uuid import UUID

from shared.event.domain_event import DomainEvent
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from ipam.prefix.domain.events import PrefixCreated, PrefixStatusChanged, PrefixUpdated
from ipam.prefix.infra.models import PrefixReadModel


async def _update_model(session_factory, model_cls, aggregate_id: UUID, values: dict) -> None:
    async with session_factory() as session:
        stmt = update(model_cls).where(model_cls.id == aggregate_id).values(**values)
        await session.execute(stmt)
        await session.commit()


async def _invalidate_cache(cache, prefix_id: UUID) -> None:
    if cache is not None:
        await cache.invalidate_prefix_utilization(prefix_id)


async def handle_prefix_created(session_factory, cache, event: DomainEvent) -> None:
    """Project a PrefixCreated event into the read model via upsert."""
    assert isinstance(event, PrefixCreated)
    async with session_factory() as session:
        stmt = insert(PrefixReadModel).values(
            id=event.aggregate_id,
            network=event.network,
            vrf_id=event.vrf_id,
            vlan_id=event.vlan_id,
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
    await _invalidate_cache(cache, event.aggregate_id)


async def handle_prefix_updated(session_factory, cache, event: DomainEvent) -> None:
    """Project a PrefixUpdated event by updating changed fields in the read model."""
    assert isinstance(event, PrefixUpdated)
    values: dict = {}
    if event.description is not None:
        values["description"] = event.description
    if event.role is not None:
        values["role"] = event.role
    if event.tenant_id is not None:
        values["tenant_id"] = event.tenant_id
    if event.vlan_id is not None:
        values["vlan_id"] = event.vlan_id
    if event.custom_fields is not None:
        values["custom_fields"] = event.custom_fields
    if event.tags is not None:
        values["tags"] = [str(t) for t in event.tags]
    if values:
        await _update_model(session_factory, PrefixReadModel, event.aggregate_id, values)
    await _invalidate_cache(cache, event.aggregate_id)


async def handle_prefix_status_changed(session_factory, cache, event: DomainEvent) -> None:
    """Project a PrefixStatusChanged event by updating the status field."""
    assert isinstance(event, PrefixStatusChanged)
    await _update_model(session_factory, PrefixReadModel, event.aggregate_id, {"status": event.new_status})
    await _invalidate_cache(cache, event.aggregate_id)


async def handle_prefix_deleted(session_factory, cache, event: DomainEvent) -> None:
    """Project a PrefixDeleted event by marking the read model as deleted."""
    await _update_model(session_factory, PrefixReadModel, event.aggregate_id, {"is_deleted": True})
    await _invalidate_cache(cache, event.aggregate_id)
