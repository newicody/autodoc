"""Build and persist the final love-research deliverable in SQL authority.

r16-r15 produces a valid local liaison synthesis whose publication flag remains
false.  This unit reuses ``build_final_synthesis_packet`` to create the final
human-readable packet, marks only the packet's cloned synthesis as ready, then
persists:

- one immutable final-deliverable authority object;
- one independently addressable artifact descriptor;
- one accepted child revision whose parent is the r16-r12 analysis revision.

The two specialist analyses and the local liaison result remain unchanged.
GitHub publication is deliberately outside this unit.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import hashlib
import json
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable

from context.context_revision_sql_authority_0287 import (
    CONTEXT_ARTIFACT_DESCRIPTOR_SCHEMA,
    CONTEXT_AUTHORITY_OBJECT_SCHEMA,
    CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
    CONTEXT_REVISION_SCHEMA,
    ContextArtifactDescriptor,
    ContextAuthorityObject,
    ContextRevision,
    ContextRevisionMembership,
    ContextSqlWriteResult,
)
from context.github_research_love_liaison_synthesis_0287 import (
    GitHubResearchLoveLiaisonSynthesisResult,
)
from context.github_research_love_sql_persistence_0287 import (
    RECEIPT_SCHEMA as ANALYSIS_SQL_RECEIPT_SCHEMA,
    RESULT_SCHEMA as ANALYSIS_SQL_RESULT_SCHEMA,
)
from context.love_imported_actions_runtime_contract_0287 import (
    ImportedActionsRuntimePorts,
    validate_imported_actions_runtime_ports,
)
from context.specialist_liaison_synthesis import (
    FinalSynthesisPacket,
    build_final_synthesis_packet,
)

PLAN_SCHEMA = "missipy.github.research_love_final_deliverable_sql_plan.v1"
READINESS_SCHEMA = (
    "missipy.github.research_love_final_deliverable_sql_readiness.v1"
)
RECEIPT_SCHEMA = (
    "missipy.github.research_love_final_deliverable_sql_receipt.v1"
)
RESULT_SCHEMA = "missipy.github.research_love_final_deliverable_sql_result.v1"
_ALLOWED_TARGET_PREFIXES = (
    "github:",
    "artifact:",
    "local:",
    "publication:",
)


class GitHubResearchLoveFinalDeliverableError(RuntimeError):
    """Raised when final-packet lineage or immutable SQL state is invalid."""


@runtime_checkable
class GitHubResearchLoveFinalAuthorityStore(Protocol):
    """Existing SQL authority methods required by this bounded unit."""

    def get_object(self, object_ref: str) -> ContextAuthorityObject | None: ...

    def put_object(
        self,
        item: ContextAuthorityObject,
    ) -> ContextSqlWriteResult: ...

    def get_artifact(
        self,
        artifact_ref: str,
    ) -> ContextArtifactDescriptor | None: ...

    def put_artifact(
        self,
        item: ContextArtifactDescriptor,
    ) -> ContextSqlWriteResult: ...

    def get_revision(self, revision_ref: str) -> ContextRevision | None: ...

    def put_revision(self, item: ContextRevision) -> ContextSqlWriteResult: ...


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveFinalDeliverableCommand:
    """Explicit request to build a final packet and persist it locally."""

    runtime_ports: ImportedActionsRuntimePorts
    liaison: GitHubResearchLoveLiaisonSynthesisResult
    analysis_sql_persistence: Mapping[str, Any]
    target_ref: str
    created_at: str

    def __post_init__(self) -> None:
        if not isinstance(
            self.liaison,
            GitHubResearchLoveLiaisonSynthesisResult,
        ):
            raise TypeError(
                "liaison must be GitHubResearchLoveLiaisonSynthesisResult"
            )
        if not isinstance(self.analysis_sql_persistence, Mapping):
            raise TypeError("analysis_sql_persistence must be a mapping")
        target = self.target_ref.strip()
        if not target.startswith(_ALLOWED_TARGET_PREFIXES):
            raise GitHubResearchLoveFinalDeliverableError(
                "target_ref must start with github:, artifact:, local: "
                "or publication:"
            )
        object.__setattr__(self, "target_ref", target)
        timestamp = self.created_at.strip()
        if "T" not in timestamp or not timestamp.endswith("Z"):
            raise GitHubResearchLoveFinalDeliverableError(
                "created_at must be a UTC timestamp ending with Z"
            )
        object.__setattr__(self, "created_at", timestamp)


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveFinalDeliverablePlan:
    """Deterministic packet and immutable SQL entities."""

    schema: str
    work_package_ref: str
    liaison_plan_digest: str
    analysis_sql_plan_digest: str
    parent_revision_ref: str
    first_analysis_object_ref: str
    second_analysis_object_ref: str
    packet: FinalSynthesisPacket
    authority_object: ContextAuthorityObject
    artifact: ContextArtifactDescriptor
    revision: ContextRevision
    plan_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema != PLAN_SCHEMA:
            raise GitHubResearchLoveFinalDeliverableError(
                "unsupported final-deliverable plan schema"
            )
        if not self.work_package_ref.startswith("research-work-package:"):
            raise GitHubResearchLoveFinalDeliverableError(
                "work_package_ref must start with research-work-package:"
            )
        for name, value in (
            ("liaison_plan_digest", self.liaison_plan_digest),
            ("analysis_sql_plan_digest", self.analysis_sql_plan_digest),
        ):
            if not value.startswith("sha256:") or len(value) != 71:
                raise GitHubResearchLoveFinalDeliverableError(
                    f"{name} must be sha256:*"
                )
        if not self.parent_revision_ref.startswith("context-revision:"):
            raise GitHubResearchLoveFinalDeliverableError(
                "parent_revision_ref must start with context-revision:"
            )
        if self.first_analysis_object_ref == self.second_analysis_object_ref:
            raise GitHubResearchLoveFinalDeliverableError(
                "source analysis objects must remain distinct"
            )
        if not self.packet.synthesis.final_publication_ready:
            raise GitHubResearchLoveFinalDeliverableError(
                "final packet synthesis must be publication-ready"
            )
        if not self.packet.synthesis.provenance_hidden:
            raise GitHubResearchLoveFinalDeliverableError(
                "final packet must keep specialist provenance hidden"
            )
        if self.packet.synthesis.request_ref != self.work_package_ref:
            raise GitHubResearchLoveFinalDeliverableError(
                "packet request_ref differs from work package"
            )
        if self.revision.parent_revision_refs != (
            self.parent_revision_ref,
        ):
            raise GitHubResearchLoveFinalDeliverableError(
                "final revision must descend from the analysis revision"
            )
        expected_members = (
            self.authority_object.object_ref,
            self.artifact.artifact_ref,
        )
        active_members = tuple(
            item.object_ref
            for item in self.revision.memberships
            if item.state == "active"
        )
        if active_members != expected_members:
            raise GitHubResearchLoveFinalDeliverableError(
                "final revision membership mismatch"
            )
        if self.revision.validation_status != "accepted":
            raise GitHubResearchLoveFinalDeliverableError(
                "final revision must be accepted"
            )
        object.__setattr__(self, "plan_digest", _plan_digest(self))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "plan_digest": self.plan_digest,
            "work_package_ref": self.work_package_ref,
            "liaison_plan_digest": self.liaison_plan_digest,
            "analysis_sql_plan_digest": self.analysis_sql_plan_digest,
            "parent_revision_ref": self.parent_revision_ref,
            "first_analysis_object_ref": self.first_analysis_object_ref,
            "second_analysis_object_ref": self.second_analysis_object_ref,
            "packet": self.packet.to_mapping(),
            "authority_object": self.authority_object.to_mapping(),
            "artifact": self.artifact.to_mapping(),
            "revision": self.revision.to_mapping(),
            "boundaries": {
                "existing_final_packet_builder_reused": True,
                "source_analyses_modified": False,
                "source_liaison_modified": False,
                "final_publication_ready": True,
                "sql_write_planned": True,
                "qdrant_write_performed": False,
                "github_mutation_performed": False,
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveFinalDeliverableReadiness:
    """Read-only immutable-state inspection."""

    schema: str
    plan_digest: str
    ready: bool
    issues: tuple[str, ...]
    states: Mapping[str, str]

    def __post_init__(self) -> None:
        if self.schema != READINESS_SCHEMA:
            raise GitHubResearchLoveFinalDeliverableError(
                "unsupported final-deliverable readiness schema"
            )
        object.__setattr__(
            self,
            "states",
            MappingProxyType(dict(self.states)),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "plan_digest": self.plan_digest,
            "ready": self.ready,
            "issues": list(self.issues),
            "states": dict(self.states),
            "boundaries": {
                "read_only": True,
                "sql_write_performed": False,
                "qdrant_write_performed": False,
                "github_mutation_performed": False,
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveFinalDeliverableReceipt:
    """Exact SQL write and readback proof, without remote publication."""

    schema: str
    plan_digest: str
    packet_ref: str
    target_ref: str
    authority_object_ref: str
    artifact_ref: str
    revision_ref: str
    writes: Mapping[str, Mapping[str, bool]]
    readback_verified: bool
    action: str

    def __post_init__(self) -> None:
        if self.schema != RECEIPT_SCHEMA:
            raise GitHubResearchLoveFinalDeliverableError(
                "unsupported final-deliverable receipt schema"
            )
        if self.action not in {"created", "replay", "mixed"}:
            raise GitHubResearchLoveFinalDeliverableError(
                "receipt action must be created, replay or mixed"
            )
        frozen = {
            key: MappingProxyType(dict(value))
            for key, value in self.writes.items()
        }
        object.__setattr__(self, "writes", MappingProxyType(frozen))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "plan_digest": self.plan_digest,
            "packet_ref": self.packet_ref,
            "target_ref": self.target_ref,
            "authority_object_ref": self.authority_object_ref,
            "artifact_ref": self.artifact_ref,
            "revision_ref": self.revision_ref,
            "writes": {
                key: dict(value)
                for key, value in self.writes.items()
            },
            "readback_verified": self.readback_verified,
            "action": self.action,
            "boundaries": {
                "final_publication_ready": True,
                "final_deliverable_persisted": True,
                "sql_remains_authority": True,
                "child_revision_written_last": True,
                "restart_safe": True,
                "remote_publication_performed": False,
                "github_mutation_performed": False,
                "projectv2_mutation_performed": False,
                "qdrant_write_performed": False,
                "scheduler_created": False,
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveFinalDeliverableResult:
    """Plan, readiness and optional durable receipt."""

    schema: str
    valid: bool
    status: str
    issues: tuple[str, ...]
    plan: GitHubResearchLoveFinalDeliverablePlan | None = None
    readiness: GitHubResearchLoveFinalDeliverableReadiness | None = None
    receipt: GitHubResearchLoveFinalDeliverableReceipt | None = None

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "status": self.status,
            "issues": list(self.issues),
            "plan": self.plan.to_mapping() if self.plan else None,
            "readiness": (
                self.readiness.to_mapping()
                if self.readiness is not None
                else None
            ),
            "receipt": (
                self.receipt.to_mapping()
                if self.receipt is not None
                else None
            ),
            "final_packet_created": self.plan is not None,
            "final_deliverable_persisted": bool(
                self.receipt and self.receipt.readback_verified
            ),
            "remote_publication_performed": False,
            "github_mutation_performed": False,
        }


def build_github_research_love_final_deliverable_plan(
    command: GitHubResearchLoveFinalDeliverableCommand,
) -> GitHubResearchLoveFinalDeliverablePlan:
    """Build the existing final packet and its SQL authority entities."""

    ports = validate_imported_actions_runtime_ports(command.runtime_ports)
    liaison = command.liaison
    if not liaison.valid or liaison.status != "synthesized":
        raise GitHubResearchLoveFinalDeliverableError(
            "liaison result must be valid and synthesized"
        )
    if liaison.synthesis is None:
        raise GitHubResearchLoveFinalDeliverableError(
            "liaison synthesis is unavailable"
        )
    if liaison.synthesis.final_publication_ready:
        raise GitHubResearchLoveFinalDeliverableError(
            "source liaison must still be non-publication-ready"
        )
    if not liaison.synthesis.provenance_hidden:
        raise GitHubResearchLoveFinalDeliverableError(
            "source liaison must hide specialist provenance"
        )

    sql_result = command.analysis_sql_persistence
    if sql_result.get("schema") != ANALYSIS_SQL_RESULT_SCHEMA:
        raise GitHubResearchLoveFinalDeliverableError(
            "unsupported analysis SQL result schema"
        )
    if sql_result.get("valid") is not True:
        raise GitHubResearchLoveFinalDeliverableError(
            "analysis SQL result must be valid"
        )
    if sql_result.get("status") != "persisted":
        raise GitHubResearchLoveFinalDeliverableError(
            "analysis SQL result must be persisted"
        )
    sql_plan = _required_mapping(sql_result, "plan")
    sql_receipt = _required_mapping(sql_result, "receipt")
    if sql_receipt.get("schema") != ANALYSIS_SQL_RECEIPT_SCHEMA:
        raise GitHubResearchLoveFinalDeliverableError(
            "unsupported analysis SQL receipt schema"
        )
    if sql_receipt.get("readback_verified") is not True:
        raise GitHubResearchLoveFinalDeliverableError(
            "analysis SQL readback must be verified"
        )

    work_package_ref = liaison.plan.work_package_ref
    first_ref = liaison.plan.first_sql_ref
    second_ref = liaison.plan.second_sql_ref
    if sql_receipt.get("work_package_ref") != work_package_ref:
        raise GitHubResearchLoveFinalDeliverableError(
            "analysis SQL work_package_ref mismatch"
        )
    if sql_receipt.get("first_object_ref") != first_ref:
        raise GitHubResearchLoveFinalDeliverableError(
            "first analysis SQL reference mismatch"
        )
    if sql_receipt.get("second_object_ref") != second_ref:
        raise GitHubResearchLoveFinalDeliverableError(
            "second analysis SQL reference mismatch"
        )
    parent_revision_ref = _required_text(
        sql_receipt,
        "revision_ref",
    )
    analysis_sql_plan_digest = _required_text(
        sql_plan,
        "plan_digest",
    )

    store = _authority_store(ports.authority_store)
    parent = store.get_revision(parent_revision_ref)
    if parent is None:
        raise GitHubResearchLoveFinalDeliverableError(
            "analysis revision does not exist in SQL authority"
        )
    if parent.validation_status != "accepted":
        raise GitHubResearchLoveFinalDeliverableError(
            "analysis revision is not accepted"
        )

    packet = build_final_synthesis_packet(
        synthesis=liaison.synthesis,
        target_ref=command.target_ref,
        mark_ready=True,
    )
    packet_mapping = packet.to_mapping()
    if packet_mapping.get("runtime_import") != (
        "external final publication adapter only"
    ):
        raise GitHubResearchLoveFinalDeliverableError(
            "final packet publication boundary mismatch"
        )
    body = json.dumps(
        packet_mapping,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    content_digest = (
        "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()
    )
    suffix = hashlib.sha256(
        (
            work_package_ref
            + "|"
            + liaison.plan.plan_digest
            + "|"
            + analysis_sql_plan_digest
            + "|"
            + packet.packet_ref
            + "|"
            + content_digest
        ).encode("utf-8")
    ).hexdigest()[:20]
    object_ref = f"context-object:github-love-final-{suffix}"
    artifact_ref = f"artifact:github-love-final-{suffix}"
    task_ref = f"task:github-love-finalize-{suffix}"

    authority_object = ContextAuthorityObject(
        schema=CONTEXT_AUTHORITY_OBJECT_SCHEMA,
        object_ref=object_ref,
        object_kind="final-deliverable",
        content_schema_ref=str(packet_mapping["schema"]),
        content_digest=content_digest,
        title=packet.title,
        body=body,
        media_type="application/json",
        byte_count=len(body.encode("utf-8")),
        metadata={
            "packet_ref": packet.packet_ref,
            "target_ref": packet.target_ref,
            "synthesis_ref": packet.synthesis.synthesis_ref,
            "work_package_ref": work_package_ref,
            "liaison_plan_digest": liaison.plan.plan_digest,
            "analysis_sql_plan_digest": analysis_sql_plan_digest,
            "first_analysis_object_ref": first_ref,
            "second_analysis_object_ref": second_ref,
            "specialist_provenance_hidden": True,
            "final_publication_ready": True,
            "remote_publication_performed": False,
        },
    )
    artifact = ContextArtifactDescriptor(
        schema=CONTEXT_ARTIFACT_DESCRIPTOR_SCHEMA,
        artifact_ref=artifact_ref,
        content_schema_ref=str(packet_mapping["schema"]),
        content_digest=content_digest,
        storage_ref=f"sql:{object_ref}",
        media_type="application/json",
        byte_count=len(body.encode("utf-8")),
        producer_task_ref=task_ref,
        created_at=command.created_at,
        metadata={
            "packet_ref": packet.packet_ref,
            "target_ref": packet.target_ref,
            "authority_object_ref": object_ref,
            "work_package_ref": work_package_ref,
            "sql_remains_authority": True,
            "remote_publication_performed": False,
        },
    )
    memberships = (
        ContextRevisionMembership(
            schema=CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
            object_ref=object_ref,
            state="active",
        ),
        ContextRevisionMembership(
            schema=CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
            object_ref=artifact_ref,
            state="active",
        ),
    )
    evidence_refs = tuple(
        dict.fromkeys(
            (
                artifact_ref,
                f"sql:{first_ref}",
                f"sql:{second_ref}",
                *packet.evidence_refs,
            )
        )
    )
    revision = ContextRevision(
        schema=CONTEXT_REVISION_SCHEMA,
        revision_ref=f"context-revision:github-love-final-{suffix}",
        context_ref=parent.context_ref,
        parent_revision_refs=(parent_revision_ref,),
        memberships=memberships,
        validation_status="accepted",
        significance="material",
        evidence_refs=evidence_refs,
        producer_task_ref=task_ref,
        created_at=command.created_at,
        metadata={
            "purpose": "github-research-final-deliverable",
            "packet_ref": packet.packet_ref,
            "target_ref": packet.target_ref,
            "work_package_ref": work_package_ref,
            "source_analysis_revision_ref": parent_revision_ref,
            "first_analysis_object_ref": first_ref,
            "second_analysis_object_ref": second_ref,
            "source_analyses_modified": False,
            "source_liaison_modified": False,
            "remote_publication_performed": False,
        },
    )
    return GitHubResearchLoveFinalDeliverablePlan(
        schema=PLAN_SCHEMA,
        work_package_ref=work_package_ref,
        liaison_plan_digest=liaison.plan.plan_digest,
        analysis_sql_plan_digest=analysis_sql_plan_digest,
        parent_revision_ref=parent_revision_ref,
        first_analysis_object_ref=first_ref,
        second_analysis_object_ref=second_ref,
        packet=packet,
        authority_object=authority_object,
        artifact=artifact,
        revision=revision,
    )


def inspect_github_research_love_final_deliverable(
    authority_store: GitHubResearchLoveFinalAuthorityStore,
    plan: GitHubResearchLoveFinalDeliverablePlan,
) -> GitHubResearchLoveFinalDeliverableReadiness:
    """Inspect immutable collisions and parent lineage without writes."""

    store = _authority_store(authority_store)
    parent = store.get_revision(plan.parent_revision_ref)
    states = {
        "authority_object": _immutable_state(
            store.get_object(plan.authority_object.object_ref),
            plan.authority_object,
        ),
        "artifact": _immutable_state(
            store.get_artifact(plan.artifact.artifact_ref),
            plan.artifact,
        ),
        "revision": _immutable_state(
            store.get_revision(plan.revision.revision_ref),
            plan.revision,
        ),
    }
    issues: list[str] = []
    if parent is None:
        issues.append("analysis revision does not exist")
    else:
        if parent.validation_status != "accepted":
            issues.append("analysis revision is not accepted")
        if parent.context_ref != plan.revision.context_ref:
            issues.append("final revision context_ref differs from parent")
    for name, state in states.items():
        if state == "collision":
            issues.append(f"immutable {name} collision")
    if states["revision"] == "identical":
        for name in ("authority_object", "artifact"):
            if states[name] != "identical":
                issues.append(
                    "existing final revision requires every member "
                    f"to exist identically: {name}"
                )
    return GitHubResearchLoveFinalDeliverableReadiness(
        schema=READINESS_SCHEMA,
        plan_digest=plan.plan_digest,
        ready=not issues,
        issues=tuple(issues),
        states=states,
    )


def execute_github_research_love_final_deliverable(
    authority_store: GitHubResearchLoveFinalAuthorityStore,
    plan: GitHubResearchLoveFinalDeliverablePlan,
) -> GitHubResearchLoveFinalDeliverableReceipt:
    """Write object and artifact first, child revision last, then read back."""

    store = _authority_store(authority_store)
    readiness = inspect_github_research_love_final_deliverable(
        store,
        plan,
    )
    if not readiness.ready:
        raise GitHubResearchLoveFinalDeliverableError(
            "final deliverable readiness failed: "
            + "; ".join(readiness.issues)
        )

    object_write = store.put_object(plan.authority_object)
    artifact_write = store.put_artifact(plan.artifact)
    revision_write = store.put_revision(plan.revision)

    readback = (
        (
            store.get_object(plan.authority_object.object_ref),
            plan.authority_object,
        ),
        (
            store.get_artifact(plan.artifact.artifact_ref),
            plan.artifact,
        ),
        (
            store.get_revision(plan.revision.revision_ref),
            plan.revision,
        ),
    )
    if any(
        _immutable_state(actual, expected) != "identical"
        for actual, expected in readback
    ):
        raise GitHubResearchLoveFinalDeliverableError(
            "final deliverable SQL readback mismatch"
        )

    writes = {
        "authority_object": _write_mapping(object_write),
        "artifact": _write_mapping(artifact_write),
        "revision": _write_mapping(revision_write),
    }
    inserted = sum(
        1 for value in writes.values() if value["inserted"]
    )
    replayed = sum(
        1 for value in writes.values() if value["idempotent_replay"]
    )
    action = (
        "created"
        if inserted == len(writes)
        else "replay"
        if replayed == len(writes)
        else "mixed"
    )
    return GitHubResearchLoveFinalDeliverableReceipt(
        schema=RECEIPT_SCHEMA,
        plan_digest=plan.plan_digest,
        packet_ref=plan.packet.packet_ref,
        target_ref=plan.packet.target_ref,
        authority_object_ref=plan.authority_object.object_ref,
        artifact_ref=plan.artifact.artifact_ref,
        revision_ref=plan.revision.revision_ref,
        writes=writes,
        readback_verified=True,
        action=action,
    )


def persist_github_research_love_final_deliverable(
    command: GitHubResearchLoveFinalDeliverableCommand,
) -> GitHubResearchLoveFinalDeliverableResult:
    """Build, inspect and persist the local final deliverable."""

    try:
        ports = validate_imported_actions_runtime_ports(
            command.runtime_ports
        )
        plan = build_github_research_love_final_deliverable_plan(
            command
        )
        store = _authority_store(ports.authority_store)
        readiness = inspect_github_research_love_final_deliverable(
            store,
            plan,
        )
        if not readiness.ready:
            return GitHubResearchLoveFinalDeliverableResult(
                schema=RESULT_SCHEMA,
                valid=False,
                status="not-ready",
                issues=readiness.issues,
                plan=plan,
                readiness=readiness,
            )
        receipt = execute_github_research_love_final_deliverable(
            store,
            plan,
        )
        return GitHubResearchLoveFinalDeliverableResult(
            schema=RESULT_SCHEMA,
            valid=True,
            status="persisted",
            issues=(),
            plan=plan,
            readiness=readiness,
            receipt=receipt,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        return GitHubResearchLoveFinalDeliverableResult(
            schema=RESULT_SCHEMA,
            valid=False,
            status="failed",
            issues=(f"{type(exc).__name__}: {exc}",),
        )


def _authority_store(
    value: object,
) -> GitHubResearchLoveFinalAuthorityStore:
    if not isinstance(value, GitHubResearchLoveFinalAuthorityStore):
        raise GitHubResearchLoveFinalDeliverableError(
            "authority_store does not expose object/artifact/revision methods"
        )
    return value


def _immutable_state(
    existing: object | None,
    expected: object,
) -> str:
    if existing is None:
        return "missing"
    existing_mapping = getattr(existing, "to_mapping", None)
    expected_mapping = getattr(expected, "to_mapping", None)
    if not callable(existing_mapping) or not callable(expected_mapping):
        return "collision"
    return (
        "identical"
        if existing_mapping() == expected_mapping()
        else "collision"
    )


def _write_mapping(
    value: ContextSqlWriteResult,
) -> Mapping[str, bool]:
    return {
        "inserted": bool(value.inserted),
        "idempotent_replay": bool(value.idempotent_replay),
    }


def _required_mapping(
    value: Mapping[str, Any],
    name: str,
) -> Mapping[str, Any]:
    candidate = value.get(name)
    if not isinstance(candidate, Mapping):
        raise GitHubResearchLoveFinalDeliverableError(
            f"{name} must be an object"
        )
    return candidate


def _required_text(
    value: Mapping[str, Any],
    name: str,
) -> str:
    candidate = value.get(name)
    if not isinstance(candidate, str) or not candidate.strip():
        raise GitHubResearchLoveFinalDeliverableError(
            f"{name} must not be empty"
        )
    return candidate.strip()


def _plan_digest(
    plan: GitHubResearchLoveFinalDeliverablePlan,
) -> str:
    payload = {
        "schema": plan.schema,
        "work_package_ref": plan.work_package_ref,
        "liaison_plan_digest": plan.liaison_plan_digest,
        "analysis_sql_plan_digest": plan.analysis_sql_plan_digest,
        "parent_revision_ref": plan.parent_revision_ref,
        "first_analysis_object_ref": plan.first_analysis_object_ref,
        "second_analysis_object_ref": plan.second_analysis_object_ref,
        "packet": plan.packet.to_mapping(),
        "authority_object": plan.authority_object.to_mapping(),
        "artifact": plan.artifact.to_mapping(),
        "revision": plan.revision.to_mapping(),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


__all__ = (
    "GitHubResearchLoveFinalAuthorityStore",
    "GitHubResearchLoveFinalDeliverableCommand",
    "GitHubResearchLoveFinalDeliverableError",
    "GitHubResearchLoveFinalDeliverablePlan",
    "GitHubResearchLoveFinalDeliverableReadiness",
    "GitHubResearchLoveFinalDeliverableReceipt",
    "GitHubResearchLoveFinalDeliverableResult",
    "PLAN_SCHEMA",
    "READINESS_SCHEMA",
    "RECEIPT_SCHEMA",
    "RESULT_SCHEMA",
    "build_github_research_love_final_deliverable_plan",
    "execute_github_research_love_final_deliverable",
    "inspect_github_research_love_final_deliverable",
    "persist_github_research_love_final_deliverable",
)
