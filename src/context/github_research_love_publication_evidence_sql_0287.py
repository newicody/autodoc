"""Persist exact remote publication evidence and close the research cycle.

This unit consumes:
- the durable final-deliverable result from r16-r16;
- the successful, exact-readback remote publication result from r16-r17.

It creates one immutable publication-evidence authority object, one artifact
descriptor and one accepted child revision.  The child revision carries the
closed-cycle state and descends from the final-deliverable revision.

No remote publication call is made here.  The Issue comment and ProjectV2 field
are never written or read again by this unit.  SQL remains the durable authority.
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
from context.github_research_love_final_deliverable_sql_0287 import (
    RECEIPT_SCHEMA as FINAL_SQL_RECEIPT_SCHEMA,
    RESULT_SCHEMA as FINAL_SQL_RESULT_SCHEMA,
)
from context.github_research_love_final_remote_publication_0287 import (
    RESULT_SCHEMA as FINAL_REMOTE_PUBLICATION_RESULT_SCHEMA,
)
from context.love_final_deliverable_remote_publication_0287 import (
    LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_RESULT_SCHEMA,
)
from context.love_imported_actions_runtime_contract_0287 import (
    ImportedActionsRuntimePorts,
    validate_imported_actions_runtime_ports,
)

EVIDENCE_SCHEMA = "missipy.github.research_love_publication_evidence.v1"
PLAN_SCHEMA = "missipy.github.research_love_publication_evidence_sql_plan.v1"
READINESS_SCHEMA = (
    "missipy.github.research_love_publication_evidence_sql_readiness.v1"
)
RECEIPT_SCHEMA = (
    "missipy.github.research_love_publication_evidence_sql_receipt.v1"
)
RESULT_SCHEMA = "missipy.github.research_love_cycle_closure_result.v1"

_ALLOWED_REMOTE_ACTIONS = frozenset(
    {"created_and_projected", "created_issue", "projected", "replay"}
)
_SHA256_HEX_LENGTH = 64


class GitHubResearchLovePublicationEvidenceError(RuntimeError):
    """Raised when publication proof or immutable SQL closure is invalid."""


@runtime_checkable
class GitHubResearchLovePublicationEvidenceStore(Protocol):
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
class GitHubResearchLovePublicationEvidenceCommand:
    runtime_ports: ImportedActionsRuntimePorts
    final_deliverable: Mapping[str, Any]
    remote_publication: Mapping[str, Any]
    closed_at: str

    def __post_init__(self) -> None:
        if not isinstance(self.final_deliverable, Mapping):
            raise TypeError("final_deliverable must be a mapping")
        if not isinstance(self.remote_publication, Mapping):
            raise TypeError("remote_publication must be a mapping")
        timestamp = self.closed_at.strip()
        if "T" not in timestamp or not timestamp.endswith("Z"):
            raise GitHubResearchLovePublicationEvidenceError(
                "closed_at must be a UTC timestamp ending with Z"
            )
        object.__setattr__(self, "closed_at", timestamp)


@dataclass(frozen=True, slots=True)
class GitHubResearchLovePublicationEvidencePlan:
    schema: str
    work_package_ref: str
    parent_revision_ref: str
    final_sql_plan_digest: str
    publication_plan_digest: str
    publication_lineage_digest: str
    authority_object: ContextAuthorityObject
    artifact: ContextArtifactDescriptor
    revision: ContextRevision
    plan_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema != PLAN_SCHEMA:
            raise GitHubResearchLovePublicationEvidenceError(
                "unsupported publication evidence plan schema"
            )
        if not self.work_package_ref.startswith("research-work-package:"):
            raise GitHubResearchLovePublicationEvidenceError(
                "work_package_ref must start with research-work-package:"
            )
        if not self.parent_revision_ref.startswith("context-revision:"):
            raise GitHubResearchLovePublicationEvidenceError(
                "parent_revision_ref must start with context-revision:"
            )
        for name, value in (
            ("final_sql_plan_digest", self.final_sql_plan_digest),
            ("publication_plan_digest", self.publication_plan_digest),
            ("publication_lineage_digest", self.publication_lineage_digest),
        ):
            if not value.startswith("sha256:") or len(value) != 71:
                raise GitHubResearchLovePublicationEvidenceError(
                    f"{name} must be sha256:*"
                )
        if self.revision.parent_revision_refs != (self.parent_revision_ref,):
            raise GitHubResearchLovePublicationEvidenceError(
                "closure revision must descend from final deliverable revision"
            )
        active_refs = tuple(
            membership.object_ref
            for membership in self.revision.memberships
            if membership.state == "active"
        )
        if active_refs != (
            self.authority_object.object_ref,
            self.artifact.artifact_ref,
        ):
            raise GitHubResearchLovePublicationEvidenceError(
                "closure revision membership mismatch"
            )
        if self.revision.validation_status != "accepted":
            raise GitHubResearchLovePublicationEvidenceError(
                "closure revision must be accepted"
            )
        if self.revision.metadata.get("cycle_status") != "closed":
            raise GitHubResearchLovePublicationEvidenceError(
                "closure revision must declare cycle_status=closed"
            )
        object.__setattr__(self, "plan_digest", _plan_digest(self))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "plan_digest": self.plan_digest,
            "work_package_ref": self.work_package_ref,
            "parent_revision_ref": self.parent_revision_ref,
            "final_sql_plan_digest": self.final_sql_plan_digest,
            "publication_plan_digest": self.publication_plan_digest,
            "publication_lineage_digest": self.publication_lineage_digest,
            "authority_object": self.authority_object.to_mapping(),
            "artifact": self.artifact.to_mapping(),
            "revision": self.revision.to_mapping(),
            "boundaries": {
                "remote_publication_reexecuted": False,
                "remote_readback_reexecuted": False,
                "sql_write_planned": True,
                "qdrant_write_performed": False,
                "scheduler_created": False,
                "cycle_status": "closed",
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLovePublicationEvidenceReadiness:
    schema: str
    plan_digest: str
    ready: bool
    issues: tuple[str, ...]
    states: Mapping[str, str]

    def __post_init__(self) -> None:
        if self.schema != READINESS_SCHEMA:
            raise GitHubResearchLovePublicationEvidenceError(
                "unsupported publication evidence readiness schema"
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
                "remote_mutation_performed": False,
                "sql_write_performed": False,
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLovePublicationEvidenceReceipt:
    schema: str
    plan_digest: str
    evidence_object_ref: str
    evidence_artifact_ref: str
    closure_revision_ref: str
    writes: Mapping[str, Mapping[str, bool]]
    readback_verified: bool
    action: str

    def __post_init__(self) -> None:
        if self.schema != RECEIPT_SCHEMA:
            raise GitHubResearchLovePublicationEvidenceError(
                "unsupported publication evidence receipt schema"
            )
        if self.action not in {"created", "replay", "mixed"}:
            raise GitHubResearchLovePublicationEvidenceError(
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
            "evidence_object_ref": self.evidence_object_ref,
            "evidence_artifact_ref": self.evidence_artifact_ref,
            "closure_revision_ref": self.closure_revision_ref,
            "writes": {
                key: dict(value)
                for key, value in self.writes.items()
            },
            "readback_verified": self.readback_verified,
            "action": self.action,
            "cycle_status": "closed",
            "boundaries": {
                "publication_evidence_persisted": True,
                "cycle_closed": True,
                "sql_remains_authority": True,
                "closure_revision_written_last": True,
                "restart_safe": True,
                "remote_publication_reexecuted": False,
                "remote_readback_reexecuted": False,
                "github_mutation_performed": False,
                "projectv2_mutation_performed": False,
                "qdrant_write_performed": False,
                "scheduler_created": False,
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveCycleClosureResult:
    schema: str
    valid: bool
    status: str
    issues: tuple[str, ...]
    plan: GitHubResearchLovePublicationEvidencePlan | None = None
    readiness: GitHubResearchLovePublicationEvidenceReadiness | None = None
    receipt: GitHubResearchLovePublicationEvidenceReceipt | None = None

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
            "publication_evidence_persisted": bool(
                self.receipt and self.receipt.readback_verified
            ),
            "cycle_closed": bool(
                self.receipt and self.receipt.readback_verified
            ),
            "remote_publication_reexecuted": False,
        }


def build_github_research_love_publication_evidence_plan(
    command: GitHubResearchLovePublicationEvidenceCommand,
) -> GitHubResearchLovePublicationEvidencePlan:
    ports = validate_imported_actions_runtime_ports(command.runtime_ports)
    final = _validated_final_deliverable(command.final_deliverable)
    publication = _validated_remote_publication(
        command.remote_publication,
        final=final,
    )

    final_plan = final["plan"]
    final_receipt = final["receipt"]
    publication_plan = publication["publication_plan"]
    remote = publication["remote"]
    readback = publication["readback"]
    project_snapshot = publication["project_snapshot"]

    parent_revision_ref = _required_text(final_receipt, "revision_ref")
    store = _store(ports.authority_store)
    parent = store.get_revision(parent_revision_ref)
    if parent is None:
        raise GitHubResearchLovePublicationEvidenceError(
            "final deliverable revision does not exist"
        )
    if parent.validation_status != "accepted":
        raise GitHubResearchLovePublicationEvidenceError(
            "final deliverable revision is not accepted"
        )

    evidence_body_mapping = {
        "schema": EVIDENCE_SCHEMA,
        "work_package_ref": _required_text(
            final_plan,
            "work_package_ref",
        ),
        "final_sql_plan_digest": _required_text(
            final_plan,
            "plan_digest",
        ),
        "final_deliverable_revision_ref": parent_revision_ref,
        "final_authority_object_ref": _required_text(
            final_receipt,
            "authority_object_ref",
        ),
        "final_artifact_ref": _required_text(
            final_receipt,
            "artifact_ref",
        ),
        "final_packet_ref": _required_text(
            final_receipt,
            "packet_ref",
        ),
        "publication_plan_digest": _required_text(
            publication,
            "plan_digest",
        ),
        "publication_lineage_digest": _required_text(
            publication,
            "lineage_digest",
        ),
        "repository": _required_text(
            publication_plan,
            "repository",
        ),
        "issue_number": _positive_int(
            publication_plan,
            "issue_number",
        ),
        "issue_marker": _required_text(
            publication_plan,
            "marker",
        ),
        "issue_body_sha256": _required_text(
            publication_plan,
            "body_sha256",
        ),
        "issue_comment_id": _positive_int(
            remote,
            "issue_comment_id",
        ),
        "issue_comment_url": _required_https_url(
            remote,
            "issue_comment_url",
        ),
        "project_item_id": _required_text(
            project_snapshot,
            "project_item_id",
        ),
        "project_field_ref": _required_text(
            project_snapshot,
            "field_ref",
        ),
        "project_field_name": _required_text(
            project_snapshot,
            "field_name",
        ),
        "project_value": _required_text(
            project_snapshot,
            "value",
        ),
        "remote_action": _required_text(remote, "action"),
        "exact_readback_valid": readback.get("valid") is True,
        "closed_at": command.closed_at,
        "cycle_status": "closed",
        "closure_reason": "final-publication-readback-verified",
    }
    body = json.dumps(
        evidence_body_mapping,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    content_digest = (
        "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()
    )
    suffix = hashlib.sha256(
        (
            evidence_body_mapping["work_package_ref"]
            + "|"
            + evidence_body_mapping["publication_plan_digest"]
            + "|"
            + content_digest
        ).encode("utf-8")
    ).hexdigest()[:20]
    object_ref = f"context-object:github-love-publication-evidence-{suffix}"
    artifact_ref = f"artifact:github-love-publication-evidence-{suffix}"
    task_ref = f"task:github-love-close-cycle-{suffix}"

    authority_object = ContextAuthorityObject(
        schema=CONTEXT_AUTHORITY_OBJECT_SCHEMA,
        object_ref=object_ref,
        object_kind="remote-publication-evidence",
        content_schema_ref=EVIDENCE_SCHEMA,
        content_digest=content_digest,
        title="Preuve de publication finale et clôture du cycle",
        body=body,
        media_type="application/json",
        byte_count=len(body.encode("utf-8")),
        metadata={
            "work_package_ref": evidence_body_mapping["work_package_ref"],
            "publication_plan_digest": (
                evidence_body_mapping["publication_plan_digest"]
            ),
            "publication_lineage_digest": (
                evidence_body_mapping["publication_lineage_digest"]
            ),
            "final_packet_ref": evidence_body_mapping["final_packet_ref"],
            "issue_comment_url": (
                evidence_body_mapping["issue_comment_url"]
            ),
            "cycle_status": "closed",
            "closure_reason": (
                "final-publication-readback-verified"
            ),
            "remote_publication_reexecuted": False,
        },
    )
    artifact = ContextArtifactDescriptor(
        schema=CONTEXT_ARTIFACT_DESCRIPTOR_SCHEMA,
        artifact_ref=artifact_ref,
        content_schema_ref=EVIDENCE_SCHEMA,
        content_digest=content_digest,
        storage_ref=f"sql:{object_ref}",
        media_type="application/json",
        byte_count=len(body.encode("utf-8")),
        producer_task_ref=task_ref,
        created_at=command.closed_at,
        metadata={
            "authority_object_ref": object_ref,
            "work_package_ref": evidence_body_mapping["work_package_ref"],
            "publication_plan_digest": (
                evidence_body_mapping["publication_plan_digest"]
            ),
            "cycle_status": "closed",
            "sql_remains_authority": True,
        },
    )
    revision = ContextRevision(
        schema=CONTEXT_REVISION_SCHEMA,
        revision_ref=f"context-revision:github-love-closed-{suffix}",
        context_ref=parent.context_ref,
        parent_revision_refs=(parent_revision_ref,),
        memberships=(
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
        ),
        validation_status="accepted",
        significance="material",
        evidence_refs=(
            artifact_ref,
            f"sql:{_required_text(final_receipt, 'authority_object_ref')}",
            f"sql:{_required_text(final_receipt, 'artifact_ref')}",
        ),
        producer_task_ref=task_ref,
        created_at=command.closed_at,
        metadata={
            "purpose": "github-research-cycle-closure",
            "work_package_ref": evidence_body_mapping["work_package_ref"],
            "cycle_status": "closed",
            "closure_reason": "final-publication-readback-verified",
            "publication_evidence_object_ref": object_ref,
            "publication_evidence_artifact_ref": artifact_ref,
            "publication_plan_digest": (
                evidence_body_mapping["publication_plan_digest"]
            ),
            "publication_lineage_digest": (
                evidence_body_mapping["publication_lineage_digest"]
            ),
            "issue_comment_id": evidence_body_mapping["issue_comment_id"],
            "issue_comment_url": evidence_body_mapping["issue_comment_url"],
            "remote_publication_reexecuted": False,
            "remote_readback_reexecuted": False,
        },
    )
    return GitHubResearchLovePublicationEvidencePlan(
        schema=PLAN_SCHEMA,
        work_package_ref=evidence_body_mapping["work_package_ref"],
        parent_revision_ref=parent_revision_ref,
        final_sql_plan_digest=evidence_body_mapping[
            "final_sql_plan_digest"
        ],
        publication_plan_digest=evidence_body_mapping[
            "publication_plan_digest"
        ],
        publication_lineage_digest=evidence_body_mapping[
            "publication_lineage_digest"
        ],
        authority_object=authority_object,
        artifact=artifact,
        revision=revision,
    )


def inspect_github_research_love_publication_evidence(
    authority_store: GitHubResearchLovePublicationEvidenceStore,
    plan: GitHubResearchLovePublicationEvidencePlan,
) -> GitHubResearchLovePublicationEvidenceReadiness:
    store = _store(authority_store)
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
        issues.append("final deliverable revision does not exist")
    else:
        if parent.validation_status != "accepted":
            issues.append("final deliverable revision is not accepted")
        if parent.context_ref != plan.revision.context_ref:
            issues.append("closure revision context_ref differs from parent")
    for name, state in states.items():
        if state == "collision":
            issues.append(f"immutable {name} collision")
    if states["revision"] == "identical":
        for name in ("authority_object", "artifact"):
            if states[name] != "identical":
                issues.append(
                    "existing closure revision requires every member "
                    f"to exist identically: {name}"
                )
    return GitHubResearchLovePublicationEvidenceReadiness(
        schema=READINESS_SCHEMA,
        plan_digest=plan.plan_digest,
        ready=not issues,
        issues=tuple(issues),
        states=states,
    )


def execute_github_research_love_publication_evidence(
    authority_store: GitHubResearchLovePublicationEvidenceStore,
    plan: GitHubResearchLovePublicationEvidencePlan,
) -> GitHubResearchLovePublicationEvidenceReceipt:
    store = _store(authority_store)
    readiness = inspect_github_research_love_publication_evidence(
        store,
        plan,
    )
    if not readiness.ready:
        raise GitHubResearchLovePublicationEvidenceError(
            "publication evidence readiness failed: "
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
        raise GitHubResearchLovePublicationEvidenceError(
            "publication evidence SQL readback mismatch"
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
    return GitHubResearchLovePublicationEvidenceReceipt(
        schema=RECEIPT_SCHEMA,
        plan_digest=plan.plan_digest,
        evidence_object_ref=plan.authority_object.object_ref,
        evidence_artifact_ref=plan.artifact.artifact_ref,
        closure_revision_ref=plan.revision.revision_ref,
        writes=writes,
        readback_verified=True,
        action=action,
    )


def close_github_research_love_cycle(
    command: GitHubResearchLovePublicationEvidenceCommand,
) -> GitHubResearchLoveCycleClosureResult:
    try:
        ports = validate_imported_actions_runtime_ports(
            command.runtime_ports
        )
        plan = build_github_research_love_publication_evidence_plan(
            command
        )
        store = _store(ports.authority_store)
        readiness = inspect_github_research_love_publication_evidence(
            store,
            plan,
        )
        if not readiness.ready:
            return GitHubResearchLoveCycleClosureResult(
                schema=RESULT_SCHEMA,
                valid=False,
                status="not-ready",
                issues=readiness.issues,
                plan=plan,
                readiness=readiness,
            )
        receipt = execute_github_research_love_publication_evidence(
            store,
            plan,
        )
        return GitHubResearchLoveCycleClosureResult(
            schema=RESULT_SCHEMA,
            valid=True,
            status="closed",
            issues=(),
            plan=plan,
            readiness=readiness,
            receipt=receipt,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        return GitHubResearchLoveCycleClosureResult(
            schema=RESULT_SCHEMA,
            valid=False,
            status="failed",
            issues=(f"{type(exc).__name__}: {exc}",),
        )


def _validated_final_deliverable(
    value: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    if value.get("schema") != FINAL_SQL_RESULT_SCHEMA:
        raise GitHubResearchLovePublicationEvidenceError(
            "unsupported final deliverable result schema"
        )
    if value.get("valid") is not True or value.get("status") != "persisted":
        raise GitHubResearchLovePublicationEvidenceError(
            "final deliverable must be valid and persisted"
        )
    plan = _required_mapping(value, "plan")
    receipt = _required_mapping(value, "receipt")
    if receipt.get("schema") != FINAL_SQL_RECEIPT_SCHEMA:
        raise GitHubResearchLovePublicationEvidenceError(
            "unsupported final deliverable receipt schema"
        )
    if receipt.get("readback_verified") is not True:
        raise GitHubResearchLovePublicationEvidenceError(
            "final deliverable SQL readback must be verified"
        )
    if receipt.get("plan_digest") != plan.get("plan_digest"):
        raise GitHubResearchLovePublicationEvidenceError(
            "final deliverable plan digest mismatch"
        )
    return {"plan": plan, "receipt": receipt}


def _validated_remote_publication(
    value: Mapping[str, Any],
    *,
    final: Mapping[str, Mapping[str, Any]],
) -> dict[str, Mapping[str, Any] | str]:
    if value.get("schema") != FINAL_REMOTE_PUBLICATION_RESULT_SCHEMA:
        raise GitHubResearchLovePublicationEvidenceError(
            "unsupported final remote publication result schema"
        )
    if value.get("valid") is not True:
        raise GitHubResearchLovePublicationEvidenceError(
            "remote publication result must be valid"
        )
    if value.get("status") not in {"published", "published-replay"}:
        raise GitHubResearchLovePublicationEvidenceError(
            "remote publication status must be published or published-replay"
        )
    publication_plan = _required_mapping(value, "publication_plan")
    remote = _required_mapping(value, "remote_publication")
    if remote.get("schema") != (
        LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_RESULT_SCHEMA
    ):
        raise GitHubResearchLovePublicationEvidenceError(
            "unsupported controlled remote publication result schema"
        )
    if remote.get("valid") is not True or remote.get("mode") != "execute":
        raise GitHubResearchLovePublicationEvidenceError(
            "remote publication must be a valid execute result"
        )
    if remote.get("action") not in _ALLOWED_REMOTE_ACTIONS:
        raise GitHubResearchLovePublicationEvidenceError(
            "remote publication action is not complete"
        )
    if remote.get("partial_execution") is not False:
        raise GitHubResearchLovePublicationEvidenceError(
            "partial remote publication cannot close the cycle"
        )
    plan_digest = _required_text(value, "plan_digest")
    if remote.get("plan_digest") != plan_digest:
        raise GitHubResearchLovePublicationEvidenceError(
            "remote publication plan digest mismatch"
        )
    if publication_plan.get("plan_digest") != plan_digest:
        raise GitHubResearchLovePublicationEvidenceError(
            "publication plan digest mismatch"
        )
    typed_plan_digest = _typed_sha256_digest(
        plan_digest,
        name="publication_plan_digest",
    )
    readback = _required_mapping(remote, "readback")
    if readback.get("valid") is not True:
        raise GitHubResearchLovePublicationEvidenceError(
            "exact remote readback must be valid"
        )
    project_snapshot = _required_mapping(remote, "project_snapshot")

    final_plan = final["plan"]
    final_receipt = final["receipt"]
    if value.get("final_sql_revision_ref") != final_receipt.get(
        "revision_ref"
    ):
        raise GitHubResearchLovePublicationEvidenceError(
            "final SQL revision lineage mismatch"
        )
    if value.get("final_authority_object_ref") != final_receipt.get(
        "authority_object_ref"
    ):
        raise GitHubResearchLovePublicationEvidenceError(
            "final authority object lineage mismatch"
        )
    if value.get("final_artifact_ref") != final_receipt.get("artifact_ref"):
        raise GitHubResearchLovePublicationEvidenceError(
            "final artifact lineage mismatch"
        )
    if value.get("final_packet_ref") != final_receipt.get("packet_ref"):
        raise GitHubResearchLovePublicationEvidenceError(
            "final packet lineage mismatch"
        )
    if value.get("lineage_digest") != _required_text(
        value,
        "lineage_digest",
    ):
        raise GitHubResearchLovePublicationEvidenceError(
            "publication lineage digest is invalid"
        )
    if final_plan.get("plan_digest") != final_receipt.get("plan_digest"):
        raise GitHubResearchLovePublicationEvidenceError(
            "final SQL plan/receipt digest mismatch"
        )
    return {
        "publication_plan": publication_plan,
        "remote": remote,
        "readback": readback,
        "project_snapshot": project_snapshot,
        "plan_digest": typed_plan_digest,
        "lineage_digest": _required_text(value, "lineage_digest"),
    }


def _store(
    value: object,
) -> GitHubResearchLovePublicationEvidenceStore:
    if not isinstance(value, GitHubResearchLovePublicationEvidenceStore):
        raise GitHubResearchLovePublicationEvidenceError(
            "authority_store does not expose object/artifact/revision methods"
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


def _required_mapping(
    value: Mapping[str, Any],
    name: str,
) -> Mapping[str, Any]:
    candidate = value.get(name)
    if not isinstance(candidate, Mapping):
        raise GitHubResearchLovePublicationEvidenceError(
            f"{name} must be an object"
        )
    return candidate


def _required_text(
    value: Mapping[str, Any],
    name: str,
) -> str:
    candidate = value.get(name)
    if not isinstance(candidate, str) or not candidate.strip():
        raise GitHubResearchLovePublicationEvidenceError(
            f"{name} must not be empty"
        )
    return candidate.strip()


def _typed_sha256_digest(
    value: object,
    *,
    name: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GitHubResearchLovePublicationEvidenceError(
            f"{name} must not be empty"
        )
    normalized = value.strip()
    hexadecimal = (
        normalized.removeprefix("sha256:")
        if normalized.startswith("sha256:")
        else normalized
    )
    if (
        len(hexadecimal) != _SHA256_HEX_LENGTH
        or any(character not in "0123456789abcdef" for character in hexadecimal)
    ):
        raise GitHubResearchLovePublicationEvidenceError(
            f"{name} must be a lowercase sha256 digest"
        )
    return "sha256:" + hexadecimal


def _positive_int(
    value: Mapping[str, Any],
    name: str,
) -> int:
    candidate = value.get(name)
    if (
        isinstance(candidate, bool)
        or not isinstance(candidate, int)
        or candidate <= 0
    ):
        raise GitHubResearchLovePublicationEvidenceError(
            f"{name} must be a positive integer"
        )
    return candidate


def _required_https_url(
    value: Mapping[str, Any],
    name: str,
) -> str:
    candidate = _required_text(value, name)
    if not candidate.startswith("https://"):
        raise GitHubResearchLovePublicationEvidenceError(
            f"{name} must be an https URL"
        )
    return candidate


def _plan_digest(
    plan: GitHubResearchLovePublicationEvidencePlan,
) -> str:
    payload = {
        "schema": plan.schema,
        "work_package_ref": plan.work_package_ref,
        "parent_revision_ref": plan.parent_revision_ref,
        "final_sql_plan_digest": plan.final_sql_plan_digest,
        "publication_plan_digest": plan.publication_plan_digest,
        "publication_lineage_digest": plan.publication_lineage_digest,
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
    "EVIDENCE_SCHEMA",
    "GitHubResearchLoveCycleClosureResult",
    "GitHubResearchLovePublicationEvidenceCommand",
    "GitHubResearchLovePublicationEvidenceError",
    "GitHubResearchLovePublicationEvidencePlan",
    "GitHubResearchLovePublicationEvidenceReadiness",
    "GitHubResearchLovePublicationEvidenceReceipt",
    "GitHubResearchLovePublicationEvidenceStore",
    "PLAN_SCHEMA",
    "READINESS_SCHEMA",
    "RECEIPT_SCHEMA",
    "RESULT_SCHEMA",
    "build_github_research_love_publication_evidence_plan",
    "close_github_research_love_cycle",
    "execute_github_research_love_publication_evidence",
    "inspect_github_research_love_publication_evidence",
)
