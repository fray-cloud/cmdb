"""Command handlers for VLANGroup aggregate write operations."""

from __future__ import annotations

from uuid import UUID

from shared.cqrs.command import CommandHandler
from shared.domain.exceptions import EntityNotFoundError
from shared.event.pg_store import PostgresEventStore
from shared.messaging.producer import KafkaEventProducer

from ipam.vlan_group import VLANGroup
from ipam.vlan_group.command.commands import (
    BulkCreateVLANGroupsCommand,
    BulkDeleteVLANGroupsCommand,
    BulkUpdateVLANGroupsCommand,
    CreateVLANGroupCommand,
    DeleteVLANGroupCommand,
    UpdateVLANGroupCommand,
)
from ipam.vlan_group.query.read_model import VLANGroupReadModelRepository

# ---------------------------------------------------------------------------
# VLANGroup
# ---------------------------------------------------------------------------


class CreateVLANGroupHandler(CommandHandler[UUID]):
    """Handle creating a new VLAN group."""

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
        """Create a VLAN group, store events, and publish to Kafka."""
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
    """Handle updating an existing VLAN group."""

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
        """Load the VLAN group, apply updates, and persist new events."""
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
    """Handle soft-deleting a VLAN group."""

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
        """Mark the VLAN group as deleted and publish the deletion event."""
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
    """Handle creating multiple VLAN groups in a single operation."""

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
        """Create each VLAN group, persist events, and return all new IDs."""
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
    """Handle updating multiple VLAN groups in a single operation."""

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
        """Apply updates to each VLAN group and return the count of updated items."""
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
    """Handle deleting multiple VLAN groups in a single operation."""

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
        """Delete each VLAN group and return the count of deleted items."""
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
