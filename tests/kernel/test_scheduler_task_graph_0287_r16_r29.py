from __future__ import annotations

import pytest

from kernel.scheduler_task_graph import (
    SchedulerTaskBarrier,
    SchedulerTaskBarrierKind,
    SchedulerTaskBranchCondition,
    SchedulerTaskBranchGate,
    SchedulerTaskBranchMode,
    SchedulerTaskBranchRule,
    SchedulerTaskGraph,
    SchedulerTaskGraphError,
)
from kernel.scheduler_task_model import (
    SchedulerTask,
    SchedulerTaskDependency,
    SchedulerTaskDependencyKind,
    SchedulerTaskState,
)


NOW = "2026-07-19T12:00:00Z"
COMMAND = "scheduler-command:github-research:test"


def task(
    name: str,
    *,
    priority: int = 50,
    state: SchedulerTaskState = SchedulerTaskState.PLANNED,
    dependencies: tuple[SchedulerTaskDependency, ...] = (),
    command_ref: str = COMMAND,
) -> SchedulerTask:
    planned = SchedulerTask.plan(
        task_ref=f"scheduler-task:{name}",
        command_ref=command_ref,
        task_kind_ref=f"task-kind:{name}",
        capability_ref=f"capability:{name}",
        contract_version=1,
        priority=priority,
        max_attempts=2,
        created_at=NOW,
        dependencies=dependencies,
    )
    if state is SchedulerTaskState.PLANNED:
        return planned
    if state is SchedulerTaskState.READY:
        return planned.mark_ready(
            dependency_states={},
            occurred_at=NOW,
            actor_ref="scheduler:canonical",
            cause_ref="scheduler-cause:test",
        ).task
    raise AssertionError("état de fixture non pris en charge")


def rebuild_state(value: SchedulerTask, state: SchedulerTaskState) -> SchedulerTask:
    return value._rebuild(  # noqa: SLF001 - fixture de contrat ciblée
        state=state,
        state_version=value.state_version + 1,
        updated_at="2026-07-19T12:01:00Z",
        attempt_count=1 if state in {SchedulerTaskState.RUNNING, SchedulerTaskState.COMPLETED} else 0,
    )


def graph(*tasks: SchedulerTask, barriers=(), branch_gates=()) -> SchedulerTaskGraph:
    return SchedulerTaskGraph.create(
        graph_ref="scheduler-task-graph:test",
        command_ref=COMMAND,
        created_at=NOW,
        tasks=tasks,
        barriers=barriers,
        branch_gates=branch_gates,
    )


def test_readiness_order_is_stable_priority_then_ref() -> None:
    current = graph(task("b", priority=70), task("a", priority=70), task("c", priority=20))
    plan = current.readiness_plan()
    assert plan.ready_task_refs == (
        "scheduler-task:a",
        "scheduler-task:b",
        "scheduler-task:c",
    )
    assert plan.plan_digest.startswith("sha256:")


def test_dependency_blocks_until_predecessor_completed() -> None:
    first = task("first")
    second = task(
        "second",
        dependencies=(
            SchedulerTaskDependency(
                task_ref=first.task_ref,
                kind=SchedulerTaskDependencyKind.SUCCEEDED,
            ),
        ),
    )
    blocked = graph(first, second).readiness_plan()
    assert blocked.ready_task_refs == (first.task_ref,)
    completed_first = rebuild_state(first, SchedulerTaskState.COMPLETED)
    ready = graph(completed_first, second).readiness_plan()
    assert ready.ready_task_refs == (second.task_ref,)


def test_barrier_all_succeeded_and_all_terminal_are_distinct() -> None:
    succeeded = rebuild_state(task("success"), SchedulerTaskState.COMPLETED)
    failed = rebuild_state(task("failure"), SchedulerTaskState.FAILED)
    target_success = task("target-success")
    target_terminal = task("target-terminal")
    current = graph(
        succeeded,
        failed,
        target_success,
        target_terminal,
        barriers=(
            SchedulerTaskBarrier(
                barrier_ref="scheduler-barrier:success",
                target_task_ref=target_success.task_ref,
                member_task_refs=(succeeded.task_ref, failed.task_ref),
                kind=SchedulerTaskBarrierKind.ALL_SUCCEEDED,
            ),
            SchedulerTaskBarrier(
                barrier_ref="scheduler-barrier:terminal",
                target_task_ref=target_terminal.task_ref,
                member_task_refs=(succeeded.task_ref, failed.task_ref),
                kind=SchedulerTaskBarrierKind.ALL_TERMINAL,
            ),
        ),
    )
    plan = current.readiness_plan()
    assert target_terminal.task_ref in plan.ready_task_refs
    assert target_success.task_ref not in plan.ready_task_refs


