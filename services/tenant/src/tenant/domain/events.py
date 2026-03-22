from shared.event.domain_event import DomainEvent


class TenantCreated(DomainEvent):
    tenant_name: str
    slug: str


class TenantSuspended(DomainEvent):
    pass


class TenantDeleted(DomainEvent):
    pass
