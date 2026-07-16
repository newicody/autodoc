"""Scheduler-authorized context-impact execution for phase 0287-r7-r8-r6.

The r8-r5 policy module produces effect-free decisions.  This companion module
executes only an explicitly authorized plan through injected Scheduler-owned
ports.  It does not introduce another Scheduler, queue, EventBus, ControlProxy,
or task runtime.

ControlProxy is contacted only when one execution target explicitly requires a
transport transition.  Semantic context revisions remain SQL-authoritative.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import re
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Any, Literal, Protocol

from contracts.event import Event, EventType
from context.context_revision_task_impact_0287 import (
    CONTEXT_IMPACT_PLAN_SCHEMA,
    ContextImpactPlan,
    SchedulerContextImpactDecision,
)

CONTEXT_IMPACT_EXECUTION_VERSION = "0287.r7.r8.r6"
CONTEXT_IMPACT_EXECUTION_AUTHORIZATION_SCHEMA = (
    "missipy.scheduler.context_impact_execution_authorization.v1"
)
CONTEXT_IMPACT_EXECUTION_TARGET_SCHEMA = (
    "missipy.scheduler.context_impact_execution_target.v1"
)
TASK_CONTEXT_RUNTIME_STATE_SCHEMA = "missipy.scheduler.task_context_runtime_state.v1"
TASK_CONTEXT_MUTATION_SCHEMA = "missipy.scheduler.task_context_mutation.v1"
TASK_CONTEXT_MUTATION_RECEIPT_SCHEMA = (
    "missipy.scheduler.task_context_mutation_receipt.v1"
)
CONTEXT_IMPACT_LABORATORY_NOTIFICATION_SCHEMA = (
    "missipy.context.impact_laboratory_notification.v1"
)
CONTEXT_IMPACT_EXECUTION_COMMAND_SCHEMA = (
    "missipy.scheduler.context_impact_execution_command.v1"
)
CONTEXT_IMPACT_EXECUTION_ITEM_SCHEMA = (
    "missipy.scheduler.context_impact_execution_item.v1"
)
CONTEXT_IMPACT_EXECUTION_REPORT_SCHEMA = (
    "missipy.scheduler.context_impact_execution_report.v1"
)
SCHEDULER_ROUTE_REQUEST_SCHEMA = "missipy.scheduler.route_adapter_request.v1"

TaskMutationStatus = Literal["applied", "no_op"]
RouteTransitionStatus = Literal["not_requested", "ready"]

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_JSON_SCALAR_TYPES = (str, int, float, bool, type(None))
_MAX_ITEMS = 100_000
_MAX_TEXT_CHARS = 1_000_000

_STATE_CHANGING_ACTIONS = frozenset(
    {
        "continue_snapshot",
        "notify_only",
        "rebind_before_start",
        "wait_for_checkpoint",
        "rebase_at_checkpoint",
        "restart_task",
        "fork_task",
        "mark_result_stale",
    }
)
_ROUTE_ELIGIBLE_ACTIONS = frozenset(
    {
        "rebind_before_start",
        "rebase_at_checkpoint",
        "restart_task",
        "fork_task",
    }
)


class ContextImpactExecutionError(RuntimeError):
    """Raised when an authorized context-impact execution cannot continue."""


@dataclass(frozen=True, slots=True)
class ContextImpactExecutionAuthorization:
    """Explicit Scheduler/policy authorization for one immutable impact plan."""

    schema: str
    authorization_ref: str
    plan_ref: str
    plan_sha256: str
    scheduler_policy_ref: str
    policy_decision_id: str
    authorized: bool
    authorized_at: str

    def __post_init__(self) -> None:
        if self.schema != CONTEXT_IMPACT_EXECUTION_AUTHORIZATION_SCHEMA:
            raise ContextImpactExecutionError("unsupported execution authorization")
        _require_typed_ref("authorization_ref", self.authorization_ref, "authorization:")
        _require_typed_ref("plan_ref", self.plan_ref, "context-impact-plan:")
        _require_sha256("plan_sha256", self.plan_sha256)
        _require_typed_ref(
            "scheduler_policy_ref",
            self.scheduler_policy_ref,
            "scheduler-policy:",
        )
        _require_typed_ref(
            "policy_decision_id",
            self.policy_decision_id,
            "policy-decision:",
        )
        if self.authorized is not True:
            raise ContextImpactExecutionError("authorized=True is required")
        _require_timestamp("authorized_at", self.authorized_at)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "authorization_ref": self.authorization_ref,
            "plan_ref": self.plan_ref,
            "plan_sha256": self.plan_sha256,
            "scheduler_policy_ref": self.scheduler_policy_ref,
            "policy_decision_id": self.policy_decision_id,
            "authorized": self.authorized,
            "authorized_at": self.authorized_at,
            "scheduler_is_authority": True,
        }


@dataclass(frozen=True, slots=True)
class ContextImpactExecutionTarget:
    """Execution metadata owned by Scheduler, not by the semantic revision."""

    schema: str
    task_ref: str
    expected_state_version: int
    notification_laboratory_refs: tuple[str, ...] = ()
    route_transition_required: bool = False
    route_id: str | None = None
    route_zone: str = "scheduler"
    route_holder: str = "scheduler"
    route_scope: str = "route.write"
    route_ttl_seconds: int = 300

    def __post_init__(self) -> None:
        if self.schema != CONTEXT_IMPACT_EXECUTION_TARGET_SCHEMA:
            raise ContextImpactExecutionError("unsupported execution target schema")
        _require_typed_ref("task_ref", self.task_ref, "specialist-task:")
        _require_nonnegative_int("expected_state_version", self.expected_state_version)
        object.__setattr__(
            self,
            "notification_laboratory_refs",
            _normalize_refs(
                self.notification_laboratory_refs,
                required_prefix="laboratory:",
            ),
        )
        _require_bool("route_transition_required", self.route_transition_required)
        if self.route_transition_required:
            if self.route_id is None:
                raise ContextImpactExecutionError(
                    "route transition requires route_id"
                )
            _require_route_id("route_id", self.route_id)
        elif self.route_id is not None:
            raise ContextImpactExecutionError(
                "route_id is reserved for an explicit route transition"
            )
        _require_identifier("route_zone", self.route_zone)
        _require_identifier("route_holder", self.route_holder)
        _require_scope("route_scope", self.route_scope)
        _require_positive_int("route_ttl_seconds", self.route_ttl_seconds)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "task_ref": self.task_ref,
            "expected_state_version": self.expected_state_version,
            "notification_laboratory_refs": list(
                self.notification_laboratory_refs
            ),
            "route_transition_required": self.route_transition_required,
            "route_id": self.route_id,
            "route_zone": self.route_zone,
            "route_holder": self.route_holder,
            "route_scope": self.route_scope,
            "route_ttl_seconds": self.route_ttl_seconds,
            "controlproxy_is_transport_only": True,
        }


@dataclass(frozen=True, slots=True)
class TaskContextRuntimeState:
    """Minimal Scheduler-owned runtime state used by the reference mutation port."""

    schema: str
    task_ref: str
    plan_ref: str
    execution_ref: str
    execution_state: str
    bound_revision_ref: str
    state_version: int
    specialist_ref: str
    laboratory_ref: str
    conversation_ref: str
    return_route_ref: str
    active_checkpoint_ref: str | None = None
    pending_revision_ref: str | None = None
    result_ref: str | None = None
    stale_against_revision_ref: str | None = None
    route_ref: str | None = None
    predecessor_execution_refs: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != TASK_CONTEXT_RUNTIME_STATE_SCHEMA:
            raise ContextImpactExecutionError("unsupported task runtime state schema")
        _require_typed_ref("task_ref", self.task_ref, "specialist-task:")
        _require_typed_ref("plan_ref", self.plan_ref, "specialist-task-plan:")
        _require_typed_ref("execution_ref", self.execution_ref, "task-execution:")
        if self.execution_state not in {
            "queued",
            "running",
            "checkpointed",
            "completed",
            "failed",
            "cancelled",
        }:
            raise ContextImpactExecutionError("unsupported task execution state")
        _require_typed_ref(
            "bound_revision_ref",
            self.bound_revision_ref,
            "context-revision:",
        )
        _require_nonnegative_int("state_version", self.state_version)
        _require_typed_ref("specialist_ref", self.specialist_ref, "specialist:")
        _require_typed_ref("laboratory_ref", self.laboratory_ref, "laboratory:")
        _require_typed_ref(
            "conversation_ref",
            self.conversation_ref,
            "laboratory-conversation:",
        )
        _require_typed_ref("return_route_ref", self.return_route_ref, "route:")
        if self.active_checkpoint_ref is not None:
            _require_typed_ref(
                "active_checkpoint_ref",
                self.active_checkpoint_ref,
                "checkpoint:",
            )
        if self.pending_revision_ref is not None:
            _require_typed_ref(
                "pending_revision_ref",
                self.pending_revision_ref,
                "context-revision:",
            )
        if self.result_ref is not None:
            _require_typed_ref("result_ref", self.result_ref)
        if self.stale_against_revision_ref is not None:
            _require_typed_ref(
                "stale_against_revision_ref",
                self.stale_against_revision_ref,
                "context-revision:",
            )
        if self.route_ref is not None:
            _require_typed_ref("route_ref", self.route_ref, "route:")
        object.__setattr__(
            self,
            "predecessor_execution_refs",
            _normalize_refs(
                self.predecessor_execution_refs,
                required_prefix="task-execution:",
            ),
        )
        object.__setattr__(self, "metadata", _freeze_json_mapping(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "task_ref": self.task_ref,
            "plan_ref": self.plan_ref,
            "execution_ref": self.execution_ref,
            "execution_state": self.execution_state,
            "bound_revision_ref": self.bound_revision_ref,
            "state_version": self.state_version,
            "specialist_ref": self.specialist_ref,
            "laboratory_ref": self.laboratory_ref,
            "conversation_ref": self.conversation_ref,
            "return_route_ref": self.return_route_ref,
            "active_checkpoint_ref": self.active_checkpoint_ref,
            "pending_revision_ref": self.pending_revision_ref,
            "result_ref": self.result_ref,
            "stale_against_revision_ref": self.stale_against_revision_ref,
            "route_ref": self.route_ref,
            "predecessor_execution_refs": list(self.predecessor_execution_refs),
            "metadata": _thaw_json(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class TaskContextMutation:
    """One idempotent mutation command accepted by a Scheduler-owned task port."""

    schema: str
    mutation_ref: str
    decision_ref: str
    task_ref: str
    action: str
    expected_state_version: int
    expected_execution_state: str
    from_revision_ref: str
    target_revision_ref: str
    scheduler_policy_ref: str
    policy_decision_id: str
    requested_at: str
    checkpoint_ref: str | None = None
    fork_task_ref: str | None = None
    route_ref: str | None = None

    def __post_init__(self) -> None:
        if self.schema != TASK_CONTEXT_MUTATION_SCHEMA:
            raise ContextImpactExecutionError("unsupported task mutation schema")
        _require_typed_ref("mutation_ref", self.mutation_ref, "task-mutation:")
        _require_typed_ref("decision_ref", self.decision_ref, "scheduler-decision:")
        _require_typed_ref("task_ref", self.task_ref, "specialist-task:")
        _require_identifier("action", self.action)
        _require_nonnegative_int("expected_state_version", self.expected_state_version)
        _require_identifier("expected_execution_state", self.expected_execution_state)
        _require_typed_ref(
            "from_revision_ref",
            self.from_revision_ref,
            "context-revision:",
        )
        _require_typed_ref(
            "target_revision_ref",
            self.target_revision_ref,
            "context-revision:",
        )
        _require_typed_ref(
            "scheduler_policy_ref",
            self.scheduler_policy_ref,
            "scheduler-policy:",
        )
        _require_typed_ref(
            "policy_decision_id",
            self.policy_decision_id,
            "policy-decision:",
        )
        _require_timestamp("requested_at", self.requested_at)
        if self.checkpoint_ref is not None:
            _require_typed_ref("checkpoint_ref", self.checkpoint_ref, "checkpoint:")
        if self.fork_task_ref is not None:
            _require_typed_ref(
                "fork_task_ref",
                self.fork_task_ref,
                "specialist-task:",
            )
        if self.route_ref is not None:
            _require_typed_ref("route_ref", self.route_ref, "route:")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "mutation_ref": self.mutation_ref,
            "decision_ref": self.decision_ref,
            "task_ref": self.task_ref,
            "action": self.action,
            "expected_state_version": self.expected_state_version,
            "expected_execution_state": self.expected_execution_state,
            "from_revision_ref": self.from_revision_ref,
            "target_revision_ref": self.target_revision_ref,
            "scheduler_policy_ref": self.scheduler_policy_ref,
            "policy_decision_id": self.policy_decision_id,
            "requested_at": self.requested_at,
            "checkpoint_ref": self.checkpoint_ref,
            "fork_task_ref": self.fork_task_ref,
            "route_ref": self.route_ref,
            "scheduler_authorized": True,
        }


@dataclass(frozen=True, slots=True)
class TaskContextMutationReceipt:
    """Stable result returned by the Scheduler-owned task mutation port."""

    schema: str
    mutation_ref: str
    status: TaskMutationStatus
    task_ref: str
    action: str
    previous_state_version: int
    current_state_version: int
    bound_revision_ref: str
    execution_ref: str
    fork_task_ref: str | None = None
    fork_execution_ref: str | None = None
    replay: bool = False

    def __post_init__(self) -> None:
        if self.schema != TASK_CONTEXT_MUTATION_RECEIPT_SCHEMA:
            raise ContextImpactExecutionError("unsupported task mutation receipt")
        _require_typed_ref("mutation_ref", self.mutation_ref, "task-mutation:")
        if self.status not in {"applied", "no_op"}:
            raise ContextImpactExecutionError("unsupported mutation receipt status")
        _require_typed_ref("task_ref", self.task_ref, "specialist-task:")
        _require_identifier("action", self.action)
        _require_nonnegative_int("previous_state_version", self.previous_state_version)
        _require_nonnegative_int("current_state_version", self.current_state_version)
        _require_typed_ref(
            "bound_revision_ref",
            self.bound_revision_ref,
            "context-revision:",
        )
        _require_typed_ref("execution_ref", self.execution_ref, "task-execution:")
        if self.fork_task_ref is not None:
            _require_typed_ref(
                "fork_task_ref",
                self.fork_task_ref,
                "specialist-task:",
            )
        if self.fork_execution_ref is not None:
            _require_typed_ref(
                "fork_execution_ref",
                self.fork_execution_ref,
                "task-execution:",
            )
        if (self.fork_task_ref is None) != (self.fork_execution_ref is None):
            raise ContextImpactExecutionError(
                "fork task and execution references must be present together"
            )
        _require_bool("replay", self.replay)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "mutation_ref": self.mutation_ref,
            "status": self.status,
            "task_ref": self.task_ref,
            "action": self.action,
            "previous_state_version": self.previous_state_version,
            "current_state_version": self.current_state_version,
            "bound_revision_ref": self.bound_revision_ref,
            "execution_ref": self.execution_ref,
            "fork_task_ref": self.fork_task_ref,
            "fork_execution_ref": self.fork_execution_ref,
            "replay": self.replay,
        }


@dataclass(frozen=True, slots=True)
class ContextImpactLaboratoryNotification:
    """Scheduler-issued notification for a laboratory affected by one decision."""

    schema: str
    notification_ref: str
    plan_ref: str
    decision_ref: str
    task_ref: str
    laboratory_ref: str
    action: str
    from_revision_ref: str
    target_revision_ref: str
    conversation_ref: str
    return_route_ref: str
    occurred_at: str

    def __post_init__(self) -> None:
        if self.schema != CONTEXT_IMPACT_LABORATORY_NOTIFICATION_SCHEMA:
            raise ContextImpactExecutionError("unsupported laboratory notification")
        _require_typed_ref(
            "notification_ref",
            self.notification_ref,
            "context-impact-notification:",
        )
        _require_typed_ref("plan_ref", self.plan_ref, "context-impact-plan:")
        _require_typed_ref("decision_ref", self.decision_ref, "scheduler-decision:")
        _require_typed_ref("task_ref", self.task_ref, "specialist-task:")
        _require_typed_ref("laboratory_ref", self.laboratory_ref, "laboratory:")
        _require_identifier("action", self.action)
        _require_typed_ref(
            "from_revision_ref",
            self.from_revision_ref,
            "context-revision:",
        )
        _require_typed_ref(
            "target_revision_ref",
            self.target_revision_ref,
            "context-revision:",
        )
        _require_typed_ref(
            "conversation_ref",
            self.conversation_ref,
            "laboratory-conversation:",
        )
        _require_typed_ref("return_route_ref", self.return_route_ref, "route:")
        _require_timestamp("occurred_at", self.occurred_at)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "notification_ref": self.notification_ref,
            "plan_ref": self.plan_ref,
            "decision_ref": self.decision_ref,
            "task_ref": self.task_ref,
            "laboratory_ref": self.laboratory_ref,
            "action": self.action,
            "from_revision_ref": self.from_revision_ref,
            "target_revision_ref": self.target_revision_ref,
            "conversation_ref": self.conversation_ref,
            "return_route_ref": self.return_route_ref,
            "occurred_at": self.occurred_at,
            "scheduler_issued": True,
            "semantic_authority_claimed": False,
        }


@dataclass(frozen=True, slots=True)
class ContextImpactExecutionCommand:
    """Immutable command handled on the existing Scheduler/Dispatcher boundary."""

    schema: str
    command_ref: str
    plan: ContextImpactPlan
    authorization: ContextImpactExecutionAuthorization
    targets: tuple[ContextImpactExecutionTarget, ...]
    requested_at: str

    def __post_init__(self) -> None:
        if self.schema != CONTEXT_IMPACT_EXECUTION_COMMAND_SCHEMA:
            raise ContextImpactExecutionError("unsupported execution command")
        _require_typed_ref(
            "command_ref",
            self.command_ref,
            "context-impact-execution:",
        )
        if not isinstance(self.plan, ContextImpactPlan):
            raise ContextImpactExecutionError("plan must be a ContextImpactPlan")
        if self.plan.schema != CONTEXT_IMPACT_PLAN_SCHEMA:
            raise ContextImpactExecutionError("unsupported impact plan")
        if not isinstance(
            self.authorization,
            ContextImpactExecutionAuthorization,
        ):
            raise ContextImpactExecutionError("authorization contract is required")
        if self.authorization.plan_ref != self.plan.plan_ref:
            raise ContextImpactExecutionError("authorization plan_ref mismatch")
        if self.authorization.plan_sha256 != compute_plan_sha256(self.plan):
            raise ContextImpactExecutionError("authorization plan digest mismatch")
        policy_refs = {item.scheduler_policy_ref for item in self.plan.decisions}
        if policy_refs != {self.authorization.scheduler_policy_ref}:
            raise ContextImpactExecutionError(
                "all decisions must match the authorized Scheduler policy"
            )
        targets = tuple(self.targets)
        if len(targets) > _MAX_ITEMS:
            raise ContextImpactExecutionError("too many execution targets")
        if not all(isinstance(item, ContextImpactExecutionTarget) for item in targets):
            raise ContextImpactExecutionError(
                "targets must contain ContextImpactExecutionTarget values"
            )
        decision_refs = {item.task_ref for item in self.plan.decisions}
        target_refs = {item.task_ref for item in targets}
        if len(target_refs) != len(targets):
            raise ContextImpactExecutionError("execution target task_refs must be unique")
        if target_refs != decision_refs:
            raise ContextImpactExecutionError(
                "execution targets must match impact plan task_refs exactly"
            )
        target_by_task = {item.task_ref: item for item in targets}
        for decision in self.plan.decisions:
            target = target_by_task[decision.task_ref]
            if target.route_transition_required and decision.action not in (
                _ROUTE_ELIGIBLE_ACTIONS
            ):
                raise ContextImpactExecutionError(
                    "route transition is not valid for this impact action"
                )
        object.__setattr__(self, "targets", tuple(sorted(targets, key=lambda x: x.task_ref)))
        _require_timestamp("requested_at", self.requested_at)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "command_ref": self.command_ref,
            "plan": self.plan.to_mapping(),
            "authorization": self.authorization.to_mapping(),
            "targets": [item.to_mapping() for item in self.targets],
            "requested_at": self.requested_at,
            "scheduler_command": True,
        }


@dataclass(frozen=True, slots=True)
class ContextImpactExecutionItem:
    """One executed decision with route and notification evidence."""

    schema: str
    decision_ref: str
    task_ref: str
    action: str
    mutation_receipt: TaskContextMutationReceipt
    route_status: RouteTransitionStatus
    route_ref: str | None
    notification_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema != CONTEXT_IMPACT_EXECUTION_ITEM_SCHEMA:
            raise ContextImpactExecutionError("unsupported execution item")
        _require_typed_ref("decision_ref", self.decision_ref, "scheduler-decision:")
        _require_typed_ref("task_ref", self.task_ref, "specialist-task:")
        _require_identifier("action", self.action)
        if not isinstance(self.mutation_receipt, TaskContextMutationReceipt):
            raise ContextImpactExecutionError("mutation receipt is required")
        if self.route_status not in {"not_requested", "ready"}:
            raise ContextImpactExecutionError("unsupported route status")
        if self.route_status == "ready":
            if self.route_ref is None:
                raise ContextImpactExecutionError("ready route requires route_ref")
            _require_typed_ref("route_ref", self.route_ref, "route:")
        elif self.route_ref is not None:
            raise ContextImpactExecutionError(
                "route_ref is reserved for a ready route transition"
            )
        object.__setattr__(
            self,
            "notification_refs",
            _normalize_refs(
                self.notification_refs,
                required_prefix="context-impact-notification:",
            ),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "decision_ref": self.decision_ref,
            "task_ref": self.task_ref,
            "action": self.action,
            "mutation_receipt": self.mutation_receipt.to_mapping(),
            "route_status": self.route_status,
            "route_ref": self.route_ref,
            "notification_refs": list(self.notification_refs),
        }


@dataclass(frozen=True, slots=True)
class ContextImpactExecutionReport:
    """Observable result of one Scheduler-authorized execution command."""

    schema: str
    report_ref: str
    command_ref: str
    plan_ref: str
    policy_decision_id: str
    items: tuple[ContextImpactExecutionItem, ...]
    completed_at: str

    def __post_init__(self) -> None:
        if self.schema != CONTEXT_IMPACT_EXECUTION_REPORT_SCHEMA:
            raise ContextImpactExecutionError("unsupported execution report")
        _require_typed_ref("report_ref", self.report_ref, "context-impact-report:")
        _require_typed_ref(
            "command_ref",
            self.command_ref,
            "context-impact-execution:",
        )
        _require_typed_ref("plan_ref", self.plan_ref, "context-impact-plan:")
        _require_typed_ref(
            "policy_decision_id",
            self.policy_decision_id,
            "policy-decision:",
        )
        items = tuple(self.items)
        if not all(isinstance(item, ContextImpactExecutionItem) for item in items):
            raise ContextImpactExecutionError(
                "items must contain ContextImpactExecutionItem values"
            )
        task_refs = tuple(item.task_ref for item in items)
        if len(task_refs) != len(set(task_refs)):
            raise ContextImpactExecutionError("execution report task_refs must be unique")
        object.__setattr__(self, "items", items)
        _require_timestamp("completed_at", self.completed_at)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "report_ref": self.report_ref,
            "command_ref": self.command_ref,
            "plan_ref": self.plan_ref,
            "policy_decision_id": self.policy_decision_id,
            "items": [item.to_mapping() for item in self.items],
            "completed_at": self.completed_at,
            "scheduler_executed": True,
            "eventbus_is_observation_only": True,
            "controlproxy_is_transport_only": True,
            "sql_revision_is_authority": True,
        }


class SchedulerTaskMutationPort(Protocol):
    """Scheduler-owned task state boundary used by the execution adapter."""

    def apply(self, mutation: TaskContextMutation) -> TaskContextMutationReceipt:
        """Apply one idempotent task mutation."""


EventPublisher = Callable[[Event], object | Awaitable[object]]
RouteRequester = Callable[[Mapping[str, Any]], object | Awaitable[object]]


class InMemorySchedulerTaskMutationPort:
    """Deterministic reference port for tests and local composition only."""

    def __init__(self, states: Sequence[TaskContextRuntimeState]) -> None:
        self._states = {item.task_ref: item for item in states}
        if len(self._states) != len(tuple(states)):
            raise ContextImpactExecutionError("initial task states must be unique")
        self._receipts: dict[str, tuple[str, TaskContextMutationReceipt]] = {}

    def state(self, task_ref: str) -> TaskContextRuntimeState:
        try:
            return self._states[task_ref]
        except KeyError as exc:
            raise ContextImpactExecutionError(f"unknown task state: {task_ref}") from exc

    def apply(self, mutation: TaskContextMutation) -> TaskContextMutationReceipt:
        digest = _sha256_mapping(mutation.to_mapping())
        previous = self._receipts.get(mutation.mutation_ref)
        if previous is not None:
            stored_digest, stored_receipt = previous
            if stored_digest != digest:
                raise ContextImpactExecutionError("task mutation idempotency collision")
            return replace(stored_receipt, replay=True)
        state = self.state(mutation.task_ref)
        _validate_mutation_against_state(mutation, state)
        updated, forked, status = _apply_mutation_to_state(mutation, state)
        self._states[state.task_ref] = updated
        if forked is not None:
            if forked.task_ref in self._states:
                raise ContextImpactExecutionError("fork task state already exists")
            self._states[forked.task_ref] = forked
        receipt = TaskContextMutationReceipt(
            schema=TASK_CONTEXT_MUTATION_RECEIPT_SCHEMA,
            mutation_ref=mutation.mutation_ref,
            status=status,
            task_ref=updated.task_ref,
            action=mutation.action,
            previous_state_version=state.state_version,
            current_state_version=updated.state_version,
            bound_revision_ref=updated.bound_revision_ref,
            execution_ref=updated.execution_ref,
            fork_task_ref=forked.task_ref if forked is not None else None,
            fork_execution_ref=forked.execution_ref if forked is not None else None,
            replay=False,
        )
        self._receipts[mutation.mutation_ref] = (digest, receipt)
        return receipt


async def execute_context_impact_command(
    *,
    command: ContextImpactExecutionCommand,
    task_mutation_port: SchedulerTaskMutationPort,
    event_bus_publish: EventPublisher,
    scheduler_emit: EventPublisher,
    route_requester: RouteRequester | None = None,
) -> ContextImpactExecutionReport:
    """Execute an authorized impact plan through existing injected boundaries."""

    target_by_task = {item.task_ref: item for item in command.targets}
    items: list[ContextImpactExecutionItem] = []
    for decision in command.plan.decisions:
        target = target_by_task[decision.task_ref]
        route_ref = await _prepare_route_if_required(
            command=command,
            decision=decision,
            target=target,
            route_requester=route_requester,
        )
        mutation = build_task_context_mutation(
            command=command,
            decision=decision,
            target=target,
            route_ref=route_ref,
        )
        receipt = task_mutation_port.apply(mutation)
        notifications = build_laboratory_notifications(
            command=command,
            decision=decision,
            receipt=receipt,
            target=target,
            task_state=_read_task_state(task_mutation_port, receipt.task_ref),
        )
        for notification in notifications:
            await _call_maybe_async(
                scheduler_emit,
                Event(
                    EventType.LABORATORY_CONTEXT_UPDATE,
                    source="scheduler.context-impact",
                    dest=notification.laboratory_ref,
                    payload=notification,
                    correlation_id=command.command_ref,
                    metadata=MappingProxyType(
                        {
                            "notification_ref": notification.notification_ref,
                            "plan_ref": command.plan.plan_ref,
                        }
                    ),
                ),
            )
        item = ContextImpactExecutionItem(
            schema=CONTEXT_IMPACT_EXECUTION_ITEM_SCHEMA,
            decision_ref=decision.decision_ref,
            task_ref=decision.task_ref,
            action=decision.action,
            mutation_receipt=receipt,
            route_status="ready" if route_ref is not None else "not_requested",
            route_ref=route_ref,
            notification_refs=tuple(item.notification_ref for item in notifications),
        )
        items.append(item)
    report_digest = _sha256_mapping(
        {
            "command_ref": command.command_ref,
            "items": [item.to_mapping() for item in items],
        }
    )
    report = ContextImpactExecutionReport(
        schema=CONTEXT_IMPACT_EXECUTION_REPORT_SCHEMA,
        report_ref=f"context-impact-report:{report_digest[:24]}",
        command_ref=command.command_ref,
        plan_ref=command.plan.plan_ref,
        policy_decision_id=command.authorization.policy_decision_id,
        items=tuple(items),
        completed_at=command.requested_at,
    )
    await _call_maybe_async(
        event_bus_publish,
        Event(
            EventType.CONTEXT_IMPACT_EXECUTION_RESULT,
            source="scheduler.context-impact",
            dest="observers",
            payload=report,
            correlation_id=command.command_ref,
            metadata=MappingProxyType(
                {
                    "report_ref": report.report_ref,
                    "plan_ref": report.plan_ref,
                }
            ),
        ),
    )
    return report


@dataclass(slots=True)
class SchedulerContextImpactExecutionHandler:
    """Dispatcher handler registered on the existing Scheduler boundary."""

    task_mutation_port: SchedulerTaskMutationPort
    event_bus_publish: EventPublisher
    scheduler_emit: EventPublisher
    route_requester: RouteRequester | None = None

    async def handle(self, event: Event) -> ContextImpactExecutionReport:
        if event.type is not EventType.CONTEXT_IMPACT_EXECUTION:
            raise ContextImpactExecutionError("unexpected event type")
        if not isinstance(event.payload, ContextImpactExecutionCommand):
            raise ContextImpactExecutionError(
                "context impact execution payload must be a command"
            )
        return await execute_context_impact_command(
            command=event.payload,
            task_mutation_port=self.task_mutation_port,
            event_bus_publish=self.event_bus_publish,
            scheduler_emit=self.scheduler_emit,
            route_requester=self.route_requester,
        )


def build_task_context_mutation(
    *,
    command: ContextImpactExecutionCommand,
    decision: SchedulerContextImpactDecision,
    target: ContextImpactExecutionTarget,
    route_ref: str | None,
) -> TaskContextMutation:
    payload = {
        "command_ref": command.command_ref,
        "decision_ref": decision.decision_ref,
        "task_ref": decision.task_ref,
        "action": decision.action,
        "expected_state_version": target.expected_state_version,
        "policy_decision_id": command.authorization.policy_decision_id,
    }
    digest = _sha256_mapping(payload)
    return TaskContextMutation(
        schema=TASK_CONTEXT_MUTATION_SCHEMA,
        mutation_ref=f"task-mutation:{digest[:24]}",
        decision_ref=decision.decision_ref,
        task_ref=decision.task_ref,
        action=decision.action,
        expected_state_version=target.expected_state_version,
        expected_execution_state=decision.execution_state,
        from_revision_ref=decision.from_revision_ref,
        target_revision_ref=decision.target_revision_ref,
        scheduler_policy_ref=decision.scheduler_policy_ref,
        policy_decision_id=command.authorization.policy_decision_id,
        requested_at=command.requested_at,
        checkpoint_ref=decision.checkpoint_ref,
        fork_task_ref=decision.fork_task_ref,
        route_ref=route_ref,
    )


def build_laboratory_notifications(
    *,
    command: ContextImpactExecutionCommand,
    decision: SchedulerContextImpactDecision,
    receipt: TaskContextMutationReceipt,
    target: ContextImpactExecutionTarget,
    task_state: TaskContextRuntimeState | None,
) -> tuple[ContextImpactLaboratoryNotification, ...]:
    if task_state is None:
        if target.notification_laboratory_refs:
            raise ContextImpactExecutionError(
                "task state readback is required for laboratory notifications"
            )
        return ()
    notifications: list[ContextImpactLaboratoryNotification] = []
    for laboratory_ref in target.notification_laboratory_refs:
        digest = _sha256_mapping(
            {
                "plan_ref": command.plan.plan_ref,
                "decision_ref": decision.decision_ref,
                "task_ref": decision.task_ref,
                "laboratory_ref": laboratory_ref,
                "mutation_ref": receipt.mutation_ref,
            }
        )
        notifications.append(
            ContextImpactLaboratoryNotification(
                schema=CONTEXT_IMPACT_LABORATORY_NOTIFICATION_SCHEMA,
                notification_ref=f"context-impact-notification:{digest[:24]}",
                plan_ref=command.plan.plan_ref,
                decision_ref=decision.decision_ref,
                task_ref=decision.task_ref,
                laboratory_ref=laboratory_ref,
                action=decision.action,
                from_revision_ref=decision.from_revision_ref,
                target_revision_ref=decision.target_revision_ref,
                conversation_ref=task_state.conversation_ref,
                return_route_ref=task_state.return_route_ref,
                occurred_at=command.requested_at,
            )
        )
    return tuple(notifications)


def build_context_impact_execution_authorization(
    *,
    plan: ContextImpactPlan,
    scheduler_policy_ref: str,
    policy_decision_id: str,
    authorized_at: str,
) -> ContextImpactExecutionAuthorization:
    plan_sha256 = compute_plan_sha256(plan)
    digest = _sha256_mapping(
        {
            "plan_ref": plan.plan_ref,
            "plan_sha256": plan_sha256,
            "scheduler_policy_ref": scheduler_policy_ref,
            "policy_decision_id": policy_decision_id,
        }
    )
    return ContextImpactExecutionAuthorization(
        schema=CONTEXT_IMPACT_EXECUTION_AUTHORIZATION_SCHEMA,
        authorization_ref=f"authorization:{digest[:24]}",
        plan_ref=plan.plan_ref,
        plan_sha256=plan_sha256,
        scheduler_policy_ref=scheduler_policy_ref,
        policy_decision_id=policy_decision_id,
        authorized=True,
        authorized_at=authorized_at,
    )


def build_context_impact_execution_command(
    *,
    plan: ContextImpactPlan,
    authorization: ContextImpactExecutionAuthorization,
    targets: Sequence[ContextImpactExecutionTarget],
    requested_at: str,
) -> ContextImpactExecutionCommand:
    digest = _sha256_mapping(
        {
            "plan_ref": plan.plan_ref,
            "authorization_ref": authorization.authorization_ref,
            "targets": [item.to_mapping() for item in targets],
            "requested_at": requested_at,
        }
    )
    return ContextImpactExecutionCommand(
        schema=CONTEXT_IMPACT_EXECUTION_COMMAND_SCHEMA,
        command_ref=f"context-impact-execution:{digest[:24]}",
        plan=plan,
        authorization=authorization,
        targets=tuple(targets),
        requested_at=requested_at,
    )


def compute_plan_sha256(plan: ContextImpactPlan) -> str:
    if not isinstance(plan, ContextImpactPlan):
        raise ContextImpactExecutionError("plan must be a ContextImpactPlan")
    return _sha256_mapping(plan.to_mapping())


async def _prepare_route_if_required(
    *,
    command: ContextImpactExecutionCommand,
    decision: SchedulerContextImpactDecision,
    target: ContextImpactExecutionTarget,
    route_requester: RouteRequester | None,
) -> str | None:
    if not target.route_transition_required:
        return None
    if route_requester is None:
        raise ContextImpactExecutionError(
            "route transition requires the existing Scheduler route adapter"
        )
    assert target.route_id is not None
    request_id = _route_request_id(command.command_ref, decision.decision_ref)
    task_id = decision.fork_task_ref or decision.task_ref
    request = {
        "schema": SCHEDULER_ROUTE_REQUEST_SCHEMA,
        "request_id": request_id,
        "route_id": target.route_id,
        "task_id": task_id,
        "holder": target.route_holder,
        "scope": target.route_scope,
        "authorized": True,
        "policy_decision_id": command.authorization.policy_decision_id,
        "ttl_seconds": target.route_ttl_seconds,
        "activate": True,
        "requested_at": command.requested_at,
        "zone": target.route_zone,
    }
    reply = await _call_maybe_async(route_requester, request)
    if not isinstance(reply, Mapping):
        if hasattr(reply, "to_mapping"):
            reply = reply.to_mapping()
        else:
            raise ContextImpactExecutionError("route adapter reply must be a mapping")
    if reply.get("status") != "ready":
        raise ContextImpactExecutionError("route adapter did not return ready")
    if reply.get("policy_decision_id") != command.authorization.policy_decision_id:
        raise ContextImpactExecutionError("route adapter policy decision mismatch")
    route_handle = reply.get("route_handle")
    if not isinstance(route_handle, str) or not route_handle:
        raise ContextImpactExecutionError("route adapter reply lacks route_handle")
    return f"route:{route_handle}"


def _route_request_id(command_ref: str, decision_ref: str) -> str:
    digest = hashlib.sha256(f"{command_ref}|{decision_ref}".encode()).hexdigest()
    return f"context-impact-{digest[:24]}"


def _validate_mutation_against_state(
    mutation: TaskContextMutation,
    state: TaskContextRuntimeState,
) -> None:
    if state.state_version != mutation.expected_state_version:
        raise ContextImpactExecutionError("task state version changed")
    if state.execution_state != mutation.expected_execution_state:
        raise ContextImpactExecutionError("task execution state changed")
    if state.bound_revision_ref != mutation.from_revision_ref:
        raise ContextImpactExecutionError("task context revision changed")
    if mutation.action == "rebase_at_checkpoint":
        if state.active_checkpoint_ref != mutation.checkpoint_ref:
            raise ContextImpactExecutionError("task checkpoint changed")
    if mutation.action == "mark_result_stale" and state.result_ref is None:
        raise ContextImpactExecutionError("completed result_ref is required")


def _apply_mutation_to_state(
    mutation: TaskContextMutation,
    state: TaskContextRuntimeState,
) -> tuple[TaskContextRuntimeState, TaskContextRuntimeState | None, TaskMutationStatus]:
    action = mutation.action
    if action == "no_action":
        return state, None, "no_op"
    if action not in _STATE_CHANGING_ACTIONS:
        raise ContextImpactExecutionError("unsupported task context mutation action")
    next_version = state.state_version + 1
    route_ref = mutation.route_ref or state.route_ref
    if action == "continue_snapshot":
        return (
            replace(
                state,
                state_version=next_version,
                stale_against_revision_ref=mutation.target_revision_ref,
                route_ref=route_ref,
            ),
            None,
            "applied",
        )
    if action == "notify_only":
        return (
            replace(
                state,
                state_version=next_version,
                pending_revision_ref=mutation.target_revision_ref,
                stale_against_revision_ref=mutation.target_revision_ref,
                route_ref=route_ref,
            ),
            None,
            "applied",
        )
    if action == "rebind_before_start":
        return (
            replace(
                state,
                state_version=next_version,
                bound_revision_ref=mutation.target_revision_ref,
                pending_revision_ref=None,
                stale_against_revision_ref=None,
                route_ref=route_ref,
            ),
            None,
            "applied",
        )
    if action == "wait_for_checkpoint":
        return (
            replace(
                state,
                state_version=next_version,
                pending_revision_ref=mutation.target_revision_ref,
                stale_against_revision_ref=mutation.target_revision_ref,
            ),
            None,
            "applied",
        )
    if action == "rebase_at_checkpoint":
        return (
            replace(
                state,
                state_version=next_version,
                bound_revision_ref=mutation.target_revision_ref,
                pending_revision_ref=None,
                stale_against_revision_ref=None,
                route_ref=route_ref,
            ),
            None,
            "applied",
        )
    if action == "restart_task":
        execution_ref = _derived_execution_ref(mutation, "restart")
        return (
            replace(
                state,
                execution_ref=execution_ref,
                execution_state="queued",
                bound_revision_ref=mutation.target_revision_ref,
                state_version=next_version,
                active_checkpoint_ref=None,
                pending_revision_ref=None,
                stale_against_revision_ref=None,
                route_ref=route_ref,
                predecessor_execution_refs=(
                    state.predecessor_execution_refs + (state.execution_ref,)
                ),
            ),
            None,
            "applied",
        )
    if action == "fork_task":
        if mutation.fork_task_ref is None:
            raise ContextImpactExecutionError("fork mutation requires fork_task_ref")
        fork_execution_ref = _derived_execution_ref(mutation, "fork")
        source = replace(
            state,
            state_version=next_version,
            stale_against_revision_ref=mutation.target_revision_ref,
        )
        forked = TaskContextRuntimeState(
            schema=TASK_CONTEXT_RUNTIME_STATE_SCHEMA,
            task_ref=mutation.fork_task_ref,
            plan_ref=state.plan_ref,
            execution_ref=fork_execution_ref,
            execution_state="queued",
            bound_revision_ref=mutation.target_revision_ref,
            state_version=0,
            specialist_ref=state.specialist_ref,
            laboratory_ref=state.laboratory_ref,
            conversation_ref=state.conversation_ref,
            return_route_ref=state.return_route_ref,
            route_ref=route_ref,
            predecessor_execution_refs=(state.execution_ref,),
            metadata={
                **_thaw_json(state.metadata),
                "forked_from_task_ref": state.task_ref,
            },
        )
        return source, forked, "applied"
    if action == "mark_result_stale":
        return (
            replace(
                state,
                state_version=next_version,
                stale_against_revision_ref=mutation.target_revision_ref,
            ),
            None,
            "applied",
        )
    raise ContextImpactExecutionError("unreachable task context mutation action")


def _derived_execution_ref(mutation: TaskContextMutation, purpose: str) -> str:
    digest = _sha256_mapping(
        {
            "mutation_ref": mutation.mutation_ref,
            "purpose": purpose,
            "target_revision_ref": mutation.target_revision_ref,
        }
    )
    return f"task-execution:{purpose}-{digest[:24]}"


def _read_task_state(
    port: SchedulerTaskMutationPort,
    task_ref: str,
) -> TaskContextRuntimeState | None:
    reader = getattr(port, "state", None)
    if not callable(reader):
        return None
    value = reader(task_ref)
    if not isinstance(value, TaskContextRuntimeState):
        raise ContextImpactExecutionError("task state readback has invalid type")
    return value


async def _call_maybe_async(function: Callable[..., object], value: object) -> object:
    result = function(value)
    if inspect.isawaitable(result):
        return await result
    return result


def _require_typed_ref(name: str, value: str, required_prefix: str | None = None) -> None:
    _require_text(name, value)
    if not _TYPED_REF_RE.fullmatch(value):
        raise ContextImpactExecutionError(f"{name} must be a typed reference")
    if required_prefix is not None and not value.startswith(required_prefix):
        raise ContextImpactExecutionError(f"{name} must start with {required_prefix}")


def _normalize_refs(
    values: Sequence[str],
    *,
    required_prefix: str | None = None,
) -> tuple[str, ...]:
    normalized = tuple(values)
    if len(normalized) > _MAX_ITEMS:
        raise ContextImpactExecutionError("too many references")
    for value in normalized:
        _require_typed_ref("reference", value, required_prefix)
    if len(normalized) != len(set(normalized)):
        raise ContextImpactExecutionError("references must be unique")
    return normalized


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContextImpactExecutionError(f"{name} must not be empty")
    if len(value) > _MAX_TEXT_CHARS:
        raise ContextImpactExecutionError(f"{name} is too large")


def _require_identifier(name: str, value: str) -> None:
    _require_text(name, value)
    if not re.fullmatch(r"[A-Za-z0-9_.:-]+", value):
        raise ContextImpactExecutionError(f"{name} contains invalid characters")


def _require_route_id(name: str, value: str) -> None:
    _require_identifier(name, value)
    if "/" in value or "\\" in value or ".." in value:
        raise ContextImpactExecutionError(f"{name} must not contain traversal")


def _require_scope(name: str, value: str) -> None:
    _require_identifier(name, value)
    if "." not in value:
        raise ContextImpactExecutionError(f"{name} must use subsystem.permission")


def _require_timestamp(name: str, value: str) -> None:
    _require_text(name, value)
    if "T" not in value or not value.endswith("Z"):
        raise ContextImpactExecutionError(f"{name} must be a UTC timestamp")


def _require_sha256(name: str, value: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ContextImpactExecutionError(f"{name} must be a lowercase SHA-256")


def _require_bool(name: str, value: bool) -> None:
    if not isinstance(value, bool):
        raise ContextImpactExecutionError(f"{name} must be a boolean")


def _require_nonnegative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ContextImpactExecutionError(f"{name} must be a non-negative integer")


def _require_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ContextImpactExecutionError(f"{name} must be a positive integer")


def _freeze_json_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContextImpactExecutionError("metadata must be a mapping")
    normalized = _normalize_json(dict(value))
    assert isinstance(normalized, dict)
    return MappingProxyType(normalized)


def _normalize_json(value: Any) -> Any:
    if isinstance(value, _JSON_SCALAR_TYPES):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_json(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return tuple(_normalize_json(item) for item in value)
    raise ContextImpactExecutionError("value is not JSON compatible")


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _sha256_mapping(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        _thaw_json(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
