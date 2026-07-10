"""Scheduler-managed embedding to Qdrant projection usage.

0262 starts from the 0261 OpenVINO/E5 embedding report and projects it toward
Qdrant through the existing Qdrant projection adapter.

Boundary:
- SQL remains the durable authority.
- Qdrant stores projection payloads carrying the SQL authority reference.
- Scheduler uses Qdrant; Scheduler does not start Qdrant.
- OpenVINO is not executed in 0262.
- No RuntimeManager and no Scheduler.run modification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from inference.openvino_embedding_adapter import (
    OpenVINOEmbeddingBatch,
    OpenVINOEmbeddingRuntimeTarget,
    OpenVINOEmbeddingVector,
)
from inference.qdrant_projection_adapter import (
    QdrantProjectionPolicy,
    QdrantProjectionTarget,
    QdrantProjectionWriteResult,
    build_qdrant_projection_batch,
)


DEFAULT_COLLECTION = "autodoc_context_embeddings"
DEFAULT_DIMENSION = 384


@dataclass(frozen=True)
class SchedulerManagedEmbeddingQdrantProjectionRequest:
    """Controlled request for Scheduler-managed Qdrant projection."""

    policy_decision_id: str = ""
    collection_name: str = DEFAULT_COLLECTION
    vector_dimension: int = DEFAULT_DIMENSION

    def to_mapping(self) -> dict[str, Any]:
        return {
            "policy_decision_id": self.policy_decision_id,
            "collection_name": self.collection_name,
            "vector_dimension": self.vector_dimension,
        }


@dataclass(frozen=True)
class SchedulerManagedEmbeddingQdrantProjectionResult:
    """Result for embedding -> Qdrant projection usage."""

    valid: bool
    issues: tuple[str, ...]
    request: SchedulerManagedEmbeddingQdrantProjectionRequest
    execute: bool
    dry_run: bool
    sql_ref: str = ""
    embedding_ref: str = ""
    batch: Mapping[str, Any] = field(default_factory=dict)
    write_result: Mapping[str, Any] = field(default_factory=dict)
    scheduler_owned: bool = True
    sql_remains_authority: bool = True
    uses_existing_qdrant_projection_adapter: bool = True
    starts_qdrant: bool = False
    runs_openvino: bool = False
    creates_runtime_manager: bool = False
    modifies_scheduler_run: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "scheduler_managed_embedding_qdrant_projection_usage": True,
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "dry_run": self.dry_run,
            "request": self.request.to_mapping(),
            "sql_ref": self.sql_ref,
            "embedding_ref": self.embedding_ref,
            "batch": dict(self.batch),
            "write_result": dict(self.write_result),
            "scheduler_owned": self.scheduler_owned,
            "sql_remains_authority": self.sql_remains_authority,
            "uses_existing_qdrant_projection_adapter": self.uses_existing_qdrant_projection_adapter,
            "starts_qdrant": self.starts_qdrant,
            "runs_openvino": self.runs_openvino,
            "creates_runtime_manager": self.creates_runtime_manager,
            "modifies_scheduler_run": self.modifies_scheduler_run,
        }


class DemoQdrantProjectionExecutor:
    """Smoke-only injected executor; not a Qdrant client."""

    def upsert_points(
        self,
        points: Sequence[Any],
        *,
        target: QdrantProjectionTarget,
        policy: QdrantProjectionPolicy,
    ) -> QdrantProjectionWriteResult:
        return QdrantProjectionWriteResult(
            target=target,
            point_ids=tuple(point.point_id for point in points),
            acknowledged=True,
        )

    def search_vector(self, vector: Sequence[float], *, target, policy, query):
        raise NotImplementedError("0262 does not implement recall")


def embedding_report_to_mapping(report: Mapping[str, Any]) -> Mapping[str, Any]:
    """Extract the embedding mapping from a 0261 report."""

    embedding = report.get("embedding", {})
    if not isinstance(embedding, Mapping):
        return {}
    return embedding


def validate_embedding_mapping_for_projection(embedding: Mapping[str, Any]) -> tuple[str, ...]:
    """Validate the 0261 embedding mapping before Qdrant projection."""

    issues: list[str] = []
    if not embedding:
        return ("embedding mapping must not be empty",)

    sql_ref = str(embedding.get("sql_ref") or "")
    if not sql_ref.startswith("sql:"):
        issues.append("embedding.sql_ref must start with sql:")

    source_ref = str(embedding.get("source_ref") or "")
    if not source_ref.startswith("ctx-fragment:sql:"):
        issues.append("embedding.source_ref must be ctx-fragment:<sql_ref>")

    vector = embedding.get("vector")
    if not isinstance(vector, list) or not vector:
        issues.append("embedding.vector must be a non-empty list")

    dimension = embedding.get("dimension")
    if isinstance(vector, list) and dimension != len(vector):
        issues.append("embedding.dimension must match vector length")

    if embedding.get("normalized") is not True:
        issues.append("embedding.normalized must be true")

    return tuple(issues)


def build_openvino_embedding_batch_from_0261_mapping(
    embedding: Mapping[str, Any],
    *,
    vector_dimension: int = DEFAULT_DIMENSION,
) -> OpenVINOEmbeddingBatch:
    """Build an existing OpenVINOEmbeddingBatch from the 0261 embedding mapping."""

    sql_ref = str(embedding["sql_ref"])
    metadata = dict(embedding.get("metadata", {}))
    metadata.setdefault("context_ref", sql_ref)
    vector = tuple(float(value) for value in embedding["vector"])
    target = OpenVINOEmbeddingRuntimeTarget(
        model_dir=str(metadata.get("model_path") or "/home/eric/model/openvino/multilingual-e5-small"),
        device=str(metadata.get("device") or "CPU"),
        dimension=vector_dimension,
        normalized=True,
        backend_ref=str(embedding.get("backend_ref") or "openvino:model:multilingual-e5-small"),
    )
    item = OpenVINOEmbeddingVector(
        embedding_ref=str(embedding["embedding_ref"]),
        source_ref=str(embedding["source_ref"]),
        vector=vector,
        backend_ref=target.backend_ref,
        role=str(embedding.get("role") or "passage"),
        normalized=True,
        metadata=tuple(sorted((str(key), str(value)) for key, value in metadata.items())),
    )
    return OpenVINOEmbeddingBatch(target=target, vectors=(item,), capped=False)


def add_sql_ref_alias_to_projection_mapping(batch_mapping: Mapping[str, Any]) -> dict[str, Any]:
    """Add a payload.sql_ref alias while preserving existing sql_context_ref."""

    payload = json.loads(json.dumps(dict(batch_mapping)))
    for point in payload.get("points", []):
        point_payload = point.get("payload", {})
        sql_context_ref = point.get("sql_context_ref") or point_payload.get("sql_context_ref")
        if sql_context_ref:
            point_payload.setdefault("sql_ref", sql_context_ref)
            point["payload"] = point_payload
    return payload


def run_scheduler_managed_embedding_qdrant_projection_usage(
    embedding_report: Mapping[str, Any],
    request: SchedulerManagedEmbeddingQdrantProjectionRequest,
    *,
    execute: bool = False,
    executor: Any | None = None,
) -> SchedulerManagedEmbeddingQdrantProjectionResult:
    """Build and optionally upsert Qdrant projection points from 0261 output."""

    embedding = embedding_report_to_mapping(embedding_report)
    issues = list(validate_embedding_mapping_for_projection(embedding))
    if request.vector_dimension <= 0:
        issues.append("vector_dimension must be > 0")
    if execute and not request.policy_decision_id:
        issues.append("execute requires policy_decision_id")
    if execute and executor is None:
        issues.append("execute requires an injected QdrantProjectionExecutor")

    if issues:
        return SchedulerManagedEmbeddingQdrantProjectionResult(
            valid=False,
            issues=tuple(issues),
            request=request,
            execute=execute,
            dry_run=not execute,
            sql_ref=str(embedding.get("sql_ref") or "") if isinstance(embedding, Mapping) else "",
            embedding_ref=str(embedding.get("embedding_ref") or "") if isinstance(embedding, Mapping) else "",
        )

    embedding_batch = build_openvino_embedding_batch_from_0261_mapping(
        embedding,
        vector_dimension=request.vector_dimension,
    )
    target = QdrantProjectionTarget(
        collection_name=request.collection_name,
        vector_dimension=request.vector_dimension,
    )
    policy = QdrantProjectionPolicy()
    batch = build_qdrant_projection_batch(embedding_batch, target, policy)
    batch_mapping = add_sql_ref_alias_to_projection_mapping(batch.to_mapping())

    if not execute:
        return SchedulerManagedEmbeddingQdrantProjectionResult(
            valid=True,
            issues=(),
            request=request,
            execute=False,
            dry_run=True,
            sql_ref=str(embedding["sql_ref"]),
            embedding_ref=str(embedding["embedding_ref"]),
            batch=batch_mapping,
        )

    write_result = executor.upsert_points(batch.points, target=target, policy=policy)
    return SchedulerManagedEmbeddingQdrantProjectionResult(
        valid=True,
        issues=(),
        request=request,
        execute=True,
        dry_run=False,
        sql_ref=str(embedding["sql_ref"]),
        embedding_ref=str(embedding["embedding_ref"]),
        batch=batch_mapping,
        write_result=write_result.to_mapping(),
    )


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def write_report(output: Path, payload: Mapping[str, Any]) -> None:
    """Write a JSON report."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
