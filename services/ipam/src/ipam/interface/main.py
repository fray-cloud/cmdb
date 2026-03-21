import asyncio
import contextlib
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ipam.domain.events import (
    ASNCreated,
    ASNDeleted,
    ASNUpdated,
    FHRPGroupCreated,
    FHRPGroupDeleted,
    FHRPGroupUpdated,
    IPAddressCreated,
    IPAddressDeleted,
    IPAddressStatusChanged,
    IPAddressUpdated,
    IPRangeCreated,
    IPRangeDeleted,
    IPRangeStatusChanged,
    IPRangeUpdated,
    PrefixCreated,
    PrefixDeleted,
    PrefixStatusChanged,
    PrefixUpdated,
    RIRCreated,
    RIRDeleted,
    RIRUpdated,
    RouteTargetCreated,
    RouteTargetDeleted,
    RouteTargetUpdated,
    ServiceCreated,
    ServiceDeleted,
    ServiceUpdated,
    VLANCreated,
    VLANDeleted,
    VLANGroupCreated,
    VLANGroupDeleted,
    VLANGroupUpdated,
    VLANStatusChanged,
    VLANUpdated,
    VRFCreated,
    VRFDeleted,
    VRFUpdated,
)
from ipam.infrastructure.cache import RedisCache
from ipam.infrastructure.config import Settings
from ipam.infrastructure.database import Database
from ipam.infrastructure.event_projector import IPAMEventProjector
from ipam.interface.routers.asn_router import router as asn_router
from ipam.interface.routers.fhrp_group_router import router as fhrp_group_router
from ipam.interface.routers.ip_address_router import router as ip_address_router
from ipam.interface.routers.ip_range_router import router as ip_range_router
from ipam.interface.routers.prefix_router import router as prefix_router
from ipam.interface.routers.rir_router import router as rir_router
from ipam.interface.routers.route_target_router import router as route_target_router
from ipam.interface.routers.service_router import router as service_router
from ipam.interface.routers.vlan_group_router import router as vlan_group_router
from ipam.interface.routers.vlan_router import router as vlan_router
from ipam.interface.routers.vrf_router import router as vrf_router
from shared.api.errors import domain_exception_handler
from shared.api.middleware import CorrelationIdMiddleware
from shared.domain.exceptions import DomainError
from shared.event.pg_store import PostgresEventStore
from shared.messaging.consumer import KafkaEventConsumer
from shared.messaging.producer import KafkaEventProducer
from shared.messaging.serialization import EventSerializer

logger = logging.getLogger(__name__)

ALL_EVENTS = [
    # Prefix
    PrefixCreated,
    PrefixUpdated,
    PrefixStatusChanged,
    PrefixDeleted,
    # IPAddress
    IPAddressCreated,
    IPAddressUpdated,
    IPAddressStatusChanged,
    IPAddressDeleted,
    # VRF
    VRFCreated,
    VRFUpdated,
    VRFDeleted,
    # VLAN
    VLANCreated,
    VLANUpdated,
    VLANStatusChanged,
    VLANDeleted,
    # IPRange
    IPRangeCreated,
    IPRangeUpdated,
    IPRangeStatusChanged,
    IPRangeDeleted,
    # RIR
    RIRCreated,
    RIRUpdated,
    RIRDeleted,
    # ASN
    ASNCreated,
    ASNUpdated,
    ASNDeleted,
    # FHRPGroup
    FHRPGroupCreated,
    FHRPGroupUpdated,
    FHRPGroupDeleted,
    # RouteTarget
    RouteTargetCreated,
    RouteTargetUpdated,
    RouteTargetDeleted,
    # VLANGroup
    VLANGroupCreated,
    VLANGroupUpdated,
    VLANGroupDeleted,
    # Service
    ServiceCreated,
    ServiceUpdated,
    ServiceDeleted,
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = Settings()
    database = Database(settings.database_url)

    event_store = PostgresEventStore(database.session)
    for event_cls in ALL_EVENTS:
        event_store.register_event_type(event_cls)

    serializer = EventSerializer()
    for event_cls in ALL_EVENTS:
        serializer.register(event_cls)
    event_producer = KafkaEventProducer(settings.kafka_bootstrap_servers, serializer)
    await event_producer.start()

    projector_consumer = KafkaEventConsumer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="ipam-projector",
        topics=["ipam.events"],
        serializer=serializer,
    )
    cache = RedisCache(settings.redis_url)
    await cache.connect()

    projector = IPAMEventProjector(database.session, cache=cache)
    projector.register_all(projector_consumer)
    await projector_consumer.start()
    consumer_task = asyncio.create_task(projector_consumer.consume())

    app.state.settings = settings
    app.state.database = database
    app.state.event_store = event_store
    app.state.event_producer = event_producer
    app.state.cache = cache

    yield

    consumer_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await consumer_task
    await projector_consumer.stop()
    await event_producer.stop()
    await cache.close()
    await database.close()


def create_app() -> FastAPI:
    app = FastAPI(title="CMDB IPAM Service", lifespan=lifespan)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_exception_handler)
    app.include_router(prefix_router, prefix="/api/v1")
    app.include_router(ip_address_router, prefix="/api/v1")
    app.include_router(vrf_router, prefix="/api/v1")
    app.include_router(vlan_router, prefix="/api/v1")
    app.include_router(ip_range_router, prefix="/api/v1")
    app.include_router(rir_router, prefix="/api/v1")
    app.include_router(asn_router, prefix="/api/v1")
    app.include_router(fhrp_group_router, prefix="/api/v1")
    app.include_router(route_target_router, prefix="/api/v1")
    app.include_router(vlan_group_router, prefix="/api/v1")
    app.include_router(service_router, prefix="/api/v1")
    return app


app = create_app()
