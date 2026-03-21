import logging
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

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
    VLANCreated,
    VLANDeleted,
    VLANStatusChanged,
    VLANUpdated,
    VRFCreated,
    VRFDeleted,
    VRFUpdated,
)
from ipam.infrastructure.models import (
    ASNReadModel,
    FHRPGroupReadModel,
    IPAddressReadModel,
    IPRangeReadModel,
    PrefixReadModel,
    RIRReadModel,
    VLANReadModel,
    VRFReadModel,
)
from shared.event.domain_event import DomainEvent
from shared.messaging.consumer import KafkaEventConsumer

logger = logging.getLogger(__name__)


class IPAMEventProjector:
    def __init__(self, session_factory: object, cache: object | None = None) -> None:
        self._session_factory = session_factory
        self._cache = cache

    async def _invalidate_cache(self, prefix_id: UUID) -> None:
        if self._cache is not None:
            await self._cache.invalidate_prefix_utilization(prefix_id)

    async def _handle_prefix_created(self, event: DomainEvent) -> None:
        assert isinstance(event, PrefixCreated)
        async with self._session_factory() as session:
            stmt = insert(PrefixReadModel).values(
                id=event.aggregate_id,
                network=event.network,
                vrf_id=event.vrf_id,
                vlan_id=event.vlan_id,
                status=event.status,
                role=event.role,
                tenant_id=event.tenant_id,
                description=event.description,
                custom_fields=event.custom_fields,
                tags=[str(t) for t in event.tags],
                is_deleted=False,
            )
            stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded))
            await session.execute(stmt)
            await session.commit()
        await self._invalidate_cache(event.aggregate_id)

    async def _handle_prefix_updated(self, event: DomainEvent) -> None:
        assert isinstance(event, PrefixUpdated)
        values: dict = {}
        if event.description is not None:
            values["description"] = event.description
        if event.role is not None:
            values["role"] = event.role
        if event.tenant_id is not None:
            values["tenant_id"] = event.tenant_id
        if event.vlan_id is not None:
            values["vlan_id"] = event.vlan_id
        if event.custom_fields is not None:
            values["custom_fields"] = event.custom_fields
        if event.tags is not None:
            values["tags"] = [str(t) for t in event.tags]
        if values:
            await self._update_model(PrefixReadModel, event.aggregate_id, values)
        await self._invalidate_cache(event.aggregate_id)

    async def _handle_prefix_status_changed(self, event: DomainEvent) -> None:
        assert isinstance(event, PrefixStatusChanged)
        await self._update_model(PrefixReadModel, event.aggregate_id, {"status": event.new_status})
        await self._invalidate_cache(event.aggregate_id)

    async def _handle_prefix_deleted(self, event: DomainEvent) -> None:
        await self._update_model(PrefixReadModel, event.aggregate_id, {"is_deleted": True})
        await self._invalidate_cache(event.aggregate_id)

    async def _handle_ip_address_created(self, event: DomainEvent) -> None:
        assert isinstance(event, IPAddressCreated)
        async with self._session_factory() as session:
            stmt = insert(IPAddressReadModel).values(
                id=event.aggregate_id,
                address=event.address,
                vrf_id=event.vrf_id,
                status=event.status,
                dns_name=event.dns_name,
                tenant_id=event.tenant_id,
                description=event.description,
                custom_fields=event.custom_fields,
                tags=[str(t) for t in event.tags],
                is_deleted=False,
            )
            stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded))
            await session.execute(stmt)
            await session.commit()

    async def _handle_ip_address_updated(self, event: DomainEvent) -> None:
        assert isinstance(event, IPAddressUpdated)
        values: dict = {}
        if event.dns_name is not None:
            values["dns_name"] = event.dns_name
        if event.description is not None:
            values["description"] = event.description
        if event.custom_fields is not None:
            values["custom_fields"] = event.custom_fields
        if event.tags is not None:
            values["tags"] = [str(t) for t in event.tags]
        if values:
            await self._update_model(IPAddressReadModel, event.aggregate_id, values)

    async def _handle_ip_address_status_changed(self, event: DomainEvent) -> None:
        assert isinstance(event, IPAddressStatusChanged)
        await self._update_model(IPAddressReadModel, event.aggregate_id, {"status": event.new_status})

    async def _handle_ip_address_deleted(self, event: DomainEvent) -> None:
        await self._update_model(IPAddressReadModel, event.aggregate_id, {"is_deleted": True})

    async def _handle_vrf_created(self, event: DomainEvent) -> None:
        assert isinstance(event, VRFCreated)
        async with self._session_factory() as session:
            stmt = insert(VRFReadModel).values(
                id=event.aggregate_id,
                name=event.name,
                rd=event.rd,
                tenant_id=event.tenant_id,
                description=event.description,
                custom_fields=event.custom_fields,
                tags=[str(t) for t in event.tags],
                is_deleted=False,
            )
            stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded))
            await session.execute(stmt)
            await session.commit()

    async def _handle_vrf_updated(self, event: DomainEvent) -> None:
        assert isinstance(event, VRFUpdated)
        values: dict = {}
        if event.name is not None:
            values["name"] = event.name
        if event.description is not None:
            values["description"] = event.description
        if event.custom_fields is not None:
            values["custom_fields"] = event.custom_fields
        if event.tags is not None:
            values["tags"] = [str(t) for t in event.tags]
        if values:
            await self._update_model(VRFReadModel, event.aggregate_id, values)

    async def _handle_vrf_deleted(self, event: DomainEvent) -> None:
        await self._update_model(VRFReadModel, event.aggregate_id, {"is_deleted": True})

    async def _handle_vlan_created(self, event: DomainEvent) -> None:
        assert isinstance(event, VLANCreated)
        async with self._session_factory() as session:
            stmt = insert(VLANReadModel).values(
                id=event.aggregate_id,
                vid=event.vid,
                name=event.name,
                group_id=event.group_id,
                status=event.status,
                role=event.role,
                tenant_id=event.tenant_id,
                description=event.description,
                custom_fields=event.custom_fields,
                tags=[str(t) for t in event.tags],
                is_deleted=False,
            )
            stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded))
            await session.execute(stmt)
            await session.commit()

    async def _handle_vlan_updated(self, event: DomainEvent) -> None:
        assert isinstance(event, VLANUpdated)
        values: dict = {}
        if event.name is not None:
            values["name"] = event.name
        if event.role is not None:
            values["role"] = event.role
        if event.description is not None:
            values["description"] = event.description
        if event.custom_fields is not None:
            values["custom_fields"] = event.custom_fields
        if event.tags is not None:
            values["tags"] = [str(t) for t in event.tags]
        if values:
            await self._update_model(VLANReadModel, event.aggregate_id, values)

    async def _handle_vlan_status_changed(self, event: DomainEvent) -> None:
        assert isinstance(event, VLANStatusChanged)
        await self._update_model(VLANReadModel, event.aggregate_id, {"status": event.new_status})

    async def _handle_vlan_deleted(self, event: DomainEvent) -> None:
        await self._update_model(VLANReadModel, event.aggregate_id, {"is_deleted": True})

    async def _handle_ip_range_created(self, event: DomainEvent) -> None:
        assert isinstance(event, IPRangeCreated)
        async with self._session_factory() as session:
            stmt = insert(IPRangeReadModel).values(
                id=event.aggregate_id,
                start_address=event.start_address,
                end_address=event.end_address,
                vrf_id=event.vrf_id,
                status=event.status,
                tenant_id=event.tenant_id,
                description=event.description,
                custom_fields=event.custom_fields,
                tags=[str(t) for t in event.tags],
                is_deleted=False,
            )
            stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded))
            await session.execute(stmt)
            await session.commit()

    async def _handle_ip_range_updated(self, event: DomainEvent) -> None:
        assert isinstance(event, IPRangeUpdated)
        values: dict = {}
        if event.description is not None:
            values["description"] = event.description
        if event.tenant_id is not None:
            values["tenant_id"] = event.tenant_id
        if event.custom_fields is not None:
            values["custom_fields"] = event.custom_fields
        if event.tags is not None:
            values["tags"] = [str(t) for t in event.tags]
        if values:
            await self._update_model(IPRangeReadModel, event.aggregate_id, values)

    async def _handle_ip_range_status_changed(self, event: DomainEvent) -> None:
        assert isinstance(event, IPRangeStatusChanged)
        await self._update_model(IPRangeReadModel, event.aggregate_id, {"status": event.new_status})

    async def _handle_ip_range_deleted(self, event: DomainEvent) -> None:
        await self._update_model(IPRangeReadModel, event.aggregate_id, {"is_deleted": True})

    async def _handle_rir_created(self, event: DomainEvent) -> None:
        assert isinstance(event, RIRCreated)
        async with self._session_factory() as session:
            stmt = insert(RIRReadModel).values(
                id=event.aggregate_id,
                name=event.name,
                is_private=event.is_private,
                description=event.description,
                custom_fields=event.custom_fields,
                tags=[str(t) for t in event.tags],
                is_deleted=False,
            )
            stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded))
            await session.execute(stmt)
            await session.commit()

    async def _handle_rir_updated(self, event: DomainEvent) -> None:
        assert isinstance(event, RIRUpdated)
        values: dict = {}
        if event.description is not None:
            values["description"] = event.description
        if event.is_private is not None:
            values["is_private"] = event.is_private
        if event.custom_fields is not None:
            values["custom_fields"] = event.custom_fields
        if event.tags is not None:
            values["tags"] = [str(t) for t in event.tags]
        if values:
            await self._update_model(RIRReadModel, event.aggregate_id, values)

    async def _handle_rir_deleted(self, event: DomainEvent) -> None:
        await self._update_model(RIRReadModel, event.aggregate_id, {"is_deleted": True})

    async def _handle_asn_created(self, event: DomainEvent) -> None:
        assert isinstance(event, ASNCreated)
        async with self._session_factory() as session:
            stmt = insert(ASNReadModel).values(
                id=event.aggregate_id,
                asn=event.asn,
                rir_id=event.rir_id,
                tenant_id=event.tenant_id,
                description=event.description,
                custom_fields=event.custom_fields,
                tags=[str(t) for t in event.tags],
                is_deleted=False,
            )
            stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded))
            await session.execute(stmt)
            await session.commit()

    async def _handle_asn_updated(self, event: DomainEvent) -> None:
        assert isinstance(event, ASNUpdated)
        values: dict = {}
        if event.description is not None:
            values["description"] = event.description
        if event.tenant_id is not None:
            values["tenant_id"] = event.tenant_id
        if event.custom_fields is not None:
            values["custom_fields"] = event.custom_fields
        if event.tags is not None:
            values["tags"] = [str(t) for t in event.tags]
        if values:
            await self._update_model(ASNReadModel, event.aggregate_id, values)

    async def _handle_asn_deleted(self, event: DomainEvent) -> None:
        await self._update_model(ASNReadModel, event.aggregate_id, {"is_deleted": True})

    async def _handle_fhrp_group_created(self, event: DomainEvent) -> None:
        assert isinstance(event, FHRPGroupCreated)
        async with self._session_factory() as session:
            stmt = insert(FHRPGroupReadModel).values(
                id=event.aggregate_id,
                protocol=event.protocol,
                group_id_value=event.group_id_value,
                auth_type=event.auth_type,
                auth_key=event.auth_key,
                name=event.name,
                description=event.description,
                custom_fields=event.custom_fields,
                tags=[str(t) for t in event.tags],
                is_deleted=False,
            )
            stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded))
            await session.execute(stmt)
            await session.commit()

    async def _handle_fhrp_group_updated(self, event: DomainEvent) -> None:
        assert isinstance(event, FHRPGroupUpdated)
        values: dict = {}
        if event.name is not None:
            values["name"] = event.name
        if event.auth_type is not None:
            values["auth_type"] = event.auth_type
        if event.auth_key is not None:
            values["auth_key"] = event.auth_key
        if event.description is not None:
            values["description"] = event.description
        if event.custom_fields is not None:
            values["custom_fields"] = event.custom_fields
        if event.tags is not None:
            values["tags"] = [str(t) for t in event.tags]
        if values:
            await self._update_model(FHRPGroupReadModel, event.aggregate_id, values)

    async def _handle_fhrp_group_deleted(self, event: DomainEvent) -> None:
        await self._update_model(FHRPGroupReadModel, event.aggregate_id, {"is_deleted": True})

    async def _update_model(self, model_cls: type, aggregate_id: UUID, values: dict) -> None:
        async with self._session_factory() as session:
            stmt = update(model_cls).where(model_cls.id == aggregate_id).values(**values)
            await session.execute(stmt)
            await session.commit()

    def register_all(self, consumer: KafkaEventConsumer) -> None:
        consumer.subscribe(PrefixCreated, self._handle_prefix_created)
        consumer.subscribe(PrefixUpdated, self._handle_prefix_updated)
        consumer.subscribe(PrefixStatusChanged, self._handle_prefix_status_changed)
        consumer.subscribe(PrefixDeleted, self._handle_prefix_deleted)

        consumer.subscribe(IPAddressCreated, self._handle_ip_address_created)
        consumer.subscribe(IPAddressUpdated, self._handle_ip_address_updated)
        consumer.subscribe(IPAddressStatusChanged, self._handle_ip_address_status_changed)
        consumer.subscribe(IPAddressDeleted, self._handle_ip_address_deleted)

        consumer.subscribe(VRFCreated, self._handle_vrf_created)
        consumer.subscribe(VRFUpdated, self._handle_vrf_updated)
        consumer.subscribe(VRFDeleted, self._handle_vrf_deleted)

        consumer.subscribe(VLANCreated, self._handle_vlan_created)
        consumer.subscribe(VLANUpdated, self._handle_vlan_updated)
        consumer.subscribe(VLANStatusChanged, self._handle_vlan_status_changed)
        consumer.subscribe(VLANDeleted, self._handle_vlan_deleted)

        consumer.subscribe(IPRangeCreated, self._handle_ip_range_created)
        consumer.subscribe(IPRangeUpdated, self._handle_ip_range_updated)
        consumer.subscribe(IPRangeStatusChanged, self._handle_ip_range_status_changed)
        consumer.subscribe(IPRangeDeleted, self._handle_ip_range_deleted)

        consumer.subscribe(RIRCreated, self._handle_rir_created)
        consumer.subscribe(RIRUpdated, self._handle_rir_updated)
        consumer.subscribe(RIRDeleted, self._handle_rir_deleted)

        consumer.subscribe(ASNCreated, self._handle_asn_created)
        consumer.subscribe(ASNUpdated, self._handle_asn_updated)
        consumer.subscribe(ASNDeleted, self._handle_asn_deleted)

        consumer.subscribe(FHRPGroupCreated, self._handle_fhrp_group_created)
        consumer.subscribe(FHRPGroupUpdated, self._handle_fhrp_group_updated)
        consumer.subscribe(FHRPGroupDeleted, self._handle_fhrp_group_deleted)
