"""Service command handlers — process create, update, delete, and bulk commands."""

from __future__ import annotations

from uuid import UUID

from shared.cqrs.command import CommandHandler
from shared.domain.exceptions import EntityNotFoundError
from shared.event.pg_store import PostgresEventStore
from shared.messaging.producer import KafkaEventProducer

from ipam.service_entity import Service, ServiceProtocol
from ipam.service_entity.command.commands import (
    BulkCreateServicesCommand,
    BulkDeleteServicesCommand,
    BulkUpdateServicesCommand,
    CreateServiceCommand,
    DeleteServiceCommand,
    UpdateServiceCommand,
)
from ipam.service_entity.query.read_model import ServiceReadModelRepository

# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class CreateServiceHandler(CommandHandler[UUID]):
    """Handle CreateServiceCommand by creating a new Service aggregate."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ServiceReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateServiceCommand) -> UUID:
        """Create a Service, persist events, update read model, and publish to Kafka."""
        svc = Service.create(
            name=command.name,
            protocol=ServiceProtocol(command.protocol),
            ports=command.ports or [],
            ip_addresses=command.ip_addresses or [],
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = svc.collect_uncommitted_events()
        await self._event_store.append(svc.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(svc)
        await self._event_producer.publish_many("ipam.events", events)
        return svc.id


class UpdateServiceHandler(CommandHandler[None]):
    """Handle UpdateServiceCommand by applying updates to an existing Service."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ServiceReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateServiceCommand) -> None:
        svc = await self._event_store.load_aggregate(Service, command.service_id)
        if svc is None:
            raise EntityNotFoundError(f"Service {command.service_id} not found")

        svc.update(
            name=command.name,
            protocol=command.protocol,
            ports=command.ports or [],
            ip_addresses=command.ip_addresses or [],
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = svc.collect_uncommitted_events()
        await self._event_store.append(
            svc.id, new_events, expected_version=svc.version - len(new_events), aggregate=svc
        )
        await self._read_model_repo.upsert_from_aggregate(svc)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteServiceHandler(CommandHandler[None]):
    """Handle DeleteServiceCommand by soft-deleting an existing Service."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ServiceReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteServiceCommand) -> None:
        svc = await self._event_store.load_aggregate(Service, command.service_id)
        if svc is None:
            raise EntityNotFoundError(f"Service {command.service_id} not found")

        svc.delete()

        new_events = svc.collect_uncommitted_events()
        await self._event_store.append(
            svc.id, new_events, expected_version=svc.version - len(new_events), aggregate=svc
        )
        await self._read_model_repo.mark_deleted(svc.id)
        await self._event_producer.publish_many("ipam.events", new_events)


# ---------------------------------------------------------------------------
# Bulk Operations
# ---------------------------------------------------------------------------


class BulkCreateServicesHandler(CommandHandler[list[UUID]]):
    """Handle BulkCreateServicesCommand by creating multiple Services."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ServiceReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateServicesCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            svc = Service.create(
                name=item.name,
                protocol=ServiceProtocol(item.protocol),
                ports=item.ports,
                ip_addresses=item.ip_addresses,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = svc.collect_uncommitted_events()
            await self._event_store.append(svc.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(svc)
            all_events.extend(events)
            results.append(svc.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkUpdateServicesHandler(CommandHandler[int]):
    """Handle BulkUpdateServicesCommand by updating multiple Services."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ServiceReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateServicesCommand) -> int:
        all_events: list = []
        for item in command.items:
            svc = await self._event_store.load_aggregate(Service, item.service_id)
            if svc is None:
                raise EntityNotFoundError(f"Service {item.service_id} not found")
            svc.update(
                name=item.name,
                protocol=item.protocol,
                ports=item.ports,
                ip_addresses=item.ip_addresses,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = svc.collect_uncommitted_events()
            await self._event_store.append(
                svc.id, new_events, expected_version=svc.version - len(new_events), aggregate=svc
            )
            await self._read_model_repo.upsert_from_aggregate(svc)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteServicesHandler(CommandHandler[int]):
    """Handle BulkDeleteServicesCommand by soft-deleting multiple Services."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ServiceReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteServicesCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            svc = await self._event_store.load_aggregate(Service, agg_id)
            if svc is None:
                raise EntityNotFoundError(f"Service {agg_id} not found")
            svc.delete()
            new_events = svc.collect_uncommitted_events()
            await self._event_store.append(
                svc.id, new_events, expected_version=svc.version - len(new_events), aggregate=svc
            )
            await self._read_model_repo.mark_deleted(svc.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)
