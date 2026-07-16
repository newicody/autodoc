"""Context revision impact policy for phase 0287-r7-r8-r5.

The module binds specialist tasks to one SQL-authoritative semantic context
revision and computes deterministic impact proposals when an accepted child
revision appears.  It does not mutate a task, submit Scheduler work, publish an
EventBus message, alter a ControlProxy route, or write SQL/Qdrant state.

Only the existing Scheduler may authorize and execute the proposed action.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal
import hashlib
import json
import re

from context.context_revision_sql_authority_0287 import (
    ContextRevision,
    ContextRevisionMembership,
)
from context.specialist_multitask_model_0287 import SpecialistTaskRequest

CONTEXT_TASK_IMPACT_VERSION = "0287.r7.r8.r5"
CONTEXT_REVISION_CHANGE_SET_SCHEMA = "missipy.context.revision_change_set.v1"
TASK_CONTEXT_BINDING_SCHEMA = "missipy.context.task_binding.v1"
TASK_CONTEXT_IMPACT_ASSESSMENT_SCHEMA = (
    "missipy.context.task_impact_assessment.v1"
)
SCHEDULER_CONTEXT_IMPACT_DECISION_SCHEMA = (
    "missipy.scheduler.context_impact_decision.v1"
)
CONTEXT_IMPACT_PLAN_SCHEMA = "missipy.scheduler.context_impact_plan.v1"

TaskContextUpdatePolicy = Literal[
    "snapshot",
    "checkpoint_rebase",
    "restart_on_material_change",
    "fork_on_material_change",
    "notify_only",
    "ignore_noncritical",
]
TaskExecutionState = Literal[
    "queued",
    "running",
    "checkpointed",
    "completed",
    "failed",
    "cancelled",
]
TaskContextImpactAction = Literal[
    "no_action",
    "continue_snapshot",
    "notify_only",
    "rebind_before_start",
    "wait_for_checkpoint",
    "rebase_at_checkpoint",
    "restart_task",
    "fork_task",
    "mark_result_stale",
]

_UPDATE_POLICIES = frozenset(
    {
        "snapshot",
        "checkpoint_rebase",
        "restart_on_material_change",
        "fork_on_material_change",
        "notify_only",
        "ignore_noncritical",
    }
)
_EXECUTION_STATES = frozenset(
    {"queued", "running", "checkpointed", "completed", "failed", "cancelled"}
)
_ACTIONS = frozenset(
    {
        "no_action",
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
_SIGNIFICANCE_ORDER = {"minor": 0, "material": 1, "critical": 2}
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_JSON_SCALAR_TYPES = (str, int, float, bool, type(None))
_MAX_ITEMS = 100_000
_MAX_TEXT_CHARS = 1_000_000


class ContextTaskImpactError(ValueError):
    """Raised when one context-impact contract is incoherent."""


@dataclass(frozen=True, slots=True)
class ContextRevisionChangeSet:
    """Reference-only semantic delta between accepted context revisions."""

    schema: str
    change_ref: str
    context_ref: str
    from_revision_ref: str
    to_revision_ref: str
    significance: str
    added_refs: tuple[str, ...] = ()
    superseded_refs: tuple[str, ...] = ()
    invalidated_refs: tuple[str, ...] = ()
    replacement_pairs: tuple[tuple[str, str], ...] = ()
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema != CONTEXT_REVISION_CHANGE_SET_SCHEMA:
            raise ContextTaskImpactError("unsupported context revision change schema")
        _require_typed_ref("change_ref", self.change_ref, "context-change:")
        _require_typed_ref("context_ref", self.context_ref)
        _require_typed_ref(
            "from_revision_ref",
            self.from_revision_ref,
            "context-revision:",
        )
        _require_typed_ref(
            "to_revision_ref",
            self.to_revision_ref,
            "context-revision:",
        )
        if self.from_revision_ref == self.to_revision_ref:
            raise ContextTaskImpactError("context revision change requires two revisions")
        if self.significance not in _SIGNIFICANCE_ORDER:
            raise ContextTaskImpactError("unsupported context significance")
        object.__setattr__(self, "added_refs", _normalize_refs(self.added_refs))
        object.__setattr__(
            self,
            "superseded_refs",
            _normalize_refs(self.superseded_refs),
        )
        object.__setattr__(
            self,
            "invalidated_refs",
            _normalize_refs(self.invalidated_refs),
        )
        pairs = tuple(self.replacement_pairs)
        if len(pairs) > _MAX_ITEMS:
            raise ContextTaskImpactError("too many replacement pairs")
        normalized_pairs: list[tuple[str, str]] = []
        for source_ref, target_ref in pairs:
            _require_typed_ref("replacement source", source_ref)
            _require_typed_ref("replacement target", target_ref)
            if source_ref == target_ref:
                raise ContextTaskImpactError("replacement refs must differ")
            normalized_pairs.append((source_ref, target_ref))
        if len(set(normalized_pairs)) != len(normalized_pairs):
            raise ContextTaskImpactError("replacement pairs must be unique")
        object.__setattr__(
            self,
            "replacement_pairs",
            tuple(sorted(normalized_pairs)),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs(self.evidence_refs),
        )

    @property
    def changed_refs(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                self.added_refs
                + self.superseded_refs
                + self.invalidated_refs
                + tuple(target for _, target in self.replacement_pairs)
            )
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "change_ref": self.change_ref,
            "context_ref": self.context_ref,
            "from_revision_ref": self.from_revision_ref,
            "to_revision_ref": self.to_revision_ref,
            "significance": self.significance,
            "added_refs": list(self.added_refs),
            "superseded_refs": list(self.superseded_refs),
            "invalidated_refs": list(self.invalidated_refs),
            "replacement_pairs": [list(item) for item in self.replacement_pairs],
            "evidence_refs": list(self.evidence_refs),
            "changed_refs": list(self.changed_refs),
            "sql_revision_is_authority": True,
            "route_generation_changed": False,
        }


@dataclass(frozen=True, slots=True)
class TaskContextBinding:
    """Immutable binding of one task to one semantic context revision."""

    schema: str
    binding_ref: str
    task_ref: str
    plan_ref: str
    context_ref: str
    bound_revision_ref: str
    update_policy: TaskContextUpdatePolicy
    minimum_significance: str = "material"
    watched_refs: tuple[str, ...] = ()
    checkpoint_refs: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != TASK_CONTEXT_BINDING_SCHEMA:
            raise ContextTaskImpactError("unsupported task context binding schema")
        _require_typed_ref("binding_ref", self.binding_ref, "task-context-binding:")
        _require_typed_ref("task_ref", self.task_ref, "specialist-task:")
        _require_typed_ref("plan_ref", self.plan_ref, "specialist-task-plan:")
        _require_typed_ref("context_ref", self.context_ref)
        _require_typed_ref(
            "bound_revision_ref",
            self.bound_revision_ref,
            "context-revision:",
        )
        if self.update_policy not in _UPDATE_POLICIES:
            raise ContextTaskImpactError("unsupported task context update policy")
        if self.minimum_significance not in _SIGNIFICANCE_ORDER:
            raise ContextTaskImpactError("unsupported minimum significance")
        object.__setattr__(
            self,
            "watched_refs",
            _normalize_refs(self.watched_refs),
        )
        object.__setattr__(
            self,
            "checkpoint_refs",
            _normalize_refs(self.checkpoint_refs, required_prefix="checkpoint:"),
        )
        object.__setattr__(self, "metadata", _freeze_json_mapping(self.metadata))

    @property
    def watches_whole_context(self) -> bool:
        return not self.watched_refs

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "binding_ref": self.binding_ref,
            "task_ref": self.task_ref,
            "plan_ref": self.plan_ref,
            "context_ref": self.context_ref,
            "bound_revision_ref": self.bound_revision_ref,
            "update_policy": self.update_policy,
            "minimum_significance": self.minimum_significance,
            "watched_refs": list(self.watched_refs),
            "checkpoint_refs": list(self.checkpoint_refs),
            "metadata": _thaw_json(self.metadata),
            "watches_whole_context": self.watches_whole_context,
            "scheduler_owned": True,
        }


@dataclass(frozen=True, slots=True)
class TaskContextImpactAssessment:
    """Deterministic impact evidence without an execution decision."""

    schema: str
    assessment_ref: str
    binding_ref: str
    task_ref: str
    change_ref: str
    affected: bool
    threshold_met: bool
    matched_refs: tuple[str, ...]
    reasons: tuple[str, ...]
    stale_against_revision_ref: str | None

    def __post_init__(self) -> None:
        if self.schema != TASK_CONTEXT_IMPACT_ASSESSMENT_SCHEMA:
            raise ContextTaskImpactError("unsupported task impact assessment schema")
        _require_typed_ref(
            "assessment_ref",
            self.assessment_ref,
            "context-impact-assessment:",
        )
        _require_typed_ref("binding_ref", self.binding_ref, "task-context-binding:")
        _require_typed_ref("task_ref", self.task_ref, "specialist-task:")
        _require_typed_ref("change_ref", self.change_ref, "context-change:")
        _require_bool("affected", self.affected)
        _require_bool("threshold_met", self.threshold_met)
        object.__setattr__(self, "matched_refs", _normalize_refs(self.matched_refs))
        object.__setattr__(self, "reasons", _normalize_texts(self.reasons))
        if self.stale_against_revision_ref is not None:
            _require_typed_ref(
                "stale_against_revision_ref",
                self.stale_against_revision_ref,
                "context-revision:",
            )
        if not self.affected and self.matched_refs:
            raise ContextTaskImpactError("unaffected assessment cannot match refs")
        if self.affected and self.stale_against_revision_ref is None:
            raise ContextTaskImpactError(
                "affected assessment requires stale revision reference"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "assessment_ref": self.assessment_ref,
            "binding_ref": self.binding_ref,
            "task_ref": self.task_ref,
            "change_ref": self.change_ref,
            "affected": self.affected,
            "threshold_met": self.threshold_met,
            "matched_refs": list(self.matched_refs),
            "reasons": list(self.reasons),
            "stale_against_revision_ref": self.stale_against_revision_ref,
            "scheduler_decision_embedded": False,
        }


@dataclass(frozen=True, slots=True)
class SchedulerContextImpactDecision:
    """Scheduler-owned proposal; execution remains outside this contract."""

    schema: str
    decision_ref: str
    scheduler_policy_ref: str
    assessment_ref: str
    task_ref: str
    execution_state: TaskExecutionState
    action: TaskContextImpactAction
    from_revision_ref: str
    target_revision_ref: str
    reason: str
    checkpoint_ref: str | None = None
    fork_task_ref: str | None = None

    def __post_init__(self) -> None:
        if self.schema != SCHEDULER_CONTEXT_IMPACT_DECISION_SCHEMA:
            raise ContextTaskImpactError("unsupported Scheduler impact decision schema")
        _require_typed_ref("decision_ref", self.decision_ref, "scheduler-decision:")
        _require_typed_ref(
            "scheduler_policy_ref",
            self.scheduler_policy_ref,
            "scheduler-policy:",
        )
        _require_typed_ref(
            "assessment_ref",
            self.assessment_ref,
            "context-impact-assessment:",
        )
        _require_typed_ref("task_ref", self.task_ref, "specialist-task:")
        if self.execution_state not in _EXECUTION_STATES:
            raise ContextTaskImpactError("unsupported task execution state")
        if self.action not in _ACTIONS:
            raise ContextTaskImpactError("unsupported task context impact action")
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
        _require_text("reason", self.reason)
        if self.checkpoint_ref is not None:
            _require_typed_ref("checkpoint_ref", self.checkpoint_ref, "checkpoint:")
        if self.fork_task_ref is not None:
            _require_typed_ref(
                "fork_task_ref",
                self.fork_task_ref,
                "specialist-task:",
            )
        if self.action == "rebase_at_checkpoint" and self.checkpoint_ref is None:
            raise ContextTaskImpactError("rebase action requires checkpoint_ref")
        if self.action != "rebase_at_checkpoint" and self.checkpoint_ref is not None:
            raise ContextTaskImpactError(
                "checkpoint_ref is reserved for rebase_at_checkpoint"
            )
        if self.action == "fork_task" and self.fork_task_ref is None:
            raise ContextTaskImpactError("fork action requires fork_task_ref")
        if self.action != "fork_task" and self.fork_task_ref is not None:
            raise ContextTaskImpactError("fork_task_ref is reserved for fork action")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "decision_ref": self.decision_ref,
            "scheduler_policy_ref": self.scheduler_policy_ref,
            "assessment_ref": self.assessment_ref,
            "task_ref": self.task_ref,
            "execution_state": self.execution_state,
            "action": self.action,
            "from_revision_ref": self.from_revision_ref,
            "target_revision_ref": self.target_revision_ref,
            "reason": self.reason,
            "checkpoint_ref": self.checkpoint_ref,
            "fork_task_ref": self.fork_task_ref,
            "scheduler_authority_required": True,
            "action_executed": False,
            "task_created": False,
            "route_changed": False,
            "event_published": False,
        }


@dataclass(frozen=True, slots=True)
class ContextImpactPlan:
    """Deterministic batch of Scheduler-owned context-impact decisions."""

    schema: str
    plan_ref: str
    change_ref: str
    decisions: tuple[SchedulerContextImpactDecision, ...]

    def __post_init__(self) -> None:
        if self.schema != CONTEXT_IMPACT_PLAN_SCHEMA:
            raise ContextTaskImpactError("unsupported context impact plan schema")
        _require_typed_ref("plan_ref", self.plan_ref, "context-impact-plan:")
        _require_typed_ref("change_ref", self.change_ref, "context-change:")
        decisions = tuple(self.decisions)
        if len(decisions) > _MAX_ITEMS:
            raise ContextTaskImpactError("too many impact decisions")
        if not all(isinstance(item, SchedulerContextImpactDecision) for item in decisions):
            raise ContextTaskImpactError(
                "decisions must contain SchedulerContextImpactDecision values"
            )
        task_refs = tuple(item.task_ref for item in decisions)
        if len(task_refs) != len(set(task_refs)):
            raise ContextTaskImpactError("impact plan task_refs must be unique")
        object.__setattr__(self, "decisions", decisions)

    def to_mapping(self) -> dict[str, object]:
        counts: dict[str, int] = {}
        for decision in self.decisions:
            counts[decision.action] = counts.get(decision.action, 0) + 1
        return {
            "schema": self.schema,
            "plan_ref": self.plan_ref,
            "change_ref": self.change_ref,
            "decisions": [item.to_mapping() for item in self.decisions],
            "action_counts": dict(sorted(counts.items())),
            "scheduler_owned": True,
            "executed": False,
            "controlproxy_is_transport_only": True,
            "sql_revision_is_authority": True,
        }


def build_context_revision_change_set(
    *,
    previous: ContextRevision,
    current: ContextRevision,
) -> ContextRevisionChangeSet:
    """Build a direct accepted-child semantic delta from two revisions."""

    if previous.context_ref != current.context_ref:
        raise ContextTaskImpactError("context revisions must share context_ref")
    if current.validation_status != "accepted":
        raise ContextTaskImpactError("target context revision must be accepted")
    if previous.revision_ref not in current.parent_revision_refs:
        raise ContextTaskImpactError(
            "target revision must directly descend from previous revision"
        )
    previous_by_ref = {item.object_ref: item for item in previous.memberships}
    current_by_ref = {item.object_ref: item for item in current.memberships}
    added: list[str] = []
    superseded: list[str] = []
    invalidated: list[str] = []
    replacements: list[tuple[str, str]] = []
    for object_ref, membership in current_by_ref.items():
        old = previous_by_ref.get(object_ref)
        if membership.state == "active" and (
            old is None or old.state != "active"
        ):
            added.append(object_ref)
        elif membership.state == "superseded" and (
            old is None
            or old.state != "superseded"
            or old.replacement_ref != membership.replacement_ref
        ):
            superseded.append(object_ref)
            assert membership.replacement_ref is not None
            replacements.append((object_ref, membership.replacement_ref))
        elif membership.state == "invalidated" and (
            old is None or old.state != "invalidated"
        ):
            invalidated.append(object_ref)
    payload = {
        "context_ref": current.context_ref,
        "from_revision_ref": previous.revision_ref,
        "to_revision_ref": current.revision_ref,
        "significance": current.significance,
        "added_refs": sorted(added),
        "superseded_refs": sorted(superseded),
        "invalidated_refs": sorted(invalidated),
        "replacement_pairs": sorted(replacements),
    }
    digest = _sha256_mapping(payload)
    return ContextRevisionChangeSet(
        schema=CONTEXT_REVISION_CHANGE_SET_SCHEMA,
        change_ref=f"context-change:{digest[:24]}",
        context_ref=current.context_ref,
        from_revision_ref=previous.revision_ref,
        to_revision_ref=current.revision_ref,
        significance=current.significance,
        added_refs=tuple(sorted(added)),
        superseded_refs=tuple(sorted(superseded)),
        invalidated_refs=tuple(sorted(invalidated)),
        replacement_pairs=tuple(sorted(replacements)),
        evidence_refs=current.evidence_refs,
    )


def build_task_context_binding(
    *,
    task: SpecialistTaskRequest,
    revision: ContextRevision,
    update_policy: TaskContextUpdatePolicy,
    minimum_significance: str = "material",
    watched_refs: Sequence[str] = (),
    checkpoint_refs: Sequence[str] = (),
) -> TaskContextBinding:
    """Bind one task to one accepted semantic revision without scheduling it."""

    if revision.validation_status != "accepted":
        raise ContextTaskImpactError("task binding requires accepted revision")
    normalized_watched = tuple(watched_refs)
    if not normalized_watched:
        normalized_watched = tuple(
            dict.fromkeys(
                task.context_refs
                + task.evidence_refs
                + tuple(item.artifact_ref for item in task.input_artifact_refs)
            )
        )
    payload = {
        "task_ref": task.task_ref,
        "revision_ref": revision.revision_ref,
        "update_policy": update_policy,
        "minimum_significance": minimum_significance,
        "watched_refs": list(normalized_watched),
    }
    digest = _sha256_mapping(payload)
    return TaskContextBinding(
        schema=TASK_CONTEXT_BINDING_SCHEMA,
        binding_ref=f"task-context-binding:{digest[:24]}",
        task_ref=task.task_ref,
        plan_ref=task.plan_ref,
        context_ref=revision.context_ref,
        bound_revision_ref=revision.revision_ref,
        update_policy=update_policy,
        minimum_significance=minimum_significance,
        watched_refs=normalized_watched,
        checkpoint_refs=tuple(checkpoint_refs),
        metadata={
            "mission_ref": task.mission_ref,
            "specialist_ref": task.specialist_ref,
        },
    )


def assess_task_context_impact(
    *,
    binding: TaskContextBinding,
    change: ContextRevisionChangeSet,
) -> TaskContextImpactAssessment:
    """Assess semantic impact without deciding what Scheduler will execute."""

    if binding.context_ref != change.context_ref:
        raise ContextTaskImpactError("binding and change target different contexts")
    if binding.bound_revision_ref != change.from_revision_ref:
        raise ContextTaskImpactError(
            "binding revision must equal change source revision"
        )
    changed = frozenset(change.changed_refs)
    matched = (
        tuple(sorted(changed))
        if binding.watches_whole_context
        else tuple(sorted(changed.intersection(binding.watched_refs)))
    )
    affected = bool(changed) and (binding.watches_whole_context or bool(matched))
    threshold_met = (
        _SIGNIFICANCE_ORDER[change.significance]
        >= _SIGNIFICANCE_ORDER[binding.minimum_significance]
    )
    reasons: list[str] = []
    if not changed:
        reasons.append("accepted revision has no membership delta")
    elif binding.watches_whole_context:
        reasons.append("task watches the complete semantic context")
    elif matched:
        reasons.append("changed references intersect task dependencies")
    else:
        reasons.append("changed references do not intersect task dependencies")
    reasons.append(
        "significance threshold met"
        if threshold_met
        else "significance is below task threshold"
    )
    digest = _sha256_mapping(
        {
            "binding_ref": binding.binding_ref,
            "change_ref": change.change_ref,
            "affected": affected,
            "threshold_met": threshold_met,
            "matched_refs": list(matched),
        }
    )
    return TaskContextImpactAssessment(
        schema=TASK_CONTEXT_IMPACT_ASSESSMENT_SCHEMA,
        assessment_ref=f"context-impact-assessment:{digest[:24]}",
        binding_ref=binding.binding_ref,
        task_ref=binding.task_ref,
        change_ref=change.change_ref,
        affected=affected,
        threshold_met=threshold_met,
        matched_refs=matched,
        reasons=tuple(reasons),
        stale_against_revision_ref=(
            change.to_revision_ref if affected else None
        ),
    )


def decide_task_context_impact(
    *,
    binding: TaskContextBinding,
    change: ContextRevisionChangeSet,
    assessment: TaskContextImpactAssessment,
    execution_state: TaskExecutionState,
    scheduler_policy_ref: str,
    active_checkpoint_ref: str | None = None,
) -> SchedulerContextImpactDecision:
    """Build a deterministic Scheduler decision proposal without executing it."""

    if assessment.binding_ref != binding.binding_ref:
        raise ContextTaskImpactError("assessment does not match binding")
    if assessment.change_ref != change.change_ref:
        raise ContextTaskImpactError("assessment does not match change")
    if execution_state not in _EXECUTION_STATES:
        raise ContextTaskImpactError("unsupported task execution state")
    _require_typed_ref(
        "scheduler_policy_ref",
        scheduler_policy_ref,
        "scheduler-policy:",
    )
    if active_checkpoint_ref is not None:
        _require_typed_ref(
            "active_checkpoint_ref",
            active_checkpoint_ref,
            "checkpoint:",
        )
        if active_checkpoint_ref not in binding.checkpoint_refs:
            raise ContextTaskImpactError(
                "active checkpoint is not declared by task binding"
            )
    action, reason, checkpoint_ref, fork_task_ref = _select_action(
        binding=binding,
        change=change,
        assessment=assessment,
        execution_state=execution_state,
        active_checkpoint_ref=active_checkpoint_ref,
    )
    digest = _sha256_mapping(
        {
            "task_ref": binding.task_ref,
            "assessment_ref": assessment.assessment_ref,
            "scheduler_policy_ref": scheduler_policy_ref,
            "execution_state": execution_state,
            "action": action,
        }
    )
    return SchedulerContextImpactDecision(
        schema=SCHEDULER_CONTEXT_IMPACT_DECISION_SCHEMA,
        decision_ref=f"scheduler-decision:{digest[:24]}",
        scheduler_policy_ref=scheduler_policy_ref,
        assessment_ref=assessment.assessment_ref,
        task_ref=binding.task_ref,
        execution_state=execution_state,
        action=action,
        from_revision_ref=change.from_revision_ref,
        target_revision_ref=change.to_revision_ref,
        reason=reason,
        checkpoint_ref=checkpoint_ref,
        fork_task_ref=fork_task_ref,
    )


def build_context_impact_plan(
    *,
    change: ContextRevisionChangeSet,
    decisions: Sequence[SchedulerContextImpactDecision],
) -> ContextImpactPlan:
    """Group precomputed Scheduler decisions into one immutable plan."""

    ordered = tuple(sorted(decisions, key=lambda item: item.task_ref))
    digest = _sha256_mapping(
        {
            "change_ref": change.change_ref,
            "decisions": [item.to_mapping() for item in ordered],
        }
    )
    return ContextImpactPlan(
        schema=CONTEXT_IMPACT_PLAN_SCHEMA,
        plan_ref=f"context-impact-plan:{digest[:24]}",
        change_ref=change.change_ref,
        decisions=ordered,
    )


def _select_action(
    *,
    binding: TaskContextBinding,
    change: ContextRevisionChangeSet,
    assessment: TaskContextImpactAssessment,
    execution_state: TaskExecutionState,
    active_checkpoint_ref: str | None,
) -> tuple[TaskContextImpactAction, str, str | None, str | None]:
    if not assessment.affected:
        return "no_action", "task dependencies are unaffected", None, None
    if execution_state == "completed":
        return (
            "mark_result_stale",
            "completed result remains reproducible but is stale against a newer revision",
            None,
            None,
        )
    if execution_state in {"failed", "cancelled"}:
        return (
            "notify_only",
            "terminal task is recorded against its original revision",
            None,
            None,
        )
    if binding.update_policy == "snapshot":
        return (
            "continue_snapshot",
            "snapshot policy preserves the bound revision",
            None,
            None,
        )
    if binding.update_policy == "notify_only":
        return "notify_only", "task receives a context-change notification", None, None
    if binding.update_policy == "ignore_noncritical":
        if change.significance == "critical":
            return (
                "notify_only",
                "critical context change bypasses noncritical ignore policy",
                None,
                None,
            )
        return "no_action", "noncritical context change is ignored by policy", None, None
    if not assessment.threshold_met:
        return (
            "notify_only",
            "context change is below the action threshold",
            None,
            None,
        )
    if execution_state == "queued":
        return (
            "rebind_before_start",
            "queued task can bind to the accepted revision before execution",
            None,
            None,
        )
    if binding.update_policy == "checkpoint_rebase":
        if active_checkpoint_ref is None:
            return (
                "wait_for_checkpoint",
                "running task requires an authorized safe checkpoint before rebase",
                None,
                None,
            )
        return (
            "rebase_at_checkpoint",
            "task may rebase at the declared safe checkpoint",
            active_checkpoint_ref,
            None,
        )
    if binding.update_policy == "restart_on_material_change":
        return (
            "restart_task",
            "material context change requires a new execution from the target revision",
            None,
            None,
        )
    if binding.update_policy == "fork_on_material_change":
        fork_digest = _sha256_mapping(
            {
                "source_task_ref": binding.task_ref,
                "target_revision_ref": change.to_revision_ref,
            }
        )
        return (
            "fork_task",
            "preserve current execution and compare a branch on the target revision",
            None,
            f"specialist-task:fork-{fork_digest[:24]}",
        )
    raise ContextTaskImpactError("unreachable task context update policy")


def _membership_map(
    values: Sequence[ContextRevisionMembership],
) -> dict[str, ContextRevisionMembership]:
    return {item.object_ref: item for item in values}


def _require_typed_ref(
    name: str,
    value: str,
    required_prefix: str | None = None,
) -> None:
    _require_text(name, value)
    if not _TYPED_REF_RE.fullmatch(value):
        raise ContextTaskImpactError(f"{name} must be a typed reference")
    if required_prefix is not None and not value.startswith(required_prefix):
        raise ContextTaskImpactError(f"{name} must start with {required_prefix}")


def _normalize_refs(
    values: Sequence[str],
    required_prefix: str | None = None,
) -> tuple[str, ...]:
    normalized = tuple(values)
    if len(normalized) > _MAX_ITEMS:
        raise ContextTaskImpactError("too many references")
    for value in normalized:
        _require_typed_ref("reference", value, required_prefix)
    if len(normalized) != len(set(normalized)):
        raise ContextTaskImpactError("references must be unique")
    return normalized


def _normalize_texts(values: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(values)
    if len(normalized) > _MAX_ITEMS:
        raise ContextTaskImpactError("too many text values")
    for value in normalized:
        _require_text("text value", value)
    return normalized


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContextTaskImpactError(f"{name} must not be empty")
    if len(value) > _MAX_TEXT_CHARS:
        raise ContextTaskImpactError(f"{name} is too large")


def _require_bool(name: str, value: bool) -> None:
    if not isinstance(value, bool):
        raise ContextTaskImpactError(f"{name} must be a boolean")


def _freeze_json_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContextTaskImpactError("metadata must be a mapping")
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
    raise ContextTaskImpactError("value is not JSON compatible")


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
