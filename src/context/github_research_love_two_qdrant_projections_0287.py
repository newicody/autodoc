"""Project the two persisted specialist analyses separately into live Qdrant.

The r16-r12 unit keeps both analyses as distinct immutable SQL authority
objects.  This unit builds two independent plans and delegates each write,
readback and SQL rehydration to the existing live projection probe.

The existing probe is the only component allowed to:
- invoke the injected OpenVINO/E5 projection port;
- write one Qdrant point;
- persist VectorProjectionMetadata in SQL;
- read a reference-only Qdrant payload;
- rehydrate the authoritative object from SQL.

This unit creates no embedding backend, Qdrant client, SQL connection,
Scheduler or synthesis.  It never serializes the authoritative body or vectors
into its result.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import hashlib
import json
from types import MappingProxyType
from typing import Any

from context.github_research_love_sql_persistence_0287 import (
    RECEIPT_SCHEMA as SQL_PERSISTENCE_RECEIPT_SCHEMA,
    RESULT_SCHEMA as SQL_PERSISTENCE_RESULT_SCHEMA,
)
from context.love_imported_actions_runtime_contract_0287 import (
    ImportedActionsRuntimePorts,
    validate_imported_actions_runtime_ports,
)
from context.love_qdrant_live_analysis_projection_0287 import (
    LoveQdrantLiveProjectionIdentity,
    build_love_qdrant_live_projection_identity_from_refs,
)
from context.love_live_qdrant_projection_probe_0287 import (
    ReferencePointReader,
    LoveLiveProjectionProbeGate,
    LoveLiveProjectionProbePlan,
    LoveLiveProjectionProbeReceipt,
    LoveLiveProjectionProbeRequest,
    build_love_live_projection_probe_plan,
    execute_love_live_projection_probe,
    inspect_love_live_projection_probe,
)

PLAN_SCHEMA = "missipy.github.research_love_two_qdrant_projection_plan.v1"
READINESS_SCHEMA = (
    "missipy.github.research_love_two_qdrant_projection_readiness.v1"
)
RECEIPT_SCHEMA = "missipy.github.research_love_two_qdrant_projection_receipt.v1"
RESULT_SCHEMA = "missipy.github.research_love_two_qdrant_projection_result.v1"


class GitHubResearchLoveTwoProjectionError(RuntimeError):
    """Raised when the two independent projections cannot fail closed."""


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveTwoProjectionCommand:
    """Explicit live projection inputs for one persisted analysis pair."""

    runtime_ports: ImportedActionsRuntimePorts
    sql_persistence: Mapping[str, Any]
    reference_point_reader: ReferencePointReader
    branch_ref: str
    project_ref: str
    conversation_ref: str
    security_scope: str
    dense_vector_name: str
    sparse_vector_name: str
    projected_at: str = ""
    allow_write: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.sql_persistence, Mapping):
            raise TypeError("sql_persistence must be a mapping")
        for name in (
            "branch_ref",
            "project_ref",
            "conversation_ref",
            "security_scope",
        ):
            _require_typed_ref(name, getattr(self, name))
        for name in ("dense_vector_name", "sparse_vector_name"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise GitHubResearchLoveTwoProjectionError(
                    f"{name} must not be empty"
                )
            object.__setattr__(self, name, value.strip())
        if self.dense_vector_name == self.sparse_vector_name:
            raise GitHubResearchLoveTwoProjectionError(
                "dense and sparse vector names must differ"
            )
        if self.projected_at and (
            "T" not in self.projected_at
            or not self.projected_at.endswith("Z")
        ):
            raise GitHubResearchLoveTwoProjectionError(
                "projected_at must be empty or a UTC timestamp ending with Z"
            )


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveTwoProjectionPlan:
    """Two distinct existing-probe plans under one deterministic pair digest."""

    schema: str
    work_package_ref: str
    sql_persistence_plan_digest: str
    first: LoveLiveProjectionProbePlan
    second: LoveLiveProjectionProbePlan
    pair_plan_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema != PLAN_SCHEMA:
            raise GitHubResearchLoveTwoProjectionError(
                "unsupported two-projection plan schema"
            )
        if not self.work_package_ref.startswith("research-work-package:"):
            raise GitHubResearchLoveTwoProjectionError(
                "work_package_ref must start with research-work-package:"
            )
        if not self.sql_persistence_plan_digest.startswith("sha256:"):
            raise GitHubResearchLoveTwoProjectionError(
                "SQL persistence plan digest must be sha256:*"
            )
        if self.first.request.object_ref == self.second.request.object_ref:
            raise GitHubResearchLoveTwoProjectionError(
                "the two analyses must use distinct SQL object references"
            )
        if self.first.request.revision_ref != self.second.request.revision_ref:
            raise GitHubResearchLoveTwoProjectionError(
                "both analyses must belong to the same accepted SQL revision"
            )
        if self.first.collection_name != self.second.collection_name:
            raise GitHubResearchLoveTwoProjectionError(
                "both analyses must target the attested Qdrant collection"
            )
        if self.first.dimension != 384 or self.second.dimension != 384:
            raise GitHubResearchLoveTwoProjectionError(
                "multilingual-e5-small projections must be 384-dimensional"
            )
        object.__setattr__(self, "pair_plan_digest", _pair_plan_digest(self))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "work_package_ref": self.work_package_ref,
            "sql_persistence_plan_digest": self.sql_persistence_plan_digest,
            "pair_plan_digest": self.pair_plan_digest,
            "first": self.first.to_mapping(),
            "second": self.second.to_mapping(),
            "boundaries": {
                "two_sql_objects_projected_separately": True,
                "existing_live_projection_probe_reused": True,
                "openvino_e5_dimension": 384,
                "qdrant_payload_reference_only": True,
                "sql_remains_authority": True,
                "global_synthesis_created": False,
                "delete_allowed": False,
                "alias_mutation_allowed": False,
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveTwoProjectionReadiness:
    """Read-only readiness for both existing probe plans."""

    schema: str
    pair_plan_digest: str
    ready: bool
    issues: tuple[str, ...]
    first: Mapping[str, Any]
    second: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.schema != READINESS_SCHEMA:
            raise GitHubResearchLoveTwoProjectionError(
                "unsupported two-projection readiness schema"
            )
        object.__setattr__(self, "first", MappingProxyType(dict(self.first)))
        object.__setattr__(self, "second", MappingProxyType(dict(self.second)))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "pair_plan_digest": self.pair_plan_digest,
            "ready": self.ready,
            "issues": list(self.issues),
            "first": dict(self.first),
            "second": dict(self.second),
            "boundaries": {
                "read_only": True,
                "openvino_inference_performed": False,
                "qdrant_write_performed": False,
                "sql_projection_write_performed": False,
                "global_synthesis_created": False,
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveTwoProjectionReceipt:
    """Secret-free proof for two distinct live projections."""

    schema: str
    pair_plan_digest: str
    policy_decision_id: str
    first: Mapping[str, Any]
    second: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.schema != RECEIPT_SCHEMA:
            raise GitHubResearchLoveTwoProjectionError(
                "unsupported two-projection receipt schema"
            )
        if not self.policy_decision_id.startswith(
            "policy:github-research-two-projections:"
        ):
            raise GitHubResearchLoveTwoProjectionError(
                "unexpected automatic projection policy decision"
            )
        object.__setattr__(self, "first", MappingProxyType(dict(self.first)))
        object.__setattr__(self, "second", MappingProxyType(dict(self.second)))
        first_object = self.first.get("object_ref")
        second_object = self.second.get("object_ref")
        if first_object == second_object:
            raise GitHubResearchLoveTwoProjectionError(
                "projection receipts must reference distinct SQL objects"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "pair_plan_digest": self.pair_plan_digest,
            "policy_decision_id": self.policy_decision_id,
            "first": dict(self.first),
            "second": dict(self.second),
            "checks": {
                "two_qdrant_points_written": True,
                "two_qdrant_points_read_back": True,
                "two_sql_sources_rehydrated": True,
                "projection_metadata_persisted_in_sql": True,
                "analysis_objects_remain_distinct": True,
            },
            "boundaries": {
                "openvino_e5_used": True,
                "embedding_dimension": 384,
                "qdrant_write_performed": True,
                "qdrant_read_performed": True,
                "qdrant_vectors_serialized": False,
                "authoritative_body_serialized": False,
                "sql_remains_authority": True,
                "global_synthesis_created": False,
                "github_mutation_performed": False,
                "scheduler_created": False,
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveTwoProjectionResult:
    """Plan, readiness and optional live receipt."""

    schema: str
    valid: bool
    status: str
    issues: tuple[str, ...]
    plan: GitHubResearchLoveTwoProjectionPlan | None = None
    readiness: GitHubResearchLoveTwoProjectionReadiness | None = None
    receipt: GitHubResearchLoveTwoProjectionReceipt | None = None

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "status": self.status,
            "issues": list(self.issues),
            "plan": self.plan.to_mapping() if self.plan else None,
            "readiness": (
                self.readiness.to_mapping() if self.readiness else None
            ),
            "receipt": self.receipt.to_mapping() if self.receipt else None,
            "first_analysis_projected": bool(self.receipt),
            "second_analysis_projected": bool(self.receipt),
            "global_synthesis_created": False,
        }


def build_github_research_love_two_projection_plan(
    command: GitHubResearchLoveTwoProjectionCommand,
) -> GitHubResearchLoveTwoProjectionPlan:
    """Build two existing-probe plans from the exact r16-r12 SQL receipt."""

    ports = validate_imported_actions_runtime_ports(command.runtime_ports)
    persistence = command.sql_persistence
    if persistence.get("schema") != SQL_PERSISTENCE_RESULT_SCHEMA:
        raise GitHubResearchLoveTwoProjectionError(
            "unsupported SQL persistence result schema"
        )
    if persistence.get("valid") is not True:
        raise GitHubResearchLoveTwoProjectionError(
            "SQL persistence result must be valid"
        )
    if persistence.get("status") != "persisted":
        raise GitHubResearchLoveTwoProjectionError(
            "SQL persistence result must be persisted"
        )
    receipt = _required_mapping(persistence, "receipt")
    if receipt.get("schema") != SQL_PERSISTENCE_RECEIPT_SCHEMA:
        raise GitHubResearchLoveTwoProjectionError(
            "unsupported SQL persistence receipt schema"
        )
    if receipt.get("readback_verified") is not True:
        raise GitHubResearchLoveTwoProjectionError(
            "SQL analysis readback must be verified"
        )
    plan = _required_mapping(persistence, "plan")
    first_object_ref = _required_text(receipt, "first_object_ref")
    second_object_ref = _required_text(receipt, "second_object_ref")
    revision_ref = _required_text(receipt, "revision_ref")
    work_package_ref = _required_text(receipt, "work_package_ref")
    if first_object_ref == second_object_ref:
        raise GitHubResearchLoveTwoProjectionError(
            "SQL persistence receipt does not keep analyses distinct"
        )

    first_object = ports.authority_store.get_object(first_object_ref)
    second_object = ports.authority_store.get_object(second_object_ref)
    revision = ports.authority_store.get_revision(revision_ref)
    if first_object is None or second_object is None or revision is None:
        raise GitHubResearchLoveTwoProjectionError(
            "SQL analysis objects or revision cannot be rehydrated"
        )

    attestation = ports.attestation
    if int(attestation.embedding_dimension) != 384:
        raise GitHubResearchLoveTwoProjectionError(
            "runtime attestation embedding dimension must be 384"
        )
    collection_name = str(attestation.qdrant_collection).strip()
    model_ref = str(attestation.model_ref).strip()
    model_revision = str(attestation.model_revision).strip()

    first_identity = build_love_qdrant_live_projection_identity_from_refs(
        object_ref=first_object_ref,
        content_digest=str(first_object.content_digest),
        revision_ref=revision_ref,
        collection_name=collection_name,
    )
    second_identity = build_love_qdrant_live_projection_identity_from_refs(
        object_ref=second_object_ref,
        content_digest=str(second_object.content_digest),
        revision_ref=revision_ref,
        collection_name=collection_name,
    )
    projected_at = _resolve_pair_projected_at(
        ports.authority_store,
        requested_projected_at=command.projected_at,
        first_identity=first_identity,
        second_identity=second_identity,
        first_expected={
            "source_ref": first_object.object_ref,
            "source_content_digest": first_object.content_digest,
            "model_ref": model_ref,
            "model_revision": model_revision,
            "dimension": 384,
            "normalized": True,
            "vector_name": command.dense_vector_name,
            "collection_name": collection_name,
            "point_id": first_identity.point_id,
            "projection_state": "active",
        },
        second_expected={
            "source_ref": second_object.object_ref,
            "source_content_digest": second_object.content_digest,
            "model_ref": model_ref,
            "model_revision": model_revision,
            "dimension": 384,
            "normalized": True,
            "vector_name": command.dense_vector_name,
            "collection_name": collection_name,
            "point_id": second_identity.point_id,
            "projection_state": "active",
        },
    )

    first_metadata = dict(first_object.metadata)
    second_metadata = dict(second_object.metadata)
    first_request = LoveLiveProjectionProbeRequest(
        object_ref=first_object_ref,
        revision_ref=revision_ref,
        branch_ref=command.branch_ref,
        project_ref=command.project_ref,
        conversation_ref=command.conversation_ref,
        specialist_ref=_required_text(
            first_metadata,
            "specialist_ref",
        ),
        laboratory_ref=_required_text(
            first_metadata,
            "laboratory_ref",
        ),
        security_scope=command.security_scope,
        projected_at=projected_at,
    )
    second_request = LoveLiveProjectionProbeRequest(
        object_ref=second_object_ref,
        revision_ref=revision_ref,
        branch_ref=command.branch_ref,
        project_ref=command.project_ref,
        conversation_ref=command.conversation_ref,
        specialist_ref=_required_text(
            second_metadata,
            "specialist_ref",
        ),
        laboratory_ref=_required_text(
            second_metadata,
            "laboratory_ref",
        ),
        security_scope=command.security_scope,
        projected_at=projected_at,
    )
    first_projection = build_love_live_projection_probe_plan(
        first_request,
        collection_name=collection_name,
        dense_vector_name=command.dense_vector_name,
        sparse_vector_name=command.sparse_vector_name,
        model_ref=model_ref,
        model_revision=model_revision,
        dimension=384,
    )
    second_projection = build_love_live_projection_probe_plan(
        second_request,
        collection_name=collection_name,
        dense_vector_name=command.dense_vector_name,
        sparse_vector_name=command.sparse_vector_name,
        model_ref=model_ref,
        model_revision=model_revision,
        dimension=384,
    )
    return GitHubResearchLoveTwoProjectionPlan(
        schema=PLAN_SCHEMA,
        work_package_ref=work_package_ref,
        sql_persistence_plan_digest=_required_text(plan, "plan_digest"),
        first=first_projection,
        second=second_projection,
    )


def inspect_github_research_love_two_projections(
    *,
    authority_store: Any,
    plan: GitHubResearchLoveTwoProjectionPlan,
) -> GitHubResearchLoveTwoProjectionReadiness:
    """Delegate read-only validation to the existing probe for both objects."""

    first = inspect_love_live_projection_probe(authority_store, plan.first)
    second = inspect_love_live_projection_probe(authority_store, plan.second)
    issues = tuple(
        dict.fromkeys(
            (
                *(f"first: {item}" for item in first.issues),
                *(f"second: {item}" for item in second.issues),
            )
        )
    )
    return GitHubResearchLoveTwoProjectionReadiness(
        schema=READINESS_SCHEMA,
        pair_plan_digest=plan.pair_plan_digest,
        ready=first.ready and second.ready and not issues,
        issues=issues,
        first=first.to_mapping(),
        second=second.to_mapping(),
    )


async def execute_github_research_love_two_projections(
    command: GitHubResearchLoveTwoProjectionCommand,
    plan: GitHubResearchLoveTwoProjectionPlan,
) -> GitHubResearchLoveTwoProjectionReceipt:
    """Execute the two existing-probe cycles with one explicit auto-policy."""

    if not command.allow_write:
        raise GitHubResearchLoveTwoProjectionError(
            "live Qdrant writes are disabled"
        )
    ports = validate_imported_actions_runtime_ports(command.runtime_ports)
    readiness = inspect_github_research_love_two_projections(
        authority_store=ports.authority_store,
        plan=plan,
    )
    if not readiness.ready:
        raise GitHubResearchLoveTwoProjectionError(
            "two-projection readiness failed: " + "; ".join(readiness.issues)
        )
    policy_decision_id = (
        "policy:github-research-two-projections:"
        + plan.pair_plan_digest[7:31]
    )
    first_gate = LoveLiveProjectionProbeGate(
        policy_decision_id=policy_decision_id,
        operator_decision="approve",
        allow_write=True,
        confirm_plan_digest=plan.first.plan_digest,
    )
    second_gate = LoveLiveProjectionProbeGate(
        policy_decision_id=policy_decision_id,
        operator_decision="approve",
        allow_write=True,
        confirm_plan_digest=plan.second.plan_digest,
    )
    first_receipt = await execute_love_live_projection_probe(
        ports.authority_store,
        ports.projection_port,
        command.reference_point_reader,
        plan.first,
        first_gate,
    )
    second_receipt = await execute_love_live_projection_probe(
        ports.authority_store,
        ports.projection_port,
        command.reference_point_reader,
        plan.second,
        second_gate,
    )
    return GitHubResearchLoveTwoProjectionReceipt(
        schema=RECEIPT_SCHEMA,
        pair_plan_digest=plan.pair_plan_digest,
        policy_decision_id=policy_decision_id,
        first=_receipt_mapping(first_receipt),
        second=_receipt_mapping(second_receipt),
    )


async def project_github_research_love_analyses(
    command: GitHubResearchLoveTwoProjectionCommand,
) -> GitHubResearchLoveTwoProjectionResult:
    """Build, inspect and execute two separate live projections."""

    try:
        plan = build_github_research_love_two_projection_plan(command)
        readiness = inspect_github_research_love_two_projections(
            authority_store=command.runtime_ports.authority_store,
            plan=plan,
        )
        if not readiness.ready:
            return GitHubResearchLoveTwoProjectionResult(
                schema=RESULT_SCHEMA,
                valid=False,
                status="not-ready",
                issues=readiness.issues,
                plan=plan,
                readiness=readiness,
            )
        receipt = await execute_github_research_love_two_projections(
            command,
            plan,
        )
        return GitHubResearchLoveTwoProjectionResult(
            schema=RESULT_SCHEMA,
            valid=True,
            status="projected",
            issues=(),
            plan=plan,
            readiness=readiness,
            receipt=receipt,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        return GitHubResearchLoveTwoProjectionResult(
            schema=RESULT_SCHEMA,
            valid=False,
            status="failed",
            issues=(f"{type(exc).__name__}: {exc}",),
        )


def _resolve_pair_projected_at(
    authority_store: Any,
    *,
    requested_projected_at: str,
    first_identity: LoveQdrantLiveProjectionIdentity,
    second_identity: LoveQdrantLiveProjectionIdentity,
    first_expected: Mapping[str, object],
    second_expected: Mapping[str, object],
) -> str:
    """Preserve the first SQL-authoritative projection timestamp on replay."""

    get_projection = getattr(authority_store, "get_projection", None)
    if get_projection is None:
        # The validated production authority store exposes this read port.
        # Legacy isolated tests replace port validation with lightweight
        # doubles; absence therefore means that no replay state is available.
        return requested_projected_at
    if not callable(get_projection):
        raise GitHubResearchLoveTwoProjectionError(
            "authority_store.get_projection must be callable"
        )

    existing = (
        (
            "first",
            get_projection(first_identity.projection_ref),
            first_expected,
        ),
        (
            "second",
            get_projection(second_identity.projection_ref),
            second_expected,
        ),
    )
    timestamps: list[tuple[str, str]] = []
    for name, projection, expected in existing:
        if projection is None:
            continue
        _require_existing_projection_matches(
            name=name,
            projection=projection,
            expected=expected,
        )
        timestamps.append((name, str(projection.projected_at or "")))

    if not timestamps:
        return requested_projected_at
    distinct = tuple(dict.fromkeys(value for _, value in timestamps))
    if len(distinct) != 1:
        details = ", ".join(f"{name}={value!r}" for name, value in timestamps)
        raise GitHubResearchLoveTwoProjectionError(
            "existing immutable projections disagree on projected_at: " + details
        )
    return distinct[0]


def _require_existing_projection_matches(
    *,
    name: str,
    projection: object,
    expected: Mapping[str, object],
) -> None:
    conflicts = tuple(
        field_name
        for field_name, expected_value in expected.items()
        if getattr(projection, field_name, object()) != expected_value
    )
    if conflicts:
        raise GitHubResearchLoveTwoProjectionError(
            f"existing {name} projection conflicts with deterministic plan: "
            + ", ".join(conflicts)
        )


def _receipt_mapping(
    receipt: LoveLiveProjectionProbeReceipt,
) -> Mapping[str, Any]:
    value = receipt.to_mapping()
    forbidden = {
        "body",
        "content",
        "vector",
        "vectors",
        "values",
        "embedding",
        "local_path",
    }.intersection(value)
    if forbidden:
        raise GitHubResearchLoveTwoProjectionError(
            "projection receipt contains forbidden authoritative/vector fields"
        )
    return value


def _pair_plan_digest(
    plan: GitHubResearchLoveTwoProjectionPlan,
) -> str:
    payload = {
        "schema": plan.schema,
        "work_package_ref": plan.work_package_ref,
        "sql_persistence_plan_digest": plan.sql_persistence_plan_digest,
        "first_plan_digest": plan.first.plan_digest,
        "second_plan_digest": plan.second.plan_digest,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _required_mapping(
    value: Mapping[str, Any],
    name: str,
) -> Mapping[str, Any]:
    candidate = value.get(name)
    if not isinstance(candidate, Mapping):
        raise GitHubResearchLoveTwoProjectionError(
            f"{name} must be an object"
        )
    return candidate


def _required_text(value: Mapping[str, Any], name: str) -> str:
    candidate = value.get(name)
    if not isinstance(candidate, str) or not candidate.strip():
        raise GitHubResearchLoveTwoProjectionError(
            f"{name} must not be empty"
        )
    return candidate.strip()


def _require_typed_ref(name: str, value: object) -> None:
    if not isinstance(value, str) or ":" not in value:
        raise GitHubResearchLoveTwoProjectionError(
            f"{name} must be a typed reference"
        )
    prefix, suffix = value.split(":", 1)
    if not prefix or not suffix or not prefix[0].islower():
        raise GitHubResearchLoveTwoProjectionError(
            f"{name} must be a typed reference"
        )


__all__ = (
    "GitHubResearchLoveTwoProjectionCommand",
    "GitHubResearchLoveTwoProjectionError",
    "GitHubResearchLoveTwoProjectionPlan",
    "GitHubResearchLoveTwoProjectionReadiness",
    "GitHubResearchLoveTwoProjectionReceipt",
    "GitHubResearchLoveTwoProjectionResult",
    "PLAN_SCHEMA",
    "READINESS_SCHEMA",
    "RECEIPT_SCHEMA",
    "RESULT_SCHEMA",
    "build_github_research_love_two_projection_plan",
    "execute_github_research_love_two_projections",
    "inspect_github_research_love_two_projections",
    "project_github_research_love_analyses",
)
