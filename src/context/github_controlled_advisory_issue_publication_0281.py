"""Controlled, idempotent GitHub Issue publication contract for 0281-r6.

The module is pure. It renders one bounded operator-facing comment and decides
whether publication would create, replay, or collide with an existing marked
comment. Network access and mutation belong to the local adapter in ``tools``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any

from context.github_operator_laboratory_advisory_projection_0281 import (
    PUBLICATION_PREVIEW_SCHEMA,
)

SCHEMA = "missipy.github.controlled_advisory_issue_publication.v1"
PLAN_SCHEMA = "missipy.github.controlled_advisory_issue_publication_plan.v1"
MARKER_PREFIX = "autodoc:copilot-advisory"
_COMMENT_MARKER_RE = re.compile(
    r"<!--\s*(autodoc:copilot-advisory:[a-f0-9]{24})\s*-->"
)
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_ALLOWED_OPERATOR_DECISIONS = frozenset({"approve"})


@dataclass(frozen=True, slots=True)
class GitHubIssueCommentSnapshot:
    comment_id: int
    body: str
    html_url: str = ""

    def __post_init__(self) -> None:
        if self.comment_id <= 0:
            raise ValueError("comment_id must be > 0")
        if not isinstance(self.body, str):
            raise TypeError("body must be a string")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "body": self.body,
            "html_url": self.html_url,
        }


@dataclass(frozen=True, slots=True)
class GitHubControlledAdvisoryIssuePublicationCommand:
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
        if self.operator_decision not in _ALLOWED_OPERATOR_DECISIONS:
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
class GitHubControlledAdvisoryIssuePublicationPlan:
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
    operator_decision_required: bool = True
    github_mutation_allowed: bool = False
    github_mutation_performed: bool = False
    request_authoritative: bool = True
    advisory_is_authority: bool = False

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


def plan_github_controlled_advisory_issue_publication(
    command: GitHubControlledAdvisoryIssuePublicationCommand,
) -> GitHubControlledAdvisoryIssuePublicationPlan:
    """Build a deterministic create/replay/collision publication plan."""

    preview = dict(command.publication_preview)
    issues = list(_validate_preview(preview))
    if issues:
        return _invalid_plan(command, issues)

    marker = _build_marker(
        command.repository,
        command.issue_number,
        preview,
    )
    body = render_github_advisory_issue_comment(
        preview,
        marker=marker,
        max_body_chars=command.max_body_chars,
    )
    body_sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest()
    plan_digest = _plan_digest(
        command.repository,
        command.issue_number,
        marker,
        body_sha256,
        command.policy_decision_id,
    )

    matches = [
        comment
        for comment in command.existing_comments
        if marker in comment.body
    ]
    if len(matches) > 1:
        return _plan(
            command=command,
            action="collision",
            issues=("multiple existing comments carry the same marker",),
            marker=marker,
            body=body,
            body_sha256=body_sha256,
            plan_digest=plan_digest,
        )
    if not matches:
        return _plan(
            command=command,
            action="create",
            issues=(),
            marker=marker,
            body=body,
            body_sha256=body_sha256,
            plan_digest=plan_digest,
        )

    existing = matches[0]
    if existing.body == body:
        return _plan(
            command=command,
            action="replay",
            issues=(),
            marker=marker,
            body=body,
            body_sha256=body_sha256,
            plan_digest=plan_digest,
            existing=existing,
        )
    return _plan(
        command=command,
        action="collision",
        issues=(
            "existing marked comment differs from the approved publication",
        ),
        marker=marker,
        body=body,
        body_sha256=body_sha256,
        plan_digest=plan_digest,
        existing=existing,
    )


def render_github_advisory_issue_comment(
    preview: Mapping[str, Any],
    *,
    marker: str,
    max_body_chars: int = 12_000,
) -> str:
    """Render bounded Markdown with an invisible idempotency marker."""

    summary = _required_text("summary", preview.get("summary"))
    suggested_route = _required_text(
        "suggested_route",
        preview.get("suggested_route"),
    )
    context_ref = _required_text(
        "advisory_context_ref",
        preview.get("advisory_context_ref"),
    )
    artifact_ref = _required_text(
        "advisory_artifact_ref",
        preview.get("advisory_artifact_ref"),
    )
    questions = _text_items(preview.get("questions"))
    risks = _text_items(preview.get("risks"))
    confidence = float(preview.get("confidence", 0.0))

    sections = [
        f"<!-- {marker} -->",
        "## Autodoc — avis Copilot contrôlé",
        "",
        "> Avis consultatif et non autoritatif. "
        "La requête GitHub et la décision opérateur restent l’autorité.",
        "",
        "### Résumé",
        summary,
        "",
        "### Orientation proposée",
        suggested_route,
        "",
        "### Questions",
        _markdown_items(questions, empty="Aucune question proposée."),
        "",
        "### Risques",
        _markdown_items(risks, empty="Aucun risque proposé."),
        "",
        f"**Confiance indicative :** {confidence:.2f}",
        "",
        "<details>",
        "<summary>Références techniques</summary>",
        "",
        f"- Contexte : `{context_ref}`",
        f"- Artefact : `{artifact_ref}`",
        f"- Source SQL laboratoire : "
        f"`{str(preview.get('laboratory_source_sql_ref', ''))}`",
        f"- Résultat laboratoire : "
        f"`{str(preview.get('laboratory_source_final_ref', ''))}`",
        "",
        "</details>",
    ]
    body = "\n".join(sections).rstrip() + "\n"
    if len(body) <= max_body_chars:
        return body

    # Preserve marker, authority warning, summary and route. Bound only lists.
    compact = [
        f"<!-- {marker} -->",
        "## Autodoc — avis Copilot contrôlé",
        "",
        "> Avis consultatif et non autoritatif. "
        "La requête GitHub et la décision opérateur restent l’autorité.",
        "",
        "### Résumé",
        _truncate(summary, 2_500),
        "",
        "### Orientation proposée",
        _truncate(suggested_route, 2_500),
        "",
        "### Questions",
        _markdown_items(questions[:5], empty="Aucune question proposée."),
        "",
        "### Risques",
        _markdown_items(risks[:5], empty="Aucun risque proposé."),
        "",
        f"**Confiance indicative :** {confidence:.2f}",
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
    """Parse the bounded subset returned by GitHub's issue comments API."""

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
    if preview.get("schema") != PUBLICATION_PREVIEW_SCHEMA:
        issues.append("unexpected publication preview schema")
    for name in (
        "source_candidate_ref",
        "advisory_context_ref",
        "advisory_artifact_ref",
        "summary",
        "suggested_route",
    ):
        if not isinstance(preview.get(name), str) or not str(
            preview.get(name)
        ).strip():
            issues.append(f"{name} must be non-empty")
    try:
        confidence = float(preview.get("confidence"))
    except (TypeError, ValueError):
        issues.append("confidence must be numeric")
    else:
        if not 0.0 <= confidence <= 1.0:
            issues.append("confidence must be between 0 and 1")
    if preview.get("advisory_is_authority") is not False:
        issues.append("advisory_is_authority must remain false")
    if preview.get("operator_decision_required") is not True:
        issues.append("operator_decision_required must remain true")
    if preview.get("publication_gate_required") is not True:
        issues.append("publication_gate_required must remain true")
    if preview.get("github_mutation_performed") is not False:
        issues.append("preview must not claim a GitHub mutation")
    return tuple(dict.fromkeys(issues))


