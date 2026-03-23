"""Command handlers for Prefix aggregate write operations."""

from __future__ import annotations

from uuid import UUID

from shared.cqrs.command import CommandHandler
from shared.domain.exceptions import EntityNotFoundError
from shared.event.pg_store import PostgresEventStore
from shared.messaging.producer import KafkaEventProducer

from ipam.prefix import Prefix, PrefixStatus
from ipam.prefix.command.commands import (
    BulkCreatePrefixesCommand,
    BulkDeletePrefixesCommand,
    BulkUpdatePrefixesCommand,
    ChangePrefixStatusCommand,
    CreatePrefixCommand,
    DeletePrefixCommand,
    UpdatePrefixCommand,
)
from ipam.prefix.query.read_model import PrefixReadModelRepository


class CreatePrefixHandler(CommandHandler[UUID]):
    """Handle creating a new prefix and persisting its events."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: PrefixReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreatePrefixCommand) -> UUID:
        """Create a prefix, store events, update read model, and publish to Kafka."""
        prefix = Prefix.create(
            network=command.network,
            vrf_id=command.vrf_id,
            vlan_id=command.vlan_id,
            status=PrefixStatus(command.status),
            role=command.role,
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = prefix.collect_uncommitted_events()
        await self._event_store.append(prefix.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(prefix)
        await self._event_producer.publish_many("ipam.events", events)
        return prefix.id


class UpdatePrefixHandler(CommandHandler[None]):
    """Handle updating an existing prefix's mutable fields."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: PrefixReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdatePrefixCommand) -> None:
        """Load the prefix, apply updates, and persist new events."""
        prefix = await self._event_store.load_aggregate(Prefix, command.prefix_id)
        if prefix is None:
            raise EntityNotFoundError(f"Prefix {command.prefix_id} not found")

        prefix.update(
            description=command.description,
            role=command.role,
            tenant_id=command.tenant_id,
            vlan_id=command.vlan_id,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = prefix.collect_uncommitted_events()
        await self._event_store.append(
            prefix.id, new_events, expected_version=prefix.version - len(new_events), aggregate=prefix
        )
        await self._read_model_repo.upsert_from_aggregate(prefix)
        await self._event_producer.publish_many("ipam.events", new_events)


class ChangePrefixStatusHandler(CommandHandler[None]):
    """Handle changing the lifecycle status of a prefix."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: PrefixReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: ChangePrefixStatusCommand) -> None:
        """Transition the prefix to the requested status."""
        prefix = await self._event_store.load_aggregate(Prefix, command.prefix_id)
        if prefix is None:
            raise EntityNotFoundError(f"Prefix {command.prefix_id} not found")

        prefix.change_status(PrefixStatus(command.status))

        new_events = prefix.collect_uncommitted_events()
        await self._event_store.append(
            prefix.id, new_events, expected_version=prefix.version - len(new_events), aggregate=prefix
        )
        await self._read_model_repo.upsert_from_aggregate(prefix)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeletePrefixHandler(CommandHandler[None]):
    """Handle soft-deleting a prefix."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: PrefixReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeletePrefixCommand) -> None:
        """Mark the prefix as deleted and publish the deletion event."""
        prefix = await self._event_store.load_aggregate(Prefix, command.prefix_id)
        if prefix is None:
            raise EntityNotFoundError(f"Prefix {command.prefix_id} not found")

        prefix.delete()

        new_events = prefix.collect_uncommitted_events()
        await self._event_store.append(
            prefix.id, new_events, expected_version=prefix.version - len(new_events), aggregate=prefix
        )
        await self._read_model_repo.mark_deleted(prefix.id)
        await self._event_producer.publish_many("ipam.events", new_events)


class BulkCreatePrefixesHandler(CommandHandler[list[UUID]]):
    """Handle creating multiple prefixes in a single operation."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: PrefixReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreatePrefixesCommand) -> list[UUID]:
        """Create each prefix, persist events, and return all new IDs."""
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            prefix = Prefix.create(
                network=item.network,
                vrf_id=item.vrf_id,
                vlan_id=item.vlan_id,
                status=PrefixStatus(item.status),
                role=item.role,
                tenant_id=item.tenant_id,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = prefix.collect_uncommitted_events()
            await self._event_store.append(prefix.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(prefix)
            all_events.extend(events)
            results.append(prefix.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkUpdatePrefixesHandler(CommandHandler[int]):
    """Handle updating multiple prefixes in a single operation."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: PrefixReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdatePrefixesCommand) -> int:
        """Apply updates to each prefix and return the count of updated items."""
        all_events: list = []
        for item in command.items:
            prefix = await self._event_store.load_aggregate(Prefix, item.prefix_id)
            if prefix is None:
                raise EntityNotFoundError(f"Prefix {item.prefix_id} not found")
            prefix.update(
                description=item.description,
                role=item.role,
                tenant_id=item.tenant_id,
                vlan_id=item.vlan_id,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = prefix.collect_uncommitted_events()
            await self._event_store.append(
                prefix.id, new_events, expected_version=prefix.version - len(new_events), aggregate=prefix
            )
            await self._read_model_repo.upsert_from_aggregate(prefix)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeletePrefixesHandler(CommandHandler[int]):
    """Handle deleting multiple prefixes in a single operation."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: PrefixReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeletePrefixesCommand) -> int:
        """Delete each prefix and return the count of deleted items."""
        all_events: list = []
        for agg_id in command.ids:
            prefix = await self._event_store.load_aggregate(Prefix, agg_id)
            if prefix is None:
                raise EntityNotFoundError(f"Prefix {agg_id} not found")
            prefix.delete()
            new_events = prefix.collect_uncommitted_events()
            await self._event_store.append(
                prefix.id, new_events, expected_version=prefix.version - len(new_events), aggregate=prefix
            )
            await self._read_model_repo.mark_deleted(prefix.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)
