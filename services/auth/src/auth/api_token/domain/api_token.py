"""API token aggregate for programmatic access credentials."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field
from shared.domain.entity import Entity
from shared.domain.exceptions import BusinessRuleViolationError
from shared.event.domain_event import DomainEvent

from auth.shared.domain import TokenGenerated, TokenRevoked


class APIToken(Entity):
    """API token aggregate root managing scoped, revocable access keys."""

    user_id: UUID
    tenant_id: UUID
    key_hash: str
    description: str | None = None
    scopes: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None
    allowed_ips: list[str] = Field(default_factory=list)
    last_used_at: datetime | None = None
    is_revoked: bool = False

    def model_post_init(self, __context: Any) -> None:
        object.__setattr__(self, "_pending_events", [])

    def collect_events(self) -> list[DomainEvent]:
        events: list[DomainEvent] = list(self._pending_events)
        self._pending_events.clear()
        return events

    @classmethod
    def create(
        cls,
        *,
        user_id: UUID,
        tenant_id: UUID,
        key_hash: str,
        description: str | None = None,
        scopes: list[str] | None = None,
        expires_at: datetime | None = None,
        allowed_ips: list[str] | None = None,
    ) -> "APIToken":
        """Create a new API token and emit a TokenGenerated event."""
        token = cls(
            user_id=user_id,
            tenant_id=tenant_id,
            key_hash=key_hash,
            description=description,
            scopes=scopes or [],
            expires_at=expires_at,
            allowed_ips=allowed_ips or [],
        )
        token._pending_events.append(
            TokenGenerated(
                aggregate_id=token.id,
                version=1,
                user_id=user_id,
                token_type="api_token",
            )
        )
        return token

    def revoke(self) -> None:
        if self.is_revoked:
            raise BusinessRuleViolationError("Token is already revoked")
        self.is_revoked = True
        self.updated_at = datetime.now()
        self._pending_events.append(TokenRevoked(aggregate_id=self.id, version=1))

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() >= self.expires_at

    def has_scope(self, scope: str) -> bool:
        if not self.scopes:
            return True
        return scope in self.scopes
