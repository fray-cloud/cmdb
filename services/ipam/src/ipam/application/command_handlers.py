from __future__ import annotations

from uuid import UUID, uuid4

from shared.cqrs.command import Command, CommandHandler
from shared.domain.exceptions import ConflictError, EntityNotFoundError
from shared.event.pg_store import PostgresEventStore
from shared.messaging.producer import KafkaEventProducer

from ipam.application.commands import (
    BulkCreateASNsCommand,
    BulkCreateFHRPGroupsCommand,
    BulkCreateIPAddressesCommand,
    BulkCreateIPRangesCommand,
    BulkCreatePrefixesCommand,
    BulkCreateRIRsCommand,
    BulkCreateRouteTargetsCommand,
    BulkCreateServicesCommand,
    BulkCreateVLANGroupsCommand,
    BulkCreateVLANsCommand,
    BulkCreateVRFsCommand,
    BulkDeleteASNsCommand,
    BulkDeleteFHRPGroupsCommand,
    BulkDeleteIPAddressesCommand,
    BulkDeleteIPRangesCommand,
    BulkDeletePrefixesCommand,
    BulkDeleteRIRsCommand,
    BulkDeleteRouteTargetsCommand,
    BulkDeleteServicesCommand,
    BulkDeleteVLANGroupsCommand,
    BulkDeleteVLANsCommand,
    BulkDeleteVRFsCommand,
    BulkUpdateASNsCommand,
    BulkUpdateFHRPGroupsCommand,
    BulkUpdateIPAddressesCommand,
    BulkUpdateIPRangesCommand,
    BulkUpdatePrefixesCommand,
    BulkUpdateRIRsCommand,
    BulkUpdateRouteTargetsCommand,
    BulkUpdateServicesCommand,
    BulkUpdateVLANGroupsCommand,
    BulkUpdateVLANsCommand,
    BulkUpdateVRFsCommand,
    ChangeIPAddressStatusCommand,
    ChangeIPRangeStatusCommand,
    ChangePrefixStatusCommand,
    ChangeVLANStatusCommand,
    CreateASNCommand,
    CreateFHRPGroupCommand,
    CreateIPAddressCommand,
    CreateIPRangeCommand,
    CreatePrefixCommand,
    CreateRIRCommand,
    CreateRouteTargetCommand,
    CreateServiceCommand,
    CreateVLANCommand,
    CreateVLANGroupCommand,
    CreateVRFCommand,
    DeleteASNCommand,
    DeleteFHRPGroupCommand,
    DeleteIPAddressCommand,
    DeleteIPRangeCommand,
    DeletePrefixCommand,
    DeleteRIRCommand,
    DeleteRouteTargetCommand,
    DeleteServiceCommand,
    DeleteVLANCommand,
    DeleteVLANGroupCommand,
    DeleteVRFCommand,
    UpdateASNCommand,
    UpdateFHRPGroupCommand,
    UpdateIPAddressCommand,
    UpdateIPRangeCommand,
    UpdatePrefixCommand,
    UpdateRIRCommand,
    UpdateRouteTargetCommand,
    UpdateServiceCommand,
    UpdateVLANCommand,
    UpdateVLANGroupCommand,
    UpdateVRFCommand,
)
from ipam.application.read_model import (
    ASNReadModelRepository,
    FHRPGroupReadModelRepository,
    IPAddressReadModelRepository,
    IPRangeReadModelRepository,
    PrefixReadModelRepository,
    RIRReadModelRepository,
    RouteTargetReadModelRepository,
    SavedFilterRepository,
    ServiceReadModelRepository,
    VLANGroupReadModelRepository,
    VLANReadModelRepository,
    VRFReadModelRepository,
)
from ipam.domain.asn import ASN
from ipam.domain.fhrp_group import FHRPGroup
from ipam.domain.ip_address import IPAddress
from ipam.domain.ip_range import IPRange
from ipam.domain.prefix import Prefix
from ipam.domain.rir import RIR
from ipam.domain.route_target import RouteTarget
from ipam.domain.service import Service
from ipam.domain.value_objects import (
    FHRPAuthType,
    FHRPProtocol,
    IPAddressStatus,
    IPRangeStatus,
    PrefixStatus,
    ServiceProtocol,
    VLANStatus,
)
from ipam.domain.vlan import VLAN
from ipam.domain.vlan_group import VLANGroup
from ipam.domain.vrf import VRF

# ---------------------------------------------------------------------------
# Prefix
# ---------------------------------------------------------------------------


class CreatePrefixHandler(CommandHandler[UUID]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: PrefixReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreatePrefixCommand) -> UUID:
        prefix = Prefix.create(
            network=command.network,
            vrf_id=command.vrf_id,
            vlan_id=command.vlan_id,
            status=PrefixStatus(command.status),
            role=command.role,
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = prefix.collect_uncommitted_events()
        await self._event_store.append(prefix.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(prefix)
        await self._event_producer.publish_many("ipam.events", events)
        return prefix.id


class UpdatePrefixHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: PrefixReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdatePrefixCommand) -> None:
        prefix = await self._event_store.load_aggregate(Prefix, command.prefix_id)
        if prefix is None:
            raise EntityNotFoundError(f"Prefix {command.prefix_id} not found")

        prefix.update(
            description=command.description,
            role=command.role,
            tenant_id=command.tenant_id,
            vlan_id=command.vlan_id,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = prefix.collect_uncommitted_events()
        await self._event_store.append(
            prefix.id, new_events, expected_version=prefix.version - len(new_events), aggregate=prefix
        )
        await self._read_model_repo.upsert_from_aggregate(prefix)
        await self._event_producer.publish_many("ipam.events", new_events)


class ChangePrefixStatusHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: PrefixReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: ChangePrefixStatusCommand) -> None:
        prefix = await self._event_store.load_aggregate(Prefix, command.prefix_id)
        if prefix is None:
            raise EntityNotFoundError(f"Prefix {command.prefix_id} not found")

        prefix.change_status(PrefixStatus(command.status))

        new_events = prefix.collect_uncommitted_events()
        await self._event_store.append(
            prefix.id, new_events, expected_version=prefix.version - len(new_events), aggregate=prefix
        )
        await self._read_model_repo.upsert_from_aggregate(prefix)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeletePrefixHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: PrefixReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeletePrefixCommand) -> None:
        prefix = await self._event_store.load_aggregate(Prefix, command.prefix_id)
        if prefix is None:
            raise EntityNotFoundError(f"Prefix {command.prefix_id} not found")

        prefix.delete()

        new_events = prefix.collect_uncommitted_events()
        await self._event_store.append(
            prefix.id, new_events, expected_version=prefix.version - len(new_events), aggregate=prefix
        )
        await self._read_model_repo.mark_deleted(prefix.id)
        await self._event_producer.publish_many("ipam.events", new_events)


