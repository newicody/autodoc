from __future__ import annotations

from dataclasses import replace

import pytest

from kernel.scheduler_task_admission import (
    SchedulerAdmissionReason,
    SchedulerAdmissionStatus,
    SchedulerBudgetCharge,
    SchedulerCommandExecutionBudget,
    SchedulerFairnessPolicy,
    SchedulerResourceInventoryItem,
    SchedulerResourceProfile,
    SchedulerResourceRequirement,
    SchedulerRetryPolicy,
    SchedulerTaskAdmissionCandidate,
    SchedulerTaskAdmissionError,
    SchedulerTaskAdmissionPlanner,
    SchedulerTaskExecutionBudget,
)
from kernel.scheduler_task_model import SchedulerTask, SchedulerTaskState


NOW = "2026-07-19T12:00:00Z"


def _ready_task(
    *,
    task_ref: str,
    priority: int = 40,
    created_at: str = "2026-07-19T11:00:00Z",
) -> SchedulerTask:
    planned = SchedulerTask.plan(
        task_ref=task_ref,
        command_ref="scheduler-command:research-54",
        task_kind_ref="task-kind:research-analysis",
        capability_ref="capability:research-analysis",
        contract_version=1,
        priority=priority,
        max_attempts=3,
        created_at=created_at,
    )
    return planned.mark_ready(
        dependency_states={},
        occurred_at=created_at,
        actor_ref="scheduler:canonical",
        cause_ref="scheduler-cause:graph-ready",
    ).task


def _candidate(
    task: SchedulerTask,
    *,
    visits: int = 0,
    retry_not_before: str = "",
    profile: SchedulerResourceProfile | None = None,
    command_budget: SchedulerCommandExecutionBudget | None = None,
) -> SchedulerTaskAdmissionCandidate:
    return SchedulerTaskAdmissionCandidate(
        task=task,
        command_budget=command_budget
        or SchedulerCommandExecutionBudget(
            budget_ref="scheduler-command-budget:research-54",
            command_ref=task.command_ref,
            max_scheduler_steps=16,
            consumed_scheduler_steps=2,
            max_specialist_visits=2,
            consumed_specialist_visits=0,
            started_at="2026-07-19T10:00:00Z",
            deadline_at="2026-07-19T13:00:00Z",
        ),
        task_budget=SchedulerTaskExecutionBudget(
            budget_ref=f"scheduler-task-budget:{task.task_ref.split(':', 1)[1]}",
            task_ref=task.task_ref,
            max_attempts=task.max_attempts,
            timeout_seconds=600,
        ),
        budget_charge=SchedulerBudgetCharge(
            scheduler_steps=1,
            specialist_visits=visits,
        ),
        resource_profile=profile
        or SchedulerResourceProfile(
            profile_ref="resource-profile:research-cpu",
            requirements=(
                SchedulerResourceRequirement("resource:cpu-slot", 1),
                SchedulerResourceRequirement("resource:postgres-connection", 1),
            ),
        ),
        fairness_policy=SchedulerFairnessPolicy(
            policy_ref="fairness-policy:default",
            aging_interval_seconds=900,
            aging_priority_points=2,
            maximum_priority=100,
            deadline_boost_window_seconds=300,
            deadline_boost_points=10,
        ),
        retry_policy=SchedulerRetryPolicy(
            policy_ref="retry-policy:bounded-exponential",
            base_delay_seconds=10,
            multiplier=2,
            max_delay_seconds=120,
        ),
        retry_not_before=retry_not_before,
    )


def _inventory(cpu: int = 2) -> tuple[SchedulerResourceInventoryItem, ...]:
    return (
        SchedulerResourceInventoryItem("resource:cpu-slot", cpu, 0),
        SchedulerResourceInventoryItem("resource:postgres-connection", 2, 0),
    )


def test_admission_reserves_resources_without_mutating_task() -> None:
    task = _ready_task(task_ref="scheduler-task:analysis-1")
    plan = SchedulerTaskAdmissionPlanner().plan(
        candidates=(_candidate(task),),
        inventory=_inventory(),
        now=NOW,
        max_admissions=1,
    )
    decision = plan.decisions[0]
    assert decision.status is SchedulerAdmissionStatus.ADMITTED
    assert decision.reason is SchedulerAdmissionReason.ADMITTED
    assert decision.attempt_deadline_at == "2026-07-19T12:10:00Z"
    assert decision.reservation is not None
    assert task.state is SchedulerTaskState.READY
    assert plan.plan_digest.startswith("sha256:")


