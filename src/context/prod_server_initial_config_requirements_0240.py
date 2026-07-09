"""Initial production server configuration requirements for phase 0240.

This module describes what a production Autodoc server must have configured
before later phases activate the runtime. It intentionally does not start
OpenRC, instantiate Scheduler/EventBus, create PostgreSQL tables, create Qdrant
collections, call GitHub, or publish EventBus traffic.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


INITIAL_CONFIGURATION_VERSION = "0240.r2"


INITIAL_CONFIGURATION_BOUNDARY: dict[str, bool] = {
    "requirements_only": True,
    "single_production_server_target": True,
    "starts_openrc": False,
    "creates_scheduler": False,
    "creates_eventbus": False,
    "starts_threads_in_init": False,
    "writes_postgresql": False,
    "writes_qdrant": False,
    "calls_github_api": False,
    "publishes_github": False,
    "publishes_events": False,
    "supervision_is_authority": False,
    "requires_non_stdlib": False,
}


@dataclass(frozen=True)
class ComponentRequirement:
    """Component entry expected in the production server INI file."""

    component_id: str
    factory: str
    phase: str
    enabled: bool
    depends_on: tuple[str, ...] = ()
    command_path: bool = False
    observation_path: bool = False


@dataclass(frozen=True)
class EventAttributeRequirement:
    """Allowlisted object attribute that may be copied to an EventBus envelope."""

    name: str
    kind: str
    required: bool = False
    redact: bool = False
    description: str = ""


@dataclass(frozen=True)
class PostgreSQLTableRequirement:
    """Required table shape for the production PostgreSQL authority store."""

    table: str
    primary_key: str
    columns: tuple[str, ...]
    jsonb_columns: tuple[str, ...] = ()
    required_indexes: tuple[str, ...] = ()


@dataclass(frozen=True)
class QdrantCollectionRequirement:
    """Required Qdrant collection shape for vector projection and recall."""

    collection: str
    vector_dimension: int
    distance: str
    normalized_vectors: bool
    required_payload: tuple[str, ...]
    optional_payload: tuple[str, ...] = ()


@dataclass(frozen=True)
class OpenRCLauncherRequirement:
    """OpenRC service requirements for the production launcher."""

    service_name: str
    command: str
    configtest: str
    description: str
    dependencies: tuple[str, ...]
    starts_individual_components: bool = False


@dataclass(frozen=True)
class GitHubIntegrationRequirement:
    """GitHub artifact-exchange requirements for the production server."""

    enabled: bool
    mode: str
    token_env: str
    repository_allowlist_required: bool
    scan_once_entrypoint: str
    scheduler_authority_required: bool
    project_push_frame_required: bool
    copilot_advisory_only: bool
    publication_review_required: bool
    publish_enabled_by_default: bool
    sql_write_during_scan: bool
    qdrant_write_during_scan: bool
    required_ini_sections: tuple[str, ...]
    required_artifact_fields: tuple[str, ...]


@dataclass(frozen=True)
class ProductionServerInitialConfiguration:
    """Complete initial configuration requirements for one production server."""

    version: str
    target: str
    boundary: dict[str, bool]
    phases: tuple[str, ...]
    component_requirements: tuple[ComponentRequirement, ...]
    event_attribute_requirements: tuple[EventAttributeRequirement, ...]
    postgresql_table_requirements: tuple[PostgreSQLTableRequirement, ...]
    qdrant_collection_requirements: tuple[QdrantCollectionRequirement, ...]
    openrc_launcher: OpenRCLauncherRequirement
    github_integration: GitHubIntegrationRequirement
    ini_sections: tuple[str, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)


PHASES: tuple[str, ...] = (
    "D00_repository_rule_gate",
    "D01_initial_server_configuration",
    "D02_scheduler_eventbus_bootstrap",
    "D03_runtime_dataplane_surfaces",
    "D04_sql_durable_authority",
    "D05_qdrant_projection_recall",
    "D06_source_artifact_ingestion",
    "D07_functional_handler_chain",
    "D08_passive_observability",
    "D09_github_artifact_exchange",
    "D10_full_server_acceptance",
)


COMPONENT_REQUIREMENTS: tuple[ComponentRequirement, ...] = (
    ComponentRequirement(
        component_id="scheduler",
        factory="autodoc.scheduler:create_scheduler",
        phase="D02_scheduler_eventbus_bootstrap",
        enabled=True,
        command_path=True,
    ),
    ComponentRequirement(
        component_id="eventbus",
        factory="autodoc.eventbus:create_eventbus",
        phase="D02_scheduler_eventbus_bootstrap",
        enabled=True,
        observation_path=True,
    ),
    ComponentRequirement(
        component_id="sql_context_store",
        factory="autodoc.sql:create_context_store",
        phase="D04_sql_durable_authority",
        enabled=True,
        depends_on=("scheduler",),
        command_path=True,
    ),
    ComponentRequirement(
        component_id="qdrant_projection",
        factory="autodoc.qdrant:create_projection_client",
        phase="D05_qdrant_projection_recall",
        enabled=True,
        depends_on=("sql_context_store",),
        command_path=True,
    ),
    ComponentRequirement(
        component_id="github_artifact_exchange",
        factory="autodoc.github:create_artifact_exchange",
        phase="D09_github_artifact_exchange",
        enabled=True,
        depends_on=("scheduler", "sql_context_store"),
        command_path=True,
    ),
    ComponentRequirement(
        component_id="passive_supervisor_sink",
        factory="autodoc.supervision:create_passive_supervisor_sink",
        phase="D08_passive_observability",
        enabled=True,
        depends_on=("eventbus",),
        observation_path=True,
    ),
)


EVENT_ATTRIBUTE_REQUIREMENTS: tuple[EventAttributeRequirement, ...] = (
    EventAttributeRequirement("schema_version", "str", required=True, description="Envelope schema."),
    EventAttributeRequirement("event_type", "str", required=True, description="Stable event name."),
    EventAttributeRequirement("trace_id", "str", required=True, description="End-to-end trace id."),
    EventAttributeRequirement("component", "str", required=True, description="Emitter component id."),
    EventAttributeRequirement("phase", "str", required=True, description="Deployment/runtime phase."),
    EventAttributeRequirement("intent_id", "str", description="Typed command/intention id."),
    EventAttributeRequirement("result_id", "str", description="Immutable result frame id."),
    EventAttributeRequirement("sql_ref", "str", description="Durable SQL reference."),
    EventAttributeRequirement("qdrant_ref", "str", description="Projection reference."),
    EventAttributeRequirement("github_ref", "str", description="GitHub artifact/project item reference."),
    EventAttributeRequirement("project_push_frame_ref", "str", description="Imported GitHub exchange frame."),
    EventAttributeRequirement("payload_hash", "str", description="Content-addressed payload hash."),
    EventAttributeRequirement("priority", "int", description="Scheduler priority snapshot."),
    EventAttributeRequirement("secret", "str", redact=True, description="Must be redacted if present."),
)


POSTGRESQL_TABLE_REQUIREMENTS: tuple[PostgreSQLTableRequirement, ...] = (
    PostgreSQLTableRequirement(
        table="context_records",
        primary_key="id",
        columns=("id", "kind", "payload_json", "content_hash", "created_at"),
        jsonb_columns=("payload_json",),
        required_indexes=("content_hash", "kind"),
    ),
    PostgreSQLTableRequirement(
        table="event_journal",
        primary_key="id",
        columns=("id", "trace_id", "event_type", "event_json", "created_at"),
        jsonb_columns=("event_json",),
        required_indexes=("trace_id", "event_type"),
    ),
    PostgreSQLTableRequirement(
        table="result_frames",
        primary_key="id",
        columns=("id", "intent_id", "result_json", "created_at"),
        jsonb_columns=("result_json",),
        required_indexes=("intent_id",),
    ),
    PostgreSQLTableRequirement(
        table="github_project_push_frames",
        primary_key="id",
        columns=("id", "github_ref", "frame_json", "publication_review_required", "created_at"),
        jsonb_columns=("frame_json",),
        required_indexes=("github_ref",),
    ),
)


QDRANT_COLLECTION_REQUIREMENTS: tuple[QdrantCollectionRequirement, ...] = (
    QdrantCollectionRequirement(
        collection="autodoc_context_e5_small",
        vector_dimension=384,
        distance="cosine",
        normalized_vectors=True,
        required_payload=("sql_ref", "model_id", "embedding_version", "content_hash"),
        optional_payload=("source_ref", "artifact_ref", "github_ref", "text_kind", "created_at"),
    ),
)


OPENRC_LAUNCHER = OpenRCLauncherRequirement(
    service_name="autodoc",
    command="/usr/bin/python -m autodoc.launcher --config /etc/autodoc/autodoc.ini",
    configtest="/usr/bin/python -m autodoc.launcher --config /etc/autodoc/autodoc.ini --configtest",
    description="Autodoc production launcher; Scheduler remains runtime authority.",
    dependencies=("postgresql", "qdrant"),
)


GITHUB_INTEGRATION = GitHubIntegrationRequirement(
    enabled=True,
    mode="artifact_exchange",
    token_env="GITHUB_TOKEN",
    repository_allowlist_required=True,
    scan_once_entrypoint="/usr/bin/python -m autodoc.github.scan_once --config /etc/autodoc/autodoc.ini",
    scheduler_authority_required=True,
    project_push_frame_required=True,
    copilot_advisory_only=True,
    publication_review_required=True,
    publish_enabled_by_default=False,
    sql_write_during_scan=False,
    qdrant_write_during_scan=False,
    required_ini_sections=(
        "github",
        "github.repositories",
        "github.artifacts",
        "github.publication",
    ),
    required_artifact_fields=(
        "ticket_ref",
        "project_item_ref",
        "artifact_ref",
        "source_repository",
        "project_push_frame_ref",
        "publication_review_required",
    ),
)


INI_SECTIONS: tuple[str, ...] = (
    "server",
    "openrc",
    "component.scheduler",
    "component.eventbus",
    "component.sql_context_store",
    "component.qdrant_projection",
    "component.github_artifact_exchange",
    "component.passive_supervisor_sink",
    "postgresql.connection",
    "postgresql.table.context_records",
    "postgresql.table.event_journal",
    "postgresql.table.result_frames",
    "postgresql.table.github_project_push_frames",
    "qdrant.connection",
    "qdrant.collection.autodoc_context_e5_small",
    "github",
    "github.repositories",
    "github.artifacts",
    "github.publication",
    "eventbus.attributes",
)


NOTES: tuple[str, ...] = (
    "OpenRC starts the launcher, not individual Python components.",
    "Scheduler remains the orchestration authority.",
    "EventBus transports observations; it is not the command path.",
    "PostgreSQL is the durable authority before Qdrant projection.",
    "Qdrant payloads must carry sql_ref for SQL rehydration.",
    "GitHub is an artifact exchange surface until reviewed publication is enabled.",
    "Copilot preliminary output is advisory only.",
    "Advanced EventBus attributes are allowlisted and may be redacted.",
)


def production_server_initial_configuration() -> ProductionServerInitialConfiguration:
    """Return the canonical phase 0240 production server configuration requirements."""

    return ProductionServerInitialConfiguration(
        version=INITIAL_CONFIGURATION_VERSION,
        target="production_server",
        boundary=dict(INITIAL_CONFIGURATION_BOUNDARY),
        phases=PHASES,
        component_requirements=COMPONENT_REQUIREMENTS,
        event_attribute_requirements=EVENT_ATTRIBUTE_REQUIREMENTS,
        postgresql_table_requirements=POSTGRESQL_TABLE_REQUIREMENTS,
        qdrant_collection_requirements=QDRANT_COLLECTION_REQUIREMENTS,
        openrc_launcher=OPENRC_LAUNCHER,
        github_integration=GITHUB_INTEGRATION,
        ini_sections=INI_SECTIONS,
        notes=NOTES,
    )


def configuration_to_dict(config: ProductionServerInitialConfiguration | None = None) -> dict[str, Any]:
    """Convert the production server configuration requirements to JSON data."""

    selected = config if config is not None else production_server_initial_configuration()
    return asdict(selected)


def validate_production_server_initial_configuration(
    config: ProductionServerInitialConfiguration | None = None,
) -> list[str]:
    """Return validation errors for the initial production server requirements."""

    selected = config if config is not None else production_server_initial_configuration()
    errors: list[str] = []

    if not selected.boundary.get("requirements_only"):
        errors.append("initial configuration must be requirements-only")
    forbidden_true = (
        "starts_openrc",
        "creates_scheduler",
        "creates_eventbus",
        "starts_threads_in_init",
        "writes_postgresql",
        "writes_qdrant",
        "calls_github_api",
        "publishes_github",
        "publishes_events",
        "supervision_is_authority",
        "requires_non_stdlib",
    )
    for key in forbidden_true:
        if selected.boundary.get(key):
            errors.append(f"boundary must keep {key}=False")

    component_ids = {entry.component_id for entry in selected.component_requirements}
    for required_component in ("scheduler", "eventbus", "sql_context_store", "qdrant_projection", "github_artifact_exchange"):
        if required_component not in component_ids:
            errors.append(f"missing component requirement {required_component}")

    for entry in selected.component_requirements:
        if ":" not in entry.factory:
            errors.append(f"factory must use module:function syntax: {entry.component_id}")
        for dependency in entry.depends_on:
            if dependency not in component_ids:
                errors.append(f"unknown dependency {dependency} for {entry.component_id}")

    event_names = {entry.name for entry in selected.event_attribute_requirements}
    for required_name in ("schema_version", "event_type", "trace_id", "component", "phase"):
        if required_name not in event_names:
            errors.append(f"missing event attribute {required_name}")

    for collection in selected.qdrant_collection_requirements:
        if collection.vector_dimension <= 0:
            errors.append(f"invalid vector dimension for {collection.collection}")
        if collection.distance != "cosine":
            errors.append(f"unexpected distance for {collection.collection}")
        if "sql_ref" not in collection.required_payload:
            errors.append(f"qdrant collection {collection.collection} must require sql_ref")

    github = selected.github_integration
    if github.token_env != "GITHUB_TOKEN":
        errors.append("GitHub token must be read from GITHUB_TOKEN")
    if not github.repository_allowlist_required:
        errors.append("GitHub repository allowlist is required")
    if github.publish_enabled_by_default:
        errors.append("GitHub publication must be disabled by default")
    if not github.publication_review_required:
        errors.append("GitHub publication review is required")
    if github.sql_write_during_scan or github.qdrant_write_during_scan:
        errors.append("GitHub scan-once must not write SQL or Qdrant")

    return errors


def write_production_server_initial_configuration(path: Path) -> dict[str, Any]:
    """Validate and write the phase 0240 production server configuration requirements."""

    config = production_server_initial_configuration()
    errors = validate_production_server_initial_configuration(config)
    payload = {
        "production_server_initial_configuration_written": not errors,
        "validation_errors": errors,
        "configuration": configuration_to_dict(config),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
