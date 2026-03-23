from uuid import UUID

from shared.event.domain_event import DomainEvent


class UserCreated(DomainEvent):
    email: str
    tenant_id: UUID


class UserLocked(DomainEvent):
    pass


class RoleAssigned(DomainEvent):
    user_id: UUID
    role_id: UUID


class RoleRemoved(DomainEvent):
    user_id: UUID
    role_id: UUID


class TokenGenerated(DomainEvent):
    user_id: UUID
    token_type: str


class TokenRevoked(DomainEvent):
    pass