def _build_marker(
    repository: str,
    issue_number: int,
    preview: Mapping[str, Any],
) -> str:
    identity = "\0".join(
        (
            repository,
            str(issue_number),
            _required_text(
                "source_candidate_ref",
                preview.get("source_candidate_ref"),
            ),
            _required_text(
                "advisory_artifact_ref",
                preview.get("advisory_artifact_ref"),
            ),
        )
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    return f"{MARKER_PREFIX}:{digest}"


def _plan_digest(
    repository: str,
    issue_number: int,
    marker: str,
    body_sha256: str,
    policy_decision_id: str,
) -> str:
    payload = {
        "repository": repository,
        "issue_number": issue_number,
        "marker": marker,
        "body_sha256": body_sha256,
        "policy_decision_id": policy_decision_id,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _plan(
    *,
    command: GitHubControlledAdvisoryIssuePublicationCommand,
    action: str,
    issues: Sequence[str],
    marker: str,
    body: str,
    body_sha256: str,
    plan_digest: str,
    existing: GitHubIssueCommentSnapshot | None = None,
) -> GitHubControlledAdvisoryIssuePublicationPlan:
    return GitHubControlledAdvisoryIssuePublicationPlan(
        valid=not issues and action in {"create", "replay"},
        action=action,
        issues=tuple(dict.fromkeys(issues)),
        repository=command.repository,
        issue_number=command.issue_number,
        marker=marker,
        body=body,
        body_sha256=body_sha256,
        plan_digest=plan_digest,
        existing_comment_id=(
            None if existing is None else existing.comment_id
        ),
        existing_comment_url=(
            "" if existing is None else existing.html_url
        ),
    )


def _invalid_plan(
    command: GitHubControlledAdvisoryIssuePublicationCommand,
    issues: Sequence[str],
) -> GitHubControlledAdvisoryIssuePublicationPlan:
    return _plan(
        command=command,
        action="blocked",
        issues=issues,
        marker="",
        body="",
        body_sha256="",
        plan_digest="",
    )


def _required_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    return value.strip()


def _text_items(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(
        dict.fromkeys(
            item.strip()
            for item in value
            if isinstance(item, str) and item.strip()
        )
    )


def _markdown_items(values: Sequence[str], *, empty: str) -> str:
    if not values:
        return empty
    return "\n".join(f"- {value}" for value in values)


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"


__all__ = (
    "MARKER_PREFIX",
    "PLAN_SCHEMA",
    "SCHEMA",
    "GitHubControlledAdvisoryIssuePublicationCommand",
    "GitHubControlledAdvisoryIssuePublicationPlan",
    "GitHubIssueCommentSnapshot",
    "parse_issue_comment_snapshots",
    "plan_github_controlled_advisory_issue_publication",
    "render_github_advisory_issue_comment",
)
