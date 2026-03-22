from uuid import UUID

from shared.cqrs.command import Command, CommandHandler
from shared.domain.exceptions import ConflictError, EntityNotFoundError
from shared.messaging.producer import KafkaEventProducer

from tenant.domain.repository import TenantRepository
from tenant.domain.tenant import Tenant, TenantSettings
from tenant.infrastructure.db_provisioning import TenantDbProvisioner


class CreateTenantHandler(CommandHandler[UUID]):
    def __init__(
        self,
        repository: TenantRepository,
        provisioner: TenantDbProvisioner,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._repository = repository
        self._provisioner = provisioner
        self._event_producer = event_producer

    async def handle(self, command: Command) -> UUID:
        existing = await self._repository.find_by_slug(command.slug)
        if existing is not None:
            raise ConflictError(f"Tenant with slug '{command.slug}' already exists")

        db_config = await self._provisioner.provision(command.slug)

        tenant = Tenant.create(
            name=command.name,
            slug=command.slug,
            settings=TenantSettings(
                custom_domain=command.custom_domain,
                logo_url=command.logo_url,
                theme=command.theme,
            ),
            db_config=db_config,
        )

        await self._repository.save(tenant)

        for event in tenant.collect_events():
            await self._event_producer.publish("tenant.events", event)

        return tenant.id


class SuspendTenantHandler(CommandHandler[None]):
    def __init__(
        self,
        repository: TenantRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._repository = repository
        self._event_producer = event_producer

    async def handle(self, command: Command) -> None:
        tenant = await self._repository.find_by_id(command.tenant_id)
        if tenant is None:
            raise EntityNotFoundError(f"Tenant {command.tenant_id} not found")
        tenant.suspend()
        await self._repository.save(tenant)
        for event in tenant.collect_events():
            await self._event_producer.publish("tenant.events", event)


class UpdateTenantSettingsHandler(CommandHandler[None]):
    def __init__(self, repository: TenantRepository) -> None:
        self._repository = repository

    async def handle(self, command: Command) -> None:
        tenant = await self._repository.find_by_id(command.tenant_id)
        if tenant is None:
            raise EntityNotFoundError(f"Tenant {command.tenant_id} not found")
        tenant.update_settings(
            TenantSettings(
                custom_domain=command.custom_domain,
                logo_url=command.logo_url,
                theme=command.theme,
            )
        )
        await self._repository.save(tenant)


class DeleteTenantHandler(CommandHandler[None]):
    def __init__(
        self,
        repository: TenantRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._repository = repository
        self._event_producer = event_producer

    async def handle(self, command: Command) -> None:
        tenant = await self._repository.find_by_id(command.tenant_id)
        if tenant is None:
            raise EntityNotFoundError(f"Tenant {command.tenant_id} not found")
        tenant.mark_deleted()
        await self._repository.save(tenant)
        for event in tenant.collect_events():
            await self._event_producer.publish("tenant.events", event)