# ---------------------------------------------------------------------------
# IPAddress
# ---------------------------------------------------------------------------


class CreateIPAddressHandler(CommandHandler[UUID]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPAddressReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateIPAddressCommand) -> UUID:
        if await self._read_model_repo.exists_in_vrf(command.address, command.vrf_id):
            raise ConflictError(f"IP address {command.address} already exists in this VRF scope")

        ip = IPAddress.create(
            address=command.address,
            vrf_id=command.vrf_id,
            status=IPAddressStatus(command.status),
            dns_name=command.dns_name,
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = ip.collect_uncommitted_events()
        await self._event_store.append(ip.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(ip)
        await self._event_producer.publish_many("ipam.events", events)
        return ip.id


class UpdateIPAddressHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPAddressReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateIPAddressCommand) -> None:
        ip = await self._event_store.load_aggregate(IPAddress, command.ip_id)
        if ip is None:
            raise EntityNotFoundError(f"IP address {command.ip_id} not found")

        ip.update(
            dns_name=command.dns_name,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = ip.collect_uncommitted_events()
        await self._event_store.append(ip.id, new_events, expected_version=ip.version - len(new_events), aggregate=ip)
        await self._read_model_repo.upsert_from_aggregate(ip)
        await self._event_producer.publish_many("ipam.events", new_events)


class ChangeIPAddressStatusHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPAddressReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: ChangeIPAddressStatusCommand) -> None:
        ip = await self._event_store.load_aggregate(IPAddress, command.ip_id)
        if ip is None:
            raise EntityNotFoundError(f"IP address {command.ip_id} not found")

        ip.change_status(IPAddressStatus(command.status))

        new_events = ip.collect_uncommitted_events()
        await self._event_store.append(ip.id, new_events, expected_version=ip.version - len(new_events), aggregate=ip)
        await self._read_model_repo.upsert_from_aggregate(ip)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteIPAddressHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPAddressReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteIPAddressCommand) -> None:
        ip = await self._event_store.load_aggregate(IPAddress, command.ip_id)
        if ip is None:
            raise EntityNotFoundError(f"IP address {command.ip_id} not found")

        ip.delete()

        new_events = ip.collect_uncommitted_events()
        await self._event_store.append(ip.id, new_events, expected_version=ip.version - len(new_events), aggregate=ip)
        await self._read_model_repo.mark_deleted(ip.id)
        await self._event_producer.publish_many("ipam.events", new_events)


# ---------------------------------------------------------------------------
# VRF
# ---------------------------------------------------------------------------


