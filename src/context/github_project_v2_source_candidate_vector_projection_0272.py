"""Project one durable ProjectV2 SourceCandidate through a locked E5 space.

0272-r9 composes the existing 0261 SQL -> OpenVINO/E5 surface and the existing
0262 embedding -> Qdrant projection surface.  It adds one immutable embedding
space profile and a compatibility gate before any Qdrant write.

Boundaries:
- SQL remains the durable authority and is read through the existing store;
- only locally produced 0261 embeddings are accepted by this composition;
- model/tokenizer/role/dimension/normalization/distance are checked explicitly;
- Qdrant receives ``sql_ref`` plus ``embedding_profile_ref`` in the payload;
- no GitHub mutation, laboratory selection, Scheduler.run or SHM change occurs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any, Callable, Mapping

from context.github_project_v2_source_candidate_durable_consumer_0272 import (
    DURABLE_CONSUMER_REPORT_SCHEMA,
)
from context.scheduler_managed_embedding_qdrant_projection_usage_0262 import (
    DEFAULT_COLLECTION,
    SchedulerManagedEmbeddingQdrantProjectionRequest,
    run_scheduler_managed_embedding_qdrant_projection_usage,
)
from context.scheduler_managed_sql_ref_openvino_embedding_usage_0261 import (
    DEFAULT_BACKEND_REF,
    DEFAULT_DIMENSION,
    SchedulerManagedSqlRefOpenVinoEmbeddingRequest,
    run_scheduler_managed_sql_ref_openvino_embedding_usage,
)

EMBEDDING_SPACE_PROFILE_SCHEMA = "missipy.embedding_space_profile.v1"
VECTOR_PROJECTION_REPORT_SCHEMA = (
    "missipy.github.project_v2_source_candidate_vector_projection_report.v1"
)
_EMBEDDING_SCHEMA = "missipy.scheduler_managed_sql_ref_openvino_embedding.v1"
_ALLOWED_ROLES = frozenset({"passage", "query"})


@dataclass(frozen=True, slots=True)
class EmbeddingSpaceProfile:
    """Immutable identity of one compatible vector space."""

    backend_ref: str = DEFAULT_BACKEND_REF
    model_ref: str = "openvino.embedding.e5-small"
    model_revision: str = "local-openvino-export"
    tokenizer_ref: str = "transformers.multilingual-e5-small"
    pooling: str = "mean"
    normalized: bool = True
    dimension: int = DEFAULT_DIMENSION
    distance: str = "Cosine"
    role: str = "passage"
    prefix_policy: str = "e5-query-passage"
    max_length: int = 128
    padding: str = "max_length"
    truncation: str = "longest_first"
    requires_token_type_ids: bool = True
    collection_name: str = DEFAULT_COLLECTION
    model_artifact_digest: str = ""

    def __post_init__(self) -> None:
        for name in (
            "backend_ref",
            "model_ref",
            "model_revision",
            "tokenizer_ref",
            "pooling",
            "prefix_policy",
            "padding",
            "truncation",
            "collection_name",
        ):
            value = str(getattr(self, name))
            if not value.strip():
                raise ValueError(f"{name} must not be empty")
        if self.dimension <= 0:
            raise ValueError("dimension must be > 0")
        if self.distance != "Cosine":
            raise ValueError("the current 0262 projection path requires Cosine distance")
        if self.role not in _ALLOWED_ROLES:
            raise ValueError("role must be passage or query")
        if self.normalized is not True:
            raise ValueError("the current projection path requires normalized vectors")
        if self.pooling != "mean":
            raise ValueError("the current E5 pipeline requires mean pooling")
        if self.prefix_policy != "e5-query-passage":
            raise ValueError("the current E5 pipeline requires e5-query-passage prefixes")
        if self.max_length != 128:
            raise ValueError("the current 0261 E5 profile requires max_length=128")
        if self.padding != "max_length":
            raise ValueError("the current E5 profile requires max_length padding")
        if self.truncation != "longest_first":
            raise ValueError("the current E5 profile requires longest_first truncation")
        if self.requires_token_type_ids is not True:
            raise ValueError("the current E5 profile requires token_type_ids")
        if self.model_artifact_digest and not self.model_artifact_digest.startswith(
            "sha256:"
        ):
            raise ValueError("model_artifact_digest must be empty or start with sha256:")

    @property
    def profile_ref(self) -> str:
        digest = hashlib.sha256(
            _canonical_json(self._identity_mapping()).encode("utf-8")
        ).hexdigest()
        return f"embedding-space:{digest[:24]}"

    def _identity_mapping(self) -> dict[str, Any]:
        return {
            "backend_ref": self.backend_ref,
            "model_ref": self.model_ref,
            "model_revision": self.model_revision,
            "tokenizer_ref": self.tokenizer_ref,
            "pooling": self.pooling,
            "normalized": self.normalized,
            "dimension": self.dimension,
            "distance": self.distance,
            "role": self.role,
            "prefix_policy": self.prefix_policy,
            "max_length": self.max_length,
            "padding": self.padding,
            "truncation": self.truncation,
            "requires_token_type_ids": self.requires_token_type_ids,
            "collection_name": self.collection_name,
            "model_artifact_digest": self.model_artifact_digest,
        }

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": EMBEDDING_SPACE_PROFILE_SCHEMA,
            "profile_ref": self.profile_ref,
            **self._identity_mapping(),
        }


@dataclass(frozen=True, slots=True)
class EmbeddingCompatibilityResult:
    """Serializable compatibility decision before Qdrant projection."""

    compatible: bool
    issues: tuple[str, ...]
    profile_ref: str
    sql_ref: str
    embedding_ref: str
    observed: Mapping[str, Any] = field(default_factory=dict)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "compatible": self.compatible,
            "issues": list(self.issues),
            "profile_ref": self.profile_ref,
            "sql_ref": self.sql_ref,
            "embedding_ref": self.embedding_ref,
            "observed": dict(self.observed),
        }


@dataclass(frozen=True, slots=True)
class GitHubProjectV2VectorProjectionCommand:
    """Controlled r9 command."""

    execute: bool = False
    policy_decision_id: str = ""
    model_dir: str | None = None
    device: str = "CPU"


@dataclass(frozen=True, slots=True)
class GitHubProjectV2VectorProjectionResult:
    """Closed r9 result with explicit effect boundaries."""

    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    sql_ref: str
    profile: Mapping[str, Any]
    embedding: Mapping[str, Any] = field(default_factory=dict)
    compatibility: Mapping[str, Any] = field(default_factory=dict)
    projection: Mapping[str, Any] = field(default_factory=dict)
    openvino_call_performed: bool = False
    qdrant_write_performed: bool = False
    boundaries: Mapping[str, bool] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": VECTOR_PROJECTION_REPORT_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "policy_decision_id": self.policy_decision_id,
            "sql_ref": self.sql_ref,
            "profile": dict(self.profile),
            "embedding": dict(self.embedding),
            "compatibility": dict(self.compatibility),
            "projection": dict(self.projection),
            "openvino_call_performed": self.openvino_call_performed,
            "qdrant_write_performed": self.qdrant_write_performed,
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"projectv2_vector_projection_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"execute={self.execute}",
                f"sql_ref={self.sql_ref or '-'}",
                f"profile_ref={self.profile.get('profile_ref', '-')}",
                f"openvino_call_performed={self.openvino_call_performed}",
                f"qdrant_write_performed={self.qdrant_write_performed}",
                "sql_remains_authority=True",
                "laboratory_selected=False",
            )
        )


def validate_durable_r8_report(report: Mapping[str, Any]) -> tuple[str, ...]:
    """Require an executed and rehydrated 0272-r8 durable result."""

    issues: list[str] = []
    if str(report.get("schema", "")) != DURABLE_CONSUMER_REPORT_SCHEMA:
        issues.append("r8 durable report schema mismatch")
    if report.get("valid") is not True:
        issues.append("r8 durable report must be valid")
    if report.get("execute") is not True:
        issues.append("r8 durable report must come from execute mode")
    if report.get("rehydrated") is not True:
        issues.append("r8 durable report must have successful SQL readback")
    sql_ref = str(report.get("sql_ref", ""))
    if not sql_ref.startswith("sql:"):
        issues.append("r8 sql_ref must start with sql:")
    durable = _mapping(report.get("durable_record"))
    readback = _mapping(report.get("readback_record"))
    if str(durable.get("context_ref", "")) != sql_ref:
        issues.append("r8 durable_record.context_ref must match sql_ref")
    if str(readback.get("context_ref", "")) != sql_ref:
        issues.append("r8 readback_record.context_ref must match sql_ref")
    boundaries = _mapping(report.get("boundaries"))
    if boundaries.get("qdrant_write_performed") is not False:
        issues.append("r8 must not have performed a Qdrant write")
    if boundaries.get("remote_mutation_allowed") is not False:
        issues.append("r8 must keep remote mutation closed")
    return tuple(dict.fromkeys(issues))


def validate_embedding_against_profile(
    embedding: Mapping[str, Any],
    profile: EmbeddingSpaceProfile,
    *,
    expected_sql_ref: str,
) -> EmbeddingCompatibilityResult:
    """Reject any embedding that is not in the declared vector space."""

    issues: list[str] = []
    metadata = _mapping(embedding.get("metadata"))
    vector = embedding.get("vector")
    sql_ref = str(embedding.get("sql_ref", ""))
    embedding_ref = str(embedding.get("embedding_ref", ""))

    if str(embedding.get("schema", "")) != _EMBEDDING_SCHEMA:
        issues.append("embedding schema mismatch")
    if sql_ref != expected_sql_ref:
        issues.append("embedding sql_ref does not match the durable SQL ref")
    if str(embedding.get("source_ref", "")) != f"ctx-fragment:{expected_sql_ref}":
        issues.append("embedding source_ref does not match the durable SQL ref")
    if str(embedding.get("backend_ref", "")) != profile.backend_ref:
        issues.append("embedding backend_ref is incompatible with profile")
    if str(embedding.get("role", "")) != profile.role:
        issues.append("embedding role is incompatible with profile")
    if embedding.get("dimension") != profile.dimension:
        issues.append("embedding dimension is incompatible with profile")
    if embedding.get("normalized") is not profile.normalized:
        issues.append("embedding normalization is incompatible with profile")
    if not isinstance(vector, list) or len(vector) != profile.dimension:
        issues.append("embedding vector length is incompatible with profile")
    l2_norm = embedding.get("l2_norm")
    if not isinstance(l2_norm, (int, float)) or not math.isclose(
        float(l2_norm), 1.0, rel_tol=1e-4, abs_tol=1e-4
    ):
        issues.append("embedding l2_norm is not compatible with normalized profile")
    if str(metadata.get("model", "")) != profile.model_ref:
        issues.append("embedding model is incompatible with profile")
    if str(metadata.get("tokenizer", "")) != profile.tokenizer_ref:
        issues.append("embedding tokenizer is incompatible with profile")
    observed_revision = str(metadata.get("model_revision", ""))
    if observed_revision and observed_revision != profile.model_revision:
        issues.append("embedding model revision is incompatible with profile")
    if profile.model_artifact_digest and str(
        metadata.get("model_artifact_digest", "")
    ) != profile.model_artifact_digest:
        issues.append("embedding model artifact digest is incompatible with profile")

    observed = {
        "backend_ref": str(embedding.get("backend_ref", "")),
        "model_ref": str(metadata.get("model", "")),
        "tokenizer_ref": str(metadata.get("tokenizer", "")),
        "model_revision": observed_revision,
        "role": str(embedding.get("role", "")),
        "dimension": embedding.get("dimension"),
        "normalized": embedding.get("normalized"),
        "l2_norm": l2_norm,
    }
    return EmbeddingCompatibilityResult(
        compatible=not issues,
        issues=tuple(dict.fromkeys(issues)),
        profile_ref=profile.profile_ref,
        sql_ref=sql_ref,
        embedding_ref=embedding_ref,
        observed=observed,
    )


def attach_profile_to_embedding(
    embedding: Mapping[str, Any], profile: EmbeddingSpaceProfile
) -> dict[str, Any]:
    """Attach profile provenance before the existing 0262 point builder."""

    payload = json.loads(json.dumps(dict(embedding)))
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    else:
        # The existing OpenVINO adapter requires every metadata value to be
        # non-empty.  Optional producer metadata such as ``model_path`` may be
        # represented by an empty string when no local path was supplied.  It
        # is not part of the vector-space identity, so remove it rather than
        # weakening the adapter contract or inventing a sentinel value.
        metadata = {
            key: value
            for key, value in metadata.items()
            if not (isinstance(value, str) and not value.strip())
        }
    payload["metadata"] = metadata
    additions = {
        "embedding_profile_ref": profile.profile_ref,
        "embedding_model_revision": profile.model_revision,
        "embedding_pooling": profile.pooling,
        "embedding_distance": profile.distance,
        "embedding_prefix_policy": profile.prefix_policy,
        "embedding_max_length": str(profile.max_length),
        "embedding_padding": profile.padding,
        "embedding_truncation": profile.truncation,
        "embedding_requires_token_type_ids": str(profile.requires_token_type_ids).lower(),
        "embedding_collection": profile.collection_name,
    }
    if profile.model_artifact_digest:
        additions["model_artifact_digest"] = profile.model_artifact_digest
    for key, value in additions.items():
        existing = metadata.get(key)
        if existing not in (None, "", value):
            raise ValueError(f"embedding metadata collision for {key}")
        metadata[key] = value
    return payload


def run_project_v2_source_candidate_vector_projection(
    durable_report: Mapping[str, Any],
    store: Any,
    command: GitHubProjectV2VectorProjectionCommand,
    *,
    profile: EmbeddingSpaceProfile | None = None,
    embedder: Callable[..., Mapping[str, Any]] | None = None,
    qdrant_executor: Any | None = None,
) -> GitHubProjectV2VectorProjectionResult:
    """Compose r8 -> 0261 -> compatibility gate -> 0262."""

    effective_profile = profile or EmbeddingSpaceProfile()
    issues = list(validate_durable_r8_report(durable_report))
    if store is None:
        issues.append("an existing SQLContextStore object is required")
    if command.execute and not command.policy_decision_id.strip():
        issues.append("policy_decision_id is required for execute mode")
    if command.execute and qdrant_executor is None:
        issues.append("execute mode requires an injected Qdrant executor")
    sql_ref = str(durable_report.get("sql_ref", ""))
    if issues:
        return _result(
            issues=issues,
            command=command,
            sql_ref=sql_ref,
            profile=effective_profile,
        )

    embedding_request = SchedulerManagedSqlRefOpenVinoEmbeddingRequest(
        sql_ref=sql_ref,
        role=effective_profile.role,
        policy_decision_id=command.policy_decision_id,
        model_dir=command.model_dir,
        device=command.device,
    )
    embedding_result = run_scheduler_managed_sql_ref_openvino_embedding_usage(
        store,
        embedding_request,
        execute=command.execute,
        embedder=embedder,
    )
    embedding_report = embedding_result.to_mapping()
    if not embedding_result.valid:
        issues.extend(embedding_result.issues)
        return _result(
            issues=issues,
            command=command,
            sql_ref=sql_ref,
            profile=effective_profile,
            embedding=embedding_report,
        )

    if not command.execute:
        return _result(
            issues=(),
            command=command,
            sql_ref=sql_ref,
            profile=effective_profile,
            embedding=embedding_report,
        )

    embedding = _mapping(embedding_report.get("embedding"))
    compatibility = validate_embedding_against_profile(
        embedding,
        effective_profile,
        expected_sql_ref=sql_ref,
    )
    if not compatibility.compatible:
        return _result(
            issues=compatibility.issues,
            command=command,
            sql_ref=sql_ref,
            profile=effective_profile,
            embedding=embedding_report,
            compatibility=compatibility.to_mapping(),
            openvino_call_performed=True,
        )

    profiled_embedding = attach_profile_to_embedding(embedding, effective_profile)
    profiled_report = dict(embedding_report)
    profiled_report["embedding"] = profiled_embedding
    projection_request = SchedulerManagedEmbeddingQdrantProjectionRequest(
        policy_decision_id=command.policy_decision_id,
        collection_name=effective_profile.collection_name,
        vector_dimension=effective_profile.dimension,
    )
    projection_result = run_scheduler_managed_embedding_qdrant_projection_usage(
        profiled_report,
        projection_request,
        execute=True,
        executor=qdrant_executor,
    )
    projection_report = projection_result.to_mapping()
    if not projection_result.valid:
        issues.extend(projection_result.issues)
    qdrant_write_performed = bool(
        _mapping(projection_report.get("write_result")).get("acknowledged") is True
    )
    if not qdrant_write_performed:
        issues.append("Qdrant projection was not acknowledged")

    return _result(
        issues=issues,
        command=command,
        sql_ref=sql_ref,
        profile=effective_profile,
        embedding=profiled_report,
        compatibility=compatibility.to_mapping(),
        projection=projection_report,
        openvino_call_performed=True,
        qdrant_write_performed=qdrant_write_performed,
    )


def _result(
    *,
    issues: Any,
    command: GitHubProjectV2VectorProjectionCommand,
    sql_ref: str,
    profile: EmbeddingSpaceProfile,
    embedding: Mapping[str, Any] | None = None,
    compatibility: Mapping[str, Any] | None = None,
    projection: Mapping[str, Any] | None = None,
    openvino_call_performed: bool = False,
    qdrant_write_performed: bool = False,
) -> GitHubProjectV2VectorProjectionResult:
    normalized_issues = tuple(dict.fromkeys(str(item) for item in issues if str(item)))
    return GitHubProjectV2VectorProjectionResult(
        valid=not normalized_issues,
        issues=normalized_issues,
        execute=command.execute,
        policy_decision_id=command.policy_decision_id,
        sql_ref=sql_ref,
        profile=profile.to_mapping(),
        embedding=dict(embedding or {}),
        compatibility=dict(compatibility or {}),
        projection=dict(projection or {}),
        openvino_call_performed=openvino_call_performed,
        qdrant_write_performed=qdrant_write_performed,
        boundaries={
            "sql_read_allowed": True,
            "sql_write_performed": False,
            "openvino_call_allowed": command.execute,
            "openvino_call_performed": openvino_call_performed,
            "qdrant_write_allowed": command.execute,
            "qdrant_write_performed": qdrant_write_performed,
            "external_embedding_accepted": False,
            "remote_mutation_allowed": False,
            "laboratory_selection_allowed": False,
            "scheduler_run_modified": False,
            "shm_touched": False,
            "sql_remains_authority": True,
        },
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
