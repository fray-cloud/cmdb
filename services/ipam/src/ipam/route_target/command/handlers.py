from __future__ import annotations

from uuid import UUID

from shared.cqrs.command import CommandHandler
from shared.domain.exceptions import EntityNotFoundError
from shared.event.pg_store import PostgresEventStore
from shared.messaging.producer import KafkaEventProducer

from ipam.route_target.command.commands import (
    BulkCreateRouteTargetsCommand,
    BulkDeleteRouteTargetsCommand,
    BulkUpdateRouteTargetsCommand,
    CreateRouteTargetCommand,
    DeleteRouteTargetCommand,
    UpdateRouteTargetCommand,
)
from ipam.route_target.domain.route_target import RouteTarget
from ipam.route_target.query.read_model import RouteTargetReadModelRepository

# ---------------------------------------------------------------------------
# RouteTarget
# ---------------------------------------------------------------------------


class CreateRouteTargetHandler(CommandHandler[UUID]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RouteTargetReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateRouteTargetCommand) -> UUID:
        rt = RouteTarget.create(
            name=command.name,
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = rt.collect_uncommitted_events()
        await self._event_store.append(rt.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(rt)
        await self._event_producer.publish_many("ipam.events", events)
        return rt.id


class UpdateRouteTargetHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RouteTargetReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateRouteTargetCommand) -> None:
        rt = await self._event_store.load_aggregate(RouteTarget, command.route_target_id)
        if rt is None:
            raise EntityNotFoundError(f"RouteTarget {command.route_target_id} not found")

        rt.update(
            description=command.description,
            tenant_id=command.tenant_id,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = rt.collect_uncommitted_events()
        await self._event_store.append(rt.id, new_events, expected_version=rt.version - len(new_events), aggregate=rt)
        await self._read_model_repo.upsert_from_aggregate(rt)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteRouteTargetHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RouteTargetReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteRouteTargetCommand) -> None:
        rt = await self._event_store.load_aggregate(RouteTarget, command.route_target_id)
        if rt is None:
            raise EntityNotFoundError(f"RouteTarget {command.route_target_id} not found")

        rt.delete()

        new_events = rt.collect_uncommitted_events()
        await self._event_store.append(rt.id, new_events, expected_version=rt.version - len(new_events), aggregate=rt)
        await self._read_model_repo.mark_deleted(rt.id)
        await self._event_producer.publish_many("ipam.events", new_events)


# ---------------------------------------------------------------------------
# Bulk Operations
# ---------------------------------------------------------------------------


class BulkCreateRouteTargetsHandler(CommandHandler[list[UUID]]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RouteTargetReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateRouteTargetsCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            rt = RouteTarget.create(
                name=item.name,
                tenant_id=item.tenant_id,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = rt.collect_uncommitted_events()
            await self._event_store.append(rt.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(rt)
            all_events.extend(events)
            results.append(rt.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkUpdateRouteTargetsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RouteTargetReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateRouteTargetsCommand) -> int:
        all_events: list = []
        for item in command.items:
            rt = await self._event_store.load_aggregate(RouteTarget, item.route_target_id)
            if rt is None:
                raise EntityNotFoundError(f"RouteTarget {item.route_target_id} not found")
            rt.update(
                description=item.description,
                tenant_id=item.tenant_id,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = rt.collect_uncommitted_events()
            await self._event_store.append(
                rt.id, new_events, expected_version=rt.version - len(new_events), aggregate=rt
            )
            await self._read_model_repo.upsert_from_aggregate(rt)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteRouteTargetsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RouteTargetReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteRouteTargetsCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            rt = await self._event_store.load_aggregate(RouteTarget, agg_id)
            if rt is None:
                raise EntityNotFoundError(f"RouteTarget {agg_id} not found")
            rt.delete()
            new_events = rt.collect_uncommitted_events()
            await self._event_store.append(
                rt.id, new_events, expected_version=rt.version - len(new_events), aggregate=rt
            )
            await self._read_model_repo.mark_deleted(rt.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)
