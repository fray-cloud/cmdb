from __future__ import annotations

from uuid import UUID

from shared.cqrs.command import CommandHandler
from shared.domain.exceptions import ConflictError, EntityNotFoundError
from shared.event.pg_store import PostgresEventStore
from shared.messaging.producer import KafkaEventProducer

from ipam.ip_address.command.commands import (
    BulkCreateIPAddressesCommand,
    BulkDeleteIPAddressesCommand,
    BulkUpdateIPAddressesCommand,
    ChangeIPAddressStatusCommand,
    CreateIPAddressCommand,
    DeleteIPAddressCommand,
    UpdateIPAddressCommand,
)
from ipam.ip_address.domain.ip_address import IPAddress
from ipam.ip_address.domain.value_objects import IPAddressStatus
from ipam.ip_address.query.read_model import IPAddressReadModelRepository


class CreateIPAddressHandler(CommandHandler[UUID]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPAddressReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateIPAddressCommand) -> UUID:
        if await self._read_model_repo.exists_in_vrf(command.address, command.vrf_id):
            raise ConflictError(f"IP address {command.address} already exists in this VRF scope")

        ip = IPAddress.create(
            address=command.address,
            vrf_id=command.vrf_id,
            status=IPAddressStatus(command.status),
            dns_name=command.dns_name,
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = ip.collect_uncommitted_events()
        await self._event_store.append(ip.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(ip)
        await self._event_producer.publish_many("ipam.events", events)
        return ip.id


class UpdateIPAddressHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPAddressReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateIPAddressCommand) -> None:
        ip = await self._event_store.load_aggregate(IPAddress, command.ip_id)
        if ip is None:
            raise EntityNotFoundError(f"IP address {command.ip_id} not found")

        ip.update(
            dns_name=command.dns_name,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = ip.collect_uncommitted_events()
        await self._event_store.append(ip.id, new_events, expected_version=ip.version - len(new_events), aggregate=ip)
        await self._read_model_repo.upsert_from_aggregate(ip)
        await self._event_producer.publish_many("ipam.events", new_events)


class ChangeIPAddressStatusHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPAddressReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: ChangeIPAddressStatusCommand) -> None:
        ip = await self._event_store.load_aggregate(IPAddress, command.ip_id)
        if ip is None:
            raise EntityNotFoundError(f"IP address {command.ip_id} not found")

        ip.change_status(IPAddressStatus(command.status))

        new_events = ip.collect_uncommitted_events()
        await self._event_store.append(ip.id, new_events, expected_version=ip.version - len(new_events), aggregate=ip)
        await self._read_model_repo.upsert_from_aggregate(ip)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteIPAddressHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPAddressReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteIPAddressCommand) -> None:
        ip = await self._event_store.load_aggregate(IPAddress, command.ip_id)
        if ip is None:
            raise EntityNotFoundError(f"IP address {command.ip_id} not found")

        ip.delete()

        new_events = ip.collect_uncommitted_events()
        await self._event_store.append(ip.id, new_events, expected_version=ip.version - len(new_events), aggregate=ip)
        await self._read_model_repo.mark_deleted(ip.id)
        await self._event_producer.publish_many("ipam.events", new_events)


class BulkCreateIPAddressesHandler(CommandHandler[list[UUID]]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPAddressReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateIPAddressesCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            if await self._read_model_repo.exists_in_vrf(item.address, item.vrf_id):
                raise ConflictError(f"IP address {item.address} already exists in this VRF scope")

            ip = IPAddress.create(
                address=item.address,
                vrf_id=item.vrf_id,
                status=IPAddressStatus(item.status),
                dns_name=item.dns_name,
                tenant_id=item.tenant_id,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = ip.collect_uncommitted_events()
            await self._event_store.append(ip.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(ip)
            all_events.extend(events)
            results.append(ip.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkUpdateIPAddressesHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPAddressReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateIPAddressesCommand) -> int:
        all_events: list = []
        for item in command.items:
            ip = await self._event_store.load_aggregate(IPAddress, item.ip_id)
            if ip is None:
                raise EntityNotFoundError(f"IP address {item.ip_id} not found")
            ip.update(
                dns_name=item.dns_name,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = ip.collect_uncommitted_events()
            await self._event_store.append(
                ip.id, new_events, expected_version=ip.version - len(new_events), aggregate=ip
            )
            await self._read_model_repo.upsert_from_aggregate(ip)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteIPAddressesHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPAddressReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteIPAddressesCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            ip = await self._event_store.load_aggregate(IPAddress, agg_id)
            if ip is None:
                raise EntityNotFoundError(f"IP address {agg_id} not found")
            ip.delete()
            new_events = ip.collect_uncommitted_events()
            await self._event_store.append(
                ip.id, new_events, expected_version=ip.version - len(new_events), aggregate=ip
            )
            await self._read_model_repo.mark_deleted(ip.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)
