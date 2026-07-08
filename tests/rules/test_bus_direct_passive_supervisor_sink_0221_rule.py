from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_0221_updates_existing_passive_supervisor_without_new_bus_or_scheduler_control() -> None:
    source = _read("src/context/passive_bus_supervisor_cellular_snapshot.py")
    tool = _read("tools/run_passive_bus_supervisor_cellular_snapshot_0220.py")
    combined = source + "\n" + tool

    assert "class PassiveSupervisorSink" in source
    assert "upstream_orchestration_authority" in source
    assert "canonical_runtime_event_transport" in source
    assert "optional_replay_or_audit_only" in tool

    forbidden = [
        "Scheduler.run(",
        "run_scheduler(",
        "dispatch_handler(",
        "mmap(",
        "upsert(",
        "download_artifact(",
        "pushback(",
    ]
    for token in forbidden:
        assert token not in combined

    assert "class EventBus" not in source
    assert "events_jsonl: Path | None" in tool


def test_0221_docs_lock_bus_direct_runtime_path() -> None:
    rule = _read("doc/code-rules/0221_bus_direct_passive_supervisor_sink_rule.md")
    changelog = _read("doc/CHANGELOG_0221_BUS_DIRECT_PASSIVE_SUPERVISOR_SINK.md")
    architecture = _read("doc/architecture/PASSIVE_BUS_SUPERVISOR_CELLULAR_SNAPSHOT_0220.md")
    dot = _read("doc/docs/architecture/runtime/221_bus_direct_passive_supervisor_sink.dot")

    assert "Scheduler is the upstream orchestration authority" in rule
    assert "EventBus -> PassiveSupervisorSink" in rule
    assert "events.jsonl` is optional audit/replay/debug output only" in rule
    assert "No new bus implementation" in changelog
    assert "EventBus -> PassiveSupervisorSink.accept(event)" in architecture
    assert "forbidden: Scheduler.run/control" in dot
