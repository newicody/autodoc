from __future__ import annotations

import sqlite3

from context.github_research_love_postgresql_continuation_store_0287 import (
    DbApiGitHubResearchLovePostgreSqlContinuationStore,
)
from kernel.scheduler_task_graph import SchedulerTaskGraph
from kernel.scheduler_task_model import SchedulerTask, SchedulerTaskState


NOW = "2026-07-20T12:00:00Z"
PROMOTED = "2026-07-20T12:00:01Z"


def _shared_tables(connection: sqlite3.Connection) -> None:
    statements = (
        "CREATE TABLE scheduler_tasks (task_ref TEXT PRIMARY KEY, command_ref TEXT NOT NULL, task_kind_ref TEXT NOT NULL, capability_ref TEXT NOT NULL, contract_version INTEGER NOT NULL, state TEXT NOT NULL, state_version INTEGER NOT NULL, initial_priority INTEGER NOT NULL, effective_priority INTEGER NOT NULL, max_attempts INTEGER NOT NULL, attempt_count INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, parent_task_ref TEXT NOT NULL, task_digest TEXT NOT NULL)",
        "CREATE TABLE scheduler_task_dependencies (task_ref TEXT NOT NULL, ordinal INTEGER NOT NULL, dependency_task_ref TEXT NOT NULL, dependency_kind TEXT NOT NULL, PRIMARY KEY(task_ref, ordinal))",
        "CREATE TABLE scheduler_task_context_refs (task_ref TEXT NOT NULL, ordinal INTEGER NOT NULL, context_ref TEXT NOT NULL, PRIMARY KEY(task_ref, ordinal))",
        "CREATE TABLE scheduler_task_evidence_refs (task_ref TEXT NOT NULL, ordinal INTEGER NOT NULL, evidence_ref TEXT NOT NULL, PRIMARY KEY(task_ref, ordinal))",
        "CREATE TABLE scheduler_task_transitions (transition_ref TEXT PRIMARY KEY, task_ref TEXT NOT NULL, from_state TEXT NOT NULL, to_state TEXT NOT NULL, state_version INTEGER NOT NULL, occurred_at TEXT NOT NULL, actor_ref TEXT NOT NULL, cause_ref TEXT NOT NULL, transition_digest TEXT NOT NULL UNIQUE)",
        "CREATE TABLE scheduler_task_launch_transactions (transaction_ref TEXT PRIMARY KEY, command_ref TEXT NOT NULL, committed_at TEXT NOT NULL)",
        "CREATE TABLE scheduler_handler_execution_transactions (transaction_ref TEXT PRIMARY KEY, command_ref TEXT NOT NULL, released_at TEXT NOT NULL)",
    )
    for statement in statements:
        connection.execute(statement)
    connection.commit()


def test_register_promote_and_reload_graph_on_same_connection() -> None:
    connection = sqlite3.connect(":memory:")
    _shared_tables(connection)
    store = DbApiGitHubResearchLovePostgreSqlContinuationStore(
        connection,
        scheduler_ref="scheduler:canonical",
        paramstyle="qmark",
    )
    store.initialize_schema()
    task = SchedulerTask.plan(
        task_ref="scheduler-task:first",
        command_ref="scheduler-command:research-15",
        task_kind_ref="task-kind:research",
        capability_ref="capability:love-first-visit",
        contract_version=1,
        priority=50,
        max_attempts=1,
        created_at=NOW,
    )
    graph = SchedulerTaskGraph.create(
        graph_ref="scheduler-task-graph:research-15",
        command_ref=task.command_ref,
        created_at=NOW,
        tasks=(task,),
    )
    initial = store.put_initial_graph(
        graph=graph,
        scheduler_ref="scheduler:canonical",
        source_transaction_ref="scheduler-graph-bootstrap:research-15",
    )
    assert initial.durable_revision == 1
    assert initial.graph.graph_digest == graph.graph_digest
    promotion = initial.graph.promote_ready(
        occurred_at=PROMOTED,
        actor_ref="scheduler:canonical",
        cause_ref="scheduler-command:research-15",
    )
    committed = store.commit_promotion(
        snapshot=initial,
        promotion=promotion,
        committed_at=PROMOTED,
        actor_ref="scheduler:canonical",
        cause_ref="scheduler-command:research-15",
    )
    assert committed.durable_revision == 2
    assert committed.graph.task(task.task_ref).state is SchedulerTaskState.READY
    assert committed.graph.graph_digest == promotion.graph.graph_digest
    assert committed.source_transaction_ref.startswith("scheduler-graph-promotion:")
