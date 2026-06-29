from __future__ import annotations

from contracts.replay import EventLogSnapshot, EventRecord, ReplayReport, ReplayScenario
from observability.replay_reader import ReplayReader
from observability.replay_scenario import ReplayScenarioRunner


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


def test_replay_scenario_runner_builds_report() -> None:
    scenario = ReplayScenario(name="basic", plan=make_plan(), tags=("phase2",))
    runner = ReplayScenarioRunner()

    report = runner.report((scenario,))

    assert isinstance(report, ReplayReport)
    assert report.ok
    assert report.scenario_count == 1
    assert report.scenario_names == ("basic",)
    assert report.accepted_count == 3
    assert report.rejected_count == 0
    assert report.handled_count == 0
    assert report.scenario_results[0].tags == ("phase2",)


def test_replay_scenario_runner_uses_shared_handlers() -> None:
    handled: list[str] = []

    def handle_tick(event):
        handled.append(event.payload_repr)
        return event.type.lower()

    scenario = ReplayScenario(name="handled", plan=make_plan())
    runner = ReplayScenarioRunner(handlers={"TICK": handle_tick})

    result = runner.run(scenario)

    assert result.ok
    assert result.handled_count == 1
    assert handled == ["'ping'"]
    assert result.sandbox_result.steps[1].result_repr == "'tick'"


def test_replay_scenario_report_is_deterministic_text() -> None:
    runner = ReplayScenarioRunner()
    ok_scenario = ReplayScenario(name="ok", plan=make_plan())
    restricted = ReplayScenario(
        name="restricted",
        plan=make_plan(),
        allowed_types=frozenset({"TICK"}),
    )

    report = runner.report((ok_scenario, restricted))

    assert not report.ok
    assert report.accepted_count == 4
    assert report.rejected_count == 2
    assert report.to_lines() == (
        "ReplayReport: FAILED",
        "scenarios=2",
        "accepted=4",
        "rejected=2",
        "handled=0",
        "scenario=ok status=OK accepted=3 rejected=0 handled=0",
        "scenario=restricted status=FAILED accepted=1 rejected=2 handled=0",
    )


def test_replay_scenario_validates_name_and_budget() -> None:
    plan = make_plan()

    try:
        ReplayScenario(name="", plan=plan)
    except ValueError as exc:
        assert "name" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("empty scenario name must be rejected")

    try:
        ReplayScenario(name="bad-budget", plan=plan, max_events=0)
    except ValueError as exc:
        assert "positive" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("invalid max_events must be rejected")
