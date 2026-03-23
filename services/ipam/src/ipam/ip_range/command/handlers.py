"""Command handlers for IPRange aggregate write operations."""

from __future__ import annotations

from uuid import UUID

from shared.cqrs.command import CommandHandler
from shared.domain.exceptions import EntityNotFoundError
from shared.event.pg_store import PostgresEventStore
from shared.messaging.producer import KafkaEventProducer

from ipam.ip_range import IPRange, IPRangeStatus
from ipam.ip_range.command.commands import (
    BulkCreateIPRangesCommand,
    BulkDeleteIPRangesCommand,
    BulkUpdateIPRangesCommand,
    ChangeIPRangeStatusCommand,
    CreateIPRangeCommand,
    DeleteIPRangeCommand,
    UpdateIPRangeCommand,
)
from ipam.ip_range.query.read_model import IPRangeReadModelRepository


class CreateIPRangeHandler(CommandHandler[UUID]):
    """Handle creating a new IP range."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPRangeReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateIPRangeCommand) -> UUID:
        """Create an IP range, store events, update read model, and publish to Kafka."""
        ip_range = IPRange.create(
            start_address=command.start_address,
            end_address=command.end_address,
            vrf_id=command.vrf_id,
            status=IPRangeStatus(command.status),
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = ip_range.collect_uncommitted_events()
        await self._event_store.append(ip_range.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(ip_range)
        await self._event_producer.publish_many("ipam.events", events)
        return ip_range.id


class UpdateIPRangeHandler(CommandHandler[None]):
    """Handle updating an existing IP range."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPRangeReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateIPRangeCommand) -> None:
        """Load the IP range, apply updates, and persist new events."""
        ip_range = await self._event_store.load_aggregate(IPRange, command.range_id)
        if ip_range is None:
            raise EntityNotFoundError(f"IP range {command.range_id} not found")

        ip_range.update(
            description=command.description,
            tenant_id=command.tenant_id,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = ip_range.collect_uncommitted_events()
        await self._event_store.append(
            ip_range.id, new_events, expected_version=ip_range.version - len(new_events), aggregate=ip_range
        )
        await self._read_model_repo.upsert_from_aggregate(ip_range)
        await self._event_producer.publish_many("ipam.events", new_events)


class ChangeIPRangeStatusHandler(CommandHandler[None]):
    """Handle changing the lifecycle status of an IP range."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPRangeReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: ChangeIPRangeStatusCommand) -> None:
        """Transition the IP range to the requested status."""
        ip_range = await self._event_store.load_aggregate(IPRange, command.range_id)
        if ip_range is None:
            raise EntityNotFoundError(f"IP range {command.range_id} not found")

        ip_range.change_status(IPRangeStatus(command.status))

        new_events = ip_range.collect_uncommitted_events()
        await self._event_store.append(
            ip_range.id, new_events, expected_version=ip_range.version - len(new_events), aggregate=ip_range
        )
        await self._read_model_repo.upsert_from_aggregate(ip_range)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteIPRangeHandler(CommandHandler[None]):
    """Handle soft-deleting an IP range."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPRangeReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteIPRangeCommand) -> None:
        """Mark the IP range as deleted and publish the deletion event."""
        ip_range = await self._event_store.load_aggregate(IPRange, command.range_id)
        if ip_range is None:
            raise EntityNotFoundError(f"IP range {command.range_id} not found")

        ip_range.delete()

        new_events = ip_range.collect_uncommitted_events()
        await self._event_store.append(
            ip_range.id, new_events, expected_version=ip_range.version - len(new_events), aggregate=ip_range
        )
        await self._read_model_repo.mark_deleted(ip_range.id)
        await self._event_producer.publish_many("ipam.events", new_events)


class BulkCreateIPRangesHandler(CommandHandler[list[UUID]]):
    """Handle creating multiple IP ranges in a single operation."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPRangeReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateIPRangesCommand) -> list[UUID]:
        """Create each IP range, persist events, and return all new IDs."""
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            ip_range = IPRange.create(
                start_address=item.start_address,
                end_address=item.end_address,
                vrf_id=item.vrf_id,
                status=IPRangeStatus(item.status),
                tenant_id=item.tenant_id,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = ip_range.collect_uncommitted_events()
            await self._event_store.append(ip_range.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(ip_range)
            all_events.extend(events)
            results.append(ip_range.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkUpdateIPRangesHandler(CommandHandler[int]):
    """Handle updating multiple IP ranges in a single operation."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPRangeReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateIPRangesCommand) -> int:
        """Apply updates to each IP range and return the count of updated items."""
        all_events: list = []
        for item in command.items:
            ip_range = await self._event_store.load_aggregate(IPRange, item.range_id)
            if ip_range is None:
                raise EntityNotFoundError(f"IP range {item.range_id} not found")
            ip_range.update(
                description=item.description,
                tenant_id=item.tenant_id,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = ip_range.collect_uncommitted_events()
            await self._event_store.append(
                ip_range.id, new_events, expected_version=ip_range.version - len(new_events), aggregate=ip_range
            )
            await self._read_model_repo.upsert_from_aggregate(ip_range)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteIPRangesHandler(CommandHandler[int]):
    """Handle deleting multiple IP ranges in a single operation."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPRangeReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteIPRangesCommand) -> int:
        """Delete each IP range and return the count of deleted items."""
        all_events: list = []
        for agg_id in command.ids:
            ip_range = await self._event_store.load_aggregate(IPRange, agg_id)
            if ip_range is None:
                raise EntityNotFoundError(f"IP range {agg_id} not found")
            ip_range.delete()
            new_events = ip_range.collect_uncommitted_events()
            await self._event_store.append(
                ip_range.id, new_events, expected_version=ip_range.version - len(new_events), aggregate=ip_range
            )
            await self._read_model_repo.mark_deleted(ip_range.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)
