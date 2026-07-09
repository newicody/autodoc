"""Projection path readiness for phase 0248.

This module composes the read-only readiness checks for the production projection
path:

SQL durable record -> OpenVINO embedding -> Qdrant point payload

It does not connect to PostgreSQL, run OpenVINO inference, call Qdrant, create
collections, or write points.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from context.prod_server_openvino_embedding_readiness_0246 import (
    build_openvino_embedding_readiness,
)
from context.prod_server_postgresql_schema_readiness_0245 import (
    build_postgresql_schema_readiness,
)
from context.prod_server_qdrant_collection_readiness_0247 import (
    build_qdrant_collection_readiness,
)


PROJECTION_PATH_READINESS_VERSION = "0248.r1"


PROJECTION_PATH_READINESS_BOUNDARY: dict[str, bool] = {
    "readiness_only": True,
    "uses_postgresql_readiness": True,
    "uses_openvino_readiness": True,
    "uses_qdrant_readiness": True,
    "connects_postgresql": False,
    "runs_openvino_inference": False,
    "calls_qdrant_api": False,
    "creates_qdrant_collection": False,
    "writes_qdrant_points": False,
    "publishes_events": False,
    "calls_github_api": False,
    "requires_non_stdlib": False,
}


@dataclass(frozen=True)
class ProjectionPathIssue:
    """One issue preventing projection path readiness."""

    surface: str
    field: str
    message: str


@dataclass(frozen=True)
class ProjectionPointShape:
    """Future Qdrant point shape derived from SQL/OpenVINO/Qdrant readiness."""

    source_table: str
    sql_ref_field: str
    text_source_field: str
    vector_dimension: int
    distance: str
    collection: str
    required_payload: tuple[str, ...]
    payload_sql_ref: str
    payload_model_id: str
    payload_embedding_version: str
    payload_content_hash: str


@dataclass(frozen=True)
class ProjectionPathReadinessReport:
    """JSON-compatible projection path readiness report."""

    version: str
    server_config_path: str
    openvino_config_path: str
    ready: bool
    point_shape: ProjectionPointShape | None
    issues: tuple[ProjectionPathIssue, ...]


def _table_names(postgresql_report: Any) -> set[str]:
    return {table.table for table in postgresql_report.tables}


def build_projection_path_readiness(*, server_config_path: Path, openvino_config_path: Path) -> ProjectionPathReadinessReport:
    """Build readiness for SQL -> OpenVINO -> Qdrant projection."""

    postgresql = build_postgresql_schema_readiness(server_config_path)
    openvino = build_openvino_embedding_readiness(openvino_config_path)
    qdrant = build_qdrant_collection_readiness(
        server_config_path=server_config_path,
        openvino_config_path=openvino_config_path,
    )
    issues: list[ProjectionPathIssue] = []

    if not postgresql.ready:
        for issue in postgresql.issues:
            issues.append(ProjectionPathIssue("postgresql", issue.field, issue.message))
    if not openvino.ready:
        for issue in openvino.issues:
            issues.append(ProjectionPathIssue("openvino", issue.field, issue.message))
    if not qdrant.ready:
        for issue in qdrant.issues:
            issues.append(ProjectionPathIssue("qdrant", issue.field, issue.message))

    if "context_records" not in _table_names(postgresql):
        issues.append(ProjectionPathIssue("postgresql", "context_records", "context_records table is required"))

    embedding = openvino.embedding
    collection = qdrant.collection
    if embedding is not None and collection is not None:
        if embedding.dimension != collection.vector_dimension:
            issues.append(ProjectionPathIssue("projection", "dimension", "OpenVINO and Qdrant dimensions must match"))
        if embedding.qdrant_distance != collection.distance:
            issues.append(ProjectionPathIssue("projection", "distance", "OpenVINO and Qdrant distance must match"))
        if not embedding.normalized or not collection.normalized_vectors:
            issues.append(ProjectionPathIssue("projection", "normalized", "OpenVINO and Qdrant must use normalized vectors"))

    point_shape: ProjectionPointShape | None = None
    if embedding is not None and collection is not None:
        point_shape = ProjectionPointShape(
            source_table="context_records",
            sql_ref_field="id",
            text_source_field="payload_json",
            vector_dimension=embedding.dimension,
            distance=collection.distance,
            collection=collection.collection,
            required_payload=collection.required_payload,
            payload_sql_ref="context_records.id",
            payload_model_id=embedding.model_id,
            payload_embedding_version="0248.r1",
            payload_content_hash="context_records.content_hash",
        )

    return ProjectionPathReadinessReport(
        version=PROJECTION_PATH_READINESS_VERSION,
        server_config_path=str(server_config_path),
        openvino_config_path=str(openvino_config_path),
        ready=not issues,
        point_shape=point_shape,
        issues=tuple(issues),
    )


def projection_path_readiness_to_dict(report: ProjectionPathReadinessReport) -> dict[str, Any]:
    """Convert a projection path readiness report to JSON-compatible data."""

    return asdict(report)


def write_projection_path_readiness_report(*, server_config_path: Path, openvino_config_path: Path, output_path: Path) -> dict[str, Any]:
    """Build and write the projection path readiness report."""

    report = build_projection_path_readiness(
        server_config_path=server_config_path,
        openvino_config_path=openvino_config_path,
    )
    payload = {
        "production_server_projection_path_readiness_written": True,
        "projection_path_readiness": projection_path_readiness_to_dict(report),
        "boundary": dict(PROJECTION_PATH_READINESS_BOUNDARY),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + chr(10), encoding="utf-8")
    return payload
