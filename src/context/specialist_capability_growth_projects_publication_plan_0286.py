"""Deterministic GitHub Projects publication plan for capability growth.

Phase 0286-r5 converts the immutable 0286-r2 review projection into one
bounded, digest-bound publication plan.  The plan contains an append-only Issue
comment and the allowed ProjectV2 field values, but performs no network access
and no remote mutation.  Execution remains reserved for the existing
operator-authorized GitHub boundary introduced in the next phase.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Protocol

from context.specialist_capability_growth_projects_review_projection_0286 import (
    SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION_SCHEMA,
    SpecialistCapabilityGrowthProjectsReviewProjection,
)


SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_SCHEMA = (
    "missipy.specialist.capability_growth.projects_publication_plan.v1"
)
SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_VERSION = "0286.r5"
SPECIALIST_CAPABILITY_GROWTH_COMMENT_MARKER_PREFIX = (
    "autodoc:specialist-capability-growth"
)

_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PROJECT_ID_RE = re.compile(r"^PVT_[A-Za-z0-9_-]+$")
_PROJECT_ITEM_ID_RE = re.compile(r"^PVTI_[A-Za-z0-9_-]+$")

_ALLOWED_PROJECTV2_FIELDS = (
    "Spécialiste",
    "Révision spécialiste",
    "Capacité proposée",
    "Action capacité",
    "Décision capacité",
    "Statut révision",
    "Référence SQL",
    "Digest décision",
    "Laboratoire",
)


class SpecialistCapabilityGrowthProjectsPublicationPlanError(ValueError):
    """Raised when a safe publication plan cannot be built."""


class GitHubIssueCommentSnapshotLike(Protocol):
    """Structural boundary compatible with the existing 0281 snapshot."""

    @property
    def comment_id(self) -> int:
        """Return the remote Issue comment identifier."""

    @property
    def body(self) -> str:
        """Return the complete remote Issue comment body."""

    @property
    def html_url(self) -> str:
        """Return the optional GitHub comment URL."""


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthProjectV2FieldMutation:
    """One deterministic desired ProjectV2 field mutation."""

    field_name: str
    desired_value: str
    current_value: str | None
    action: str

    def __post_init__(self) -> None:
        if self.field_name not in _ALLOWED_PROJECTV2_FIELDS:
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                f"unsupported ProjectV2 field: {self.field_name}"
            )
        if not isinstance(self.desired_value, str) or not self.desired_value.strip():
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                "desired ProjectV2 field values must be non-empty strings"
            )
        if self.current_value is not None and not isinstance(self.current_value, str):
            raise TypeError("current_value must be a string or None")
        expected = "replay" if self.current_value == self.desired_value else "set"
        if self.action != expected:
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                "field mutation action does not match current and desired values"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "field_name": self.field_name,
            "desired_value": self.desired_value,
            "current_value": self.current_value,
            "action": self.action,
        }


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthProjectsPublicationCommand:
    """Typed intent for building a non-mutating publication plan."""

    repository: str
    issue_number: int
    project_id: str
    project_item_id: str
    policy_decision_id: str
    operator_decision: str
    review_projection: SpecialistCapabilityGrowthProjectsReviewProjection
    existing_comments: tuple[GitHubIssueCommentSnapshotLike, ...] = field(
        default_factory=tuple
    )
    existing_projectv2_field_values: tuple[tuple[str, str], ...] = field(
        default_factory=tuple
    )
    max_comment_chars: int = 12_000

    def __post_init__(self) -> None:
        if not _REPOSITORY_RE.fullmatch(self.repository):
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                "repository must be owner/name"
            )
        if self.issue_number <= 0:
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                "issue_number must be > 0"
            )
        if not _PROJECT_ID_RE.fullmatch(self.project_id):
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                "project_id must start with PVT_"
            )
        if not _PROJECT_ITEM_ID_RE.fullmatch(self.project_item_id):
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                "project_item_id must start with PVTI_"
            )
        if not self.policy_decision_id.startswith("policy:"):
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                "policy_decision_id must start with policy:"
            )
        if self.operator_decision != "approve":
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                "operator_decision must be approve"
            )
        if not isinstance(
            self.review_projection,
            SpecialistCapabilityGrowthProjectsReviewProjection,
        ):
            raise TypeError(
                "review_projection must be "
                "SpecialistCapabilityGrowthProjectsReviewProjection"
            )
        object.__setattr__(self, "existing_comments", tuple(self.existing_comments))
        object.__setattr__(
            self,
            "existing_projectv2_field_values",
            _normalize_existing_field_values(self.existing_projectv2_field_values),
        )
        if self.max_comment_chars < 2_000:
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                "max_comment_chars must be >= 2000"
            )


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthProjectsPublicationPlan:
    """One immutable Issue comment and ProjectV2 field publication plan."""

    schema: str
    valid: bool
    action: str
    issues: tuple[str, ...]
    repository: str
    issue_number: int
    project_id: str
    project_item_id: str
    policy_decision_id: str
    review_ref: str
    revision_ref: str
    sql_ref: str
    decision_ref: str
    projection_digest_sha256: str
    marker: str
    comment_action: str
    comment_body: str
    comment_body_sha256: str
    existing_comment_id: int | None
    existing_comment_url: str
    projectv2_action: str
    projectv2_field_mutations: tuple[
        SpecialistCapabilityGrowthProjectV2FieldMutation, ...
    ]
    plan_digest: str
    operator_decision_required: bool = field(default=True, init=False)
    remote_mutation_allowed: bool = field(default=False, init=False)
    github_mutation_performed: bool = field(default=False, init=False)
    issue_comment_published: bool = field(default=False, init=False)
    projectv2_mutation_performed: bool = field(default=False, init=False)
    github_projects_authoritative: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_SCHEMA:
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                "unsupported publication plan schema"
            )
        if self.action not in {
            "create_comment_and_set_fields",
            "create_comment",
            "set_fields",
            "replay",
            "collision",
            "blocked",
        }:
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                "unsupported publication plan action"
            )
        if self.comment_action not in {"create", "replay", "collision", "blocked"}:
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                "unsupported comment action"
            )
        if self.projectv2_action not in {"set", "replay", "blocked"}:
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                "unsupported ProjectV2 action"
            )
        if self.valid != (not self.issues and self.action not in {"collision", "blocked"}):
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                "valid flag does not match plan issues/action"
            )
        if self.plan_digest and not _SHA256_RE.fullmatch(self.plan_digest):
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                "plan_digest must be a lowercase SHA-256"
            )

    @property
    def projectv2_field_values(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            (mutation.field_name, mutation.desired_value)
            for mutation in self.projectv2_field_mutations
        )

    @property
    def projectv2_field_changes(self) -> tuple[
        SpecialistCapabilityGrowthProjectV2FieldMutation, ...
    ]:
        return tuple(
            mutation
            for mutation in self.projectv2_field_mutations
            if mutation.action == "set"
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "action": self.action,
            "issues": list(self.issues),
            "repository": self.repository,
            "issue_number": self.issue_number,
            "project_id": self.project_id,
            "project_item_id": self.project_item_id,
            "policy_decision_id": self.policy_decision_id,
            "review_ref": self.review_ref,
            "revision_ref": self.revision_ref,
            "sql_ref": self.sql_ref,
            "decision_ref": self.decision_ref,
            "projection_digest_sha256": self.projection_digest_sha256,
            "marker": self.marker,
            "comment_action": self.comment_action,
            "comment_body": self.comment_body,
            "comment_body_sha256": self.comment_body_sha256,
            "existing_comment_id": self.existing_comment_id,
            "existing_comment_url": self.existing_comment_url,
            "projectv2_action": self.projectv2_action,
            "projectv2_field_values": dict(self.projectv2_field_values),
            "projectv2_field_mutations": [
                mutation.to_mapping()
                for mutation in self.projectv2_field_mutations
            ],
            "projectv2_field_changes": [
                mutation.to_mapping()
                for mutation in self.projectv2_field_changes
            ],
            "plan_digest": self.plan_digest,
            "operator_decision_required": True,
            "remote_mutation_allowed": False,
            "github_mutation_performed": False,
            "issue_comment_published": False,
            "projectv2_mutation_performed": False,
            "github_projects_authoritative": False,
            "sql_remains_durable_authority": True,
            "scheduler_remains_only_orchestrator": True,
            "qdrant_authoritative": False,
            "copilot_authoritative": False,
            "collision_guarded": True,
            "idempotent_replay": self.action == "replay",
            "new_scheduler_created": False,
            "new_global_specialist_registry_created": False,
            "new_http_client_created": False,
        }


def plan_specialist_capability_growth_projects_publication(
    command: SpecialistCapabilityGrowthProjectsPublicationCommand,
) -> SpecialistCapabilityGrowthProjectsPublicationPlan:
    """Build a deterministic create/replay/collision publication plan."""

    projection = command.review_projection
    issues = list(_validate_review_projection(projection))
    if issues:
        return _blocked_plan(command, issues)

    marker = _build_marker(command)
    comment_body = render_specialist_capability_growth_issue_comment(
        projection,
        marker=marker,
        max_comment_chars=command.max_comment_chars,
    )
    comment_body_sha256 = sha256(comment_body.encode("utf-8")).hexdigest()
    comment_action, existing_comment_id, existing_comment_url, comment_issues = (
        _plan_comment_action(
            command.existing_comments,
            marker=marker,
            expected_body=comment_body,
        )
    )
    issues.extend(comment_issues)

    field_mutations = _build_field_mutations(
        projection.projectv2_field_values,
        command.existing_projectv2_field_values,
    )
    projectv2_action = (
        "replay"
        if all(mutation.action == "replay" for mutation in field_mutations)
        else "set"
    )

    if issues or comment_action == "collision":
        action = "collision"
        projectv2_action = "blocked"
    elif comment_action == "create" and projectv2_action == "set":
        action = "create_comment_and_set_fields"
    elif comment_action == "create":
        action = "create_comment"
    elif projectv2_action == "set":
        action = "set_fields"
    else:
        action = "replay"

    plan_digest = _plan_digest(
        command=command,
        marker=marker,
        comment_body_sha256=comment_body_sha256,
        field_mutations=field_mutations,
        action=action,
    )
    return SpecialistCapabilityGrowthProjectsPublicationPlan(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_SCHEMA,
        valid=not issues and action != "collision",
        action=action,
        issues=tuple(dict.fromkeys(issues)),
        repository=command.repository,
        issue_number=command.issue_number,
        project_id=command.project_id,
        project_item_id=command.project_item_id,
        policy_decision_id=command.policy_decision_id,
        review_ref=projection.review_ref,
        revision_ref=projection.revision_ref,
        sql_ref=projection.sql_ref,
        decision_ref=projection.decision_ref,
        projection_digest_sha256=projection.projection_digest,
        marker=marker,
        comment_action=comment_action,
        comment_body=comment_body,
        comment_body_sha256=comment_body_sha256,
        existing_comment_id=existing_comment_id,
        existing_comment_url=existing_comment_url,
        projectv2_action=projectv2_action,
        projectv2_field_mutations=field_mutations,
        plan_digest=plan_digest,
    )


def render_specialist_capability_growth_issue_comment(
    projection: SpecialistCapabilityGrowthProjectsReviewProjection,
    *,
    marker: str,
    max_comment_chars: int = 12_000,
) -> str:
    """Render one bounded, operator-facing, append-only review comment."""

    context_lines = [f"- `{_inline_code(value)}`" for value in projection.context_refs]
    evidence_lines = [f"- `{_inline_code(value)}`" for value in projection.evidence_refs]
    lines = [
        f"<!-- {marker} -->",
        "## Autodoc — révision de capacité spécialiste",
        "",
        "> Projection de revue non autoritative. SQL conserve l’historique durable; "
        "la décision opérateur locale et le Scheduler Autodoc restent les autorités.",
        "",
        "### Révision approuvée",
        "",
        f"- Spécialiste : `{_inline_code(projection.specialist_ref)}`",
        f"- Version : `{_inline_code(projection.specialist_version)}`",
        f"- Révision : `{_inline_code(projection.revision_ref)}`",
        f"- Capacité : `{_inline_code(projection.capability)}`",
        f"- Action : `{_inline_code(projection.action)}`",
        f"- Décision : `{_inline_code(projection.decision_outcome)}`",
        f"- Statut : `{_inline_code(projection.review_status)}`",
        f"- Laboratoire : `{_inline_code(projection.laboratory_ref)}`",
        "",
        "### Preuves et contexte",
        "",
        *(evidence_lines or ["- Aucune référence de preuve."]),
        "",
        "Contextes :",
        *(context_lines or ["- Aucun contexte."]),
        "",
        "### Corrélation locale",
        "",
        f"- SQL : `{_inline_code(projection.sql_ref)}`",
        f"- Entrée historique : `{_inline_code(projection.history_entry_ref)}`",
        f"- Décision : `{_inline_code(projection.decision_ref)}`",
        f"- Sélection Scheduler : `{_inline_code(projection.selection_ref)}`",
        f"- Projection : `{projection.projection_digest}`",
        f"- Digest décision : `{projection.decision_digest_sha256}`",
        "",
        "_Ce commentaire ne constitue ni une nouvelle décision, ni une autorisation "
        "d’exécution, ni une source d’autorité durable._",
        "",
    ]
    body = "\n".join(lines)
    if len(body) <= max_comment_chars:
        return body

    compact = [
        f"<!-- {marker} -->",
        "## Autodoc — révision de capacité spécialiste",
        "",
        "> Projection de revue non autoritative; SQL et la décision opérateur locale "
        "restent les autorités.",
        "",
        f"- Spécialiste : `{_inline_code(projection.specialist_ref)}`",
        f"- Révision : `{_inline_code(projection.revision_ref)}`",
        f"- Capacité : `{_inline_code(projection.capability)}`",
        f"- Décision : `{_inline_code(projection.decision_outcome)}`",
        f"- SQL : `{_inline_code(projection.sql_ref)}`",
        f"- Projection : `{projection.projection_digest}`",
        "",
        "_Commentaire réduit par la politique de taille Autodoc._",
        "",
    ]
    bounded = "\n".join(compact)
    if len(bounded) > max_comment_chars:
        raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
            "max_comment_chars is too small for the mandatory publication comment"
        )
    return bounded


def _validate_review_projection(
    projection: SpecialistCapabilityGrowthProjectsReviewProjection,
) -> tuple[str, ...]:
    issues: list[str] = []
    mapping = projection.to_mapping()
    if mapping.get("schema") != SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION_SCHEMA:
        issues.append("unexpected review projection schema")
    required_true = (
        "review_only",
        "phase_0285_closed_required",
        "operator_decision_preserved",
        "sql_remains_durable_authority",
        "scheduler_remains_only_orchestrator",
        "eventbus_observation_reused",
    )
    for key in required_true:
        if mapping.get(key) is not True:
            issues.append(f"review projection requires {key}=true")
    required_false = (
        "github_projects_authoritative",
        "publication_performed",
        "projectv2_mutation_performed",
        "issue_comment_published",
        "qdrant_authoritative",
        "copilot_authoritative",
        "new_scheduler_created",
        "new_global_specialist_registry_created",
        "new_http_client_created",
    )
    for key in required_false:
        if mapping.get(key) is not False:
            issues.append(f"review projection requires {key}=false")
    if projection.decision_outcome != "approve":
        issues.append("review projection must preserve an approved decision")
    if not _SHA256_RE.fullmatch(projection.projection_digest):
        issues.append("review projection digest must be a lowercase SHA-256")
    field_names = tuple(name for name, _value in projection.projectv2_field_values)
    if field_names != _ALLOWED_PROJECTV2_FIELDS:
        issues.append("review projection field set drifted from the r4 contract")
    return tuple(dict.fromkeys(issues))


def _build_marker(
    command: SpecialistCapabilityGrowthProjectsPublicationCommand,
) -> str:
    projection = command.review_projection
    identity = "\0".join(
        (
            command.repository,
            str(command.issue_number),
            projection.review_ref,
            projection.revision_ref,
            projection.projection_digest,
        )
    )
    digest = sha256(identity.encode("utf-8")).hexdigest()[:24]
    return f"{SPECIALIST_CAPABILITY_GROWTH_COMMENT_MARKER_PREFIX}:{digest}"


def _plan_comment_action(
    comments: Sequence[GitHubIssueCommentSnapshotLike],
    *,
    marker: str,
    expected_body: str,
) -> tuple[str, int | None, str, tuple[str, ...]]:
    matches: list[tuple[int, str, str]] = []
    for comment in comments:
        comment_id = getattr(comment, "comment_id", None)
        body = getattr(comment, "body", None)
        html_url = getattr(comment, "html_url", "")
        if not isinstance(comment_id, int) or comment_id <= 0:
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                "existing comment_id must be a positive integer"
            )
        if not isinstance(body, str):
            raise TypeError("existing comment body must be a string")
        if not isinstance(html_url, str):
            raise TypeError("existing comment html_url must be a string")
        if marker in body:
            matches.append((comment_id, body, html_url))
    if len(matches) > 1:
        return (
            "collision",
            None,
            "",
            ("multiple existing comments carry the same idempotency marker",),
        )
    if not matches:
        return "create", None, "", ()
    comment_id, body, html_url = matches[0]
    if body == expected_body:
        return "replay", comment_id, html_url, ()
    return (
        "collision",
        comment_id,
        html_url,
        ("existing marked comment differs from the approved publication",),
    )


def _build_field_mutations(
    desired_values: Sequence[tuple[str, str]],
    existing_values: Sequence[tuple[str, str]],
) -> tuple[SpecialistCapabilityGrowthProjectV2FieldMutation, ...]:
    existing = dict(existing_values)
    mutations = tuple(
        SpecialistCapabilityGrowthProjectV2FieldMutation(
            field_name=name,
            desired_value=value,
            current_value=existing.get(name),
            action="replay" if existing.get(name) == value else "set",
        )
        for name, value in desired_values
    )
    if tuple(item.field_name for item in mutations) != _ALLOWED_PROJECTV2_FIELDS:
        raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
            "publication field order drifted from the review projection"
        )
    return mutations


def _plan_digest(
    *,
    command: SpecialistCapabilityGrowthProjectsPublicationCommand,
    marker: str,
    comment_body_sha256: str,
    field_mutations: Sequence[SpecialistCapabilityGrowthProjectV2FieldMutation],
    action: str,
) -> str:
    payload = {
        "schema": SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_SCHEMA,
        "repository": command.repository,
        "issue_number": command.issue_number,
        "project_id": command.project_id,
        "project_item_id": command.project_item_id,
        "policy_decision_id": command.policy_decision_id,
        "operator_decision": command.operator_decision,
        "review_ref": command.review_projection.review_ref,
        "revision_ref": command.review_projection.revision_ref,
        "sql_ref": command.review_projection.sql_ref,
        "projection_digest_sha256": command.review_projection.projection_digest,
        "marker": marker,
        "comment_body_sha256": comment_body_sha256,
        "field_mutations": [item.to_mapping() for item in field_mutations],
        "action": action,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _blocked_plan(
    command: SpecialistCapabilityGrowthProjectsPublicationCommand,
    issues: Sequence[str],
) -> SpecialistCapabilityGrowthProjectsPublicationPlan:
    projection = command.review_projection
    return SpecialistCapabilityGrowthProjectsPublicationPlan(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_SCHEMA,
        valid=False,
        action="blocked",
        issues=tuple(dict.fromkeys(issues)),
        repository=command.repository,
        issue_number=command.issue_number,
        project_id=command.project_id,
        project_item_id=command.project_item_id,
        policy_decision_id=command.policy_decision_id,
        review_ref=projection.review_ref,
        revision_ref=projection.revision_ref,
        sql_ref=projection.sql_ref,
        decision_ref=projection.decision_ref,
        projection_digest_sha256=projection.projection_digest,
        marker="",
        comment_action="blocked",
        comment_body="",
        comment_body_sha256="",
        existing_comment_id=None,
        existing_comment_url="",
        projectv2_action="blocked",
        projectv2_field_mutations=(),
        plan_digest="",
    )


def _normalize_existing_field_values(
    values: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    normalized: dict[str, str] = {}
    for item in values:
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError(
                "existing_projectv2_field_values must contain (name, value) tuples"
            )
        name, value = item
        if name not in _ALLOWED_PROJECTV2_FIELDS:
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                f"unexpected existing ProjectV2 field: {name}"
            )
        if not isinstance(value, str):
            raise TypeError("existing ProjectV2 field values must be strings")
        if name in normalized:
            raise SpecialistCapabilityGrowthProjectsPublicationPlanError(
                f"duplicate existing ProjectV2 field: {name}"
            )
        normalized[name] = value
    return tuple((name, normalized[name]) for name in _ALLOWED_PROJECTV2_FIELDS if name in normalized)


def _inline_code(value: object) -> str:
    return str(value).replace("`", "'").strip()


__all__ = (
    "SPECIALIST_CAPABILITY_GROWTH_COMMENT_MARKER_PREFIX",
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_SCHEMA",
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_VERSION",
    "GitHubIssueCommentSnapshotLike",
    "SpecialistCapabilityGrowthProjectV2FieldMutation",
    "SpecialistCapabilityGrowthProjectsPublicationCommand",
    "SpecialistCapabilityGrowthProjectsPublicationPlan",
    "SpecialistCapabilityGrowthProjectsPublicationPlanError",
    "plan_specialist_capability_growth_projects_publication",
    "render_specialist_capability_growth_issue_comment",
)