def test_branch_gate_any_accepts_one_matching_terminal_path() -> None:
    success = rebuild_state(task("success"), SchedulerTaskState.COMPLETED)
    failure = rebuild_state(task("failure"), SchedulerTaskState.FAILED)
    target = task("target")
    gate = SchedulerTaskBranchGate(
        gate_ref="scheduler-branch-gate:choice",
        target_task_ref=target.task_ref,
        mode=SchedulerTaskBranchMode.ANY,
        rules=(
            SchedulerTaskBranchRule(
                source_task_ref=success.task_ref,
                condition=SchedulerTaskBranchCondition.FAILED,
            ),
            SchedulerTaskBranchRule(
                source_task_ref=failure.task_ref,
                condition=SchedulerTaskBranchCondition.FAILED,
            ),
        ),
    )
    assert graph(success, failure, target, branch_gates=(gate,)).readiness_plan().ready_task_refs == (
        target.task_ref,
    )


def test_branch_gate_all_requires_every_rule() -> None:
    success = rebuild_state(task("success"), SchedulerTaskState.COMPLETED)
    failure = rebuild_state(task("failure"), SchedulerTaskState.FAILED)
    target = task("target")
    gate = SchedulerTaskBranchGate(
        gate_ref="scheduler-branch-gate:all",
        target_task_ref=target.task_ref,
        mode=SchedulerTaskBranchMode.ALL,
        rules=(
            SchedulerTaskBranchRule(success.task_ref, SchedulerTaskBranchCondition.COMPLETED),
            SchedulerTaskBranchRule(failure.task_ref, SchedulerTaskBranchCondition.COMPLETED),
        ),
    )
    plan = graph(success, failure, target, branch_gates=(gate,)).readiness_plan()
    assert target.task_ref not in plan.ready_task_refs


def test_promotion_returns_new_graph_and_typed_mutations() -> None:
    current = graph(task("high", priority=80), task("low", priority=10))
    promotion = current.promote_ready(
        occurred_at="2026-07-19T12:02:00Z",
        actor_ref="scheduler:canonical",
        cause_ref="scheduler-cause:readiness",
    )
    assert promotion.changed is True
    assert promotion.graph.graph_version == 2
    assert tuple(item.task.state for item in promotion.mutations) == (
        SchedulerTaskState.READY,
        SchedulerTaskState.READY,
    )
    assert current.graph_version == 1
    second = promotion.graph.promote_ready(
        occurred_at="2026-07-19T12:03:00Z",
        actor_ref="scheduler:canonical",
        cause_ref="scheduler-cause:readiness",
    )
    assert second.changed is False
    assert second.graph is promotion.graph


def test_cycle_through_dependencies_is_rejected() -> None:
    a = task(
        "a",
        dependencies=(
            SchedulerTaskDependency("scheduler-task:b", SchedulerTaskDependencyKind.SUCCEEDED),
        ),
    )
    b = task(
        "b",
        dependencies=(
            SchedulerTaskDependency("scheduler-task:a", SchedulerTaskDependencyKind.SUCCEEDED),
        ),
    )
    with pytest.raises(SchedulerTaskGraphError, match="cycle"):
        graph(a, b)


def test_cycle_through_branch_is_rejected() -> None:
    a = task("a")
    b = task("b")
    gates = (
        SchedulerTaskBranchGate(
            "scheduler-branch-gate:a-to-b",
            b.task_ref,
            SchedulerTaskBranchMode.ALL,
            (SchedulerTaskBranchRule(a.task_ref, SchedulerTaskBranchCondition.COMPLETED),),
        ),
        SchedulerTaskBranchGate(
            "scheduler-branch-gate:b-to-a",
            a.task_ref,
            SchedulerTaskBranchMode.ALL,
            (SchedulerTaskBranchRule(b.task_ref, SchedulerTaskBranchCondition.COMPLETED),),
        ),
    )
    with pytest.raises(SchedulerTaskGraphError, match="cycle"):
        graph(a, b, branch_gates=gates)


def test_missing_reference_and_foreign_command_are_rejected() -> None:
    missing = task(
        "missing",
        dependencies=(
            SchedulerTaskDependency(
                "scheduler-task:not-present",
                SchedulerTaskDependencyKind.SUCCEEDED,
            ),
        ),
    )
    with pytest.raises(SchedulerTaskGraphError, match="absente"):
        graph(missing)
    with pytest.raises(SchedulerTaskGraphError, match="command_ref"):
        graph(task("foreign", command_ref="scheduler-command:other"))


def test_duplicate_task_ref_is_rejected() -> None:
    duplicated = task("same")
    with pytest.raises(SchedulerTaskGraphError, match="dupliquée"):
        graph(duplicated, duplicated)
