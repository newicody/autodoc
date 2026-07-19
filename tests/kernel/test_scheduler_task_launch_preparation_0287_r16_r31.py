from __future__ import annotations

from dataclasses import dataclass, replace

import pytest

from kernel.scheduler_handler_catalog import SchedulerHandlerCatalog
from kernel.scheduler_handler_contract import (
    HandlerExecutionPolicy,
    HandlerIdempotencyKind,
    HandlerInformation,
    SchedulerHandler,
)
from kernel.scheduler_task_admission import (
    SchedulerBudgetCharge,
    SchedulerCommandExecutionBudget,
    SchedulerFairnessPolicy,
    SchedulerResourceInventoryItem,
    SchedulerResourceProfile,
    SchedulerResourceRequirement,
    SchedulerRetryPolicy,
    SchedulerTaskAdmissionCandidate,
    SchedulerTaskAdmissionPlanner,
    SchedulerTaskExecutionBudget,
)
from kernel.scheduler_task_launch_preparation import (
    SchedulerTaskLaunchCommit,
    SchedulerTaskLaunchPreparationError,
    SchedulerTaskLaunchPreparationService,
)
from kernel.scheduler_task_model import SchedulerTask, SchedulerTaskState


NOW = "2026-07-19T12:00:00Z"
APPLIED_AT = "2026-07-19T12:00:01Z"


@dataclass(frozen=True, slots=True)
class DummyCommand:
    command_ref: str


@dataclass(frozen=True, slots=True)
class DummyResult:
    result_ref: str


class DummyResearchHandler(SchedulerHandler[DummyCommand, DummyResult]):
    ABSTRACT_HANDLER = False
    HANDLER_REF = "handler:dummy-research"
    CAPABILITY_REF = "capability:research-analysis"
    COMMAND_TYPE = DummyCommand
    RESULT_TYPE = DummyResult
    CONTRACT_VERSION = 1
    EXECUTION_POLICY = HandlerExecutionPolicy(
        idempotency=HandlerIdempotencyKind.DEDUPLICATED,
        timeout_policy_ref="timeout-policy:bounded-600s",
        retry_policy_ref="retry-policy:bounded-exponential",
        resource_profile_ref="resource-profile:research-cpu",
        laboratory_compatibility=("laboratory-kind:love",),
    )
    INFORMATION = HandlerInformation(
        title="Analyse factice",
        summary="Handler de test jamais instancié par r16-r31.",
    )
    instances = 0
    executions = 0

    def __init__(self) -> None:
        type(self).instances += 1

    async def execute(self, command: DummyCommand, context: object) -> DummyResult:
        type(self).executions += 1
        return DummyResult("result:never")


class RecordingTransaction:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.corrupt_field = ""

    def commit_launch(self, **kwargs: object) -> SchedulerTaskLaunchCommit:
        self.calls.append(dict(kwargs))
        attempt_start = kwargs["attempt_start"]
        budget_mutation = kwargs["budget_mutation"]
        reservation = kwargs["reservation"]
        plan = kwargs["plan"]
        assert hasattr(attempt_start, "attempt")
        assert hasattr(budget_mutation, "scheduler_steps_after")
        assert hasattr(reservation, "reservation_ref")
        assert hasattr(plan, "plan_digest")
        values = dict(
            scheduler_ref=str(kwargs["scheduler_ref"]),
            command_ref=attempt_start.task.command_ref,
            task_ref=attempt_start.task.task_ref,
            attempt_ref=attempt_start.attempt.attempt_ref,
            reservation_ref=reservation.reservation_ref,
            admission_plan_digest=plan.plan_digest,
            task_state_version=attempt_start.task.state_version,
            scheduler_steps_after=budget_mutation.scheduler_steps_after,
            specialist_visits_after=budget_mutation.specialist_visits_after,
            committed_at=str(kwargs["committed_at"]),
        )
        if self.corrupt_field:
            if self.corrupt_field == "scheduler_steps_after":
                values[self.corrupt_field] = int(values[self.corrupt_field]) + 1
            else:
                values[self.corrupt_field] = "scheduler-task:corrupt"
        return SchedulerTaskLaunchCommit.create(**values)


def _ready_task() -> SchedulerTask:
    planned = SchedulerTask.plan(
        task_ref="scheduler-task:analysis-1",
        command_ref="scheduler-command:research-54",
        task_kind_ref="task-kind:research-analysis",
        capability_ref="capability:research-analysis",
        contract_version=1,
        priority=40,
        max_attempts=3,
        created_at="2026-07-19T11:00:00Z",
    )
    return planned.mark_ready(
        dependency_states={},
        occurred_at="2026-07-19T11:00:01Z",
        actor_ref="scheduler:canonical",
        cause_ref="scheduler-cause:graph-ready",
    ).task


def _candidate() -> SchedulerTaskAdmissionCandidate:
    task = _ready_task()
    return SchedulerTaskAdmissionCandidate(
        task=task,
        command_budget=SchedulerCommandExecutionBudget(
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
            budget_ref="scheduler-task-budget:analysis-1",
            task_ref=task.task_ref,
            max_attempts=task.max_attempts,
            timeout_seconds=600,
        ),
        budget_charge=SchedulerBudgetCharge(
            scheduler_steps=1,
            specialist_visits=1,
        ),
        resource_profile=SchedulerResourceProfile(
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
        ),
        retry_policy=SchedulerRetryPolicy(
            policy_ref="retry-policy:bounded-exponential",
            base_delay_seconds=10,
            multiplier=2,
            max_delay_seconds=120,
        ),
    )


