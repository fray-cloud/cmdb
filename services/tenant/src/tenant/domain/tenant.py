from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field
from shared.domain.entity import Entity
from shared.domain.exceptions import BusinessRuleViolationError
from shared.domain.value_object import ValueObject
from shared.event.domain_event import DomainEvent

from tenant.domain.events import TenantCreated, TenantDeleted, TenantSuspended


class TenantStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class TenantSettings(ValueObject):
    custom_domain: str | None = None
    logo_url: str | None = None
    theme: str | None = None


class TenantDbConfig(ValueObject):
    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def sync_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


class Tenant(Entity):
    name: str
    slug: str
    status: TenantStatus = TenantStatus.ACTIVE
    settings: TenantSettings = Field(default_factory=TenantSettings)
    db_config: TenantDbConfig | None = None

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
        name: str,
        slug: str,
        settings: TenantSettings | None = None,
        db_config: TenantDbConfig | None = None,
    ) -> "Tenant":
        tenant = cls(
            name=name,
            slug=slug,
            settings=settings or TenantSettings(),
            db_config=db_config,
        )
        tenant._pending_events.append(
            TenantCreated(
                aggregate_id=tenant.id,
                version=1,
                tenant_name=name,
                slug=slug,
            )
        )
        return tenant

    def suspend(self) -> None:
        if self.status == TenantStatus.DELETED:
            raise BusinessRuleViolationError("Cannot suspend a deleted tenant")
        if self.status == TenantStatus.SUSPENDED:
            raise BusinessRuleViolationError("Tenant is already suspended")
        self.status = TenantStatus.SUSPENDED
        self.updated_at = datetime.now()
        self._pending_events.append(TenantSuspended(aggregate_id=self.id, version=1))

    def mark_deleted(self) -> None:
        if self.status == TenantStatus.DELETED:
            raise BusinessRuleViolationError("Tenant is already deleted")
        self.status = TenantStatus.DELETED
        self.updated_at = datetime.now()
        self._pending_events.append(TenantDeleted(aggregate_id=self.id, version=1))

    def update_settings(self, settings: TenantSettings) -> None:
        if self.status == TenantStatus.DELETED:
            raise BusinessRuleViolationError("Cannot update a deleted tenant")
        self.settings = settings
        self.updated_at = datetime.now()
