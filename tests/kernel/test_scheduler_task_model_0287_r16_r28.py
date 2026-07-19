from __future__ import annotations

import pytest

from kernel.scheduler_task_model import (
    SchedulerTask,
    SchedulerTaskAttemptState,
    SchedulerTaskDependency,
    SchedulerTaskDependencyKind,
    SchedulerTaskFailure,
    SchedulerTaskModelError,
    SchedulerTaskResult,
    SchedulerTaskState,
)


COMMAND_REF = "scheduler-command:github-research:0123456789abcdef01234567"
TASK_REF = "scheduler-task:issue-54-first-analysis"
ACTOR_REF = "scheduler:canonical"
CAUSE_REF = "scheduler-cause:dependency-barrier-satisfied"


def _planned(*, dependencies=(), max_attempts: int = 2) -> SchedulerTask:
    return SchedulerTask.plan(
        task_ref=TASK_REF,
        command_ref=COMMAND_REF,
        task_kind_ref="task-kind:specialist-analysis",
        capability_ref="capability:research.specialist.analyse.v1",
        contract_version=1,
        priority=60,
        max_attempts=max_attempts,
        created_at="2026-07-19T10:00:00Z",
        dependencies=dependencies,
        context_refs=("context:issue-54",),
        evidence_refs=("evidence:artifact-triplet",),
    )


def _ready(task: SchedulerTask | None = None) -> SchedulerTask:
    source = task or _planned()
    return source.mark_ready(
        dependency_states={},
        occurred_at="2026-07-19T10:01:00Z",
        actor_ref=ACTOR_REF,
        cause_ref=CAUSE_REF,
    ).task


def test_plan_is_immutable_deterministic_and_not_json_authority() -> None:
    first = _planned()
    second = _planned()
    assert first == second
    assert first.state is SchedulerTaskState.PLANNED
    assert first.state_version == 1
    assert first.attempt_count == 0
    assert first.task_digest.startswith("sha256:")
    with pytest.raises(Exception):
        first.state = SchedulerTaskState.READY  # type: ignore[misc]


def test_dependencies_gate_ready_transition() -> None:
    dependency = SchedulerTaskDependency(
        task_ref="scheduler-task:prepare-visit",
        kind=SchedulerTaskDependencyKind.SUCCEEDED,
    )
    task = _planned(dependencies=(dependency,))
    with pytest.raises(SchedulerTaskModelError, match="dépendances"):
        task.mark_ready(
            dependency_states={
                dependency.task_ref: SchedulerTaskState.RUNNING,
            },
            occurred_at="2026-07-19T10:01:00Z",
            actor_ref=ACTOR_REF,
            cause_ref=CAUSE_REF,
        )
    mutation = task.mark_ready(
        dependency_states={dependency.task_ref: SchedulerTaskState.COMPLETED},
        occurred_at="2026-07-19T10:02:00Z",
        actor_ref=ACTOR_REF,
        cause_ref=CAUSE_REF,
    )
    assert mutation.task.state is SchedulerTaskState.READY
    assert mutation.transition.from_state is SchedulerTaskState.PLANNED
    assert mutation.transition.to_state is SchedulerTaskState.READY
    assert mutation.task.state_version == 2


def test_start_attempt_consumes_one_attempt_and_correlates_bundle() -> None:
    start = _ready().start_attempt(
        handler_ref="handler:love-first-analysis",
        contract_version=1,
        started_at="2026-07-19T10:03:00Z",
        deadline_at="2026-07-19T10:13:00Z",
        actor_ref=ACTOR_REF,
        cause_ref="scheduler-cause:task-selected",
    )
    assert start.task.state is SchedulerTaskState.RUNNING
    assert start.task.attempt_count == 1
    assert start.attempt.state is SchedulerTaskAttemptState.RUNNING
    assert start.attempt.task_ref == start.task.task_ref
    assert start.attempt.number == 1
    assert start.transition.to_state is SchedulerTaskState.RUNNING


