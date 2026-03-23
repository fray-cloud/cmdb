"""RIR command handlers — process RIR create, update, delete, and bulk commands."""

from __future__ import annotations

from uuid import UUID

from shared.cqrs.command import CommandHandler
from shared.domain.exceptions import EntityNotFoundError
from shared.event.pg_store import PostgresEventStore
from shared.messaging.producer import KafkaEventProducer

from ipam.rir import RIR
from ipam.rir.command.commands import (
    BulkCreateRIRsCommand,
    BulkDeleteRIRsCommand,
    BulkUpdateRIRsCommand,
    CreateRIRCommand,
    DeleteRIRCommand,
    UpdateRIRCommand,
)
from ipam.rir.query.read_model import RIRReadModelRepository


class CreateRIRHandler(CommandHandler[UUID]):
    """Handle CreateRIRCommand by creating a new RIR aggregate."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RIRReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateRIRCommand) -> UUID:
        """Create a RIR, persist events, update read model, and publish to Kafka."""
        rir = RIR.create(
            name=command.name,
            is_private=command.is_private,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = rir.collect_uncommitted_events()
        await self._event_store.append(rir.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(rir)
        await self._event_producer.publish_many("ipam.events", events)
        return rir.id


class UpdateRIRHandler(CommandHandler[None]):
    """Handle UpdateRIRCommand by applying updates to an existing RIR."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RIRReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateRIRCommand) -> None:
        """Load the RIR, apply updates, persist events, and update the read model."""
        rir = await self._event_store.load_aggregate(RIR, command.rir_id)
        if rir is None:
            raise EntityNotFoundError(f"RIR {command.rir_id} not found")

        rir.update(
            description=command.description,
            is_private=command.is_private,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = rir.collect_uncommitted_events()
        await self._event_store.append(
            rir.id, new_events, expected_version=rir.version - len(new_events), aggregate=rir
        )
        await self._read_model_repo.upsert_from_aggregate(rir)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteRIRHandler(CommandHandler[None]):
    """Handle DeleteRIRCommand by soft-deleting an existing RIR."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RIRReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteRIRCommand) -> None:
        """Load the RIR, mark as deleted, persist events, and update the read model."""
        rir = await self._event_store.load_aggregate(RIR, command.rir_id)
        if rir is None:
            raise EntityNotFoundError(f"RIR {command.rir_id} not found")

        rir.delete()

        new_events = rir.collect_uncommitted_events()
        await self._event_store.append(
            rir.id, new_events, expected_version=rir.version - len(new_events), aggregate=rir
        )
        await self._read_model_repo.mark_deleted(rir.id)
        await self._event_producer.publish_many("ipam.events", new_events)


class BulkCreateRIRsHandler(CommandHandler[list[UUID]]):
    """Handle BulkCreateRIRsCommand by creating multiple RIRs in sequence."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RIRReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateRIRsCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            rir = RIR.create(
                name=item.name,
                is_private=item.is_private,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = rir.collect_uncommitted_events()
            await self._event_store.append(rir.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(rir)
            all_events.extend(events)
            results.append(rir.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkUpdateRIRsHandler(CommandHandler[int]):
    """Handle BulkUpdateRIRsCommand by updating multiple RIRs in sequence."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RIRReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateRIRsCommand) -> int:
        all_events: list = []
        for item in command.items:
            rir = await self._event_store.load_aggregate(RIR, item.rir_id)
            if rir is None:
                raise EntityNotFoundError(f"RIR {item.rir_id} not found")
            rir.update(
                description=item.description,
                is_private=item.is_private,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = rir.collect_uncommitted_events()
            await self._event_store.append(
                rir.id, new_events, expected_version=rir.version - len(new_events), aggregate=rir
            )
            await self._read_model_repo.upsert_from_aggregate(rir)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteRIRsHandler(CommandHandler[int]):
    """Handle BulkDeleteRIRsCommand by soft-deleting multiple RIRs in sequence."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RIRReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteRIRsCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            rir = await self._event_store.load_aggregate(RIR, agg_id)
            if rir is None:
                raise EntityNotFoundError(f"RIR {agg_id} not found")
            rir.delete()
            new_events = rir.collect_uncommitted_events()
            await self._event_store.append(
                rir.id, new_events, expected_version=rir.version - len(new_events), aggregate=rir
            )
            await self._read_model_repo.mark_deleted(rir.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)
