"""Bridge the r16 final SQL deliverable to controlled Issue + ProjectV2 publication.

The repository already owns two canonical publication components:

- ``plan_love_final_deliverable_publication`` prepares a deterministic,
  collision-guarded Issue comment and one ProjectV2 field projection;
- ``execute_love_final_deliverable_remote_publication`` performs preview or
  controlled mutation through injected ports, requires three locks and the
  exact plan digest, then verifies exact remote readback.

This unit adapts the r16-r15 liaison and r16-r16 durable final packet to that
existing boundary.  It creates no GitHub client, subprocess, Scheduler, SQL
write, Qdrant write or new publication protocol.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any

from context.github_research_love_final_deliverable_sql_0287 import (
    RECEIPT_SCHEMA as FINAL_SQL_RECEIPT_SCHEMA,
    RESULT_SCHEMA as FINAL_SQL_RESULT_SCHEMA,
)
from context.github_research_love_liaison_synthesis_0287 import (
    RESULT_SCHEMA as LIAISON_RESULT_SCHEMA,
)
from context.love_final_deliverable_publication_plan_0287 import (
    R12_RESULT_SCHEMA,
    LoveFinalDeliverablePublicationCommand,
    LoveFinalDeliverablePublicationPlan,
    plan_love_final_deliverable_publication,
)
from context.love_final_deliverable_remote_publication_0287 import (
    LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_COMMAND_SCHEMA,
    FinalDeliverableIssuePublicationPort,
    FinalDeliverableProjectV2PublicationPort,
    LoveFinalDeliverableRemotePublicationCommand,
    LoveFinalDeliverableRemotePublicationResult,
    execute_love_final_deliverable_remote_publication,
)

PLAN_SCHEMA = "missipy.github.research_love_final_remote_publication_plan.v1"
RESULT_SCHEMA = "missipy.github.research_love_final_remote_publication_result.v1"

_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_ISSUE_REF_RE = re.compile(
    r"^github-frame:"
    r"(?P<repository>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"
    r"/issues/(?P<number>[1-9][0-9]*)$"
)


class GitHubResearchLoveFinalRemotePublicationError(RuntimeError):
    """Raised when final SQL lineage cannot enter the remote boundary safely."""


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveFinalPublicationCommand:
    """Pure plan inputs after ProjectV2 target resolution."""

    final_deliverable: Mapping[str, Any]
    liaison: Mapping[str, Any]
    repository: str
    issue_number: int
    source_issue_ref: str
    policy_decision_id: str
    operator_decision: str
    project_item_id: str
    project_field_ref: str
    project_field_name: str
    project_status_value: str = "Livrable final prêt"
    max_body_chars: int = 30_000
    max_project_value_chars: int = 500

    def __post_init__(self) -> None:
        if not isinstance(self.final_deliverable, Mapping):
            raise TypeError("final_deliverable must be a mapping")
        if not isinstance(self.liaison, Mapping):
            raise TypeError("liaison must be a mapping")
        repository = self.repository.strip()
        if not _REPOSITORY_RE.fullmatch(repository):
            raise GitHubResearchLoveFinalRemotePublicationError(
                "repository must be owner/name"
            )
        object.__setattr__(self, "repository", repository)
        if (
            isinstance(self.issue_number, bool)
            or not isinstance(self.issue_number, int)
            or self.issue_number <= 0
        ):
            raise GitHubResearchLoveFinalRemotePublicationError(
                "issue_number must be > 0"
            )
        match = _ISSUE_REF_RE.fullmatch(self.source_issue_ref.strip())
        if match is None:
            raise GitHubResearchLoveFinalRemotePublicationError(
                "source_issue_ref must use "
                "github-frame:<owner>/<repo>/issues/<number>"
            )
        if match.group("repository") != repository:
            raise GitHubResearchLoveFinalRemotePublicationError(
                "source_issue_ref repository mismatch"
            )
        if int(match.group("number")) != self.issue_number:
            raise GitHubResearchLoveFinalRemotePublicationError(
                "source_issue_ref issue number mismatch"
            )
        if not self.policy_decision_id.startswith("policy:"):
            raise GitHubResearchLoveFinalRemotePublicationError(
                "policy_decision_id must start with policy:"
            )
        if self.operator_decision != "approve":
            raise GitHubResearchLoveFinalRemotePublicationError(
                "operator_decision must be approve"
            )
        for name in (
            "project_item_id",
            "project_field_ref",
            "project_field_name",
            "project_status_value",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise GitHubResearchLoveFinalRemotePublicationError(
                    f"{name} must not be empty"
                )
            object.__setattr__(self, name, value.strip())
        if self.max_body_chars < 4_000:
            raise GitHubResearchLoveFinalRemotePublicationError(
                "max_body_chars must be >= 4000"
            )
        if self.max_project_value_chars < 32:
            raise GitHubResearchLoveFinalRemotePublicationError(
                "max_project_value_chars must be >= 32"
            )


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveFinalPublicationPlan:
    """Lineage wrapper directly consumable by the existing publication CLI."""

    schema: str
    work_package_ref: str
    final_sql_plan_digest: str
    final_sql_revision_ref: str
    final_authority_object_ref: str
    final_artifact_ref: str
    final_packet_ref: str
    liaison_plan_digest: str
    publication_plan: LoveFinalDeliverablePublicationPlan
    lineage_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema != PLAN_SCHEMA:
            raise GitHubResearchLoveFinalRemotePublicationError(
                "unsupported GitHub research final publication plan schema"
            )
        if not self.work_package_ref.startswith("research-work-package:"):
            raise GitHubResearchLoveFinalRemotePublicationError(
                "work_package_ref must start with research-work-package:"
            )
        for name, value in (
            ("final_sql_plan_digest", self.final_sql_plan_digest),
            ("liaison_plan_digest", self.liaison_plan_digest),
        ):
            if not value.startswith("sha256:") or len(value) != 71:
                raise GitHubResearchLoveFinalRemotePublicationError(
                    f"{name} must be sha256:*"
                )
        if not self.final_sql_revision_ref.startswith("context-revision:"):
            raise GitHubResearchLoveFinalRemotePublicationError(
                "final_sql_revision_ref must be context-revision:*"
            )
        if not self.final_authority_object_ref.startswith("context-object:"):
            raise GitHubResearchLoveFinalRemotePublicationError(
                "final_authority_object_ref must be context-object:*"
            )
        if not self.final_artifact_ref.startswith("artifact:"):
            raise GitHubResearchLoveFinalRemotePublicationError(
                "final_artifact_ref must be artifact:*"
            )
        if not self.final_packet_ref.startswith("publication:"):
            raise GitHubResearchLoveFinalRemotePublicationError(
                "final_packet_ref must be publication:*"
            )
        if not isinstance(
            self.publication_plan,
            LoveFinalDeliverablePublicationPlan,
        ):
            raise TypeError(
                "publication_plan must be LoveFinalDeliverablePublicationPlan"
            )
        if not self.publication_plan.valid:
            raise GitHubResearchLoveFinalRemotePublicationError(
                "existing publication planner returned an invalid plan: "
                + "; ".join(self.publication_plan.issues)
            )
        object.__setattr__(self, "lineage_digest", _lineage_digest(self))

    @property
    def plan_digest(self) -> str:
        """Exact digest to pass to ``--confirm-plan-digest``."""

        return self.publication_plan.plan_digest

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": True,
            "work_package_ref": self.work_package_ref,
            "final_sql_plan_digest": self.final_sql_plan_digest,
            "final_sql_revision_ref": self.final_sql_revision_ref,
            "final_authority_object_ref": self.final_authority_object_ref,
            "final_artifact_ref": self.final_artifact_ref,
            "final_packet_ref": self.final_packet_ref,
            "liaison_plan_digest": self.liaison_plan_digest,
            "lineage_digest": self.lineage_digest,
            "plan_digest": self.plan_digest,
            # The existing CLI parser intentionally accepts a wrapper carrying
            # the canonical r13 plan under this exact key.
            "publication_plan": self.publication_plan.to_mapping(),
            "boundaries": {
                "existing_publication_planner_reused": True,
                "existing_remote_executor_reused": True,
                "existing_github_cli_adapter_compatible": True,
                "preview_is_default": True,
                "operator_approval_required": True,
                "exact_plan_digest_confirmation_required": True,
                "remote_mutation_lock_required": True,
                "issue_publication_lock_required": True,
                "project_projection_lock_required": True,
                "collision_guarded": True,
                "exact_remote_readback_required": True,
                "remote_mutation_performed": False,
                "sql_write_performed": False,
                "qdrant_write_performed": False,
                "scheduler_created": False,
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveFinalPublicationExecution:
    """Preview/execute controls passed to the existing remote executor."""

    plan: GitHubResearchLoveFinalPublicationPlan
    operator_decision: str
    execute: bool = False
    confirm_plan_digest: str = ""
    remote_mutation_allowed: bool = False
    issue_publication_allowed: bool = False
    project_projection_allowed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(
            self.plan,
            GitHubResearchLoveFinalPublicationPlan,
        ):
            raise TypeError(
                "plan must be GitHubResearchLoveFinalPublicationPlan"
            )
        if self.operator_decision != "approve":
            raise GitHubResearchLoveFinalRemotePublicationError(
                "operator_decision must be approve"
            )
        if self.execute and not self.confirm_plan_digest:
            raise GitHubResearchLoveFinalRemotePublicationError(
                "execute requires confirm_plan_digest"
            )


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveFinalPublicationResult:
    """Remote outcome plus immutable local lineage."""

    schema: str
    plan: GitHubResearchLoveFinalPublicationPlan
    remote_result: LoveFinalDeliverableRemotePublicationResult

    def __post_init__(self) -> None:
        if self.schema != RESULT_SCHEMA:
            raise GitHubResearchLoveFinalRemotePublicationError(
                "unsupported GitHub research final publication result schema"
            )
        if self.remote_result.plan_digest != self.plan.plan_digest:
            raise GitHubResearchLoveFinalRemotePublicationError(
                "remote publication result plan digest mismatch"
            )

    @property
    def valid(self) -> bool:
        return self.remote_result.valid

    @property
    def status(self) -> str:
        if self.remote_result.mode == "preview":
            return "preview"
        if not self.remote_result.valid:
            return self.remote_result.action
        if self.remote_result.action == "replay":
            return "published-replay"
        return "published"

    def to_mapping(self) -> dict[str, object]:
        remote = self.remote_result.to_mapping()
        return {
            "schema": self.schema,
            "valid": self.valid,
            "status": self.status,
            "issues": list(self.remote_result.issues),
            "plan_digest": self.plan.plan_digest,
            "lineage_digest": self.plan.lineage_digest,
            "final_sql_revision_ref": self.plan.final_sql_revision_ref,
            "final_authority_object_ref": (
                self.plan.final_authority_object_ref
            ),
            "final_artifact_ref": self.plan.final_artifact_ref,
            "final_packet_ref": self.plan.final_packet_ref,
            "publication_plan": self.plan.publication_plan.to_mapping(),
            "remote_publication": remote,
            "boundaries": {
                "existing_remote_executor_reused": True,
                "exact_remote_readback_confirmed": bool(
                    self.remote_result.readback
                    and self.remote_result.readback.valid
                ),
                "issue_mutation_performed": (
                    self.remote_result.issue_mutation_performed
                ),
                "project_mutation_performed": (
                    self.remote_result.project_mutation_performed
                ),
                "partial_execution": self.remote_result.partial_execution,
                "sql_write_performed": False,
                "qdrant_write_performed": False,
                "scheduler_created": False,
                "laboratory_execution_started": False,
                "specialist_execution_started": False,
            },
        }


def build_github_research_love_final_publication_plan(
    command: GitHubResearchLoveFinalPublicationCommand,
) -> GitHubResearchLoveFinalPublicationPlan:
    """Validate r16 lineage then reuse the existing pure publication planner."""

    lineage = _validated_lineage(command)
    compatibility_result = _legacy_compatible_synthesis_result(lineage)

    publication_plan = plan_love_final_deliverable_publication(
        LoveFinalDeliverablePublicationCommand(
            repository=command.repository,
            issue_number=command.issue_number,
            source_issue_ref=command.source_issue_ref,
            policy_decision_id=command.policy_decision_id,
            operator_decision=command.operator_decision,
            synthesis_result=compatibility_result,
            project_item_id=command.project_item_id,
            project_field_ref=command.project_field_ref,
            project_field_name=command.project_field_name,
            project_status_value=command.project_status_value,
            existing_comments=(),
            project_snapshot=None,
            max_body_chars=command.max_body_chars,
            max_project_value_chars=command.max_project_value_chars,
        )
    )
    if not publication_plan.valid:
        raise GitHubResearchLoveFinalRemotePublicationError(
            "existing publication planner rejected the final deliverable: "
            + "; ".join(publication_plan.issues)
        )

    final_plan = lineage["final_plan"]
    final_receipt = lineage["final_receipt"]
    liaison_plan = lineage["liaison_plan"]
    return GitHubResearchLoveFinalPublicationPlan(
        schema=PLAN_SCHEMA,
        work_package_ref=_required_text(
            final_plan,
            "work_package_ref",
        ),
        final_sql_plan_digest=_required_text(
            final_plan,
            "plan_digest",
        ),
        final_sql_revision_ref=_required_text(
            final_receipt,
            "revision_ref",
        ),
        final_authority_object_ref=_required_text(
            final_receipt,
            "authority_object_ref",
        ),
        final_artifact_ref=_required_text(
            final_receipt,
            "artifact_ref",
        ),
        final_packet_ref=_required_text(
            final_receipt,
            "packet_ref",
        ),
        liaison_plan_digest=_required_text(
            liaison_plan,
            "plan_digest",
        ),
        publication_plan=publication_plan,
    )


def execute_github_research_love_final_publication(
    execution: GitHubResearchLoveFinalPublicationExecution,
    *,
    issue_port: FinalDeliverableIssuePublicationPort,
    project_port: FinalDeliverableProjectV2PublicationPort,
) -> GitHubResearchLoveFinalPublicationResult:
    """Delegate preview/mutation/readback to the existing controlled executor."""

    remote_command = LoveFinalDeliverableRemotePublicationCommand(
        schema=LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_COMMAND_SCHEMA,
        plan=execution.plan.publication_plan,
        operator_decision=execution.operator_decision,
        execute=execution.execute,
        confirm_plan_digest=execution.confirm_plan_digest,
        remote_mutation_allowed=execution.remote_mutation_allowed,
        issue_publication_allowed=execution.issue_publication_allowed,
        project_projection_allowed=execution.project_projection_allowed,
    )
    remote_result = execute_love_final_deliverable_remote_publication(
        remote_command,
        issue_port=issue_port,
        project_port=project_port,
    )
    return GitHubResearchLoveFinalPublicationResult(
        schema=RESULT_SCHEMA,
        plan=execution.plan,
        remote_result=remote_result,
    )


def _validated_lineage(
    command: GitHubResearchLoveFinalPublicationCommand,
) -> dict[str, Mapping[str, Any]]:
    final = command.final_deliverable
    liaison = command.liaison

    if final.get("schema") != FINAL_SQL_RESULT_SCHEMA:
        raise GitHubResearchLoveFinalRemotePublicationError(
            "unsupported final deliverable SQL result schema"
        )
    if final.get("valid") is not True or final.get("status") != "persisted":
        raise GitHubResearchLoveFinalRemotePublicationError(
            "final deliverable must be valid and persisted"
        )
    final_plan = _required_mapping(final, "plan")
    final_receipt = _required_mapping(final, "receipt")
    if final_receipt.get("schema") != FINAL_SQL_RECEIPT_SCHEMA:
        raise GitHubResearchLoveFinalRemotePublicationError(
            "unsupported final deliverable SQL receipt schema"
        )
    if final_receipt.get("readback_verified") is not True:
        raise GitHubResearchLoveFinalRemotePublicationError(
            "final deliverable SQL readback must be verified"
        )

    if liaison.get("schema") != LIAISON_RESULT_SCHEMA:
        raise GitHubResearchLoveFinalRemotePublicationError(
            "unsupported liaison synthesis result schema"
        )
    if liaison.get("valid") is not True or liaison.get("status") != "synthesized":
        raise GitHubResearchLoveFinalRemotePublicationError(
            "liaison synthesis must be valid and synthesized"
        )
    liaison_plan = _required_mapping(liaison, "plan")
    mutualization = _required_mapping(liaison, "mutualization")

    packet = _required_mapping(final_plan, "packet")
    packet_synthesis = _required_mapping(packet, "synthesis")
    authority_object = _required_mapping(final_plan, "authority_object")
    artifact = _required_mapping(final_plan, "artifact")

    work_package_ref = _required_text(final_plan, "work_package_ref")
    if liaison_plan.get("work_package_ref") != work_package_ref:
        raise GitHubResearchLoveFinalRemotePublicationError(
            "liaison and final deliverable work_package_ref mismatch"
        )
    liaison_plan_digest = _required_text(liaison_plan, "plan_digest")
    if final_plan.get("liaison_plan_digest") != liaison_plan_digest:
        raise GitHubResearchLoveFinalRemotePublicationError(
            "final deliverable liaison_plan_digest mismatch"
        )

    first_ref = _required_text(final_plan, "first_analysis_object_ref")
    second_ref = _required_text(final_plan, "second_analysis_object_ref")
    if liaison_plan.get("first_sql_ref") != first_ref:
        raise GitHubResearchLoveFinalRemotePublicationError(
            "first liaison SQL reference mismatch"
        )
    if liaison_plan.get("second_sql_ref") != second_ref:
        raise GitHubResearchLoveFinalRemotePublicationError(
            "second liaison SQL reference mismatch"
        )

    expected_target = f"github:{command.repository}#{command.issue_number}"
    if packet.get("target_ref") != expected_target:
        raise GitHubResearchLoveFinalRemotePublicationError(
            "final packet target_ref differs from requested Issue"
        )
    if final_receipt.get("target_ref") != expected_target:
        raise GitHubResearchLoveFinalRemotePublicationError(
            "final SQL receipt target_ref differs from requested Issue"
        )
    packet_ref = _required_text(packet, "packet_ref")
    if final_receipt.get("packet_ref") != packet_ref:
        raise GitHubResearchLoveFinalRemotePublicationError(
            "final SQL receipt packet_ref mismatch"
        )
    if final_receipt.get("authority_object_ref") != authority_object.get(
        "object_ref"
    ):
        raise GitHubResearchLoveFinalRemotePublicationError(
            "final authority object receipt mismatch"
        )
    if final_receipt.get("artifact_ref") != artifact.get("artifact_ref"):
        raise GitHubResearchLoveFinalRemotePublicationError(
            "final artifact receipt mismatch"
        )
    if packet_synthesis.get("final_publication_ready") is not True:
        raise GitHubResearchLoveFinalRemotePublicationError(
            "final packet synthesis is not publication-ready"
        )
    if packet_synthesis.get("provenance_hidden") is not True:
        raise GitHubResearchLoveFinalRemotePublicationError(
            "final packet does not hide specialist provenance"
        )
    if final.get("remote_publication_performed") not in {False, None}:
        raise GitHubResearchLoveFinalRemotePublicationError(
            "final deliverable already reports remote publication"
        )

    return {
        "final": final,
        "final_plan": final_plan,
        "final_receipt": final_receipt,
        "packet": packet,
        "packet_synthesis": packet_synthesis,
        "authority_object": authority_object,
        "artifact": artifact,
        "liaison": liaison,
        "liaison_plan": liaison_plan,
        "mutualization": mutualization,
    }


def _legacy_compatible_synthesis_result(
    lineage: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    """Adapt r16 fields to the already installed r12/r13 planner contract."""

    final_plan = lineage["final_plan"]
    final_receipt = lineage["final_receipt"]
    packet = lineage["packet"]
    packet_synthesis = lineage["packet_synthesis"]
    mutualization = lineage["mutualization"]

    return {
        "schema": R12_RESULT_SCHEMA,
        "github_mutation_performed": False,
        "synthesis": dict(packet_synthesis),
        "study_result": {
            "status": "synthesized",
            "context_revision_ref": _required_text(
                final_plan,
                "parent_revision_ref",
            ),
            "unresolved_points": list(
                _text_sequence(mutualization.get("uncertainties"))
            ),
        },
        "final_envelope": {
            "final_ref": _required_text(packet, "packet_ref"),
            "artifact_ref": _required_text(
                final_receipt,
                "artifact_ref",
            ),
            "synthesis_ref": _required_text(
                packet_synthesis,
                "synthesis_ref",
            ),
            "title": _required_text(packet, "title"),
            "body": _required_text(packet, "body"),
            "evidence_refs": list(
                _text_sequence(packet.get("evidence_refs"))
            ),
            "context_influence_refs": list(
                _text_sequence(packet.get("context_influence_refs"))
            ),
            "validation_refs": list(
                _text_sequence(packet.get("validation_refs"))
            ),
        },
        "mutualization": dict(mutualization),
        "synthesis_revision": {
            "revision_ref": _required_text(
                final_receipt,
                "revision_ref",
            ),
        },
    }


def _lineage_digest(
    plan: GitHubResearchLoveFinalPublicationPlan,
) -> str:
    payload = {
        "schema": plan.schema,
        "work_package_ref": plan.work_package_ref,
        "final_sql_plan_digest": plan.final_sql_plan_digest,
        "final_sql_revision_ref": plan.final_sql_revision_ref,
        "final_authority_object_ref": plan.final_authority_object_ref,
        "final_artifact_ref": plan.final_artifact_ref,
        "final_packet_ref": plan.final_packet_ref,
        "liaison_plan_digest": plan.liaison_plan_digest,
        "publication_plan_digest": plan.publication_plan.plan_digest,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _required_mapping(
    value: Mapping[str, Any],
    name: str,
) -> Mapping[str, Any]:
    candidate = value.get(name)
    if not isinstance(candidate, Mapping):
        raise GitHubResearchLoveFinalRemotePublicationError(
            f"{name} must be an object"
        )
    return candidate


def _required_text(
    value: Mapping[str, Any],
    name: str,
) -> str:
    candidate = value.get(name)
    if not isinstance(candidate, str) or not candidate.strip():
        raise GitHubResearchLoveFinalRemotePublicationError(
            f"{name} must not be empty"
        )
    return candidate.strip()


def _text_sequence(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise GitHubResearchLoveFinalRemotePublicationError(
            "expected a list of strings"
        )
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise GitHubResearchLoveFinalRemotePublicationError(
                "list entries must be non-empty strings"
            )
        result.append(item.strip())
    return tuple(result)


__all__ = (
    "GitHubResearchLoveFinalPublicationCommand",
    "GitHubResearchLoveFinalPublicationExecution",
    "GitHubResearchLoveFinalPublicationPlan",
    "GitHubResearchLoveFinalPublicationResult",
    "GitHubResearchLoveFinalRemotePublicationError",
    "PLAN_SCHEMA",
    "RESULT_SCHEMA",
    "build_github_research_love_final_publication_plan",
    "execute_github_research_love_final_publication",
)
