"""Scheduler-managed sql_ref to OpenVINO/E5 embedding usage.

0261 starts from a real SQL authority reference produced by 0260, rehydrates it
through an existing SQLContextStore object, and prepares or executes an explicit
OpenVINO/E5 passage embedding.

Boundary:
- Scheduler uses an existing SQLContextStore object.
- Scheduler uses the existing OpenVINO/E5 pipeline surface.
- Scheduler does not start OpenVINO.
- Qdrant is not involved in 0261.
- No RuntimeManager and no Scheduler.run modification.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
import asyncio
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence


SQL_REF_PREFIX = "sql:"
DEFAULT_ROLE = "passage"
DEFAULT_DIMENSION = 384
DEFAULT_BACKEND_REF = "openvino:model:multilingual-e5-small"


class ExistingSqlContextStoreReader(Protocol):
    """Existing SQLContextStore reader surface used by duck typing only."""

    def get_record(self, context_ref: str) -> object | None:
        ...


EmbeddingCallable = Callable[[str, str, str | None, str], Mapping[str, Any]]


@dataclass(frozen=True)
class SchedulerManagedSqlRefOpenVinoEmbeddingRequest:
    """Controlled request for Scheduler-managed SQL ref embedding."""

    sql_ref: str
    role: str = DEFAULT_ROLE
    policy_decision_id: str = ""
    model_dir: str | None = None
    device: str = "CPU"

    def to_mapping(self) -> dict[str, Any]:
        return {
            "sql_ref": self.sql_ref,
            "role": self.role,
            "policy_decision_id": self.policy_decision_id,
            "model_dir": self.model_dir,
            "device": self.device,
        }


@dataclass(frozen=True)
class SchedulerManagedSqlRefOpenVinoEmbeddingResult:
    """Result of SQL rehydrate -> OpenVINO embedding usage."""

    valid: bool
    issues: tuple[str, ...]
    request: SchedulerManagedSqlRefOpenVinoEmbeddingRequest
    execute: bool
    dry_run: bool
    record: Mapping[str, Any] = field(default_factory=dict)
    embedding_text: str = ""
    embedding: Mapping[str, Any] = field(default_factory=dict)
    scheduler_owned: bool = True
    uses_existing_sql_context_store: bool = True
    uses_existing_openvino_e5_pipeline: bool = True
    starts_openvino: bool = False
    calls_qdrant: bool = False
    creates_runtime_manager: bool = False
    modifies_scheduler_run: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "scheduler_managed_sql_ref_openvino_embedding_usage": True,
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "dry_run": self.dry_run,
            "request": self.request.to_mapping(),
            "record": dict(self.record),
            "embedding_text": self.embedding_text,
            "embedding": dict(self.embedding),
            "scheduler_owned": self.scheduler_owned,
            "uses_existing_sql_context_store": self.uses_existing_sql_context_store,
            "uses_existing_openvino_e5_pipeline": self.uses_existing_openvino_e5_pipeline,
            "starts_openvino": self.starts_openvino,
            "calls_qdrant": self.calls_qdrant,
            "creates_runtime_manager": self.creates_runtime_manager,
            "modifies_scheduler_run": self.modifies_scheduler_run,
        }


def validate_sql_ref_for_openvino_embedding(sql_ref: str) -> tuple[str, ...]:
    """Validate the SQL authority reference before embedding."""

    if not sql_ref:
        return ("sql_ref must not be empty",)
    if not sql_ref.startswith(SQL_REF_PREFIX):
        return ("sql_ref must start with sql:",)
    return ()


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


def build_openvino_passage_text_from_sql_record(record: Mapping[str, Any]) -> str:
    """Build the explicit E5 passage text from a hydrated SQL record."""

    title = str(record.get("title") or record.get("context_ref") or "SQL context record").strip()
    body = str(record.get("body") or record.get("content") or record.get("text") or "").strip()
    if not body:
        raise ValueError("SQL record body must not be empty")
    return f"passage: {title}\n{body}"


def build_embedding_ref(sql_ref: str, role: str, text: str) -> str:
    """Build a deterministic typed embedding ref."""

    digest = hashlib.sha256()
    digest.update(sql_ref.encode("utf-8"))
    digest.update(b"\0")
    digest.update(role.encode("utf-8"))
    digest.update(b"\0")
    digest.update(text.encode("utf-8"))
    return f"embedding:{role}:{digest.hexdigest()[:16]}"


def build_embedding_mapping(
    *,
    sql_ref: str,
    role: str,
    text: str,
    vector: Sequence[float],
    backend_ref: str = DEFAULT_BACKEND_REF,
    model: str = "openvino.embedding.e5-small",
    tokenizer: str = "transformers.multilingual-e5-small",
    model_path: str = "",
    device: str = "CPU",
) -> dict[str, Any]:
    """Build a stable embedding mapping suitable for later vector projection."""

    values = tuple(float(value) for value in vector)
    if not values:
        raise ValueError("embedding vector must not be empty")
    l2_norm = math.sqrt(sum(value * value for value in values))
    normalized = math.isclose(l2_norm, 1.0, rel_tol=1e-4, abs_tol=1e-4)
    return {
        "schema": "missipy.scheduler_managed_sql_ref_openvino_embedding.v1",
        "embedding_ref": build_embedding_ref(sql_ref, role, text),
        "source_ref": f"ctx-fragment:{sql_ref}",
        "sql_ref": sql_ref,
        "backend_ref": backend_ref,
        "role": role,
        "dimension": len(values),
        "normalized": normalized,
        "l2_norm": l2_norm,
        "metadata": {
            "context_ref": sql_ref,
            "model": model,
            "tokenizer": tokenizer,
            "model_path": model_path,
            "device": device,
        },
        "vector": list(values),
    }


def build_demo_embedding(
    text: str,
    sql_ref: str,
    model_dir: str | None = None,
    device: str = "CPU",
    *,
    role: str = DEFAULT_ROLE,
    dimension: int = DEFAULT_DIMENSION,
) -> dict[str, Any]:
    """Build a deterministic normalized demo embedding for tests/smokes."""

    if dimension <= 0:
        raise ValueError("dimension must be > 0")
    vector = [0.0] * dimension
    vector[0] = 1.0
    return build_embedding_mapping(
        sql_ref=sql_ref,
        role=role,
        text=text,
        vector=vector,
        model="demo.openvino.embedding.e5-small",
        tokenizer="demo.tokenizer",
        model_path=model_dir or "",
        device=device,
    )


def embed_with_existing_openvino_e5_pipeline(
    text: str,
    sql_ref: str,
    model_dir: str | None = None,
    device: str = "CPU",
    *,
    role: str = DEFAULT_ROLE,
) -> dict[str, Any]:
    """Execute the existing OpenVINO/E5 pipeline explicitly."""

    from inference.e5_pipeline import (  # noqa: WPS433 - explicit existing runtime surface.
        MultilingualE5SmallPipelineConfig,
        build_multilingual_e5_small_pipeline,
    )
    from inference.e5_profile import MultilingualE5SmallLocalConfig  # noqa: WPS433
    from inference.e5_text import ensure_e5_text  # noqa: WPS433

    config = MultilingualE5SmallPipelineConfig(
        local=MultilingualE5SmallLocalConfig(model_dir=model_dir, device=device),
        require_model_exists=True,
        metadata={"scheduler_managed_sql_ref_openvino_embedding_usage": "0261"},
    )
    bundle = build_multilingual_e5_small_pipeline(config)
    e5_text = ensure_e5_text(text, default_role=role)
    result = asyncio.run(bundle.pipeline.embed_text(e5_text.prefixed))
    return build_embedding_mapping(
        sql_ref=sql_ref,
        role=role,
        text=e5_text.prefixed,
        vector=result.vector.values,
        model=result.model,
        tokenizer=result.tokenizer_name,
        model_path=bundle.summary.model_path,
        device=bundle.summary.device,
    )


def run_scheduler_managed_sql_ref_openvino_embedding_usage(
    store: ExistingSqlContextStoreReader,
    request: SchedulerManagedSqlRefOpenVinoEmbeddingRequest,
    *,
    execute: bool = False,
    embedder: EmbeddingCallable | None = None,
) -> SchedulerManagedSqlRefOpenVinoEmbeddingResult:
    """Rehydrate a SQL ref and optionally embed it through OpenVINO/E5."""

    issues = list(validate_sql_ref_for_openvino_embedding(request.sql_ref))
    if request.role not in ("passage", "query"):
        issues.append("role must be passage or query")
    if execute and not request.policy_decision_id:
        issues.append("execute requires policy_decision_id")

    record_mapping: dict[str, Any] = {}
    embedding_text = ""
    if not issues:
        record_obj = store.get_record(request.sql_ref)
        if record_obj is None:
            issues.append("sql_ref was not found in SQLContextStore")
        else:
            record_mapping = record_to_public_mapping(record_obj)
            try:
                embedding_text = build_openvino_passage_text_from_sql_record(record_mapping)
            except ValueError as exc:
                issues.append(str(exc))

    if issues:
        return SchedulerManagedSqlRefOpenVinoEmbeddingResult(
            valid=False,
            issues=tuple(issues),
            request=request,
            execute=execute,
            dry_run=not execute,
            record=record_mapping,
            embedding_text=embedding_text,
        )

    if not execute:
        return SchedulerManagedSqlRefOpenVinoEmbeddingResult(
            valid=True,
            issues=(),
            request=request,
            execute=False,
            dry_run=True,
            record=record_mapping,
            embedding_text=embedding_text,
        )

    effective_embedder = embedder or embed_with_existing_openvino_e5_pipeline
    embedding = effective_embedder(embedding_text, request.sql_ref, request.model_dir, request.device)
    return SchedulerManagedSqlRefOpenVinoEmbeddingResult(
        valid=True,
        issues=(),
        request=request,
        execute=True,
        dry_run=False,
        record=record_mapping,
        embedding_text=embedding_text,
        embedding=embedding,
    )


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def write_report(output: Path, payload: Mapping[str, Any]) -> None:
    """Write a JSON report."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
