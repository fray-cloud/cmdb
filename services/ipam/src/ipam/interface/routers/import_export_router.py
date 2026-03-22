"""Import/Export router — CSV import, CSV/JSON/YAML export, Jinja2 template rendering."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse

from ipam.application.command_handlers import (
    BulkCreateASNsHandler,
    BulkCreateFHRPGroupsHandler,
    BulkCreateIPAddressesHandler,
    BulkCreateIPRangesHandler,
    BulkCreatePrefixesHandler,
    BulkCreateRIRsHandler,
    BulkCreateRouteTargetsHandler,
    BulkCreateServicesHandler,
    BulkCreateVLANGroupsHandler,
    BulkCreateVLANsHandler,
    BulkCreateVRFsHandler,
)
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
)
from ipam.application.export_service import export_csv, export_json, export_yaml
from ipam.application.import_service import VALID_ENTITY_TYPES, parse_csv
from ipam.application.queries import (
    ListASNsQuery,
    ListFHRPGroupsQuery,
    ListIPAddressesQuery,
    ListIPRangesQuery,
    ListPrefixesQuery,
    ListRIRsQuery,
    ListRouteTargetsQuery,
    ListServicesQuery,
    ListVLANGroupsQuery,
    ListVLANsQuery,
    ListVRFsQuery,
)
from ipam.application.query_handlers import (
    ListASNsHandler,
    ListFHRPGroupsHandler,
    ListIPAddressesHandler,
    ListIPRangesHandler,
    ListPrefixesHandler,
    ListRIRsHandler,
    ListRouteTargetsHandler,
    ListServicesHandler,
    ListVLANGroupsHandler,
    ListVLANsHandler,
    ListVRFsHandler,
)
from ipam.infrastructure.read_model_repository import (
    PostgresASNReadModelRepository,
    PostgresFHRPGroupReadModelRepository,
    PostgresIPAddressReadModelRepository,
    PostgresIPRangeReadModelRepository,
    PostgresPrefixReadModelRepository,
    PostgresRIRReadModelRepository,
    PostgresRouteTargetReadModelRepository,
    PostgresServiceReadModelRepository,
    PostgresVLANGroupReadModelRepository,
    PostgresVLANReadModelRepository,
    PostgresVRFReadModelRepository,
)
from ipam.interface.schemas import ImportResponse, ImportRowErrorSchema
from shared.cqrs.bus import CommandBus, QueryBus

router = APIRouter(tags=["import-export"])

# Mapping entity_type -> (BulkCreateCommand, CreateCommand, BulkCreateHandler, ReadModelRepo)
_BULK_CREATE_MAP: dict[str, tuple] = {
    "prefix": (
        BulkCreatePrefixesCommand,
        CreatePrefixCommand,
        BulkCreatePrefixesHandler,
        PostgresPrefixReadModelRepository,
    ),
    "ip_address": (
        BulkCreateIPAddressesCommand,
        CreateIPAddressCommand,
        BulkCreateIPAddressesHandler,
        PostgresIPAddressReadModelRepository,
    ),
    "vrf": (
        BulkCreateVRFsCommand,
        CreateVRFCommand,
        BulkCreateVRFsHandler,
        PostgresVRFReadModelRepository,
    ),
    "vlan": (
        BulkCreateVLANsCommand,
        CreateVLANCommand,
        BulkCreateVLANsHandler,
        PostgresVLANReadModelRepository,
    ),
    "ip_range": (
        BulkCreateIPRangesCommand,
        CreateIPRangeCommand,
        BulkCreateIPRangesHandler,
        PostgresIPRangeReadModelRepository,
    ),
    "rir": (
        BulkCreateRIRsCommand,
        CreateRIRCommand,
        BulkCreateRIRsHandler,
        PostgresRIRReadModelRepository,
    ),
    "asn": (
        BulkCreateASNsCommand,
        CreateASNCommand,
        BulkCreateASNsHandler,
        PostgresASNReadModelRepository,
    ),
    "fhrp_group": (
        BulkCreateFHRPGroupsCommand,
        CreateFHRPGroupCommand,
        BulkCreateFHRPGroupsHandler,
        PostgresFHRPGroupReadModelRepository,
    ),
    "route_target": (
        BulkCreateRouteTargetsCommand,
        CreateRouteTargetCommand,
        BulkCreateRouteTargetsHandler,
        PostgresRouteTargetReadModelRepository,
    ),
    "vlan_group": (
        BulkCreateVLANGroupsCommand,
        CreateVLANGroupCommand,
        BulkCreateVLANGroupsHandler,
        PostgresVLANGroupReadModelRepository,
    ),
    "service": (
        BulkCreateServicesCommand,
        CreateServiceCommand,
        BulkCreateServicesHandler,
        PostgresServiceReadModelRepository,
    ),
}

# Mapping entity_type -> (ListQuery, ListHandler, ReadModelRepo)
_LIST_QUERY_MAP = {
    "prefix": (ListPrefixesQuery, ListPrefixesHandler, PostgresPrefixReadModelRepository),
    "ip_address": (ListIPAddressesQuery, ListIPAddressesHandler, PostgresIPAddressReadModelRepository),
    "vrf": (ListVRFsQuery, ListVRFsHandler, PostgresVRFReadModelRepository),
    "vlan": (ListVLANsQuery, ListVLANsHandler, PostgresVLANReadModelRepository),
    "ip_range": (ListIPRangesQuery, ListIPRangesHandler, PostgresIPRangeReadModelRepository),
    "rir": (ListRIRsQuery, ListRIRsHandler, PostgresRIRReadModelRepository),
    "asn": (ListASNsQuery, ListASNsHandler, PostgresASNReadModelRepository),
    "fhrp_group": (ListFHRPGroupsQuery, ListFHRPGroupsHandler, PostgresFHRPGroupReadModelRepository),
    "route_target": (ListRouteTargetsQuery, ListRouteTargetsHandler, PostgresRouteTargetReadModelRepository),
    "vlan_group": (ListVLANGroupsQuery, ListVLANGroupsHandler, PostgresVLANGroupReadModelRepository),
    "service": (ListServicesQuery, ListServicesHandler, PostgresServiceReadModelRepository),
}

_FORMAT_CONTENT_TYPES = {
    "csv": "text/csv",
    "json": "application/json",
    "yaml": "application/x-yaml",
}

_FORMAT_EXPORTERS = {
    "csv": export_csv,
    "json": export_json,
    "yaml": export_yaml,
}


def _validate_entity_type(entity_type: str) -> None:
    if entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity_type '{entity_type}'. Valid types: {sorted(VALID_ENTITY_TYPES)}",
        )


# =============================================================================
# CSV Import
# =============================================================================


@router.post("/import/{entity_type}", response_model=ImportResponse, status_code=status.HTTP_200_OK)
async def import_csv(
    entity_type: str,
    file: UploadFile,
    request: Request,
) -> ImportResponse:
    _validate_entity_type(entity_type)

    content = (await file.read()).decode("utf-8-sig")
    items, parse_errors = parse_csv(content)
    schema_errors = [ImportRowErrorSchema(row=e.row, field=e.field, error=e.error) for e in parse_errors]

    if not items:
        return ImportResponse(imported=0, failed=len(schema_errors), errors=schema_errors)

    bulk_cmd_cls, create_cmd_cls, handler_cls, repo_cls = _BULK_CREATE_MAP[entity_type]

    session = request.app.state.database.session()
    repo = repo_cls(session)
    event_store = request.app.state.event_store
    event_producer = request.app.state.event_producer

    bus = CommandBus()
    bus.register(bulk_cmd_cls, handler_cls(event_store, repo, event_producer))

    create_commands = []
    import_errors = list(schema_errors)
    for i, item in enumerate(items):
        try:
            cmd = create_cmd_cls(**item)
            create_commands.append(cmd)
        except Exception as e:
            import_errors.append(ImportRowErrorSchema(row=i + 2, field="", error=str(e)))

    if not create_commands:
        return ImportResponse(imported=0, failed=len(import_errors), errors=import_errors)

    try:
        result_ids = await bus.dispatch(bulk_cmd_cls(items=create_commands))
        return ImportResponse(imported=len(result_ids), failed=len(import_errors), errors=import_errors)
    except Exception as e:
        import_errors.append(ImportRowErrorSchema(row=0, field="", error=f"Bulk create failed: {e}"))
        return ImportResponse(imported=0, failed=len(import_errors), errors=import_errors)


# =============================================================================
# Export
# =============================================================================


@router.get("/export/{entity_type}")
async def export_data(
    entity_type: str,
    request: Request,
    export_format: Literal["csv", "json", "yaml"] = "csv",
    limit: int = 10000,
) -> StreamingResponse:
    _validate_entity_type(entity_type)

    if limit > 10000:
        limit = 10000

    query_cls, handler_cls, repo_cls = _LIST_QUERY_MAP[entity_type]

    session = request.app.state.database.session()
    repo = repo_cls(session)

    bus = QueryBus()
    bus.register(query_cls, handler_cls(repo))

    query = query_cls(offset=0, limit=limit)
    items, _total = await bus.dispatch(query)

    item_dicts = [item.model_dump() for item in items]
    exporter = _FORMAT_EXPORTERS[export_format]
    output = exporter(item_dicts)

    content_type = _FORMAT_CONTENT_TYPES[export_format]
    filename = f"{entity_type}_export.{export_format}"

    return StreamingResponse(
        iter([output]),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# =============================================================================
# Jinja2 Template Rendering
# =============================================================================


@router.post("/export/{entity_type}/render")
async def render_template(
    entity_type: str,
    request: Request,
    template_id: UUID | None = None,
    limit: int = 10000,
) -> StreamingResponse:
    _validate_entity_type(entity_type)

    if template_id is None:
        raise HTTPException(status_code=400, detail="template_id is required")

    if limit > 10000:
        limit = 10000

    from ipam.infrastructure.template_repository import TemplateRepository

    session = request.app.state.database.session()
    template_repo = TemplateRepository(session)
    template = await template_repo.find_by_id(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail=f"ExportTemplate {template_id} not found")

    query_cls, handler_cls, repo_cls = _LIST_QUERY_MAP[entity_type]
    repo = repo_cls(session)
    bus = QueryBus()
    bus.register(query_cls, handler_cls(repo))

    query = query_cls(offset=0, limit=limit)
    items, total = await bus.dispatch(query)
    item_dicts = [item.model_dump() for item in items]

    from jinja2.sandbox import SandboxedEnvironment

    env = SandboxedEnvironment()
    jinja_template = env.from_string(template.template_content)
    rendered = jinja_template.render(items=item_dicts, total=total, entity_type=entity_type)

    content_type_map = {
        "csv": "text/csv",
        "json": "application/json",
        "yaml": "application/x-yaml",
        "html": "text/html",
        "xml": "application/xml",
        "text": "text/plain",
    }
    content_type = content_type_map.get(template.output_format, "text/plain")
    filename = f"{entity_type}_export.{template.output_format}"

    return StreamingResponse(
        iter([rendered]),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# =============================================================================
# Export Templates CRUD
# =============================================================================


@router.post("/export-templates", status_code=status.HTTP_201_CREATED)
async def create_export_template(
    request: Request,
    body: dict,
) -> dict:
    from uuid import uuid4

    from ipam.infrastructure.template_repository import TemplateRepository

    session = request.app.state.database.session()
    repo = TemplateRepository(session)
    template = await repo.create(
        {
            "id": uuid4(),
            "name": body["name"],
            "entity_type": body["entity_type"],
            "template_content": body["template_content"],
            "output_format": body.get("output_format", "text"),
            "description": body.get("description", ""),
        }
    )
    return {
        "id": str(template.id),
        "name": template.name,
        "entity_type": template.entity_type,
        "output_format": template.output_format,
        "description": template.description,
        "created_at": template.created_at.isoformat() if template.created_at else None,
    }


@router.get("/export-templates")
async def list_export_templates(
    request: Request,
    entity_type: str | None = None,
) -> list[dict]:
    from ipam.infrastructure.template_repository import TemplateRepository

    session = request.app.state.database.session()
    repo = TemplateRepository(session)
    templates = await repo.find_all(entity_type=entity_type)
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "entity_type": t.entity_type,
            "output_format": t.output_format,
            "description": t.description,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in templates
    ]


@router.get("/export-templates/{template_id}")
async def get_export_template(
    template_id: UUID,
    request: Request,
) -> dict:
    from ipam.infrastructure.template_repository import TemplateRepository

    session = request.app.state.database.session()
    repo = TemplateRepository(session)
    template = await repo.find_by_id(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail=f"ExportTemplate {template_id} not found")
    return {
        "id": str(template.id),
        "name": template.name,
        "entity_type": template.entity_type,
        "template_content": template.template_content,
        "output_format": template.output_format,
        "description": template.description,
        "created_at": template.created_at.isoformat() if template.created_at else None,
    }


@router.delete("/export-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_export_template(
    template_id: UUID,
    request: Request,
) -> None:
    from ipam.infrastructure.template_repository import TemplateRepository

    session = request.app.state.database.session()
    repo = TemplateRepository(session)
    template = await repo.find_by_id(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail=f"ExportTemplate {template_id} not found")
    await repo.delete(template_id)
