from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from kernel.scheduler_canonical_continuation import (
    SchedulerCanonicalBoundedCycle,
    SchedulerCanonicalContinuationError,
    SchedulerCanonicalCycleBound,
    SchedulerContinuationStatus,
    SchedulerDurableContinuationPlanner,
    SchedulerDurableGraphSnapshot,
)
from kernel.scheduler_task_graph import SchedulerTaskGraph
from kernel.scheduler_task_model import SchedulerTask, SchedulerTaskResult


TIMES = iter(
    (
        "2026-07-19T20:00:00Z",
        "2026-07-19T20:00:01Z",
        "2026-07-19T20:00:02Z",
        "2026-07-19T20:00:03Z",
        "2026-07-19T20:00:04Z",
        "2026-07-19T20:00:05Z",
        "2026-07-19T20:00:06Z",
        "2026-07-19T20:00:07Z",
    )
)


def _task() -> SchedulerTask:
    return SchedulerTask.plan(
        task_ref="scheduler-task:root",
        command_ref="scheduler-command:test",
        task_kind_ref="task-kind:test",
        capability_ref="capability:test",
        contract_version=1,
        priority=60,
        max_attempts=2,
        created_at="2026-07-19T19:59:00Z",
    )


def _graph(task: SchedulerTask | None = None) -> SchedulerTaskGraph:
    return SchedulerTaskGraph.create(
        graph_ref="scheduler-task-graph:test",
        command_ref="scheduler-command:test",
        created_at="2026-07-19T19:59:00Z",
        tasks=(task or _task(),),
    )


def _snapshot(graph: SchedulerTaskGraph, *, revision: int = 1, loaded_at: str = "2026-07-19T20:00:00Z") -> SchedulerDurableGraphSnapshot:
    return SchedulerDurableGraphSnapshot.create(
        command_ref="scheduler-command:test",
        scheduler_ref="scheduler:canonical",
        durable_revision=revision,
        loaded_at=loaded_at,
        graph=graph,
    )


def test_planner_promotes_root_task_and_exposes_ready_order() -> None:
    decision = SchedulerDurableContinuationPlanner().plan(
        snapshot=_snapshot(_graph()),
        occurred_at="2026-07-19T20:00:01Z",
        actor_ref="actor:scheduler",
        cause_ref="cause:durable-continuation",
    )

    assert decision.status is SchedulerContinuationStatus.READY
    assert decision.promotion.changed is True
    assert decision.ready_task_refs == ("scheduler-task:root",)
    assert decision.next_ready_task_ref == "scheduler-task:root"


@dataclass(frozen=True)
class _Outcome:
    outcome_ref: str


class _Store:
    def __init__(self, snapshot: SchedulerDurableGraphSnapshot) -> None:
        self.snapshot = snapshot
        self.commits = 0

    def load_snapshot(self, *, command_ref: str, scheduler_ref: str, loaded_at: str) -> SchedulerDurableGraphSnapshot:
        return SchedulerDurableGraphSnapshot.create(
            command_ref=command_ref,
            scheduler_ref=scheduler_ref,
            durable_revision=self.snapshot.durable_revision,
            loaded_at=loaded_at,
            graph=self.snapshot.graph,
            source_transaction_ref=self.snapshot.source_transaction_ref,
        )

    def commit_promotion(self, *, snapshot, promotion, committed_at, actor_ref, cause_ref):
        self.commits += 1
        self.snapshot = SchedulerDurableGraphSnapshot.create(
            command_ref=snapshot.command_ref,
            scheduler_ref=snapshot.scheduler_ref,
            durable_revision=snapshot.durable_revision + 1,
            loaded_at=committed_at,
            graph=promotion.graph,
            source_transaction_ref="scheduler-transaction:promotion",
        )
        return self.snapshot


class _Runner:
    def __init__(self, store: _Store) -> None:
        self.store = store
        self.calls: list[str] = []

    async def run_ready_task(self, *, snapshot, task_ref):
        self.calls.append(task_ref)
        ready = snapshot.graph.task(task_ref)
        started = ready.start_attempt(
            handler_ref="handler:test",
            contract_version=1,
            started_at="2026-07-19T20:00:02Z",
            deadline_at="2026-07-19T20:10:00Z",
            actor_ref="actor:scheduler",
            cause_ref="cause:test-run",
        )
        result = SchedulerTaskResult.create(
            task_ref=task_ref,
            attempt_ref=started.attempt.attempt_ref,
            result_type_ref="result-type:test",
            completed_at="2026-07-19T20:00:03Z",
        )
        completion = started.task.complete_attempt(
            attempt=started.attempt,
            result=result,
            occurred_at="2026-07-19T20:00:03Z",
            actor_ref="actor:scheduler",
            cause_ref="cause:test-complete",
        )
        graph = SchedulerTaskGraph.create(
            graph_ref=snapshot.graph.graph_ref,
            command_ref=snapshot.command_ref,
            created_at=snapshot.graph.created_at,
            tasks=(completion.task,),
        )
        self.store.snapshot = SchedulerDurableGraphSnapshot.create(
            command_ref=snapshot.command_ref,
            scheduler_ref=snapshot.scheduler_ref,
            durable_revision=snapshot.durable_revision + 1,
            loaded_at="2026-07-19T20:00:03Z",
            graph=graph,
            source_transaction_ref="scheduler-handler-execution-transaction:test",
        )
        return _Outcome("scheduler-handler-outcome:test")


def test_bounded_cycle_promotes_executes_reloads_and_stops_on_completion() -> None:
    global TIMES
    TIMES = iter(
        (
            "2026-07-19T20:00:00Z",
            "2026-07-19T20:00:01Z",
            "2026-07-19T20:00:04Z",
            "2026-07-19T20:00:05Z",
            "2026-07-19T20:00:06Z",
        )
    )
    store = _Store(_snapshot(_graph()))
    runner = _Runner(store)
    cycle = SchedulerCanonicalBoundedCycle(
        store=store,
        step_runner=runner,
        clock=lambda: next(TIMES),
        running_probe=lambda: True,
    )

    report = asyncio.run(
        cycle.run(
            command_ref="scheduler-command:test",
            scheduler_ref="scheduler:canonical",
            actor_ref="actor:scheduler",
            cause_ref="cause:bounded-cycle",
            bound=SchedulerCanonicalCycleBound(max_task_steps=4),
        )
    )

    assert report.completed_task_steps == 1
    assert report.final_status is SchedulerContinuationStatus.COMPLETED
    assert report.bound_exhausted is False
    assert report.stopped_cooperatively is False
    assert runner.calls == ["scheduler-task:root"]
    assert store.commits == 1


def test_cycle_refuses_to_start_a_scheduler_it_does_not_own() -> None:
    store = _Store(_snapshot(_graph()))
    cycle = SchedulerCanonicalBoundedCycle(
        store=store,
        step_runner=_Runner(store),
        clock=lambda: "2026-07-19T20:00:00Z",
        running_probe=lambda: False,
    )

    with pytest.raises(
        SchedulerCanonicalContinuationError,
        match="doit déjà être actif",
    ):
        asyncio.run(
            cycle.run(
                command_ref="scheduler-command:test",
                scheduler_ref="scheduler:canonical",
                actor_ref="actor:scheduler",
                cause_ref="cause:bounded-cycle",
                bound=SchedulerCanonicalCycleBound(max_task_steps=1),
            )
        )
