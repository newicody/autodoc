from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc/architecture/CELLULAR_TOPOLOGY_EVENTBUS_SUPERVISION_CONTRACT_0225.md"
RULE = ROOT / "doc/code-rules/0225_cellular_topology_eventbus_supervision_contract_rule.md"
DOT = ROOT / "doc/docs/architecture/runtime/225_cellular_topology_eventbus_supervision_contract.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0225_CELLULAR_TOPOLOGY_EVENTBUS_SUPERVISION_CONTRACT.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0225_CELLULAR_TOPOLOGY_EVENTBUS_SUPERVISION_CONTRACT_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0225_CELLULAR_TOPOLOGY_EVENTBUS_SUPERVISION_CONTRACT_TEST_REPORT.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_cellular_topology_contract_files_exist() -> None:
    for path in (DOC, RULE, DOT, CHANGELOG, MANIFEST, REPORT):
        assert path.exists(), path


def test_cellular_topology_is_downstream_projection() -> None:
    text = read(DOC)
    assert "projection of canonical EventBus events" in text
    assert "Movement is observed" in text
    assert "It must not execute the movement" in text
    assert "The supervisor must not invent authoritative identities" in text


def test_cellular_topology_preserves_authority_boundaries() -> None:
    text = read(DOC) + "\n" + read(RULE)
    required = [
        "call Scheduler.run()",
        "wrap Scheduler.run()",
        "claim or release proxy leases",
        "write to SHM",
        "decide policy",
        "write SQL",
        "query/write Qdrant",
        "mutate GitHub",
        "introduce a parallel bus",
    ]
    for token in required:
        assert token in text


def test_cellular_topology_keeps_snapshot_and_audit_optional() -> None:
    text = read(DOC) + "\n" + read(RULE)
    assert "optional snapshot" in text
    assert "optional audit/replay" in text
    assert "They are not the canonical runtime path" in text


def test_cellular_topology_dot_shows_eventbus_path() -> None:
    dot = read(DOT)
    assert "EventBus" in dot
    assert "PassiveSupervisorSink" in dot
    assert "CellularTopology" in dot
    assert "future VisPy view" in dot
    assert "no control" in dot
