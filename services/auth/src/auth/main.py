from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.api.errors import domain_exception_handler
from shared.api.middleware import CorrelationIdMiddleware
from shared.domain.exceptions import DomainError
from shared.messaging.producer import KafkaEventProducer
from shared.messaging.serialization import EventSerializer

from auth.routers import api_token_router, auth_router, permission_router, role_router, user_router
from auth.shared.config import Settings
from auth.shared.database import Database
from auth.shared.domain.events import (
    RoleAssigned,
    RoleRemoved,
    TokenGenerated,
    TokenRevoked,
    UserCreated,
    UserLocked,
)
from auth.shared.login_rate_limiter import LoginRateLimiter
from auth.shared.security import BcryptPasswordService, JWTService
from auth.shared.token_blacklist import RedisTokenBlacklist


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = Settings()

    database = Database(settings.database_url)

    serializer = EventSerializer()
    serializer.register(UserCreated)
    serializer.register(UserLocked)
    serializer.register(RoleAssigned)
    serializer.register(RoleRemoved)
    serializer.register(TokenGenerated)
    serializer.register(TokenRevoked)
    event_producer = KafkaEventProducer(
        settings.kafka_bootstrap_servers,
        serializer,
    )
    await event_producer.start()

    password_service = BcryptPasswordService(settings.bcrypt_rounds)
    jwt_service = JWTService(settings)
    token_blacklist = RedisTokenBlacklist(settings.redis_url)
    rate_limiter = LoginRateLimiter(settings.redis_url)

    app.state.database = database
    app.state.settings = settings
    app.state.event_producer = event_producer
    app.state.password_service = password_service
    app.state.jwt_service = jwt_service
    app.state.token_blacklist = token_blacklist
    app.state.rate_limiter = rate_limiter

    yield

    await event_producer.stop()
    await token_blacklist.close()
    await rate_limiter.close()
    await database.close()


def create_app() -> FastAPI:
    app = FastAPI(title="CMDB Auth Service", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_exception_handler)
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(role_router)
    app.include_router(api_token_router)
    app.include_router(permission_router)

    # JWKS endpoint
    @app.get("/auth/.well-known/jwks.json", tags=["auth"])
    async def jwks() -> dict:
        return app.state.jwt_service.get_jwks()

    # Health check
    @app.get("/health", include_in_schema=False)
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
