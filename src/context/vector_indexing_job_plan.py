"""Vector indexing job plan.

0128 turns vectorized contracts, specialist outputs, context chunks, bus signals,
and synthesis candidates into Scheduler-addressable indexing jobs.  The plan is
pure contract data: Scheduler remains the orchestrator of vector indexing jobs;
route /dev/shm is the multitask data-plane interface and future grid seam;
E5/OpenVINO remains embedding only behind adapter; Qdrant is projection and
recall only; it does not decide; SQLContextStore is durable context authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re

from context.vector_collection_registry import VectorCollectionRegistry, VectorPointRoutingPlan, build_default_vector_collection_registry

_INDEXABLE_ITEM_SCHEMA = "missipy.vector.indexable_item.v1"
_EMBEDDING_JOB_SCHEMA = "missipy.vector.embedding_job.v1"
_PROJECTION_JOB_SCHEMA = "missipy.vector.projection_job.v1"
_ROUTE_FRAME_SCHEMA = "missipy.vector.indexing_route_frame.v1"
_BATCH_COMMAND_SCHEMA = "missipy.scheduler.vector_indexing_batch_command.v1"
_JOB_PLAN_SCHEMA = "missipy.vector.indexing_job_plan.v1"

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_ALLOWED_REF_PREFIXES = (
    "sql:",
    "ctx:",
    "ctx-result:",
    "ctx-fragment:",
    "qdrant:",
    "collection:",
    "contract:",
    "specialist:",
    "specialist-output:",
    "specialist-opinion:",
    "route:",
    "route-frame:",
    "artifact:",
    "github:",
    "bus:",
    "specialist-path:",
    "scheduler-trace:",
    "openvino:",
    "e5:",
    "embedding:",
    "embedding-job:",
    "embedding-model:",
    "projection-job:",
    "vector-plan:",
    "vector-point:",
    "vector-registry:",
    "vector-route:",
    "command:",
    "scheduler-command:",
)
_ALLOWED_EMBEDDING_ROLES = ("query", "passage")
_ALLOWED_ROUTE_FRAME_KINDS = ("embedding_request", "embedding_result", "projection_request", "projection_ack")
_ALLOWED_OUTPUT_KINDS = (
    "context_chunk",
    "contract",
    "instruction_contract",
    "human_representation_contract",
    "preliminary_opinion",
    "feasibility_review",
    "context_patch_proposal",
    "work_product",
    "analysis_signal",
    "bus_fact",
    "scheduler_trace",
    "specialist_path",
    "final_synthesis_candidate",
    "synthesis_candidate",
)


@dataclass(frozen=True, slots=True)
class VectorIndexableItem:
    """One SQL-owned or bus-observed item that should be embedded and projected."""

    source_ref: str
    output_kind: str
    text_for_embedding: str
    embedding_role: str = "passage"
    sql_authority_ref: str = "sql:context-store"
    specialist_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_typed_ref("source_ref", self.source_ref)
        if self.output_kind not in _ALLOWED_OUTPUT_KINDS:
            raise ValueError("output_kind must be one of the locked vector indexing output kinds")
        if self.embedding_role not in _ALLOWED_EMBEDDING_ROLES:
            raise ValueError("embedding_role must be query or passage")
        _require_typed_ref("sql_authority_ref", self.sql_authority_ref, required_prefixes=("sql:",))
        if self.specialist_ref is not None:
            _require_typed_ref("specialist_ref", self.specialist_ref, required_prefixes=("specialist:",))
        _require_prefixed_embedding_text(self.embedding_role, self.text_for_embedding)
        object.__setattr__(self, "evidence_refs", _normalize_refs("evidence_refs", self.evidence_refs, allow_empty=True))
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def item_ref(self) -> str:
        seed = f"{self.source_ref}|{self.output_kind}|{self.embedding_role}|{self.text_for_embedding}"
        return f"vector-plan:item-{_stable_suffix(seed)}"

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _INDEXABLE_ITEM_SCHEMA,
            "item_ref": self.item_ref,
            "source_ref": self.source_ref,
            "output_kind": self.output_kind,
            "embedding_role": self.embedding_role,
            "text_for_embedding": self.text_for_embedding,
            "sql_authority_ref": self.sql_authority_ref,
            "specialist_ref": self.specialist_ref,
            "evidence_refs": list(self.evidence_refs),
            "metadata": dict(self.metadata),
            "e5_openvino_role": "embedding only behind adapter",
            "sql_is_authority": True,
        }


@dataclass(frozen=True, slots=True)
class VectorIndexingRouteFrameRef:
    """Typed /dev/shm route frame ref for vector indexing worker exchange."""

    route_ref: str
    dev_shm_path: str
    frame_kind: str
    source_ref: str

    def __post_init__(self) -> None:
        _require_typed_ref("route_ref", self.route_ref, required_prefixes=("route:", "route-frame:", "vector-route:"))
        if not self.dev_shm_path.startswith("/dev/shm/autodoc/routes/"):
            raise ValueError("dev_shm_path must start with /dev/shm/autodoc/routes/")
        if ".." in self.dev_shm_path:
            raise ValueError("dev_shm_path must not contain '..'")
        if self.frame_kind not in _ALLOWED_ROUTE_FRAME_KINDS:
            raise ValueError("frame_kind must be a locked vector indexing route frame kind")
        _require_typed_ref("source_ref", self.source_ref)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _ROUTE_FRAME_SCHEMA,
            "route_ref": self.route_ref,
            "dev_shm_path": self.dev_shm_path,
            "frame_kind": self.frame_kind,
            "source_ref": self.source_ref,
            "data_plane": "dev_shm_multitask_interface",
            "future_grid_seam": True,
            "durable_authority": False,
        }


@dataclass(frozen=True, slots=True)
class VectorEmbeddingJob:
    """Scheduler-addressable job for E5/OpenVINO embedding behind adapter."""

    job_ref: str
    item: VectorIndexableItem
    request_frame: VectorIndexingRouteFrameRef
    result_frame: VectorIndexingRouteFrameRef
    embedding_model_ref: str = "openvino:e5-small"
    expected_dimension: int = 384

    def __post_init__(self) -> None:
        _require_typed_ref("job_ref", self.job_ref, required_prefixes=("embedding-job:",))
        _require_typed_ref("embedding_model_ref", self.embedding_model_ref, required_prefixes=("openvino:", "e5:", "embedding-model:"))
        if self.expected_dimension <= 0:
            raise ValueError("expected_dimension must be > 0")
        if self.request_frame.frame_kind != "embedding_request":
            raise ValueError("request_frame must be embedding_request")
        if self.result_frame.frame_kind != "embedding_result":
            raise ValueError("result_frame must be embedding_result")
        if self.request_frame.source_ref != self.item.source_ref or self.result_frame.source_ref != self.item.source_ref:
            raise ValueError("embedding route frames must reference the indexed item source")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _EMBEDDING_JOB_SCHEMA,
            "job_ref": self.job_ref,
            "item": self.item.to_mapping(),
            "request_frame": self.request_frame.to_mapping(),
            "result_frame": self.result_frame.to_mapping(),
            "embedding_model_ref": self.embedding_model_ref,
            "expected_dimension": self.expected_dimension,
            "runtime_import_required_here": False,
            "openvino_adapter_executes_later": True,
            "e5_openvino_role": "embedding only behind adapter",
        }


@dataclass(frozen=True, slots=True)
class VectorProjectionJob:
    """Scheduler-addressable job for Qdrant projection behind adapter."""

    job_ref: str
    embedding_job_ref: str
    routing_plan: VectorPointRoutingPlan
    request_frame: VectorIndexingRouteFrameRef
    ack_frame: VectorIndexingRouteFrameRef
    operation: str = "upsert"

    def __post_init__(self) -> None:
        _require_typed_ref("job_ref", self.job_ref, required_prefixes=("projection-job:",))
        _require_typed_ref("embedding_job_ref", self.embedding_job_ref, required_prefixes=("embedding-job:",))
        if self.request_frame.frame_kind != "projection_request":
            raise ValueError("request_frame must be projection_request")
        if self.ack_frame.frame_kind != "projection_ack":
            raise ValueError("ack_frame must be projection_ack")
        if self.operation != "upsert":
            raise ValueError("operation must be upsert in 0128")

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _PROJECTION_JOB_SCHEMA,
            "job_ref": self.job_ref,
            "embedding_job_ref": self.embedding_job_ref,
            "routing_plan": self.routing_plan.to_mapping(),
            "request_frame": self.request_frame.to_mapping(),
            "ack_frame": self.ack_frame.to_mapping(),
            "operation": self.operation,
            "qdrant_adapter_executes_later": True,
            "qdrant_role": "projection and recall only",
            "qdrant_decides": False,
            "payload_refs": list(self.routing_plan.payload_refs),
            "collection_ref": self.routing_plan.collection_role.collection_ref,
            "collection_role": self.routing_plan.collection_role.role,
        }


@dataclass(frozen=True, slots=True)
class SchedulerVectorIndexingBatchCommand:
    """Command data the Scheduler can use to orchestrate vector indexing."""

    command_ref: str
    registry_ref: str
    route_root_ref: str
    dev_shm_root_path: str
    max_items: int = 128
    priority: int = 200

    def __post_init__(self) -> None:
        _require_typed_ref("command_ref", self.command_ref, required_prefixes=("command:", "scheduler-command:"))
        _require_typed_ref("registry_ref", self.registry_ref, required_prefixes=("vector-registry:",))
        _require_typed_ref("route_root_ref", self.route_root_ref, required_prefixes=("route:", "vector-route:"))
        if not self.dev_shm_root_path.startswith("/dev/shm/autodoc/routes/"):
            raise ValueError("dev_shm_root_path must start with /dev/shm/autodoc/routes/")
        if self.max_items <= 0:
            raise ValueError("max_items must be > 0")
        if not 0 <= self.priority <= 10_000:
            raise ValueError("priority must be between 0 and 10000")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _BATCH_COMMAND_SCHEMA,
            "command_ref": self.command_ref,
            "registry_ref": self.registry_ref,
            "route_root_ref": self.route_root_ref,
            "dev_shm_root_path": self.dev_shm_root_path,
            "max_items": self.max_items,
            "priority": self.priority,
            "scheduler_is_orchestrator": True,
            "route_dev_shm_multitask_interface": True,
            "bounded_indexing_batch": True,
        }


@dataclass(frozen=True, slots=True)
class VectorIndexingJobPlan:
    """Pure plan for Scheduler-driven embedding and projection jobs."""

    plan_ref: str
    batch_command: SchedulerVectorIndexingBatchCommand
    registry: VectorCollectionRegistry
    embedding_jobs: tuple[VectorEmbeddingJob, ...]
    projection_jobs: tuple[VectorProjectionJob, ...]
    observation_fact_refs: tuple[str, ...] = ()
    capped: bool = False

    def __post_init__(self) -> None:
        _require_typed_ref("plan_ref", self.plan_ref, required_prefixes=("vector-plan:",))
        object.__setattr__(self, "embedding_jobs", tuple(self.embedding_jobs))
        object.__setattr__(self, "projection_jobs", tuple(self.projection_jobs))
        object.__setattr__(self, "observation_fact_refs", _normalize_refs("observation_fact_refs", self.observation_fact_refs, allow_empty=True, required_prefixes=("bus:", "scheduler-trace:")))
        if len(self.embedding_jobs) != len(self.projection_jobs):
            raise ValueError("embedding_jobs and projection_jobs must have the same size")
        if len(self.embedding_jobs) > self.batch_command.max_items:
            raise ValueError("embedding_jobs must not exceed batch_command.max_items")

    @property
    def item_count(self) -> int:
        return len(self.embedding_jobs)

    @property
    def collection_refs(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(job.routing_plan.collection_role.collection_ref for job in self.projection_jobs))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _JOB_PLAN_SCHEMA,
            "plan_ref": self.plan_ref,
            "batch_command": self.batch_command.to_mapping(),
            "registry_ref": self.registry.registry_ref,
            "qdrant_instance_ref": self.registry.qdrant_instance_ref,
            "item_count": self.item_count,
            "capped": self.capped,
            "collection_refs": list(self.collection_refs),
            "embedding_jobs": [job.to_mapping() for job in self.embedding_jobs],
            "projection_jobs": [job.to_mapping() for job in self.projection_jobs],
            "observation_fact_refs": list(self.observation_fact_refs),
            "scheduler_is_orchestrator": True,
            "parallel_local_orchestrator": False,
            "e5_openvino_role": "embedding only behind adapter",
            "qdrant_role": "projection and recall only",
            "sql_is_authority": True,
            "github_exchange_only": True,
            "event_bus_observation_only": True,
        }


def build_vector_indexing_job_plan(
    items: tuple[VectorIndexableItem, ...],
    *,
    registry: VectorCollectionRegistry | None = None,
    command_ref: str = "scheduler-command:vector-indexing-batch",
    route_root_ref: str = "route:vector-indexing/default",
    dev_shm_root_path: str = "/dev/shm/autodoc/routes/vector-indexing/default",
    max_items: int = 128,
) -> VectorIndexingJobPlan:
    """Build a bounded plan; adapters execute E5/OpenVINO and Qdrant later."""

    if not items:
        raise ValueError("items must not be empty")
    active_registry = registry or build_default_vector_collection_registry()
    selected = items[:max_items]
    capped = len(items) > len(selected)
    batch_command = SchedulerVectorIndexingBatchCommand(
        command_ref=command_ref,
        registry_ref=active_registry.registry_ref,
        route_root_ref=route_root_ref,
        dev_shm_root_path=dev_shm_root_path,
        max_items=max_items,
    )
    embedding_jobs: list[VectorEmbeddingJob] = []
    projection_jobs: list[VectorProjectionJob] = []
    observation_refs: list[str] = [f"scheduler-trace:vector-indexing-batch-{_stable_suffix(command_ref)}"]
    for index, item in enumerate(selected, start=1):
        route_seed = _stable_suffix(f"{command_ref}|{index}|{item.item_ref}")
        route_prefix = f"{route_root_ref}/{route_seed}"
        path_prefix = f"{dev_shm_root_path}/{route_seed}"
        request_frame = VectorIndexingRouteFrameRef(
            route_ref=f"route-frame:embedding-request-{route_seed}",
            dev_shm_path=f"{path_prefix}/embedding-request.frame",
            frame_kind="embedding_request",
            source_ref=item.source_ref,
        )
        result_frame = VectorIndexingRouteFrameRef(
            route_ref=f"route-frame:embedding-result-{route_seed}",
            dev_shm_path=f"{path_prefix}/embedding-result.frame",
            frame_kind="embedding_result",
            source_ref=item.source_ref,
        )
        embedding_job = VectorEmbeddingJob(
            job_ref=f"embedding-job:{route_seed}",
            item=item,
            request_frame=request_frame,
            result_frame=result_frame,
            embedding_model_ref=active_registry.embedding_model_ref,
        )
        routing = active_registry.route_point(
            source_ref=item.source_ref,
            output_kind=item.output_kind,
            specialist_ref=item.specialist_ref,
        )
        projection_request = VectorIndexingRouteFrameRef(
            route_ref=f"route-frame:projection-request-{route_seed}",
            dev_shm_path=f"{path_prefix}/projection-request.frame",
            frame_kind="projection_request",
            source_ref=item.source_ref,
        )
        projection_ack = VectorIndexingRouteFrameRef(
            route_ref=f"route-frame:projection-ack-{route_seed}",
            dev_shm_path=f"{path_prefix}/projection-ack.frame",
            frame_kind="projection_ack",
            source_ref=item.source_ref,
        )
        projection_job = VectorProjectionJob(
            job_ref=f"projection-job:{route_seed}",
            embedding_job_ref=embedding_job.job_ref,
            routing_plan=routing,
            request_frame=projection_request,
            ack_frame=projection_ack,
        )
        embedding_jobs.append(embedding_job)
        projection_jobs.append(projection_job)
        observation_refs.append(f"bus:vector-indexing/{route_seed}/queued")
    seed = f"{command_ref}|{active_registry.registry_ref}|{','.join(item.item_ref for item in selected)}"
    return VectorIndexingJobPlan(
        plan_ref=f"vector-plan:indexing-job-{_stable_suffix(seed)}",
        batch_command=batch_command,
        registry=active_registry,
        embedding_jobs=tuple(embedding_jobs),
        projection_jobs=tuple(projection_jobs),
        observation_fact_refs=tuple(observation_refs),
        capped=capped,
    )


def build_indexable_item_from_mapping(
    *,
    source_ref: str,
    output_kind: str,
    text: str,
    embedding_role: str = "passage",
    specialist_ref: str | None = None,
    sql_authority_ref: str = "sql:context-store",
) -> VectorIndexableItem:
    prefix = f"{embedding_role}: "
    text_for_embedding = text if text.startswith(prefix) else f"{prefix}{text}"
    return VectorIndexableItem(
        source_ref=source_ref,
        output_kind=output_kind,
        text_for_embedding=text_for_embedding,
        embedding_role=embedding_role,
        specialist_ref=specialist_ref,
        sql_authority_ref=sql_authority_ref,
    )


def _require_typed_ref(name: str, value: str, *, required_prefixes: tuple[str, ...] = _ALLOWED_REF_PREFIXES) -> None:
    _require_non_empty(name, value)
    if not _TYPED_REF_RE.match(value):
        raise ValueError(f"{name} must be a typed ref")
    if required_prefixes and not value.startswith(required_prefixes):
        raise ValueError(f"{name} must start with one of {required_prefixes}")


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _require_prefixed_embedding_text(role: str, value: str) -> None:
    _require_non_empty("text_for_embedding", value)
    expected = f"{role}: "
    if not value.startswith(expected):
        raise ValueError(f"text_for_embedding must start with {expected!r}")


def _normalize_refs(
    name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
    required_prefixes: tuple[str, ...] = _ALLOWED_REF_PREFIXES,
) -> tuple[str, ...]:
    normalized = tuple(dict.fromkeys(values))
    if not allow_empty and not normalized:
        raise ValueError(f"{name} must not be empty")
    for value in normalized:
        _require_typed_ref(name, value, required_prefixes=required_prefixes)
    return normalized


def _normalize_metadata(values: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    normalized: list[tuple[str, str]] = []
    for key, value in values:
        _require_non_empty("metadata key", key)
        _require_non_empty("metadata value", value)
        normalized.append((key.strip(), value.strip()))
    return tuple(normalized)


def _stable_suffix(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
