from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RULE = ROOT / "doc" / "code-rules" / "0224_data_surface_eventbus_upstream_contract_rule.md"
ARCH = ROOT / "doc" / "architecture" / "DATA_SURFACE_EVENTBUS_UPSTREAM_CONTRACT_0224.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "224_data_surface_eventbus_upstream_contract.dot"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_data_surface_contract_mentions_all_observed_surfaces() -> None:
    text = read(ARCH)
    for token in [
        "GitHub artifact",
        "SourceCandidate",
        "SQL",
        "Qdrant",
        "Rehydration",
        "Pushback",
        "EventBus",
        "PassiveSupervisorSink",
    ]:
        assert token in text


def test_data_surface_contract_keeps_supervisor_downstream_only() -> None:
    text = read(RULE)
    for forbidden in [
        "call GitHub APIs",
        "validate, promote, reject, or enrich SourceCandidates",
        "write, read, migrate, or reconcile SQL state",
        "write, query, create, delete, or reconcile Qdrant state",
        "execute rehydration",
        "send pushback",
        "call or wrap `Scheduler.run()`",
        "control RouteProxy or ControlProxy",
        "mutate SHM",
        "make policy decisions",
        "introduce a new EventBus",
    ]:
        assert forbidden in text


def test_data_surface_contract_preserves_first_level_refs() -> None:
    text = read(RULE)
    for token in [
        "artifact_ref",
        "source_candidate_ref",
        "sql_ref",
        "qdrant_ref",
        "handoff_ref",
        "pushback_ref",
    ]:
        assert token in text


def test_data_surface_dot_shows_optional_outputs_and_forbidden_edges() -> None:
    text = read(DOT)
    for token in [
        "EventBus",
        "PassiveSupervisorSink",
        "CellularState",
        "optional audit/replay",
        "forbidden mutation",
        "forbidden write/read",
        "forbidden write/query",
        "forbidden Scheduler.run",
    ]:
        assert token in text


def test_events_jsonl_is_optional_not_normal_path() -> None:
    text = read(RULE) + "\n" + read(ARCH)
    assert "optional audit/replay" in text
    assert "make `events.jsonl` or `status.json` the normal runtime path" in text
