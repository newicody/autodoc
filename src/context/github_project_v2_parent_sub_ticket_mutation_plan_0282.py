"""Deterministic parent/sub-ticket mutation plan for phase 0282-r5.

The module consumes the append-only cycle history from 0282-r4 and an explicit
snapshot of the relevant GitHub Issues. It produces a bounded create/link,
link-only, replay, collision or blocked plan.

This is a pure planning boundary. It performs no HTTP request, GraphQL query,
GraphQL mutation, GitHub write, filesystem write, SQL write, Qdrant write,
Scheduler change or laboratory execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from context.github_project_v2_append_only_cycle_history_0282 import (
    GitHubProjectV2AppendOnlyCycleHistoryResult,
    GitHubProjectV2CycleHistoryEntry,
)


ISSUE_SNAPSHOT_SCHEMA = (
    "missipy.github.project_v2_issue_snapshot.v1"
)
MUTATION_OPERATION_SCHEMA = (
    "missipy.github.project_v2_parent_sub_ticket_mutation_operation.v1"
)
MUTATION_PLAN_SCHEMA = (
    "missipy.github.project_v2_parent_sub_ticket_mutation_plan.v1"
)
MARKER_PREFIX = "autodoc:projectv2-cycle"

_REPOSITORY_RE = re.compile(
    r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$"
)
_ISSUE_REF_RE = re.compile(
    r"^github-frame:"
    r"(?P<repository>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"
    r"/issues/(?P<number>[1-9][0-9]*)$"
)
_ALLOWED_OPERATOR_DECISIONS = frozenset({"approve"})
_ALLOWED_STATES = frozenset({"OPEN", "CLOSED"})
_ALLOWED_OPERATION_KINDS = frozenset(
    {"create_issue", "add_sub_issue"}
)


@dataclass(frozen=True, slots=True)
class GitHubProjectV2IssueSnapshot:
    issue_ref: str
    issue_number: int
    title: str
    body: str
    parent_issue_ref: str = ""
    sub_issue_refs: tuple[str, ...] = ()
    state: str = "OPEN"
    html_url: str = ""

    def __post_init__(self) -> None:
        repository, parsed_number = _parse_issue_ref(self.issue_ref)
        if self.issue_number <= 0:
            raise ValueError("issue_number must be > 0")
        if parsed_number != self.issue_number:
            raise ValueError(
                "issue_number must match issue_ref"
            )
        if not self.title.strip():
            raise ValueError("title must be non-empty")
        if not isinstance(self.body, str):
            raise TypeError("body must be a string")
        if self.parent_issue_ref:
            parent_repository, _ = _parse_issue_ref(
                self.parent_issue_ref
            )
            if parent_repository != repository:
                raise ValueError(
                    "parent_issue_ref repository mismatch"
                )
        normalized_sub_issues = tuple(
            sorted(ref.strip() for ref in self.sub_issue_refs)
        )
        if any(not ref for ref in normalized_sub_issues):
            raise ValueError(
                "sub_issue_refs must not contain empty references"
            )
        if len(normalized_sub_issues) != len(
            set(normalized_sub_issues)
        ):
            raise ValueError("sub_issue_refs must be unique")
        for ref in normalized_sub_issues:
            child_repository, _ = _parse_issue_ref(ref)
            if child_repository != repository:
                raise ValueError(
                    "sub_issue_refs repository mismatch"
                )
        if self.issue_ref in normalized_sub_issues:
            raise ValueError(
                "issue must not reference itself as a sub-issue"
            )
        normalized_state = self.state.strip().upper()
        if normalized_state not in _ALLOWED_STATES:
            raise ValueError("state must be OPEN or CLOSED")
        object.__setattr__(
            self,
            "sub_issue_refs",
            normalized_sub_issues,
        )
        object.__setattr__(self, "state", normalized_state)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": ISSUE_SNAPSHOT_SCHEMA,
            "issue_ref": self.issue_ref,
            "issue_number": self.issue_number,
            "title": self.title,
            "body": self.body,
            "body_sha256": _sha256_text(self.body),
            "parent_issue_ref": self.parent_issue_ref,
            "sub_issue_refs": list(self.sub_issue_refs),
            "state": self.state,
            "html_url": self.html_url,
        }


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ParentSubTicketMutationCommand:
    history: GitHubProjectV2AppendOnlyCycleHistoryResult
    policy_decision_id: str
    operator_decision: str
    next_cycle_title: str
    next_cycle_summary: str
    existing_issues: tuple[GitHubProjectV2IssueSnapshot, ...]
    source_artifact_refs: tuple[str, ...] = ()
    decision_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.policy_decision_id.startswith("policy:"):
            raise ValueError(
                "policy_decision_id must start with policy:"
            )
        if self.operator_decision not in _ALLOWED_OPERATOR_DECISIONS:
            raise ValueError("operator_decision must be approve")
        if not self.next_cycle_title.strip():
            raise ValueError("next_cycle_title must be non-empty")
        if not self.next_cycle_summary.strip():
            raise ValueError("next_cycle_summary must be non-empty")
        if not isinstance(self.existing_issues, tuple):
            object.__setattr__(
                self,
                "existing_issues",
                tuple(self.existing_issues),
            )


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ParentSubTicketMutationPolicy:
    require_valid_history: bool = True
    require_root_issue_snapshot: bool = True
    require_latest_cycle: bool = True
    require_open_existing_issue: bool = True
    allow_link_existing: bool = True
    max_title_chars: int = 180
    max_summary_chars: int = 8_000
    max_existing_issues: int = 500
    max_source_artifact_refs: int = 128
    max_decision_refs: int = 64

    def __post_init__(self) -> None:
        if self.max_title_chars <= 0:
            raise ValueError("max_title_chars must be > 0")
        if self.max_summary_chars <= 0:
            raise ValueError("max_summary_chars must be > 0")
        if self.max_existing_issues <= 0:
            raise ValueError("max_existing_issues must be > 0")
        if self.max_source_artifact_refs < 0:
            raise ValueError(
                "max_source_artifact_refs must be >= 0"
            )
        if self.max_decision_refs < 0:
            raise ValueError(
                "max_decision_refs must be >= 0"
            )


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ParentSubTicketMutationOperation:
    operation_ref: str
    kind: str
    repository: str
    target_ref: str
    parent_issue_ref: str = ""
    child_issue_ref: str = ""
    title: str = ""
    body: str = ""
    depends_on: tuple[str, ...] = ()
    preconditions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in _ALLOWED_OPERATION_KINDS:
            raise ValueError("unsupported mutation operation kind")
        if not self.operation_ref.startswith(
            "github-project-v2-operation:"
        ):
            raise ValueError(
                "operation_ref must use GitHub ProjectV2 prefix"
            )
        if not _REPOSITORY_RE.fullmatch(self.repository):
            raise ValueError("repository must use owner/name form")

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": MUTATION_OPERATION_SCHEMA,
            "operation_ref": self.operation_ref,
            "kind": self.kind,
            "repository": self.repository,
            "target_ref": self.target_ref,
            "parent_issue_ref": self.parent_issue_ref,
            "child_issue_ref": self.child_issue_ref,
            "title": self.title,
            "body": self.body,
            "body_sha256": (
                _sha256_text(self.body) if self.body else ""
            ),
            "depends_on": list(self.depends_on),
            "preconditions": list(self.preconditions),
            "github_mutation_allowed": False,
            "github_mutation_performed": False,
        }


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ParentSubTicketMutationPlan:
    valid: bool
    action: str
    issues: tuple[str, ...]
    plan_ref: str
    plan_digest: str
    repository: str
    root_issue_ref: str
    previous_cycle_ref: str
    next_cycle_ordinal: int
    marker: str
    title: str
    body: str
    planned_issue_ref: str
    existing_issue_ref: str
    operations: tuple[
        GitHubProjectV2ParentSubTicketMutationOperation,
        ...,
    ]
    boundaries: tuple[tuple[str, bool], ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": MUTATION_PLAN_SCHEMA,
            "valid": self.valid,
            "action": self.action,
            "issues": list(self.issues),
            "plan_ref": self.plan_ref,
            "plan_digest": self.plan_digest,
            "repository": self.repository,
            "root_issue_ref": self.root_issue_ref,
            "previous_cycle_ref": self.previous_cycle_ref,
            "next_cycle_ordinal": self.next_cycle_ordinal,
            "marker": self.marker,
            "title": self.title,
            "body": self.body,
            "body_sha256": (
                _sha256_text(self.body) if self.body else ""
            ),
            "planned_issue_ref": self.planned_issue_ref,
            "existing_issue_ref": self.existing_issue_ref,
            "operations": [
                operation.to_json_dict()
                for operation in self.operations
            ],
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"project_v2_parent_sub_ticket_plan_valid={self.valid}",
                f"action={self.action}",
                f"issues={len(self.issues)}",
                f"operations={len(self.operations)}",
                f"next_cycle={self.next_cycle_ordinal}",
                f"plan_ref={self.plan_ref or '-'}",
                "github_mutation_allowed=False",
                "github_mutation_performed=False",
            )
        )


def plan_github_project_v2_parent_sub_ticket_mutation(
    command: GitHubProjectV2ParentSubTicketMutationCommand,
    policy: (
        GitHubProjectV2ParentSubTicketMutationPolicy | None
    ) = None,
) -> GitHubProjectV2ParentSubTicketMutationPlan:
    """Build a deterministic plan without executing a remote mutation."""

    active_policy = (
        policy or GitHubProjectV2ParentSubTicketMutationPolicy()
    )
    history = command.history
    issues = _validate_history(history, active_policy)
    issues.extend(
        _validate_refs(
            "source_artifact_refs",
            command.source_artifact_refs,
            active_policy.max_source_artifact_refs,
        )
    )
    issues.extend(
        _validate_refs(
            "decision_refs",
            command.decision_refs,
            active_policy.max_decision_refs,
        )
    )

    repository = _history_repository(history)
    root_issue_ref = history.root_issue_ref
    latest_entry = (
        history.entries[-1] if history.entries else None
    )
    previous_cycle_ref = (
        latest_entry.cycle_ref if latest_entry else ""
    )
    next_cycle_ordinal = (
        latest_entry.cycle_ordinal + 1
        if latest_entry is not None
        else 0
    )

    title = _bounded_text(
        command.next_cycle_title,
        active_policy.max_title_chars,
    )
    summary = _bounded_text(
        command.next_cycle_summary,
        active_policy.max_summary_chars,
    )
    if title != command.next_cycle_title.strip():
        issues.append("next_cycle_title exceeds policy maximum")
    if summary != command.next_cycle_summary.strip():
        issues.append("next_cycle_summary exceeds policy maximum")

    if len(command.existing_issues) > active_policy.max_existing_issues:
        issues.append("existing issue count exceeds policy maximum")

    snapshot_issues = _validate_issue_snapshots(
        command.existing_issues,
        repository,
    )
    issues.extend(snapshot_issues)

    marker = ""
    body = ""
    planned_issue_ref = ""
    if (
        repository
        and root_issue_ref
        and previous_cycle_ref
        and next_cycle_ordinal > 0
    ):
        marker = _build_marker(
            repository=repository,
            root_issue_ref=root_issue_ref,
            history_ref=history.history_ref,
            previous_cycle_ref=previous_cycle_ref,
            next_cycle_ordinal=next_cycle_ordinal,
        )
        planned_issue_ref = (
            "github-planned-issue:"
            + marker.rsplit(":", 1)[-1]
        )
        body = _render_body(
            marker=marker,
            summary=summary,
            history=history,
            latest_entry=latest_entry,
            source_artifact_refs=command.source_artifact_refs,
            decision_refs=command.decision_refs,
        )

    if issues:
        return _build_plan(
            valid=False,
            action="blocked",
            issues=tuple(dict.fromkeys(issues)),
            command=command,
            repository=repository,
            root_issue_ref=root_issue_ref,
            previous_cycle_ref=previous_cycle_ref,
            next_cycle_ordinal=next_cycle_ordinal,
            marker=marker,
            title=title,
            body=body,
            planned_issue_ref=planned_issue_ref,
            existing_issue_ref="",
            operations=(),
        )

    root_matches = tuple(
        snapshot
        for snapshot in command.existing_issues
        if snapshot.issue_ref == root_issue_ref
    )
    if not root_matches:
        if active_policy.require_root_issue_snapshot:
            return _build_plan(
                valid=False,
                action="blocked",
                issues=("root issue snapshot is required",),
                command=command,
                repository=repository,
                root_issue_ref=root_issue_ref,
                previous_cycle_ref=previous_cycle_ref,
                next_cycle_ordinal=next_cycle_ordinal,
                marker=marker,
                title=title,
                body=body,
                planned_issue_ref=planned_issue_ref,
                existing_issue_ref="",
                operations=(),
            )
        root_snapshot = None
    elif len(root_matches) > 1:
        return _build_plan(
            valid=False,
            action="collision",
            issues=("multiple root issue snapshots found",),
            command=command,
            repository=repository,
            root_issue_ref=root_issue_ref,
            previous_cycle_ref=previous_cycle_ref,
            next_cycle_ordinal=next_cycle_ordinal,
            marker=marker,
            title=title,
            body=body,
            planned_issue_ref=planned_issue_ref,
            existing_issue_ref="",
            operations=(),
        )
    else:
        root_snapshot = root_matches[0]

    marker_matches = tuple(
        snapshot
        for snapshot in command.existing_issues
        if marker in snapshot.body
    )
    if len(marker_matches) > 1:
        return _build_plan(
            valid=False,
            action="collision",
            issues=("multiple issues carry the same cycle marker",),
            command=command,
            repository=repository,
            root_issue_ref=root_issue_ref,
            previous_cycle_ref=previous_cycle_ref,
            next_cycle_ordinal=next_cycle_ordinal,
            marker=marker,
            title=title,
            body=body,
            planned_issue_ref=planned_issue_ref,
            existing_issue_ref="",
            operations=(),
        )

    if not marker_matches:
        operations = _create_and_link_operations(
            repository=repository,
            root_issue_ref=root_issue_ref,
            planned_issue_ref=planned_issue_ref,
            title=title,
            body=body,
        )
        return _build_plan(
            valid=True,
            action="create_and_link",
            issues=(),
            command=command,
            repository=repository,
            root_issue_ref=root_issue_ref,
            previous_cycle_ref=previous_cycle_ref,
            next_cycle_ordinal=next_cycle_ordinal,
            marker=marker,
            title=title,
            body=body,
            planned_issue_ref=planned_issue_ref,
            existing_issue_ref="",
            operations=operations,
        )

    existing = marker_matches[0]
    if existing.body != body:
        return _build_plan(
            valid=False,
            action="collision",
            issues=(
                "existing marked issue differs from approved cycle body",
            ),
            command=command,
            repository=repository,
            root_issue_ref=root_issue_ref,
            previous_cycle_ref=previous_cycle_ref,
            next_cycle_ordinal=next_cycle_ordinal,
            marker=marker,
            title=title,
            body=body,
            planned_issue_ref=planned_issue_ref,
            existing_issue_ref=existing.issue_ref,
            operations=(),
        )
    if existing.title != title:
        return _build_plan(
            valid=False,
            action="collision",
            issues=(
                "existing marked issue title differs from approved title",
            ),
            command=command,
            repository=repository,
            root_issue_ref=root_issue_ref,
            previous_cycle_ref=previous_cycle_ref,
            next_cycle_ordinal=next_cycle_ordinal,
            marker=marker,
            title=title,
            body=body,
            planned_issue_ref=planned_issue_ref,
            existing_issue_ref=existing.issue_ref,
            operations=(),
        )
    if (
        active_policy.require_open_existing_issue
        and existing.state != "OPEN"
    ):
        return _build_plan(
            valid=False,
            action="collision",
            issues=("existing marked issue is not open",),
            command=command,
            repository=repository,
            root_issue_ref=root_issue_ref,
            previous_cycle_ref=previous_cycle_ref,
            next_cycle_ordinal=next_cycle_ordinal,
            marker=marker,
            title=title,
            body=body,
            planned_issue_ref=planned_issue_ref,
            existing_issue_ref=existing.issue_ref,
            operations=(),
        )

    parent_claims_link = (
        existing.parent_issue_ref == root_issue_ref
    )
    root_claims_link = bool(
        root_snapshot
        and existing.issue_ref in root_snapshot.sub_issue_refs
    )

    if (
        existing.parent_issue_ref
        and existing.parent_issue_ref != root_issue_ref
    ):
        return _build_plan(
            valid=False,
            action="collision",
            issues=(
                "existing marked issue belongs to another parent",
            ),
            command=command,
            repository=repository,
            root_issue_ref=root_issue_ref,
            previous_cycle_ref=previous_cycle_ref,
            next_cycle_ordinal=next_cycle_ordinal,
            marker=marker,
            title=title,
            body=body,
            planned_issue_ref=planned_issue_ref,
            existing_issue_ref=existing.issue_ref,
            operations=(),
        )

    if parent_claims_link != root_claims_link:
        return _build_plan(
            valid=False,
            action="collision",
            issues=(
                "parent and sub-issue snapshots disagree",
            ),
            command=command,
            repository=repository,
            root_issue_ref=root_issue_ref,
            previous_cycle_ref=previous_cycle_ref,
            next_cycle_ordinal=next_cycle_ordinal,
            marker=marker,
            title=title,
            body=body,
            planned_issue_ref=planned_issue_ref,
            existing_issue_ref=existing.issue_ref,
            operations=(),
        )

    if parent_claims_link and root_claims_link:
        return _build_plan(
            valid=True,
            action="replay",
            issues=(),
            command=command,
            repository=repository,
            root_issue_ref=root_issue_ref,
            previous_cycle_ref=previous_cycle_ref,
            next_cycle_ordinal=next_cycle_ordinal,
            marker=marker,
            title=title,
            body=body,
            planned_issue_ref=planned_issue_ref,
            existing_issue_ref=existing.issue_ref,
            operations=(),
        )

    if not active_policy.allow_link_existing:
        return _build_plan(
            valid=False,
            action="blocked",
            issues=("linking an existing issue is forbidden by policy",),
            command=command,
            repository=repository,
            root_issue_ref=root_issue_ref,
            previous_cycle_ref=previous_cycle_ref,
            next_cycle_ordinal=next_cycle_ordinal,
            marker=marker,
            title=title,
            body=body,
            planned_issue_ref=planned_issue_ref,
            existing_issue_ref=existing.issue_ref,
            operations=(),
        )

    link_operation = _link_existing_operation(
        repository=repository,
        root_issue_ref=root_issue_ref,
        existing_issue_ref=existing.issue_ref,
    )
    return _build_plan(
        valid=True,
        action="link_existing",
        issues=(),
        command=command,
        repository=repository,
        root_issue_ref=root_issue_ref,
        previous_cycle_ref=previous_cycle_ref,
        next_cycle_ordinal=next_cycle_ordinal,
        marker=marker,
        title=title,
        body=body,
        planned_issue_ref=planned_issue_ref,
        existing_issue_ref=existing.issue_ref,
        operations=(link_operation,),
    )


def _validate_history(
    history: GitHubProjectV2AppendOnlyCycleHistoryResult,
    policy: GitHubProjectV2ParentSubTicketMutationPolicy,
) -> list[str]:
    issues: list[str] = []
    if policy.require_valid_history and not history.valid:
        issues.append("cycle history must be valid")
    if not history.history_ref.startswith(
        "github-project-v2-cycle-history:"
    ):
        issues.append("history_ref is required")
    if not history.entries:
        issues.append("cycle history must contain at least one entry")
        return issues
    if not history.root_issue_ref:
        issues.append("root_issue_ref is required")
    if (
        policy.require_latest_cycle
        and history.action not in {"append", "replay"}
    ):
        issues.append(
            "cycle history action must be append or replay"
        )
    latest = history.entries[-1]
    if latest.root_issue_ref != history.root_issue_ref:
        issues.append(
            "latest entry root_issue_ref mismatch"
        )
    if not latest.cycle_ref:
        issues.append("latest cycle_ref is required")
    if latest.cycle_ordinal <= 0:
        issues.append("latest cycle_ordinal must be positive")
    return issues


def _validate_issue_snapshots(
    snapshots: Sequence[GitHubProjectV2IssueSnapshot],
    repository: str,
) -> list[str]:
    issues: list[str] = []
    seen: set[str] = set()
    for snapshot in snapshots:
        snapshot_repository, _ = _parse_issue_ref(
            snapshot.issue_ref
        )
        if snapshot_repository != repository:
            issues.append(
                "existing issue snapshot repository mismatch"
            )
        if snapshot.issue_ref in seen:
            issues.append("duplicate existing issue snapshot")
        seen.add(snapshot.issue_ref)
    return issues


def _create_and_link_operations(
    *,
    repository: str,
    root_issue_ref: str,
    planned_issue_ref: str,
    title: str,
    body: str,
) -> tuple[GitHubProjectV2ParentSubTicketMutationOperation, ...]:
    create_ref = _operation_ref(
        "create_issue",
        repository,
        planned_issue_ref,
        root_issue_ref,
    )
    link_ref = _operation_ref(
        "add_sub_issue",
        repository,
        root_issue_ref,
        planned_issue_ref,
    )
    return (
        GitHubProjectV2ParentSubTicketMutationOperation(
            operation_ref=create_ref,
            kind="create_issue",
            repository=repository,
            target_ref=planned_issue_ref,
            title=title,
            body=body,
            preconditions=(
                "no existing issue carries the cycle marker",
                "operator authorization remains required",
            ),
        ),
        GitHubProjectV2ParentSubTicketMutationOperation(
            operation_ref=link_ref,
            kind="add_sub_issue",
            repository=repository,
            target_ref=root_issue_ref,
            parent_issue_ref=root_issue_ref,
            child_issue_ref=planned_issue_ref,
            depends_on=(create_ref,),
            preconditions=(
                "created issue identity must replace planned_issue_ref",
                "root and child snapshots must be refreshed after mutation",
            ),
        ),
    )


def _link_existing_operation(
    *,
    repository: str,
    root_issue_ref: str,
    existing_issue_ref: str,
) -> GitHubProjectV2ParentSubTicketMutationOperation:
    return GitHubProjectV2ParentSubTicketMutationOperation(
        operation_ref=_operation_ref(
            "add_sub_issue",
            repository,
            root_issue_ref,
            existing_issue_ref,
        ),
        kind="add_sub_issue",
        repository=repository,
        target_ref=root_issue_ref,
        parent_issue_ref=root_issue_ref,
        child_issue_ref=existing_issue_ref,
        preconditions=(
            "existing issue body and title match the approved plan",
            "existing issue has no other parent",
            "root and child snapshots must be refreshed after mutation",
        ),
    )


def _build_plan(
    *,
    valid: bool,
    action: str,
    issues: tuple[str, ...],
    command: GitHubProjectV2ParentSubTicketMutationCommand,
    repository: str,
    root_issue_ref: str,
    previous_cycle_ref: str,
    next_cycle_ordinal: int,
    marker: str,
    title: str,
    body: str,
    planned_issue_ref: str,
    existing_issue_ref: str,
    operations: tuple[
        GitHubProjectV2ParentSubTicketMutationOperation,
        ...,
    ],
) -> GitHubProjectV2ParentSubTicketMutationPlan:
    payload = {
        "repository": repository,
        "root_issue_ref": root_issue_ref,
        "previous_cycle_ref": previous_cycle_ref,
        "next_cycle_ordinal": next_cycle_ordinal,
        "marker": marker,
        "title": title,
        "body_sha256": _sha256_text(body) if body else "",
        "planned_issue_ref": planned_issue_ref,
        "existing_issue_ref": existing_issue_ref,
        "action": action,
        "issues": list(issues),
        "operations": [
            operation.to_json_dict()
            for operation in operations
        ],
        "policy_decision_id": command.policy_decision_id,
        "operator_decision": command.operator_decision,
    }
    digest = _digest_json(payload)
    return GitHubProjectV2ParentSubTicketMutationPlan(
        valid=valid,
        action=action,
        issues=issues,
        plan_ref=(
            f"github-project-v2-parent-sub-ticket-plan:{digest[:16]}"
            if valid
            else ""
        ),
        plan_digest=digest,
        repository=repository,
        root_issue_ref=root_issue_ref,
        previous_cycle_ref=previous_cycle_ref,
        next_cycle_ordinal=next_cycle_ordinal,
        marker=marker,
        title=title,
        body=body,
        planned_issue_ref=planned_issue_ref,
        existing_issue_ref=existing_issue_ref,
        operations=operations,
        boundaries=_boundaries(),
    )


def _render_body(
    *,
    marker: str,
    summary: str,
    history: GitHubProjectV2AppendOnlyCycleHistoryResult,
    latest_entry: GitHubProjectV2CycleHistoryEntry | None,
    source_artifact_refs: Sequence[str],
    decision_refs: Sequence[str],
) -> str:
    if latest_entry is None:
        return ""
    theme_lines = (
        "\n".join(
            f"- {value}"
            for value in latest_entry.theme_values
        )
        or "- Aucun thème"
    )
    source_lines = (
        "\n".join(f"- `{ref}`" for ref in source_artifact_refs)
        or "- Aucun artefact supplémentaire"
    )
    decision_lines = (
        "\n".join(f"- `{ref}`" for ref in decision_refs)
        or "- Aucune décision supplémentaire"
    )
    return "\n".join(
        (
            f"<!-- {marker} -->",
            "",
            f"# Cycle Autodoc {latest_entry.cycle_ordinal + 1}",
            "",
            summary,
            "",
            "## Filiation",
            "",
            f"- Ticket racine : `{history.root_issue_ref}`",
            f"- Cycle précédent : `{latest_entry.cycle_ref}`",
            f"- Historique : `{history.history_ref}`",
            f"- Entrée précédente : `{latest_entry.entry_ref}`",
            "",
            "## Thèmes hérités",
            "",
            theme_lines,
            "",
            "## Artefacts sources",
            "",
            source_lines,
            "",
            "## Décisions",
            "",
            decision_lines,
            "",
            "> Ce ticket est un cycle dérivé. "
            "L’historique local append-only reste l’autorité.",
            "",
        )
    )


def _build_marker(
    *,
    repository: str,
    root_issue_ref: str,
    history_ref: str,
    previous_cycle_ref: str,
    next_cycle_ordinal: int,
) -> str:
    digest = hashlib.sha256(
        "\0".join(
            (
                repository,
                root_issue_ref,
                history_ref,
                previous_cycle_ref,
                str(next_cycle_ordinal),
            )
        ).encode("utf-8")
    ).hexdigest()[:24]
    return f"{MARKER_PREFIX}:{digest}"


def _operation_ref(kind: str, *parts: str) -> str:
    digest = hashlib.sha256(
        "\0".join((kind, *parts)).encode("utf-8")
    ).hexdigest()[:16]
    return f"github-project-v2-operation:{digest}"


def _history_repository(
    history: GitHubProjectV2AppendOnlyCycleHistoryResult,
) -> str:
    return history.entries[-1].repository if history.entries else ""


def _parse_issue_ref(value: str) -> tuple[str, int]:
    match = _ISSUE_REF_RE.fullmatch(value.strip())
    if match is None:
        raise ValueError(
            "issue_ref must use github-frame:<owner>/<repo>/issues/<number>"
        )
    return (
        match.group("repository"),
        int(match.group("number")),
    )


def _validate_refs(
    label: str,
    refs: Sequence[str],
    maximum: int,
) -> list[str]:
    normalized = tuple(ref.strip() for ref in refs)
    issues: list[str] = []
    if any(not ref for ref in normalized):
        issues.append(f"{label} must not contain empty references")
    if len(normalized) != len(set(normalized)):
        issues.append(f"{label} must be unique")
    if len(normalized) > maximum:
        issues.append(f"{label} exceed policy maximum")
    return issues


def _bounded_text(value: str, maximum: int) -> str:
    normalized = value.strip()
    return normalized[:maximum]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _digest_json(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _boundaries() -> tuple[tuple[str, bool], ...]:
    return (
        ("plan_only", True),
        ("operator_authorization_required", True),
        ("external_call_performed", False),
        ("graphql_query_performed", False),
        ("graphql_mutation_allowed", False),
        ("github_mutation_allowed", False),
        ("github_mutation_performed", False),
        ("filesystem_write_allowed", False),
        ("sql_write_allowed", False),
        ("qdrant_write_allowed", False),
        ("scheduler_modified", False),
        ("projects_repository_change_required", False),
    )
