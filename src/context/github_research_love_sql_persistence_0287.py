"""Persist both GitHub research specialist analyses in the existing SQL authority.

This unit consumes the successful r16-r10 and r16-r11 result mappings.  It
creates two immutable ContextAuthorityObject values, two independently
addressable ContextArtifactDescriptor values and one accepted child
ContextRevision containing the four references.

The existing authority_store is injected through ImportedActionsRuntimePorts.
No SQL driver, table, connection, Scheduler, Qdrant client, OpenVINO executor,
synthesis, or GitHub mutation is created here.

Writes are restart-safe rather than pretending to be one hidden transaction:
every entity is immutable, collisions are inspected before writing, the child
revision is written last, and an interrupted execution can be replayed until
the exact readback is complete.
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
from context.github_research_love_first_visit_dispatch_0287 import (
    SCHEMA as FIRST_VISIT_DISPATCH_SCHEMA,
)
from context.github_research_love_second_visit_dispatch_0287 import (
    SCHEMA as SECOND_VISIT_DISPATCH_SCHEMA,
)
from context.love_imported_actions_runtime_contract_0287 import (
    ImportedActionsRuntimePorts,
    validate_imported_actions_runtime_ports,
)

PLAN_SCHEMA = "missipy.github.research_love_sql_persistence_plan.v1"
READINESS_SCHEMA = "missipy.github.research_love_sql_persistence_readiness.v1"
RECEIPT_SCHEMA = "missipy.github.research_love_sql_persistence_receipt.v1"
RESULT_SCHEMA = "missipy.github.research_love_sql_persistence_result.v1"


class GitHubResearchLoveSqlPersistenceError(RuntimeError):
    """Raised when immutable analysis persistence cannot be proven safe."""


@runtime_checkable
class GitHubResearchLoveSqlAuthorityStore(Protocol):
    """Existing SQL-authority surface reused by this unit."""

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
class GitHubResearchLoveSqlPersistencePlan:
    """Deterministic immutable SQL entities for both specialist analyses."""

    schema: str
    parent_revision_ref: str
    first_object: ContextAuthorityObject
    second_object: ContextAuthorityObject
    first_artifact: ContextArtifactDescriptor
    second_artifact: ContextArtifactDescriptor
    revision: ContextRevision
    work_package_ref: str
    plan_digest: str = field(init=False)
    boundaries: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != PLAN_SCHEMA:
            raise GitHubResearchLoveSqlPersistenceError(
                "unsupported SQL persistence plan schema"
            )
        if not self.parent_revision_ref.startswith("context-revision:"):
            raise GitHubResearchLoveSqlPersistenceError(
                "parent_revision_ref must start with context-revision:"
            )
        if not self.work_package_ref.startswith("research-work-package:"):
            raise GitHubResearchLoveSqlPersistenceError(
                "work_package_ref must start with research-work-package:"
            )
        if self.revision.parent_revision_refs != (self.parent_revision_ref,):
            raise GitHubResearchLoveSqlPersistenceError(
                "analysis revision must have exactly the installed base revision "
                "as parent"
            )
        expected_refs = (
            self.first_object.object_ref,
            self.first_artifact.artifact_ref,
            self.second_object.object_ref,
            self.second_artifact.artifact_ref,
        )
        active_refs = tuple(
            membership.object_ref
            for membership in self.revision.memberships
            if membership.state == "active"
        )
        if active_refs != expected_refs:
            raise GitHubResearchLoveSqlPersistenceError(
                "analysis revision membership order or content mismatch"
            )
        if self.first_object.object_ref == self.second_object.object_ref:
            raise GitHubResearchLoveSqlPersistenceError(
                "specialist analyses must remain distinct SQL objects"
            )
        if self.first_artifact.artifact_ref == self.second_artifact.artifact_ref:
            raise GitHubResearchLoveSqlPersistenceError(
                "specialist analyses must remain distinct artifacts"
            )
        if self.revision.validation_status != "accepted":
            raise GitHubResearchLoveSqlPersistenceError(
                "analysis revision must be accepted"
            )
        object.__setattr__(
            self,
            "boundaries",
            MappingProxyType(dict(self.boundaries)),
        )
        object.__setattr__(self, "plan_digest", _plan_digest(self))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "plan_digest": self.plan_digest,
            "parent_revision_ref": self.parent_revision_ref,
            "work_package_ref": self.work_package_ref,
            "first_object": self.first_object.to_mapping(),
            "second_object": self.second_object.to_mapping(),
            "first_artifact": self.first_artifact.to_mapping(),
            "second_artifact": self.second_artifact.to_mapping(),
            "revision": self.revision.to_mapping(),
            "boundaries": dict(self.boundaries),
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveSqlPersistenceReadiness:
    """Read-only immutable collision inspection before SQL writes."""

    schema: str
    plan_digest: str
    ready: bool
    issues: tuple[str, ...]
    states: Mapping[str, str]

    def __post_init__(self) -> None:
        if self.schema != READINESS_SCHEMA:
            raise GitHubResearchLoveSqlPersistenceError(
                "unsupported SQL persistence readiness schema"
            )
        object.__setattr__(self, "states", MappingProxyType(dict(self.states)))

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
                "global_synthesis_created": False,
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveSqlPersistenceReceipt:
    """Exact SQL write/readback evidence for both analyses."""

    schema: str
    plan_digest: str
    work_package_ref: str
    first_object_ref: str
    second_object_ref: str
    first_artifact_ref: str
    second_artifact_ref: str
    revision_ref: str
    writes: Mapping[str, Mapping[str, bool]]
    readback_verified: bool
    action: str

    def __post_init__(self) -> None:
        if self.schema != RECEIPT_SCHEMA:
            raise GitHubResearchLoveSqlPersistenceError(
                "unsupported SQL persistence receipt schema"
            )
        if self.action not in {"created", "replay", "mixed"}:
            raise GitHubResearchLoveSqlPersistenceError(
                "receipt action must be created, replay or mixed"
            )
        frozen_writes = {
            key: MappingProxyType(dict(value))
            for key, value in self.writes.items()
        }
        object.__setattr__(self, "writes", MappingProxyType(frozen_writes))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "plan_digest": self.plan_digest,
            "work_package_ref": self.work_package_ref,
            "first_object_ref": self.first_object_ref,
            "second_object_ref": self.second_object_ref,
            "first_artifact_ref": self.first_artifact_ref,
            "second_artifact_ref": self.second_artifact_ref,
            "revision_ref": self.revision_ref,
            "writes": {
                key: dict(value)
                for key, value in self.writes.items()
            },
            "readback_verified": self.readback_verified,
            "action": self.action,
            "boundaries": {
                "sql_write_performed": True,
                "sql_remains_authority": True,
                "two_analyses_remain_distinct": True,
                "child_revision_written_last": True,
                "restart_safe": True,
                "qdrant_write_performed": False,
                "openvino_inference_performed": False,
                "global_synthesis_created": False,
                "github_mutation_performed": False,
                "scheduler_created": False,
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveSqlPersistenceResult:
    """Convenience result containing the deterministic plan and receipt."""

    schema: str
    valid: bool
    status: str
    issues: tuple[str, ...]
    plan: GitHubResearchLoveSqlPersistencePlan | None = None
    readiness: GitHubResearchLoveSqlPersistenceReadiness | None = None
    receipt: GitHubResearchLoveSqlPersistenceReceipt | None = None

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "status": self.status,
            "issues": list(self.issues),
            "plan": self.plan.to_mapping() if self.plan is not None else None,
            "readiness": (
                self.readiness.to_mapping()
                if self.readiness is not None
                else None
            ),
            "receipt": (
                self.receipt.to_mapping() if self.receipt is not None else None
            ),
            "first_analysis_persisted": bool(
                self.receipt and self.receipt.readback_verified
            ),
            "second_analysis_persisted": bool(
                self.receipt and self.receipt.readback_verified
            ),
            "qdrant_write_performed": False,
            "global_synthesis_created": False,
        }


def build_github_research_love_sql_persistence_plan(
    *,
    runtime_ports: ImportedActionsRuntimePorts,
    first_dispatch: Mapping[str, Any],
    second_dispatch: Mapping[str, Any],
    created_at: str,
) -> GitHubResearchLoveSqlPersistencePlan:
    """Build two immutable objects/artifacts and one accepted child revision."""

    ports = validate_imported_actions_runtime_ports(runtime_ports)
    if not isinstance(first_dispatch, Mapping):
        raise TypeError("first_dispatch must be a mapping")
    if not isinstance(second_dispatch, Mapping):
        raise TypeError("second_dispatch must be a mapping")
    created_at = _utc_text("created_at", created_at)

    first_result, first_task, first_visit, work_package_ref = (
        _validated_first_dispatch(first_dispatch)
    )
    second_result, second_task, second_visit = _validated_second_dispatch(
        second_dispatch,
        work_package_ref=work_package_ref,
        first_visit_ref=_required_text(first_visit, "visit_ref"),
    )
    if _required_text(second_visit, "parent_visit_ref") != _required_text(
        first_visit,
        "visit_ref",
    ):
        raise GitHubResearchLoveSqlPersistenceError(
            "second visit does not continue the first visit"
        )

    authority_store = _authority_store(ports.authority_store)
    parent = authority_store.get_revision(ports.base_revision_ref)
    if parent is None:
        raise GitHubResearchLoveSqlPersistenceError(
            "installed base revision does not exist"
        )
    if parent.validation_status != "accepted":
        raise GitHubResearchLoveSqlPersistenceError(
            "installed base revision is not accepted"
        )

    first_body, first_digest = _canonical_body_and_digest(first_result)
    second_body, second_digest = _canonical_body_and_digest(second_result)
    pair_digest = hashlib.sha256(
        (
            work_package_ref
            + "|"
            + first_digest
            + "|"
            + second_digest
        ).encode("utf-8")
    ).hexdigest()
    suffix = pair_digest[:20]

    first_object = _authority_object(
        stage="first",
        suffix=suffix,
        result=first_result,
        task=first_task,
        visit=first_visit,
        body=first_body,
        digest=first_digest,
        work_package_ref=work_package_ref,
    )
    second_object = _authority_object(
        stage="second",
        suffix=suffix,
        result=second_result,
        task=second_task,
        visit=second_visit,
        body=second_body,
        digest=second_digest,
        work_package_ref=work_package_ref,
    )
    first_artifact = _artifact_descriptor(
        stage="first",
        suffix=suffix,
        authority_object=first_object,
        result=first_result,
        task=first_task,
        visit=first_visit,
        created_at=created_at,
        work_package_ref=work_package_ref,
    )
    second_artifact = _artifact_descriptor(
        stage="second",
        suffix=suffix,
        authority_object=second_object,
        result=second_result,
        task=second_task,
        visit=second_visit,
        created_at=created_at,
        work_package_ref=work_package_ref,
    )
    memberships = tuple(
        ContextRevisionMembership(
            schema=CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
            object_ref=ref,
            state="active",
        )
        for ref in (
            first_object.object_ref,
            first_artifact.artifact_ref,
            second_object.object_ref,
            second_artifact.artifact_ref,
        )
    )
    revision = ContextRevision(
        schema=CONTEXT_REVISION_SCHEMA,
        revision_ref=f"context-revision:github-love-pair-{suffix}",
        context_ref=parent.context_ref,
        parent_revision_refs=(ports.base_revision_ref,),
        memberships=memberships,
        validation_status="accepted",
        significance="minor",
        evidence_refs=(
            first_artifact.artifact_ref,
            second_artifact.artifact_ref,
        ),
        created_at=created_at,
        metadata={
            "purpose": "github-research-two-specialist-analysis-persistence",
            "work_package_ref": work_package_ref,
            "first_analysis_object_ref": first_object.object_ref,
            "second_analysis_object_ref": second_object.object_ref,
            "analyses_kept_distinct": True,
            "global_synthesis_created": False,
        },
    )
    return GitHubResearchLoveSqlPersistencePlan(
        schema=PLAN_SCHEMA,
        parent_revision_ref=ports.base_revision_ref,
        first_object=first_object,
        second_object=second_object,
        first_artifact=first_artifact,
        second_artifact=second_artifact,
        revision=revision,
        work_package_ref=work_package_ref,
        boundaries={
            "preview_first": True,
            "sql_only": True,
            "base_revision_mutated": False,
            "two_analyses_remain_distinct": True,
            "qdrant_write_performed": False,
            "global_synthesis_created": False,
            "scheduler_constructed": False,
            "restart_safe": True,
        },
    )


def inspect_github_research_love_sql_persistence(
    authority_store: GitHubResearchLoveSqlAuthorityStore,
    plan: GitHubResearchLoveSqlPersistencePlan,
) -> GitHubResearchLoveSqlPersistenceReadiness:
    """Read parent and immutable entities without performing writes."""

    store = _authority_store(authority_store)
    parent = store.get_revision(plan.parent_revision_ref)
    values = {
        "first_object": (
            store.get_object(plan.first_object.object_ref),
            plan.first_object,
        ),
        "second_object": (
            store.get_object(plan.second_object.object_ref),
            plan.second_object,
        ),
        "first_artifact": (
            store.get_artifact(plan.first_artifact.artifact_ref),
            plan.first_artifact,
        ),
        "second_artifact": (
            store.get_artifact(plan.second_artifact.artifact_ref),
            plan.second_artifact,
        ),
        "revision": (
            store.get_revision(plan.revision.revision_ref),
            plan.revision,
        ),
    }
    states = {
        name: _immutable_state(existing, expected)
        for name, (existing, expected) in values.items()
    }
    issues: list[str] = []
    if parent is None:
        issues.append("installed base revision does not exist")
    else:
        if parent.validation_status != "accepted":
            issues.append("installed base revision is not accepted")
        if parent.context_ref != plan.revision.context_ref:
            issues.append("child revision context_ref differs from base revision")
    for name, state in states.items():
        if state == "collision":
            issues.append(f"immutable {name} collision")
    if states["revision"] == "identical":
        for name in (
            "first_object",
            "second_object",
            "first_artifact",
            "second_artifact",
        ):
            if states[name] != "identical":
                issues.append(
                    "existing child revision requires every member to exist "
                    f"identically: {name}"
                )
    return GitHubResearchLoveSqlPersistenceReadiness(
        schema=READINESS_SCHEMA,
        plan_digest=plan.plan_digest,
        ready=not issues,
        issues=tuple(issues),
        states=states,
    )


def execute_github_research_love_sql_persistence(
    authority_store: GitHubResearchLoveSqlAuthorityStore,
    plan: GitHubResearchLoveSqlPersistencePlan,
) -> GitHubResearchLoveSqlPersistenceReceipt:
    """Write immutable entities, child revision last, then verify exact readback."""

    store = _authority_store(authority_store)
    readiness = inspect_github_research_love_sql_persistence(store, plan)
    if not readiness.ready:
        raise GitHubResearchLoveSqlPersistenceError(
            "SQL persistence readiness failed: " + "; ".join(readiness.issues)
        )

    first_object_write = store.put_object(plan.first_object)
    second_object_write = store.put_object(plan.second_object)
    first_artifact_write = store.put_artifact(plan.first_artifact)
    second_artifact_write = store.put_artifact(plan.second_artifact)
    revision_write = store.put_revision(plan.revision)

    expected_readback = (
        (store.get_object(plan.first_object.object_ref), plan.first_object),
        (store.get_object(plan.second_object.object_ref), plan.second_object),
        (
            store.get_artifact(plan.first_artifact.artifact_ref),
            plan.first_artifact,
        ),
        (
            store.get_artifact(plan.second_artifact.artifact_ref),
            plan.second_artifact,
        ),
        (store.get_revision(plan.revision.revision_ref), plan.revision),
    )
    if any(_immutable_state(actual, expected) != "identical"
           for actual, expected in expected_readback):
        raise GitHubResearchLoveSqlPersistenceError(
            "SQL analysis persistence readback mismatch"
        )

    writes = {
        "first_object": _write_mapping(first_object_write),
        "second_object": _write_mapping(second_object_write),
        "first_artifact": _write_mapping(first_artifact_write),
        "second_artifact": _write_mapping(second_artifact_write),
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
    return GitHubResearchLoveSqlPersistenceReceipt(
        schema=RECEIPT_SCHEMA,
        plan_digest=plan.plan_digest,
        work_package_ref=plan.work_package_ref,
        first_object_ref=plan.first_object.object_ref,
        second_object_ref=plan.second_object.object_ref,
        first_artifact_ref=plan.first_artifact.artifact_ref,
        second_artifact_ref=plan.second_artifact.artifact_ref,
        revision_ref=plan.revision.revision_ref,
        writes=writes,
        readback_verified=True,
        action=action,
    )


def persist_github_research_love_analyses(
    *,
    runtime_ports: ImportedActionsRuntimePorts,
    first_dispatch: Mapping[str, Any],
    second_dispatch: Mapping[str, Any],
    created_at: str,
) -> GitHubResearchLoveSqlPersistenceResult:
    """Build, inspect and execute the bounded SQL-only persistence use-case."""

    try:
        ports = validate_imported_actions_runtime_ports(runtime_ports)
        plan = build_github_research_love_sql_persistence_plan(
            runtime_ports=ports,
            first_dispatch=first_dispatch,
            second_dispatch=second_dispatch,
            created_at=created_at,
        )
        readiness = inspect_github_research_love_sql_persistence(
            _authority_store(ports.authority_store),
            plan,
        )
        if not readiness.ready:
            return GitHubResearchLoveSqlPersistenceResult(
                schema=RESULT_SCHEMA,
                valid=False,
                status="not-ready",
                issues=readiness.issues,
                plan=plan,
                readiness=readiness,
            )
        receipt = execute_github_research_love_sql_persistence(
            _authority_store(ports.authority_store),
            plan,
        )
        return GitHubResearchLoveSqlPersistenceResult(
            schema=RESULT_SCHEMA,
            valid=True,
            status="persisted",
            issues=(),
            plan=plan,
            readiness=readiness,
            receipt=receipt,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        return GitHubResearchLoveSqlPersistenceResult(
            schema=RESULT_SCHEMA,
            valid=False,
            status="failed",
            issues=(f"{type(exc).__name__}: {exc}",),
        )


def _validated_first_dispatch(
    value: Mapping[str, Any],
) -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], str]:
    if value.get("schema") != FIRST_VISIT_DISPATCH_SCHEMA:
        raise GitHubResearchLoveSqlPersistenceError(
            "unsupported first-visit dispatch schema"
        )
    if value.get("valid") is not True:
        raise GitHubResearchLoveSqlPersistenceError(
            "first specialist dispatch must be valid"
        )
    if value.get("status") != "first-specialist-completed":
        raise GitHubResearchLoveSqlPersistenceError(
            "first specialist dispatch is not completed"
        )
    work_package_ref = _required_text(value, "work_package_ref")
    surface = _required_mapping(value, "surface")
    first_task = _required_mapping(surface, "first_task")
    first_visit = _required_mapping(surface, "first_visit")
    receipt = _required_mapping(value, "scheduler_receipt")
    execution = _required_mapping(receipt, "execution")
    if execution.get("specialist_stage") != "first_analysis":
        raise GitHubResearchLoveSqlPersistenceError(
            "first receipt stage mismatch"
        )
    if execution.get("result_valid") is not True:
        raise GitHubResearchLoveSqlPersistenceError(
            "first analysis is not valid"
        )
    result = _required_mapping(execution, "result")
    _validate_visit_result(result, visit=first_visit, task=first_task)
    return result, first_task, first_visit, work_package_ref


def _validated_second_dispatch(
    value: Mapping[str, Any],
    *,
    work_package_ref: str,
    first_visit_ref: str,
) -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]]:
    if value.get("schema") != SECOND_VISIT_DISPATCH_SCHEMA:
        raise GitHubResearchLoveSqlPersistenceError(
            "unsupported second-visit dispatch schema"
        )
    if value.get("valid") is not True:
        raise GitHubResearchLoveSqlPersistenceError(
            "second specialist dispatch must be valid"
        )
    if value.get("status") != "second-specialist-completed":
        raise GitHubResearchLoveSqlPersistenceError(
            "second specialist dispatch is not completed"
        )
    if value.get("work_package_ref") != work_package_ref:
        raise GitHubResearchLoveSqlPersistenceError(
            "specialist dispatch work_package_ref mismatch"
        )
    if value.get("first_visit_ref") != first_visit_ref:
        raise GitHubResearchLoveSqlPersistenceError(
            "second dispatch first_visit_ref mismatch"
        )
    preparation = _required_mapping(value, "preparation")
    second_task = _required_mapping(preparation, "second_task")
    second_visit = _required_mapping(preparation, "second_visit")
    receipt = _required_mapping(value, "scheduler_receipt")
    execution = _required_mapping(receipt, "execution")
    if execution.get("specialist_stage") != "second_analysis":
        raise GitHubResearchLoveSqlPersistenceError(
            "second receipt stage mismatch"
        )
    if execution.get("result_valid") is not True:
        raise GitHubResearchLoveSqlPersistenceError(
            "second analysis is not valid"
        )
    result = _required_mapping(execution, "result")
    _validate_visit_result(result, visit=second_visit, task=second_task)
    return result, second_task, second_visit


def _validate_visit_result(
    result: Mapping[str, Any],
    *,
    visit: Mapping[str, Any],
    task: Mapping[str, Any],
) -> None:
    if result.get("schema") != "missipy.laboratory.visit_result.v1":
        raise GitHubResearchLoveSqlPersistenceError(
            "unsupported laboratory visit result schema"
        )
    if result.get("status") != "completed":
        raise GitHubResearchLoveSqlPersistenceError(
            "laboratory visit result must be completed"
        )
    if result.get("visit_ref") != visit.get("visit_ref"):
        raise GitHubResearchLoveSqlPersistenceError(
            "laboratory result visit_ref mismatch"
        )
    if result.get("specialist_ref") != visit.get("specialist_ref"):
        raise GitHubResearchLoveSqlPersistenceError(
            "laboratory result specialist_ref mismatch"
        )
    if result.get("laboratory_ref") != visit.get("laboratory_ref"):
        raise GitHubResearchLoveSqlPersistenceError(
            "laboratory result laboratory_ref mismatch"
        )
    if result.get("output_contract_ref") != task.get(
        "expected_output_contract_ref"
    ):
        raise GitHubResearchLoveSqlPersistenceError(
            "laboratory result output contract mismatch"
        )
    machine_result = _required_mapping(result, "machine_result")
    if not _optional_text(machine_result.get("schema")):
        raise GitHubResearchLoveSqlPersistenceError(
            "analysis machine_result schema must not be empty"
        )
    if not _optional_text(machine_result.get("analysis_ref")):
        raise GitHubResearchLoveSqlPersistenceError(
            "analysis_ref must not be empty"
        )
    if machine_result.get("specialist_ref") != result.get("specialist_ref"):
        raise GitHubResearchLoveSqlPersistenceError(
            "analysis and visit specialist_ref mismatch"
        )


def _authority_object(
    *,
    stage: str,
    suffix: str,
    result: Mapping[str, Any],
    task: Mapping[str, Any],
    visit: Mapping[str, Any],
    body: str,
    digest: str,
    work_package_ref: str,
) -> ContextAuthorityObject:
    machine_result = _required_mapping(result, "machine_result")
    title = (
        "Analyse conceptuelle et affective"
        if stage == "first"
        else "Analyse des dynamiques relationnelles"
    )
    return ContextAuthorityObject(
        schema=CONTEXT_AUTHORITY_OBJECT_SCHEMA,
        object_ref=f"context-object:github-love-{stage}-{suffix}",
        object_kind="specialist-analysis",
        content_schema_ref=_required_text(machine_result, "schema"),
        content_digest=digest,
        title=title,
        body=body,
        media_type="application/json",
        byte_count=len(body.encode("utf-8")),
        metadata={
            "stage": stage,
            "work_package_ref": work_package_ref,
            "analysis_ref": _required_text(machine_result, "analysis_ref"),
            "visit_ref": _required_text(visit, "visit_ref"),
            "task_ref": _required_text(task, "task_ref"),
            "specialist_ref": _required_text(result, "specialist_ref"),
            "laboratory_ref": _required_text(result, "laboratory_ref"),
            "contribution_kind": machine_result.get(
                "contribution_kind",
                "domain_analysis",
            ),
            "global_synthesis_created": False,
        },
    )


def _artifact_descriptor(
    *,
    stage: str,
    suffix: str,
    authority_object: ContextAuthorityObject,
    result: Mapping[str, Any],
    task: Mapping[str, Any],
    visit: Mapping[str, Any],
    created_at: str,
    work_package_ref: str,
) -> ContextArtifactDescriptor:
    return ContextArtifactDescriptor(
        schema=CONTEXT_ARTIFACT_DESCRIPTOR_SCHEMA,
        artifact_ref=f"artifact:github-love-{stage}-{suffix}",
        content_schema_ref=authority_object.content_schema_ref,
        content_digest=authority_object.content_digest,
        storage_ref=f"sql:{authority_object.object_ref}",
        media_type=authority_object.media_type,
        byte_count=authority_object.byte_count,
        producer_task_ref=_required_text(task, "task_ref"),
        producer_specialist_ref=_required_text(result, "specialist_ref"),
        producer_laboratory_ref=_required_text(result, "laboratory_ref"),
        created_at=created_at,
        metadata={
            "stage": stage,
            "work_package_ref": work_package_ref,
            "authority_object_ref": authority_object.object_ref,
            "visit_ref": _required_text(visit, "visit_ref"),
            "sql_remains_authority": True,
        },
    )


def _canonical_body_and_digest(
    value: Mapping[str, Any],
) -> tuple[str, str]:
    body = json.dumps(
        dict(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()
    return body, digest


def _authority_store(value: object) -> GitHubResearchLoveSqlAuthorityStore:
    if not isinstance(value, GitHubResearchLoveSqlAuthorityStore):
        raise GitHubResearchLoveSqlPersistenceError(
            "authority_store does not expose object/artifact/revision SQL methods"
        )
    return value


def _immutable_state(existing: object | None, expected: object) -> str:
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


def _write_mapping(value: ContextSqlWriteResult) -> Mapping[str, bool]:
    return {
        "inserted": bool(value.inserted),
        "idempotent_replay": bool(value.idempotent_replay),
    }


def _plan_digest(plan: GitHubResearchLoveSqlPersistencePlan) -> str:
    payload = {
        "schema": plan.schema,
        "parent_revision_ref": plan.parent_revision_ref,
        "work_package_ref": plan.work_package_ref,
        "first_object": plan.first_object.to_mapping(),
        "second_object": plan.second_object.to_mapping(),
        "first_artifact": plan.first_artifact.to_mapping(),
        "second_artifact": plan.second_artifact.to_mapping(),
        "revision": plan.revision.to_mapping(),
        "boundaries": dict(plan.boundaries),
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
        raise GitHubResearchLoveSqlPersistenceError(
            f"{name} must be an object"
        )
    return candidate


def _required_text(value: Mapping[str, Any], name: str) -> str:
    text = _optional_text(value.get(name))
    if not text:
        raise GitHubResearchLoveSqlPersistenceError(
            f"{name} must not be empty"
        )
    return text


def _optional_text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _utc_text(name: str, value: object) -> str:
    text = _optional_text(value)
    if "T" not in text or not text.endswith("Z"):
        raise GitHubResearchLoveSqlPersistenceError(
            f"{name} must be a UTC timestamp ending with Z"
        )
    return text


__all__ = (
    "GitHubResearchLoveSqlAuthorityStore",
    "GitHubResearchLoveSqlPersistenceError",
    "GitHubResearchLoveSqlPersistencePlan",
    "GitHubResearchLoveSqlPersistenceReadiness",
    "GitHubResearchLoveSqlPersistenceReceipt",
    "GitHubResearchLoveSqlPersistenceResult",
    "PLAN_SCHEMA",
    "READINESS_SCHEMA",
    "RECEIPT_SCHEMA",
    "RESULT_SCHEMA",
    "build_github_research_love_sql_persistence_plan",
    "execute_github_research_love_sql_persistence",
    "inspect_github_research_love_sql_persistence",
    "persist_github_research_love_analyses",
)
