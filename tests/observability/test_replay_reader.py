from __future__ import annotations

from types import MappingProxyType

from contracts.replay import EventLogSnapshot, EventRecord, ReplayPlan
from observability.replay_reader import ReplayReader


def make_snapshot() -> EventLogSnapshot:
    return EventLogSnapshot(
        records=(
            EventRecord(
                id="1",
                type="LOAD",
                source="Worker",
                dest="scheduler",
                priority=0,
                timestamp_ns=10,
                payload_repr="None",
            ),
            EventRecord(
                id="2",
                type="TICK",
                source="Worker",
                dest="scheduler",
                priority=0,
                timestamp_ns=20,
                payload_repr="'ping'",
                metadata=MappingProxyType({"phase": "test"}),
            ),
            EventRecord(
                id="3",
                type="STOP",
                source="Worker",
                dest="scheduler",
                priority=0,
                timestamp_ns=30,
                payload_repr="None",
            ),
        )
    )


def test_replay_reader_filters_records_without_mutating_snapshot() -> None:
    snapshot = make_snapshot()
    reader = ReplayReader(snapshot)

    tick_records = reader.records(event_type="TICK")

    assert snapshot.count == 3
    assert len(tick_records) == 1
    assert tick_records[0].id == "2"
    assert reader.records(source="Worker", dest="scheduler") == snapshot.records


def test_replay_reader_returns_distinct_event_types_in_order() -> None:
    reader = ReplayReader(make_snapshot())

    assert reader.event_types() == ("LOAD", "TICK", "STOP")


def test_replay_reader_builds_controlled_replay_plan() -> None:
    reader = ReplayReader(make_snapshot())

    plan = reader.to_replay_plan(
        include_types=("LOAD", "TICK", "STOP"),
        exclude_types=("LOAD",),
    )

    assert isinstance(plan, ReplayPlan)
    assert plan.source_record_count == 3
    assert plan.count == 2
    assert plan.event_types == ("TICK", "STOP")
    assert plan.events[0].original_id == "2"
    assert plan.events[0].payload_repr == "'ping'"
    assert dict(plan.events[0].metadata) == {"phase": "test"}


def test_replay_plan_is_immutable() -> None:
    reader = ReplayReader(make_snapshot())
    plan = reader.to_replay_plan()

    try:
        plan.events += ()
    except Exception as exc:  # noqa: BLE001 - test volontaire d'immutabilité runtime
        assert isinstance(exc, AttributeError)
    else:  # pragma: no cover
        raise AssertionError("ReplayPlan must be immutable")
