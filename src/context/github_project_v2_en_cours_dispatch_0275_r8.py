"""Pure dispatch selection for ProjectV2 transitions into ``En cours``.

The module consumes immutable 0272 change sets and produces typed,
serializable workflow-dispatch candidates. It performs no IO or network
access and never mutates GitHub, SQL, Qdrant or the Scheduler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Mapping, Sequence


CHANGE_SET_SCHEMA = "missipy.github.project_v2_snapshot_change_set.v1"
STATE_SCHEMA = "missipy.github.project_v2_en_cours_dispatch_state.v1"
REPORT_SCHEMA = "missipy.github.project_v2_en_cours_dispatch_report.v1"

_INTENT_BY_PREVIOUS_STATUS = {
    "": "Recherche",
    "Recherche": "Recherche",
    "Développement": "Développement",
    "Production": "Production",
}


@dataclass(frozen=True, slots=True)
class GitHubProjectV2EnCoursDispatchConfig:
    repository: str
    workflow_name: str
    ref: str
    target_status: str = "En cours"
    max_dispatches: int = 10
    allow_workflow_dispatch: bool = False
    allow_remote_mutation: bool = False


@dataclass(frozen=True, slots=True)
class GitHubProjectV2EnCoursDispatchCommand:
    execute: bool = False
    policy_decision_id: str = ""


@dataclass(frozen=True, slots=True)
class GitHubProjectV2EnCoursDispatchCandidate:
    decision_id: str
    change_set_ref: str
    project_item_id: str
    repository: str
    issue_number: int
    issue_title: str
    issue_url: str
    previous_status: str
    current_status: str
    requested_status: str
    request_mode: str
    parent_event_ref: str = ""

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "change_set_ref": self.change_set_ref,
            "project_item_id": self.project_item_id,
            "repository": self.repository,
            "issue_number": self.issue_number,
            "issue_title": self.issue_title,
            "issue_url": self.issue_url,
            "previous_status": self.previous_status,
            "current_status": self.current_status,
            "workflow_dispatch": {
                "ref": "",
                "inputs": {
                    "issue_number": str(self.issue_number),
                    "requested_status": self.requested_status,
                    "request_mode": self.request_mode,
                    "parent_event_ref": self.parent_event_ref,
                },
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubProjectV2EnCoursDispatchPlan:
    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    repository: str
    workflow_name: str
    ref: str
    change_set_ref: str
    candidates: tuple[GitHubProjectV2EnCoursDispatchCandidate, ...]
    skipped_already_processed: int
    skipped_non_triggering: int
    boundaries: Mapping[str, bool] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        candidates = []
        for candidate in self.candidates:
            payload = candidate.to_json_dict()
            payload["workflow_dispatch"]["ref"] = self.ref
            candidates.append(payload)
        return {
            "schema": REPORT_SCHEMA,
            "kind": "plan",
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "policy_decision_id": self.policy_decision_id,
            "repository": self.repository,
            "workflow_name": self.workflow_name,
            "ref": self.ref,
            "change_set_ref": self.change_set_ref,
            "candidates": candidates,
            "counts": {
                "candidate_count": len(candidates),
                "skipped_already_processed": self.skipped_already_processed,
                "skipped_non_triggering": self.skipped_non_triggering,
            },
            "boundaries": dict(self.boundaries),
        }


def empty_dispatch_state() -> dict[str, Any]:
    return {
        "schema": STATE_SCHEMA,
        "processed_decision_ids": [],
        "issue_dispatch_counts": {},
    }


def validate_dispatch_state(state: Mapping[str, Any]) -> tuple[str, ...]:
    issues: list[str] = []
    if str(state.get("schema", "")) != STATE_SCHEMA:
        issues.append("dispatch state schema mismatch")
    processed = state.get("processed_decision_ids")
    if not isinstance(processed, list) or not all(
        isinstance(value, str) and value for value in processed
    ):
        issues.append("processed_decision_ids must be a list of strings")
    counts = state.get("issue_dispatch_counts")
    if not isinstance(counts, Mapping):
        issues.append("issue_dispatch_counts must be an object")
    elif any(
        not isinstance(key, str)
        or not key
        or not isinstance(value, int)
        or value < 0
        for key, value in counts.items()
    ):
        issues.append("issue_dispatch_counts contains an invalid entry")
    return tuple(issues)


def build_en_cours_dispatch_plan(
    config: GitHubProjectV2EnCoursDispatchConfig,
    command: GitHubProjectV2EnCoursDispatchCommand,
    *,
    change_set: Mapping[str, Any],
    state: Mapping[str, Any],
) -> GitHubProjectV2EnCoursDispatchPlan:
    issues: list[str] = []
    repository = config.repository.strip()
    workflow_name = config.workflow_name.strip()
    ref = config.ref.strip()
    target_status = config.target_status.strip()

    if not repository or "/" not in repository:
        issues.append("repository must be owner/name")
    if not workflow_name:
        issues.append("workflow_name is required")
    if not ref:
        issues.append("ref is required")
    if target_status != "En cours":
        issues.append("target_status must be En cours")
    if config.max_dispatches <= 0:
        issues.append("max_dispatches must be positive")
    if command.execute and not command.policy_decision_id.strip():
        issues.append("policy_decision_id is required for execute mode")
    if command.execute and not config.allow_workflow_dispatch:
        issues.append("workflow dispatch is not allowed")
    if command.execute and not config.allow_remote_mutation:
        issues.append("scoped remote mutation is not allowed")
    if str(change_set.get("schema", "")) != CHANGE_SET_SCHEMA:
        issues.append("change set schema mismatch")
    issues.extend(validate_dispatch_state(state))

    change_set_ref = str(change_set.get("change_set_ref", "")).strip()
    if not change_set_ref:
        issues.append("change_set_ref is required")

    if issues:
        return GitHubProjectV2EnCoursDispatchPlan(
            valid=False,
            issues=tuple(issues),
            execute=command.execute,
            policy_decision_id=command.policy_decision_id,
            repository=repository,
            workflow_name=workflow_name,
            ref=ref,
            change_set_ref=change_set_ref,
            candidates=(),
            skipped_already_processed=0,
            skipped_non_triggering=0,
            boundaries=_boundaries(command.execute),
        )

    processed = set(str(value) for value in state["processed_decision_ids"])
    issue_counts = {
        str(key): int(value)
        for key, value in dict(state["issue_dispatch_counts"]).items()
    }
    changed = _mapping(_mapping(change_set.get("items")).get("changed"))
    changed_items: Sequence[object]
    if isinstance(_mapping(change_set.get("items")).get("changed"), list):
        changed_items = _mapping(change_set.get("items")).get("changed")  # type: ignore[assignment]
    else:
        changed_items = ()

    candidates: list[GitHubProjectV2EnCoursDispatchCandidate] = []
    skipped_processed = 0
    skipped_non_triggering = 0

    for raw in changed_items:
        change = _mapping(raw)
        status = _mapping(change.get("status"))
        previous_status = str(status.get("before", "")).strip()
        current_status = str(status.get("after", "")).strip()
        if current_status != target_status:
            skipped_non_triggering += 1
            continue
        requested_status = _INTENT_BY_PREVIOUS_STATUS.get(previous_status)
        if requested_status is None:
            skipped_non_triggering += 1
            continue

        item_type = str(_mapping(change.get("item_type")).get("after", "")).upper()
        after = _mapping(change.get("after"))
        content = _mapping(after.get("content"))
        candidate_repository = str(
            _mapping(content.get("repository")).get("nameWithOwner", "")
        ).strip()
        issue_number = int(content.get("number", 0) or 0)
        item_id = str(change.get("item_id", "")).strip()
        if (
            item_type != "ISSUE"
            or candidate_repository != repository
            or issue_number <= 0
            or not item_id
        ):
            skipped_non_triggering += 1
            continue

        decision_id = _decision_id(
            change_set_ref=change_set_ref,
            item_id=item_id,
            previous_status=previous_status,
            current_status=current_status,
        )
        if decision_id in processed:
            skipped_processed += 1
            continue

        issue_key = f"{candidate_repository}#{issue_number}"
        title = str(content.get("title", ""))
        if title.startswith("[Événement lié]"):
            request_mode = "transversal"
        elif issue_counts.get(issue_key, 0) > 0:
            request_mode = "continuation"
        else:
            request_mode = "initial"

        candidates.append(
            GitHubProjectV2EnCoursDispatchCandidate(
                decision_id=decision_id,
                change_set_ref=change_set_ref,
                project_item_id=item_id,
                repository=candidate_repository,
                issue_number=issue_number,
                issue_title=title,
                issue_url=str(content.get("url", "")),
                previous_status=previous_status,
                current_status=current_status,
                requested_status=requested_status,
                request_mode=request_mode,
            )
        )

    if len(candidates) > config.max_dispatches:
        issues.append(
            f"candidate count {len(candidates)} exceeds max_dispatches "
            f"{config.max_dispatches}"
        )
        candidates = []

    return GitHubProjectV2EnCoursDispatchPlan(
        valid=not issues,
        issues=tuple(issues),
        execute=command.execute,
        policy_decision_id=command.policy_decision_id,
        repository=repository,
        workflow_name=workflow_name,
        ref=ref,
        change_set_ref=change_set_ref,
        candidates=tuple(candidates),
        skipped_already_processed=skipped_processed,
        skipped_non_triggering=skipped_non_triggering,
        boundaries=_boundaries(command.execute),
    )


def apply_successful_dispatch(
    state: Mapping[str, Any],
    candidate: GitHubProjectV2EnCoursDispatchCandidate,
) -> dict[str, Any]:
    issues = validate_dispatch_state(state)
    if issues:
        raise ValueError("; ".join(issues))
    processed = list(str(value) for value in state["processed_decision_ids"])
    if candidate.decision_id not in processed:
        processed.append(candidate.decision_id)
    counts = {
        str(key): int(value)
        for key, value in dict(state["issue_dispatch_counts"]).items()
    }
    issue_key = f"{candidate.repository}#{candidate.issue_number}"
    counts[issue_key] = counts.get(issue_key, 0) + 1
    return {
        "schema": STATE_SCHEMA,
        "processed_decision_ids": sorted(set(processed)),
        "issue_dispatch_counts": dict(sorted(counts.items())),
    }


def _decision_id(
    *,
    change_set_ref: str,
    item_id: str,
    previous_status: str,
    current_status: str,
) -> str:
    payload = {
        "change_set_ref": change_set_ref,
        "item_id": item_id,
        "previous_status": previous_status,
        "current_status": current_status,
    }
    digest = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:24]
    return f"github-project-v2-en-cours-dispatch:{digest}"


def _boundaries(execute: bool) -> dict[str, bool]:
    return {
        "plan_only": not execute,
        "consumes_existing_0272_change_set": True,
        "project_query_performed": False,
        "project_mutation_allowed": False,
        "issue_mutation_allowed": False,
        "workflow_dispatch_allowed": execute,
        "scoped_remote_mutation_only": execute,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
        "scheduler_modified": False,
        "scheduler_run_modified": False,
        "token_value_serialized": False,
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
