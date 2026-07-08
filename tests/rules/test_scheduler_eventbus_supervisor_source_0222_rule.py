from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_0222_extends_existing_supervisor_without_scheduler_control_or_new_bus() -> None:
    source = _read("src/context/passive_bus_supervisor_cellular_snapshot.py")
    tool = _read("tools/run_scheduler_eventbus_supervisor_smoke_0222.py")
    combined = source + "\n" + tool

    assert "def scheduler_supervision_event" in source
    assert "def accept_scheduler_event" in source
    assert "upstream_orchestration_authority" in combined
    assert "canonical_runtime_event_transport" in combined
    assert "PassiveSupervisorSink" in tool

    forbidden = [
        "from src.scheduler",
        "import Scheduler",
        "Scheduler.run(",
        "run_scheduler(",
        "dispatch_handler(",
        "class EventBus",
        "mmap(",
        "upsert(",
        "download_artifact(",
        "pushback(",
    ]
    for token in forbidden:
        assert token not in combined


def test_0222_docs_lock_scheduler_upstream_path() -> None:
    rule = _read("doc/code-rules/0222_scheduler_eventbus_supervisor_source_rule.md")
    changelog = _read("doc/CHANGELOG_0222_SCHEDULER_EVENTBUS_SUPERVISOR_SOURCE.md")
    architecture = _read("doc/architecture/PASSIVE_BUS_SUPERVISOR_CELLULAR_SNAPSHOT_0220.md")
    dot = _read("doc/docs/architecture/runtime/222_scheduler_eventbus_supervisor_source.dot")

    assert "Scheduler is the upstream orchestration authority" in rule
    assert "Scheduler -> EventBus -> PassiveSupervisorSink" in rule
    assert "No Scheduler import" in changelog
    assert "canonical Scheduler EventBus event" in architecture
    assert "forbidden: Scheduler.run/control" in dot
