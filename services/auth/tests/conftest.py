from uuid import UUID

import pytest
from auth.domain.api_token import APIToken
from auth.domain.group import Group
from auth.domain.repository import APITokenRepository, GroupRepository, RoleRepository, UserRepository
from auth.domain.role import Role
from auth.domain.user import User
from auth.infrastructure.config import Settings
from auth.infrastructure.security import BcryptPasswordService, JWTService
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from shared.event.domain_event import DomainEvent
from shared.messaging.producer import KafkaEventProducer

# ---------------------------------------------------------------------------
# In-Memory Repository Implementations
# ---------------------------------------------------------------------------


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, User] = {}

    async def find_by_id(self, entity_id: UUID) -> User | None:
        return self._store.get(entity_id)

    async def save(self, entity: User) -> User:
        self._store[entity.id] = entity
        return entity

    async def delete(self, entity_id: UUID) -> None:
        self._store.pop(entity_id, None)

    async def find_by_email(self, email: str, tenant_id: UUID) -> User | None:
        for user in self._store.values():
            if user.email == email and user.tenant_id == tenant_id:
                return user
        return None

    async def find_all(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[User], int]:
        users = [u for u in self._store.values() if u.tenant_id == tenant_id]
        return users[offset : offset + limit], len(users)


class InMemoryRoleRepository(RoleRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Role] = {}

    async def find_by_id(self, entity_id: UUID) -> Role | None:
        return self._store.get(entity_id)

    async def save(self, entity: Role) -> Role:
        self._store[entity.id] = entity
        return entity

    async def delete(self, entity_id: UUID) -> None:
        self._store.pop(entity_id, None)

    async def find_by_name(self, name: str, tenant_id: UUID) -> Role | None:
        for role in self._store.values():
            if role.name == name and role.tenant_id == tenant_id:
                return role
        return None

    async def find_by_ids(self, role_ids: list[UUID]) -> list[Role]:
        return [r for r in self._store.values() if r.id in role_ids]

    async def find_all(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Role], int]:
        roles = [r for r in self._store.values() if r.tenant_id == tenant_id]
        return roles[offset : offset + limit], len(roles)


class InMemoryGroupRepository(GroupRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Group] = {}

    async def find_by_id(self, entity_id: UUID) -> Group | None:
        return self._store.get(entity_id)

    async def save(self, entity: Group) -> Group:
        self._store[entity.id] = entity
        return entity

    async def delete(self, entity_id: UUID) -> None:
        self._store.pop(entity_id, None)

    async def find_by_name(self, name: str, tenant_id: UUID) -> Group | None:
        for group in self._store.values():
            if group.name == name and group.tenant_id == tenant_id:
                return group
        return None

    async def find_by_ids(self, group_ids: list[UUID]) -> list[Group]:
        return [g for g in self._store.values() if g.id in group_ids]

    async def find_all(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Group], int]:
        groups = [g for g in self._store.values() if g.tenant_id == tenant_id]
        return groups[offset : offset + limit], len(groups)


class InMemoryAPITokenRepository(APITokenRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, APIToken] = {}

    async def find_by_id(self, entity_id: UUID) -> APIToken | None:
        return self._store.get(entity_id)

    async def save(self, entity: APIToken) -> APIToken:
        self._store[entity.id] = entity
        return entity

    async def delete(self, entity_id: UUID) -> None:
        self._store.pop(entity_id, None)

    async def find_by_key_hash(self, key_hash: str) -> APIToken | None:
        for token in self._store.values():
            if token.key_hash == key_hash:
                return token
        return None

    async def find_all_by_user(
        self,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[APIToken], int]:
        tokens = [t for t in self._store.values() if t.user_id == user_id]
        return tokens[offset : offset + limit], len(tokens)


# ---------------------------------------------------------------------------
# Fake Kafka Producer
# ---------------------------------------------------------------------------


class FakeKafkaProducer(KafkaEventProducer):
    """A no-op Kafka producer that records published events for assertions."""

    def __init__(self) -> None:
        self.published: list[tuple[str, DomainEvent]] = []

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def publish(self, topic: str, event: DomainEvent) -> None:
        self.published.append((topic, event))

    async def publish_many(self, topic: str, events: list[DomainEvent]) -> None:
        for event in events:
            self.published.append((topic, event))


# ---------------------------------------------------------------------------
# Fake Login Rate Limiter
# ---------------------------------------------------------------------------


class FakeLoginRateLimiter:
    """A no-op rate limiter that never locks."""

    async def is_locked(self, email: str, ip: str) -> bool:
        return False

    async def record_failure(self, email: str, ip: str) -> None:
        pass

    async def reset(self, email: str, ip: str) -> None:
        pass


# ---------------------------------------------------------------------------
# RSA Key Pair for JWT
# ---------------------------------------------------------------------------


def _generate_rsa_keys() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )
    return private_pem, public_pem


_PRIVATE_PEM, _PUBLIC_PEM = _generate_rsa_keys()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user_repository() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def role_repository() -> InMemoryRoleRepository:
    return InMemoryRoleRepository()


@pytest.fixture
def group_repository() -> InMemoryGroupRepository:
    return InMemoryGroupRepository()


@pytest.fixture
def api_token_repository() -> InMemoryAPITokenRepository:
    return InMemoryAPITokenRepository()


@pytest.fixture
def password_service() -> BcryptPasswordService:
    return BcryptPasswordService(rounds=4)


@pytest.fixture
def jwt_settings() -> Settings:
    return Settings(
        rsa_private_key=_PRIVATE_PEM,
        rsa_public_key=_PUBLIC_PEM,
        jwt_algorithm="RS256",
        jwt_access_token_expire_minutes=30,
        jwt_refresh_token_expire_days=7,
    )


@pytest.fixture
def jwt_service(jwt_settings: Settings) -> JWTService:
    return JWTService(jwt_settings)


@pytest.fixture
def event_producer() -> FakeKafkaProducer:
    return FakeKafkaProducer()


@pytest.fixture
def rate_limiter() -> FakeLoginRateLimiter:
    return FakeLoginRateLimiter()
