"""SQL controlled write handler readiness for phase 0251.

This module derives a minimal Scheduler-controlled SQL write handler frame from
the typed intention/event envelope surface introduced in phase 0250.

It remains dry-run/readiness only: no PostgreSQL connection is opened, no SQL is
executed, no EventBus is created, and no handler is dispatched by Scheduler.run.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from context.prod_server_postgresql_schema_readiness_0245 import (
    build_postgresql_schema_readiness,
)
from context.prod_server_scheduler_intention_event_emission_0250 import (
    EventEnvelope,
    TypedSchedulerIntention,
    event_envelope_from_intention,
    sample_scheduler_intention,
)


SQL_CONTROLLED_WRITE_HANDLER_READINESS_VERSION = "0251.r1"


SQL_CONTROLLED_WRITE_HANDLER_READINESS_BOUNDARY: dict[str, bool] = {
    "readiness_only": True,
    "uses_scheduler_intention_event_emission": True,
    "uses_postgresql_schema_readiness": True,
    "connects_postgresql": False,
    "executes_sql": False,
    "writes_postgresql": False,
    "creates_eventbus": False,
    "publishes_events": False,
    "calls_scheduler_run": False,
    "dispatches_handler": False,
    "runs_openvino_inference": False,
    "writes_qdrant": False,
    "calls_github_api": False,
    "requires_non_stdlib": False,
}


@dataclass(frozen=True)
class SQLControlledWriteIssue:
    """One issue found while preparing the controlled SQL write handler frame."""

    field: str
    message: str


@dataclass(frozen=True)
class SQLControlledWriteRequest:
    """Dry-run SQL controlled write request derived from a Scheduler intention."""

    request_id: str
    handler_id: str
    intent_id: str
    table: str
    operation: str
    primary_key_field: str
    sql_ref: str
    content_hash: str
    payload_kind: str
    payload_source: str
    idempotency_key: str
    preview_sql: str


@dataclass(frozen=True)
class SQLControlledWriteHandlerFrame:
    """Minimal handler frame connecting intention, envelope, and SQL request."""

    frame_id: str
    intention: TypedSchedulerIntention
    observed_event: EventEnvelope
    write_request: SQLControlledWriteRequest
    result_event_type: str


@dataclass(frozen=True)
class SQLControlledWriteHandlerReadinessReport:
    """JSON-compatible SQL controlled write handler readiness report."""

    version: str
    server_config_path: str
    openvino_config_path: str
    ready: bool
    handler_frame: SQLControlledWriteHandlerFrame | None
    issues: tuple[SQLControlledWriteIssue, ...]


def _context_records_primary_key(server_config_path: Path) -> tuple[str, tuple[SQLControlledWriteIssue, ...]]:
    schema = build_postgresql_schema_readiness(server_config_path)
    issues: list[SQLControlledWriteIssue] = []
    if not schema.ready:
        for issue in schema.issues:
            issues.append(SQLControlledWriteIssue(issue.field, issue.message))
    for table in schema.tables:
        if table.table == "context_records":
            return table.primary_key, tuple(issues)
    return "", tuple(issues + [SQLControlledWriteIssue("context_records", "context_records table is required")])


def _preview_insert_sql(table: str, primary_key: str) -> str:
    return (
        f"INSERT INTO {table} ({primary_key}, kind, payload_json, content_hash, created_at) "
        "VALUES (:id, :kind, :payload_json, :content_hash, now()) "
        f"ON CONFLICT ({primary_key}) DO NOTHING;"
    )


def build_sql_controlled_write_handler_readiness(
    *,
    server_config_path: Path,
    openvino_config_path: Path,
    intention: TypedSchedulerIntention | None = None,
) -> SQLControlledWriteHandlerReadinessReport:
    """Build a dry-run SQL controlled write handler frame."""

    selected_intention = intention if intention is not None else sample_scheduler_intention()
    event_report = event_envelope_from_intention(
        selected_intention,
        server_config_path=server_config_path,
        openvino_config_path=openvino_config_path,
    )
    issues: list[SQLControlledWriteIssue] = []

    if not event_report.valid:
        for issue in event_report.issues:
            issues.append(SQLControlledWriteIssue(issue.field, issue.message))
    if event_report.envelope is None:
        issues.append(SQLControlledWriteIssue("event_envelope", "event envelope is required"))

    primary_key, schema_issues = _context_records_primary_key(server_config_path)
    issues.extend(schema_issues)

    if not selected_intention.sql_ref:
        issues.append(SQLControlledWriteIssue("sql_ref", "sql_ref is required for controlled write"))
    if not selected_intention.payload_hash:
        issues.append(SQLControlledWriteIssue("payload_hash", "payload_hash is required for controlled write"))

    if issues or event_report.envelope is None or not primary_key:
        return SQLControlledWriteHandlerReadinessReport(
            version=SQL_CONTROLLED_WRITE_HANDLER_READINESS_VERSION,
            server_config_path=str(server_config_path),
            openvino_config_path=str(openvino_config_path),
            ready=False,
            handler_frame=None,
            issues=tuple(issues),
        )

    write_request = SQLControlledWriteRequest(
        request_id="sql-write:" + selected_intention.intent_id,
        handler_id="handler.sql_context_store.controlled_write",
        intent_id=selected_intention.intent_id,
        table="context_records",
        operation="insert_if_absent",
        primary_key_field=primary_key,
        sql_ref=selected_intention.sql_ref,
        content_hash=selected_intention.payload_hash,
        payload_kind="scheduler_intention_projection_seed",
        payload_source="scheduler_intention_event_envelope",
        idempotency_key=selected_intention.payload_hash,
        preview_sql=_preview_insert_sql("context_records", primary_key),
    )
    frame = SQLControlledWriteHandlerFrame(
        frame_id="handler-frame:" + selected_intention.intent_id,
        intention=event_report.intention,
        observed_event=event_report.envelope,
        write_request=write_request,
        result_event_type="sql.controlled_write.prepared",
    )

    return SQLControlledWriteHandlerReadinessReport(
        version=SQL_CONTROLLED_WRITE_HANDLER_READINESS_VERSION,
        server_config_path=str(server_config_path),
        openvino_config_path=str(openvino_config_path),
        ready=True,
        handler_frame=frame,
        issues=tuple(),
    )


def sql_controlled_write_handler_readiness_to_dict(report: SQLControlledWriteHandlerReadinessReport) -> dict[str, Any]:
    """Convert a handler readiness report to JSON-compatible data."""

    return asdict(report)


def write_sql_controlled_write_handler_readiness_report(*, server_config_path: Path, openvino_config_path: Path, output_path: Path) -> dict[str, Any]:
    """Build and write the SQL controlled write handler readiness report."""

    report = build_sql_controlled_write_handler_readiness(
        server_config_path=server_config_path,
        openvino_config_path=openvino_config_path,
    )
    payload = {
        "production_server_sql_controlled_write_handler_readiness_written": True,
        "sql_controlled_write_handler_readiness": sql_controlled_write_handler_readiness_to_dict(report),
        "boundary": dict(SQL_CONTROLLED_WRITE_HANDLER_READINESS_BOUNDARY),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + chr(10), encoding="utf-8")
    return payload
