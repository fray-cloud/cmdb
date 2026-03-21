from __future__ import annotations

from uuid import UUID

from ipam.application.commands import (
    BulkCreateASNsCommand,
    BulkCreateFHRPGroupsCommand,
    BulkCreateIPAddressesCommand,
    BulkCreateIPRangesCommand,
    BulkCreatePrefixesCommand,
    BulkCreateRIRsCommand,
    BulkCreateVLANsCommand,
    BulkCreateVRFsCommand,
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
    CreateVLANCommand,
    CreateVRFCommand,
    DeleteASNCommand,
    DeleteFHRPGroupCommand,
    DeleteIPAddressCommand,
    DeleteIPRangeCommand,
    DeletePrefixCommand,
    DeleteRIRCommand,
    DeleteVLANCommand,
    DeleteVRFCommand,
    UpdateASNCommand,
    UpdateFHRPGroupCommand,
    UpdateIPAddressCommand,
    UpdateIPRangeCommand,
    UpdatePrefixCommand,
    UpdateRIRCommand,
    UpdateVLANCommand,
    UpdateVRFCommand,
)
from ipam.application.read_model import (
    ASNReadModelRepository,
    FHRPGroupReadModelRepository,
    IPAddressReadModelRepository,
    IPRangeReadModelRepository,
    PrefixReadModelRepository,
    RIRReadModelRepository,
    VLANReadModelRepository,
    VRFReadModelRepository,
)
from ipam.domain.asn import ASN
from ipam.domain.fhrp_group import FHRPGroup
from ipam.domain.ip_address import IPAddress
from ipam.domain.ip_range import IPRange
from ipam.domain.prefix import Prefix
from ipam.domain.rir import RIR
from ipam.domain.value_objects import (
    FHRPAuthType,
    FHRPProtocol,
    IPAddressStatus,
    IPRangeStatus,
    PrefixStatus,
    VLANStatus,
)
from ipam.domain.vlan import VLAN
from ipam.domain.vrf import VRF
from shared.cqrs.command import CommandHandler
from shared.domain.exceptions import ConflictError, EntityNotFoundError
from shared.event.pg_store import PostgresEventStore
from shared.messaging.producer import KafkaEventProducer

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
            custom_fields=command.custom_fields,
            tags=command.tags,
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
            custom_fields=command.custom_fields,
            tags=command.tags,
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
            custom_fields=command.custom_fields,
            tags=command.tags,
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
            custom_fields=command.custom_fields,
            tags=command.tags,
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
            tenant_id=command.tenant_id,
            description=command.description,
            custom_fields=command.custom_fields,
            tags=command.tags,
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
            description=command.description,
            custom_fields=command.custom_fields,
            tags=command.tags,
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
            custom_fields=command.custom_fields,
            tags=command.tags,
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
            custom_fields=command.custom_fields,
            tags=command.tags,
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
            custom_fields=command.custom_fields,
            tags=command.tags,
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
            custom_fields=command.custom_fields,
            tags=command.tags,
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
            custom_fields=command.custom_fields,
            tags=command.tags,
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
            custom_fields=command.custom_fields,
            tags=command.tags,
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
            custom_fields=command.custom_fields,
            tags=command.tags,
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
            custom_fields=command.custom_fields,
            tags=command.tags,
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
            custom_fields=command.custom_fields,
            tags=command.tags,
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
            custom_fields=command.custom_fields,
            tags=command.tags,
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
