"""Correlated operational evidence for the complete phase 0284 chain.

Phase 0284-r9 does not execute a second specialist, Scheduler, SQL, OpenVINO,
Qdrant, GitHub or ProjectV2 path.  It validates the stable JSON projection of
one already executed 0284-r7 integrated smoke, derives the immutable r8
operational evidence and asks the existing r8 closure audit for the decision.

Repository reads and report writes belong to the thin CLI adapter.  This
module is deterministic, standard-library only and effect free.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
from typing import Any

from context.specialists_laboratories_chain_closure_audit_0284 import (
    Phase0284ClosureAuditResult,
    Phase0284OperationalEvidence,
    audit_specialists_laboratories_chain_closure,
)

SPECIALISTS_LABORATORIES_LIVE_PATH_EVIDENCE_VERSION = "0284.r9"
SPECIALISTS_LABORATORIES_LIVE_PATH_EVIDENCE_COMMAND_SCHEMA = (
    "missipy.specialists_laboratories.live_path_evidence_command.v1"
)
SPECIALISTS_LABORATORIES_LIVE_PATH_EVIDENCE_RESULT_SCHEMA = (
    "missipy.specialists_laboratories.live_path_evidence_result.v1"
)
PROJECTS_COPILOT_SPECIALIST_RESULT_SCHEMA = (
    "missipy.github.projects_copilot_specialist_smoke_result.v1"
)
EXPECTED_E5_DIMENSION = 384


class SpecialistsLaboratoriesLivePathEvidenceError(ValueError):
    """Raised when an evidence command is structurally invalid."""


@dataclass(frozen=True, slots=True)
class SpecialistsLaboratoriesLivePathEvidenceCommand:
    """Expected identity of one correlated real r7 execution."""

    evidence_ref: str
    repository: str
    run_id: str
    source_revision: str
    expected_vector_dimension: int = EXPECTED_E5_DIMENSION
    schema: str = SPECIALISTS_LABORATORIES_LIVE_PATH_EVIDENCE_COMMAND_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SPECIALISTS_LABORATORIES_LIVE_PATH_EVIDENCE_COMMAND_SCHEMA:
            raise SpecialistsLaboratoriesLivePathEvidenceError(
                "unsupported live-path evidence command schema"
            )
        for name in ("evidence_ref", "repository", "run_id", "source_revision"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise SpecialistsLaboratoriesLivePathEvidenceError(
                    f"{name} must be a non-empty string"
                )
        if "/" not in self.repository:
            raise SpecialistsLaboratoriesLivePathEvidenceError(
                "repository must be owner/name"
            )
        if self.expected_vector_dimension != EXPECTED_E5_DIMENSION:
            raise SpecialistsLaboratoriesLivePathEvidenceError(
                "multilingual-e5-small evidence dimension must be exactly 384"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "evidence_ref": self.evidence_ref,
            "repository": self.repository,
            "run_id": self.run_id,
            "source_revision": self.source_revision,
            "expected_vector_dimension": self.expected_vector_dimension,
            "remote_mutation_allowed": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistsLaboratoriesLivePathEvidenceResult:
    """Deterministic evidence envelope and r8 closure decision."""

    valid: bool
    issues: tuple[str, ...]
    command: SpecialistsLaboratoriesLivePathEvidenceCommand
    operational_evidence: Phase0284OperationalEvidence
    closure_audit: Phase0284ClosureAuditResult
    integrated_result_digest: str
    evidence_digest: str
    policy_decision_id: str = ""
    candidate_id: str = ""
    sql_ref: str = ""
    vector_dimensions: tuple[int, ...] = ()
    correlation_refs: tuple[str, ...] = ()
    source_file_count: int = 0
    integrated_result: Mapping[str, Any] = field(default_factory=dict)
    schema: str = SPECIALISTS_LABORATORIES_LIVE_PATH_EVIDENCE_RESULT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SPECIALISTS_LABORATORIES_LIVE_PATH_EVIDENCE_RESULT_SCHEMA:
            raise SpecialistsLaboratoriesLivePathEvidenceError(
                "unsupported live-path evidence result schema"
            )
        if self.valid != (not self.issues and self.closure_audit.phase_0284_closed):
            raise SpecialistsLaboratoriesLivePathEvidenceError(
                "valid must match issue-free phase closure"
            )

    @property
    def phase_0284_closed(self) -> bool:
        return self.valid and self.closure_audit.phase_0284_closed

    @property
    def live_path_status(self) -> str:
        if self.phase_0284_closed:
            return "green"
        if not self.closure_audit.valid:
            return "red"
        return "transition"

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "issues": list(self.issues),
            "command": self.command.to_mapping(),
            "operational_evidence": self.operational_evidence.to_mapping(),
            "closure_audit": self.closure_audit.to_mapping(),
            "integrated_result_digest": self.integrated_result_digest,
            "evidence_digest": self.evidence_digest,
            "policy_decision_id": self.policy_decision_id,
            "candidate_id": self.candidate_id,
            "sql_ref": self.sql_ref,
            "vector_dimensions": list(self.vector_dimensions),
            "correlation_refs": list(self.correlation_refs),
            "source_file_count": self.source_file_count,
            "integrated_result": _json_value(self.integrated_result),
            "phase_0284_closed": self.phase_0284_closed,
            "live_path_status": self.live_path_status,
            "live_path_uses_real_backend": self.phase_0284_closed,
            "existing_scheduler_remains_orchestrator": True,
            "new_scheduler_added": False,
            "new_laboratory_manager_added": False,
            "sql_remains_authority": True,
            "qdrant_projection_recall_only": True,
            "eventbus_observation_only": True,
            "github_mutation_performed": False,
            "projectv2_mutation_performed": False,
        }


def build_specialists_laboratories_live_path_evidence(
    command: SpecialistsLaboratoriesLivePathEvidenceCommand,
    integrated_result: Mapping[str, Any],
    sources: Mapping[str, str],
) -> SpecialistsLaboratoriesLivePathEvidenceResult:
    """Validate one r7 result and close r8 only with correlated real evidence."""

    if not isinstance(command, SpecialistsLaboratoriesLivePathEvidenceCommand):
        raise TypeError(
            "command must be SpecialistsLaboratoriesLivePathEvidenceCommand"
        )
    if not isinstance(integrated_result, Mapping):
        raise TypeError("integrated_result must be a mapping")
    if not isinstance(sources, Mapping):
        raise TypeError("sources must be a mapping")

    result = _json_mapping(integrated_result)
    command_mapping = _mapping(result.get("command"))
    memory_command = _mapping(command_mapping.get("memory"))
    memory = _mapping(result.get("memory"))
    publication_preview = _mapping(result.get("publication_preview"))
    assembly = _mapping(result.get("assembly"))
    intake = _mapping(assembly.get("intake"))
    candidate = _mapping(intake.get("source_candidate"))

    issues: list[str] = []
    _expect_equal(
        issues,
        "integrated result schema",
        result.get("schema"),
        PROJECTS_COPILOT_SPECIALIST_RESULT_SCHEMA,
    )
    _expect_equal(
        issues,
        "repository",
        command_mapping.get("repository"),
        command.repository,
    )
    _expect_equal(issues, "run_id", str(command_mapping.get("run_id", "")), command.run_id)

    required_integrated_flags = (
        "valid",
        "artifact_correlation_verified",
        "advisory_context_injected",
        "source_candidate_injected",
        "request_authoritative",
        "advisory_used_as_hint_only",
        "real_memory_closed",
        "publication_plan_ready",
        "projects_projection_ready",
        "integrated_closed_loop_complete",
        "existing_scheduler_used",
    )
    for name in required_integrated_flags:
        if result.get(name) is not True:
            issues.append(f"integrated result requires {name}=true")
    if result.get("issues") not in ([], ()):
        issues.append("integrated result must be issue-free")

    forbidden_integrated_flags = (
        "scheduler_created",
        "scheduler_modified",
        "parallel_orchestrator_created",
        "github_mutation_performed",
        "projectv2_mutation_performed",
    )
    for name in forbidden_integrated_flags:
        if result.get(name) is not False:
            issues.append(f"integrated result requires {name}=false")

    required_memory_flags = (
        "valid",
        "real_sql_authority_used",
        "real_openvino_e5_used",
        "real_qdrant_projection_used",
        "real_qdrant_recall_used",
        "qdrant_returns_references_only",
        "sql_rehydration_verified",
        "portable_identity_preserved",
        "memory_closed",
        "persistent_qdrant_point_created",
        "existing_scheduler_used",
    )
    for name in required_memory_flags:
        if memory.get(name) is not True:
            issues.append(f"memory result requires {name}=true")
    if memory.get("issues") not in ([], ()):
        issues.append("memory result must be issue-free")
    if memory.get("preview_only") is not False:
        issues.append("memory result must be an executed path, not a preview")
    for name in (
        "automatic_cleanup_performed",
        "scheduler_created",
        "scheduler_modified",
        "new_qdrant_executor_added",
        "new_transport_added",
        "github_mutation_performed",
        "embedding_runtime_injected",
    ):
        if memory.get(name) is not False:
            issues.append(f"memory result requires {name}=false")

    if memory_command.get("execute") is not True:
        issues.append("r7 memory command must have execute=true")
    if memory_command.get("authorize_real_memory") is not True:
        issues.append("real memory execution must be explicitly authorised")
    if memory_command.get("authorize_persistent_qdrant_point") is not True:
        issues.append("persistent Qdrant point must be explicitly authorised")

    vector_dimensions = tuple(
        value
        for value in _values_for_key(memory_command, "vector_dimension")
        if isinstance(value, int) and not isinstance(value, bool)
    )
    if not vector_dimensions:
        issues.append("memory command must expose its Qdrant vector dimension")
    elif any(value != command.expected_vector_dimension for value in vector_dimensions):
        issues.append("all Qdrant vector dimensions must be exactly 384")

    policy_decision_id = _text(command_mapping.get("policy_decision_id"))
    if not policy_decision_id:
        issues.append("integrated command must expose policy_decision_id")
    policy_ids = tuple(
        _text(value)
        for value in _values_for_key(memory_command, "policy_decision_id")
        if _text(value)
    )
    if policy_decision_id and (
        not policy_ids or any(value != policy_decision_id for value in policy_ids)
    ):
        issues.append("GitHub, SQL and Qdrant paths must share policy_decision_id")

    sql_ref = _text(memory.get("sql_ref"))
    if not sql_ref.startswith("sql:"):
        issues.append("real memory evidence must expose a durable sql_ref")
    if _text(publication_preview.get("laboratory_source_sql_ref")) != sql_ref:
        issues.append("publication preview must correlate the same sql_ref")

    candidate_id = _text(candidate.get("candidate_id"))
    if not candidate_id:
        issues.append("assembled intake must expose source candidate identity")

    correlation_refs = _unique_text(
        (
            command.evidence_ref,
            f"github-run:{command.repository}:{command.run_id}",
            policy_decision_id,
            candidate_id,
            sql_ref,
            _text(memory.get("passage_embedding_ref")),
            _text(memory.get("query_embedding_ref")),
        )
    )

    operational_evidence = Phase0284OperationalEvidence(
        fake_specialist_scheduler_closed=bool(
            memory.get("specialist_smoke")
            and memory.get("existing_scheduler_used") is True
        ),
        existing_scheduler_path_verified=_nested_bool(
            memory, "specialist_smoke", "existing_scheduler_path_verified"
        ),
        real_sql_authority_used=memory.get("real_sql_authority_used") is True,
        real_openvino_e5_used=memory.get("real_openvino_e5_used") is True,
        real_qdrant_projection_used=(
            memory.get("real_qdrant_projection_used") is True
        ),
        real_qdrant_recall_used=memory.get("real_qdrant_recall_used") is True,
        qdrant_returns_references_only=(
            memory.get("qdrant_returns_references_only") is True
        ),
        sql_rehydration_verified=memory.get("sql_rehydration_verified") is True,
        portable_identity_preserved=(
            memory.get("portable_identity_preserved") is True
        ),
        artifact_correlation_verified=(
            result.get("artifact_correlation_verified") is True
        ),
        advisory_context_injected=result.get("advisory_context_injected") is True,
        source_candidate_injected=result.get("source_candidate_injected") is True,
        integrated_closed_loop_complete=(
            result.get("integrated_closed_loop_complete") is True
        ),
        publication_plan_ready=result.get("publication_plan_ready") is True,
        projects_projection_ready=result.get("projects_projection_ready") is True,
        github_mutation_performed=result.get("github_mutation_performed") is not False,
        projectv2_mutation_performed=(
            result.get("projectv2_mutation_performed") is not False
        ),
    )
    if not operational_evidence.green:
        issues.append("derived r8 operational evidence is not green")

    normalized_sources = {str(path): str(text) for path, text in sources.items()}
    closure = audit_specialists_laboratories_chain_closure(
        normalized_sources,
        operational_evidence,
    )
    issues.extend(closure.issues)
    if not closure.phase_0284_closed:
        issues.append("r8 closure audit did not close phase 0284")

    normalized_issues = _unique_text(issues)
    integrated_digest = _digest(result)
    evidence_payload = {
        "command": command.to_mapping(),
        "integrated_result_digest": integrated_digest,
        "operational_evidence": operational_evidence.to_mapping(),
        "closure_audit": closure.to_mapping(),
        "policy_decision_id": policy_decision_id,
        "candidate_id": candidate_id,
        "sql_ref": sql_ref,
        "vector_dimensions": list(vector_dimensions),
        "correlation_refs": list(correlation_refs),
    }
    evidence_digest = _digest(evidence_payload)
    valid = not normalized_issues and closure.phase_0284_closed
    return SpecialistsLaboratoriesLivePathEvidenceResult(
        valid=valid,
        issues=normalized_issues,
        command=command,
        operational_evidence=operational_evidence,
        closure_audit=closure,
        integrated_result_digest=integrated_digest,
        evidence_digest=evidence_digest,
        policy_decision_id=policy_decision_id,
        candidate_id=candidate_id,
        sql_ref=sql_ref,
        vector_dimensions=vector_dimensions,
        correlation_refs=correlation_refs,
        source_file_count=len(normalized_sources),
        integrated_result=result,
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _json_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    normalized = _json_value(value)
    if not isinstance(normalized, dict):
        raise TypeError("integrated_result must normalize to a JSON object")
    return normalized


def _json_value(value: object) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"evidence contains non-JSON value: {type(value).__name__}")


def _values_for_key(value: object, key: str) -> tuple[object, ...]:
    found: list[object] = []
    if isinstance(value, Mapping):
        for current_key, item in value.items():
            if str(current_key) == key:
                found.append(item)
            found.extend(_values_for_key(item, key))
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for item in value:
            found.extend(_values_for_key(item, key))
    return tuple(found)


def _nested_bool(mapping: Mapping[str, Any], *path: str) -> bool:
    current: object = mapping
    for key in path:
        if not isinstance(current, Mapping):
            return False
        current = current.get(key)
    return current is True


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _expect_equal(
    issues: list[str], name: str, actual: object, expected: object
) -> None:
    if actual != expected:
        issues.append(f"{name} mismatch: expected {expected!r}")


def _unique_text(values: Sequence[object]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(text for value in values if (text := _text(value))))


def _digest(value: object) -> str:
    payload = json.dumps(
        _json_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


__all__ = (
    "SPECIALISTS_LABORATORIES_LIVE_PATH_EVIDENCE_VERSION",
    "SPECIALISTS_LABORATORIES_LIVE_PATH_EVIDENCE_COMMAND_SCHEMA",
    "SPECIALISTS_LABORATORIES_LIVE_PATH_EVIDENCE_RESULT_SCHEMA",
    "EXPECTED_E5_DIMENSION",
    "SpecialistsLaboratoriesLivePathEvidenceCommand",
    "SpecialistsLaboratoriesLivePathEvidenceError",
    "SpecialistsLaboratoriesLivePathEvidenceResult",
    "build_specialists_laboratories_live_path_evidence",
)
