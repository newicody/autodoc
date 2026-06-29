from __future__ import annotations

from types import MappingProxyType

from contracts.replay import EventLogSnapshot, EventRecord, ReplaySandboxResult
from observability.replay_reader import ReplayReader
from observability.replay_sandbox import (
    ReplaySandbox,
    ReplaySandboxConfig,
    replay_plan_types,
)


def make_plan():
    snapshot = EventLogSnapshot(
        records=(
            EventRecord(
                id="1",
                type="LOAD",
                source="Worker",
                dest="scheduler",
                priority=0,
                timestamp_ns=10,
            ),
            EventRecord(
                id="2",
                type="TICK",
                source="Worker",
                dest="scheduler",
                priority=0,
                timestamp_ns=20,
                payload_repr="'ping'",
                metadata=MappingProxyType({"phase": "sandbox"}),
            ),
            EventRecord(
                id="3",
                type="STOP",
                source="Worker",
                dest="scheduler",
                priority=0,
                timestamp_ns=30,
            ),
        )
    )
    return ReplayReader(snapshot).to_replay_plan()


def test_replay_sandbox_replays_plan_without_scheduler() -> None:
    plan = make_plan()
    sandbox = ReplaySandbox()

    result = sandbox.replay(plan)

    assert isinstance(result, ReplaySandboxResult)
    assert result.ok
    assert result.source_record_count == 3
    assert result.planned_event_count == 3
    assert result.accepted_count == 3
    assert result.rejected_count == 0
    assert result.handled_count == 0
    assert result.event_types == ("LOAD", "TICK", "STOP")


def test_replay_sandbox_uses_simulation_handlers() -> None:
    handled_payloads: list[str] = []

    def handle_tick(event):
        handled_payloads.append(event.payload_repr)
        return {"handled": event.type, "payload": event.payload_repr}

    sandbox = ReplaySandbox(handlers={"TICK": handle_tick})

    result = sandbox.replay(make_plan())

    assert result.ok
    assert result.handled_count == 1
    assert handled_payloads == ["'ping'"]
    assert result.steps[1].handled is True
    assert result.steps[1].result_repr == "{'handled': 'TICK', 'payload': \"'ping'\"}"


def test_replay_sandbox_denies_shutdown_by_default() -> None:
    snapshot = EventLogSnapshot(
        records=(
            EventRecord(
                id="shutdown",
                type="SHUTDOWN",
                source="kernel",
                dest="scheduler",
                priority=1_000_000,
                timestamp_ns=100,
            ),
        )
    )
    plan = ReplayReader(snapshot).to_replay_plan()
    sandbox = ReplaySandbox()

    result = sandbox.replay(plan)

    assert not result.ok
    assert result.accepted_count == 0
    assert result.rejected_count == 1
    assert result.steps[0].reason == "sandbox.type.denied"


def test_replay_sandbox_can_restrict_allowed_types() -> None:
    sandbox = ReplaySandbox(
        ReplaySandboxConfig(allowed_types=frozenset({"TICK"})),
    )

    result = sandbox.replay(make_plan())

    assert not result.ok
    assert result.accepted_count == 1
    assert result.rejected_count == 2
    assert [step.reason for step in result.steps] == [
        "sandbox.type.not_allowed",
        "accepted",
        "sandbox.type.not_allowed",
    ]


def test_replay_sandbox_respects_max_events() -> None:
    sandbox = ReplaySandbox(ReplaySandboxConfig(max_events=2))

    result = sandbox.replay(make_plan())

    assert not result.ok
    assert len(result.steps) == 3
    assert result.steps[-1].reason == "sandbox.max_events"


def test_replay_plan_types_is_pure() -> None:
    plan = make_plan()

    assert replay_plan_types(plan, exclude=("LOAD",)) == ("TICK", "STOP")
    assert plan.event_types == ("LOAD", "TICK", "STOP")
