"""Pure local change detection for immutable GitHub ProjectV2 snapshots.

The module compares snapshots produced by phase 0272-r3.  It performs no IO,
network access, SQL write, Qdrant write or GitHub mutation.  Filesystem effects
remain in the CLI boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Mapping, Sequence

from context.github_project_v2_query_only_snapshot_0272 import SNAPSHOT_SCHEMA

CHANGE_SET_SCHEMA = "missipy.github.project_v2_snapshot_change_set.v1"
REPORT_SCHEMA = "missipy.github.project_v2_snapshot_change_detection_report.v1"


@dataclass(frozen=True, slots=True)
class GitHubProjectV2SnapshotChangeCommand:
    execute: bool = False
    policy_decision_id: str = ""


@dataclass(frozen=True, slots=True)
class GitHubProjectV2SnapshotChangePlan:
    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    previous_snapshot_path: str
    current_snapshot_path: str
    baseline: bool
    boundaries: Mapping[str, bool]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": REPORT_SCHEMA,
            "kind": "plan",
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "policy_decision_id": self.policy_decision_id,
            "previous_snapshot_path": self.previous_snapshot_path,
            "current_snapshot_path": self.current_snapshot_path,
            "baseline": self.baseline,
            "boundaries": dict(self.boundaries),
        }


@dataclass(frozen=True, slots=True)
class GitHubProjectV2SnapshotChangeResult:
    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    baseline: bool
    previous_snapshot_ref: str
    current_snapshot_ref: str
    change_set_ref: str
    change_set_path: str
    added_count: int
    removed_count: int
    changed_count: int
    unchanged_count: int
    project_changed: bool
    field_definitions_added_count: int
    field_definitions_removed_count: int
    field_definitions_changed_count: int
    status_transition_count: int
    external_call_performed: bool = False
    boundaries: Mapping[str, bool] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": REPORT_SCHEMA,
            "kind": "result",
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "policy_decision_id": self.policy_decision_id,
            "baseline": self.baseline,
            "previous_snapshot_ref": self.previous_snapshot_ref,
            "current_snapshot_ref": self.current_snapshot_ref,
            "change_set_ref": self.change_set_ref,
            "change_set_path": self.change_set_path,
            "counts": {
                "added_count": self.added_count,
                "removed_count": self.removed_count,
                "changed_count": self.changed_count,
                "unchanged_count": self.unchanged_count,
                "field_definitions_added_count": self.field_definitions_added_count,
                "field_definitions_removed_count": self.field_definitions_removed_count,
                "field_definitions_changed_count": self.field_definitions_changed_count,
                "status_transition_count": self.status_transition_count,
            },
            "project_changed": self.project_changed,
            "external_call_performed": self.external_call_performed,
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"github_project_v2_snapshot_change_detection_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"execute={self.execute}",
                f"baseline={self.baseline}",
                f"previous_snapshot_ref={self.previous_snapshot_ref or '-'}",
                f"current_snapshot_ref={self.current_snapshot_ref or '-'}",
                f"change_set_ref={self.change_set_ref or '-'}",
                f"added={self.added_count}",
                f"removed={self.removed_count}",
                f"changed={self.changed_count}",
                f"unchanged={self.unchanged_count}",
                f"status_transitions={self.status_transition_count}",
                "external_call_performed=False",
                "remote_mutation_allowed=False",
            )
        )


def build_snapshot_change_plan(
    command: GitHubProjectV2SnapshotChangeCommand,
    *,
    previous_snapshot_path: str,
    current_snapshot_path: str,
) -> GitHubProjectV2SnapshotChangePlan:
    issues: list[str] = []
    current_path = current_snapshot_path.strip()
    previous_path = previous_snapshot_path.strip()
    if not current_path:
        issues.append("current snapshot path is required")
    if command.execute and not command.policy_decision_id.strip():
        issues.append("policy_decision_id is required for execute mode")
    if previous_path and previous_path == current_path:
        issues.append("previous and current snapshot paths must differ")
    return GitHubProjectV2SnapshotChangePlan(
        valid=not issues,
        issues=tuple(issues),
        execute=command.execute,
        policy_decision_id=command.policy_decision_id,
        previous_snapshot_path=previous_path,
        current_snapshot_path=current_path,
        baseline=not previous_path,
        boundaries=_boundaries(command.execute),
    )


def build_snapshot_change_set(
    *,
    previous_snapshot: Mapping[str, Any] | None,
    current_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    current_issues = validate_project_v2_snapshot(current_snapshot, label="current")
    if current_issues:
        raise ValueError("; ".join(current_issues))
    previous = dict(previous_snapshot or {})
    if previous:
        previous_issues = validate_project_v2_snapshot(previous, label="previous")
        if previous_issues:
            raise ValueError("; ".join(previous_issues))
        _validate_same_project(previous, current_snapshot)

    current_items = _index_by_id(current_snapshot.get("items"), label="current item")
    previous_items = _index_by_id(previous.get("items"), label="previous item") if previous else {}
    current_fields = _index_by_id(current_snapshot.get("fields"), label="current field")
    previous_fields = _index_by_id(previous.get("fields"), label="previous field") if previous else {}

    baseline = not previous
    if baseline:
        added_ids: list[str] = []
        removed_ids: list[str] = []
        changed_ids: list[str] = []
        unchanged_ids = sorted(current_items)
    else:
        added_ids = sorted(set(current_items) - set(previous_items))
        removed_ids = sorted(set(previous_items) - set(current_items))
        common = sorted(set(previous_items) & set(current_items))
        changed_ids = [
            item_id
            for item_id in common
            if _canonical_json(_normalize_item(previous_items[item_id]))
            != _canonical_json(_normalize_item(current_items[item_id]))
        ]
        unchanged_ids = [item_id for item_id in common if item_id not in set(changed_ids)]

    changed_items = [
        _item_change(previous_items[item_id], current_items[item_id])
        for item_id in changed_ids
    ]
    status_transitions = [
        change
        for change in changed_items
        if change["status"]["before"] != change["status"]["after"]
    ]

    field_added_ids = [] if baseline else sorted(set(current_fields) - set(previous_fields))
    field_removed_ids = [] if baseline else sorted(set(previous_fields) - set(current_fields))
    field_common = sorted(set(previous_fields) & set(current_fields)) if not baseline else []
    field_changed_ids = [
        field_id
        for field_id in field_common
        if _canonical_json(previous_fields[field_id]) != _canonical_json(current_fields[field_id])
    ]

    previous_project = _mapping(previous.get("project")) if previous else {}
    current_project = _mapping(current_snapshot.get("project"))
    project_changes = _changed_paths(previous_project, current_project) if previous else []

    payload: dict[str, Any] = {
        "schema": CHANGE_SET_SCHEMA,
        "kind": "github_project_v2_snapshot_change_set",
        "baseline": baseline,
        "project": {
            "id": str(current_project.get("id", "")),
            "owner": str(current_project.get("owner", "")),
            "number": int(current_project.get("number", 0) or 0),
            "title": str(current_project.get("title", "")),
            "url": str(current_project.get("url", "")),
        },
        "previous_snapshot_ref": str(previous.get("snapshot_ref", "")),
        "current_snapshot_ref": str(current_snapshot.get("snapshot_ref", "")),
        "project_changes": project_changes,
        "field_definitions": {
            "added": [_copy_json(current_fields[field_id]) for field_id in field_added_ids],
            "removed": [_copy_json(previous_fields[field_id]) for field_id in field_removed_ids],
            "changed": [
                {
                    "field_id": field_id,
                    "before": _copy_json(previous_fields[field_id]),
                    "after": _copy_json(current_fields[field_id]),
                    "changed_paths": _changed_paths(
                        previous_fields[field_id], current_fields[field_id]
                    ),
                }
                for field_id in field_changed_ids
            ],
        },
        "items": {
            "added": [_item_summary(current_items[item_id]) for item_id in added_ids],
            "removed": [_item_summary(previous_items[item_id]) for item_id in removed_ids],
            "changed": changed_items,
            "unchanged_ids": unchanged_ids,
        },
        "counts": {
            "added_count": len(added_ids),
            "removed_count": len(removed_ids),
            "changed_count": len(changed_ids),
            "unchanged_count": len(unchanged_ids),
            "field_definitions_added_count": len(field_added_ids),
            "field_definitions_removed_count": len(field_removed_ids),
            "field_definitions_changed_count": len(field_changed_ids),
            "status_transition_count": len(status_transitions),
        },
        "boundaries": {
            "local_snapshot_comparison_only": True,
            "external_call_performed": False,
            "graphql_query_performed": False,
            "graphql_mutation_allowed": False,
            "remote_mutation_allowed": False,
            "sql_write_allowed": False,
            "qdrant_write_allowed": False,
            "token_required": False,
            "token_value_serialized": False,
            "github_is_workflow_surface": True,
            "local_authority_preserved": True,
        },
    }
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()[:16]
    payload["change_set_ref"] = f"github-project-v2-change-set:{digest}"
    return payload


def close_snapshot_change_result(
    plan: GitHubProjectV2SnapshotChangePlan,
    *,
    change_set: Mapping[str, Any] | None,
    change_set_path: str,
    errors: Sequence[str] = (),
) -> GitHubProjectV2SnapshotChangeResult:
    issues = list(plan.issues)
    issues.extend(str(error) for error in errors if str(error))
    payload = dict(change_set or {})
    counts = _mapping(payload.get("counts"))
    if plan.execute:
        if not payload:
            issues.append("execute mode must produce a change set")
        if payload and str(payload.get("schema", "")) != CHANGE_SET_SCHEMA:
            issues.append("change set schema mismatch")
        if payload and bool(_mapping(payload.get("boundaries")).get("external_call_performed", True)):
            issues.append("change detection must remain local-only")
    elif payload:
        issues.append("plan-only mode must not contain a change set")
    return GitHubProjectV2SnapshotChangeResult(
        valid=not issues,
        issues=tuple(issues),
        execute=plan.execute,
        policy_decision_id=plan.policy_decision_id,
        baseline=bool(payload.get("baseline", plan.baseline)),
        previous_snapshot_ref=str(payload.get("previous_snapshot_ref", "")),
        current_snapshot_ref=str(payload.get("current_snapshot_ref", "")),
        change_set_ref=str(payload.get("change_set_ref", "")),
        change_set_path=change_set_path,
        added_count=int(counts.get("added_count", 0) or 0),
        removed_count=int(counts.get("removed_count", 0) or 0),
        changed_count=int(counts.get("changed_count", 0) or 0),
        unchanged_count=int(counts.get("unchanged_count", 0) or 0),
        project_changed=bool(payload.get("project_changes", [])),
        field_definitions_added_count=int(
            counts.get("field_definitions_added_count", 0) or 0
        ),
        field_definitions_removed_count=int(
            counts.get("field_definitions_removed_count", 0) or 0
        ),
        field_definitions_changed_count=int(
            counts.get("field_definitions_changed_count", 0) or 0
        ),
        status_transition_count=int(counts.get("status_transition_count", 0) or 0),
        external_call_performed=False,
        boundaries=_boundaries(plan.execute),
    )


def validate_project_v2_snapshot(snapshot: Mapping[str, Any], *, label: str) -> list[str]:
    issues: list[str] = []
    if str(snapshot.get("schema", "")) != SNAPSHOT_SCHEMA:
        issues.append(f"{label} snapshot schema mismatch")
    snapshot_ref = str(snapshot.get("snapshot_ref", ""))
    if not snapshot_ref.startswith("github-project-v2-snapshot:"):
        issues.append(f"{label} snapshot_ref is invalid")
    project = _mapping(snapshot.get("project"))
    if not str(project.get("id", "")).startswith("PVT_"):
        issues.append(f"{label} project id is invalid")
    if int(project.get("number", 0) or 0) <= 0:
        issues.append(f"{label} project number is invalid")
    boundaries = _mapping(snapshot.get("boundaries"))
    if boundaries.get("graphql_mutation_allowed") is not False:
        issues.append(f"{label} snapshot must forbid GraphQL mutation")
    if boundaries.get("remote_mutation_allowed") is not False:
        issues.append(f"{label} snapshot must forbid remote mutation")
    return issues


def _validate_same_project(
    previous: Mapping[str, Any], current: Mapping[str, Any]
) -> None:
    previous_project = _mapping(previous.get("project"))
    current_project = _mapping(current.get("project"))
    keys = ("id", "owner", "number")
    differences = [
        key for key in keys if previous_project.get(key) != current_project.get(key)
    ]
    if differences:
        raise ValueError(
            "snapshots belong to different projects: " + ",".join(differences)
        )


def _index_by_id(value: object, *, label: str) -> dict[str, Mapping[str, Any]]:
    if not isinstance(value, list):
        return {}
    indexed: dict[str, Mapping[str, Any]] = {}
    for raw in value:
        if not isinstance(raw, Mapping):
            continue
        item_id = str(raw.get("id", ""))
        if not item_id:
            raise ValueError(f"{label} id is required")
        if item_id in indexed:
            raise ValueError(f"duplicate {label} id: {item_id}")
        indexed[item_id] = dict(raw)
    return indexed


def _item_change(
    previous: Mapping[str, Any], current: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "item_id": str(current.get("id", previous.get("id", ""))),
        "item_type": {
            "before": str(previous.get("type", "")),
            "after": str(current.get("type", "")),
        },
        "title": {
            "before": _item_title(previous),
            "after": _item_title(current),
        },
        "status": {
            "before": _item_status(previous),
            "after": _item_status(current),
        },
        "changed_paths": _changed_paths(
            _normalize_item(previous), _normalize_item(current)
        ),
        "before": _copy_json(previous),
        "after": _copy_json(current),
    }


def _item_summary(item: Mapping[str, Any]) -> dict[str, Any]:
    content = _mapping(item.get("content"))
    return {
        "item_id": str(item.get("id", "")),
        "item_type": str(item.get("type", "")),
        "content_id": str(content.get("id", "")),
        "title": _item_title(item),
        "status": _item_status(item),
        "repository": str(_mapping(content.get("repository")).get("nameWithOwner", "")),
        "number": int(content.get("number", 0) or 0),
        "url": str(content.get("url", "")),
    }


def _item_title(item: Mapping[str, Any]) -> str:
    return str(_mapping(item.get("content")).get("title", ""))


def _item_status(item: Mapping[str, Any]) -> str:
    field_values = _mapping(item.get("fieldValues"))
    nodes = field_values.get("nodes")
    if not isinstance(nodes, list):
        return ""
    for raw in nodes:
        if not isinstance(raw, Mapping):
            continue
        field = _mapping(raw.get("field"))
        if str(field.get("name", "")).casefold() == "status":
            return str(raw.get("name", raw.get("text", "")))
    return ""


def _normalize_item(item: Mapping[str, Any]) -> dict[str, Any]:
    normalized = _copy_json(item)
    field_values = normalized.get("fieldValues")
    if isinstance(field_values, dict) and isinstance(field_values.get("nodes"), list):
        field_values["nodes"] = sorted(
            field_values["nodes"],
            key=lambda value: (
                str(_mapping(_mapping(value).get("field")).get("id", "")),
                str(_mapping(value).get("__typename", "")),
                _canonical_json(_mapping(value)),
            ),
        )
    return normalized


def _changed_paths(before: object, after: object, *, prefix: str = "") -> list[str]:
    if isinstance(before, Mapping) and isinstance(after, Mapping):
        paths: list[str] = []
        for key in sorted(set(before) | set(after), key=str):
            path = f"{prefix}.{key}" if prefix else str(key)
            if key not in before or key not in after:
                paths.append(path)
            else:
                paths.extend(_changed_paths(before[key], after[key], prefix=path))
        return paths
    if isinstance(before, list) and isinstance(after, list):
        if _canonical_json({"value": before}) == _canonical_json({"value": after}):
            return []
        return [prefix or "$list"]
    return [] if before == after else [prefix or "$value"]


def _boundaries(execute: bool) -> dict[str, bool]:
    return {
        "plan_only": not execute,
        "local_snapshot_comparison_only": True,
        "external_call_performed": False,
        "graphql_query_performed": False,
        "graphql_mutation_allowed": False,
        "remote_mutation_allowed": False,
        "token_required": False,
        "token_value_serialized": False,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
        "scheduler_modified": False,
        "shm_touched": False,
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _copy_json(value: object) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
