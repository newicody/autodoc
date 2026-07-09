"""Recall to SQL rehydrate readiness for phase 0253.

This module derives the future Qdrant recall payload and PostgreSQL rehydrate
read shape from the handler projection readiness prepared in phase 0252.

It remains readiness-only: it does not call Qdrant, execute SQL SELECT, run
OpenVINO inference, publish EventBus events, or dispatch handlers.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from context.prod_server_handler_projection_readiness_0252 import (
    build_handler_projection_readiness,
)
from context.prod_server_postgresql_schema_readiness_0245 import (
    build_postgresql_schema_readiness,
)


RECALL_REHYDRATE_READINESS_VERSION = "0253.r1"


RECALL_REHYDRATE_READINESS_BOUNDARY: dict[str, bool] = {
    "readiness_only": True,
    "uses_handler_projection_readiness": True,
    "uses_postgresql_schema_readiness": True,
    "calls_qdrant_api": False,
    "executes_sql_select": False,
    "writes_postgresql": False,
    "runs_openvino_inference": False,
    "publishes_events": False,
    "dispatches_handler": False,
    "calls_scheduler_run": False,
    "calls_github_api": False,
    "requires_non_stdlib": False,
}


@dataclass(frozen=True)
class RecallRehydrateIssue:
    """One issue preventing recall to SQL rehydrate readiness."""

    surface: str
    field: str
    message: str


@dataclass(frozen=True)
class QdrantRecallPayloadShape:
    """Payload shape expected from a future Qdrant recall hit."""

    collection: str
    vector_dimension: int
    distance: str
    required_payload: tuple[str, ...]
    sql_ref: str
    content_hash: str
    model_id: str
    embedding_version: str


@dataclass(frozen=True)
class SQLRehydrateReadShape:
    """SQL read shape used after a future Qdrant recall hit."""

    table: str
    lookup_field: str
    sql_ref: str
    selected_columns: tuple[str, ...]
    preview_sql: str


@dataclass(frozen=True)
class RecallRehydrateReadinessReport:
    """JSON-compatible recall to SQL rehydrate readiness report."""

    version: str
    server_config_path: str
    openvino_config_path: str
    ready: bool
    qdrant_recall_payload: QdrantRecallPayloadShape | None
    sql_rehydrate_read: SQLRehydrateReadShape | None
    issues: tuple[RecallRehydrateIssue, ...]


def _split_sql_ref(sql_ref: str) -> tuple[str, str]:
    if "." not in sql_ref:
        return "", ""
    table, field = sql_ref.split(".", 1)
    return table.strip(), field.strip()


def _preview_select_sql(table: str, lookup_field: str, columns: tuple[str, ...]) -> str:
    joined = ", ".join(columns)
    return f"SELECT {joined} FROM {table} WHERE {lookup_field} = :sql_ref LIMIT 1;"


def build_recall_rehydrate_readiness(*, server_config_path: Path, openvino_config_path: Path) -> RecallRehydrateReadinessReport:
    """Build readiness for Qdrant recall payload to PostgreSQL rehydrate read."""

    projection = build_handler_projection_readiness(
        server_config_path=server_config_path,
        openvino_config_path=openvino_config_path,
    )
    schema = build_postgresql_schema_readiness(server_config_path)
    issues: list[RecallRehydrateIssue] = []

    if not projection.ready:
        for issue in projection.issues:
            issues.append(RecallRehydrateIssue("projection", issue.field, issue.message))
    if not schema.ready:
        for issue in schema.issues:
            issues.append(RecallRehydrateIssue("postgresql", issue.field, issue.message))

    if projection.projection_request is None:
        issues.append(RecallRehydrateIssue("projection", "projection_request", "projection request is required"))
        return RecallRehydrateReadinessReport(
            version=RECALL_REHYDRATE_READINESS_VERSION,
            server_config_path=str(server_config_path),
            openvino_config_path=str(openvino_config_path),
            ready=False,
            qdrant_recall_payload=None,
            sql_rehydrate_read=None,
            issues=tuple(issues),
        )

    request = projection.projection_request
    ref_table, ref_field = _split_sql_ref(request.sql_ref)
    if not ref_table or not ref_field:
        issues.append(RecallRehydrateIssue("qdrant", "sql_ref", "sql_ref must use table.field shape"))
    if ref_table and ref_table != request.source_table:
        issues.append(RecallRehydrateIssue("qdrant", "sql_ref", "sql_ref table must match projection source table"))

    table = None
    for candidate in schema.tables:
        if candidate.table == request.source_table:
            table = candidate
            break
    if table is None:
        issues.append(RecallRehydrateIssue("postgresql", request.source_table, "source table is required for rehydrate"))
    elif ref_field and ref_field != table.primary_key:
        issues.append(RecallRehydrateIssue("postgresql", "lookup_field", "sql_ref field must match table primary key"))

    required_payload = ("sql_ref", "model_id", "embedding_version", "content_hash")
    payload_shape = QdrantRecallPayloadShape(
        collection=request.qdrant_collection,
        vector_dimension=request.vector_dimension,
        distance=request.qdrant_distance,
        required_payload=required_payload,
        sql_ref=request.sql_ref,
        content_hash=request.content_hash,
        model_id=request.openvino_model_id,
        embedding_version=request.payload_shape.embedding_version,
    )

    selected_columns = tuple(column.name for column in table.columns) if table is not None else tuple()
    read_shape = None
    if table is not None and ref_field:
        read_shape = SQLRehydrateReadShape(
            table=table.table,
            lookup_field=ref_field,
            sql_ref=request.sql_ref,
            selected_columns=selected_columns,
            preview_sql=_preview_select_sql(table.table, ref_field, selected_columns),
        )

    return RecallRehydrateReadinessReport(
        version=RECALL_REHYDRATE_READINESS_VERSION,
        server_config_path=str(server_config_path),
        openvino_config_path=str(openvino_config_path),
        ready=not issues and read_shape is not None,
        qdrant_recall_payload=payload_shape,
        sql_rehydrate_read=read_shape,
        issues=tuple(issues),
    )


def recall_rehydrate_readiness_to_dict(report: RecallRehydrateReadinessReport) -> dict[str, Any]:
    """Convert a recall rehydrate readiness report to JSON-compatible data."""

    return asdict(report)


def write_recall_rehydrate_readiness_report(*, server_config_path: Path, openvino_config_path: Path, output_path: Path) -> dict[str, Any]:
    """Build and write the recall to SQL rehydrate readiness report."""

    report = build_recall_rehydrate_readiness(
        server_config_path=server_config_path,
        openvino_config_path=openvino_config_path,
    )
    payload = {
        "production_server_recall_rehydrate_readiness_written": True,
        "recall_rehydrate_readiness": recall_rehydrate_readiness_to_dict(report),
        "boundary": dict(RECALL_REHYDRATE_READINESS_BOUNDARY),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + chr(10), encoding="utf-8")
    return payload
