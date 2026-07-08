from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "FUNCTIONAL_RESUMPTION_SUPERVISION_GATE_CONTRACT_0227.md"
RULE = ROOT / "doc" / "code-rules" / "0227_functional_resumption_supervision_gate_contract_rule.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "227_functional_resumption_supervision_gate_contract.dot"
CHANGELOG = ROOT / "doc" / "CHANGELOG_0227_FUNCTIONAL_RESUMPTION_SUPERVISION_GATE_CONTRACT.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0227_FUNCTIONAL_RESUMPTION_SUPERVISION_GATE_CONTRACT_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0227_FUNCTIONAL_RESUMPTION_SUPERVISION_GATE_CONTRACT_TEST_REPORT.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0227_contract_files_exist() -> None:
    for path in (DOC, RULE, DOT, CHANGELOG, MANIFEST, REPORT):
        assert path.exists(), path


def test_0227_contract_requires_audit_and_reuse_before_runtime_code() -> None:
    text = _read(DOC)
    assert "Mandatory pre-implementation audit" in text
    assert "existing EventBus implementation" in text
    assert "existing Scheduler event/emission surface" in text
    assert "existing passive supervisor / cellular snapshot module from 0220" in text
    assert "A new runtime module is allowed only when the audit proves" in text
    assert "prefer extension over invention" in text


def test_0227_contract_keeps_direct_eventbus_path_and_optional_outputs() -> None:
    text = _read(DOC)
    assert "EventBus -> PassiveSupervisorSink -> CellularState" in text
    assert "snapshot.json" in text
    assert "events.jsonl audit" in text
    assert "optional" in text
    assert "status.json -> supervisor as primary source" in text
    assert "snapshot.json -> live runtime state owner" in text


def test_0227_rule_forbids_parallel_runtime_and_authority_leaks() -> None:
    text = _read(RULE)
    required = [
        "new EventBus",
        "parallel bridge subsystem",
        "new scheduler wrapper",
        "mandatory events.jsonl live path",
        "status JSON as primary live input",
        "Scheduler.run()",
        "proxy control",
        "SHM mutation",
        "policy decision or override",
        "SQL/Qdrant/GitHub mutation",
        "VisPy in the critical runtime path",
    ]
    for needle in required:
        assert needle in text


def test_0227_dot_documents_gate_and_rejections() -> None:
    text = _read(DOT)
    assert "0227 functional resumption gate" in text
    assert "EventBus" in text
    assert "PassiveSupervisorSink" in text
    assert "CellularState" in text
    assert "reject" in text
