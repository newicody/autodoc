"""Scheduler-managed Qdrant recall to SQL rehydrate usage.

0263 starts from the 0261 query/embedding report, asks an injected Qdrant recall
executor for reference-only hits, and rehydrates the returned SQL refs through
the existing SQLContextStore.

Boundary:
- Qdrant is recall only and carries refs.
- SQL remains the durable authority for content.
- Scheduler uses Qdrant; Scheduler does not start Qdrant.
- OpenVINO is not executed in 0263.
- No RuntimeManager and no Scheduler.run modification.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from inference.qdrant_projection_adapter import (
    QdrantProjectionPolicy,
    QdrantProjectionTarget,
    QdrantRecallHit,
    QdrantRecallQuery,
    QdrantRecallResult,
    unique_sql_context_refs_from_recall,
)


DEFAULT_COLLECTION = "autodoc_context_embeddings"
DEFAULT_DIMENSION = 384


@dataclass(frozen=True)
class SchedulerManagedQdrantRecallSqlRehydrateRequest:
    """Controlled request for Scheduler-managed Qdrant recall and SQL rehydrate."""

    query_ref: str
    policy_decision_id: str = ""
    collection_name: str = DEFAULT_COLLECTION
    vector_dimension: int = DEFAULT_DIMENSION
    limit: int = 8

    def to_mapping(self) -> dict[str, Any]:
        return {
            "query_ref": self.query_ref,
            "policy_decision_id": self.policy_decision_id,
            "collection_name": self.collection_name,
            "vector_dimension": self.vector_dimension,
            "limit": self.limit,
        }


@dataclass(frozen=True)
class SchedulerManagedQdrantRecallSqlRehydrateResult:
    """Result for Qdrant recall refs followed by SQL rehydration."""

    valid: bool
    issues: tuple[str, ...]
    request: SchedulerManagedQdrantRecallSqlRehydrateRequest
    execute: bool
    dry_run: bool
    recall: Mapping[str, Any] = field(default_factory=dict)
    sql_refs: tuple[str, ...] = ()
    hydrated_records: tuple[Mapping[str, Any], ...] = ()
    missing_sql_refs: tuple[str, ...] = ()
    scheduler_owned: bool = True
    sql_remains_authority: bool = True
    qdrant_recall_refs_only: bool = True
    uses_existing_qdrant_projection_adapter: bool = True
    uses_existing_sql_context_store: bool = True
    starts_qdrant: bool = False
    runs_openvino: bool = False
    creates_runtime_manager: bool = False
    modifies_scheduler_run: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "scheduler_managed_qdrant_recall_sql_rehydrate_usage": True,
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "dry_run": self.dry_run,
            "request": self.request.to_mapping(),
            "recall": dict(self.recall),
            "sql_refs": list(self.sql_refs),
            "hydrated_count": len(self.hydrated_records),
            "missing_count": len(self.missing_sql_refs),
            "hydrated_records": [dict(record) for record in self.hydrated_records],
            "missing_sql_refs": list(self.missing_sql_refs),
            "scheduler_owned": self.scheduler_owned,
            "sql_remains_authority": self.sql_remains_authority,
            "qdrant_recall_refs_only": self.qdrant_recall_refs_only,
            "uses_existing_qdrant_projection_adapter": self.uses_existing_qdrant_projection_adapter,
            "uses_existing_sql_context_store": self.uses_existing_sql_context_store,
            "starts_qdrant": self.starts_qdrant,
            "runs_openvino": self.runs_openvino,
            "creates_runtime_manager": self.creates_runtime_manager,
            "modifies_scheduler_run": self.modifies_scheduler_run,
        }


class DemoQdrantRecallExecutor:
    """Smoke-only injected recall executor; not a Qdrant client."""

    def __init__(
        self,
        *,
        sql_refs: Sequence[str],
        point_prefix: str = "qdrant-point:demo",
        score: float = 1.0,
    ) -> None:
        self.sql_refs = tuple(sql_refs)
        self.point_prefix = point_prefix
        self.score = float(score)

    def upsert_points(self, points: Sequence[Any], *, target, policy):
        raise NotImplementedError("0263 does not implement projection writes")

    def search_vector(
        self,
        vector: Sequence[float],
        *,
        target: QdrantProjectionTarget,
        policy: QdrantProjectionPolicy,
        query: QdrantRecallQuery,
    ) -> QdrantRecallResult:
        hits: list[QdrantRecallHit] = []
        for index, sql_ref in enumerate(self.sql_refs[: query.limit]):
            hits.append(
                QdrantRecallHit(
                    point_id=f"{self.point_prefix}:{index}",
                    sql_context_ref=sql_ref,
                    score=max(0.0, min(1.0, self.score)),
                    source_ref=f"ctx-fragment:{sql_ref}",
                    payload=(
                        ("sql_context_ref", sql_ref),
                        ("sql_ref", sql_ref),
                        ("query_ref", query.query_ref),
                    ),
                )
            )
        return QdrantRecallResult(target=target, query=query, hits=tuple(hits), capped=False)


def embedding_report_to_vector(report: Mapping[str, Any]) -> tuple[float, ...]:
    """Extract the query vector from a 0261 embedding report."""

    embedding = report.get("embedding", {})
    if not isinstance(embedding, Mapping):
        return ()
    vector = embedding.get("vector")
    if not isinstance(vector, list):
        return ()
    return tuple(float(value) for value in vector)


def default_query_ref_from_embedding_report(report: Mapping[str, Any]) -> str:
    """Return a typed query ref from the 0261 embedding report."""

    embedding = report.get("embedding", {})
    if isinstance(embedding, Mapping):
        embedding_ref = str(embedding.get("embedding_ref") or "")
        if embedding_ref:
            return "qdrant-query:" + embedding_ref.removeprefix("embedding:")
    return "qdrant-query:0263"


def validate_recall_request(
    *,
    vector: Sequence[float],
    request: SchedulerManagedQdrantRecallSqlRehydrateRequest,
    execute: bool,
    executor: Any | None,
) -> tuple[str, ...]:
    """Validate Qdrant recall request before execution."""

    issues: list[str] = []
    if not vector:
        issues.append("query vector must not be empty")
    if request.vector_dimension <= 0:
        issues.append("vector_dimension must be > 0")
    if vector and len(vector) != request.vector_dimension:
        issues.append("query vector dimension must match vector_dimension")
    if request.limit <= 0:
        issues.append("limit must be > 0")
    if not request.query_ref.startswith("qdrant-query:"):
        issues.append("query_ref must start with qdrant-query:")
    if execute and not request.policy_decision_id:
        issues.append("execute requires policy_decision_id")
    if execute and executor is None:
        issues.append("execute requires an injected QdrantProjectionExecutor")
    return tuple(issues)


def record_to_public_mapping(record: object) -> dict[str, Any]:
    """Convert a SqlContextRecord-like object into a serialisable mapping."""

    if record is None:
        return {}
    if isinstance(record, Mapping):
        return dict(record)
    if hasattr(record, "to_mapping") and callable(record.to_mapping):
        payload = record.to_mapping()
        if isinstance(payload, Mapping):
            return dict(payload)
    if is_dataclass(record) and not isinstance(record, type):
        return dict(asdict(record))
    public: dict[str, Any] = {}
    for name in ("context_ref", "kind", "title", "body", "parent_ref", "metadata"):
        if hasattr(record, name):
            value = getattr(record, name)
            if isinstance(value, tuple):
                try:
                    value = dict(value)
                except (TypeError, ValueError):
                    value = list(value)
            public[name] = value
    return public


def rehydrate_sql_refs(store: Any, sql_refs: Sequence[str]) -> tuple[tuple[Mapping[str, Any], ...], tuple[str, ...]]:
    """Read recall refs back from SQL authority."""

    records: list[Mapping[str, Any]] = []
    missing: list[str] = []
    for sql_ref in sql_refs:
        record = store.get_record(sql_ref)
        if record is None:
            missing.append(sql_ref)
        else:
            records.append(record_to_public_mapping(record))
    return tuple(records), tuple(missing)


def run_scheduler_managed_qdrant_recall_sql_rehydrate_usage(
    embedding_report: Mapping[str, Any],
    store: Any,
    request: SchedulerManagedQdrantRecallSqlRehydrateRequest,
    *,
    execute: bool = False,
    executor: Any | None = None,
) -> SchedulerManagedQdrantRecallSqlRehydrateResult:
    """Run Qdrant recall through injected executor, then SQL rehydrate refs."""

    vector = embedding_report_to_vector(embedding_report)
    issues = list(
        validate_recall_request(
            vector=vector,
            request=request,
            execute=execute,
            executor=executor,
        )
    )
    if issues:
        return SchedulerManagedQdrantRecallSqlRehydrateResult(
            valid=False,
            issues=tuple(issues),
            request=request,
            execute=execute,
            dry_run=not execute,
        )

    target = QdrantProjectionTarget(
        collection_name=request.collection_name,
        vector_dimension=request.vector_dimension,
    )
    policy = QdrantProjectionPolicy(max_recall_hits=request.limit)
    query = QdrantRecallQuery(query_ref=request.query_ref, limit=request.limit, role="query")

    if not execute:
        return SchedulerManagedQdrantRecallSqlRehydrateResult(
            valid=True,
            issues=(),
            request=request,
            execute=False,
            dry_run=True,
            recall={
                "target": target.to_mapping(),
                "query_ref": query.query_ref,
                "limit": query.limit,
                "planned": True,
            },
        )

    recall = executor.search_vector(vector, target=target, policy=policy, query=query)
    sql_refs = unique_sql_context_refs_from_recall(recall, max_refs=request.limit)
    hydrated, missing = rehydrate_sql_refs(store, sql_refs)

    return SchedulerManagedQdrantRecallSqlRehydrateResult(
        valid=True,
        issues=(),
        request=request,
        execute=True,
        dry_run=False,
        recall=recall.to_mapping(),
        sql_refs=sql_refs,
        hydrated_records=hydrated,
        missing_sql_refs=missing,
    )


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def write_report(output: Path, payload: Mapping[str, Any]) -> None:
    """Write a JSON report."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
