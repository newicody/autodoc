from __future__ import annotations

import json

from contracts.replay import EventLogSnapshot, EventRecord, ReplayReportExport, ReplayScenario
from observability.replay_exporter import ReplayReportExporter
from observability.replay_reader import ReplayReader
from observability.replay_scenario import ReplayScenarioRunner


def make_report():
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
    plan = ReplayReader(snapshot).to_replay_plan()
    runner = ReplayScenarioRunner(handlers={"TICK": lambda event: event.type.lower()})
    return runner.report((ReplayScenario(name="export", plan=plan, tags=("phase2",)),))


def test_replay_report_exporter_text_is_stable() -> None:
    report = make_report()
    exporter = ReplayReportExporter()

    export = exporter.to_text(report)

    assert isinstance(export, ReplayReportExport)
    assert export.format == "text"
    assert export.media_type == "text/plain; charset=utf-8"
    assert export.content == "\n".join(report.to_lines())
    assert "ReplayReport: OK" in export.content


def test_replay_report_exporter_json_is_deterministic() -> None:
    report = make_report()
    exporter = ReplayReportExporter()

    first = exporter.to_json(report)
    second = exporter.to_json(report)

    assert first == second
    assert first.format == "json"
    assert first.media_type == "application/json; charset=utf-8"
    assert first.content == second.content
    assert first.content.startswith('{"accepted_count"')

    data = json.loads(first.content)
    assert data["schema"] == "missipy.replay.report.v1"
    assert data["ok"] is True
    assert data["scenario_count"] == 1
    assert data["handled_count"] == 1
    assert data["scenarios"][0]["name"] == "export"
    assert data["scenarios"][0]["tags"] == ["phase2"]
    assert data["scenarios"][0]["steps"][1]["result_repr"] == "'tick'"


def test_replay_report_export_validates_metadata() -> None:
    try:
        ReplayReportExport(format="", media_type="text/plain", content="x")
    except ValueError as exc:
        assert "format" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("empty format must be rejected")

    try:
        ReplayReportExport(format="text", media_type="", content="x")
    except ValueError as exc:
        assert "media_type" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("empty media_type must be rejected")
