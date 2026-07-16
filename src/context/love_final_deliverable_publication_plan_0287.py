"""Pure final-deliverable publication planning for phase 0287-r7-r13.

The module turns the r12 ``FinalArtifactEnvelope`` boundary into a bounded,
human-readable GitHub Issue comment and one concise ProjectV2 field projection.
It only prepares deterministic create/replay/collision/update plans and exact
readback expectations. Network access and remote mutation are deliberately out
of scope.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

from context.github_controlled_advisory_issue_publication_0281 import (
    GitHubIssueCommentSnapshot,
)

SCHEMA = "missipy.love.final_deliverable_publication_plan.v1"
PROJECT_PROJECTION_SCHEMA = (
    "missipy.love.final_deliverable_project_v2_projection.v1"
)
READBACK_EXPECTATION_SCHEMA = (
    "missipy.love.final_deliverable_publication_readback_expectation.v1"
)
READBACK_RESULT_SCHEMA = (
    "missipy.love.final_deliverable_publication_readback_result.v1"
)
R12_RESULT_SCHEMA = "missipy.love.memory_evidence_synthesis_result.v1"
MARKER_PREFIX = "autodoc:final-deliverable"
_COMMENT_MARKER_RE = re.compile(
    r"<!--\s*(autodoc:final-deliverable:[a-f0-9]{24})\s*-->"
)
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_ISSUE_REF_RE = re.compile(
    r"^github-frame:"
    r"(?P<repository>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"
    r"/issues/(?P<number>[1-9][0-9]*)$"
)
_ALLOWED_OPERATOR_DECISIONS = frozenset({"approve"})
_ALLOWED_PLAN_ACTIONS = frozenset(
    {
        "create_and_project",
        "create_issue",
        "project",
        "replay",
        "collision",
        "blocked",
    }
)
_ALLOWED_ISSUE_ACTIONS = frozenset({"create", "replay", "collision", "blocked"})
_ALLOWED_PROJECT_ACTIONS = frozenset({"update", "replay", "blocked"})


@dataclass(frozen=True, slots=True)
class ProjectV2FieldSnapshot:
    """Read-only snapshot of one ProjectV2 field used for planning/readback."""

    project_item_id: str
    field_ref: str
    field_name: str
    value: str

    def __post_init__(self) -> None:
        _require_text("project_item_id", self.project_item_id)
        _require_text("field_ref", self.field_ref)
        _require_text("field_name", self.field_name)
        if not isinstance(self.value, str):
            raise TypeError("value must be a string")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "project_item_id": self.project_item_id,
            "field_ref": self.field_ref,
            "field_name": self.field_name,
            "value": self.value,
        }


@dataclass(frozen=True, slots=True)
class FinalDeliverableProjectV2Projection:
    schema: str
    project_item_id: str
    field_ref: str
    field_name: str
    value: str
    value_sha256: str
    source_issue_ref: str
    final_ref: str
    artifact_ref: str
    synthesis_ref: str
    readback_required: bool = True

    def __post_init__(self) -> None:
        if self.schema != PROJECT_PROJECTION_SCHEMA:
            raise ValueError("unsupported ProjectV2 projection schema")
        for field_name in (
            "project_item_id",
            "field_ref",
            "field_name",
            "value",
            "value_sha256",
            "source_issue_ref",
            "final_ref",
            "artifact_ref",
            "synthesis_ref",
        ):
            _require_text(field_name, getattr(self, field_name))
        if self.value_sha256 != _sha256(self.value):
            raise ValueError("ProjectV2 value_sha256 mismatch")
        if not self.readback_required:
            raise ValueError("ProjectV2 projection must require readback")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "project_item_id": self.project_item_id,
            "field_ref": self.field_ref,
            "field_name": self.field_name,
            "value": self.value,
            "value_sha256": self.value_sha256,
            "source_issue_ref": self.source_issue_ref,
            "final_ref": self.final_ref,
            "artifact_ref": self.artifact_ref,
            "synthesis_ref": self.synthesis_ref,
            "readback_required": True,
        }


@dataclass(frozen=True, slots=True)
class FinalDeliverablePublicationOperation:
    kind: str
    target_ref: str
    payload_sha256: str
    depends_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in {
            "create_issue_comment",
            "update_project_v2_field",
        }:
            raise ValueError("unsupported publication operation kind")
        _require_text("target_ref", self.target_ref)
        _require_text("payload_sha256", self.payload_sha256)
        if not isinstance(self.depends_on, tuple):
            object.__setattr__(self, "depends_on", tuple(self.depends_on))

    def to_mapping(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "target_ref": self.target_ref,
            "payload_sha256": self.payload_sha256,
            "depends_on": list(self.depends_on),
        }


@dataclass(frozen=True, slots=True)
class FinalDeliverablePublicationReadbackExpectation:
    schema: str
    marker: str
    body_sha256: str
    project_item_id: str
    project_field_ref: str
    project_value_sha256: str
    require_exact_issue_body: bool = True
    require_exact_project_value: bool = True

    def __post_init__(self) -> None:
        if self.schema != READBACK_EXPECTATION_SCHEMA:
            raise ValueError("unsupported readback expectation schema")
        for field_name in (
            "marker",
            "body_sha256",
            "project_item_id",
            "project_field_ref",
            "project_value_sha256",
        ):
            _require_text(field_name, getattr(self, field_name))
        if not self.marker.startswith(f"{MARKER_PREFIX}:"):
            raise ValueError("readback marker is not a final-deliverable marker")
        if not self.require_exact_issue_body:
            raise ValueError("exact Issue body readback is required")
        if not self.require_exact_project_value:
            raise ValueError("exact ProjectV2 value readback is required")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "marker": self.marker,
            "body_sha256": self.body_sha256,
            "project_item_id": self.project_item_id,
            "project_field_ref": self.project_field_ref,
            "project_value_sha256": self.project_value_sha256,
            "require_exact_issue_body": True,
            "require_exact_project_value": True,
        }


@dataclass(frozen=True, slots=True)
class LoveFinalDeliverablePublicationCommand:
    repository: str
    issue_number: int
    source_issue_ref: str
    policy_decision_id: str
    operator_decision: str
    synthesis_result: Any
    project_item_id: str
    project_field_ref: str
    project_field_name: str
    project_status_value: str = "Livrable final prêt"
    existing_comments: tuple[GitHubIssueCommentSnapshot, ...] = ()
    project_snapshot: ProjectV2FieldSnapshot | None = None
    max_body_chars: int = 30_000
    max_project_value_chars: int = 500

    def __post_init__(self) -> None:
        if not _REPOSITORY_RE.fullmatch(self.repository):
            raise ValueError("repository must be owner/name")
        if self.issue_number <= 0:
            raise ValueError("issue_number must be > 0")
        issue_ref_match = _ISSUE_REF_RE.fullmatch(self.source_issue_ref.strip())
        if issue_ref_match is None:
            raise ValueError(
                "source_issue_ref must use "
                "github-frame:<owner>/<repo>/issues/<number>"
            )
        if issue_ref_match.group("repository") != self.repository:
            raise ValueError("source_issue_ref repository mismatch")
        if int(issue_ref_match.group("number")) != self.issue_number:
            raise ValueError("source_issue_ref issue number mismatch")
        if not self.policy_decision_id.startswith("policy:"):
            raise ValueError("policy_decision_id must start with policy:")
        if self.operator_decision not in _ALLOWED_OPERATOR_DECISIONS:
            raise ValueError("operator_decision must be approve")
        for field_name in (
            "project_item_id",
            "project_field_ref",
            "project_field_name",
            "project_status_value",
        ):
            _require_text(field_name, getattr(self, field_name))
        if not isinstance(self.existing_comments, tuple):
            object.__setattr__(
                self,
                "existing_comments",
                tuple(self.existing_comments),
            )
        if self.max_body_chars < 4_000:
            raise ValueError("max_body_chars must be >= 4000")
        if self.max_project_value_chars < 32:
            raise ValueError("max_project_value_chars must be >= 32")


@dataclass(frozen=True, slots=True)
class LoveFinalDeliverablePublicationPlan:
    valid: bool
    action: str
    issue_action: str
    project_action: str
    issues: tuple[str, ...]
    repository: str
    issue_number: int
    source_issue_ref: str
    marker: str
    body: str
    body_sha256: str
    plan_ref: str
    plan_digest: str
    project_projection: FinalDeliverableProjectV2Projection | None
    operations: tuple[FinalDeliverablePublicationOperation, ...]
    readback_expectation: FinalDeliverablePublicationReadbackExpectation | None
    existing_comment_id: int | None = None
    existing_comment_url: str = ""
    operator_decision_required: bool = True
    confirmed_plan_digest_required: bool = True
    github_issue_mutation_allowed: bool = False
    project_v2_mutation_allowed: bool = False
    github_mutation_performed: bool = False
    scheduler_modified: bool = False
    sql_modified: bool = False
    qdrant_modified: bool = False
    openvino_modified: bool = False

    def __post_init__(self) -> None:
        if self.action not in _ALLOWED_PLAN_ACTIONS:
            raise ValueError("unsupported plan action")
        if self.issue_action not in _ALLOWED_ISSUE_ACTIONS:
            raise ValueError("unsupported Issue action")
        if self.project_action not in _ALLOWED_PROJECT_ACTIONS:
            raise ValueError("unsupported ProjectV2 action")
        if not isinstance(self.issues, tuple):
            object.__setattr__(self, "issues", tuple(self.issues))
        if not isinstance(self.operations, tuple):
            object.__setattr__(self, "operations", tuple(self.operations))
        if self.valid and self.issues:
            raise ValueError("valid plan cannot carry issues")
        if self.valid and not self.plan_digest:
            raise ValueError("valid plan must carry plan_digest")
        if self.valid and self.project_projection is None:
            raise ValueError("valid plan must carry ProjectV2 projection")
        if self.valid and self.readback_expectation is None:
            raise ValueError("valid plan must carry readback expectation")
        if any(
            (
                self.github_issue_mutation_allowed,
                self.project_v2_mutation_allowed,
                self.github_mutation_performed,
                self.scheduler_modified,
                self.sql_modified,
                self.qdrant_modified,
                self.openvino_modified,
            )
        ):
            raise ValueError("r13 planning boundaries must remain closed")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "valid": self.valid,
            "action": self.action,
            "issue_action": self.issue_action,
            "project_action": self.project_action,
            "issues": list(self.issues),
            "repository": self.repository,
            "issue_number": self.issue_number,
            "source_issue_ref": self.source_issue_ref,
            "marker": self.marker,
            "body": self.body,
            "body_sha256": self.body_sha256,
            "plan_ref": self.plan_ref,
            "plan_digest": self.plan_digest,
            "project_projection": (
                None
                if self.project_projection is None
                else self.project_projection.to_mapping()
            ),
            "operations": [operation.to_mapping() for operation in self.operations],
            "readback_expectation": (
                None
                if self.readback_expectation is None
                else self.readback_expectation.to_mapping()
            ),
            "existing_comment_id": self.existing_comment_id,
            "existing_comment_url": self.existing_comment_url,
            "operator_decision_required": True,
            "confirmed_plan_digest_required": True,
            "github_issue_mutation_allowed": False,
            "project_v2_mutation_allowed": False,
            "github_mutation_performed": False,
            "scheduler_modified": False,
            "sql_modified": False,
            "qdrant_modified": False,
            "openvino_modified": False,
            "collision_guarded": True,
            "idempotent_replay": self.action == "replay",
        }


@dataclass(frozen=True, slots=True)
class FinalDeliverablePublicationReadbackResult:
    valid: bool
    action: str
    issues: tuple[str, ...]
    plan_digest: str
    issue_comment_id: int | None = None
    issue_comment_url: str = ""
    project_value_sha256: str = ""
    remote_mutation_performed: bool = False

    def __post_init__(self) -> None:
        if self.action not in {"confirmed", "blocked", "collision"}:
            raise ValueError("unsupported readback action")
        if not isinstance(self.issues, tuple):
            object.__setattr__(self, "issues", tuple(self.issues))
        if self.valid and self.action != "confirmed":
            raise ValueError("valid readback must be confirmed")
        if self.valid and self.issues:
            raise ValueError("valid readback cannot carry issues")
        if self.remote_mutation_performed:
            raise ValueError("readback verifier cannot perform remote mutation")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": READBACK_RESULT_SCHEMA,
            "valid": self.valid,
            "action": self.action,
            "issues": list(self.issues),
            "plan_digest": self.plan_digest,
            "issue_comment_id": self.issue_comment_id,
            "issue_comment_url": self.issue_comment_url,
            "project_value_sha256": self.project_value_sha256,
            "remote_mutation_performed": False,
        }


def plan_love_final_deliverable_publication(
    command: LoveFinalDeliverablePublicationCommand,
) -> LoveFinalDeliverablePublicationPlan:
    """Prepare exact Issue + ProjectV2 publication operations without mutation."""

    validation_issues = list(_validate_synthesis_result(command.synthesis_result))
    if validation_issues:
        return _invalid_plan(command, validation_issues)

    envelope = _value(command.synthesis_result, "final_envelope")
    marker = _build_marker(command, envelope)
    body = render_love_final_deliverable_markdown(
        command.synthesis_result,
        marker=marker,
        max_body_chars=command.max_body_chars,
    )
    body_sha256 = _sha256(body)

    projection = _build_project_projection(command, envelope)
    issue_action, existing, issue_issues = _plan_issue_action(
        marker,
        body,
        command.existing_comments,
    )
    project_action, project_issues = _plan_project_action(
        projection,
        command.project_snapshot,
    )
    issues = tuple((*issue_issues, *project_issues))

    plan_digest = _plan_digest(
        command=command,
        marker=marker,
        body_sha256=body_sha256,
        projection=projection,
    )
    plan_ref = f"github-final-deliverable-plan:{plan_digest[:24]}"

    if issues:
        action = "collision" if issue_action == "collision" else "blocked"
        return _build_plan(
            command=command,
            valid=False,
            action=action,
            issue_action=issue_action,
            project_action=project_action,
            issues=issues,
            marker=marker,
            body=body,
            body_sha256=body_sha256,
            plan_ref=plan_ref,
            plan_digest=plan_digest,
            projection=projection,
            operations=(),
            existing=existing,
        )

    operations = _build_operations(
        command=command,
        issue_action=issue_action,
        project_action=project_action,
        body_sha256=body_sha256,
        projection=projection,
    )
    action = _combined_action(issue_action, project_action)
    expectation = FinalDeliverablePublicationReadbackExpectation(
        schema=READBACK_EXPECTATION_SCHEMA,
        marker=marker,
        body_sha256=body_sha256,
        project_item_id=projection.project_item_id,
        project_field_ref=projection.field_ref,
        project_value_sha256=projection.value_sha256,
    )
    return _build_plan(
        command=command,
        valid=True,
        action=action,
        issue_action=issue_action,
        project_action=project_action,
        issues=(),
        marker=marker,
        body=body,
        body_sha256=body_sha256,
        plan_ref=plan_ref,
        plan_digest=plan_digest,
        projection=projection,
        operations=operations,
        readback_expectation=expectation,
        existing=existing,
    )


def render_love_final_deliverable_markdown(
    synthesis_result: Any,
    *,
    marker: str,
    max_body_chars: int = 30_000,
) -> str:
    """Render bounded Markdown preserving conclusions, disputes and provenance."""

    if not marker.startswith(f"{MARKER_PREFIX}:"):
        raise ValueError("marker must use the final-deliverable namespace")
    if max_body_chars < 4_000:
        raise ValueError("max_body_chars must be >= 4000")

    envelope = _value(synthesis_result, "final_envelope")
    mutualization = _value(synthesis_result, "mutualization")
    study_result = _value(synthesis_result, "study_result")
    synthesis_revision = _value(synthesis_result, "synthesis_revision")

    title = _require_result_text(envelope, "title")
    body = _require_result_text(envelope, "body")
    final_ref = _require_result_text(envelope, "final_ref")
    artifact_ref = _require_result_text(envelope, "artifact_ref")
    synthesis_ref = _require_result_text(envelope, "synthesis_ref")
    context_revision_ref = _optional_result_text(
        study_result,
        "context_revision_ref",
        fallback="non renseigné",
    )
    synthesis_revision_ref = _optional_result_text(
        synthesis_revision,
        "revision_ref",
        fallback="non renseigné",
    )

    sections = [
        f"<!-- {marker} -->",
        "## Autodoc — livrable final",
        "",
        "> Synthèse finale issue du laboratoire après analyses spécialisées, "
        "mutualisation des preuves et liaison contrôlée.",
        "",
        f"### {title}",
        "",
        body.strip(),
        "",
        "### Convergences",
        "",
        _markdown_items(
            _sequence_value(mutualization, "convergences"),
            empty="Aucune convergence explicite n'a été déclarée.",
        ),
        "",
        "### Contradictions conservées",
        "",
        _markdown_items(
            _sequence_value(mutualization, "contradictions"),
            empty="Aucune contradiction explicite n'a été déclarée.",
        ),
        "",
        "### Incertitudes et points non résolus",
        "",
        _markdown_items(
            _merge_unique(
                _sequence_value(mutualization, "uncertainties"),
                _sequence_value(study_result, "unresolved_points"),
            ),
            empty="Aucune incertitude explicite n'a été déclarée.",
        ),
        "",
        "### Recommandations",
        "",
        _markdown_items(
            _sequence_value(mutualization, "recommendations"),
            empty="Aucune recommandation explicite n'a été déclarée.",
        ),
        "",
        "<details>",
        "<summary>Provenance technique et références</summary>",
        "",
        f"- Final : `{final_ref}`",
        f"- Artefact : `{artifact_ref}`",
        f"- Synthèse : `{synthesis_ref}`",
        f"- Révision de synthèse : `{synthesis_revision_ref}`",
        f"- Révision de contexte : `{context_revision_ref}`",
        "",
        "#### Références de preuve",
        "",
        _markdown_items(
            _merge_unique(
                _sequence_value(envelope, "evidence_refs"),
                _sequence_value(mutualization, "evidence_refs"),
            ),
            empty="Aucune référence de preuve déclarée.",
            code=True,
            max_items=40,
        ),
        "",
        "#### Influences de contexte",
        "",
        _markdown_items(
            _sequence_value(envelope, "context_influence_refs"),
            empty="Aucune influence de contexte déclarée.",
            code=True,
            max_items=40,
        ),
        "",
        "#### Validations",
        "",
        _markdown_items(
            _sequence_value(envelope, "validation_refs"),
            empty="Aucune référence de validation déclarée.",
            code=True,
            max_items=40,
        ),
        "",
        "</details>",
    ]
    rendered = "\n".join(sections).strip() + "\n"
    if len(rendered) <= max_body_chars:
        return rendered

    bounded_body = _truncate(body.strip(), max(1_000, max_body_chars // 3))
    sections[8] = bounded_body
    rendered = "\n".join(sections).strip() + "\n"
    if len(rendered) <= max_body_chars:
        return rendered

    suffix = "\n\n> Contenu borné par le contrat de publication r13.\n"
    available = max_body_chars - len(suffix)
    return rendered[:available].rstrip() + suffix


def verify_love_final_deliverable_publication_readback(
    plan: LoveFinalDeliverablePublicationPlan,
    *,
    issue_comments: Sequence[GitHubIssueCommentSnapshot],
    project_snapshot: ProjectV2FieldSnapshot | None,
) -> FinalDeliverablePublicationReadbackResult:
    """Verify exact remote readback without performing any remote operation."""

    if not plan.valid or plan.readback_expectation is None:
        return FinalDeliverablePublicationReadbackResult(
            valid=False,
            action="blocked",
            issues=("publication plan is not valid or lacks readback expectation",),
            plan_digest=plan.plan_digest,
        )

    matching = [comment for comment in issue_comments if plan.marker in comment.body]
    if len(matching) > 1:
        return FinalDeliverablePublicationReadbackResult(
            valid=False,
            action="collision",
            issues=("multiple Issue comments carry the final deliverable marker",),
            plan_digest=plan.plan_digest,
        )
    if not matching:
        return FinalDeliverablePublicationReadbackResult(
            valid=False,
            action="blocked",
            issues=("final deliverable Issue comment is missing from readback",),
            plan_digest=plan.plan_digest,
        )
    comment = matching[0]
    issues: list[str] = []
    if _sha256(comment.body) != plan.body_sha256 or comment.body != plan.body:
        issues.append("Issue comment readback differs from the approved body")

    projection = plan.project_projection
    if projection is None:
        issues.append("ProjectV2 projection is missing from the plan")
    elif project_snapshot is None:
        issues.append("ProjectV2 field readback is missing")
    else:
        if project_snapshot.project_item_id != projection.project_item_id:
            issues.append("ProjectV2 item readback identity mismatch")
        if project_snapshot.field_ref != projection.field_ref:
            issues.append("ProjectV2 field readback identity mismatch")
        if project_snapshot.field_name != projection.field_name:
            issues.append("ProjectV2 field readback name mismatch")
        if project_snapshot.value != projection.value:
            issues.append("ProjectV2 field readback differs from the approved value")

    if issues:
        return FinalDeliverablePublicationReadbackResult(
            valid=False,
            action="blocked",
            issues=tuple(issues),
            plan_digest=plan.plan_digest,
            issue_comment_id=comment.comment_id,
            issue_comment_url=comment.html_url,
            project_value_sha256=(
                "" if project_snapshot is None else _sha256(project_snapshot.value)
            ),
        )
    assert project_snapshot is not None
    return FinalDeliverablePublicationReadbackResult(
        valid=True,
        action="confirmed",
        issues=(),
        plan_digest=plan.plan_digest,
        issue_comment_id=comment.comment_id,
        issue_comment_url=comment.html_url,
        project_value_sha256=_sha256(project_snapshot.value),
    )


def _validate_synthesis_result(result: Any) -> tuple[str, ...]:
    issues: list[str] = []
    if _value(result, "schema") != R12_RESULT_SCHEMA:
        issues.append("synthesis_result schema is not the closed r12 result")
    if bool(_value(result, "github_mutation_performed")):
        issues.append("r12 result already reports a GitHub mutation")
    synthesis = _value(result, "synthesis")
    if not bool(_value(synthesis, "final_publication_ready")):
        issues.append("liaison synthesis is not final-publication ready")
    study_result = _value(result, "study_result")
    if _value(study_result, "status") != "synthesized":
        issues.append("love study result is not synthesized")
    envelope = _value(result, "final_envelope")
    for field_name in (
        "final_ref",
        "artifact_ref",
        "synthesis_ref",
        "title",
        "body",
    ):
        if not _optional_result_text(envelope, field_name):
            issues.append(f"final envelope is missing {field_name}")
    return tuple(issues)


def _build_marker(command: LoveFinalDeliverablePublicationCommand, envelope: Any) -> str:
    identity = {
        "repository": command.repository,
        "issue_number": command.issue_number,
        "source_issue_ref": command.source_issue_ref,
        "final_ref": _require_result_text(envelope, "final_ref"),
        "artifact_ref": _require_result_text(envelope, "artifact_ref"),
        "synthesis_ref": _require_result_text(envelope, "synthesis_ref"),
    }
    digest = hashlib.sha256(_canonical_json(identity).encode("utf-8")).hexdigest()[:24]
    return f"{MARKER_PREFIX}:{digest}"


def _build_project_projection(
    command: LoveFinalDeliverablePublicationCommand,
    envelope: Any,
) -> FinalDeliverableProjectV2Projection:
    title = _require_result_text(envelope, "title")
    artifact_ref = _require_result_text(envelope, "artifact_ref")
    summary = f"{command.project_status_value} — {title} — {artifact_ref}"
    value = _truncate(summary, command.max_project_value_chars)
    return FinalDeliverableProjectV2Projection(
        schema=PROJECT_PROJECTION_SCHEMA,
        project_item_id=command.project_item_id,
        field_ref=command.project_field_ref,
        field_name=command.project_field_name,
        value=value,
        value_sha256=_sha256(value),
        source_issue_ref=command.source_issue_ref,
        final_ref=_require_result_text(envelope, "final_ref"),
        artifact_ref=artifact_ref,
        synthesis_ref=_require_result_text(envelope, "synthesis_ref"),
    )


def _plan_issue_action(
    marker: str,
    body: str,
    comments: Sequence[GitHubIssueCommentSnapshot],
) -> tuple[str, GitHubIssueCommentSnapshot | None, tuple[str, ...]]:
    matches = [comment for comment in comments if marker in comment.body]
    if len(matches) > 1:
        return (
            "collision",
            None,
            ("multiple existing comments carry the final deliverable marker",),
        )
    if not matches:
        return "create", None, ()
    existing = matches[0]
    if existing.body == body:
        return "replay", existing, ()
    return (
        "collision",
        existing,
        ("existing final deliverable marker carries a different body",),
    )


def _plan_project_action(
    projection: FinalDeliverableProjectV2Projection,
    snapshot: ProjectV2FieldSnapshot | None,
) -> tuple[str, tuple[str, ...]]:
    if snapshot is None:
        return "update", ()
    if snapshot.project_item_id != projection.project_item_id:
        return "blocked", ("ProjectV2 snapshot item identity mismatch",)
    if snapshot.field_ref != projection.field_ref:
        return "blocked", ("ProjectV2 snapshot field identity mismatch",)
    if snapshot.field_name != projection.field_name:
        return "blocked", ("ProjectV2 snapshot field name mismatch",)
    if snapshot.value == projection.value:
        return "replay", ()
    return "update", ()


def _build_operations(
    *,
    command: LoveFinalDeliverablePublicationCommand,
    issue_action: str,
    project_action: str,
    body_sha256: str,
    projection: FinalDeliverableProjectV2Projection,
) -> tuple[FinalDeliverablePublicationOperation, ...]:
    operations: list[FinalDeliverablePublicationOperation] = []
    if issue_action == "create":
        operations.append(
            FinalDeliverablePublicationOperation(
                kind="create_issue_comment",
                target_ref=command.source_issue_ref,
                payload_sha256=body_sha256,
            )
        )
    if project_action == "update":
        dependencies = (
            ("create_issue_comment",) if issue_action == "create" else ()
        )
        operations.append(
            FinalDeliverablePublicationOperation(
                kind="update_project_v2_field",
                target_ref=(
                    f"github-project-v2-item:{projection.project_item_id}:"
                    f"{projection.field_ref}"
                ),
                payload_sha256=projection.value_sha256,
                depends_on=dependencies,
            )
        )
    return tuple(operations)


def _combined_action(issue_action: str, project_action: str) -> str:
    if issue_action == "replay" and project_action == "replay":
        return "replay"
    if issue_action == "create" and project_action == "update":
        return "create_and_project"
    if issue_action == "create" and project_action == "replay":
        return "create_issue"
    if issue_action == "replay" and project_action == "update":
        return "project"
    raise ValueError("unsupported valid action combination")


def _plan_digest(
    *,
    command: LoveFinalDeliverablePublicationCommand,
    marker: str,
    body_sha256: str,
    projection: FinalDeliverableProjectV2Projection,
) -> str:
    payload = {
        "schema": SCHEMA,
        "repository": command.repository,
        "issue_number": command.issue_number,
        "source_issue_ref": command.source_issue_ref,
        "marker": marker,
        "body_sha256": body_sha256,
        "project_projection": projection.to_mapping(),
        "policy_decision_id": command.policy_decision_id,
        "operator_decision": command.operator_decision,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _build_plan(
    *,
    command: LoveFinalDeliverablePublicationCommand,
    valid: bool,
    action: str,
    issue_action: str,
    project_action: str,
    issues: tuple[str, ...],
    marker: str,
    body: str,
    body_sha256: str,
    plan_ref: str,
    plan_digest: str,
    projection: FinalDeliverableProjectV2Projection | None,
    operations: tuple[FinalDeliverablePublicationOperation, ...],
    readback_expectation: FinalDeliverablePublicationReadbackExpectation | None = None,
    existing: GitHubIssueCommentSnapshot | None = None,
) -> LoveFinalDeliverablePublicationPlan:
    return LoveFinalDeliverablePublicationPlan(
        valid=valid,
        action=action,
        issue_action=issue_action,
        project_action=project_action,
        issues=issues,
        repository=command.repository,
        issue_number=command.issue_number,
        source_issue_ref=command.source_issue_ref,
        marker=marker,
        body=body,
        body_sha256=body_sha256,
        plan_ref=plan_ref,
        plan_digest=plan_digest,
        project_projection=projection,
        operations=operations,
        readback_expectation=readback_expectation,
        existing_comment_id=None if existing is None else existing.comment_id,
        existing_comment_url="" if existing is None else existing.html_url,
    )


def _invalid_plan(
    command: LoveFinalDeliverablePublicationCommand,
    issues: Sequence[str],
) -> LoveFinalDeliverablePublicationPlan:
    return LoveFinalDeliverablePublicationPlan(
        valid=False,
        action="blocked",
        issue_action="blocked",
        project_action="blocked",
        issues=tuple(issues),
        repository=command.repository,
        issue_number=command.issue_number,
        source_issue_ref=command.source_issue_ref,
        marker="",
        body="",
        body_sha256="",
        plan_ref="",
        plan_digest="",
        project_projection=None,
        operations=(),
        readback_expectation=None,
    )


def _value(obj: Any, name: str) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name)
    return getattr(obj, name, None)


def _require_result_text(obj: Any, name: str) -> str:
    value = _optional_result_text(obj, name)
    if not value:
        raise ValueError(f"result field {name} must be non-empty text")
    return value


def _optional_result_text(obj: Any, name: str, *, fallback: str = "") -> str:
    value = _value(obj, name)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _sequence_value(obj: Any, name: str) -> tuple[str, ...]:
    value = _value(obj, name)
    if value is None:
        return ()
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if not isinstance(value, Sequence):
        return ()
    return _merge_unique(tuple(str(item).strip() for item in value if str(item).strip()))


def _merge_unique(*groups: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    merged: list[str] = []
    for group in groups:
        for item in group:
            text = str(item).strip()
            if text and text not in seen:
                seen.add(text)
                merged.append(text)
    return tuple(merged)


def _markdown_items(
    items: Sequence[str],
    *,
    empty: str,
    code: bool = False,
    max_items: int = 20,
) -> str:
    normalized = _merge_unique(items)
    if not normalized:
        return empty
    lines: list[str] = []
    for item in normalized[:max_items]:
        rendered = f"`{item.replace('`', '')}`" if code else item
        lines.append(f"- {rendered}")
    if len(normalized) > max_items:
        lines.append(f"- … {len(normalized) - max_items} autre(s) référence(s)")
    return "\n".join(lines)


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    if limit <= 1:
        return value[:limit]
    return value[: limit - 1].rstrip() + "…"


def _require_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


__all__ = [
    "SCHEMA",
    "PROJECT_PROJECTION_SCHEMA",
    "READBACK_EXPECTATION_SCHEMA",
    "READBACK_RESULT_SCHEMA",
    "R12_RESULT_SCHEMA",
    "MARKER_PREFIX",
    "ProjectV2FieldSnapshot",
    "FinalDeliverableProjectV2Projection",
    "FinalDeliverablePublicationOperation",
    "FinalDeliverablePublicationReadbackExpectation",
    "LoveFinalDeliverablePublicationCommand",
    "LoveFinalDeliverablePublicationPlan",
    "FinalDeliverablePublicationReadbackResult",
    "plan_love_final_deliverable_publication",
    "render_love_final_deliverable_markdown",
    "verify_love_final_deliverable_publication_readback",
]
