"""Typed GitHub research command prepared for SQL-authoritative scheduling.

The r16-r24 filesystem handoff remains available only as historical
compatibility.  This module converts one validated and authorized intake
projection into immutable Python objects.  It performs no filesystem, SQL,
Scheduler, Dispatcher, EventBus, ControlProxy, laboratory, Qdrant, OpenVINO,
or GitHub operation.

Mappings are accepted and emitted only at adaptation boundaries.  The internal
command authority is the object graph defined here.  A PostgreSQL adapter will
implement ``GitHubResearchSchedulerCommandStore`` in the following unit.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import math
import re
from typing import Any, Protocol, runtime_checkable

from runtime.scheduler_route_adapter import SchedulerRouteRequest


COMMAND_SCHEMA = "missipy.scheduler.command.v1"
AUTHORIZED_COMMAND_SCHEMA = "missipy.scheduler.authorized_command.v1"
GITHUB_RESEARCH_COMMAND_SCHEMA = "missipy.github.research_scheduler_command.v1"
COMMAND_BUILD_RESULT_SCHEMA = (
    "missipy.github.research_scheduler_command_build_result.v1"
)
COMMAND_WRITE_RESULT_SCHEMA = "missipy.scheduler.command_sql_write_result.v1"
INTAKE_REPORT_SCHEMA = "missipy.github.research_scheduler_intake_report.v1"
INTAKE_SCHEMA = "missipy.github.research_scheduler_intake.v1"
INTAKE_PLAN_SCHEMA = "missipy.github_artifact.scheduler_intake_plan.v1"
INTAKE_CANDIDATE_SCHEMA = "missipy.github_artifact.scheduler_intake_candidate.v1"
ROUTE_CANDIDATE_SCHEMA = "missipy.github.research_laboratory_route_candidate.v1"
POLICY_DECISION_SCHEMA = (
    "missipy.github.research_automatic_scheduler_policy_decision.v1"
)

_SHA256_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")


class GitHubResearchSchedulerCommandError(ValueError):
    """Raised when a typed Scheduler command cannot be built safely."""


@dataclass(frozen=True, slots=True)
class SchedulerCommand:
    """Root command contract interpreted by the canonical Scheduler."""

    schema: str
    command_ref: str
    issued_at: str
    priority: int

    def __post_init__(self) -> None:
        if self.schema not in {
            COMMAND_SCHEMA,
            AUTHORIZED_COMMAND_SCHEMA,
            GITHUB_RESEARCH_COMMAND_SCHEMA,
        }:
            raise GitHubResearchSchedulerCommandError(
                "unsupported Scheduler command schema"
            )
        _require_typed_ref("command_ref", self.command_ref)
        _require_utc("issued_at", self.issued_at)
        _require_int_range("priority", self.priority, minimum=0, maximum=100)


@dataclass(frozen=True, slots=True)
class SchedulerAuthorization:
    """Explicit authorization proof composed into an authorized command."""

    schema: str
    policy_decision_id: str
    policy_ref: str
    decision_digest: str
    decision: str
    automatic: bool

    def __post_init__(self) -> None:
        if self.schema != POLICY_DECISION_SCHEMA:
            raise GitHubResearchSchedulerCommandError(
                "unsupported Scheduler authorization schema"
            )
        _require_typed_ref("policy_decision_id", self.policy_decision_id)
        _require_typed_ref("policy_ref", self.policy_ref)
        _require_sha256("decision_digest", self.decision_digest)
        if self.decision != "approve":
            raise GitHubResearchSchedulerCommandError(
                "Scheduler authorization decision must be approve"
            )
        if self.automatic is not True:
            raise GitHubResearchSchedulerCommandError(
                "automatic authorization proof is required by this schema"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "policy_decision_id": self.policy_decision_id,
            "policy_ref": self.policy_ref,
            "decision_digest": self.decision_digest,
            "decision": self.decision,
            "automatic": self.automatic,
        }


@dataclass(frozen=True, slots=True)
class AuthorizedSchedulerCommand(SchedulerCommand):
    """Scheduler command carrying an explicit authorization proof."""

    authorization: SchedulerAuthorization

    def __post_init__(self) -> None:
        SchedulerCommand.__post_init__(self)
        if self.schema not in {
            AUTHORIZED_COMMAND_SCHEMA,
            GITHUB_RESEARCH_COMMAND_SCHEMA,
        }:
            raise GitHubResearchSchedulerCommandError(
                "authorized command schema mismatch"
            )


@dataclass(frozen=True, slots=True)
class GitHubResearchCorrelation:
    """Stable correlation between GitHub, conversation and return path."""

    repository: str
    issue_number: int
    run_id: str
    conversation_ref: str
    return_route_ref: str

    def __post_init__(self) -> None:
        _require_repository(self.repository)
        _require_positive_int("issue_number", self.issue_number)
        _require_run_id(self.run_id)
        _require_typed_ref("conversation_ref", self.conversation_ref)
        _require_typed_ref("return_route_ref", self.return_route_ref)

    def to_mapping(self) -> dict[str, object]:
        return {
            "repository": self.repository,
            "issue_number": self.issue_number,
            "run_id": self.run_id,
            "conversation_ref": self.conversation_ref,
            "return_route_ref": self.return_route_ref,
        }


@dataclass(frozen=True, slots=True)
class ResearchExecutionBudget:
    """Explicit finite resources granted to one research command."""

    max_scheduler_steps: int
    max_specialist_visits: int
    max_wall_time_s: float

    def __post_init__(self) -> None:
        _require_positive_int("max_scheduler_steps", self.max_scheduler_steps)
        _require_positive_int(
            "max_specialist_visits",
            self.max_specialist_visits,
        )
        if self.max_specialist_visits > self.max_scheduler_steps:
            raise GitHubResearchSchedulerCommandError(
                "max_specialist_visits must not exceed max_scheduler_steps"
            )
        if (
            isinstance(self.max_wall_time_s, bool)
            or not isinstance(self.max_wall_time_s, (int, float))
            or not math.isfinite(float(self.max_wall_time_s))
            or self.max_wall_time_s <= 0
        ):
            raise GitHubResearchSchedulerCommandError(
                "max_wall_time_s must be greater than zero"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "max_scheduler_steps": self.max_scheduler_steps,
            "max_specialist_visits": self.max_specialist_visits,
            "max_wall_time_s": float(self.max_wall_time_s),
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchPayload:
    """Research references and admissibility proof."""

    work_package_ref: str
    route_candidate_ref: str
    requested_status: str
    request_mode: str
    parent_event_ref: str
    context_generation: int
    context_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    admissibility_digest: str

    def __post_init__(self) -> None:
        _require_typed_ref("work_package_ref", self.work_package_ref)
        _require_typed_ref("route_candidate_ref", self.route_candidate_ref)
        if self.requested_status != "Recherche":
            raise GitHubResearchSchedulerCommandError(
                "requested_status must be Recherche"
            )
        if self.request_mode not in {"initial", "continuation"}:
            raise GitHubResearchSchedulerCommandError(
                "request_mode must be initial or continuation"
            )
        if self.request_mode == "initial" and self.parent_event_ref:
            raise GitHubResearchSchedulerCommandError(
                "initial research must not carry parent_event_ref"
            )
        if self.request_mode == "continuation":
            _require_typed_ref("parent_event_ref", self.parent_event_ref)
        _require_non_negative_int("context_generation", self.context_generation)
        object.__setattr__(
            self,
            "context_refs",
            _validated_refs("context_refs", self.context_refs),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _validated_refs("evidence_refs", self.evidence_refs),
        )
        if len(self.evidence_refs) != 3:
            raise GitHubResearchSchedulerCommandError(
                "evidence_refs must contain the exact GitHub artifact triplet"
            )
        _require_sha256("admissibility_digest", self.admissibility_digest)

    def to_mapping(self) -> dict[str, object]:
        return {
            "work_package_ref": self.work_package_ref,
            "route_candidate_ref": self.route_candidate_ref,
            "requested_status": self.requested_status,
            "request_mode": self.request_mode,
            "parent_event_ref": self.parent_event_ref,
            "context_generation": self.context_generation,
            "context_refs": list(self.context_refs),
            "evidence_refs": list(self.evidence_refs),
            "admissibility_digest": self.admissibility_digest,
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchSchedulerCommand(AuthorizedSchedulerCommand):
    """Complete typed command for exactly one GitHub research run."""

    correlation: GitHubResearchCorrelation
    research: GitHubResearchPayload
    execution_budget: ResearchExecutionBudget
    route_request: SchedulerRouteRequest
    command_digest: str

    def __post_init__(self) -> None:
        AuthorizedSchedulerCommand.__post_init__(self)
        if self.schema != GITHUB_RESEARCH_COMMAND_SCHEMA:
            raise GitHubResearchSchedulerCommandError(
                "GitHub research command schema mismatch"
            )
        if self.route_request.authorized is not True:
            raise GitHubResearchSchedulerCommandError(
                "route_request must already be authorized"
            )
        if (
            self.route_request.policy_decision_id
            != self.authorization.policy_decision_id
        ):
            raise GitHubResearchSchedulerCommandError(
                "route request and authorization identifiers differ"
            )
        if self.route_request.requested_at != self.issued_at:
            raise GitHubResearchSchedulerCommandError(
                "issued_at must match the authorized route request timestamp"
            )
        _require_sha256("command_digest", self.command_digest)
        expected_ref = (
            "scheduler-command:github-research:"
            f"{_bare_digest(self.command_digest)[:24]}"
        )
        if self.command_ref != expected_ref:
            raise GitHubResearchSchedulerCommandError(
                "command_ref digest mismatch"
            )
        expected_digest = _command_digest(
            issued_at=self.issued_at,
            priority=self.priority,
            authorization=self.authorization,
            correlation=self.correlation,
            research=self.research,
            execution_budget=self.execution_budget,
            route_request=self.route_request,
        )
        if self.command_digest != expected_digest:
            raise GitHubResearchSchedulerCommandError("command_digest mismatch")

    def to_mapping(self) -> dict[str, object]:
        """Boundary projection; this mapping is not the internal authority."""

        return {
            "schema": self.schema,
            "command_ref": self.command_ref,
            "command_digest": self.command_digest,
            "issued_at": self.issued_at,
            "priority": self.priority,
            "authorization": self.authorization.to_mapping(),
            "correlation": self.correlation.to_mapping(),
            "research": self.research.to_mapping(),
            "execution_budget": self.execution_budget.to_mapping(),
            "route_request": self.route_request.to_mapping(),
        }


@dataclass(frozen=True, slots=True)
class SchedulerCommandSqlWriteResult:
    """Result contract for future PostgreSQL command persistence."""

    schema: str
    command_ref: str
    command_digest: str
    authority_ref: str
    inserted: bool
    idempotent_replay: bool

    def __post_init__(self) -> None:
        if self.schema != COMMAND_WRITE_RESULT_SCHEMA:
            raise GitHubResearchSchedulerCommandError(
                "unsupported Scheduler command SQL write result schema"
            )
        _require_typed_ref("command_ref", self.command_ref)
        _require_sha256("command_digest", self.command_digest)
        _require_typed_ref("authority_ref", self.authority_ref)
        if self.inserted == self.idempotent_replay:
            raise GitHubResearchSchedulerCommandError(
                "exactly one SQL write outcome must be true"
            )


@runtime_checkable
class GitHubResearchSchedulerCommandStore(Protocol):
    """PostgreSQL persistence port implemented by the server runtime."""

    def get_command(
        self,
        command_ref: str,
    ) -> GitHubResearchSchedulerCommand | None: ...

    def put_command(
        self,
        command: GitHubResearchSchedulerCommand,
    ) -> SchedulerCommandSqlWriteResult: ...


@dataclass(frozen=True, slots=True)
class GitHubResearchSchedulerCommandBuildResult:
    """Pure build result used by tests and the temporary CLI adapter."""

    schema: str
    valid: bool
    status: str
    issues: tuple[str, ...]
    command: GitHubResearchSchedulerCommand | None = None

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "status": self.status,
            "issues": list(self.issues),
            "command": self.command.to_mapping() if self.command else None,
            "boundaries": {
                "typed_command_created": self.command is not None,
                "legacy_filesystem_handoff_is_canonical": False,
                "filesystem_write_performed": False,
                "sql_write_performed": False,
                "scheduler_started": False,
                "dispatcher_called": False,
                "eventbus_used": False,
                "laboratory_execution_started": False,
                "github_mutation_performed": False,
            },
        }


def build_typed_github_research_scheduler_command(
    *,
    scheduler_intake_report: Mapping[str, Any],
    execution_budget: ResearchExecutionBudget,
) -> GitHubResearchSchedulerCommandBuildResult:
    """Build one complete typed command without persistence or dispatch."""

    try:
        result = _single_authorized_result(scheduler_intake_report)
        candidate = _mapping(result, "research_route_candidate")
        policy = _mapping(result, "policy_decision")
        route_request = SchedulerRouteRequest.from_mapping(
            _mapping(result, "scheduler_route_request")
        )
        intake_plan = _mapping(result, "scheduler_intake_plan")
        intake_candidate = _mapping(intake_plan, "candidate")

        correlation = GitHubResearchCorrelation(
            repository=_text(candidate, "repository"),
            issue_number=_positive_int(candidate, "issue_number"),
            run_id=_run_id(candidate, "run_id"),
            conversation_ref=_text(candidate, "conversation_ref"),
            return_route_ref=_text(candidate, "return_route_ref"),
        )
        research = GitHubResearchPayload(
            work_package_ref=_text(candidate, "work_package_ref"),
            route_candidate_ref=_text(candidate, "route_candidate_ref"),
            requested_status=_text(candidate, "requested_status"),
            request_mode=_text(candidate, "request_mode"),
            parent_event_ref=_optional_text(candidate.get("parent_event_ref")),
            context_generation=_non_negative_int(candidate, "context_generation"),
            context_refs=_refs(candidate, "context_refs"),
            evidence_refs=_refs(candidate, "evidence_refs"),
            admissibility_digest=_text(candidate, "admissibility_digest"),
        )
        _validate_cross_correlation(correlation=correlation, research=research)
        authorization = SchedulerAuthorization(
            schema=_text(policy, "schema"),
            policy_decision_id=_text(policy, "policy_decision_id"),
            policy_ref=_text(policy, "policy_ref"),
            decision_digest=_text(policy, "decision_digest"),
            decision=_text(policy, "decision"),
            automatic=_bool(policy, "automatic"),
        )
        priority = _int_range(
            intake_candidate,
            "priority",
            minimum=0,
            maximum=100,
        )
        _validate_intake_plan(
            intake_plan=intake_plan,
            intake_candidate=intake_candidate,
            correlation=correlation,
            research=research,
            authorization=authorization,
            route_request=route_request,
        )
        digest = _command_digest(
            issued_at=route_request.requested_at,
            priority=priority,
            authorization=authorization,
            correlation=correlation,
            research=research,
            execution_budget=execution_budget,
            route_request=route_request,
        )
        command = GitHubResearchSchedulerCommand(
            schema=GITHUB_RESEARCH_COMMAND_SCHEMA,
            command_ref=(
                "scheduler-command:github-research:"
                f"{_bare_digest(digest)[:24]}"
            ),
            issued_at=route_request.requested_at,
            priority=priority,
            authorization=authorization,
            correlation=correlation,
            research=research,
            execution_budget=execution_budget,
            route_request=route_request,
            command_digest=digest,
        )
        return GitHubResearchSchedulerCommandBuildResult(
            schema=COMMAND_BUILD_RESULT_SCHEMA,
            valid=True,
            status="typed-command-ready-for-sql",
            issues=(),
            command=command,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        return GitHubResearchSchedulerCommandBuildResult(
            schema=COMMAND_BUILD_RESULT_SCHEMA,
            valid=False,
            status="rejected",
            issues=(f"{type(exc).__name__}: {exc}",),
        )


def _single_authorized_result(report: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(report, Mapping):
        raise GitHubResearchSchedulerCommandError(
            "scheduler_intake_report must be an object"
        )
    if report.get("schema") != INTAKE_REPORT_SCHEMA:
        raise GitHubResearchSchedulerCommandError(
            "unsupported intake report schema"
        )
    if (
        report.get("valid") is not True
        or report.get("status") != "scheduler-requests-ready"
    ):
        raise GitHubResearchSchedulerCommandError("intake report is not ready")
    results = report.get("results")
    if not isinstance(results, list) or len(results) != 1:
        raise GitHubResearchSchedulerCommandError(
            "exactly one authorized intake result is required"
        )
    result = results[0]
    if not isinstance(result, Mapping):
        raise GitHubResearchSchedulerCommandError(
            "intake result must be an object"
        )
    if result.get("schema") != INTAKE_SCHEMA:
        raise GitHubResearchSchedulerCommandError(
            "unsupported intake result schema"
        )
    if result.get("valid") is not True or result.get("authorized") is not True:
        raise GitHubResearchSchedulerCommandError(
            "intake result is not authorized"
        )
    if result.get("status") != "scheduler-request-ready":
        raise GitHubResearchSchedulerCommandError("intake result is not ready")
    if result.get("scheduler_dispatch_started") is not False:
        raise GitHubResearchSchedulerCommandError(
            "Scheduler dispatch already started"
        )
    if result.get("laboratory_execution_started") is not False:
        raise GitHubResearchSchedulerCommandError(
            "laboratory execution already started"
        )
    candidate = _mapping(result, "research_route_candidate")
    if candidate.get("schema") != ROUTE_CANDIDATE_SCHEMA:
        raise GitHubResearchSchedulerCommandError(
            "unsupported route candidate schema"
        )
    return result


def _validate_cross_correlation(
    *,
    correlation: GitHubResearchCorrelation,
    research: GitHubResearchPayload,
) -> None:
    repository_key = correlation.repository.replace("/", "-")
    expected_conversation = (
        "github-research-conversation:"
        f"{repository_key}:{correlation.issue_number}:{correlation.run_id}"
    )
    expected_return = (
        "github-issue-return:"
        f"{repository_key}:{correlation.issue_number}"
    )
    expected_context = (
        "github-actions-ready-run:"
        f"{repository_key}:{correlation.run_id}"
    )
    evidence_prefix = (
        "github-actions-artifact:"
        f"{repository_key}:{correlation.run_id}:"
    )
    if correlation.conversation_ref != expected_conversation:
        raise GitHubResearchSchedulerCommandError(
            "conversation_ref does not match repository/issue/run correlation"
        )
    if correlation.return_route_ref != expected_return:
        raise GitHubResearchSchedulerCommandError(
            "return_route_ref does not match repository/issue correlation"
        )
    if expected_context not in research.context_refs:
        raise GitHubResearchSchedulerCommandError(
            "context_refs do not contain the selected GitHub ready run"
        )
    if not all(ref.startswith(evidence_prefix) for ref in research.evidence_refs):
        raise GitHubResearchSchedulerCommandError(
            "evidence_refs do not match repository/run correlation"
        )


def _validate_intake_plan(
    *,
    intake_plan: Mapping[str, Any],
    intake_candidate: Mapping[str, Any],
    correlation: GitHubResearchCorrelation,
    research: GitHubResearchPayload,
    authorization: SchedulerAuthorization,
    route_request: SchedulerRouteRequest,
) -> None:
    if intake_plan.get("schema") != INTAKE_PLAN_SCHEMA:
        raise GitHubResearchSchedulerCommandError(
            "unsupported Scheduler intake plan schema"
        )
    if intake_plan.get("authorized") is not True:
        raise GitHubResearchSchedulerCommandError(
            "Scheduler intake plan must be authorized"
        )
    if intake_plan.get("calls_handle_scheduler_route_request") is not False:
        raise GitHubResearchSchedulerCommandError(
            "Scheduler route handler must not already have been called"
        )
    if intake_candidate.get("schema") != INTAKE_CANDIDATE_SCHEMA:
        raise GitHubResearchSchedulerCommandError(
            "unsupported Scheduler intake candidate schema"
        )
    checks = {
        "repository": correlation.repository,
        "run_id": correlation.run_id,
        "policy_decision_id": authorization.policy_decision_id,
        "dataset_root_ref": research.work_package_ref,
        "observation_ref": research.route_candidate_ref,
        "route_id": route_request.route_id,
        "task_id": route_request.task_id,
        "requested_at": route_request.requested_at,
    }
    for field_name, expected in checks.items():
        if str(intake_candidate.get(field_name, "")) != str(expected):
            raise GitHubResearchSchedulerCommandError(
                f"Scheduler intake candidate {field_name} mismatch"
            )
    if intake_candidate.get("authorized") is not True:
        raise GitHubResearchSchedulerCommandError(
            "Scheduler intake candidate must be authorized"
        )
    if intake_candidate.get("scheduler_route_request_ready") is not True:
        raise GitHubResearchSchedulerCommandError(
            "Scheduler route request is not ready"
        )
    if intake_candidate.get("status") != "planned":
        raise GitHubResearchSchedulerCommandError(
            "Scheduler intake candidate must remain planned"
        )


def _command_digest(
    *,
    issued_at: str,
    priority: int,
    authorization: SchedulerAuthorization,
    correlation: GitHubResearchCorrelation,
    research: GitHubResearchPayload,
    execution_budget: ResearchExecutionBudget,
    route_request: SchedulerRouteRequest,
) -> str:
    parts: list[tuple[str, object]] = [
        ("schema", GITHUB_RESEARCH_COMMAND_SCHEMA),
        ("issued_at", issued_at),
        ("priority", priority),
        ("authorization_schema", authorization.schema),
        ("policy_decision_id", authorization.policy_decision_id),
        ("policy_ref", authorization.policy_ref),
        ("decision_digest", authorization.decision_digest),
        ("decision", authorization.decision),
        ("automatic", authorization.automatic),
        ("repository", correlation.repository),
        ("issue_number", correlation.issue_number),
        ("run_id", correlation.run_id),
        ("conversation_ref", correlation.conversation_ref),
        ("return_route_ref", correlation.return_route_ref),
        ("work_package_ref", research.work_package_ref),
        ("route_candidate_ref", research.route_candidate_ref),
        ("requested_status", research.requested_status),
        ("request_mode", research.request_mode),
        ("parent_event_ref", research.parent_event_ref),
        ("context_generation", research.context_generation),
        ("admissibility_digest", research.admissibility_digest),
        ("max_scheduler_steps", execution_budget.max_scheduler_steps),
        ("max_specialist_visits", execution_budget.max_specialist_visits),
        ("max_wall_time_s", float(execution_budget.max_wall_time_s)),
        ("route_schema", route_request.schema),
        ("route_request_id", route_request.request_id),
        ("route_id", route_request.route_id),
        ("task_id", route_request.task_id),
        ("route_holder", route_request.holder),
        ("route_scope", route_request.scope),
        ("route_authorized", route_request.authorized),
        ("route_policy_decision_id", route_request.policy_decision_id),
        ("route_ttl_seconds", route_request.ttl_seconds),
        ("route_activate", route_request.activate),
        ("route_requested_at", route_request.requested_at),
    ]
    parts.extend(("context_ref", value) for value in research.context_refs)
    parts.extend(("evidence_ref", value) for value in research.evidence_refs)
    return "sha256:" + _length_prefixed_digest(parts)


def _length_prefixed_digest(parts: Sequence[tuple[str, object]]) -> str:
    digest = hashlib.sha256()
    for name, value in parts:
        key = name.encode("utf-8")
        encoded = _scalar_text(value).encode("utf-8")
        digest.update(len(key).to_bytes(4, "big"))
        digest.update(key)
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _scalar_text(value: object) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, float):
        if not math.isfinite(value):
            raise GitHubResearchSchedulerCommandError(
                "digest floats must be finite"
            )
        return value.hex()
    if isinstance(value, (str, int)):
        return str(value)
    raise GitHubResearchSchedulerCommandError(
        f"unsupported digest scalar type: {type(value).__name__}"
    )


def _mapping(value: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    item = value.get(name)
    if not isinstance(item, Mapping):
        raise GitHubResearchSchedulerCommandError(f"{name} must be an object")
    return item


def _text(value: Mapping[str, Any], name: str) -> str:
    text = _optional_text(value.get(name))
    if not text:
        raise GitHubResearchSchedulerCommandError(f"{name} must not be empty")
    return text


def _optional_text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _positive_int(value: Mapping[str, Any], name: str) -> int:
    item = value.get(name)
    _require_positive_int(name, item)
    assert isinstance(item, int)
    return item


def _non_negative_int(value: Mapping[str, Any], name: str) -> int:
    item = value.get(name)
    _require_non_negative_int(name, item)
    assert isinstance(item, int)
    return item


def _int_range(
    value: Mapping[str, Any],
    name: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    item = value.get(name)
    _require_int_range(name, item, minimum=minimum, maximum=maximum)
    assert isinstance(item, int)
    return item


def _bool(value: Mapping[str, Any], name: str) -> bool:
    item = value.get(name)
    if not isinstance(item, bool):
        raise GitHubResearchSchedulerCommandError(f"{name} must be a boolean")
    return item


def _run_id(value: Mapping[str, Any], name: str) -> str:
    item = value.get(name)
    if isinstance(item, bool):
        raise GitHubResearchSchedulerCommandError(f"{name} must be numeric")
    text = str(item).strip()
    _require_run_id(text)
    return text


def _refs(value: Mapping[str, Any], name: str) -> tuple[str, ...]:
    item = value.get(name)
    if not isinstance(item, (list, tuple)):
        raise GitHubResearchSchedulerCommandError(f"{name} must be a sequence")
    return tuple(str(entry) for entry in item)


def _validated_refs(name: str, values: Sequence[str]) -> tuple[str, ...]:
    if not values:
        raise GitHubResearchSchedulerCommandError(f"{name} must not be empty")
    result: list[str] = []
    for value in values:
        _require_typed_ref(name, value)
        if value in result:
            raise GitHubResearchSchedulerCommandError(
                f"{name} must not contain duplicates"
            )
        result.append(value)
    return tuple(result)


def _require_repository(value: str) -> None:
    parts = value.split("/")
    if len(parts) != 2 or not all(parts):
        raise GitHubResearchSchedulerCommandError(
            "repository must use owner/name format"
        )
    for part in parts:
        allowed = part.replace("_", "").replace(".", "").replace("-", "")
        if not allowed.isalnum():
            raise GitHubResearchSchedulerCommandError(
                "repository contains invalid characters"
            )


def _require_run_id(value: str) -> None:
    if not value.isdigit():
        raise GitHubResearchSchedulerCommandError("run_id must be numeric")


def _require_typed_ref(name: str, value: str) -> None:
    if not isinstance(value, str) or _TYPED_REF_RE.fullmatch(value) is None:
        raise GitHubResearchSchedulerCommandError(
            f"{name} must be a non-empty typed reference"
        )


def _require_sha256(name: str, value: str) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise GitHubResearchSchedulerCommandError(
            f"{name} must be a lowercase SHA-256"
        )


def _bare_digest(value: str) -> str:
    return value.removeprefix("sha256:")


def _require_utc(name: str, value: str) -> None:
    if not isinstance(value, str) or "T" not in value or not value.endswith("Z"):
        raise GitHubResearchSchedulerCommandError(
            f"{name} must be a UTC timestamp ending with Z"
        )


def _require_positive_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise GitHubResearchSchedulerCommandError(
            f"{name} must be a positive integer"
        )


def _require_non_negative_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GitHubResearchSchedulerCommandError(
            f"{name} must be a non-negative integer"
        )


def _require_int_range(
    name: str,
    value: object,
    *,
    minimum: int,
    maximum: int,
) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise GitHubResearchSchedulerCommandError(
            f"{name} must be an integer between {minimum} and {maximum}"
        )


__all__ = (
    "AUTHORIZED_COMMAND_SCHEMA",
    "COMMAND_BUILD_RESULT_SCHEMA",
    "COMMAND_SCHEMA",
    "COMMAND_WRITE_RESULT_SCHEMA",
    "GITHUB_RESEARCH_COMMAND_SCHEMA",
    "AuthorizedSchedulerCommand",
    "GitHubResearchCorrelation",
    "GitHubResearchPayload",
    "GitHubResearchSchedulerCommand",
    "GitHubResearchSchedulerCommandBuildResult",
    "GitHubResearchSchedulerCommandError",
    "GitHubResearchSchedulerCommandStore",
    "ResearchExecutionBudget",
    "SchedulerAuthorization",
    "SchedulerCommand",
    "SchedulerCommandSqlWriteResult",
    "build_typed_github_research_scheduler_command",
)
