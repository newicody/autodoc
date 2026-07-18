"""Transform an admissible GitHub research route candidate into an authorized
Scheduler route request by reusing the existing Scheduler intake adapter.

This unit deliberately stops before Scheduler emission.  The automatic policy
is explicit and deterministic: only a candidate already approved by the r16-r6
admissibility gate for ``newicody/projects`` can become an authorized
``SchedulerRouteRequest``.

No Scheduler, Dispatcher, EventBus, laboratory, SQL, Qdrant, OpenVINO, GitHub
client, daemon, or filesystem adapter is instantiated here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any

from context.github_artifact_scheduler_intake import (
    build_github_artifact_scheduler_intake_plan,
)
from context.github_research_work_package_admissibility_0287 import (
    ROUTE_CANDIDATE_SCHEMA,
)

SCHEMA = "missipy.github.research_scheduler_intake.v1"
POLICY_SCHEMA = "missipy.github.research_automatic_scheduler_policy.v1"
POLICY_DECISION_SCHEMA = (
    "missipy.github.research_automatic_scheduler_policy_decision.v1"
)
_ALLOWED_REPOSITORY = "newicody/projects"
_ALLOWED_STATUS = "Recherche"
_ALLOWED_MODES = frozenset(("initial", "continuation"))
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class GitHubResearchAutomaticSchedulerPolicy:
    """Explicit policy allowing admissible research to enter Scheduler intake."""

    schema: str = POLICY_SCHEMA
    policy_ref: str = "policy:github-research:auto-scheduler:r16-r8"
    enabled: bool = True
    repository: str = _ALLOWED_REPOSITORY
    requested_status: str = _ALLOWED_STATUS
    request_modes: tuple[str, ...] = ("initial", "continuation")
    priority: int = 60

    def __post_init__(self) -> None:
        if self.schema != POLICY_SCHEMA:
            raise ValueError("unsupported automatic Scheduler policy schema")
        if not self.policy_ref.strip():
            raise ValueError("policy_ref must not be empty")
        if self.repository != _ALLOWED_REPOSITORY:
            raise ValueError("automatic Scheduler policy repository mismatch")
        if self.requested_status != _ALLOWED_STATUS:
            raise ValueError("automatic Scheduler policy status mismatch")
        if frozenset(self.request_modes) != _ALLOWED_MODES:
            raise ValueError("automatic Scheduler policy modes mismatch")
        if isinstance(self.priority, bool) or not 0 <= self.priority <= 100:
            raise ValueError("priority must be an integer between 0 and 100")


@dataclass(frozen=True, slots=True)
class GitHubResearchSchedulerIntakeCommand:
    """Pure request to build an authorized route request without dispatch."""

    route_candidate: Mapping[str, Any]
    requested_at: str
    policy: GitHubResearchAutomaticSchedulerPolicy = field(
        default_factory=GitHubResearchAutomaticSchedulerPolicy
    )
    dispatch: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.route_candidate, Mapping):
            raise TypeError("route_candidate must be a mapping")
        timestamp = self.requested_at.strip()
        if "T" not in timestamp or not timestamp.endswith("Z"):
            raise ValueError("requested_at must be a UTC timestamp ending with Z")
        object.__setattr__(self, "requested_at", timestamp)
        if self.dispatch:
            raise ValueError(
                "r16-r8 only builds the request; dispatch must remain false"
            )


@dataclass(frozen=True, slots=True)
class GitHubResearchSchedulerIntakeResult:
    """Authorized Scheduler intake plan and its explicit policy proof."""

    valid: bool
    authorized: bool
    status: str
    issues: tuple[str, ...]
    policy_decision: Mapping[str, Any] = field(default_factory=dict)
    scheduler_intake_plan: Mapping[str, Any] = field(default_factory=dict)
    research_route_candidate: Mapping[str, Any] = field(default_factory=dict)

    def to_mapping(self) -> dict[str, Any]:
        route_request = self.scheduler_intake_plan.get("scheduler_route_request")
        return {
            "schema": SCHEMA,
            "valid": self.valid,
            "authorized": self.authorized,
            "status": self.status,
            "issues": list(self.issues),
            "policy_decision": dict(self.policy_decision),
            "scheduler_intake_plan": dict(self.scheduler_intake_plan),
            "scheduler_route_request": (
                dict(route_request) if isinstance(route_request, Mapping) else None
            ),
            "research_route_candidate": dict(self.research_route_candidate),
            "automatic_policy_is_explicit": True,
            "existing_scheduler_intake_reused": True,
            "existing_scheduler_route_adapter_reused": True,
            "operator_decision_required": False,
            "scheduler_modified": False,
            "scheduler_command_created": self.authorized,
            "scheduler_dispatch_started": False,
            "laboratory_execution_started": False,
            "sql_write_performed": False,
            "qdrant_write_performed": False,
            "github_mutation_performed": False,
        }


def build_authorized_scheduler_intake_for_admissible_research(
    command: GitHubResearchSchedulerIntakeCommand,
) -> GitHubResearchSchedulerIntakeResult:
    """Apply the explicit auto-admission policy and reuse existing intake."""

    candidate = dict(command.route_candidate)
    issues = _validate_route_candidate(candidate, command.policy)
    if not command.policy.enabled:
        issues.append("automatic Scheduler admission policy is disabled")
    if issues:
        return GitHubResearchSchedulerIntakeResult(
            valid=False,
            authorized=False,
            status="rejected",
            issues=tuple(dict.fromkeys(issues)),
            research_route_candidate=candidate,
        )

    policy_decision = _build_policy_decision(candidate, command.policy)
    decision_id = str(policy_decision["policy_decision_id"])
    digest = str(candidate["admissibility_digest"])
    issue_number = int(candidate["issue_number"])

    intake_source = {
        "observation_ref": str(candidate["route_candidate_ref"]),
        "repository": str(candidate["repository"]),
        "run_id": str(candidate["run_id"]),
        "artifact_id": f"research-i{issue_number}-{digest[:16]}",
        "dataset_root_ref": str(candidate["work_package_ref"]),
        "route_id": f"github-research-laboratory-{digest[:24]}",
        "task_id": f"task:github-research:{digest[:24]}",
        "candidate_ref": f"scheduler-candidate:github-research:{digest[:24]}",
        "status": "planned",
        "priority": command.policy.priority,
        "requested_at": command.requested_at,
    }
    try:
        plan = build_github_artifact_scheduler_intake_plan(
            intake_source,
            policy_decision_id=decision_id,
            authorized=True,
        )
        plan_mapping = plan.to_mapping()
    except (TypeError, ValueError) as exc:
        return GitHubResearchSchedulerIntakeResult(
            valid=False,
            authorized=False,
            status="intake-invalid",
            issues=(str(exc),),
            policy_decision=policy_decision,
            research_route_candidate=candidate,
        )

    route_request = plan_mapping.get("scheduler_route_request")
    if plan_mapping.get("authorized") is not True:
        return _invalid_plan(
            "existing Scheduler intake did not authorize the route request",
            policy_decision,
            plan_mapping,
            candidate,
        )
    if not isinstance(route_request, Mapping):
        return _invalid_plan(
            "existing Scheduler intake did not produce a route request",
            policy_decision,
            plan_mapping,
            candidate,
        )
    if route_request.get("authorized") is not True:
        return _invalid_plan(
            "Scheduler route request is not authorized",
            policy_decision,
            plan_mapping,
            candidate,
        )
    if route_request.get("policy_decision_id") != decision_id:
        return _invalid_plan(
            "Scheduler route request policy decision mismatch",
            policy_decision,
            plan_mapping,
            candidate,
        )

    return GitHubResearchSchedulerIntakeResult(
        valid=True,
        authorized=True,
        status="scheduler-request-ready",
        issues=(),
        policy_decision=policy_decision,
        scheduler_intake_plan=plan_mapping,
        research_route_candidate=candidate,
    )


def _validate_route_candidate(
    candidate: Mapping[str, Any],
    policy: GitHubResearchAutomaticSchedulerPolicy,
) -> list[str]:
    issues: list[str] = []
    if candidate.get("schema") != ROUTE_CANDIDATE_SCHEMA:
        issues.append("unsupported research route candidate schema")
    if candidate.get("repository") != policy.repository:
        issues.append("research route candidate repository is not authorized")
    if candidate.get("requested_status") != policy.requested_status:
        issues.append("research route candidate status is not authorized")
    mode = candidate.get("request_mode")
    if mode not in policy.request_modes:
        issues.append("research route candidate mode is not authorized")
    parent = candidate.get("parent_event_ref")
    if mode == "initial" and parent not in ("", None):
        issues.append("initial research must not carry parent_event_ref")
    if mode == "continuation" and not _text(parent):
        issues.append("continuation research requires parent_event_ref")

    issue_number = candidate.get("issue_number")
    if (
        isinstance(issue_number, bool)
        or not isinstance(issue_number, int)
        or issue_number <= 0
    ):
        issues.append("issue_number must be a positive integer")

    for field_name in (
        "route_candidate_ref",
        "work_package_ref",
        "repository",
        "run_id",
        "requested_status",
        "request_mode",
        "conversation_ref",
        "return_route_ref",
        "admissibility_digest",
    ):
        if not _text(candidate.get(field_name)):
            issues.append(f"{field_name} must not be empty")

    digest = _text(candidate.get("admissibility_digest"))
    if digest and _SHA256_RE.fullmatch(digest) is None:
        issues.append("admissibility_digest must be a lowercase SHA-256")

    for flag in (
        "scheduler_command_created",
        "scheduler_dispatch_started",
        "laboratory_execution_started",
    ):
        if candidate.get(flag) is not False:
            issues.append(f"{flag} must be false before Scheduler intake")

    for field_name in ("context_refs", "evidence_refs"):
        value = candidate.get(field_name)
        if not isinstance(value, list) or any(not _text(item) for item in value):
            issues.append(f"{field_name} must be a list of non-empty strings")

    generation = candidate.get("context_generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        issues.append("context_generation must be a non-negative integer")
    return issues


def _build_policy_decision(
    candidate: Mapping[str, Any],
    policy: GitHubResearchAutomaticSchedulerPolicy,
) -> dict[str, Any]:
    payload = {
        "policy_ref": policy.policy_ref,
        "repository": candidate["repository"],
        "run_id": candidate["run_id"],
        "issue_number": candidate["issue_number"],
        "requested_status": candidate["requested_status"],
        "request_mode": candidate["request_mode"],
        "route_candidate_ref": candidate["route_candidate_ref"],
        "admissibility_digest": candidate["admissibility_digest"],
        "decision": "approve",
        "reason": "research package already passed the locked r16-r6 gate",
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    return {
        "schema": POLICY_DECISION_SCHEMA,
        "policy_decision_id": (
            f"policy-decision:github-research-auto:{digest[:24]}"
        ),
        "policy_ref": policy.policy_ref,
        "decision": "approve",
        "automatic": True,
        "repository": candidate["repository"],
        "run_id": candidate["run_id"],
        "issue_number": candidate["issue_number"],
        "route_candidate_ref": candidate["route_candidate_ref"],
        "admissibility_digest": candidate["admissibility_digest"],
        "decision_digest": digest,
        "scheduler_dispatch_started": False,
        "laboratory_execution_started": False,
    }


def _invalid_plan(
    issue: str,
    policy_decision: Mapping[str, Any],
    plan: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> GitHubResearchSchedulerIntakeResult:
    return GitHubResearchSchedulerIntakeResult(
        valid=False,
        authorized=False,
        status="intake-invalid",
        issues=(issue,),
        policy_decision=dict(policy_decision),
        scheduler_intake_plan=dict(plan),
        research_route_candidate=dict(candidate),
    )


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""
