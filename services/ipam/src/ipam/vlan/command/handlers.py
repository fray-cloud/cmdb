"""Command handlers for VLAN aggregate write operations."""

from __future__ import annotations

from uuid import UUID

from shared.cqrs.command import CommandHandler
from shared.domain.exceptions import EntityNotFoundError
from shared.event.pg_store import PostgresEventStore
from shared.messaging.producer import KafkaEventProducer

from ipam.vlan import VLAN, VLANStatus
from ipam.vlan.command.commands import (
    BulkCreateVLANsCommand,
    BulkDeleteVLANsCommand,
    BulkUpdateVLANsCommand,
    ChangeVLANStatusCommand,
    CreateVLANCommand,
    DeleteVLANCommand,
    UpdateVLANCommand,
)
from ipam.vlan.query.read_model import VLANReadModelRepository


class CreateVLANHandler(CommandHandler[UUID]):
    """Handle creating a new VLAN."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateVLANCommand) -> UUID:
        """Create a VLAN, store events, update read model, and publish to Kafka."""
        vlan = VLAN.create(
            vid=command.vid,
            name=command.name,
            group_id=command.group_id,
            status=VLANStatus(command.status),
            role=command.role,
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = vlan.collect_uncommitted_events()
        await self._event_store.append(vlan.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(vlan)
        await self._event_producer.publish_many("ipam.events", events)
        return vlan.id


class UpdateVLANHandler(CommandHandler[None]):
    """Handle updating an existing VLAN."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateVLANCommand) -> None:
        """Load the VLAN, apply updates, and persist new events."""
        vlan = await self._event_store.load_aggregate(VLAN, command.vlan_id)
        if vlan is None:
            raise EntityNotFoundError(f"VLAN {command.vlan_id} not found")

        vlan.update(
            name=command.name,
            role=command.role,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = vlan.collect_uncommitted_events()
        await self._event_store.append(
            vlan.id, new_events, expected_version=vlan.version - len(new_events), aggregate=vlan
        )
        await self._read_model_repo.upsert_from_aggregate(vlan)
        await self._event_producer.publish_many("ipam.events", new_events)


class ChangeVLANStatusHandler(CommandHandler[None]):
    """Handle changing the lifecycle status of a VLAN."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: ChangeVLANStatusCommand) -> None:
        """Transition the VLAN to the requested status."""
        vlan = await self._event_store.load_aggregate(VLAN, command.vlan_id)
        if vlan is None:
            raise EntityNotFoundError(f"VLAN {command.vlan_id} not found")

        vlan.change_status(VLANStatus(command.status))

        new_events = vlan.collect_uncommitted_events()
        await self._event_store.append(
            vlan.id, new_events, expected_version=vlan.version - len(new_events), aggregate=vlan
        )
        await self._read_model_repo.upsert_from_aggregate(vlan)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteVLANHandler(CommandHandler[None]):
    """Handle soft-deleting a VLAN."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteVLANCommand) -> None:
        """Mark the VLAN as deleted and publish the deletion event."""
        vlan = await self._event_store.load_aggregate(VLAN, command.vlan_id)
        if vlan is None:
            raise EntityNotFoundError(f"VLAN {command.vlan_id} not found")

        vlan.delete()

        new_events = vlan.collect_uncommitted_events()
        await self._event_store.append(
            vlan.id, new_events, expected_version=vlan.version - len(new_events), aggregate=vlan
        )
        await self._read_model_repo.mark_deleted(vlan.id)
        await self._event_producer.publish_many("ipam.events", new_events)


class BulkCreateVLANsHandler(CommandHandler[list[UUID]]):
    """Handle creating multiple VLANs in a single operation."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateVLANsCommand) -> list[UUID]:
        """Create each VLAN, persist events, and return all new IDs."""
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            vlan = VLAN.create(
                vid=item.vid,
                name=item.name,
                group_id=item.group_id,
                status=VLANStatus(item.status),
                role=item.role,
                tenant_id=item.tenant_id,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = vlan.collect_uncommitted_events()
            await self._event_store.append(vlan.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(vlan)
            all_events.extend(events)
            results.append(vlan.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkUpdateVLANsHandler(CommandHandler[int]):
    """Handle updating multiple VLANs in a single operation."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateVLANsCommand) -> int:
        """Apply updates to each VLAN and return the count of updated items."""
        all_events: list = []
        for item in command.items:
            vlan = await self._event_store.load_aggregate(VLAN, item.vlan_id)
            if vlan is None:
                raise EntityNotFoundError(f"VLAN {item.vlan_id} not found")
            vlan.update(
                name=item.name,
                role=item.role,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = vlan.collect_uncommitted_events()
            await self._event_store.append(
                vlan.id, new_events, expected_version=vlan.version - len(new_events), aggregate=vlan
            )
            await self._read_model_repo.upsert_from_aggregate(vlan)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteVLANsHandler(CommandHandler[int]):
    """Handle deleting multiple VLANs in a single operation."""

    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteVLANsCommand) -> int:
        """Delete each VLAN and return the count of deleted items."""
        all_events: list = []
        for agg_id in command.ids:
            vlan = await self._event_store.load_aggregate(VLAN, agg_id)
            if vlan is None:
                raise EntityNotFoundError(f"VLAN {agg_id} not found")
            vlan.delete()
            new_events = vlan.collect_uncommitted_events()
            await self._event_store.append(
                vlan.id, new_events, expected_version=vlan.version - len(new_events), aggregate=vlan
            )
            await self._read_model_repo.mark_deleted(vlan.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)
