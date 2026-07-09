"""Qdrant collection readiness aligned with OpenVINO for phase 0247.

This module checks that the production server Qdrant collection shape matches
the OpenVINO embedding readiness from phase 0246. It does not call Qdrant,
create collections, upsert points, or run embeddings.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from context.prod_server_ini_validation_0241 import load_ini, validate_ini_file
from context.prod_server_openvino_embedding_readiness_0246 import (
    build_openvino_embedding_readiness,
)


QDRANT_COLLECTION_READINESS_VERSION = "0247.r1"


QDRANT_COLLECTION_READINESS_BOUNDARY: dict[str, bool] = {
    "readiness_only": True,
    "uses_validated_ini": True,
    "uses_openvino_readiness": True,
    "calls_qdrant_api": False,
    "creates_qdrant_collection": False,
    "upserts_qdrant_points": False,
    "runs_openvino_inference": False,
    "writes_postgresql": False,
    "publishes_events": False,
    "calls_github_api": False,
    "requires_non_stdlib": False,
}


QDRANT_SECTION = "qdrant.collection.autodoc_context_e5_small"
REQUIRED_COLLECTION = "autodoc_context_e5_small"
REQUIRED_PAYLOAD = ("sql_ref", "model_id", "embedding_version", "content_hash")


@dataclass(frozen=True)
class QdrantCollectionIssue:
    """One issue in Qdrant collection readiness."""

    section: str
    field: str
    message: str


@dataclass(frozen=True)
class QdrantCollectionSpec:
    """Qdrant collection shape expected by the production server."""

    collection: str
    vector_dimension: int
    distance: str
    normalized_vectors: bool
    required_payload: tuple[str, ...]
    optional_payload: tuple[str, ...]
    aligned_openvino_model_id: str
    aligned_openvino_device: str


@dataclass(frozen=True)
class QdrantCollectionReadinessReport:
    """JSON-compatible Qdrant collection readiness report."""

    version: str
    server_config_path: str
    openvino_config_path: str
    ready: bool
    collection: QdrantCollectionSpec | None
    issues: tuple[QdrantCollectionIssue, ...]


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def build_qdrant_collection_readiness(*, server_config_path: Path, openvino_config_path: Path) -> QdrantCollectionReadinessReport:
    """Build Qdrant collection readiness from server and OpenVINO INI files."""

    server_validation = validate_ini_file(server_config_path)
    openvino_readiness = build_openvino_embedding_readiness(openvino_config_path)
    parser = load_ini(server_config_path)
    issues: list[QdrantCollectionIssue] = []

    if not server_validation.valid:
        for issue in server_validation.issues:
            if issue.section.startswith("qdrant"):
                issues.append(QdrantCollectionIssue(issue.section, issue.key, issue.message))
    if not openvino_readiness.ready:
        for issue in openvino_readiness.issues:
            issues.append(QdrantCollectionIssue(issue.section, issue.field, issue.message))

    if not parser.has_section(QDRANT_SECTION):
        return QdrantCollectionReadinessReport(
            version=QDRANT_COLLECTION_READINESS_VERSION,
            server_config_path=str(server_config_path),
            openvino_config_path=str(openvino_config_path),
            ready=False,
            collection=None,
            issues=tuple(issues + [QdrantCollectionIssue(QDRANT_SECTION, "*", "missing Qdrant collection section")]),
        )

    section = QDRANT_SECTION
    collection = parser.get(section, "collection", fallback="")
    vector_dimension = parser.getint(section, "vector_dimension", fallback=0)
    distance = parser.get(section, "distance", fallback="")
    normalized_vectors = parser.getboolean(section, "normalized_vectors", fallback=False)
    required_payload = _split_csv(parser.get(section, "required_payload", fallback=""))
    optional_payload = _split_csv(parser.get(section, "optional_payload", fallback=""))

    embedding = openvino_readiness.embedding
    expected_dimension = embedding.dimension if embedding is not None else 0
    expected_distance = embedding.qdrant_distance if embedding is not None else ""
    expected_normalized = embedding.normalized if embedding is not None else False
    model_id = embedding.model_id if embedding is not None else ""
    device = embedding.device if embedding is not None else ""

    if collection != REQUIRED_COLLECTION:
        issues.append(QdrantCollectionIssue(section, "collection", f"must be {REQUIRED_COLLECTION}"))
    if vector_dimension != expected_dimension:
        issues.append(QdrantCollectionIssue(section, "vector_dimension", f"must match OpenVINO dimension {expected_dimension}"))
    if distance != expected_distance:
        issues.append(QdrantCollectionIssue(section, "distance", f"must match OpenVINO distance {expected_distance}"))
    if normalized_vectors != expected_normalized:
        issues.append(QdrantCollectionIssue(section, "normalized_vectors", "must match OpenVINO normalized setting"))
    for payload_key in REQUIRED_PAYLOAD:
        if payload_key not in required_payload:
            issues.append(QdrantCollectionIssue(section, "required_payload", f"must include {payload_key}"))

    spec = QdrantCollectionSpec(
        collection=collection,
        vector_dimension=vector_dimension,
        distance=distance,
        normalized_vectors=normalized_vectors,
        required_payload=required_payload,
        optional_payload=optional_payload,
        aligned_openvino_model_id=model_id,
        aligned_openvino_device=device,
    )

    return QdrantCollectionReadinessReport(
        version=QDRANT_COLLECTION_READINESS_VERSION,
        server_config_path=str(server_config_path),
        openvino_config_path=str(openvino_config_path),
        ready=not issues,
        collection=spec,
        issues=tuple(issues),
    )


def qdrant_collection_readiness_to_dict(report: QdrantCollectionReadinessReport) -> dict[str, Any]:
    """Convert a Qdrant readiness report to JSON-compatible data."""

    return asdict(report)


def write_qdrant_collection_readiness_report(*, server_config_path: Path, openvino_config_path: Path, output_path: Path) -> dict[str, Any]:
    """Build and write the Qdrant collection readiness report."""

    report = build_qdrant_collection_readiness(
        server_config_path=server_config_path,
        openvino_config_path=openvino_config_path,
    )
    payload = {
        "production_server_qdrant_collection_readiness_written": True,
        "qdrant_collection_readiness": qdrant_collection_readiness_to_dict(report),
        "boundary": dict(QDRANT_COLLECTION_READINESS_BOUNDARY),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + chr(10), encoding="utf-8")
    return payload
