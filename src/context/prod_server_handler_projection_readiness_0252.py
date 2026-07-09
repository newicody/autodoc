"""Handler projection readiness for phase 0252.

This module derives a future SQL -> OpenVINO -> Qdrant projection request from
the SQL controlled write handler frame prepared in phase 0251.

It remains readiness-only: it does not execute SQL, run OpenVINO inference, call
Qdrant, write points, publish EventBus events, or dispatch handlers.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from context.prod_server_openvino_embedding_readiness_0246 import (
    build_openvino_embedding_readiness,
)
from context.prod_server_qdrant_collection_readiness_0247 import (
    build_qdrant_collection_readiness,
)
from context.prod_server_sql_controlled_write_handler_readiness_0251 import (
    build_sql_controlled_write_handler_readiness,
)


HANDLER_PROJECTION_READINESS_VERSION = "0252.r1"


HANDLER_PROJECTION_READINESS_BOUNDARY: dict[str, bool] = {
    "readiness_only": True,
    "uses_sql_controlled_write_handler_readiness": True,
    "uses_openvino_readiness": True,
    "uses_qdrant_readiness": True,
    "executes_sql": False,
    "runs_openvino_inference": False,
    "calls_qdrant_api": False,
    "writes_qdrant_points": False,
    "publishes_events": False,
    "dispatches_handler": False,
    "calls_scheduler_run": False,
    "calls_github_api": False,
    "requires_non_stdlib": False,
}


@dataclass(frozen=True)
class HandlerProjectionIssue:
    """One issue preventing handler projection readiness."""

    surface: str
    field: str
    message: str


@dataclass(frozen=True)
class HandlerProjectionPayloadShape:
    """Future Qdrant payload derived from the SQL handler frame."""

    sql_ref: str
    model_id: str
    embedding_version: str
    content_hash: str
    source_handler_id: str
    source_intent_id: str


@dataclass(frozen=True)
class HandlerProjectionRequest:
    """Readiness-only projection request derived from a SQL handler frame."""

    projection_id: str
    source_table: str
    text_source_field: str
    sql_ref: str
    content_hash: str
    openvino_model_id: str
    openvino_device: str
    vector_dimension: int
    normalized: bool
    qdrant_collection: str
    qdrant_distance: str
    payload_shape: HandlerProjectionPayloadShape


@dataclass(frozen=True)
class HandlerProjectionReadinessReport:
    """JSON-compatible handler projection readiness report."""

    version: str
    server_config_path: str
    openvino_config_path: str
    ready: bool
    projection_request: HandlerProjectionRequest | None
    issues: tuple[HandlerProjectionIssue, ...]


def build_handler_projection_readiness(*, server_config_path: Path, openvino_config_path: Path) -> HandlerProjectionReadinessReport:
    """Build projection readiness from the SQL controlled write handler frame."""

    handler = build_sql_controlled_write_handler_readiness(
        server_config_path=server_config_path,
        openvino_config_path=openvino_config_path,
    )
    openvino = build_openvino_embedding_readiness(openvino_config_path)
    qdrant = build_qdrant_collection_readiness(
        server_config_path=server_config_path,
        openvino_config_path=openvino_config_path,
    )
    issues: list[HandlerProjectionIssue] = []

    if not handler.ready:
        for issue in handler.issues:
            issues.append(HandlerProjectionIssue("handler", issue.field, issue.message))
    if not openvino.ready:
        for issue in openvino.issues:
            issues.append(HandlerProjectionIssue("openvino", issue.field, issue.message))
    if not qdrant.ready:
        for issue in qdrant.issues:
            issues.append(HandlerProjectionIssue("qdrant", issue.field, issue.message))

    if handler.handler_frame is None:
        issues.append(HandlerProjectionIssue("handler", "handler_frame", "handler frame is required"))
    if openvino.embedding is None:
        issues.append(HandlerProjectionIssue("openvino", "embedding", "OpenVINO embedding readiness is required"))
    if qdrant.collection is None:
        issues.append(HandlerProjectionIssue("qdrant", "collection", "Qdrant collection readiness is required"))

    if issues or handler.handler_frame is None or openvino.embedding is None or qdrant.collection is None:
        return HandlerProjectionReadinessReport(
            version=HANDLER_PROJECTION_READINESS_VERSION,
            server_config_path=str(server_config_path),
            openvino_config_path=str(openvino_config_path),
            ready=False,
            projection_request=None,
            issues=tuple(issues),
        )

    write_request = handler.handler_frame.write_request
    embedding = openvino.embedding
    collection = qdrant.collection

    if embedding.dimension != collection.vector_dimension:
        issues.append(HandlerProjectionIssue("projection", "vector_dimension", "OpenVINO and Qdrant dimensions must match"))
    if embedding.qdrant_distance != collection.distance:
        issues.append(HandlerProjectionIssue("projection", "distance", "OpenVINO and Qdrant distance must match"))
    if "sql_ref" not in collection.required_payload:
        issues.append(HandlerProjectionIssue("projection", "sql_ref", "Qdrant payload must include sql_ref"))

    payload_shape = HandlerProjectionPayloadShape(
        sql_ref=write_request.sql_ref,
        model_id=embedding.model_id,
        embedding_version=HANDLER_PROJECTION_READINESS_VERSION,
        content_hash=write_request.content_hash,
        source_handler_id=write_request.handler_id,
        source_intent_id=write_request.intent_id,
    )
    projection_request = HandlerProjectionRequest(
        projection_id="projection:" + write_request.request_id,
        source_table=write_request.table,
        text_source_field="payload_json",
        sql_ref=write_request.sql_ref,
        content_hash=write_request.content_hash,
        openvino_model_id=embedding.model_id,
        openvino_device=embedding.device,
        vector_dimension=embedding.dimension,
        normalized=embedding.normalized,
        qdrant_collection=collection.collection,
        qdrant_distance=collection.distance,
        payload_shape=payload_shape,
    )

    return HandlerProjectionReadinessReport(
        version=HANDLER_PROJECTION_READINESS_VERSION,
        server_config_path=str(server_config_path),
        openvino_config_path=str(openvino_config_path),
        ready=not issues,
        projection_request=projection_request,
        issues=tuple(issues),
    )


def handler_projection_readiness_to_dict(report: HandlerProjectionReadinessReport) -> dict[str, Any]:
    """Convert a handler projection readiness report to JSON-compatible data."""

    return asdict(report)


def write_handler_projection_readiness_report(*, server_config_path: Path, openvino_config_path: Path, output_path: Path) -> dict[str, Any]:
    """Build and write the handler projection readiness report."""

    report = build_handler_projection_readiness(
        server_config_path=server_config_path,
        openvino_config_path=openvino_config_path,
    )
    payload = {
        "production_server_handler_projection_readiness_written": True,
        "handler_projection_readiness": handler_projection_readiness_to_dict(report),
        "boundary": dict(HANDLER_PROJECTION_READINESS_BOUNDARY),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + chr(10), encoding="utf-8")
    return payload
