from __future__ import annotations

import sqlite3

from context.github_research_love_externally_managed_runtime_0287 import (
    BufferedPersistentHandlerInformationSink,
    DbApiSchedulerTemporalObservationStore,
)
from kernel.scheduler_handler_contract import (
    HandlerLifecycleNotice,
    HandlerLifecyclePhase,
    HandlerNoticeLevel,
)


def test_temporal_notices_are_buffered_then_persisted_relationally() -> None:
    connection = sqlite3.connect(":memory:")
    store = DbApiSchedulerTemporalObservationStore(
        connection,
        paramstyle="qmark",
    )
    store.initialize_schema()
    sink = BufferedPersistentHandlerInformationSink(
        scheduler_ref="scheduler:autodoc-local-canonical",
        clock=lambda: "2026-07-20T18:00:00Z",
    )
    sink.publish(
        HandlerLifecycleNotice(
            handler_ref="handler:test-v1",
            capability_ref="capability:test.v1",
            phase=HandlerLifecyclePhase.CREATED,
            level=HandlerNoticeLevel.INFO,
            text="créé",
            attributes={
                "command_ref": "scheduler-command:test",
                "task_ref": "scheduler-task:test",
                "attempt": 1,
            },
        )
    )
    assert sink.pending_count == 1
    inserted, error_type = sink.flush(store)
    assert inserted == 1
    assert error_type == ""
    assert sink.pending_count == 0
    row = connection.execute(
        "SELECT phase, handler_ref, command_ref, task_ref, attempt "
        "FROM scheduler_handler_temporal_observations"
    ).fetchone()
    assert row == (
        "created",
        "handler:test-v1",
        "scheduler-command:test",
        "scheduler-task:test",
        1,
    )


def test_observation_replay_is_idempotent() -> None:
    connection = sqlite3.connect(":memory:")
    store = DbApiSchedulerTemporalObservationStore(connection, paramstyle="qmark")
    store.initialize_schema()
    sink = BufferedPersistentHandlerInformationSink(
        scheduler_ref="scheduler:autodoc-local-canonical",
        clock=lambda: "2026-07-20T18:00:00Z",
    )
    notice = HandlerLifecycleNotice(
        handler_ref="handler:test-v1",
        capability_ref="capability:test.v1",
        phase=HandlerLifecyclePhase.CLOSED,
        level=HandlerNoticeLevel.INFO,
        text="fermé",
        attributes={"task_ref": "scheduler-task:test", "attempt": 1},
    )
    sink.publish(notice)
    first = tuple(sink._pending)
    assert store.append_many(first) == 1
    assert store.append_many(first) == 0
