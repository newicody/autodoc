from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "doc/architecture/RUNTIME_SURFACE_EVENTBUS_UPSTREAM_CONTRACT_0223.md"
RULE = ROOT / "doc/code-rules/0223_runtime_surface_eventbus_upstream_contract_rule.md"
DOT = ROOT / "doc/docs/architecture/runtime/223_runtime_surface_eventbus_upstream_contract.dot"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_runtime_surface_contract_documents_canonical_eventbus_path() -> None:
    text = _read(ARCH)

    assert "RouteProxy" in text
    assert "ControlProxy" in text
    assert "SHM" in text
    assert "Policy" in text
    assert "EventBus" in text
    assert "PassiveSupervisorSink" in text
    assert "CellularState" in text
    assert "runtime surface -> EventBus -> PassiveSupervisorSink -> CellularState" in text


def test_runtime_surface_contract_preserves_scheduler_and_policy_authority() -> None:
    text = _read(ARCH)

    assert "The Scheduler remains the orchestration authority." in text
    assert "Policy = decision authority" in text
    assert "must not invoke or wrap" in text
    assert "must not decide policy" in text


def test_runtime_surface_rule_forbids_parallel_control_paths() -> None:
    text = _read(RULE)

    required = [
        "create a new EventBus implementation",
        "make status JSON or events.jsonl the normal runtime transport",
        "call, wrap, or modify `Scheduler.run()`",
        "control RouteProxy or ControlProxy",
        "write SHM or mutate SHM cursors/slots",
        "decide policy or become a policy engine",
        "write SQL or Qdrant",
        "mutate GitHub",
        "introduce VisPy into the runtime path",
    ]

    for phrase in required:
        assert phrase in text


def test_runtime_surface_contract_keeps_snapshot_and_audit_optional() -> None:
    arch = _read(ARCH)
    rule = _read(RULE)

    assert "optional snapshot" in arch
    assert "optional audit/replay" in arch
    assert "keep snapshot and events.jsonl optional outputs only" in rule
    assert "events.jsonl -> supervisor as primary transport" in arch
    assert "Forbidden normal path" in arch


def test_runtime_surface_dot_contains_forbidden_back_edges() -> None:
    text = _read(DOT)

    assert "EventBus" in text
    assert "PassiveSupervisorSink" in text
    assert "forbidden control" in text
    assert "forbidden write/mmap authority" in text
    assert "forbidden decision" in text
