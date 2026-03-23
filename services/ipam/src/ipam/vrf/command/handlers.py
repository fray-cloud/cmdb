from __future__ import annotations

from uuid import UUID

from shared.cqrs.command import CommandHandler
from shared.domain.exceptions import EntityNotFoundError
from shared.event.pg_store import PostgresEventStore
from shared.messaging.producer import KafkaEventProducer

from ipam.vrf.command.commands import (
    BulkCreateVRFsCommand,
    BulkDeleteVRFsCommand,
    BulkUpdateVRFsCommand,
    CreateVRFCommand,
    DeleteVRFCommand,
    UpdateVRFCommand,
)
from ipam.vrf.domain.vrf import VRF
from ipam.vrf.query.read_model import VRFReadModelRepository


class CreateVRFHandler(CommandHandler[UUID]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VRFReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateVRFCommand) -> UUID:
        vrf = VRF.create(
            name=command.name,
            rd=command.rd,
            import_targets=command.import_targets or [],
            export_targets=command.export_targets or [],
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = vrf.collect_uncommitted_events()
        await self._event_store.append(vrf.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(vrf)
        await self._event_producer.publish_many("ipam.events", events)
        return vrf.id


class UpdateVRFHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VRFReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateVRFCommand) -> None:
        vrf = await self._event_store.load_aggregate(VRF, command.vrf_id)
        if vrf is None:
            raise EntityNotFoundError(f"VRF {command.vrf_id} not found")

        vrf.update(
            name=command.name,
            import_targets=command.import_targets,
            export_targets=command.export_targets,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = vrf.collect_uncommitted_events()
        await self._event_store.append(
            vrf.id, new_events, expected_version=vrf.version - len(new_events), aggregate=vrf
        )
        await self._read_model_repo.upsert_from_aggregate(vrf)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteVRFHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VRFReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteVRFCommand) -> None:
        vrf = await self._event_store.load_aggregate(VRF, command.vrf_id)
        if vrf is None:
            raise EntityNotFoundError(f"VRF {command.vrf_id} not found")

        vrf.delete()

        new_events = vrf.collect_uncommitted_events()
        await self._event_store.append(
            vrf.id, new_events, expected_version=vrf.version - len(new_events), aggregate=vrf
        )
        await self._read_model_repo.mark_deleted(vrf.id)
        await self._event_producer.publish_many("ipam.events", new_events)


class BulkCreateVRFsHandler(CommandHandler[list[UUID]]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VRFReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateVRFsCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            vrf = VRF.create(
                name=item.name,
                rd=item.rd,
                import_targets=item.import_targets,
                export_targets=item.export_targets,
                tenant_id=item.tenant_id,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = vrf.collect_uncommitted_events()
            await self._event_store.append(vrf.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(vrf)
            all_events.extend(events)
            results.append(vrf.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkUpdateVRFsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VRFReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateVRFsCommand) -> int:
        all_events: list = []
        for item in command.items:
            vrf = await self._event_store.load_aggregate(VRF, item.vrf_id)
            if vrf is None:
                raise EntityNotFoundError(f"VRF {item.vrf_id} not found")
            vrf.update(
                name=item.name,
                import_targets=item.import_targets,
                export_targets=item.export_targets,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = vrf.collect_uncommitted_events()
            await self._event_store.append(
                vrf.id, new_events, expected_version=vrf.version - len(new_events), aggregate=vrf
            )
            await self._read_model_repo.upsert_from_aggregate(vrf)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteVRFsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VRFReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteVRFsCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            vrf = await self._event_store.load_aggregate(VRF, agg_id)
            if vrf is None:
                raise EntityNotFoundError(f"VRF {agg_id} not found")
            vrf.delete()
            new_events = vrf.collect_uncommitted_events()
            await self._event_store.append(
                vrf.id, new_events, expected_version=vrf.version - len(new_events), aggregate=vrf
            )
            await self._read_model_repo.mark_deleted(vrf.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)