def test_aging_prevents_starvation_and_order_is_stable() -> None:
    old = _ready_task(
        task_ref="scheduler-task:old",
        priority=30,
        created_at="2026-07-19T08:00:00Z",
    )
    recent = _ready_task(
        task_ref="scheduler-task:recent",
        priority=45,
        created_at="2026-07-19T11:59:00Z",
    )
    plan = SchedulerTaskAdmissionPlanner().plan(
        candidates=(_candidate(recent), _candidate(old)),
        inventory=_inventory(cpu=1),
        now=NOW,
        max_admissions=1,
    )
    assert plan.decisions[0].task_ref == old.task_ref
    assert plan.decisions[0].status is SchedulerAdmissionStatus.ADMITTED
    assert plan.decisions[1].reason is SchedulerAdmissionReason.ADMISSION_WINDOW_FULL


def test_resource_shortage_defers_without_reservation() -> None:
    task = _ready_task(task_ref="scheduler-task:no-cpu")
    decision = SchedulerTaskAdmissionPlanner().plan(
        candidates=(_candidate(task),),
        inventory=_inventory(cpu=0),
        now=NOW,
        max_admissions=1,
    ).decisions[0]
    assert decision.status is SchedulerAdmissionStatus.DEFERRED
    assert decision.reason is SchedulerAdmissionReason.RESOURCE_UNAVAILABLE
    assert decision.reservation is None


def test_command_budget_and_deadline_are_hard_rejections() -> None:
    task = _ready_task(task_ref="scheduler-task:budget")
    exhausted = SchedulerCommandExecutionBudget(
        budget_ref="scheduler-command-budget:research-54",
        command_ref=task.command_ref,
        max_scheduler_steps=2,
        consumed_scheduler_steps=2,
        max_specialist_visits=2,
        consumed_specialist_visits=0,
        started_at="2026-07-19T10:00:00Z",
        deadline_at="2026-07-19T13:00:00Z",
    )
    decision = SchedulerTaskAdmissionPlanner().plan(
        candidates=(_candidate(task, command_budget=exhausted),),
        inventory=_inventory(),
        now=NOW,
        max_admissions=1,
    ).decisions[0]
    assert decision.status is SchedulerAdmissionStatus.REJECTED
    assert decision.reason is SchedulerAdmissionReason.COMMAND_STEP_BUDGET_EXHAUSTED

    expired = replace(
        exhausted,
        max_scheduler_steps=3,
        deadline_at="2026-07-19T11:59:59Z",
    )
    decision = SchedulerTaskAdmissionPlanner().plan(
        candidates=(_candidate(task, command_budget=expired),),
        inventory=_inventory(),
        now=NOW,
        max_admissions=1,
    ).decisions[0]
    assert decision.reason is SchedulerAdmissionReason.COMMAND_DEADLINE_EXPIRED


def test_retry_backoff_is_deterministic_and_defers_early_retry() -> None:
    task = _ready_task(task_ref="scheduler-task:retry")
    policy = _candidate(task).retry_policy
    assert policy.delay_seconds(failed_attempt_number=1) == 10
    assert policy.delay_seconds(failed_attempt_number=4) == 80
    assert policy.delay_seconds(failed_attempt_number=8) == 120
    retry_at = policy.retry_not_before(
        failed_at="2026-07-19T11:59:55Z",
        failed_attempt_number=1,
    )
    decision = SchedulerTaskAdmissionPlanner().plan(
        candidates=(_candidate(task, retry_not_before=retry_at),),
        inventory=_inventory(),
        now=NOW,
        max_admissions=1,
    ).decisions[0]
    assert decision.status is SchedulerAdmissionStatus.DEFERRED
    assert decision.reason is SchedulerAdmissionReason.RETRY_BACKOFF_ACTIVE


def test_task_budget_must_match_task_contract() -> None:
    task = _ready_task(task_ref="scheduler-task:mismatch")
    with pytest.raises(SchedulerTaskAdmissionError, match="max_attempts"):
        SchedulerTaskAdmissionCandidate(
            task=task,
            command_budget=_candidate(task).command_budget,
            task_budget=SchedulerTaskExecutionBudget(
                budget_ref="scheduler-task-budget:mismatch",
                task_ref=task.task_ref,
                max_attempts=2,
                timeout_seconds=60,
            ),
            budget_charge=SchedulerBudgetCharge(),
            resource_profile=_candidate(task).resource_profile,
            fairness_policy=_candidate(task).fairness_policy,
            retry_policy=_candidate(task).retry_policy,
        )


def test_no_scheduler_or_handler_execution_surface_is_exposed() -> None:
    import kernel.scheduler_task_admission as module

    source = module.__file__
    assert source is not None
    for forbidden in ("Dispatcher", "EventBus", "asyncio.create_task", ".execute("):
        assert forbidden not in open(source, encoding="utf-8").read()
