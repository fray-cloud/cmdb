"""Service event projector — handles domain events to update the Service read model."""

from uuid import UUID

from shared.event.domain_event import DomainEvent
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from ipam.service_entity.domain.events import ServiceCreated, ServiceUpdated
from ipam.service_entity.infra.models import ServiceReadModel


async def _update_model(session_factory, model_cls, aggregate_id: UUID, values: dict) -> None:
    async with session_factory() as session:
        stmt = update(model_cls).where(model_cls.id == aggregate_id).values(**values)
        await session.execute(stmt)
        await session.commit()


async def handle_service_created(session_factory, cache, event: DomainEvent) -> None:
    assert isinstance(event, ServiceCreated)
    async with session_factory() as session:
        stmt = insert(ServiceReadModel).values(
            id=event.aggregate_id,
            name=event.name,
            protocol=event.protocol,
            ports=event.ports,
            ip_addresses=[str(ip) for ip in event.ip_addresses],
            description=event.description,
            custom_fields=event.custom_fields,
            tags=[str(t) for t in event.tags],
            is_deleted=False,
        )
        stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded))
        await session.execute(stmt)
        await session.commit()


async def handle_service_updated(session_factory, cache, event: DomainEvent) -> None:
    assert isinstance(event, ServiceUpdated)
    values: dict = {}
    if event.name is not None:
        values["name"] = event.name
    if event.protocol is not None:
        values["protocol"] = event.protocol
    if event.ports is not None:
        values["ports"] = event.ports
    if event.ip_addresses is not None:
        values["ip_addresses"] = [str(ip) for ip in event.ip_addresses]
    if event.description is not None:
        values["description"] = event.description
    if event.custom_fields is not None:
        values["custom_fields"] = event.custom_fields
    if event.tags is not None:
        values["tags"] = [str(t) for t in event.tags]
    if values:
        await _update_model(session_factory, ServiceReadModel, event.aggregate_id, values)


async def handle_service_deleted(session_factory, cache, event: DomainEvent) -> None:
    await _update_model(session_factory, ServiceReadModel, event.aggregate_id, {"is_deleted": True})
