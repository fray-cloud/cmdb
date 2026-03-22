from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.api.errors import domain_exception_handler
from shared.api.middleware import CorrelationIdMiddleware
from shared.domain.exceptions import DomainError
from shared.messaging.producer import KafkaEventProducer
from shared.messaging.serialization import EventSerializer

from tenant.domain.events import TenantCreated, TenantDeleted, TenantSuspended
from tenant.infrastructure.config import Settings
from tenant.infrastructure.database import Database
from tenant.infrastructure.db_provisioning import TenantDbProvisioner
from tenant.infrastructure.tenant_db_manager import TenantDbManager
from tenant.interface.router import router
from tenant.interface.setup_router import setup_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = Settings()

    database = Database(settings.database_url)

    serializer = EventSerializer()
    serializer.register(TenantCreated)
    serializer.register(TenantSuspended)
    serializer.register(TenantDeleted)
    event_producer = KafkaEventProducer(
        settings.kafka_bootstrap_servers,
        serializer,
    )
    await event_producer.start()

    provisioner = TenantDbProvisioner(settings)
    tenant_db_manager = TenantDbManager()

    app.state.database = database
    app.state.settings = settings
    app.state.event_producer = event_producer
    app.state.provisioner = provisioner
    app.state.tenant_db_manager = tenant_db_manager

    yield

    await event_producer.stop()
    await database.close()
    await tenant_db_manager.close_all()


def create_app() -> FastAPI:
    app = FastAPI(title="CMDB Tenant Service", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_exception_handler)
    app.include_router(router)
    app.include_router(setup_router)
    return app


app = create_app()
