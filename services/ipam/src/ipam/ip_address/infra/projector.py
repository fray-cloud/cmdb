"""Event projectors that sync IPAddress domain events to the read model."""

from uuid import UUID

from shared.event.domain_event import DomainEvent
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from ipam.ip_address.domain.events import (
    IPAddressCreated,
    IPAddressStatusChanged,
    IPAddressUpdated,
)
from ipam.ip_address.infra.models import IPAddressReadModel


async def _update_model(session_factory, model_cls, aggregate_id: UUID, values: dict) -> None:
    async with session_factory() as session:
        stmt = update(model_cls).where(model_cls.id == aggregate_id).values(**values)
        await session.execute(stmt)
        await session.commit()


async def handle_ip_address_created(session_factory, cache, event: DomainEvent) -> None:
    """Project an IPAddressCreated event into the read model via upsert."""
    assert isinstance(event, IPAddressCreated)
    async with session_factory() as session:
        stmt = insert(IPAddressReadModel).values(
            id=event.aggregate_id,
            address=event.address,
            vrf_id=event.vrf_id,
            status=event.status,
            dns_name=event.dns_name,
            tenant_id=event.tenant_id,
            description=event.description,
            custom_fields=event.custom_fields,
            tags=[str(t) for t in event.tags],
            is_deleted=False,
        )
        stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded))
        await session.execute(stmt)
        await session.commit()


async def handle_ip_address_updated(session_factory, cache, event: DomainEvent) -> None:
    """Project an IPAddressUpdated event by updating changed fields."""
    assert isinstance(event, IPAddressUpdated)
    values: dict = {}
    if event.dns_name is not None:
        values["dns_name"] = event.dns_name
    if event.description is not None:
        values["description"] = event.description
    if event.custom_fields is not None:
        values["custom_fields"] = event.custom_fields
    if event.tags is not None:
        values["tags"] = [str(t) for t in event.tags]
    if values:
        await _update_model(session_factory, IPAddressReadModel, event.aggregate_id, values)


async def handle_ip_address_status_changed(session_factory, cache, event: DomainEvent) -> None:
    """Project an IPAddressStatusChanged event by updating the status field."""
    assert isinstance(event, IPAddressStatusChanged)
    await _update_model(session_factory, IPAddressReadModel, event.aggregate_id, {"status": event.new_status})


async def handle_ip_address_deleted(session_factory, cache, event: DomainEvent) -> None:
    """Project an IPAddressDeleted event by marking the read model as deleted."""
    await _update_model(session_factory, IPAddressReadModel, event.aggregate_id, {"is_deleted": True})
