"""Immutable ProjectV2 cycle-lineage contract for phase 0282-r2.

The contract composes the append-only GitHub ticket references already exposed
by ``github_project_push_frame``. It performs no IO, GraphQL request, GitHub
mutation, persistence write, scheduling or laboratory execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping

from context.github_project_push_frame import build_origin_frame_id


CYCLE_LINEAGE_SCHEMA = "missipy.github.project_v2_cycle_lineage.v1"
CYCLE_LINEAGE_RESULT_SCHEMA = (
    "missipy.github.project_v2_cycle_lineage_result.v1"
)

_REPOSITORY_RE = re.compile(
    r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$"
)
_CYCLE_REF_PREFIX = "github-project-v2-cycle:"
_ITEM_REF_PREFIX = "github-project-v2-item:"
_THEME_REF_PREFIX = "github-project-v2-theme:"
_REVISION_REF_PREFIX = "github-ticket-revision:"


@dataclass(frozen=True, slots=True)
class GitHubProjectV2CycleLineageCommand:
    repository: str
    project_id: str
    project_item_ref: str
    root_issue_ref: str
    cycle_ordinal: int
    status_revision_ref: str
    parent_issue_ref: str = ""
    previous_cycle_ref: str = ""
    sub_issue_refs: tuple[str, ...] = ()
    theme_refs: tuple[str, ...] = ()
    result_issue_ref: str = ""
    metadata: tuple[tuple[str, str], ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": CYCLE_LINEAGE_SCHEMA,
            "repository": self.repository,
            "project_id": self.project_id,
            "project_item_ref": self.project_item_ref,
            "cycle_ordinal": self.cycle_ordinal,
            "root_issue_ref": self.root_issue_ref,
            "parent_issue_ref": self.parent_issue_ref,
            "previous_cycle_ref": self.previous_cycle_ref,
            "status_revision_ref": self.status_revision_ref,
            "sub_issue_refs": list(self.sub_issue_refs),
            "theme_refs": list(self.theme_refs),
            "result_issue_ref": self.result_issue_ref,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class GitHubProjectV2CycleLineagePolicy:
    require_parent_after_initial: bool = True
    require_previous_cycle_after_initial: bool = True
    allow_parent_on_initial_cycle: bool = False
    max_cycle_ordinal: int = 10_000
    max_sub_issue_refs: int = 64
    max_theme_refs: int = 16

    def __post_init__(self) -> None:
        if self.max_cycle_ordinal <= 0:
            raise ValueError("max_cycle_ordinal must be > 0")
        if self.max_sub_issue_refs < 0:
            raise ValueError("max_sub_issue_refs must be >= 0")
        if self.max_theme_refs < 0:
            raise ValueError("max_theme_refs must be >= 0")


@dataclass(frozen=True, slots=True)
class GitHubProjectV2CycleLineageResult:
    valid: bool
    issues: tuple[str, ...]
    cycle_ref: str
    lineage_digest: str
    repository: str
    project_id: str
    project_item_ref: str
    cycle_ordinal: int
    root_issue_ref: str
    parent_issue_ref: str
    previous_cycle_ref: str
    status_revision_ref: str
    sub_issue_refs: tuple[str, ...]
    theme_refs: tuple[str, ...]
    result_issue_ref: str
    metadata: tuple[tuple[str, str], ...]
    boundaries: tuple[tuple[str, bool], ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": CYCLE_LINEAGE_RESULT_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "cycle_ref": self.cycle_ref,
            "lineage_digest": self.lineage_digest,
            "repository": self.repository,
            "project_id": self.project_id,
            "project_item_ref": self.project_item_ref,
            "cycle_ordinal": self.cycle_ordinal,
            "root_issue_ref": self.root_issue_ref,
            "parent_issue_ref": self.parent_issue_ref,
            "previous_cycle_ref": self.previous_cycle_ref,
            "status_revision_ref": self.status_revision_ref,
            "sub_issue_refs": list(self.sub_issue_refs),
            "theme_refs": list(self.theme_refs),
            "result_issue_ref": self.result_issue_ref,
            "metadata": dict(self.metadata),
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"github_project_v2_cycle_lineage_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"cycle_ref={self.cycle_ref or '-'}",
                f"cycle_ordinal={self.cycle_ordinal}",
                f"themes={len(self.theme_refs)}",
                f"sub_issues={len(self.sub_issue_refs)}",
                "external_call_performed=False",
                "remote_mutation_allowed=False",
            )
        )


def build_github_project_v2_issue_ref(
    repository: str,
    issue_number: int,
) -> str:
    if not _REPOSITORY_RE.fullmatch(repository.strip()):
        raise ValueError("repository must use owner/name form")
    if issue_number <= 0:
        raise ValueError("issue_number must be > 0")
    return build_origin_frame_id(repository.strip(), issue_number)


def build_github_project_v2_item_ref(item_id: str) -> str:
    normalized = item_id.strip()
    if not normalized:
        raise ValueError("item_id is required")
    return f"{_ITEM_REF_PREFIX}{normalized}"


def build_github_project_v2_theme_ref(
    project_id: str,
    field_id: str,
    option_ref: str,
) -> str:
    values = tuple(
        value.strip()
        for value in (project_id, field_id, option_ref)
    )
    if not all(values):
        raise ValueError(
            "project_id, field_id and option_ref are required"
        )
    digest = hashlib.sha256(
        "\0".join(values).encode("utf-8")
    ).hexdigest()[:16]
    return f"{_THEME_REF_PREFIX}{digest}"


def build_github_project_v2_cycle_lineage(
    command: GitHubProjectV2CycleLineageCommand,
    policy: GitHubProjectV2CycleLineagePolicy | None = None,
) -> GitHubProjectV2CycleLineageResult:
    active_policy = policy or GitHubProjectV2CycleLineagePolicy()
    normalized = _normalize_command(command)
    issues = _validate_command(normalized, active_policy)
    digest = _lineage_digest(normalized)
    cycle_ref = f"{_CYCLE_REF_PREFIX}{digest[:16]}" if not issues else ""

    return GitHubProjectV2CycleLineageResult(
        valid=not issues,
        issues=tuple(issues),
        cycle_ref=cycle_ref,
        lineage_digest=digest,
        repository=normalized.repository,
        project_id=normalized.project_id,
        project_item_ref=normalized.project_item_ref,
        cycle_ordinal=normalized.cycle_ordinal,
        root_issue_ref=normalized.root_issue_ref,
        parent_issue_ref=normalized.parent_issue_ref,
        previous_cycle_ref=normalized.previous_cycle_ref,
        status_revision_ref=normalized.status_revision_ref,
        sub_issue_refs=normalized.sub_issue_refs,
        theme_refs=normalized.theme_refs,
        result_issue_ref=normalized.result_issue_ref,
        metadata=normalized.metadata,
        boundaries=_boundaries(),
    )


def _normalize_command(
    command: GitHubProjectV2CycleLineageCommand,
) -> GitHubProjectV2CycleLineageCommand:
    return GitHubProjectV2CycleLineageCommand(
        repository=command.repository.strip(),
        project_id=command.project_id.strip(),
        project_item_ref=command.project_item_ref.strip(),
        root_issue_ref=command.root_issue_ref.strip(),
        cycle_ordinal=command.cycle_ordinal,
        status_revision_ref=command.status_revision_ref.strip(),
        parent_issue_ref=command.parent_issue_ref.strip(),
        previous_cycle_ref=command.previous_cycle_ref.strip(),
        sub_issue_refs=tuple(
            sorted(ref.strip() for ref in command.sub_issue_refs)
        ),
        theme_refs=tuple(
            sorted(ref.strip() for ref in command.theme_refs)
        ),
        result_issue_ref=command.result_issue_ref.strip(),
        metadata=tuple(
            sorted(
                (str(key).strip(), str(value))
                for key, value in command.metadata
            )
        ),
    )


def _validate_command(
    command: GitHubProjectV2CycleLineageCommand,
    policy: GitHubProjectV2CycleLineagePolicy,
) -> list[str]:
    issues: list[str] = []

    if not _REPOSITORY_RE.fullmatch(command.repository):
        issues.append("repository must use owner/name form")
    if not command.project_id.startswith("PVT_"):
        issues.append("project_id must start with PVT_")
    if not command.project_item_ref.startswith(_ITEM_REF_PREFIX):
        issues.append(
            "project_item_ref must use github-project-v2-item prefix"
        )
    if command.cycle_ordinal <= 0:
        issues.append("cycle_ordinal must be > 0")
    if command.cycle_ordinal > policy.max_cycle_ordinal:
        issues.append("cycle_ordinal exceeds policy maximum")
    if not command.status_revision_ref.startswith(
        _REVISION_REF_PREFIX
    ):
        issues.append(
            "status_revision_ref must use github-ticket-revision prefix"
        )

    for label, issue_ref in (
        ("root_issue_ref", command.root_issue_ref),
        ("parent_issue_ref", command.parent_issue_ref),
        ("result_issue_ref", command.result_issue_ref),
    ):
        if issue_ref and not _valid_issue_ref(
            issue_ref,
            command.repository,
        ):
            issues.append(
                f"{label} must reference an issue in repository"
            )

    if not command.root_issue_ref:
        issues.append("root_issue_ref is required")

    for issue_ref in command.sub_issue_refs:
        if not _valid_issue_ref(issue_ref, command.repository):
            issues.append(
                "sub_issue_refs must reference issues in repository"
            )
            break

    if len(command.sub_issue_refs) != len(
        set(command.sub_issue_refs)
    ):
        issues.append("sub_issue_refs must be unique")
    if len(command.theme_refs) != len(set(command.theme_refs)):
        issues.append("theme_refs must be unique")
    if len(command.sub_issue_refs) > policy.max_sub_issue_refs:
        issues.append("sub_issue_refs exceed policy maximum")
    if len(command.theme_refs) > policy.max_theme_refs:
        issues.append("theme_refs exceed policy maximum")
    if command.root_issue_ref in command.sub_issue_refs:
        issues.append("root_issue_ref must not be a sub_issue_ref")
    if (
        command.parent_issue_ref
        and command.parent_issue_ref in command.sub_issue_refs
    ):
        issues.append("parent_issue_ref must not be a sub_issue_ref")

    for theme_ref in command.theme_refs:
        if not theme_ref.startswith(_THEME_REF_PREFIX):
            issues.append(
                "theme_refs must use github-project-v2-theme prefix"
            )
            break

    metadata_keys = tuple(key for key, _ in command.metadata)
    if not all(metadata_keys):
        issues.append("metadata keys must be non-empty")
    if len(metadata_keys) != len(set(metadata_keys)):
        issues.append("metadata keys must be unique")

    if command.cycle_ordinal == 1:
        if command.previous_cycle_ref:
            issues.append(
                "initial cycle must not reference previous_cycle_ref"
            )
        if (
            command.parent_issue_ref
            and not policy.allow_parent_on_initial_cycle
        ):
            issues.append(
                "initial cycle must not reference parent_issue_ref"
            )
    else:
        if (
            policy.require_previous_cycle_after_initial
            and not command.previous_cycle_ref
        ):
            issues.append(
                "previous_cycle_ref is required after initial cycle"
            )
        if (
            policy.require_parent_after_initial
            and not command.parent_issue_ref
        ):
            issues.append(
                "parent_issue_ref is required after initial cycle"
            )

    if (
        command.previous_cycle_ref
        and not command.previous_cycle_ref.startswith(
            _CYCLE_REF_PREFIX
        )
    ):
        issues.append(
            "previous_cycle_ref must use github-project-v2-cycle prefix"
        )

    return issues


def _valid_issue_ref(issue_ref: str, repository: str) -> bool:
    prefix = f"github-frame:{repository}/issues/"
    if not issue_ref.startswith(prefix):
        return False
    number = issue_ref[len(prefix):]
    return number.isdigit() and int(number) > 0


def _lineage_digest(
    command: GitHubProjectV2CycleLineageCommand,
) -> str:
    payload = command.to_json_dict()
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _boundaries() -> tuple[tuple[str, bool], ...]:
    return (
        ("contract_only", True),
        ("external_call_performed", False),
        ("graphql_query_performed", False),
        ("graphql_mutation_allowed", False),
        ("remote_mutation_allowed", False),
        ("sql_write_allowed", False),
        ("qdrant_write_allowed", False),
        ("scheduler_modified", False),
        ("projects_repository_change_required", False),
    )
