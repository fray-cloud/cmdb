from __future__ import annotations

from uuid import UUID

from shared.cqrs.command import CommandHandler
from shared.domain.exceptions import EntityNotFoundError
from shared.event.pg_store import PostgresEventStore
from shared.messaging.producer import KafkaEventProducer

from ipam.asn.command.commands import (
    BulkCreateASNsCommand,
    BulkDeleteASNsCommand,
    BulkUpdateASNsCommand,
    CreateASNCommand,
    DeleteASNCommand,
    UpdateASNCommand,
)
from ipam.asn.domain.asn import ASN
from ipam.asn.query.read_model import ASNReadModelRepository

# ---------------------------------------------------------------------------
# ASN
# ---------------------------------------------------------------------------


class CreateASNHandler(CommandHandler[UUID]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ASNReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateASNCommand) -> UUID:
        asn = ASN.create(
            asn=command.asn,
            rir_id=command.rir_id,
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = asn.collect_uncommitted_events()
        await self._event_store.append(asn.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(asn)
        await self._event_producer.publish_many("ipam.events", events)
        return asn.id


class UpdateASNHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ASNReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateASNCommand) -> None:
        asn = await self._event_store.load_aggregate(ASN, command.asn_id)
        if asn is None:
            raise EntityNotFoundError(f"ASN {command.asn_id} not found")

        asn.update(
            description=command.description,
            tenant_id=command.tenant_id,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = asn.collect_uncommitted_events()
        await self._event_store.append(
            asn.id, new_events, expected_version=asn.version - len(new_events), aggregate=asn
        )
        await self._read_model_repo.upsert_from_aggregate(asn)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteASNHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ASNReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteASNCommand) -> None:
        asn = await self._event_store.load_aggregate(ASN, command.asn_id)
        if asn is None:
            raise EntityNotFoundError(f"ASN {command.asn_id} not found")

        asn.delete()

        new_events = asn.collect_uncommitted_events()
        await self._event_store.append(
            asn.id, new_events, expected_version=asn.version - len(new_events), aggregate=asn
        )
        await self._read_model_repo.mark_deleted(asn.id)
        await self._event_producer.publish_many("ipam.events", new_events)


# ---------------------------------------------------------------------------
# Bulk Operations
# ---------------------------------------------------------------------------


class BulkCreateASNsHandler(CommandHandler[list[UUID]]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ASNReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateASNsCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            asn = ASN.create(
                asn=item.asn,
                rir_id=item.rir_id,
                tenant_id=item.tenant_id,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = asn.collect_uncommitted_events()
            await self._event_store.append(asn.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(asn)
            all_events.extend(events)
            results.append(asn.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkUpdateASNsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ASNReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateASNsCommand) -> int:
        all_events: list = []
        for item in command.items:
            asn = await self._event_store.load_aggregate(ASN, item.asn_id)
            if asn is None:
                raise EntityNotFoundError(f"ASN {item.asn_id} not found")
            asn.update(
                description=item.description,
                tenant_id=item.tenant_id,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = asn.collect_uncommitted_events()
            await self._event_store.append(
                asn.id, new_events, expected_version=asn.version - len(new_events), aggregate=asn
            )
            await self._read_model_repo.upsert_from_aggregate(asn)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteASNsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ASNReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteASNsCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            asn = await self._event_store.load_aggregate(ASN, agg_id)
            if asn is None:
                raise EntityNotFoundError(f"ASN {agg_id} not found")
            asn.delete()
            new_events = asn.collect_uncommitted_events()
            await self._event_store.append(
                asn.id, new_events, expected_version=asn.version - len(new_events), aggregate=asn
            )
            await self._read_model_repo.mark_deleted(asn.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)
