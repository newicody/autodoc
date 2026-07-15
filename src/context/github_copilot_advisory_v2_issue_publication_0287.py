"""Controlled Issue publication for the Copilot first-opinion v2 contract.

The module is pure. It renders deterministic Markdown and decides whether the
publication would create, replay, or collide with one existing marked comment.
Network access remains in a local adapter.
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

PREVIEW_SCHEMA = "missipy.github.copilot_advisory_publication_preview.v2"
PLAN_SCHEMA = "missipy.github.copilot_advisory_v2_issue_publication_plan.v1"
MARKER_PREFIX = "autodoc:copilot-advisory-v2"
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


@dataclass(frozen=True, slots=True)
class CopilotAdvisoryV2IssuePublicationCommand:
    repository: str
    issue_number: int
    policy_decision_id: str
    operator_decision: str
    publication_preview: Mapping[str, Any]
    existing_comments: tuple[GitHubIssueCommentSnapshot, ...] = ()
    max_body_chars: int = 12_000

    def __post_init__(self) -> None:
        if not _REPOSITORY_RE.fullmatch(self.repository):
            raise ValueError("repository must be owner/name")
        if self.issue_number <= 0:
            raise ValueError("issue_number must be > 0")
        if not self.policy_decision_id.startswith("policy:"):
            raise ValueError("policy_decision_id must start with policy:")
        if self.operator_decision != "approve":
            raise ValueError("operator_decision must be approve")
        if not isinstance(self.publication_preview, Mapping):
            raise TypeError("publication_preview must be a mapping")
        if not isinstance(self.existing_comments, tuple):
            object.__setattr__(
                self,
                "existing_comments",
                tuple(self.existing_comments),
            )
        if self.max_body_chars < 1_000:
            raise ValueError("max_body_chars must be >= 1000")


@dataclass(frozen=True, slots=True)
class CopilotAdvisoryV2IssuePublicationPlan:
    valid: bool
    action: str
    issues: tuple[str, ...]
    repository: str
    issue_number: int
    marker: str
    body: str
    body_sha256: str
    plan_digest: str
    existing_comment_id: int | None = None
    existing_comment_url: str = ""

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": PLAN_SCHEMA,
            "valid": self.valid,
            "action": self.action,
            "issues": list(self.issues),
            "repository": self.repository,
            "issue_number": self.issue_number,
            "marker": self.marker,
            "body": self.body,
            "body_sha256": self.body_sha256,
            "plan_digest": self.plan_digest,
            "existing_comment_id": self.existing_comment_id,
            "existing_comment_url": self.existing_comment_url,
            "operator_decision_required": True,
            "github_mutation_allowed": False,
            "github_mutation_performed": False,
            "request_authoritative": True,
            "advisory_is_authority": False,
            "collision_guarded": True,
            "idempotent_replay": self.action == "replay",
        }


def plan_copilot_advisory_v2_issue_publication(
    command: CopilotAdvisoryV2IssuePublicationCommand,
) -> CopilotAdvisoryV2IssuePublicationPlan:
    preview = dict(command.publication_preview)
    issues = list(_validate_preview(preview))
    if preview.get("repository") != command.repository:
        issues.append("publication preview repository mismatch")
    if preview.get("issue_number") != command.issue_number:
        issues.append("publication preview Issue mismatch")
    issues = tuple(dict.fromkeys(issues))
    if issues:
        return _plan(command, "invalid", issues, "", "", "", "")

    marker = _build_marker(command.repository, command.issue_number, preview)
    body = render_copilot_advisory_v2_issue_comment(
        preview,
        marker=marker,
        max_body_chars=command.max_body_chars,
    )
    body_sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest()
    plan_digest = _plan_digest(command, marker, body_sha256)
    matches = [item for item in command.existing_comments if marker in item.body]

    if len(matches) > 1:
        return _plan(
            command,
            "collision",
            ("multiple existing comments carry the same marker",),
            marker,
            body,
            body_sha256,
            plan_digest,
        )
    if not matches:
        return _plan(
            command,
            "create",
            (),
            marker,
            body,
            body_sha256,
            plan_digest,
        )

    existing = matches[0]
    if existing.body == body:
        return _plan(
            command,
            "replay",
            (),
            marker,
            body,
            body_sha256,
            plan_digest,
            existing,
        )
    return _plan(
        command,
        "collision",
        ("existing marked comment differs from the approved publication",),
        marker,
        body,
        body_sha256,
        plan_digest,
        existing,
    )


def render_copilot_advisory_v2_issue_comment(
    preview: Mapping[str, Any],
    *,
    marker: str,
    max_body_chars: int = 12_000,
) -> str:
    objective = _required_text("concrete_objective", preview.get("concrete_objective"))
    expected = _required_text("expected_result", preview.get("expected_result"))
    constraints = _text_items("provided_constraints", preview.get("provided_constraints"))
    criteria = _text_items("success_criteria", preview.get("success_criteria"))
    artifact_ref = _required_text(
        "advisory_artifact_ref",
        preview.get("advisory_artifact_ref"),
    )
    source_ref = _required_text(
        "source_candidate_ref",
        preview.get("source_candidate_ref"),
    )
    run_ref = _required_text("workflow_run_ref", preview.get("workflow_run_ref"))

    sections = [
        f"<!-- {marker} -->",
        "## Autodoc — premier avis Copilot",
        "",
        "> Avis consultatif et non autoritatif. La demande GitHub et la décision ",
        "> opérateur restent l’autorité.",
        "",
        "### Objectif concret",
        objective,
        "",
        "### Résultat attendu",
        expected,
        "",
        "### Contraintes et éléments déjà fournis",
        _markdown_items(constraints, empty="Aucune contrainte explicite relevée."),
        "",
        "### Critères de réussite observables",
        _markdown_items(criteria, empty="Aucun critère valide fourni."),
        "",
        "<details>",
        "<summary>Références techniques</summary>",
        "",
        f"- Demande : `{source_ref}`",
        f"- Avis Copilot : `{artifact_ref}`",
        f"- Run : `{run_ref}`",
        f"- Empreinte réponse : `{preview.get('response_digest', '')}`",
        "",
        "</details>",
    ]
    body = "\n".join(sections).rstrip() + "\n"
    if len(body) <= max_body_chars:
        return body

    compact = sections[:9] + [
        "### Résultat attendu",
        _truncate(expected, 2_500),
        "",
        "### Contraintes et éléments déjà fournis",
        _markdown_items(constraints[:5], empty="Aucune contrainte explicite relevée."),
        "",
        "### Critères de réussite observables",
        _markdown_items(criteria[:5], empty="Aucun critère valide fourni."),
        "",
        "_Commentaire tronqué par la politique de publication Autodoc._",
    ]
    bounded = "\n".join(compact).rstrip() + "\n"
    if len(bounded) > max_body_chars:
        bounded = bounded[: max_body_chars - 1].rstrip() + "\n"
    return bounded


def parse_issue_comment_snapshots(
    payload: object,
) -> tuple[GitHubIssueCommentSnapshot, ...]:
    if not isinstance(payload, Sequence) or isinstance(
        payload,
        (str, bytes, bytearray),
    ):
        raise ValueError("comments payload must be a JSON array")
    comments: list[GitHubIssueCommentSnapshot] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise ValueError("each comment must be a JSON object")
        comments.append(
            GitHubIssueCommentSnapshot(
                comment_id=int(item.get("id", 0)),
                body=str(item.get("body", "")),
                html_url=str(item.get("html_url", "")),
            )
        )
    return tuple(comments)


def _validate_preview(preview: Mapping[str, Any]) -> tuple[str, ...]:
    issues: list[str] = []
    if preview.get("schema") != PREVIEW_SCHEMA:
        issues.append("unexpected publication preview schema")
    for name in (
        "source_candidate_ref",
        "advisory_artifact_ref",
        "concrete_objective",
        "expected_result",
        "workflow_run_ref",
        "response_digest",
        "repository",
    ):
        if not isinstance(preview.get(name), str) or not str(preview.get(name)).strip():
            issues.append(f"{name} must be non-empty")
    issue_number = preview.get("issue_number")
    if isinstance(issue_number, bool) or not isinstance(issue_number, int) or issue_number <= 0:
        issues.append("issue_number must be a positive integer")
    advisory_schema = preview.get("advisory_schema")
    if advisory_schema != "missipy.github.copilot_advisory.v2":
        issues.append("advisory_schema must identify Copilot advisory v2")
    response_digest = preview.get("response_digest")
    if not isinstance(response_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", response_digest):
        issues.append("response_digest must be a lowercase sha256")
    try:
        constraints = _text_items("provided_constraints", preview.get("provided_constraints"))
        criteria = _text_items("success_criteria", preview.get("success_criteria"))
    except (TypeError, ValueError) as exc:
        issues.append(str(exc))
    else:
        if not criteria:
            issues.append("success_criteria must not be empty")
        if len(constraints) > 100 or len(criteria) > 100:
            issues.append("publication lists exceed the bounded item count")
    if preview.get("request_authoritative") is not True:
        issues.append("request_authoritative must remain true")
    if preview.get("advisory_is_authority") is not False:
        issues.append("advisory_is_authority must remain false")
    if preview.get("operator_decision_required") is not True:
        issues.append("operator_decision_required must remain true")
    if preview.get("publication_gate_required") is not True:
        issues.append("publication_gate_required must remain true")
    if preview.get("github_mutation_performed") is not False:
        issues.append("preview must not claim a GitHub mutation")
    if preview.get("remote_mutation_allowed") not in (False, None):
        issues.append("preview must not pre-authorize remote mutation")
    return tuple(dict.fromkeys(issues))


def _build_marker(
    repository: str,
    issue_number: int,
    preview: Mapping[str, Any],
) -> str:
    payload = {
        "repository": repository,
        "issue_number": issue_number,
        "artifact_ref": preview.get("advisory_artifact_ref"),
        "response_digest": preview.get("response_digest"),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    return f"{MARKER_PREFIX}:{digest}"


def _plan_digest(
    command: CopilotAdvisoryV2IssuePublicationCommand,
    marker: str,
    body_sha256: str,
) -> str:
    payload = {
        "repository": command.repository,
        "issue_number": command.issue_number,
        "policy_decision_id": command.policy_decision_id,
        "marker": marker,
        "body_sha256": body_sha256,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _plan(
    command: CopilotAdvisoryV2IssuePublicationCommand,
    action: str,
    issues: tuple[str, ...],
    marker: str,
    body: str,
    body_sha256: str,
    plan_digest: str,
    existing: GitHubIssueCommentSnapshot | None = None,
) -> CopilotAdvisoryV2IssuePublicationPlan:
    return CopilotAdvisoryV2IssuePublicationPlan(
        valid=not issues,
        action=action,
        issues=issues,
        repository=command.repository,
        issue_number=command.issue_number,
        marker=marker,
        body=body,
        body_sha256=body_sha256,
        plan_digest=plan_digest,
        existing_comment_id=None if existing is None else existing.comment_id,
        existing_comment_url="" if existing is None else existing.html_url,
    )


def _required_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    return value.strip()


def _text_items(name: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{name} must be a string array")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"{name} must be a string array")
    return tuple(item.strip() for item in value if item.strip())


def _markdown_items(items: tuple[str, ...], *, empty: str) -> str:
    if not items:
        return empty
    return "\n".join(f"- {item}" for item in items)


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(1, limit - 1)].rstrip() + "…"
