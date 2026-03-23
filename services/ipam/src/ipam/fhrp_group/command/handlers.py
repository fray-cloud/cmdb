"""FHRP Group command handlers — process create, update, delete, and bulk commands."""

from __future__ import annotations

from uuid import UUID

from shared.cqrs.command import CommandHandler
from shared.domain.exceptions import EntityNotFoundError
from shared.event.pg_store import PostgresEventStore
from shared.messaging.producer import KafkaEventProducer

from ipam.fhrp_group import FHRPAuthType, FHRPGroup, FHRPProtocol
from ipam.fhrp_group.command.commands import (
    BulkCreateFHRPGroupsCommand,
    BulkDeleteFHRPGroupsCommand,
    BulkUpdateFHRPGroupsCommand,
    CreateFHRPGroupCommand,
    DeleteFHRPGroupCommand,
    UpdateFHRPGroupCommand,
)
from ipam.fhrp_group.query.read_model import FHRPGroupReadModelRepository

# ---------------------------------------------------------------------------
# FHRPGroup
# ---------------------------------------------------------------------------


class CreateFHRPGroupHandler(CommandHandler[UUID]):
    """Handle CreateFHRPGroupCommand by creating a new FHRP Group aggregate."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: FHRPGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateFHRPGroupCommand) -> UUID:
        """Create an FHRP Group, persist events, update read model, and publish to Kafka."""
        group = FHRPGroup.create(
            protocol=FHRPProtocol(command.protocol),
            group_id_value=command.group_id_value,
            auth_type=FHRPAuthType(command.auth_type),
            auth_key=command.auth_key,
            name=command.name,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = group.collect_uncommitted_events()
        await self._event_store.append(group.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(group)
        await self._event_producer.publish_many("ipam.events", events)
        return group.id


class UpdateFHRPGroupHandler(CommandHandler[None]):
    """Handle UpdateFHRPGroupCommand by applying updates to an existing FHRP Group."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: FHRPGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateFHRPGroupCommand) -> None:
        group = await self._event_store.load_aggregate(FHRPGroup, command.fhrp_group_id)
        if group is None:
            raise EntityNotFoundError(f"FHRP group {command.fhrp_group_id} not found")

        group.update(
            name=command.name,
            auth_type=command.auth_type,
            auth_key=command.auth_key,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = group.collect_uncommitted_events()
        await self._event_store.append(
            group.id, new_events, expected_version=group.version - len(new_events), aggregate=group
        )
        await self._read_model_repo.upsert_from_aggregate(group)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteFHRPGroupHandler(CommandHandler[None]):
    """Handle DeleteFHRPGroupCommand by soft-deleting an existing FHRP Group."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: FHRPGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteFHRPGroupCommand) -> None:
        group = await self._event_store.load_aggregate(FHRPGroup, command.fhrp_group_id)
        if group is None:
            raise EntityNotFoundError(f"FHRP group {command.fhrp_group_id} not found")

        group.delete()

        new_events = group.collect_uncommitted_events()
        await self._event_store.append(
            group.id, new_events, expected_version=group.version - len(new_events), aggregate=group
        )
        await self._read_model_repo.mark_deleted(group.id)
        await self._event_producer.publish_many("ipam.events", new_events)


# ---------------------------------------------------------------------------
# Bulk Operations
# ---------------------------------------------------------------------------


class BulkCreateFHRPGroupsHandler(CommandHandler[list[UUID]]):
    """Handle BulkCreateFHRPGroupsCommand by creating multiple FHRP Groups."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: FHRPGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateFHRPGroupsCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            group = FHRPGroup.create(
                protocol=FHRPProtocol(item.protocol),
                group_id_value=item.group_id_value,
                auth_type=FHRPAuthType(item.auth_type),
                auth_key=item.auth_key,
                name=item.name,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = group.collect_uncommitted_events()
            await self._event_store.append(group.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(group)
            all_events.extend(events)
            results.append(group.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkUpdateFHRPGroupsHandler(CommandHandler[int]):
    """Handle BulkUpdateFHRPGroupsCommand by updating multiple FHRP Groups."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: FHRPGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateFHRPGroupsCommand) -> int:
        all_events: list = []
        for item in command.items:
            group = await self._event_store.load_aggregate(FHRPGroup, item.fhrp_group_id)
            if group is None:
                raise EntityNotFoundError(f"FHRP group {item.fhrp_group_id} not found")
            group.update(
                name=item.name,
                auth_type=item.auth_type,
                auth_key=item.auth_key,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = group.collect_uncommitted_events()
            await self._event_store.append(
                group.id, new_events, expected_version=group.version - len(new_events), aggregate=group
            )
            await self._read_model_repo.upsert_from_aggregate(group)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteFHRPGroupsHandler(CommandHandler[int]):
    """Handle BulkDeleteFHRPGroupsCommand by soft-deleting multiple FHRP Groups."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: FHRPGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteFHRPGroupsCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            group = await self._event_store.load_aggregate(FHRPGroup, agg_id)
            if group is None:
                raise EntityNotFoundError(f"FHRP group {agg_id} not found")
            group.delete()
            new_events = group.collect_uncommitted_events()
            await self._event_store.append(
                group.id, new_events, expected_version=group.version - len(new_events), aggregate=group
            )
            await self._read_model_repo.mark_deleted(group.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)
