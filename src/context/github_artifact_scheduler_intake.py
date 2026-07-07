"""GitHub artifact scheduler intake contract.

0177 turns GitHub artifact/server dataset observations into scheduler-addressable
intake candidates without executing Scheduler, without modifying Scheduler.run(),
and without bypassing policy.

The module reuses the existing scheduler route adapter constructor:
scheduler_route_request_mapping(...).

Important boundary:

- A candidate is not authorized work.
- A SchedulerRouteRequest is produced only when an explicit policy_decision_id is
  supplied.
- This module does not call handle_scheduler_route_request.
- This module does not instantiate Scheduler, Dispatcher, PriorityQueue,
  EventBus, ControlProxy, RouteProxyRuntime, VisPy, GitHub, SQL, Qdrant,
  OpenVINO, or network clients.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from runtime.scheduler_route_adapter import (
    SCHEDULER_ROUTE_REQUEST_SCHEMA,
    scheduler_route_request_mapping,
)


GITHUB_ARTIFACT_SCHEDULER_INTAKE_CANDIDATE_SCHEMA = "missipy.github_artifact.scheduler_intake_candidate.v1"
GITHUB_ARTIFACT_SCHEDULER_INTAKE_PLAN_SCHEMA = "missipy.github_artifact.scheduler_intake_plan.v1"

_ALLOWED_STATUS = {
    "planned",
    "born",
    "discovered",
    "fetched",
    "synced",
    "validated",
    "queued",
    "running",
    "succeeded",
    "failed",
    "blocked",
    "dead",
    "superseded",
    "retrying",
    "stale",
    "partial",
}
_SAFE_RE = re.compile(r"[^a-z0-9_.-]+")


class GithubArtifactSchedulerIntakeError(ValueError):
    """Raised when scheduler intake cannot be built safely."""


@dataclass(frozen=True, slots=True)
class GithubArtifactSchedulerIntakeCandidate:
    """Scheduler-addressable candidate derived from a dataset observation.

    This is not a command. It is not authorized. It is a compact planning object
    that can later become a SchedulerRouteRequest through the existing adapter
    constructor after policy has produced a policy_decision_id.
    """

    schema: str
    candidate_ref: str
    observation_ref: str
    repository: str
    run_id: str
    artifact_id: str
    dataset_root_ref: str
    route_id: str
    task_id: str
    status: str
    priority: int
    requested_at: str
    authorized: bool = False
    policy_decision_id: str | None = None
    scheduler_modified: bool = False
    scheduler_route_request_ready: bool = False
    observation_only_source: bool = True

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "GithubArtifactSchedulerIntakeCandidate":
        required = {
            "observation_ref",
            "repository",
            "run_id",
            "artifact_id",
            "dataset_root_ref",
            "status",
            "requested_at",
        }
        missing = sorted(required.difference(raw))
        if missing:
            raise GithubArtifactSchedulerIntakeError(
                "scheduler intake candidate missing required fields: " + ", ".join(missing)
            )

        repository = _require_text(raw, "repository")
        run_id = _require_text(raw, "run_id")
        artifact_id = _require_text(raw, "artifact_id")
        route_id = _safe_id(str(raw.get("route_id") or f"github-artifact-{repository}-{run_id}-{artifact_id}"), prefix="route")
        task_id = _safe_id(str(raw.get("task_id") or f"task:github-artifact:{repository}:{run_id}:{artifact_id}"), prefix="task")
        candidate_ref = _safe_id(str(raw.get("candidate_ref") or f"scheduler-candidate:{repository}:{run_id}:{artifact_id}"), prefix="scheduler-candidate")
        policy_decision_id = raw.get("policy_decision_id")
        if policy_decision_id is not None:
            policy_decision_id = _require_id_value("policy_decision_id", policy_decision_id)
        authorized = bool(raw.get("authorized", False))
        if authorized and not policy_decision_id:
            raise GithubArtifactSchedulerIntakeError("authorized candidate requires policy_decision_id")

        return cls(
            schema=str(raw.get("schema", GITHUB_ARTIFACT_SCHEDULER_INTAKE_CANDIDATE_SCHEMA)),
            candidate_ref=candidate_ref,
            observation_ref=_require_text(raw, "observation_ref"),
            repository=repository,
            run_id=run_id,
            artifact_id=artifact_id,
            dataset_root_ref=_require_text(raw, "dataset_root_ref"),
            route_id=route_id,
            task_id=task_id,
            status=_require_status(raw["status"]),
            priority=_require_priority(raw.get("priority", 50)),
            requested_at=_require_timestamp(raw, "requested_at"),
            authorized=authorized,
            policy_decision_id=policy_decision_id,
            scheduler_route_request_ready=authorized and policy_decision_id is not None,
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "candidate_ref": self.candidate_ref,
            "observation_ref": self.observation_ref,
            "repository": self.repository,
            "run_id": self.run_id,
            "artifact_id": self.artifact_id,
            "dataset_root_ref": self.dataset_root_ref,
            "route_id": self.route_id,
            "task_id": self.task_id,
            "status": self.status,
            "priority": self.priority,
            "requested_at": self.requested_at,
            "authorized": self.authorized,
            "policy_decision_id": self.policy_decision_id,
            "scheduler_modified": self.scheduler_modified,
            "scheduler_route_request_ready": self.scheduler_route_request_ready,
            "observation_only_source": self.observation_only_source,
        }


@dataclass(frozen=True, slots=True)
class GithubArtifactSchedulerIntakePlan:
    """Pure planning result for scheduler intake."""

    schema: str
    candidate: GithubArtifactSchedulerIntakeCandidate
    scheduler_route_request: Mapping[str, Any] | None

    @property
    def authorized(self) -> bool:
        return self.scheduler_route_request is not None

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "candidate": self.candidate.to_mapping(),
            "authorized": self.authorized,
            "scheduler_route_request": dict(self.scheduler_route_request) if self.scheduler_route_request else None,
            "uses_existing_scheduler_route_adapter": True,
            "scheduler_modified": False,
            "calls_handle_scheduler_route_request": False,
            "creates_parallel_scheduler": False,
            "creates_parallel_bus": False,
        }


def build_github_artifact_scheduler_intake_candidate(
    raw: Mapping[str, Any],
) -> GithubArtifactSchedulerIntakeCandidate:
    """Build an unauthorized scheduler-addressable intake candidate."""

    candidate = GithubArtifactSchedulerIntakeCandidate.from_mapping(raw)
    if candidate.schema != GITHUB_ARTIFACT_SCHEDULER_INTAKE_CANDIDATE_SCHEMA:
        raise GithubArtifactSchedulerIntakeError("unsupported scheduler intake candidate schema")
    return candidate


def build_github_artifact_scheduler_intake_plan(
    raw: Mapping[str, Any],
    *,
    policy_decision_id: str | None = None,
    authorized: bool = False,
) -> GithubArtifactSchedulerIntakePlan:
    """Build an intake plan, optionally using the existing route request mapping.

    If authorized is false, no SchedulerRouteRequest is produced. If authorized is
    true, policy_decision_id is mandatory and the existing
    scheduler_route_request_mapping(...) constructor is used.
    """

    merged = dict(raw)
    if policy_decision_id is not None:
        merged["policy_decision_id"] = policy_decision_id
    if authorized:
        merged["authorized"] = True
    candidate = build_github_artifact_scheduler_intake_candidate(merged)

    route_request: Mapping[str, Any] | None = None
    if authorized:
        if not candidate.policy_decision_id:
            raise GithubArtifactSchedulerIntakeError("policy_decision_id is required for authorized scheduler route request")
        route_request = scheduler_route_request_mapping(
            request_id=_safe_id(f"request:{candidate.candidate_ref}", prefix="request"),
            route_id=candidate.route_id,
            task_id=candidate.task_id,
            holder="scheduler",
            scope="route.write",
            policy_decision_id=candidate.policy_decision_id,
            ttl_seconds=300,
            activate=True,
            requested_at=candidate.requested_at,
        )
        if route_request.get("schema") != SCHEDULER_ROUTE_REQUEST_SCHEMA:
            raise GithubArtifactSchedulerIntakeError("existing scheduler route adapter returned unexpected schema")

    return GithubArtifactSchedulerIntakePlan(
        schema=GITHUB_ARTIFACT_SCHEDULER_INTAKE_PLAN_SCHEMA,
        candidate=candidate,
        scheduler_route_request=route_request,
    )


def _require_text(raw: Mapping[str, Any], field: str) -> str:
    value = raw[field]
    if not isinstance(value, str) or not value.strip():
        raise GithubArtifactSchedulerIntakeError(f"{field} must be a non-empty string")
    if "\x00" in value:
        raise GithubArtifactSchedulerIntakeError(f"{field} must not contain NUL bytes")
    return value.strip()


def _require_id_value(field: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GithubArtifactSchedulerIntakeError(f"{field} must be a non-empty string")
    if not value.replace("_", "").replace(".", "").replace(":", "").replace("-", "").isalnum():
        raise GithubArtifactSchedulerIntakeError(f"{field} contains invalid characters")
    return value


def _require_status(value: Any) -> str:
    if not isinstance(value, str) or value not in _ALLOWED_STATUS:
        raise GithubArtifactSchedulerIntakeError("status must be in the locked activity vocabulary")
    return value


def _require_priority(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > 100:
        raise GithubArtifactSchedulerIntakeError("priority must be an integer between 0 and 100")
    return value


def _require_timestamp(raw: Mapping[str, Any], field: str) -> str:
    value = _require_text(raw, field)
    if "T" not in value or not value.endswith("Z"):
        raise GithubArtifactSchedulerIntakeError(f"{field} must be a UTC timestamp ending with Z")
    return value


def _safe_id(value: str, *, prefix: str) -> str:
    candidate = value.lower().replace(":", "-").replace("/", "-").replace("\\", "-")
    candidate = _SAFE_RE.sub("-", candidate).strip("._-")
    while "--" in candidate:
        candidate = candidate.replace("--", "-")
    if not candidate:
        candidate = prefix
    if not candidate.startswith(prefix):
        candidate = f"{prefix}-{candidate}"
    if len(candidate) > 128:
        candidate = candidate[:128].rstrip("._-")
    return candidate