class CreateVRFHandler(CommandHandler[UUID]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VRFReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateVRFCommand) -> UUID:
        vrf = VRF.create(
            name=command.name,
            rd=command.rd,
            import_targets=command.import_targets or [],
            export_targets=command.export_targets or [],
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = vrf.collect_uncommitted_events()
        await self._event_store.append(vrf.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(vrf)
        await self._event_producer.publish_many("ipam.events", events)
        return vrf.id


class UpdateVRFHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VRFReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateVRFCommand) -> None:
        vrf = await self._event_store.load_aggregate(VRF, command.vrf_id)
        if vrf is None:
            raise EntityNotFoundError(f"VRF {command.vrf_id} not found")

        vrf.update(
            name=command.name,
            import_targets=command.import_targets,
            export_targets=command.export_targets,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = vrf.collect_uncommitted_events()
        await self._event_store.append(
            vrf.id, new_events, expected_version=vrf.version - len(new_events), aggregate=vrf
        )
        await self._read_model_repo.upsert_from_aggregate(vrf)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteVRFHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VRFReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteVRFCommand) -> None:
        vrf = await self._event_store.load_aggregate(VRF, command.vrf_id)
        if vrf is None:
            raise EntityNotFoundError(f"VRF {command.vrf_id} not found")

        vrf.delete()

        new_events = vrf.collect_uncommitted_events()
        await self._event_store.append(
            vrf.id, new_events, expected_version=vrf.version - len(new_events), aggregate=vrf
        )
        await self._read_model_repo.mark_deleted(vrf.id)
        await self._event_producer.publish_many("ipam.events", new_events)


# ---------------------------------------------------------------------------
# VLAN
# ---------------------------------------------------------------------------


class CreateVLANHandler(CommandHandler[UUID]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateVLANCommand) -> UUID:
        vlan = VLAN.create(
            vid=command.vid,
            name=command.name,
            group_id=command.group_id,
            status=VLANStatus(command.status),
            role=command.role,
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = vlan.collect_uncommitted_events()
        await self._event_store.append(vlan.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(vlan)
        await self._event_producer.publish_many("ipam.events", events)
        return vlan.id


class UpdateVLANHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateVLANCommand) -> None:
        vlan = await self._event_store.load_aggregate(VLAN, command.vlan_id)
        if vlan is None:
            raise EntityNotFoundError(f"VLAN {command.vlan_id} not found")

        vlan.update(
            name=command.name,
            role=command.role,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = vlan.collect_uncommitted_events()
        await self._event_store.append(
            vlan.id, new_events, expected_version=vlan.version - len(new_events), aggregate=vlan
        )
        await self._read_model_repo.upsert_from_aggregate(vlan)
        await self._event_producer.publish_many("ipam.events", new_events)


class ChangeVLANStatusHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: ChangeVLANStatusCommand) -> None:
        vlan = await self._event_store.load_aggregate(VLAN, command.vlan_id)
        if vlan is None:
            raise EntityNotFoundError(f"VLAN {command.vlan_id} not found")

        vlan.change_status(VLANStatus(command.status))

        new_events = vlan.collect_uncommitted_events()
        await self._event_store.append(
            vlan.id, new_events, expected_version=vlan.version - len(new_events), aggregate=vlan
        )
        await self._read_model_repo.upsert_from_aggregate(vlan)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteVLANHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteVLANCommand) -> None:
        vlan = await self._event_store.load_aggregate(VLAN, command.vlan_id)
        if vlan is None:
            raise EntityNotFoundError(f"VLAN {command.vlan_id} not found")

        vlan.delete()

        new_events = vlan.collect_uncommitted_events()
        await self._event_store.append(
            vlan.id, new_events, expected_version=vlan.version - len(new_events), aggregate=vlan
        )
        await self._read_model_repo.mark_deleted(vlan.id)
        await self._event_producer.publish_many("ipam.events", new_events)


# ---------------------------------------------------------------------------
# IPRange
# ---------------------------------------------------------------------------


class CreateIPRangeHandler(CommandHandler[UUID]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPRangeReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateIPRangeCommand) -> UUID:
        ip_range = IPRange.create(
            start_address=command.start_address,
            end_address=command.end_address,
            vrf_id=command.vrf_id,
            status=IPRangeStatus(command.status),
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = ip_range.collect_uncommitted_events()
        await self._event_store.append(ip_range.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(ip_range)
        await self._event_producer.publish_many("ipam.events", events)
        return ip_range.id


class UpdateIPRangeHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPRangeReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateIPRangeCommand) -> None:
        ip_range = await self._event_store.load_aggregate(IPRange, command.range_id)
        if ip_range is None:
            raise EntityNotFoundError(f"IP range {command.range_id} not found")

        ip_range.update(
            description=command.description,
            tenant_id=command.tenant_id,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = ip_range.collect_uncommitted_events()
        await self._event_store.append(
            ip_range.id, new_events, expected_version=ip_range.version - len(new_events), aggregate=ip_range
        )
        await self._read_model_repo.upsert_from_aggregate(ip_range)
        await self._event_producer.publish_many("ipam.events", new_events)


class ChangeIPRangeStatusHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPRangeReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: ChangeIPRangeStatusCommand) -> None:
        ip_range = await self._event_store.load_aggregate(IPRange, command.range_id)
        if ip_range is None:
            raise EntityNotFoundError(f"IP range {command.range_id} not found")

        ip_range.change_status(IPRangeStatus(command.status))

        new_events = ip_range.collect_uncommitted_events()
        await self._event_store.append(
            ip_range.id, new_events, expected_version=ip_range.version - len(new_events), aggregate=ip_range
        )
        await self._read_model_repo.upsert_from_aggregate(ip_range)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteIPRangeHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPRangeReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteIPRangeCommand) -> None:
        ip_range = await self._event_store.load_aggregate(IPRange, command.range_id)
        if ip_range is None:
            raise EntityNotFoundError(f"IP range {command.range_id} not found")

        ip_range.delete()

        new_events = ip_range.collect_uncommitted_events()
        await self._event_store.append(
            ip_range.id, new_events, expected_version=ip_range.version - len(new_events), aggregate=ip_range
        )
        await self._read_model_repo.mark_deleted(ip_range.id)
        await self._event_producer.publish_many("ipam.events", new_events)


# ---------------------------------------------------------------------------
# RIR
# ---------------------------------------------------------------------------


class CreateRIRHandler(CommandHandler[UUID]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RIRReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateRIRCommand) -> UUID:
        rir = RIR.create(
            name=command.name,
            is_private=command.is_private,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = rir.collect_uncommitted_events()
        await self._event_store.append(rir.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(rir)
        await self._event_producer.publish_many("ipam.events", events)
        return rir.id


class UpdateRIRHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RIRReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateRIRCommand) -> None:
        rir = await self._event_store.load_aggregate(RIR, command.rir_id)
        if rir is None:
            raise EntityNotFoundError(f"RIR {command.rir_id} not found")

        rir.update(
            description=command.description,
            is_private=command.is_private,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = rir.collect_uncommitted_events()
        await self._event_store.append(
            rir.id, new_events, expected_version=rir.version - len(new_events), aggregate=rir
        )
        await self._read_model_repo.upsert_from_aggregate(rir)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteRIRHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RIRReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteRIRCommand) -> None:
        rir = await self._event_store.load_aggregate(RIR, command.rir_id)
        if rir is None:
            raise EntityNotFoundError(f"RIR {command.rir_id} not found")

        rir.delete()

        new_events = rir.collect_uncommitted_events()
        await self._event_store.append(
            rir.id, new_events, expected_version=rir.version - len(new_events), aggregate=rir
        )
        await self._read_model_repo.mark_deleted(rir.id)
        await self._event_producer.publish_many("ipam.events", new_events)


# ---------------------------------------------------------------------------
# ASN
# ---------------------------------------------------------------------------


class CreateASNHandler(CommandHandler[UUID]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ASNReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateASNCommand) -> UUID:
        asn = ASN.create(
            asn=command.asn,
            rir_id=command.rir_id,
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = asn.collect_uncommitted_events()
        await self._event_store.append(asn.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(asn)
        await self._event_producer.publish_many("ipam.events", events)
        return asn.id


class UpdateASNHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ASNReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateASNCommand) -> None:
        asn = await self._event_store.load_aggregate(ASN, command.asn_id)
        if asn is None:
            raise EntityNotFoundError(f"ASN {command.asn_id} not found")

        asn.update(
            description=command.description,
            tenant_id=command.tenant_id,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = asn.collect_uncommitted_events()
        await self._event_store.append(
            asn.id, new_events, expected_version=asn.version - len(new_events), aggregate=asn
        )
        await self._read_model_repo.upsert_from_aggregate(asn)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteASNHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ASNReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteASNCommand) -> None:
        asn = await self._event_store.load_aggregate(ASN, command.asn_id)
        if asn is None:
            raise EntityNotFoundError(f"ASN {command.asn_id} not found")

        asn.delete()

        new_events = asn.collect_uncommitted_events()
        await self._event_store.append(
            asn.id, new_events, expected_version=asn.version - len(new_events), aggregate=asn
        )
        await self._read_model_repo.mark_deleted(asn.id)
        await self._event_producer.publish_many("ipam.events", new_events)


# ---------------------------------------------------------------------------
# FHRPGroup
# ---------------------------------------------------------------------------


class CreateFHRPGroupHandler(CommandHandler[UUID]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: FHRPGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateFHRPGroupCommand) -> UUID:
        group = FHRPGroup.create(
            protocol=FHRPProtocol(command.protocol),
            group_id_value=command.group_id_value,
            auth_type=FHRPAuthType(command.auth_type),
            auth_key=command.auth_key,
            name=command.name,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = group.collect_uncommitted_events()
        await self._event_store.append(group.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(group)
        await self._event_producer.publish_many("ipam.events", events)
        return group.id


class UpdateFHRPGroupHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: FHRPGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateFHRPGroupCommand) -> None:
        group = await self._event_store.load_aggregate(FHRPGroup, command.fhrp_group_id)
        if group is None:
            raise EntityNotFoundError(f"FHRP group {command.fhrp_group_id} not found")

        group.update(
            name=command.name,
            auth_type=command.auth_type,
            auth_key=command.auth_key,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = group.collect_uncommitted_events()
        await self._event_store.append(
            group.id, new_events, expected_version=group.version - len(new_events), aggregate=group
        )
        await self._read_model_repo.upsert_from_aggregate(group)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteFHRPGroupHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: FHRPGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteFHRPGroupCommand) -> None:
        group = await self._event_store.load_aggregate(FHRPGroup, command.fhrp_group_id)
        if group is None:
            raise EntityNotFoundError(f"FHRP group {command.fhrp_group_id} not found")

        group.delete()

        new_events = group.collect_uncommitted_events()
        await self._event_store.append(
            group.id, new_events, expected_version=group.version - len(new_events), aggregate=group
        )
        await self._read_model_repo.mark_deleted(group.id)
        await self._event_producer.publish_many("ipam.events", new_events)


# ---------------------------------------------------------------------------
# Bulk Operations
# ---------------------------------------------------------------------------


class BulkCreatePrefixesHandler(CommandHandler[list[UUID]]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: PrefixReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreatePrefixesCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            prefix = Prefix.create(
                network=item.network,
                vrf_id=item.vrf_id,
                vlan_id=item.vlan_id,
                status=PrefixStatus(item.status),
                role=item.role,
                tenant_id=item.tenant_id,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = prefix.collect_uncommitted_events()
            await self._event_store.append(prefix.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(prefix)
            all_events.extend(events)
            results.append(prefix.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkCreateIPAddressesHandler(CommandHandler[list[UUID]]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPAddressReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateIPAddressesCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            if await self._read_model_repo.exists_in_vrf(item.address, item.vrf_id):
                raise ConflictError(f"IP address {item.address} already exists in this VRF scope")

            ip = IPAddress.create(
                address=item.address,
                vrf_id=item.vrf_id,
                status=IPAddressStatus(item.status),
                dns_name=item.dns_name,
                tenant_id=item.tenant_id,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = ip.collect_uncommitted_events()
            await self._event_store.append(ip.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(ip)
            all_events.extend(events)
            results.append(ip.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkCreateVRFsHandler(CommandHandler[list[UUID]]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VRFReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateVRFsCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            vrf = VRF.create(
                name=item.name,
                rd=item.rd,
                import_targets=item.import_targets,
                export_targets=item.export_targets,
                tenant_id=item.tenant_id,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = vrf.collect_uncommitted_events()
            await self._event_store.append(vrf.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(vrf)
            all_events.extend(events)
            results.append(vrf.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkCreateVLANsHandler(CommandHandler[list[UUID]]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateVLANsCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            vlan = VLAN.create(
                vid=item.vid,
                name=item.name,
                group_id=item.group_id,
                status=VLANStatus(item.status),
                role=item.role,
                tenant_id=item.tenant_id,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = vlan.collect_uncommitted_events()
            await self._event_store.append(vlan.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(vlan)
            all_events.extend(events)
            results.append(vlan.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkCreateIPRangesHandler(CommandHandler[list[UUID]]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPRangeReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateIPRangesCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            ip_range = IPRange.create(
                start_address=item.start_address,
                end_address=item.end_address,
                vrf_id=item.vrf_id,
                status=IPRangeStatus(item.status),
                tenant_id=item.tenant_id,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = ip_range.collect_uncommitted_events()
            await self._event_store.append(ip_range.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(ip_range)
            all_events.extend(events)
            results.append(ip_range.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkCreateRIRsHandler(CommandHandler[list[UUID]]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RIRReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateRIRsCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            rir = RIR.create(
                name=item.name,
                is_private=item.is_private,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = rir.collect_uncommitted_events()
            await self._event_store.append(rir.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(rir)
            all_events.extend(events)
            results.append(rir.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkCreateASNsHandler(CommandHandler[list[UUID]]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ASNReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateASNsCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            asn = ASN.create(
                asn=item.asn,
                rir_id=item.rir_id,
                tenant_id=item.tenant_id,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = asn.collect_uncommitted_events()
            await self._event_store.append(asn.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(asn)
            all_events.extend(events)
            results.append(asn.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkCreateFHRPGroupsHandler(CommandHandler[list[UUID]]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: FHRPGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateFHRPGroupsCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            group = FHRPGroup.create(
                protocol=FHRPProtocol(item.protocol),
                group_id_value=item.group_id_value,
                auth_type=FHRPAuthType(item.auth_type),
                auth_key=item.auth_key,
                name=item.name,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = group.collect_uncommitted_events()
            await self._event_store.append(group.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(group)
            all_events.extend(events)
            results.append(group.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


# ---------------------------------------------------------------------------
# Bulk Update / Delete
# ---------------------------------------------------------------------------


class BulkUpdatePrefixesHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: PrefixReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdatePrefixesCommand) -> int:
        all_events: list = []
        for item in command.items:
            prefix = await self._event_store.load_aggregate(Prefix, item.prefix_id)
            if prefix is None:
                raise EntityNotFoundError(f"Prefix {item.prefix_id} not found")
            prefix.update(
                description=item.description,
                role=item.role,
                tenant_id=item.tenant_id,
                vlan_id=item.vlan_id,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = prefix.collect_uncommitted_events()
            await self._event_store.append(
                prefix.id, new_events, expected_version=prefix.version - len(new_events), aggregate=prefix
            )
            await self._read_model_repo.upsert_from_aggregate(prefix)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeletePrefixesHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: PrefixReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeletePrefixesCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            prefix = await self._event_store.load_aggregate(Prefix, agg_id)
            if prefix is None:
                raise EntityNotFoundError(f"Prefix {agg_id} not found")
            prefix.delete()
            new_events = prefix.collect_uncommitted_events()
            await self._event_store.append(
                prefix.id, new_events, expected_version=prefix.version - len(new_events), aggregate=prefix
            )
            await self._read_model_repo.mark_deleted(prefix.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)


class BulkUpdateIPAddressesHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPAddressReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateIPAddressesCommand) -> int:
        all_events: list = []
        for item in command.items:
            ip = await self._event_store.load_aggregate(IPAddress, item.ip_id)
            if ip is None:
                raise EntityNotFoundError(f"IP address {item.ip_id} not found")
            ip.update(
                dns_name=item.dns_name,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = ip.collect_uncommitted_events()
            await self._event_store.append(
                ip.id, new_events, expected_version=ip.version - len(new_events), aggregate=ip
            )
            await self._read_model_repo.upsert_from_aggregate(ip)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteIPAddressesHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPAddressReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteIPAddressesCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            ip = await self._event_store.load_aggregate(IPAddress, agg_id)
            if ip is None:
                raise EntityNotFoundError(f"IP address {agg_id} not found")
            ip.delete()
            new_events = ip.collect_uncommitted_events()
            await self._event_store.append(
                ip.id, new_events, expected_version=ip.version - len(new_events), aggregate=ip
            )
            await self._read_model_repo.mark_deleted(ip.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)


class BulkUpdateVRFsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VRFReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateVRFsCommand) -> int:
        all_events: list = []
        for item in command.items:
            vrf = await self._event_store.load_aggregate(VRF, item.vrf_id)
            if vrf is None:
                raise EntityNotFoundError(f"VRF {item.vrf_id} not found")
            vrf.update(
                name=item.name,
                import_targets=item.import_targets,
                export_targets=item.export_targets,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = vrf.collect_uncommitted_events()
            await self._event_store.append(
                vrf.id, new_events, expected_version=vrf.version - len(new_events), aggregate=vrf
            )
            await self._read_model_repo.upsert_from_aggregate(vrf)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteVRFsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VRFReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteVRFsCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            vrf = await self._event_store.load_aggregate(VRF, agg_id)
            if vrf is None:
                raise EntityNotFoundError(f"VRF {agg_id} not found")
            vrf.delete()
            new_events = vrf.collect_uncommitted_events()
            await self._event_store.append(
                vrf.id, new_events, expected_version=vrf.version - len(new_events), aggregate=vrf
            )
            await self._read_model_repo.mark_deleted(vrf.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)


class BulkUpdateVLANsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateVLANsCommand) -> int:
        all_events: list = []
        for item in command.items:
            vlan = await self._event_store.load_aggregate(VLAN, item.vlan_id)
            if vlan is None:
                raise EntityNotFoundError(f"VLAN {item.vlan_id} not found")
            vlan.update(
                name=item.name,
                role=item.role,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = vlan.collect_uncommitted_events()
            await self._event_store.append(
                vlan.id, new_events, expected_version=vlan.version - len(new_events), aggregate=vlan
            )
            await self._read_model_repo.upsert_from_aggregate(vlan)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteVLANsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteVLANsCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            vlan = await self._event_store.load_aggregate(VLAN, agg_id)
            if vlan is None:
                raise EntityNotFoundError(f"VLAN {agg_id} not found")
            vlan.delete()
            new_events = vlan.collect_uncommitted_events()
            await self._event_store.append(
                vlan.id, new_events, expected_version=vlan.version - len(new_events), aggregate=vlan
            )
            await self._read_model_repo.mark_deleted(vlan.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)


class BulkUpdateIPRangesHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPRangeReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateIPRangesCommand) -> int:
        all_events: list = []
        for item in command.items:
            ip_range = await self._event_store.load_aggregate(IPRange, item.range_id)
            if ip_range is None:
                raise EntityNotFoundError(f"IP range {item.range_id} not found")
            ip_range.update(
                description=item.description,
                tenant_id=item.tenant_id,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = ip_range.collect_uncommitted_events()
            await self._event_store.append(
                ip_range.id, new_events, expected_version=ip_range.version - len(new_events), aggregate=ip_range
            )
            await self._read_model_repo.upsert_from_aggregate(ip_range)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteIPRangesHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: IPRangeReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteIPRangesCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            ip_range = await self._event_store.load_aggregate(IPRange, agg_id)
            if ip_range is None:
                raise EntityNotFoundError(f"IP range {agg_id} not found")
            ip_range.delete()
            new_events = ip_range.collect_uncommitted_events()
            await self._event_store.append(
                ip_range.id, new_events, expected_version=ip_range.version - len(new_events), aggregate=ip_range
            )
            await self._read_model_repo.mark_deleted(ip_range.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)


class BulkUpdateRIRsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RIRReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateRIRsCommand) -> int:
        all_events: list = []
        for item in command.items:
            rir = await self._event_store.load_aggregate(RIR, item.rir_id)
            if rir is None:
                raise EntityNotFoundError(f"RIR {item.rir_id} not found")
            rir.update(
                description=item.description,
                is_private=item.is_private,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = rir.collect_uncommitted_events()
            await self._event_store.append(
                rir.id, new_events, expected_version=rir.version - len(new_events), aggregate=rir
            )
            await self._read_model_repo.upsert_from_aggregate(rir)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteRIRsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RIRReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteRIRsCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            rir = await self._event_store.load_aggregate(RIR, agg_id)
            if rir is None:
                raise EntityNotFoundError(f"RIR {agg_id} not found")
            rir.delete()
            new_events = rir.collect_uncommitted_events()
            await self._event_store.append(
                rir.id, new_events, expected_version=rir.version - len(new_events), aggregate=rir
            )
            await self._read_model_repo.mark_deleted(rir.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)


class BulkUpdateASNsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ASNReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateASNsCommand) -> int:
        all_events: list = []
        for item in command.items:
            asn = await self._event_store.load_aggregate(ASN, item.asn_id)
            if asn is None:
                raise EntityNotFoundError(f"ASN {item.asn_id} not found")
            asn.update(
                description=item.description,
                tenant_id=item.tenant_id,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = asn.collect_uncommitted_events()
            await self._event_store.append(
                asn.id, new_events, expected_version=asn.version - len(new_events), aggregate=asn
            )
            await self._read_model_repo.upsert_from_aggregate(asn)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteASNsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ASNReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteASNsCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            asn = await self._event_store.load_aggregate(ASN, agg_id)
            if asn is None:
                raise EntityNotFoundError(f"ASN {agg_id} not found")
            asn.delete()
            new_events = asn.collect_uncommitted_events()
            await self._event_store.append(
                asn.id, new_events, expected_version=asn.version - len(new_events), aggregate=asn
            )
            await self._read_model_repo.mark_deleted(asn.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)


class BulkUpdateFHRPGroupsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: FHRPGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateFHRPGroupsCommand) -> int:
        all_events: list = []
        for item in command.items:
            group = await self._event_store.load_aggregate(FHRPGroup, item.fhrp_group_id)
            if group is None:
                raise EntityNotFoundError(f"FHRP group {item.fhrp_group_id} not found")
            group.update(
                name=item.name,
                auth_type=item.auth_type,
                auth_key=item.auth_key,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = group.collect_uncommitted_events()
            await self._event_store.append(
                group.id, new_events, expected_version=group.version - len(new_events), aggregate=group
            )
            await self._read_model_repo.upsert_from_aggregate(group)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteFHRPGroupsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: FHRPGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteFHRPGroupsCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            group = await self._event_store.load_aggregate(FHRPGroup, agg_id)
            if group is None:
                raise EntityNotFoundError(f"FHRP group {agg_id} not found")
            group.delete()
            new_events = group.collect_uncommitted_events()
            await self._event_store.append(
                group.id, new_events, expected_version=group.version - len(new_events), aggregate=group
            )
            await self._read_model_repo.mark_deleted(group.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)


# ---------------------------------------------------------------------------
# RouteTarget
# ---------------------------------------------------------------------------


class CreateRouteTargetHandler(CommandHandler[UUID]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RouteTargetReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateRouteTargetCommand) -> UUID:
        rt = RouteTarget.create(
            name=command.name,
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = rt.collect_uncommitted_events()
        await self._event_store.append(rt.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(rt)
        await self._event_producer.publish_many("ipam.events", events)
        return rt.id


class UpdateRouteTargetHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RouteTargetReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateRouteTargetCommand) -> None:
        rt = await self._event_store.load_aggregate(RouteTarget, command.route_target_id)
        if rt is None:
            raise EntityNotFoundError(f"RouteTarget {command.route_target_id} not found")

        rt.update(
            description=command.description,
            tenant_id=command.tenant_id,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = rt.collect_uncommitted_events()
        await self._event_store.append(rt.id, new_events, expected_version=rt.version - len(new_events), aggregate=rt)
        await self._read_model_repo.upsert_from_aggregate(rt)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteRouteTargetHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RouteTargetReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteRouteTargetCommand) -> None:
        rt = await self._event_store.load_aggregate(RouteTarget, command.route_target_id)
        if rt is None:
            raise EntityNotFoundError(f"RouteTarget {command.route_target_id} not found")

        rt.delete()

        new_events = rt.collect_uncommitted_events()
        await self._event_store.append(rt.id, new_events, expected_version=rt.version - len(new_events), aggregate=rt)
        await self._read_model_repo.mark_deleted(rt.id)
        await self._event_producer.publish_many("ipam.events", new_events)


# ---------------------------------------------------------------------------
# VLANGroup
# ---------------------------------------------------------------------------


class CreateVLANGroupHandler(CommandHandler[UUID]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateVLANGroupCommand) -> UUID:
        group = VLANGroup.create(
            name=command.name,
            slug=command.slug,
            min_vid=command.min_vid,
            max_vid=command.max_vid,
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = group.collect_uncommitted_events()
        await self._event_store.append(group.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(group)
        await self._event_producer.publish_many("ipam.events", events)
        return group.id


class UpdateVLANGroupHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateVLANGroupCommand) -> None:
        group = await self._event_store.load_aggregate(VLANGroup, command.vlan_group_id)
        if group is None:
            raise EntityNotFoundError(f"VLANGroup {command.vlan_group_id} not found")

        group.update(
            name=command.name,
            description=command.description,
            min_vid=command.min_vid,
            max_vid=command.max_vid,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = group.collect_uncommitted_events()
        await self._event_store.append(
            group.id, new_events, expected_version=group.version - len(new_events), aggregate=group
        )
        await self._read_model_repo.upsert_from_aggregate(group)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteVLANGroupHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteVLANGroupCommand) -> None:
        group = await self._event_store.load_aggregate(VLANGroup, command.vlan_group_id)
        if group is None:
            raise EntityNotFoundError(f"VLANGroup {command.vlan_group_id} not found")

        group.delete()

        new_events = group.collect_uncommitted_events()
        await self._event_store.append(
            group.id, new_events, expected_version=group.version - len(new_events), aggregate=group
        )
        await self._read_model_repo.mark_deleted(group.id)
        await self._event_producer.publish_many("ipam.events", new_events)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class CreateServiceHandler(CommandHandler[UUID]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ServiceReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: CreateServiceCommand) -> UUID:
        svc = Service.create(
            name=command.name,
            protocol=ServiceProtocol(command.protocol),
            ports=command.ports or [],
            ip_addresses=command.ip_addresses or [],
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )
        events = svc.collect_uncommitted_events()
        await self._event_store.append(svc.id, events, expected_version=0)
        await self._read_model_repo.upsert_from_aggregate(svc)
        await self._event_producer.publish_many("ipam.events", events)
        return svc.id


class UpdateServiceHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ServiceReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: UpdateServiceCommand) -> None:
        svc = await self._event_store.load_aggregate(Service, command.service_id)
        if svc is None:
            raise EntityNotFoundError(f"Service {command.service_id} not found")

        svc.update(
            name=command.name,
            protocol=command.protocol,
            ports=command.ports or [],
            ip_addresses=command.ip_addresses or [],
            description=command.description,
            custom_fields=command.custom_fields or {},
            tags=command.tags or [],
        )

        new_events = svc.collect_uncommitted_events()
        await self._event_store.append(
            svc.id, new_events, expected_version=svc.version - len(new_events), aggregate=svc
        )
        await self._read_model_repo.upsert_from_aggregate(svc)
        await self._event_producer.publish_many("ipam.events", new_events)


class DeleteServiceHandler(CommandHandler[None]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ServiceReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: DeleteServiceCommand) -> None:
        svc = await self._event_store.load_aggregate(Service, command.service_id)
        if svc is None:
            raise EntityNotFoundError(f"Service {command.service_id} not found")

        svc.delete()

        new_events = svc.collect_uncommitted_events()
        await self._event_store.append(
            svc.id, new_events, expected_version=svc.version - len(new_events), aggregate=svc
        )
        await self._read_model_repo.mark_deleted(svc.id)
        await self._event_producer.publish_many("ipam.events", new_events)


class BulkUpdateRouteTargetsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RouteTargetReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateRouteTargetsCommand) -> int:
        all_events: list = []
        for item in command.items:
            rt = await self._event_store.load_aggregate(RouteTarget, item.route_target_id)
            if rt is None:
                raise EntityNotFoundError(f"RouteTarget {item.route_target_id} not found")
            rt.update(
                description=item.description,
                tenant_id=item.tenant_id,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = rt.collect_uncommitted_events()
            await self._event_store.append(
                rt.id, new_events, expected_version=rt.version - len(new_events), aggregate=rt
            )
            await self._read_model_repo.upsert_from_aggregate(rt)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteRouteTargetsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RouteTargetReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteRouteTargetsCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            rt = await self._event_store.load_aggregate(RouteTarget, agg_id)
            if rt is None:
                raise EntityNotFoundError(f"RouteTarget {agg_id} not found")
            rt.delete()
            new_events = rt.collect_uncommitted_events()
            await self._event_store.append(
                rt.id, new_events, expected_version=rt.version - len(new_events), aggregate=rt
            )
            await self._read_model_repo.mark_deleted(rt.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)


class BulkUpdateVLANGroupsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateVLANGroupsCommand) -> int:
        all_events: list = []
        for item in command.items:
            group = await self._event_store.load_aggregate(VLANGroup, item.vlan_group_id)
            if group is None:
                raise EntityNotFoundError(f"VLANGroup {item.vlan_group_id} not found")
            group.update(
                name=item.name,
                description=item.description,
                min_vid=item.min_vid,
                max_vid=item.max_vid,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = group.collect_uncommitted_events()
            await self._event_store.append(
                group.id, new_events, expected_version=group.version - len(new_events), aggregate=group
            )
            await self._read_model_repo.upsert_from_aggregate(group)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteVLANGroupsHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteVLANGroupsCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            group = await self._event_store.load_aggregate(VLANGroup, agg_id)
            if group is None:
                raise EntityNotFoundError(f"VLANGroup {agg_id} not found")
            group.delete()
            new_events = group.collect_uncommitted_events()
            await self._event_store.append(
                group.id, new_events, expected_version=group.version - len(new_events), aggregate=group
            )
            await self._read_model_repo.mark_deleted(group.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)


class BulkUpdateServicesHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ServiceReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkUpdateServicesCommand) -> int:
        all_events: list = []
        for item in command.items:
            svc = await self._event_store.load_aggregate(Service, item.service_id)
            if svc is None:
                raise EntityNotFoundError(f"Service {item.service_id} not found")
            svc.update(
                name=item.name,
                protocol=item.protocol,
                ports=item.ports,
                ip_addresses=item.ip_addresses,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            new_events = svc.collect_uncommitted_events()
            await self._event_store.append(
                svc.id, new_events, expected_version=svc.version - len(new_events), aggregate=svc
            )
            await self._read_model_repo.upsert_from_aggregate(svc)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.items)


class BulkDeleteServicesHandler(CommandHandler[int]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ServiceReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkDeleteServicesCommand) -> int:
        all_events: list = []
        for agg_id in command.ids:
            svc = await self._event_store.load_aggregate(Service, agg_id)
            if svc is None:
                raise EntityNotFoundError(f"Service {agg_id} not found")
            svc.delete()
            new_events = svc.collect_uncommitted_events()
            await self._event_store.append(
                svc.id, new_events, expected_version=svc.version - len(new_events), aggregate=svc
            )
            await self._read_model_repo.mark_deleted(svc.id)
            all_events.extend(new_events)
        await self._event_producer.publish_many("ipam.events", all_events)
        return len(command.ids)


# ---------------------------------------------------------------------------
# Bulk Operations (new aggregates)
# ---------------------------------------------------------------------------


class BulkCreateRouteTargetsHandler(CommandHandler[list[UUID]]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: RouteTargetReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateRouteTargetsCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            rt = RouteTarget.create(
                name=item.name,
                tenant_id=item.tenant_id,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = rt.collect_uncommitted_events()
            await self._event_store.append(rt.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(rt)
            all_events.extend(events)
            results.append(rt.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkCreateVLANGroupsHandler(CommandHandler[list[UUID]]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: VLANGroupReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateVLANGroupsCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            group = VLANGroup.create(
                name=item.name,
                slug=item.slug,
                min_vid=item.min_vid,
                max_vid=item.max_vid,
                tenant_id=item.tenant_id,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = group.collect_uncommitted_events()
            await self._event_store.append(group.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(group)
            all_events.extend(events)
            results.append(group.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


class BulkCreateServicesHandler(CommandHandler[list[UUID]]):
    def __init__(
        self,
        event_store: PostgresEventStore,
        read_model_repo: ServiceReadModelRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._event_store = event_store
        self._read_model_repo = read_model_repo
        self._event_producer = event_producer

    async def handle(self, command: BulkCreateServicesCommand) -> list[UUID]:
        results: list[UUID] = []
        all_events: list = []
        for item in command.items:
            svc = Service.create(
                name=item.name,
                protocol=ServiceProtocol(item.protocol),
                ports=item.ports,
                ip_addresses=item.ip_addresses,
                description=item.description,
                custom_fields=item.custom_fields,
                tags=item.tags,
            )
            events = svc.collect_uncommitted_events()
            await self._event_store.append(svc.id, events, expected_version=0)
            await self._read_model_repo.upsert_from_aggregate(svc)
            all_events.extend(events)
            results.append(svc.id)
        await self._event_producer.publish_many("ipam.events", all_events)
        return results


# ---------------------------------------------------------------------------
# Saved Filter
# ---------------------------------------------------------------------------


class CreateSavedFilterHandler(CommandHandler[UUID]):
    def __init__(self, repo: SavedFilterRepository) -> None:
        self._repo = repo

    async def handle(self, command: Command) -> UUID:
        if command.is_default:
            await self._repo.clear_default(command.user_id, command.entity_type)
        return await self._repo.create(
            {
                "id": uuid4(),
                "user_id": command.user_id,
                "name": command.name,
                "entity_type": command.entity_type,
                "filter_config": command.filter_config,
                "is_default": command.is_default,
            }
        )


class UpdateSavedFilterHandler(CommandHandler[None]):
    def __init__(self, repo: SavedFilterRepository) -> None:
        self._repo = repo

    async def handle(self, command: Command) -> None:
        existing = await self._repo.find_by_id(command.filter_id)
        if existing is None:
            raise EntityNotFoundError(f"SavedFilter {command.filter_id} not found")
        update_data: dict = {}
        if command.name is not None:
            update_data["name"] = command.name
        if command.filter_config is not None:
            update_data["filter_config"] = command.filter_config
        if command.is_default is not None:
            update_data["is_default"] = command.is_default
            if command.is_default:
                await self._repo.clear_default(existing["user_id"], existing["entity_type"])
        if update_data:
            await self._repo.update(command.filter_id, update_data)


class DeleteSavedFilterHandler(CommandHandler[None]):
    def __init__(self, repo: SavedFilterRepository) -> None:
        self._repo = repo

    async def handle(self, command: Command) -> None:
        existing = await self._repo.find_by_id(command.filter_id)
        if existing is None:
            raise EntityNotFoundError(f"SavedFilter {command.filter_id} not found")
        await self._repo.delete(command.filter_id)
