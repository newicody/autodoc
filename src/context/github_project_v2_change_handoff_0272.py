"""Convert a local GitHub ProjectV2 change set into candidate handoffs.

The phase reuses the existing ``SourceCandidate`` contract.  It performs no
network call, no GitHub mutation, no SQL/Qdrant write and no Scheduler change.
Filesystem writes remain at the CLI boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Mapping, Sequence

from context.github_project_v2_snapshot_change_detection_0272 import CHANGE_SET_SCHEMA
from context.source_candidate import (
    SourceCandidateInput,
    SourceCandidateOrigin,
    SourceCandidatePolicy,
    build_source_candidate,
)

HANDOFF_BATCH_SCHEMA = "missipy.github.project_v2_change_handoff_batch.v1"
REPORT_SCHEMA = "missipy.github.project_v2_change_handoff_report.v1"


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ChangeHandoffPolicy:
    include_added: bool = True
    include_changed: bool = True
    include_removed: bool = True
    include_baseline: bool = False
    max_handoffs: int = 100

    def __post_init__(self) -> None:
        if self.max_handoffs <= 0:
            raise ValueError("max_handoffs must be > 0")

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "include_added": self.include_added,
            "include_changed": self.include_changed,
            "include_removed": self.include_removed,
            "include_baseline": self.include_baseline,
            "max_handoffs": self.max_handoffs,
        }


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ChangeHandoffCommand:
    execute: bool = False
    policy_decision_id: str = ""


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ChangeHandoffPlan:
    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    change_set_path: str
    policy: GitHubProjectV2ChangeHandoffPolicy
    boundaries: Mapping[str, bool]


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ChangeHandoffResult:
    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    change_set_ref: str
    handoff_batch_ref: str
    handoff_batch_path: str
    baseline: bool
    candidate_count: int
    added_candidate_count: int
    changed_candidate_count: int
    removed_candidate_count: int
    truncated_count: int
    external_call_performed: bool = False
    boundaries: Mapping[str, bool] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": REPORT_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "policy_decision_id": self.policy_decision_id,
            "change_set_ref": self.change_set_ref,
            "handoff_batch_ref": self.handoff_batch_ref,
            "handoff_batch_path": self.handoff_batch_path,
            "baseline": self.baseline,
            "counts": {
                "candidate_count": self.candidate_count,
                "added_candidate_count": self.added_candidate_count,
                "changed_candidate_count": self.changed_candidate_count,
                "removed_candidate_count": self.removed_candidate_count,
                "truncated_count": self.truncated_count,
            },
            "external_call_performed": self.external_call_performed,
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"github_project_v2_change_handoff_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"execute={self.execute}",
                f"baseline={self.baseline}",
                f"change_set_ref={self.change_set_ref or '-'}",
                f"handoff_batch_ref={self.handoff_batch_ref or '-'}",
                f"candidates={self.candidate_count}",
                f"added={self.added_candidate_count}",
                f"changed={self.changed_candidate_count}",
                f"removed={self.removed_candidate_count}",
                f"truncated={self.truncated_count}",
                "external_call_performed=False",
                "sql_write_allowed=False",
                "qdrant_write_allowed=False",
                "remote_mutation_allowed=False",
            )
        )


def build_change_handoff_plan(
    command: GitHubProjectV2ChangeHandoffCommand,
    *,
    change_set_path: str,
    policy: GitHubProjectV2ChangeHandoffPolicy,
) -> GitHubProjectV2ChangeHandoffPlan:
    issues: list[str] = []
    path = change_set_path.strip()
    if not path:
        issues.append("change set path is required")
    if command.execute and not command.policy_decision_id.strip():
        issues.append("policy_decision_id is required for execute mode")
    return GitHubProjectV2ChangeHandoffPlan(
        valid=not issues,
        issues=tuple(issues),
        execute=command.execute,
        policy_decision_id=command.policy_decision_id,
        change_set_path=path,
        policy=policy,
        boundaries=_boundaries(command.execute),
    )


def validate_change_set(change_set: Mapping[str, Any]) -> tuple[str, ...]:
    issues: list[str] = []
    if str(change_set.get("schema", "")) != CHANGE_SET_SCHEMA:
        issues.append("change set schema mismatch")
    if not str(change_set.get("change_set_ref", "")).startswith(
        "github-project-v2-change-set:"
    ):
        issues.append("change_set_ref is invalid")
    project = _mapping(change_set.get("project"))
    if not str(project.get("id", "")).startswith("PVT_"):
        issues.append("project id is invalid")
    if int(project.get("number", 0) or 0) <= 0:
        issues.append("project number is invalid")
    boundaries = _mapping(change_set.get("boundaries"))
    if boundaries.get("external_call_performed") is not False:
        issues.append("change set must be local-only")
    if boundaries.get("remote_mutation_allowed") is not False:
        issues.append("change set must forbid remote mutation")
    if boundaries.get("sql_write_allowed") is not False:
        issues.append("change set must forbid SQL writes")
    if boundaries.get("qdrant_write_allowed") is not False:
        issues.append("change set must forbid Qdrant writes")
    return tuple(issues)


def build_change_handoff_batch(
    *,
    change_set: Mapping[str, Any],
    policy: GitHubProjectV2ChangeHandoffPolicy,
) -> dict[str, Any]:
    issues = validate_change_set(change_set)
    if issues:
        raise ValueError("; ".join(issues))

    baseline = bool(change_set.get("baseline", False))
    project = _mapping(change_set.get("project"))
    items = _mapping(change_set.get("items"))
    selected: list[tuple[str, Mapping[str, Any]]] = []
    if not baseline or policy.include_baseline:
        if policy.include_added:
            selected.extend(("added", item) for item in _mapping_items(items.get("added")))
        if policy.include_changed:
            selected.extend(("changed", item) for item in _mapping_items(items.get("changed")))
        if policy.include_removed:
            selected.extend(("removed", item) for item in _mapping_items(items.get("removed")))

    selected.sort(key=lambda entry: (entry[0], _item_id(entry[1])))
    truncated_count = max(0, len(selected) - policy.max_handoffs)
    selected = selected[: policy.max_handoffs]
    handoffs = [
        _build_candidate_handoff(
            change_kind=change_kind,
            item=item,
            change_set_ref=str(change_set.get("change_set_ref", "")),
            project=project,
        )
        for change_kind, item in selected
    ]
    counts = {
        "candidate_count": len(handoffs),
        "added_candidate_count": sum(
            1 for handoff in handoffs if handoff["change_kind"] == "added"
        ),
        "changed_candidate_count": sum(
            1 for handoff in handoffs if handoff["change_kind"] == "changed"
        ),
        "removed_candidate_count": sum(
            1 for handoff in handoffs if handoff["change_kind"] == "removed"
        ),
        "truncated_count": truncated_count,
    }
    payload: dict[str, Any] = {
        "schema": HANDOFF_BATCH_SCHEMA,
        "kind": "github_project_v2_change_handoff_batch",
        "change_set_ref": str(change_set.get("change_set_ref", "")),
        "previous_snapshot_ref": str(change_set.get("previous_snapshot_ref", "")),
        "current_snapshot_ref": str(change_set.get("current_snapshot_ref", "")),
        "baseline": baseline,
        "project": {
            "id": str(project.get("id", "")),
            "owner": str(project.get("owner", "")),
            "number": int(project.get("number", 0) or 0),
            "title": str(project.get("title", "")),
            "url": str(project.get("url", "")),
        },
        "policy": policy.to_json_dict(),
        "handoffs": handoffs,
        "counts": counts,
        "boundaries": _boundaries(True),
    }
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()[:16]
    payload["handoff_batch_ref"] = f"github-project-v2-handoff-batch:{digest}"
    return payload


def close_change_handoff_result(
    plan: GitHubProjectV2ChangeHandoffPlan,
    *,
    handoff_batch: Mapping[str, Any] | None,
    handoff_batch_path: str,
    errors: Sequence[str] = (),
) -> GitHubProjectV2ChangeHandoffResult:
    issues = list(plan.issues)
    issues.extend(str(error) for error in errors if str(error))
    payload = dict(handoff_batch or {})
    if plan.execute:
        if not payload:
            issues.append("execute mode must produce a handoff batch")
        if payload and str(payload.get("schema", "")) != HANDOFF_BATCH_SCHEMA:
            issues.append("handoff batch schema mismatch")
    elif payload:
        issues.append("plan-only mode must not contain a handoff batch")
    counts = _mapping(payload.get("counts"))
    return GitHubProjectV2ChangeHandoffResult(
        valid=not issues,
        issues=tuple(issues),
        execute=plan.execute,
        policy_decision_id=plan.policy_decision_id,
        change_set_ref=str(payload.get("change_set_ref", "")),
        handoff_batch_ref=str(payload.get("handoff_batch_ref", "")),
        handoff_batch_path=handoff_batch_path,
        baseline=bool(payload.get("baseline", False)),
        candidate_count=int(counts.get("candidate_count", 0) or 0),
        added_candidate_count=int(counts.get("added_candidate_count", 0) or 0),
        changed_candidate_count=int(counts.get("changed_candidate_count", 0) or 0),
        removed_candidate_count=int(counts.get("removed_candidate_count", 0) or 0),
        truncated_count=int(counts.get("truncated_count", 0) or 0),
        external_call_performed=False,
        boundaries=_boundaries(plan.execute),
    )


def _build_candidate_handoff(
    *,
    change_kind: str,
    item: Mapping[str, Any],
    change_set_ref: str,
    project: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = _normalized_change_item(change_kind, item)
    item_id = str(normalized.get("item_id", ""))
    item_type = str(normalized.get("item_type", "UNKNOWN"))
    repository = str(normalized.get("repository", ""))
    title = str(normalized.get("title", "")).strip() or f"GitHub Project item {item_id}"
    body = str(normalized.get("body", ""))
    project_url = str(project.get("url", ""))
    reference = f"{project_url}#item:{item_id}" if project_url else f"github-project-v2-item:{item_id}"
    labels = (
        "github-project-v2",
        f"change-{change_kind}",
        f"item-{item_type.lower().replace('_', '-')}",
    )
    metadata = {
        "change_kind": change_kind,
        "change_set_ref": change_set_ref,
        "project_id": str(project.get("id", "")),
        "project_owner": str(project.get("owner", "")),
        "project_number": int(project.get("number", 0) or 0),
        "project_url": project_url,
        "item_id": item_id,
        "item_type": item_type,
        "content_id": str(normalized.get("content_id", "")),
        "status": str(normalized.get("status", "")),
        "repository": repository,
        "number": int(normalized.get("number", 0) or 0),
        "url": str(normalized.get("url", "")),
        "changed_paths": list(normalized.get("changed_paths", ())),
        "removal_is_advisory": change_kind == "removed",
        "durable_ingestion_allowed": False,
    }
    creation = build_source_candidate(
        SourceCandidateInput(
            title=title,
            body=body,
            origin=SourceCandidateOrigin(
                kind="github",
                reference=reference,
                repository=repository or None,
            ),
            labels=labels,
            metadata=metadata,
        ),
        SourceCandidatePolicy(
            default_status="new",
            default_repository=None,
            id_prefix="ghpv2",
        ),
    )
    candidate = creation.candidate.to_json_dict()
    handoff_seed = {
        "change_kind": change_kind,
        "change_set_ref": change_set_ref,
        "candidate_id": candidate["candidate_id"],
        "item_id": item_id,
    }
    digest = hashlib.sha256(_canonical_json(handoff_seed).encode("utf-8")).hexdigest()[:16]
    return {
        "schema": "missipy.github.project_v2_change_handoff.v1",
        "handoff_ref": f"github-project-v2-change-handoff:{digest}",
        "change_kind": change_kind,
        "candidate": candidate,
        "requires_operator_gate": True,
        "durable_ingestion_allowed": False,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
        "remote_mutation_allowed": False,
    }


def _normalized_change_item(change_kind: str, item: Mapping[str, Any]) -> dict[str, Any]:
    if change_kind == "changed":
        after = _mapping(item.get("after"))
        content = _mapping(after.get("content"))
        repository = _mapping(content.get("repository"))
        item_type = _mapping(item.get("item_type"))
        status = _mapping(item.get("status"))
        title = _mapping(item.get("title"))
        return {
            "item_id": str(item.get("item_id", after.get("id", ""))),
            "item_type": str(item_type.get("after", after.get("type", "UNKNOWN"))),
            "content_id": str(content.get("id", "")),
            "title": str(title.get("after", content.get("title", ""))),
            "body": str(content.get("body", "")),
            "status": str(status.get("after", "")),
            "repository": str(repository.get("nameWithOwner", "")),
            "number": int(content.get("number", 0) or 0),
            "url": str(content.get("url", "")),
            "changed_paths": tuple(str(path) for path in item.get("changed_paths", ())),
        }
    return {
        "item_id": str(item.get("item_id", "")),
        "item_type": str(item.get("item_type", "UNKNOWN")),
        "content_id": str(item.get("content_id", "")),
        "title": str(item.get("title", "")),
        "body": str(item.get("body", "")),
        "status": str(item.get("status", "")),
        "repository": str(item.get("repository", "")),
        "number": int(item.get("number", 0) or 0),
        "url": str(item.get("url", "")),
        "changed_paths": (),
    }


def _mapping_items(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(dict(item) for item in value if isinstance(item, Mapping))


def _item_id(item: Mapping[str, Any]) -> str:
    return str(item.get("item_id", _mapping(item.get("after")).get("id", "")))


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _boundaries(execute: bool) -> dict[str, bool]:
    return {
        "local_change_set_read_only": True,
        "source_candidate_contract_reused": True,
        "operator_gate_required": True,
        "execute_requested": execute,
        "external_call_performed": False,
        "graphql_query_performed": False,
        "graphql_mutation_allowed": False,
        "remote_mutation_allowed": False,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
        "scheduler_modified": False,
        "shm_modified": False,
        "local_authority_preserved": True,
    }
