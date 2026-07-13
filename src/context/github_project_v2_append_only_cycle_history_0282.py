"""Append-only ProjectV2 cycle-history projection for phase 0282-r4.

The projection composes the immutable lineage result from 0282-r2 with the
query-only parent/theme normalization item from 0282-r3. It performs no IO,
GraphQL request, GitHub mutation, persistence write, scheduling or laboratory
execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Sequence

from context.github_project_v2_cycle_lineage_0282 import (
    GitHubProjectV2CycleLineageResult,
)
from context.github_project_v2_parent_theme_query_normalization_0282 import (
    GitHubProjectV2NormalizedParentThemeItem,
)


CYCLE_HISTORY_ENTRY_SCHEMA = (
    "missipy.github.project_v2_cycle_history_entry.v1"
)
CYCLE_HISTORY_RESULT_SCHEMA = (
    "missipy.github.project_v2_cycle_history_projection.v1"
)
_HISTORY_REF_PREFIX = "github-project-v2-cycle-history:"
_ENTRY_REF_PREFIX = "github-project-v2-cycle-history-entry:"


@dataclass(frozen=True, slots=True)
class GitHubProjectV2CycleHistoryEntry:
    entry_ref: str
    entry_digest: str
    cycle_ref: str
    lineage_digest: str
    cycle_ordinal: int
    repository: str
    project_id: str
    project_item_ref: str
    issue_ref: str
    root_issue_ref: str
    parent_issue_ref: str
    previous_cycle_ref: str
    status_revision_ref: str
    status_name: str
    sub_issue_refs: tuple[str, ...]
    theme_refs: tuple[str, ...]
    theme_values: tuple[str, ...]
    result_issue_ref: str
    source_artifact_refs: tuple[str, ...]
    decision_refs: tuple[str, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": CYCLE_HISTORY_ENTRY_SCHEMA,
            "entry_ref": self.entry_ref,
            "entry_digest": self.entry_digest,
            "cycle_ref": self.cycle_ref,
            "lineage_digest": self.lineage_digest,
            "cycle_ordinal": self.cycle_ordinal,
            "repository": self.repository,
            "project_id": self.project_id,
            "project_item_ref": self.project_item_ref,
            "issue_ref": self.issue_ref,
            "root_issue_ref": self.root_issue_ref,
            "parent_issue_ref": self.parent_issue_ref,
            "previous_cycle_ref": self.previous_cycle_ref,
            "status_revision_ref": self.status_revision_ref,
            "status_name": self.status_name,
            "sub_issue_refs": list(self.sub_issue_refs),
            "theme_refs": list(self.theme_refs),
            "theme_values": list(self.theme_values),
            "result_issue_ref": self.result_issue_ref,
            "source_artifact_refs": list(self.source_artifact_refs),
            "decision_refs": list(self.decision_refs),
        }


@dataclass(frozen=True, slots=True)
class GitHubProjectV2AppendOnlyCycleHistoryCommand:
    lineage: GitHubProjectV2CycleLineageResult
    normalized_item: GitHubProjectV2NormalizedParentThemeItem
    existing_entries: tuple[GitHubProjectV2CycleHistoryEntry, ...] = ()
    source_artifact_refs: tuple[str, ...] = ()
    decision_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GitHubProjectV2AppendOnlyCycleHistoryPolicy:
    require_valid_lineage: bool = True
    require_project_item_match: bool = True
    require_status_revision_match: bool = True
    require_parent_match: bool = True
    require_sub_issue_match: bool = True
    require_theme_match: bool = True
    require_contiguous_ordinals: bool = True
    allow_identical_replay: bool = True
    max_entries: int = 10_000
    max_source_artifact_refs: int = 128
    max_decision_refs: int = 64

    def __post_init__(self) -> None:
        if self.max_entries <= 0:
            raise ValueError("max_entries must be > 0")
        if self.max_source_artifact_refs < 0:
            raise ValueError(
                "max_source_artifact_refs must be >= 0"
            )
        if self.max_decision_refs < 0:
            raise ValueError("max_decision_refs must be >= 0")


@dataclass(frozen=True, slots=True)
class GitHubProjectV2AppendOnlyCycleHistoryResult:
    valid: bool
    action: str
    issues: tuple[str, ...]
    history_ref: str
    history_digest: str
    appended_entry_ref: str
    root_issue_ref: str
    entries: tuple[GitHubProjectV2CycleHistoryEntry, ...]
    boundaries: tuple[tuple[str, bool], ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": CYCLE_HISTORY_RESULT_SCHEMA,
            "valid": self.valid,
            "action": self.action,
            "issues": list(self.issues),
            "history_ref": self.history_ref,
            "history_digest": self.history_digest,
            "appended_entry_ref": self.appended_entry_ref,
            "root_issue_ref": self.root_issue_ref,
            "entries": [entry.to_json_dict() for entry in self.entries],
            "counts": {"entry_count": len(self.entries)},
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"project_v2_cycle_history_valid={self.valid}",
                f"action={self.action}",
                f"issues={len(self.issues)}",
                f"entries={len(self.entries)}",
                f"history_ref={self.history_ref or '-'}",
                "append_only=True",
                "external_call_performed=False",
                "remote_mutation_allowed=False",
            )
        )


def project_github_project_v2_append_only_cycle_history(
    command: GitHubProjectV2AppendOnlyCycleHistoryCommand,
    policy: GitHubProjectV2AppendOnlyCycleHistoryPolicy | None = None,
) -> GitHubProjectV2AppendOnlyCycleHistoryResult:
    active_policy = (
        policy or GitHubProjectV2AppendOnlyCycleHistoryPolicy()
    )
    existing_entries = tuple(command.existing_entries)
    issues = _validate_existing_entries(
        existing_entries,
        active_policy,
    )
    issues.extend(
        _validate_candidate_inputs(
            command,
            active_policy,
        )
    )

    candidate = _build_entry(
        command.lineage,
        command.normalized_item,
        command.source_artifact_refs,
        command.decision_refs,
    )

    if len(existing_entries) >= active_policy.max_entries:
        issues.append("cycle history entry count exceeds policy maximum")

    same_cycle = tuple(
        entry
        for entry in existing_entries
        if entry.cycle_ref == candidate.cycle_ref
    )
    same_ordinal = tuple(
        entry
        for entry in existing_entries
        if entry.cycle_ordinal == candidate.cycle_ordinal
    )

    if same_cycle:
        if len(same_cycle) != 1:
            issues.append("existing cycle_ref is duplicated")
            action = "collision"
        elif same_cycle[0] == candidate:
            if active_policy.allow_identical_replay:
                action = "replay"
            else:
                issues.append("identical replay is forbidden by policy")
                action = "reject"
        else:
            issues.append("cycle_ref collision with different entry content")
            action = "collision"
    elif same_ordinal:
        issues.append("cycle ordinal collision")
        action = "collision"
    else:
        action = "append"

    if action == "append":
        issues.extend(
            _validate_append_position(
                existing_entries,
                candidate,
                active_policy,
            )
        )

    if issues:
        return _result(
            valid=False,
            action=(
                action
                if action in {"collision", "reject"}
                else "reject"
            ),
            issues=tuple(issues),
            entries=existing_entries,
            appended_entry_ref="",
        )

    if action == "replay":
        return _result(
            valid=True,
            action="replay",
            issues=(),
            entries=existing_entries,
            appended_entry_ref=candidate.entry_ref,
        )

    return _result(
        valid=True,
        action="append",
        issues=(),
        entries=existing_entries + (candidate,),
        appended_entry_ref=candidate.entry_ref,
    )


def _validate_candidate_inputs(
    command: GitHubProjectV2AppendOnlyCycleHistoryCommand,
    policy: GitHubProjectV2AppendOnlyCycleHistoryPolicy,
) -> list[str]:
    lineage = command.lineage
    item = command.normalized_item
    issues: list[str] = []

    if policy.require_valid_lineage and not lineage.valid:
        issues.append("lineage result must be valid")
    if not lineage.cycle_ref:
        issues.append("lineage cycle_ref is required")
    if not lineage.lineage_digest:
        issues.append("lineage_digest is required")

    if (
        policy.require_project_item_match
        and lineage.project_item_ref != item.project_item_ref
    ):
        issues.append("project_item_ref mismatch")
    if (
        policy.require_status_revision_match
        and lineage.status_revision_ref != item.status_revision_ref
    ):
        issues.append("status_revision_ref mismatch")
    if (
        policy.require_parent_match
        and lineage.parent_issue_ref != item.parent_issue_ref
    ):
        issues.append("parent_issue_ref mismatch")
    if (
        policy.require_sub_issue_match
        and tuple(lineage.sub_issue_refs)
        != tuple(item.sub_issue_refs)
    ):
        issues.append("sub_issue_refs mismatch")
    if (
        policy.require_theme_match
        and tuple(lineage.theme_refs) != tuple(item.theme_refs)
    ):
        issues.append("theme_refs mismatch")

    issues.extend(
        _validate_refs(
            "source_artifact_refs",
            command.source_artifact_refs,
            policy.max_source_artifact_refs,
        )
    )
    issues.extend(
        _validate_refs(
            "decision_refs",
            command.decision_refs,
            policy.max_decision_refs,
        )
    )
    return issues


def _validate_existing_entries(
    entries: Sequence[GitHubProjectV2CycleHistoryEntry],
    policy: GitHubProjectV2AppendOnlyCycleHistoryPolicy,
) -> list[str]:
    issues: list[str] = []
    if len(entries) > policy.max_entries:
        issues.append("existing cycle history exceeds policy maximum")
    if not entries:
        return issues

    repository = entries[0].repository
    project_id = entries[0].project_id
    root_issue_ref = entries[0].root_issue_ref
    seen_cycles: set[str] = set()
    seen_ordinals: set[int] = set()

    for position, entry in enumerate(entries):
        if entry.repository != repository:
            issues.append("existing history repository mismatch")
        if entry.project_id != project_id:
            issues.append("existing history project_id mismatch")
        if entry.root_issue_ref != root_issue_ref:
            issues.append("existing history root_issue_ref mismatch")
        if entry.cycle_ref in seen_cycles:
            issues.append("existing history duplicate cycle_ref")
        if entry.cycle_ordinal in seen_ordinals:
            issues.append("existing history duplicate cycle ordinal")
        seen_cycles.add(entry.cycle_ref)
        seen_ordinals.add(entry.cycle_ordinal)

        if entry.entry_digest != _entry_digest(entry, include_ref=False):
            issues.append("existing history entry digest mismatch")

        expected_ordinal = position + 1
        if (
            policy.require_contiguous_ordinals
            and entry.cycle_ordinal != expected_ordinal
        ):
            issues.append("existing history ordinals are not contiguous")

        if position == 0:
            if entry.previous_cycle_ref:
                issues.append(
                    "initial history entry must not have previous_cycle_ref"
                )
        elif entry.previous_cycle_ref != entries[position - 1].cycle_ref:
            issues.append("existing history previous_cycle_ref mismatch")

    return issues


def _validate_append_position(
    entries: Sequence[GitHubProjectV2CycleHistoryEntry],
    candidate: GitHubProjectV2CycleHistoryEntry,
    policy: GitHubProjectV2AppendOnlyCycleHistoryPolicy,
) -> list[str]:
    issues: list[str] = []
    if not entries:
        if candidate.cycle_ordinal != 1:
            issues.append("first history entry must have cycle_ordinal 1")
        if candidate.previous_cycle_ref:
            issues.append(
                "first history entry must not have previous_cycle_ref"
            )
        return issues

    last = entries[-1]
    if candidate.repository != last.repository:
        issues.append("candidate repository differs from history")
    if candidate.project_id != last.project_id:
        issues.append("candidate project_id differs from history")
    if candidate.root_issue_ref != last.root_issue_ref:
        issues.append("candidate root_issue_ref differs from history")
    if candidate.previous_cycle_ref != last.cycle_ref:
        issues.append("candidate previous_cycle_ref must target last cycle")
    if (
        policy.require_contiguous_ordinals
        and candidate.cycle_ordinal != last.cycle_ordinal + 1
    ):
        issues.append("candidate cycle_ordinal is not contiguous")
    return issues


def _build_entry(
    lineage: GitHubProjectV2CycleLineageResult,
    item: GitHubProjectV2NormalizedParentThemeItem,
    source_artifact_refs: Sequence[str],
    decision_refs: Sequence[str],
) -> GitHubProjectV2CycleHistoryEntry:
    base = GitHubProjectV2CycleHistoryEntry(
        entry_ref="",
        entry_digest="",
        cycle_ref=lineage.cycle_ref,
        lineage_digest=lineage.lineage_digest,
        cycle_ordinal=lineage.cycle_ordinal,
        repository=lineage.repository,
        project_id=lineage.project_id,
        project_item_ref=lineage.project_item_ref,
        issue_ref=item.issue_ref,
        root_issue_ref=lineage.root_issue_ref,
        parent_issue_ref=lineage.parent_issue_ref,
        previous_cycle_ref=lineage.previous_cycle_ref,
        status_revision_ref=lineage.status_revision_ref,
        status_name=item.status_name,
        sub_issue_refs=tuple(sorted(lineage.sub_issue_refs)),
        theme_refs=tuple(sorted(lineage.theme_refs)),
        theme_values=tuple(sorted(item.theme_values)),
        result_issue_ref=lineage.result_issue_ref,
        source_artifact_refs=tuple(sorted(source_artifact_refs)),
        decision_refs=tuple(sorted(decision_refs)),
    )
    digest = _entry_digest(base, include_ref=False)
    return GitHubProjectV2CycleHistoryEntry(
        entry_ref=f"{_ENTRY_REF_PREFIX}{digest[:16]}",
        entry_digest=digest,
        cycle_ref=base.cycle_ref,
        lineage_digest=base.lineage_digest,
        cycle_ordinal=base.cycle_ordinal,
        repository=base.repository,
        project_id=base.project_id,
        project_item_ref=base.project_item_ref,
        issue_ref=base.issue_ref,
        root_issue_ref=base.root_issue_ref,
        parent_issue_ref=base.parent_issue_ref,
        previous_cycle_ref=base.previous_cycle_ref,
        status_revision_ref=base.status_revision_ref,
        status_name=base.status_name,
        sub_issue_refs=base.sub_issue_refs,
        theme_refs=base.theme_refs,
        theme_values=base.theme_values,
        result_issue_ref=base.result_issue_ref,
        source_artifact_refs=base.source_artifact_refs,
        decision_refs=base.decision_refs,
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


def _entry_digest(
    entry: GitHubProjectV2CycleHistoryEntry,
    *,
    include_ref: bool,
) -> str:
    payload = entry.to_json_dict()
    payload.pop("schema", None)
    payload.pop("entry_digest", None)
    if not include_ref:
        payload.pop("entry_ref", None)
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _history_digest(
    entries: Sequence[GitHubProjectV2CycleHistoryEntry],
) -> str:
    payload = [entry.to_json_dict() for entry in entries]
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _result(
    *,
    valid: bool,
    action: str,
    issues: tuple[str, ...],
    entries: tuple[GitHubProjectV2CycleHistoryEntry, ...],
    appended_entry_ref: str,
) -> GitHubProjectV2AppendOnlyCycleHistoryResult:
    digest = _history_digest(entries)
    root_issue_ref = entries[0].root_issue_ref if entries else ""
    history_ref = (
        f"{_HISTORY_REF_PREFIX}{digest[:16]}"
        if valid
        else ""
    )
    return GitHubProjectV2AppendOnlyCycleHistoryResult(
        valid=valid,
        action=action,
        issues=issues,
        history_ref=history_ref,
        history_digest=digest,
        appended_entry_ref=appended_entry_ref,
        root_issue_ref=root_issue_ref,
        entries=entries,
        boundaries=_boundaries(),
    )


def _boundaries() -> tuple[tuple[str, bool], ...]:
    return (
        ("append_only_projection", True),
        ("external_call_performed", False),
        ("graphql_query_performed", False),
        ("graphql_mutation_allowed", False),
        ("remote_mutation_allowed", False),
        ("filesystem_write_allowed", False),
        ("sql_write_allowed", False),
        ("qdrant_write_allowed", False),
        ("scheduler_modified", False),
        ("projects_repository_change_required", False),
    )
