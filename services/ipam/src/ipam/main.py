import asyncio
import contextlib
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.api.errors import domain_exception_handler
from shared.api.middleware import CorrelationIdMiddleware, UserMiddleware
from shared.domain.exceptions import DomainError
from shared.event.pg_store import PostgresEventStore
from shared.messaging.consumer import KafkaEventConsumer
from shared.messaging.producer import KafkaEventProducer
from shared.messaging.serialization import EventSerializer
from strawberry.fastapi import GraphQLRouter

from ipam.asn.domain.events import ASNCreated, ASNDeleted, ASNUpdated
from ipam.fhrp_group.domain.events import FHRPGroupCreated, FHRPGroupDeleted, FHRPGroupUpdated
from ipam.graphql.context import get_graphql_context
from ipam.graphql.schema import schema
from ipam.ip_address.domain.events import (
    IPAddressCreated,
    IPAddressDeleted,
    IPAddressStatusChanged,
    IPAddressUpdated,
)
from ipam.ip_range.domain.events import IPRangeCreated, IPRangeDeleted, IPRangeStatusChanged, IPRangeUpdated
from ipam.prefix.domain.events import PrefixCreated, PrefixDeleted, PrefixStatusChanged, PrefixUpdated
from ipam.rir.domain.events import RIRCreated, RIRDeleted, RIRUpdated
from ipam.route_target.domain.events import RouteTargetCreated, RouteTargetDeleted, RouteTargetUpdated
from ipam.routers import ALL_ROUTERS
from ipam.service_entity.domain.events import ServiceCreated, ServiceDeleted, ServiceUpdated
from ipam.shared.cache import RedisCache
from ipam.shared.config import Settings
from ipam.shared.database import Database
from ipam.shared.event_projector import IPAMEventProjector
from ipam.vlan.domain.events import VLANCreated, VLANDeleted, VLANStatusChanged, VLANUpdated
from ipam.vlan_group.domain.events import VLANGroupCreated, VLANGroupDeleted, VLANGroupUpdated
from ipam.vrf.domain.events import VRFCreated, VRFDeleted, VRFUpdated

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


OPENAPI_TAGS = [
    {"name": "prefixes", "description": "IP prefix (subnet) management"},
    {"name": "ip-addresses", "description": "IP address management"},
    {"name": "vrfs", "description": "Virtual Routing and Forwarding instances"},
    {"name": "vlans", "description": "VLAN management"},
    {"name": "ip-ranges", "description": "IP address range management"},
    {"name": "rirs", "description": "Regional Internet Registries"},
    {"name": "asns", "description": "Autonomous System Numbers"},
    {"name": "fhrp-groups", "description": "First Hop Redundancy Protocol groups"},
    {"name": "route-targets", "description": "BGP route targets for VRF import/export"},
    {"name": "vlan-groups", "description": "VLAN group management"},
    {"name": "services", "description": "Network service (TCP/UDP/SCTP) management"},
    {"name": "saved-filters", "description": "User-specific saved filter presets"},
    {"name": "search", "description": "Global full-text search across IPAM entities"},
    {"name": "import-export", "description": "CSV import, CSV/JSON/YAML export, Jinja2 templates"},
]


def create_app() -> FastAPI:
    app = FastAPI(
        title="CMDB IPAM Service",
        version="1.0.0",
        description="IP Address Management service — prefixes, addresses, VRFs, VLANs, and more.",
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(UserMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_exception_handler)
    for router in ALL_ROUTERS:
        app.include_router(router, prefix="/api/v1")
    graphql_app = GraphQLRouter(schema, context_getter=get_graphql_context)
    app.include_router(graphql_app, prefix="/graphql")
    return app


app = create_app()
