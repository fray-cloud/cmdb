from __future__ import annotations

from uuid import UUID

from shared.cqrs.command import CommandHandler
from shared.domain.exceptions import EntityNotFoundError
from shared.event.pg_store import PostgresEventStore
from shared.messaging.producer import KafkaEventProducer

from ipam.vlan_group.command.commands import (
    BulkCreateVLANGroupsCommand,
    BulkDeleteVLANGroupsCommand,
    BulkUpdateVLANGroupsCommand,
    CreateVLANGroupCommand,
    DeleteVLANGroupCommand,
    UpdateVLANGroupCommand,
)
from ipam.vlan_group.domain.vlan_group import VLANGroup
from ipam.vlan_group.query.read_model import VLANGroupReadModelRepository

# ---------------------------------------------------------------------------
# VLANGroup
# ---------------------------------------------------------------------------


class CreateVLANGroupHandler(CommandHandler[UUID]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateVLANGroupCommand) -> UUID:
        group = VLANGroup.create(
            name=command.name,
            slug=command.slug,
            min_vid=command.min_vid,
            max_vid=command.max_vid,
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = group.collect_uncommitted_events()
        await self._event_store.append(group.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(group)
        await self._event_producer.publish_many("ipam.events", events)
        return group.id


class UpdateVLANGroupHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateVLANGroupCommand) -> None:
        group = await self._event_store.load_aggregate(VLANGroup, command.vlan_group_id)
        if group is None:
            raise EntityNotFoundError(f"VLANGroup {command.vlan_group_id} not found")

        group.update(
            name=command.name,
            description=command.description,
            min_vid=command.min_vid,
            max_vid=command.max_vid,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = group.collect_uncommitted_events()
        await self._event_store.append(
            group.id, new_events, expected_version=group.version - len(new_events), aggregate=group
        )
        await self._read_model_repo.upsert_from_aggregate(group)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteVLANGroupHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteVLANGroupCommand) -> None:
        group = await self._event_store.load_aggregate(VLANGroup, command.vlan_group_id)
        if group is None:
            raise EntityNotFoundError(f"VLANGroup {command.vlan_group_id} not found")

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


class BulkCreateVLANGroupsHandler(CommandHandler[list[UUID]]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateVLANGroupsCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            group = VLANGroup.create(
                name=item.name,
                slug=item.slug,
                min_vid=item.min_vid,
                max_vid=item.max_vid,
                tenant_id=item.tenant_id,
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


class BulkUpdateVLANGroupsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateVLANGroupsCommand) -> int:
        all_events: list = []
        for item in command.items:
            group = await self._event_store.load_aggregate(VLANGroup, item.vlan_group_id)
            if group is None:
                raise EntityNotFoundError(f"VLANGroup {item.vlan_group_id} not found")
            group.update(
                name=item.name,
                description=item.description,
                min_vid=item.min_vid,
                max_vid=item.max_vid,
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


class BulkDeleteVLANGroupsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteVLANGroupsCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            group = await self._event_store.load_aggregate(VLANGroup, agg_id)
            if group is None:
                raise EntityNotFoundError(f"VLANGroup {agg_id} not found")
            group.delete()
            new_events = group.collect_uncommitted_events()
            await self._event_store.append(
                group.id, new_events, expected_version=group.version - len(new_events), aggregate=group
            )
            await self._read_model_repo.mark_deleted(group.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)
