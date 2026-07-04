from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "BABY_FORK_RUNTIME_FLOW_CLI.md"
MODULE = ROOT / "src" / "context" / "baby_fork_runtime_flow.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_runtime_flow_cli_doc_locks_end_to_end_file_backed_scope() -> None:
    text = _read(DOC)

    required_phrases = [
        "baby_fork_report.json",
        "runtime projection",
        "fake runtime surface",
        "recorder journal",
        "optional ControlFS desired manifests",
        "optional RouteProxy dry-run plan",
        "real Scheduler run",
        "RouteProxy daemon",
        "real shared memory",
        "real semaphores",
        "ring buffer",
        "active route creation",
        "ZFS requirement",
        "NetworkBridge",
        "HardwareBridge",
        "cluster dispatch",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_runtime_flow_module_is_orchestrator_only() -> None:
    text = _read(MODULE)

    required_phrases = [
        "It only orchestrates already-validated local pieces",
        "run the real Scheduler",
        "start RouteProxy",
        "create shared memory",
        "create semaphores",
        "implement a ring buffer",
        "mutate active/routes",
        "mutate revoked/routes",
        "require ZFS",
        "implement NetworkBridge or HardwareBridge",
    ]

    for phrase in required_phrases:
        assert phrase in text