def _plan(candidate: SchedulerTaskAdmissionCandidate):
    return SchedulerTaskAdmissionPlanner().plan(
        candidates=(candidate,),
        inventory=(
            SchedulerResourceInventoryItem("resource:cpu-slot", 2, 0),
            SchedulerResourceInventoryItem(
                "resource:postgres-connection", 2, 0
            ),
        ),
        now=NOW,
        max_admissions=1,
    )


def _apply(
    *,
    candidate: SchedulerTaskAdmissionCandidate | None = None,
    transaction: RecordingTransaction | None = None,
    applied_at: str = APPLIED_AT,
):
    selected = candidate or _candidate()
    tx = transaction or RecordingTransaction()
    ticket = SchedulerTaskLaunchPreparationService().apply(
        scheduler_ref="scheduler:canonical",
        command=DummyCommand(selected.task.command_ref),
        candidate=selected,
        plan=_plan(selected),
        catalog=SchedulerHandlerCatalog((DummyResearchHandler,)),
        transaction=tx,
        applied_at=applied_at,
    )
    return ticket, tx


def test_admitted_plan_is_committed_and_returns_typed_launch_ticket() -> None:
    ticket, transaction = _apply()
    assert len(transaction.calls) == 1
    assert ticket.task_before.state is SchedulerTaskState.READY
    assert ticket.task_running.state is SchedulerTaskState.RUNNING
    assert ticket.task_running.attempt_count == 1
    assert ticket.attempt.handler_ref == DummyResearchHandler.HANDLER_REF
    assert ticket.launch_commit.transaction_ref.startswith(
        "scheduler-launch-transaction:"
    )
    assert ticket.ticket_ref.startswith("scheduler-handler-launch:")


def test_effective_priority_and_budget_charge_are_committed() -> None:
    candidate = _candidate()
    plan = _plan(candidate)
    expected_priority = plan.decisions[0].effective_priority
    ticket, _ = _apply(candidate=candidate)
    assert ticket.task_running.effective_priority == expected_priority
    assert ticket.budget_mutation.scheduler_steps_before == 2
    assert ticket.budget_mutation.scheduler_steps_after == 3
    assert ticket.budget_mutation.specialist_visits_after == 1


def test_handler_is_resolved_but_never_instantiated_or_executed() -> None:
    DummyResearchHandler.instances = 0
    DummyResearchHandler.executions = 0
    ticket, _ = _apply()
    assert ticket.handler_binding.handler_type is DummyResearchHandler
    assert DummyResearchHandler.instances == 0
    assert DummyResearchHandler.executions == 0


def test_non_admitted_decision_cannot_be_applied() -> None:
    candidate = _candidate()
    deferred_plan = SchedulerTaskAdmissionPlanner().plan(
        candidates=(candidate,),
        inventory=(
            SchedulerResourceInventoryItem("resource:cpu-slot", 0, 0),
            SchedulerResourceInventoryItem(
                "resource:postgres-connection", 2, 0
            ),
        ),
        now=NOW,
        max_admissions=1,
    )
    with pytest.raises(SchedulerTaskLaunchPreparationError, match="admitted"):
        SchedulerTaskLaunchPreparationService().apply(
            scheduler_ref="scheduler:canonical",
            command=DummyCommand(candidate.task.command_ref),
            candidate=candidate,
            plan=deferred_plan,
            catalog=SchedulerHandlerCatalog((DummyResearchHandler,)),
            transaction=RecordingTransaction(),
            applied_at=APPLIED_AT,
        )


def test_expired_launch_window_is_rejected_before_transaction() -> None:
    tx = RecordingTransaction()
    with pytest.raises(SchedulerTaskLaunchPreparationError, match="expirée"):
        _apply(transaction=tx, applied_at="2026-07-19T12:10:00Z")
    assert tx.calls == []


def test_handler_resource_policy_must_match_admission_profile() -> None:
    candidate = _candidate()
    incompatible = replace(
        candidate,
        resource_profile=SchedulerResourceProfile(
            profile_ref="resource-profile:other",
            requirements=(SchedulerResourceRequirement("resource:cpu-slot", 1),),
        ),
    )
    with pytest.raises(SchedulerTaskLaunchPreparationError, match="profil de ressources"):
        _apply(candidate=incompatible)


def test_corrupt_transaction_receipt_is_rejected() -> None:
    tx = RecordingTransaction()
    tx.corrupt_field = "scheduler_steps_after"
    with pytest.raises(SchedulerTaskLaunchPreparationError, match="receipt"):
        _apply(transaction=tx)


def test_source_has_no_handler_execution_or_json_storage() -> None:
    import kernel.scheduler_task_launch_preparation as module

    source = open(module.__file__, encoding="utf-8").read()
    for forbidden in (
        ".execute(",
        "Dispatcher",
        "EventBus",
        "json.dumps",
        "json.loads",
        "JSONL",
        "asyncio.create_task",
    ):
        assert forbidden not in source
