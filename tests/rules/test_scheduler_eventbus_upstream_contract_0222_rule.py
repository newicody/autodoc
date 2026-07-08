from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "doc/architecture/SCHEDULER_EVENTBUS_UPSTREAM_CONTRACT_0222.md"
RULE = ROOT / "doc/code-rules/0222_scheduler_eventbus_upstream_contract_rule.md"
DOT = ROOT / "doc/docs/architecture/runtime/222_scheduler_eventbus_upstream_contract.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0222_SCHEDULER_EVENTBUS_UPSTREAM_CONTRACT.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_scheduler_is_upstream_authority_and_supervisor_downstream_only() -> None:
    text = read(ARCH)
    assert "The Scheduler remains the orchestration authority" in text
    assert "PassiveSupervisorSink" in text
    assert "downstream-only" in text
    assert "EventBus is the canonical transport" in text


def test_scheduler_run_and_runtime_authority_are_forbidden() -> None:
    combined = read(ARCH) + "\n" + read(RULE)
    assert "call Scheduler.run()" in combined
    assert "modify `Scheduler.run()`" in combined
    assert "must not let the passive supervisor dispatch handlers" in combined
    assert "write SQL" in combined
    assert "write Qdrant" in combined
    assert "mutate GitHub" in combined


def test_files_are_not_canonical_observation_path() -> None:
    text = read(ARCH)
    assert "Scheduler -> status.json -> supervisor" in text
    assert "Scheduler -> events.jsonl -> supervisor" in text
    assert "only for audit, replay, smoke tests" in text


def test_runtime_diagram_keeps_scheduler_eventbus_sink_order() -> None:
    text = read(DOT)
    assert "scheduler -> eventbus" in text
    assert "eventbus -> sink" in text
    assert "sink -> cellular" in text
    assert "forbidden" in text


def test_changelog_declares_no_runtime_change() -> None:
    text = read(CHANGELOG)
    assert "No runtime code" in text
    assert "No `Scheduler.run()` call or modification" in text
