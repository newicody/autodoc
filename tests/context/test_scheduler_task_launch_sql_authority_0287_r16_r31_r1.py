from __future__ import annotations

from dataclasses import dataclass
import sqlite3

import pytest

from context.scheduler_task_launch_sql_authority_0287 import (
    DbApiSchedulerTaskLaunchTransaction,
    SchedulerTaskLaunchSqlAuthorityError,
)
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
    SchedulerTaskLaunchPreparationService,
)
from kernel.scheduler_task_model import SchedulerTask


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
        summary="Handler jamais instancié par l’autorité SQL.",
    )

    async def execute(self, command: DummyCommand, context: object) -> DummyResult:
        return DummyResult("result:unused")


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
        context_refs=("context:issue-54",),
        evidence_refs=("evidence:triplet-54",),
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
            consumed_scheduler_steps=0,
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


def _database(
    *,
    claimed_by: str = "scheduler:canonical",
    cpu_capacity: int = 2,
):
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE scheduler_command_execution_budgets ("
        "command_ref TEXT PRIMARY KEY, "
        "max_scheduler_steps INTEGER NOT NULL, "
        "max_specialist_visits INTEGER NOT NULL, "
        "max_wall_time_s DOUBLE PRECISION NOT NULL)"
    )
    connection.execute(
        "CREATE TABLE scheduler_command_states ("
        "command_ref TEXT PRIMARY KEY, state_schema TEXT NOT NULL, "
        "state TEXT NOT NULL, state_version INTEGER NOT NULL, "
        "updated_at TEXT NOT NULL, claimed_by TEXT NOT NULL, "
        "claimed_at TEXT NOT NULL, started_at TEXT NOT NULL, "
        "completed_at TEXT NOT NULL, failed_at TEXT NOT NULL, "
        "last_error_code TEXT NOT NULL)"
    )
    connection.execute(
        "INSERT INTO scheduler_command_execution_budgets "
        "VALUES (?, ?, ?, ?)",
        ("scheduler-command:research-54", 16, 2, 1800.0),
    )
    connection.execute(
        "INSERT INTO scheduler_command_states VALUES "
        "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "scheduler-command:research-54",
            "missipy.scheduler.command_sql_state.v1",
            "claimed",
            2,
            NOW,
            claimed_by,
            NOW,
            "",
            "",
            "",
            "",
        ),
    )
    connection.commit()
    transaction = DbApiSchedulerTaskLaunchTransaction(
        connection,
        paramstyle="qmark",
    )
    transaction.initialize_schema()
    transaction.put_resource_inventory_item(
        resource_ref="resource:cpu-slot",
        capacity=cpu_capacity,
        reserved=0,
        state_version=1,
        updated_at=NOW,
    )
    transaction.put_resource_inventory_item(
        resource_ref="resource:postgres-connection",
        capacity=2,
        reserved=0,
        state_version=1,
        updated_at=NOW,
    )
    return connection, transaction


def _apply(transaction: DbApiSchedulerTaskLaunchTransaction):
    candidate = _candidate()
    return SchedulerTaskLaunchPreparationService().apply(
        scheduler_ref="scheduler:canonical",
        command=DummyCommand(candidate.task.command_ref),
        candidate=candidate,
        plan=_plan(candidate),
        catalog=SchedulerHandlerCatalog((DummyResearchHandler,)),
        transaction=transaction,
        applied_at=APPLIED_AT,
    )


def test_launch_commit_is_atomic_and_relational() -> None:
    connection, transaction = _database()
    ticket = _apply(transaction)

    command_state = connection.execute(
        "SELECT state, state_version, claimed_by, started_at "
        "FROM scheduler_command_states"
    ).fetchone()
    assert command_state == ("running", 3, "scheduler:canonical", APPLIED_AT)
    budget = connection.execute(
        "SELECT consumed_scheduler_steps, consumed_specialist_visits "
        "FROM scheduler_command_budget_states"
    ).fetchone()
    assert budget == (1, 1)
    task = connection.execute(
        "SELECT state, state_version, attempt_count, effective_priority "
        "FROM scheduler_tasks"
    ).fetchone()
    assert task == (
        "running",
        ticket.task_running.state_version,
        1,
        ticket.task_running.effective_priority,
    )
    assert connection.execute(
        "SELECT COUNT(*) FROM scheduler_task_attempts"
    ).fetchone() == (1,)
    assert connection.execute(
        "SELECT COUNT(*) FROM scheduler_task_transitions"
    ).fetchone() == (1,)
    assert connection.execute(
        "SELECT COUNT(*) FROM scheduler_resource_reservations"
    ).fetchone() == (1,)
    inventory = dict(
        connection.execute(
            "SELECT resource_ref, reserved FROM scheduler_resource_inventory"
        ).fetchall()
    )
    assert inventory == {
        "resource:cpu-slot": 1,
        "resource:postgres-connection": 1,
    }
    assert ticket.launch_commit.transaction_ref.startswith(
        "scheduler-launch-transaction:"
    )


def test_exact_replay_returns_same_commit_without_double_charge() -> None:
    connection, transaction = _database()
    first = _apply(transaction)
    second = _apply(transaction)
    assert second.launch_commit == first.launch_commit
    assert connection.execute(
        "SELECT COUNT(*) FROM scheduler_task_launch_transactions"
    ).fetchone() == (1,)
    assert connection.execute(
        "SELECT consumed_scheduler_steps, consumed_specialist_visits "
        "FROM scheduler_command_budget_states"
    ).fetchone() == (1, 1)
    assert connection.execute(
        "SELECT SUM(reserved) FROM scheduler_resource_inventory"
    ).fetchone() == (2,)


def test_stale_resource_snapshot_rolls_back_every_write() -> None:
    connection, transaction = _database(cpu_capacity=0)
    with pytest.raises(SchedulerTaskLaunchSqlAuthorityError, match="capacité"):
        _apply(transaction)
    assert connection.execute(
        "SELECT state, state_version FROM scheduler_command_states"
    ).fetchone() == ("claimed", 2)
    for table in (
        "scheduler_command_budget_states",
        "scheduler_tasks",
        "scheduler_task_attempts",
        "scheduler_resource_reservations",
        "scheduler_task_launch_transactions",
    ):
        assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone() == (0,)


def test_foreign_scheduler_claim_rolls_back() -> None:
    connection, transaction = _database(claimed_by="scheduler:other")
    with pytest.raises(SchedulerTaskLaunchSqlAuthorityError, match="réclamée"):
        _apply(transaction)
    assert connection.execute(
        "SELECT state, state_version FROM scheduler_command_states"
    ).fetchone() == ("claimed", 2)
    assert connection.execute(
        "SELECT COUNT(*) FROM scheduler_task_launch_transactions"
    ).fetchone() == (0,)


def test_autocommit_connection_is_rejected() -> None:
    class AutocommitConnection:
        autocommit = True

    with pytest.raises(SchedulerTaskLaunchSqlAuthorityError, match="autocommit"):
        DbApiSchedulerTaskLaunchTransaction(AutocommitConnection())  # type: ignore[arg-type]


def test_source_has_no_json_dispatcher_or_handler_execution() -> None:
    import context.scheduler_task_launch_sql_authority_0287 as module

    source = open(module.__file__, encoding="utf-8").read()
    for forbidden in (
        "json.dumps",
        "json.loads",
        "JSONL",
        "Dispatcher",
        ".execute(command",
        "asyncio.create_task",
    ):
        assert forbidden not in source
