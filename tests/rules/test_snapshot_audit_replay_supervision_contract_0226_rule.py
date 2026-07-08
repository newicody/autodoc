from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "SNAPSHOT_AUDIT_REPLAY_SUPERVISION_CONTRACT_0226.md"
RULE = ROOT / "doc" / "code-rules" / "0226_snapshot_audit_replay_supervision_contract_rule.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "226_snapshot_audit_replay_supervision_contract.dot"
CHANGELOG = ROOT / "doc" / "CHANGELOG_0226_SNAPSHOT_AUDIT_REPLAY_SUPERVISION_CONTRACT.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_canonical_live_path_is_eventbus_sink_cellular_state() -> None:
    text = read(DOC)
    assert "EventBus" in text
    assert "PassiveSupervisorSink" in text
    assert "CellularState" in text
    assert "component -> EventBus -> PassiveSupervisorSink -> CellularState -> optional snapshot" in text


def test_events_jsonl_and_snapshot_are_not_mandatory_runtime_inputs() -> None:
    text = read(DOC) + read(RULE)
    assert "events.jsonl" in text
    assert "snapshot.json" in text
    assert "must not be mandatory in the runtime path" in text
    assert "Do not make `events.jsonl` mandatory for live supervision." in text
    assert "Do not make `snapshot.json` the normal upstream source of truth." in text


def test_replay_and_vispy_are_optional_downstream_or_test_surfaces() -> None:
    text = read(DOC) + read(RULE)
    assert "replay mode = file fixture / audit journal / regression test" in text
    assert "VisPy is a future view" in text
    assert "Future VisPy views that read `snapshot()` or `snapshot.json` only." in text
    assert "Do not place VisPy in the critical runtime path." in text


def test_forbidden_authority_expansion_is_documented() -> None:
    text = read(DOC) + read(RULE)
    assert "Do not call or wrap `Scheduler.run()` from the passive supervisor." in text
    assert "VisPy -> Scheduler" in text
    assert "EventBus -> PassiveSupervisorSink -> CellularState" in text
    assert "status-file-first bridge" in text


def test_dot_and_changelog_record_optional_outputs() -> None:
    dot = read(DOT)
    changelog = read(CHANGELOG)
    assert "optional audit/replay" in dot
    assert "test/debug only" in dot
    assert "forbidden as normal input" in dot
    assert "No runtime code." in changelog