def test_success_result_closes_task_and_attempt() -> None:
    start = _ready().start_attempt(
        handler_ref="handler:love-first-analysis",
        contract_version=1,
        started_at="2026-07-19T10:03:00Z",
        deadline_at="2026-07-19T10:13:00Z",
        actor_ref=ACTOR_REF,
        cause_ref="scheduler-cause:task-selected",
    )
    result = SchedulerTaskResult.create(
        task_ref=start.task.task_ref,
        attempt_ref=start.attempt.attempt_ref,
        result_type_ref="result-type:specialist-analysis",
        completed_at="2026-07-19T10:05:00Z",
        evidence_refs=("analysis:sql-authority-1",),
    )
    completion = start.task.complete_attempt(
        attempt=start.attempt,
        result=result,
        occurred_at="2026-07-19T10:05:00Z",
        actor_ref=ACTOR_REF,
        cause_ref="scheduler-cause:handler-result-accepted",
    )
    assert completion.task.state is SchedulerTaskState.COMPLETED
    assert completion.task.state.terminal is True
    assert completion.attempt.state is SchedulerTaskAttemptState.SUCCEEDED
    assert completion.attempt.result_ref == result.result_ref


def test_retryable_failure_moves_to_retry_wait_before_budget_exhaustion() -> None:
    start = _ready(_planned(max_attempts=2)).start_attempt(
        handler_ref="handler:love-first-analysis",
        contract_version=1,
        started_at="2026-07-19T10:03:00Z",
        deadline_at="2026-07-19T10:13:00Z",
        actor_ref=ACTOR_REF,
        cause_ref="scheduler-cause:task-selected",
    )
    failure = SchedulerTaskFailure.create(
        task_ref=start.task.task_ref,
        attempt_ref=start.attempt.attempt_ref,
        error_type="TemporaryBackendError",
        message="backend temporairement indisponible",
        retryable=True,
        failed_at="2026-07-19T10:04:00Z",
    )
    outcome = start.task.fail_attempt(
        attempt=start.attempt,
        failure=failure,
        occurred_at="2026-07-19T10:04:00Z",
        actor_ref=ACTOR_REF,
        cause_ref="scheduler-cause:retry-policy-approved",
    )
    assert outcome.retry_scheduled is True
    assert outcome.task.state is SchedulerTaskState.RETRY_WAIT
    assert outcome.attempt.state is SchedulerTaskAttemptState.FAILED


def test_failure_becomes_terminal_when_attempt_budget_is_exhausted() -> None:
    start = _ready(_planned(max_attempts=1)).start_attempt(
        handler_ref="handler:love-first-analysis",
        contract_version=1,
        started_at="2026-07-19T10:03:00Z",
        deadline_at="2026-07-19T10:13:00Z",
        actor_ref=ACTOR_REF,
        cause_ref="scheduler-cause:task-selected",
    )
    failure = SchedulerTaskFailure.create(
        task_ref=start.task.task_ref,
        attempt_ref=start.attempt.attempt_ref,
        error_type="TemporaryBackendError",
        message="plus de tentative disponible",
        retryable=True,
        failed_at="2026-07-19T10:04:00Z",
    )
    outcome = start.task.fail_attempt(
        attempt=start.attempt,
        failure=failure,
        occurred_at="2026-07-19T10:04:00Z",
        actor_ref=ACTOR_REF,
        cause_ref="scheduler-cause:attempt-budget-exhausted",
    )
    assert outcome.retry_scheduled is False
    assert outcome.task.state is SchedulerTaskState.FAILED
    assert outcome.task.state.terminal is True


def test_generic_move_cannot_bypass_execution_specific_transitions() -> None:
    ready = _ready()
    with pytest.raises(SchedulerTaskModelError, match="méthode d'exécution"):
        ready.move_to(
            to_state=SchedulerTaskState.RUNNING,
            occurred_at="2026-07-19T10:03:00Z",
            actor_ref=ACTOR_REF,
            cause_ref="scheduler-cause:invalid-shortcut",
        )


def test_terminal_task_cannot_be_reopened() -> None:
    cancelled = _planned().move_to(
        to_state=SchedulerTaskState.CANCELLED,
        occurred_at="2026-07-19T10:01:00Z",
        actor_ref=ACTOR_REF,
        cause_ref="scheduler-cause:operator-cancelled",
    ).task
    with pytest.raises(SchedulerTaskModelError, match="transition interdite"):
        cancelled.move_to(
            to_state=SchedulerTaskState.READY,
            occurred_at="2026-07-19T10:02:00Z",
            actor_ref=ACTOR_REF,
            cause_ref="scheduler-cause:invalid-reopen",
        )
